/*
 * block2_absorber_probe.c
 *
 * Stochastic second-block absorber probe for block2_wang.
 *
 * This is not a certificate generator. It is a fast triage tool for asking:
 * given one of the block-1 residual vectors already in the corpus, can a
 * free second-block message difference reduce that IV/state difference over
 * the first R SHA-256 rounds?
 *
 * Input is the existing JSONL residual corpus, e.g.
 *   residuals/F28_deep_corpus.jsonl
 *
 * The tool extracts diff63 as an XOR IV difference, sets
 *   IV2 = IV1 xor diff63,
 * keeps M1 fixed at zero, mutates M2[0..15], and hill-climbs the XOR
 * state-difference HW after `rounds` rounds. That is deliberately modest:
 * it is a cheap "is this residual absorbable at all?" probe, not a full
 * Wang bitcondition engine.
 *
 * Build:
 *   gcc -O3 -march=native -Wall -Wextra \
 *     headline_hunt/bets/block2_wang/prototypes/block2_absorber_probe.c \
 *     -o /tmp/block2_absorber_probe
 *
 * Example:
 *   /tmp/block2_absorber_probe \
 *     headline_hunt/bets/block2_wang/residuals/F28_deep_corpus.jsonl \
 *     12 200000 0x1234 20
 *
 * Args:
 *   corpus.jsonl rounds iterations seed max_records
 */

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint32_t u32;
typedef uint64_t u64;

enum { NWORDS = 16, NST = 8, MAX_LINE = 8192, MAX_ID = 160 };

static const u32 K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

static const u32 IV[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

typedef struct {
    char candidate_id[MAX_ID];
    int hw_total;
    u32 diff[8];
} residual_t;

typedef struct {
    int best_hw;
    int start_hw;
    u32 best_m2[16];
    u32 best_state_diff[8];
} probe_result_t;

static inline u32 ror32(u32 x, int n) {
    return (x >> n) | (x << (32 - n));
}

static inline u32 Ch(u32 e, u32 f, u32 g) {
    return (e & f) ^ ((~e) & g);
}

static inline u32 Maj(u32 a, u32 b, u32 c) {
    return (a & b) ^ (a & c) ^ (b & c);
}

static inline u32 Sigma0(u32 a) {
    return ror32(a, 2) ^ ror32(a, 13) ^ ror32(a, 22);
}

static inline u32 Sigma1(u32 e) {
    return ror32(e, 6) ^ ror32(e, 11) ^ ror32(e, 25);
}

static inline u32 sigma0(u32 x) {
    return ror32(x, 7) ^ ror32(x, 18) ^ (x >> 3);
}

static inline u32 sigma1(u32 x) {
    return ror32(x, 17) ^ ror32(x, 19) ^ (x >> 10);
}

static inline u32 rng32(u32 *s) {
    u32 x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x ? x : 0x9e3779b9U;
    return *s;
}

static int hw_state_xor(const u32 a[8], const u32 b[8], u32 out_diff[8]) {
    int hw = 0;
    for (int i = 0; i < 8; i++) {
        u32 d = a[i] ^ b[i];
        if (out_diff) out_diff[i] = d;
        hw += __builtin_popcount(d);
    }
    return hw;
}

static void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

static void expand_schedule(const u32 m[16], u32 W[64]) {
    for (int i = 0; i < 16; i++) W[i] = m[i];
    for (int i = 16; i < 64; i++)
        W[i] = sigma1(W[i - 2]) + W[i - 7] + sigma0(W[i - 15]) + W[i - 16];
}

static int eval_message(const u32 iv1[8], const u32 iv2[8],
                        const u32 m2[16], int rounds, u32 out_diff[8]) {
    u32 W1[64], W2[64];
    u32 M1[16] = {0};
    expand_schedule(M1, W1);
    expand_schedule(m2, W2);

    u32 s1[8], s2[8];
    memcpy(s1, iv1, sizeof(u32) * 8);
    memcpy(s2, iv2, sizeof(u32) * 8);
    for (int r = 0; r < rounds; r++) {
        sha_round(s1, K[r], W1[r]);
        sha_round(s2, K[r], W2[r]);
    }
    return hw_state_xor(s1, s2, out_diff);
}

static int extract_json_string(const char *line, const char *key,
                               char *out, size_t out_sz) {
    const char *p = strstr(line, key);
    if (!p) return 0;
    p = strchr(p, ':');
    if (!p) return 0;
    p++;
    while (*p && isspace((unsigned char)*p)) p++;
    if (*p != '"') return 0;
    p++;
    const char *q = strchr(p, '"');
    if (!q) return 0;
    size_t n = (size_t)(q - p);
    if (n >= out_sz) n = out_sz - 1;
    memcpy(out, p, n);
    out[n] = '\0';
    return 1;
}

static int extract_json_int(const char *line, const char *key, int *out) {
    const char *p = strstr(line, key);
    if (!p) return 0;
    p = strchr(p, ':');
    if (!p) return 0;
    *out = (int)strtol(p + 1, NULL, 10);
    return 1;
}

static int parse_diff63(const char *line, u32 diff[8]) {
    const char *p = strstr(line, "\"diff63\"");
    if (!p) return 0;
    p = strchr(p, '[');
    if (!p) return 0;
    for (int i = 0; i < 8; i++) {
        const char *h = strstr(p, "0x");
        if (!h) return 0;
        diff[i] = (u32)strtoul(h, NULL, 16);
        p = h + 2;
    }
    return 1;
}

static int parse_residual_line(const char *line, residual_t *r) {
    memset(r, 0, sizeof(*r));
    strcpy(r->candidate_id, "unknown");
    extract_json_string(line, "\"candidate_id\"", r->candidate_id, sizeof(r->candidate_id));
    extract_json_int(line, "\"hw_total\"", &r->hw_total);
    return parse_diff63(line, r->diff);
}

static void run_probe(const residual_t *res, int rounds, u64 iterations,
                      u32 seed, probe_result_t *out) {
    u32 iv1[8], iv2[8], cur_m2[16] = {0}, cur_diff[8], best_diff[8];
    for (int i = 0; i < 8; i++) {
        iv1[i] = IV[i];
        iv2[i] = IV[i] ^ res->diff[i];
    }

    int cur_hw = eval_message(iv1, iv2, cur_m2, rounds, cur_diff);
    int best_hw = cur_hw;
    u32 best_m2[16];
    memcpy(best_m2, cur_m2, sizeof(best_m2));
    memcpy(best_diff, cur_diff, sizeof(best_diff));

    u32 rng = seed ? seed : 0x12345678U;
    for (u64 it = 0; it < iterations; it++) {
        int word = (int)(rng32(&rng) & 15U);
        int bit = (int)(rng32(&rng) & 31U);
        u32 mask = (u32)1 << bit;
        cur_m2[word] ^= mask;

        int next_hw = eval_message(iv1, iv2, cur_m2, rounds, cur_diff);
        int accept = 0;
        if (next_hw <= cur_hw) {
            accept = 1;
        } else {
            int slack = next_hw - cur_hw;
            u32 gate = rng32(&rng) & 1023U;
            accept = (slack <= 2 && gate == 0);
        }

        if (accept) {
            cur_hw = next_hw;
            if (next_hw < best_hw) {
                best_hw = next_hw;
                memcpy(best_m2, cur_m2, sizeof(best_m2));
                memcpy(best_diff, cur_diff, sizeof(best_diff));
            }
        } else {
            cur_m2[word] ^= mask;
        }
    }

    out->start_hw = eval_message(iv1, iv2, (u32[16]){0}, rounds, NULL);
    out->best_hw = best_hw;
    memcpy(out->best_m2, best_m2, sizeof(best_m2));
    memcpy(out->best_state_diff, best_diff, sizeof(best_diff));
}

static void print_words16(const u32 w[16]) {
    for (int i = 0; i < 16; i++) {
        if (i) putchar(',');
        printf("0x%08x", w[i]);
    }
}

static void print_words8(const u32 w[8]) {
    for (int i = 0; i < 8; i++) {
        if (i) putchar(',');
        printf("0x%08x", w[i]);
    }
}

int main(int argc, char **argv) {
    if (argc < 6) {
        fprintf(stderr, "Usage: %s corpus.jsonl rounds iterations seed max_records\n", argv[0]);
        return 2;
    }

    const char *path = argv[1];
    int rounds = atoi(argv[2]);
    u64 iterations = strtoull(argv[3], NULL, 0);
    u32 seed = (u32)strtoul(argv[4], NULL, 0);
    int max_records = atoi(argv[5]);
    if (rounds < 1 || rounds > 64 || max_records < 1) {
        fprintf(stderr, "bad rounds or max_records\n");
        return 2;
    }

    FILE *f = fopen(path, "r");
    if (!f) {
        perror(path);
        return 1;
    }

    printf("record,candidate_id,input_hw,rounds,start_hw,best_hw,improvement,best_m2,best_state_diff\n");
    char line[MAX_LINE];
    int seen = 0, used = 0;
    while (fgets(line, sizeof(line), f)) {
        residual_t res;
        seen++;
        if (!parse_residual_line(line, &res)) continue;

        probe_result_t pr;
        run_probe(&res, rounds, iterations, seed ^ (u32)(0x9e3779b9U * (u32)seen), &pr);

        printf("%d,%s,%d,%d,%d,%d,%d,\"",
               seen, res.candidate_id, res.hw_total, rounds, pr.start_hw,
               pr.best_hw, pr.start_hw - pr.best_hw);
        print_words16(pr.best_m2);
        printf("\",\"");
        print_words8(pr.best_state_diff);
        printf("\"\n");

        used++;
        if (used >= max_records) break;
    }
    fclose(f);

    fprintf(stderr, "processed %d usable residual records from %s\n", used, path);
    return 0;
}
