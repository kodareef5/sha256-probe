/*
 * bdd_quotient_and_marginals.c
 *
 * Two analyses on the collision BDD (built from collision list):
 *
 * 1. COMPLETION QUOTIENT (GPT-5.4 Review 7):
 *    At each prefix depth d, count distinct residual sub-BDD node IDs.
 *    If quotient stays polynomial → constructive automaton may exist.
 *    If it blows up → polynomial BDD is not constructively accessible.
 *
 * 2. MARGINAL PROBABILITIES (Gemini Review 7):
 *    For each variable, compute P(var=1 | collision).
 *    Output as SAT phase hints: strongly biased vars get fixed phases.
 *
 * Reads collision coordinates from stdin (W1 only, cascade W2 implied).
 * Usage: cascade_dp_output | ./bdd_qm N
 * Compile: gcc -O3 -march=native -o bdd_qm bdd_quotient_and_marginals.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

static int N, NVARS;

/* ===== BDD core (same as bdd_from_collisions.c) ===== */
typedef struct { int var, lo, hi; } BDDNode;
#define BDD_FALSE 0
#define BDD_TRUE  1
static BDDNode *bdd_nodes; static int bdd_count, bdd_cap;

typedef struct { int var,lo,hi,node_id,next; } UEntry;
#define UHASH_BITS 22
#define UHASH_SIZE (1<<UHASH_BITS)
#define UHASH_MASK (UHASH_SIZE-1)
static int *uhash_table; static UEntry *uentry_pool; static int uentry_count, uentry_cap;

#define CHASH_BITS 22
#define CHASH_SIZE (1<<CHASH_BITS)
#define CHASH_MASK (CHASH_SIZE-1)
typedef struct { int op,f,g,result; } CEntry;
static CEntry *comp_table;

static void bdd_init(void) {
    bdd_cap = 1<<20; bdd_nodes = malloc(bdd_cap*sizeof(BDDNode));
    bdd_nodes[0] = (BDDNode){NVARS,0,0};
    bdd_nodes[1] = (BDDNode){NVARS,1,1};
    bdd_count = 2;
    uhash_table = malloc(UHASH_SIZE*sizeof(int));
    for (int i=0; i<UHASH_SIZE; i++) uhash_table[i] = -1;
    uentry_cap = 1<<20; uentry_pool = malloc(uentry_cap*sizeof(UEntry)); uentry_count = 0;
    comp_table = calloc(CHASH_SIZE, sizeof(CEntry));
    for (int i=0; i<CHASH_SIZE; i++) comp_table[i].op = -1;
}

static int bdd_make(int var, int lo, int hi) {
    if (lo == hi) return lo;
    uint32_t h = ((uint32_t)var*7919u + (uint32_t)lo*104729u + (uint32_t)hi*1000003u) & UHASH_MASK;
    for (int ei = uhash_table[h]; ei >= 0; ei = uentry_pool[ei].next) {
        UEntry *e = &uentry_pool[ei];
        if (e->var==var && e->lo==lo && e->hi==hi) return e->node_id;
    }
    if (bdd_count >= bdd_cap) { bdd_cap *= 2; bdd_nodes = realloc(bdd_nodes, bdd_cap*sizeof(BDDNode)); }
    int id = bdd_count++; bdd_nodes[id] = (BDDNode){var,lo,hi};
    if (uentry_count >= uentry_cap) { uentry_cap *= 2; uentry_pool = realloc(uentry_pool, uentry_cap*sizeof(UEntry)); }
    int nei = uentry_count++;
    uentry_pool[nei] = (UEntry){var,lo,hi,id,uhash_table[h]}; uhash_table[h] = nei;
    return id;
}

enum { OP_AND=0, OP_OR=1 };
static int bdd_apply(int op, int f, int g) {
    if (f<=1 && g<=1) return (op==OP_AND ? (f&g) : (f|g)) ? BDD_TRUE : BDD_FALSE;
    if (op==OP_AND) {
        if (f==BDD_FALSE || g==BDD_FALSE) return BDD_FALSE;
        if (f==BDD_TRUE) return g; if (g==BDD_TRUE) return f; if (f==g) return f;
    } else {
        if (f==BDD_TRUE || g==BDD_TRUE) return BDD_TRUE;
        if (f==BDD_FALSE) return g; if (g==BDD_FALSE) return f; if (f==g) return f;
    }
    if (f>g) { int t=f; f=g; g=t; }
    uint32_t ch = ((uint32_t)op*314159u + (uint32_t)f*271828u + (uint32_t)g*161803u) & CHASH_MASK;
    CEntry *ce = &comp_table[ch];
    if (ce->op==op && ce->f==f && ce->g==g) return ce->result;
    int vf = (f<=1) ? NVARS : bdd_nodes[f].var;
    int vg = (g<=1) ? NVARS : bdd_nodes[g].var;
    int v = (vf<vg) ? vf : vg;
    int fl = (vf==v) ? bdd_nodes[f].lo : f;
    int fh = (vf==v) ? bdd_nodes[f].hi : f;
    int gl = (vg==v) ? bdd_nodes[g].lo : g;
    int gh = (vg==v) ? bdd_nodes[g].hi : g;
    int r = bdd_make(v, bdd_apply(op,fl,gl), bdd_apply(op,fh,gh));
    *ce = (CEntry){op,f,g,r};
    return r;
}

static int make_point_bdd(uint32_t w57, uint32_t w58, uint32_t w59, uint32_t w60) {
    int node = BDD_TRUE;
    for (int bit = N-1; bit >= 0; bit--) {
        int b57 = (w57>>bit)&1, b58 = (w58>>bit)&1, b59 = (w59>>bit)&1, b60 = (w60>>bit)&1;
        int var_base = bit*4;
        node = bdd_make(var_base+3, b60?BDD_FALSE:node, b60?node:BDD_FALSE);
        node = bdd_make(var_base+2, b59?BDD_FALSE:node, b59?node:BDD_FALSE);
        node = bdd_make(var_base+1, b58?BDD_FALSE:node, b58?node:BDD_FALSE);
        node = bdd_make(var_base+0, b57?BDD_FALSE:node, b57?node:BDD_FALSE);
    }
    return node;
}

/* ===== Counting & analysis ===== */

static int *vis; static int vis_cap;
static int cnt_rec(int n) {
    if (n<=1 || vis[n]) return 0;
    vis[n] = 1;
    return 1 + cnt_rec(bdd_nodes[n].lo) + cnt_rec(bdd_nodes[n].hi);
}
static int count_nodes(int root) {
    if (vis_cap < bdd_count) { vis = realloc(vis, bdd_count*sizeof(int)); vis_cap = bdd_count; }
    memset(vis, 0, vis_cap*sizeof(int));
    return cnt_rec(root);
}

static double satcount(int node, int level) {
    if (node == BDD_FALSE) return 0.0;
    if (node == BDD_TRUE) return ldexp(1.0, NVARS - level);
    int v = bdd_nodes[node].var;
    return ldexp(1.0, v-level) * (satcount(bdd_nodes[node].lo, v+1) + satcount(bdd_nodes[node].hi, v+1));
}

/* ===== ANALYSIS 1: Completion Quotient ===== */

static void completion_quotient(int root) {
    printf("\n=== COMPLETION QUOTIENT (Distinct residual nodes per depth) ===\n\n");
    printf("Depth  QuotientWidth  VarName\n");

    /* BFS: at each depth d, collect set of BDD nodes reachable at that level.
       A node "at depth d" means: it's a child (lo or hi) of a node at depth d-1,
       where we skip levels if the BDD variable > d. */

    /* Simple approach: for each variable level, collect distinct node IDs
       that are the "residual" after fixing all variables < level. */

    /* Use a set (hash set) of node IDs per level */
    int max_set = bdd_count + 2;
    int *cur_set = malloc(max_set * sizeof(int));
    int *next_set = malloc(max_set * sizeof(int));
    char *in_set = calloc(bdd_count + 2, 1);
    int cur_size = 0, next_size = 0;

    /* Start with root */
    cur_set[0] = root; cur_size = 1;
    in_set[root] = 1;

    for (int depth = 0; depth < NVARS; depth++) {
        /* Report current quotient width */
        const char *word_names[] = {"W57","W58","W59","W60"};
        int word_idx = depth % 4;
        int bit_idx = depth / 4;
        printf(" %3d    %8d       %s[%d]\n", depth, cur_size, word_names[word_idx], bit_idx);

        /* Build next level: for each node in cur_set, follow lo and hi */
        next_size = 0;
        memset(in_set, 0, bdd_count + 2);

        for (int i = 0; i < cur_size; i++) {
            int n = cur_set[i];
            if (n <= 1) {
                /* Terminal: stays as-is */
                if (!in_set[n]) { next_set[next_size++] = n; in_set[n] = 1; }
                continue;
            }
            int v = bdd_nodes[n].var;
            if (v == depth) {
                /* This node branches at this depth: follow both children */
                int lo = bdd_nodes[n].lo, hi = bdd_nodes[n].hi;
                if (!in_set[lo]) { next_set[next_size++] = lo; in_set[lo] = 1; }
                if (!in_set[hi]) { next_set[next_size++] = hi; in_set[hi] = 1; }
            } else {
                /* Node's variable is deeper — it survives as-is (variable skipped) */
                if (!in_set[n]) { next_set[next_size++] = n; in_set[n] = 1; }
            }
        }

        /* Swap */
        int *tmp = cur_set; cur_set = next_set; next_set = tmp;
        cur_size = next_size;
    }

    printf(" %3d    %8d       (terminal)\n", NVARS, cur_size);

    /* Summary */
    printf("\nMax quotient width across all depths will show if this is polynomial or exponential.\n");

    free(cur_set); free(next_set); free(in_set);
}

/* ===== ANALYSIS 2: Marginal Probabilities ===== */

static double *path_count;  /* paths to TRUE from each node */
static double *mass;        /* probability mass arriving at each node */

static void compute_marginals(int root) {
    printf("\n=== MARGINAL PROBABILITIES (P(var=1) across all collisions) ===\n\n");

    /* Allocate arrays */
    path_count = calloc(bdd_count, sizeof(double));
    mass = calloc(bdd_count, sizeof(double));
    double *marginals = calloc(NVARS, sizeof(double));

    /* Pass 1: bottom-up path counting */
    path_count[BDD_FALSE] = 0.0;
    path_count[BDD_TRUE] = 1.0;
    /* Process nodes in reverse order (higher ID = higher in tree) */
    for (int i = bdd_count-1; i >= 2; i--) {
        int v = bdd_nodes[i].var;
        int lo = bdd_nodes[i].lo, hi = bdd_nodes[i].hi;
        /* Account for skipped variables: if child is at variable v', multiply by 2^(v'-v-1) */
        int lo_var = (lo <= 1) ? NVARS : bdd_nodes[lo].var;
        int hi_var = (hi <= 1) ? NVARS : bdd_nodes[hi].var;
        double lo_skip = ldexp(1.0, lo_var - v - 1);
        double hi_skip = ldexp(1.0, hi_var - v - 1);
        path_count[i] = path_count[lo] * lo_skip + path_count[hi] * hi_skip;
    }

    /* Pass 2: top-down marginal computation */
    mass[root] = 1.0;
    for (int i = 2; i < bdd_count; i++) {
        /* Process in order (lower ID = deeper, but we need top-down...) */
        /* Actually we need to process in topological order. Since BDD IDs are
           not guaranteed topological, let's use the variable ordering. */
    }

    /* Build topological order: sort nodes by variable (ascending = top-down) */
    int *topo = malloc(bdd_count * sizeof(int));
    int topo_n = 0;
    for (int i = 2; i < bdd_count; i++) topo[topo_n++] = i;
    /* Simple bucket sort by variable */
    int *buckets = calloc(NVARS + 1, sizeof(int));
    for (int i = 0; i < topo_n; i++) buckets[bdd_nodes[topo[i]].var]++;
    int *offsets = calloc(NVARS + 1, sizeof(int));
    for (int v = 1; v <= NVARS; v++) offsets[v] = offsets[v-1] + buckets[v-1];
    int *sorted = malloc(topo_n * sizeof(int));
    int *pos = calloc(NVARS + 1, sizeof(int));
    for (int i = 0; i < topo_n; i++) {
        int v = bdd_nodes[topo[i]].var;
        sorted[offsets[v] + pos[v]++] = topo[i];
    }

    /* Top-down marginal computation using sorted order */
    memset(mass, 0, bdd_count * sizeof(double));
    mass[root] = 1.0;

    for (int si = 0; si < topo_n; si++) {
        int i = sorted[si];
        if (mass[i] == 0.0) continue;
        int v = bdd_nodes[i].var;
        int lo = bdd_nodes[i].lo, hi = bdd_nodes[i].hi;
        double total = path_count[i];
        if (total == 0.0) continue;

        int lo_var = (lo <= 1) ? NVARS : bdd_nodes[lo].var;
        int hi_var = (hi <= 1) ? NVARS : bdd_nodes[hi].var;
        double lo_paths = path_count[lo] * ldexp(1.0, lo_var - v - 1);
        double hi_paths = path_count[hi] * ldexp(1.0, hi_var - v - 1);

        double hi_frac = hi_paths / total;
        marginals[v] += mass[i] * hi_frac;

        mass[lo] += mass[i] * (1.0 - hi_frac);
        mass[hi] += mass[i] * hi_frac;
    }

    free(topo); free(buckets); free(offsets); free(sorted); free(pos);

    /* Print marginals */
    const char *word_names[] = {"W57","W58","W59","W60"};
    printf("Var  Word     Bit  P(=1)    Bias     Phase\n");
    int n_biased = 0;
    for (int v = 0; v < NVARS; v++) {
        int word_idx = v % 4;
        int bit_idx = v / 4;
        double p = marginals[v];
        double bias = fabs(p - 0.5);
        const char *phase = (p > 0.85) ? "FORCE_1" : (p < 0.15) ? "FORCE_0" : (p > 0.65) ? "hint_1" : (p < 0.35) ? "hint_0" : "~50%";
        if (bias > 0.15) n_biased++;
        printf(" %2d  %s  %3d  %.4f  %+.4f  %s\n", v, word_names[word_idx], bit_idx, p, p-0.5, phase);
    }
    printf("\nBiased variables (>15%% from 0.5): %d/%d\n", n_biased, NVARS);
    printf("These can be used as Kissat --phase hints for guided search.\n");

    free(path_count); free(mass); free(marginals);
}

/* ===== MAIN ===== */

int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    struct timespec t0; clock_gettime(CLOCK_MONOTONIC, &t0);

    N = (argc > 1) ? atoi(argv[1]) : 8;
    if (N < 2 || N > 32) { printf("N must be 2..32\n"); return 1; }
    NVARS = 4*N;

    printf("=== BDD Quotient + Marginals, N=%d (%d variables) ===\n\n", N, NVARS);
    bdd_init();

    /* Read collisions */
    int collision_bdd = BDD_FALSE;
    int ncoll = 0;
    char line[256];
    uint32_t w57, w58, w59, w60;

    while (fgets(line, sizeof(line), stdin)) {
        if (sscanf(line, "COLL %x %x %x %x", &w57, &w58, &w59, &w60) == 4 ||
            sscanf(line, "%x %x %x %x", &w57, &w58, &w59, &w60) == 4) {
            int point = make_point_bdd(w57, w58, w59, w60);
            collision_bdd = bdd_apply(OP_OR, collision_bdd, point);
            ncoll++;
            if (ncoll % 100 == 0) fprintf(stderr, "  %d collisions...\n", ncoll);
        }
    }

    struct timespec t1; clock_gettime(CLOCK_MONOTONIC, &t1);
    double build_time = (t1.tv_sec-t0.tv_sec) + (t1.tv_nsec-t0.tv_nsec)/1e9;

    int final_nodes = count_nodes(collision_bdd);
    double sat = satcount(collision_bdd, 0);

    printf("Collisions: %d, BDD nodes: %d, satcount: %.0f, match: %s\n",
           ncoll, final_nodes, sat, (ncoll == (int)sat) ? "YES" : "NO");
    printf("Build time: %.2fs\n", build_time);

    /* Analysis 1: Completion Quotient */
    completion_quotient(collision_bdd);

    /* Analysis 2: Marginal Probabilities */
    compute_marginals(collision_bdd);

    printf("\nDone.\n");
    return 0;
}
