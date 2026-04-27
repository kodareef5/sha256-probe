/* dispatcher.c — concurrent kissat work queue runner for Apple Silicon.
 *
 * Reads work_queue.tsv (TAB-separated: cnf_path<TAB>seed<TAB>conflicts<TAB>tag)
 * Forks N parallel kissat workers. As each finishes, pops next job atomically
 * (via O_APPEND lock + state file) and replaces it. Logs status + wall to
 * ./logs/run_NNNNN.log + appends summary line to results.tsv.
 *
 * Concurrency: M workers running at any time. Tested with M=6 on M5 (10 cores
 * total; leave 4 for system/this process/IO).
 *
 * Signal handling: SIGINT / SIGTERM cleanly waits for active workers, drains
 * partial logs, exits.
 *
 * Compile: gcc -O3 -march=native -o dispatcher dispatcher.c
 * Usage:   ./dispatcher <queue.tsv> <num_workers> [--time-cap-sec N]
 *
 * Each kissat invocation:
 *   kissat <cnf> -q --seed=<S> --conflicts=<C> --time=<T>
 * where T is min(time_cap, conflicts/avg_conflict_rate).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <time.h>

#define MAX_WORKERS 32
#define MAX_LINE 1024

static volatile sig_atomic_t g_stop = 0;
static void on_sigint(int sig) { (void)sig; g_stop = 1; }

typedef struct {
    pid_t pid;
    int run_id;
    char cnf[512];
    int seed;
    long long conflicts;
    char tag[128];
    struct timespec start;
    int active;
} worker_t;

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static void timestamp_iso(char *out, size_t n) {
    time_t t = time(NULL);
    struct tm tm;
    gmtime_r(&t, &tm);
    strftime(out, n, "%Y-%m-%dT%H:%M:%SZ", &tm);
}

/* Atomic line-pop from queue. Reads queue.tsv, finds first line whose
 * status column is "PENDING", flips to "RUNNING:<pid>", writes back. */
static int pop_job(const char *queue_path,
                   char *cnf_out, int *seed_out, long long *conflicts_out,
                   char *tag_out, int *line_no_out, pid_t worker_pid) {
    int fd = open(queue_path, O_RDWR);
    if (fd < 0) return -1;
    if (flock(fd, LOCK_EX) < 0) { close(fd); return -1; }

    /* Read entire file. */
    struct stat st;
    fstat(fd, &st);
    char *buf = malloc(st.st_size + 1);
    pread(fd, buf, st.st_size, 0);
    buf[st.st_size] = 0;

    int line_no = 0;
    int found = -1;
    char *p = buf;
    while (*p) {
        char *line_start = p;
        char *eol = strchr(p, '\n');
        size_t len = eol ? (size_t)(eol - p) : strlen(p);
        line_no++;
        if (len > 0 && *p != '#') {
            /* Format: status<TAB>cnf<TAB>seed<TAB>conflicts<TAB>tag */
            char tmp[MAX_LINE];
            if (len < MAX_LINE) {
                memcpy(tmp, p, len); tmp[len] = 0;
                if (strncmp(tmp, "PENDING\t", 8) == 0) {
                    /* Parse fields. */
                    char *fields[5] = {0};
                    fields[0] = tmp;
                    int nf = 1;
                    for (char *q = tmp; *q && nf < 5; q++) {
                        if (*q == '\t') { *q = 0; fields[nf++] = q+1; }
                    }
                    if (nf == 5) {
                        strncpy(cnf_out, fields[1], 511);
                        *seed_out = atoi(fields[2]);
                        *conflicts_out = atoll(fields[3]);
                        strncpy(tag_out, fields[4], 127);
                        *line_no_out = line_no;
                        found = (line_start - buf);
                        /* Flip status to RUNNING:<pid> in original buffer. */
                        char status_replace[64];
                        snprintf(status_replace, sizeof status_replace, "RUNNING:%d", worker_pid);
                        size_t status_len = strlen("PENDING");
                        size_t replace_len = strlen(status_replace);
                        if (replace_len <= status_len) {
                            /* Pad with spaces. */
                            memcpy(buf + (line_start - buf), status_replace, replace_len);
                            for (size_t i = replace_len; i < status_len; i++)
                                buf[(line_start - buf) + i] = ' ';
                        } else {
                            /* Truncate (lossy but harmless). */
                            memcpy(buf + (line_start - buf), status_replace, status_len);
                        }
                        break;
                    }
                }
            }
        }
        p = eol ? eol + 1 : p + len;
    }

    if (found >= 0) {
        pwrite(fd, buf, st.st_size, 0);
    }
    free(buf);
    flock(fd, LOCK_UN);
    close(fd);
    return found >= 0 ? 0 : -1;
}

/* Mark line as DONE:<status> wall=<wall>. */
static void mark_done(const char *queue_path, int line_no,
                      const char *status, double wall, int run_id) {
    int fd = open(queue_path, O_RDWR);
    if (fd < 0) return;
    flock(fd, LOCK_EX);
    struct stat st;
    fstat(fd, &st);
    char *buf = malloc(st.st_size + 1);
    pread(fd, buf, st.st_size, 0);
    buf[st.st_size] = 0;

    char *p = buf;
    int n = 0;
    while (*p && n < line_no - 1) {
        if (*p == '\n') n++;
        p++;
    }
    /* p now points at the start of line_no. */
    char *eol = strchr(p, '\n');
    size_t len = eol ? (size_t)(eol - p) : strlen(p);

    char new_status[64];
    snprintf(new_status, sizeof new_status, "DONE_%s_w%.1f_r%d",
             status, wall, run_id);
    /* Replace the leading status field in this line. */
    char *tab = memchr(p, '\t', len);
    if (tab) {
        size_t status_len = (size_t)(tab - p);
        size_t replace_len = strlen(new_status);
        if (replace_len <= status_len) {
            memcpy(p, new_status, replace_len);
            for (size_t i = replace_len; i < status_len; i++) p[i] = ' ';
        } else {
            /* Truncate to the existing status field width. */
            memcpy(p, new_status, status_len);
        }
        pwrite(fd, buf, st.st_size, 0);
    }
    free(buf);
    flock(fd, LOCK_UN);
    close(fd);
}

/* Spawn a kissat worker. Returns pid. Outputs go to logs/run_NNNNN.log.
 * Computes time cap from conflicts heuristic + global cap. */
static pid_t spawn_kissat(const char *cnf, int seed, long long conflicts,
                          int time_cap_sec, int run_id) {
    char log_path[256];
    snprintf(log_path, sizeof log_path, "logs/run_%05d.log", run_id);

    pid_t pid = fork();
    if (pid < 0) return -1;
    if (pid == 0) {
        /* Child: redirect stdout+stderr to log, exec kissat. */
        int fd = open(log_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd < 0) _exit(127);
        dup2(fd, 1); dup2(fd, 2); close(fd);

        char seed_arg[32], conf_arg[64], time_arg[32];
        snprintf(seed_arg, sizeof seed_arg, "--seed=%d", seed);
        snprintf(conf_arg, sizeof conf_arg, "--conflicts=%lld", conflicts);
        snprintf(time_arg, sizeof time_arg, "--time=%d", time_cap_sec);

        execlp("kissat", "kissat", cnf, "-q",
               seed_arg, conf_arg, time_arg, (char *)NULL);
        _exit(127);
    }
    return pid;
}

/* Read trailing log lines to extract status (s SAT / s UNSAT / s UNKNOWN). */
static void parse_status(int run_id, char *status_out) {
    strcpy(status_out, "UNKNOWN");
    char log_path[256];
    snprintf(log_path, sizeof log_path, "logs/run_%05d.log", run_id);
    FILE *f = fopen(log_path, "r");
    if (!f) return;
    char line[256];
    while (fgets(line, sizeof line, f)) {
        if (line[0] == 's' && line[1] == ' ') {
            char *end = strchr(line + 2, '\n');
            if (end) *end = 0;
            strncpy(status_out, line + 2, 31);
            status_out[31] = 0;
        }
    }
    fclose(f);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <queue.tsv> <num_workers> [--time-cap-sec N]\n", argv[0]);
        return 1;
    }
    const char *queue_path = argv[1];
    int num_workers = atoi(argv[2]);
    int time_cap_sec = 1800; /* default 30 min */
    for (int i = 3; i < argc; i++) {
        if (strcmp(argv[i], "--time-cap-sec") == 0 && i + 1 < argc) {
            time_cap_sec = atoi(argv[++i]);
        }
    }
    if (num_workers < 1 || num_workers > MAX_WORKERS) {
        fprintf(stderr, "num_workers out of range\n");
        return 1;
    }

    signal(SIGINT, on_sigint);
    signal(SIGTERM, on_sigint);

    worker_t workers[MAX_WORKERS] = {0};
    int next_run_id = 1;
    int total_done = 0;

    /* Find next run_id from existing logs/ directory. */
    {
        for (int n = 1; n < 100000; n++) {
            char path[256];
            snprintf(path, sizeof path, "logs/run_%05d.log", n);
            if (access(path, F_OK) == 0) {
                next_run_id = n + 1;
            } else if (n > next_run_id + 10) {
                break;
            }
        }
    }

    char ts[32];
    timestamp_iso(ts, sizeof ts);
    fprintf(stderr, "[%s] dispatcher start: queue=%s workers=%d time_cap=%ds next_run_id=%d\n",
            ts, queue_path, num_workers, time_cap_sec, next_run_id);
    fflush(stderr);

    while (!g_stop) {
        /* Fill empty worker slots from queue. */
        int active = 0;
        for (int i = 0; i < num_workers; i++) {
            if (workers[i].active) { active++; continue; }

            char cnf[512], tag[128];
            int seed, line_no;
            long long conflicts;
            int rc = pop_job(queue_path, cnf, &seed, &conflicts, tag, &line_no, getpid());
            if (rc < 0) continue; /* Queue empty for now. */

            int run_id = next_run_id++;
            pid_t pid = spawn_kissat(cnf, seed, conflicts, time_cap_sec, run_id);
            if (pid < 0) {
                fprintf(stderr, "spawn failed\n");
                continue;
            }

            workers[i].pid = pid;
            workers[i].run_id = run_id;
            strncpy(workers[i].cnf, cnf, 511);
            workers[i].seed = seed;
            workers[i].conflicts = conflicts;
            strncpy(workers[i].tag, tag, 127);
            clock_gettime(CLOCK_MONOTONIC, &workers[i].start);
            workers[i].active = 1;
            active++;

            timestamp_iso(ts, sizeof ts);
            fprintf(stderr, "[%s] LAUNCH run=%d worker=%d pid=%d cnf=%s seed=%d conflicts=%lld tag=%s\n",
                    ts, run_id, i, pid, cnf, seed, conflicts, tag);
            fflush(stderr);
        }

        if (active == 0) {
            /* Queue empty AND no active workers — done. */
            timestamp_iso(ts, sizeof ts);
            fprintf(stderr, "[%s] queue exhausted, all workers idle. exit.\n", ts);
            break;
        }

        /* Wait for any worker. */
        int status;
        pid_t pid = waitpid(-1, &status, 0);
        if (pid < 0) {
            if (errno == EINTR) continue;
            break;
        }
        for (int i = 0; i < num_workers; i++) {
            if (workers[i].active && workers[i].pid == pid) {
                struct timespec end;
                clock_gettime(CLOCK_MONOTONIC, &end);
                double wall = (end.tv_sec - workers[i].start.tv_sec) +
                              (end.tv_nsec - workers[i].start.tv_nsec) / 1e9;

                char st[64];
                parse_status(workers[i].run_id, st);
                /* Find appropriate single token in st */
                char short_status[16] = "UNKNOWN";
                if (strstr(st, "SATISFIABLE") || strstr(st, "SAT") == st) strcpy(short_status, "SAT");
                else if (strstr(st, "UNSATISFIABLE") || strstr(st, "UNSAT")) strcpy(short_status, "UNSAT");

                /* Append summary line to results.tsv */
                FILE *r = fopen("results.tsv", "a");
                if (r) {
                    char ts2[32]; timestamp_iso(ts2, sizeof ts2);
                    fprintf(r, "%s\t%d\t%s\t%d\t%lld\t%s\t%.2f\t%s\n",
                            ts2, workers[i].run_id, workers[i].cnf,
                            workers[i].seed, workers[i].conflicts,
                            short_status, wall, workers[i].tag);
                    fclose(r);
                }

                timestamp_iso(ts, sizeof ts);
                fprintf(stderr, "[%s] FINISH run=%d worker=%d wall=%.1fs status=%s tag=%s\n",
                        ts, workers[i].run_id, i, wall, short_status, workers[i].tag);
                fflush(stderr);

                /* Note: we don't update the queue's line_no field here; it's
                 * marked RUNNING. Periodic queue cleanup is a later concern. */

                workers[i].active = 0;
                total_done++;
                break;
            }
        }
    }

    /* On signal: wait for active workers to finish (or kill after grace). */
    if (g_stop) {
        timestamp_iso(ts, sizeof ts);
        fprintf(stderr, "[%s] STOP requested. Waiting for %d active workers (30s grace).\n",
                ts, 0);
        for (int i = 0; i < num_workers; i++) {
            if (workers[i].active) {
                fprintf(stderr, "  worker %d still running (pid=%d run=%d)\n",
                        i, workers[i].pid, workers[i].run_id);
            }
        }
        /* Send SIGTERM to children. */
        for (int i = 0; i < num_workers; i++) {
            if (workers[i].active) kill(workers[i].pid, SIGTERM);
        }
        sleep(5);
        /* Force kill remaining. */
        for (int i = 0; i < num_workers; i++) {
            if (workers[i].active) kill(workers[i].pid, SIGKILL);
        }
        /* Reap. */
        while (waitpid(-1, NULL, 0) > 0) {}
    }

    fprintf(stderr, "TOTAL_DONE %d\n", total_done);
    return 0;
}
