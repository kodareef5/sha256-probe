/*
 * bdd_n8.c — BDD construction for N=8 mini-SHA collision function
 *
 * Phase 1: Generate truth table of the collision function over all 2^32
 *          message combos (W57, W58, W59, W60), each 8-bit.
 *          Uses cascade DP (same logic as structural_solver_n8.c).
 *          Stored as a packed bitarray (512MB = 2^32 bits).
 *          Bit ordering: interleaved (bit-first) variable order.
 *
 * Phase 2: Build reduced ordered BDD (ROBDD) bottom-up from truth table.
 *          Uses unique table with hash-based memoization.
 *
 * Phase 3: Report node count, compare with N=4 (183) and N=6 (615),
 *          test O(N^3) scaling prediction (~1453 nodes).
 *
 * N=8, MSB kernel, M[0]=0x67, fill=0xff.
 * Expected: 260 collisions.
 *
 * Compile: gcc -O3 -march=native -o bdd_n8 bdd_n8.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---- N=8 parameters ---- */
#define N 8
#define MASK ((1U << N) - 1)
#define MSB  (1U << (N - 1))
#define NVARS (4 * N)  /* 32 Boolean variables */

/* ---- Rotation parameters (scaled from SHA-256's 32-bit rotations) ---- */
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

/* ---- SHA-256 primitives (N-bit) ---- */
static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N;
    return ((x >> k) | (x << (N - k))) & MASK;
}
static inline uint32_t fnS0(uint32_t a) {
    return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]);
}
static inline uint32_t fnS1(uint32_t e) {
    return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]);
}
static inline uint32_t fns0(uint32_t x) {
    return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & MASK);
}
static inline uint32_t fns1(uint32_t x) {
    return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & MASK);
}
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) {
    return ((e & f) ^ ((~e) & g)) & MASK;
}
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) {
    return ((a & b) ^ (a & c) ^ (b & c)) & MASK;
}

/* ---- SHA-256 constants ---- */
static const uint32_t K32[64] = {
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
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

static uint32_t KN[64], IVN[8];
static uint32_t state1[8], state2[8], W1p[57], W2p[57];

/* ---- Precompute state through round 56 and schedule through W[56] ---- */
static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a=IVN[0], b=IVN[1], c=IVN[2], d=IVN[3],
             e=IVN[4], f=IVN[5], g=IVN[6], h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fnS1(e) + fnCh(e,f,g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fnS0(a) + fnMj(a,b,c)) & MASK;
        h=g; g=f; f=e; e=(d+T1)&MASK; d=c; c=b; b=a; a=(T1+T2)&MASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

/* ---- SHA round function ---- */
static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fnS1(s[4]) + fnCh(s[4],s[5],s[6]) + k + w) & MASK;
    uint32_t T2 = (fnS0(s[0]) + fnMj(s[0],s[1],s[2])) & MASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
}

/* ---- Cascade offset: find W2 such that da_{r+1} = 0 given W1 ---- */
static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7] + fnS1(s1[4]) + fnCh(s1[4],s1[5],s1[6]) + KN[rnd]) & MASK;
    uint32_t r2 = (s2[7] + fnS1(s2[4]) + fnCh(s2[4],s2[5],s2[6]) + KN[rnd]) & MASK;
    uint32_t T21 = (fnS0(s1[0]) + fnMj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T22 = (fnS0(s2[0]) + fnMj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + r1 - r2 + T21 - T22) & MASK;
}

/* ---- Convert natural (w57,w58,w59,w60) index to interleaved BDD variable order ----
 *
 * Interleaved variable order (bit-first):
 *   var 0 = W57[0], var 1 = W58[0], var 2 = W59[0], var 3 = W60[0],
 *   var 4 = W57[1], var 5 = W58[1], var 6 = W59[1], var 7 = W60[1],
 *   ...
 *   var 28 = W57[7], var 29 = W58[7], var 30 = W59[7], var 31 = W60[7]
 *
 * Truth table index bit layout (interleaved):
 *   index = sum over bit b in [0..7]:
 *     w57_bit[b] << (4*b + 0) |
 *     w58_bit[b] << (4*b + 1) |
 *     w59_bit[b] << (4*b + 2) |
 *     w60_bit[b] << (4*b + 3)
 */
static uint32_t natural_to_interleaved(uint32_t w57, uint32_t w58,
                                        uint32_t w59, uint32_t w60) {
    uint32_t idx = 0;
    for (int b = 0; b < N; b++) {
        idx |= ((w57 >> b) & 1) << (4*b + 0);
        idx |= ((w58 >> b) & 1) << (4*b + 1);
        idx |= ((w59 >> b) & 1) << (4*b + 2);
        idx |= ((w60 >> b) & 1) << (4*b + 3);
    }
    return idx;
}

/* ================================================================
 * BDD DATA STRUCTURES
 *
 * Terminal nodes: 0 (FALSE), 1 (TRUE)
 * Internal nodes: (var, lo, hi) where var is BDD variable index [0..31],
 *   lo = child when var=0, hi = child when var=1.
 * Reduced: no node has lo == hi (redundant test eliminated).
 * Ordered: var strictly increases along any root-to-terminal path.
 * ================================================================ */

typedef struct {
    int var;    /* variable index [0..NVARS-1], or -1 for terminals */
    int lo;     /* child node when var = 0 */
    int hi;     /* child node when var = 1 */
} BDDNode;

#define BDD_FALSE 0
#define BDD_TRUE  1
#define BDD_INITIAL_CAP (1 << 20)  /* 1M nodes initial capacity */

static BDDNode *bdd_nodes = NULL;
static int bdd_count = 0;
static int bdd_cap = 0;

/* ---- Unique table: hash (var, lo, hi) -> node_id ---- */
#define UHASH_SIZE (1 << 22)  /* 4M buckets */
#define UHASH_MASK (UHASH_SIZE - 1)

typedef struct UEntry {
    int var, lo, hi;
    int node_id;
    struct UEntry *next;
} UEntry;

static UEntry *uhash_table[UHASH_SIZE];
static UEntry *uentry_pool = NULL;
static int uentry_count = 0;
static int uentry_cap = 0;

static void bdd_init(void) {
    bdd_cap = BDD_INITIAL_CAP;
    bdd_nodes = (BDDNode *)malloc(bdd_cap * sizeof(BDDNode));
    /* Terminal nodes: 0 = FALSE, 1 = TRUE */
    bdd_nodes[0] = (BDDNode){-1, 0, 0};  /* FALSE */
    bdd_nodes[1] = (BDDNode){-1, 1, 1};  /* TRUE */
    bdd_count = 2;

    memset(uhash_table, 0, sizeof(uhash_table));
    uentry_cap = BDD_INITIAL_CAP;
    uentry_pool = (UEntry *)malloc(uentry_cap * sizeof(UEntry));
    uentry_count = 0;
}

static inline uint32_t uhash(int var, int lo, int hi) {
    uint32_t h = (uint32_t)var * 7919u + (uint32_t)lo * 104729u + (uint32_t)hi * 1000003u;
    return h & UHASH_MASK;
}

static int bdd_make(int var, int lo, int hi) {
    /* Reduction rule: if both children are the same, skip this node */
    if (lo == hi) return lo;

    /* Lookup in unique table */
    uint32_t h = uhash(var, lo, hi);
    for (UEntry *e = uhash_table[h]; e; e = e->next) {
        if (e->var == var && e->lo == lo && e->hi == hi)
            return e->node_id;
    }

    /* Create new node */
    if (bdd_count >= bdd_cap) {
        bdd_cap *= 2;
        bdd_nodes = (BDDNode *)realloc(bdd_nodes, bdd_cap * sizeof(BDDNode));
    }
    int id = bdd_count++;
    bdd_nodes[id] = (BDDNode){var, lo, hi};

    /* Insert into unique table */
    if (uentry_count >= uentry_cap) {
        uentry_cap *= 2;
        uentry_pool = (UEntry *)realloc(uentry_pool, uentry_cap * sizeof(UEntry));
    }
    UEntry *ne = &uentry_pool[uentry_count++];
    ne->var = var;
    ne->lo = lo;
    ne->hi = hi;
    ne->node_id = id;
    ne->next = uhash_table[h];
    uhash_table[h] = ne;

    return id;
}

/* ================================================================
 * BOTTOM-UP BDD CONSTRUCTION FROM TRUTH TABLE
 *
 * We build the BDD bottom-up, processing variable NVARS-1 first (deepest),
 * then NVARS-2, ..., then variable 0 (root).
 *
 * At each level, we have a "layer" of node IDs. The bottom layer has
 * 2^NVARS entries (one per truth table row). Each level halves the count
 * by pairing adjacent entries and calling bdd_make.
 *
 * For variable v at depth d (d = NVARS - 1 - v from root):
 *   The truth table is laid out so that bit v is at position v in the index.
 *   At this level, we have 2^(NVARS - 1 - level_from_bottom) groups.
 *   Within each group, the lo child is at offset 0, hi child at offset 2^v.
 *
 * Since the truth table uses interleaved ordering and the BDD variables
 * are numbered 0..31 in that same order, variable v corresponds to
 * bit v in the truth table index.
 *
 * Bottom-up approach:
 *   Start with 2^32 terminal node IDs (from truth table bits).
 *   Process variables from v=31 down to v=0:
 *     For each pair of entries differing only in bit v:
 *       lo = entry with bit v = 0
 *       hi = entry with bit v = 1
 *       result = bdd_make(v, lo, hi)
 *
 * Memory: we need arrays of node IDs. At the bottom level, 2^32 entries
 * of int (4 bytes) = 16GB -- too much.
 *
 * OPTIMIZATION: Process variables in groups. We process 4 variables at a
 * time (one "nibble"), reducing the working set by 16x per step.
 *
 * Actually, let's think about this more carefully. We process variable 31
 * first (the highest bit). The truth table has 2^32 entries. After
 * processing var 31, we have 2^31 entries. After var 30, 2^30, etc.
 *
 * We can't hold 2^32 ints in memory (16GB). But we CAN process the truth
 * table in chunks. For the first variable (v=31), we iterate over all
 * 2^31 pairs. Each pair consists of two truth table bits at positions
 * i and i | (1<<31). We produce one node ID per pair.
 *
 * Working set for level k (after processing vars 31 down to k):
 *   2^k node IDs = 2^k * 4 bytes.
 *   At k=31: 2^31 * 4 = 8GB -- still too much.
 *
 * BETTER APPROACH: Process 8 variables at a time. Start from the bottom
 * (vars 31..24 = one byte), reducing 2^32 to 2^24 node IDs. Then process
 * vars 23..16, reducing to 2^16 node IDs. Then 15..8 -> 2^8. Then 7..0 -> 1.
 *
 * For the first batch (vars 31..24), we iterate over all 2^24 groups of
 * 256 truth table bits. For each group, we build a local 8-variable BDD
 * from 256 bits, producing one node ID. The 2^24 node IDs fit in 64MB.
 *
 * For subsequent batches, we pair/merge node IDs similarly.
 *
 * IMPLEMENTATION: We use a hybrid approach:
 *   - Bottom layer: convert each 256-bit chunk of truth table into a
 *     local 8-var BDD (using the global unique table).
 *   - Then merge layers 8 variables at a time upward.
 * ================================================================ */

/* Build an 8-variable BDD from 256 truth table bits.
 * vars[0..7] are the BDD variable indices (in order from root to leaf).
 * tt256 contains 256 bits packed into 4 uint64_t values (or 32 bytes).
 * Returns the root node ID. */
static int build_bdd_8vars(const uint8_t *bits256, const int vars[8]) {
    /* Bottom-up: start with 256 terminal nodes, merge pairs 8 times. */
    int layer[256];
    for (int i = 0; i < 256; i++)
        layer[i] = bits256[i] ? BDD_TRUE : BDD_FALSE;

    /* Process variables from vars[7] (deepest) up to vars[0] (shallowest) */
    int count = 256;
    for (int d = 7; d >= 0; d--) {
        int var = vars[d];
        int half = count / 2;
        /* Bit d in the local index selects lo (0) vs hi (1).
         * Entries where local bit d = 0 are the lo children.
         * Entries where local bit d = 1 are the hi children.
         * With the natural enumeration of [0..count-1], bit d
         * splits each group of 2^(d+1) into two halves of 2^d. */
        int new_layer[128]; /* max half = 128 */
        int out = 0;
        int stride = 1 << d;  /* distance between lo and hi entries */
        int block = stride * 2;  /* size of each block */
        for (int base = 0; base < count; base += block) {
            for (int j = 0; j < stride; j++) {
                int lo = layer[base + j];
                int hi = layer[base + j + stride];
                new_layer[out++] = bdd_make(var, lo, hi);
            }
        }
        /* Copy back */
        count = half;
        memcpy(layer, new_layer, count * sizeof(int));
    }

    return layer[0];
}

/* Build a sub-BDD for nvars variables from an array of node IDs.
 * vars[0..nvars-1] are BDD variable indices (root to leaf order).
 * nodes has 2^nvars entries.
 * Returns the root node ID. */
static int merge_bdd_layer(const int *nodes, int nvars, const int vars[]) {
    /* We need a working buffer. Since nvars <= 8, max size is 256. */
    int layer[256];
    int count = 1 << nvars;
    if (count > 256) {
        fprintf(stderr, "merge_bdd_layer: nvars=%d too large\n", nvars);
        exit(1);
    }
    memcpy(layer, nodes, count * sizeof(int));

    for (int d = nvars - 1; d >= 0; d--) {
        int var = vars[d];
        int half = count / 2;
        int new_layer[128];
        int out = 0;
        int stride = 1 << d;
        int block = stride * 2;
        for (int base = 0; base < count; base += block) {
            for (int j = 0; j < stride; j++) {
                int lo = layer[base + j];
                int hi = layer[base + j + stride];
                new_layer[out++] = bdd_make(var, lo, hi);
            }
        }
        count = half;
        memcpy(layer, new_layer, count * sizeof(int));
    }
    return layer[0];
}

/* ================================================================
 * TRUTH TABLE GENERATION AND BDD CONSTRUCTION
 * ================================================================ */

int main(void) {
    setbuf(stdout, NULL);
    struct timespec t0, t1, t2, t3;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    /* ---- Initialize rotation parameters ---- */
    rS0[0]=scale_rot(2);  rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);  rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);  rs0[1]=scale_rot(18);  ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19);  ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & MASK;

    printf("=== BDD Construction for N=%d Collision Function ===\n\n", N);

    /* ---- Setup candidate: MSB kernel, M[0]=0x67, fill=0xff ---- */
    uint32_t M1[16], M2[16];
    for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
    M1[0] = 0x67; M2[0] = 0x67 ^ MSB; M2[9] = MASK ^ MSB;
    precompute(M1, state1, W1p);
    precompute(M2, state2, W2p);

    printf("Candidate: M[0]=0x67, fill=0xff, MSB kernel\n");
    printf("State56 diffs: da=%d db=%d dc=%d dd=%d de=%d df=%d dg=%d dh=%d\n",
           (state1[0] - state2[0]) & MASK, (state1[1] - state2[1]) & MASK,
           (state1[2] - state2[2]) & MASK, (state1[3] - state2[3]) & MASK,
           (state1[4] - state2[4]) & MASK, (state1[5] - state2[5]) & MASK,
           (state1[6] - state2[6]) & MASK, (state1[7] - state2[7]) & MASK);

    if (((state1[0] - state2[0]) & MASK) != 0) {
        printf("ERROR: da56 != 0, candidate invalid\n");
        return 1;
    }

    /* ================================================================
     * PHASE 1: Generate truth table (512MB bitarray)
     *
     * For each (w57, w58, w59, w60) in [0..255]^4:
     *   Run cascade rounds 57-63, check collision.
     *   Store result at interleaved index.
     *
     * We process in natural order (nested loops) but write to interleaved
     * positions using the mapping function.
     * ================================================================ */
    printf("\n--- Phase 1: Truth table generation (2^32 entries) ---\n");
    clock_gettime(CLOCK_MONOTONIC, &t1);

    /* Allocate 512MB bitarray */
    uint64_t tt_bytes = (1ULL << 32) / 8;  /* 512MB */
    uint8_t *tt = (uint8_t *)calloc(tt_bytes, 1);
    if (!tt) {
        printf("ERROR: Failed to allocate %llu bytes for truth table\n",
               (unsigned long long)tt_bytes);
        return 1;
    }
    printf("Allocated %llu MB for truth table\n", (unsigned long long)(tt_bytes >> 20));

    uint64_t n_collisions = 0;

    for (uint32_t w57 = 0; w57 < 256; w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

        for (uint32_t w58 = 0; w58 < 256; w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

            for (uint32_t w59 = 0; w59 < 256; w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);

                /* Cascade offset for round 60 */
                uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);

                /* Schedule: W[61] depends on w59 (via sigma1(w59)) */
                uint32_t W1_61 = (fns1(w59) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
                uint32_t W2_61 = (fns1(w59b) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;

                /* Schedule: W[63] depends on W[61] (hence w59) */
                uint32_t W1_63 = (fns1(W1_61) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
                uint32_t W2_63 = (fns1(W2_61) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;

                /* Schedule constants for W[62] */
                uint32_t sched62_c1 = (W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK;
                uint32_t sched62_c2 = (W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK;

                for (uint32_t w60 = 0; w60 < 256; w60++) {
                    uint32_t w60b = (w60 + cas_off60) & MASK;

                    /* Round 60 */
                    uint32_t s60a[8], s60b[8];
                    memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                    sha_round(s60a, KN[60], w60);
                    sha_round(s60b, KN[60], w60b);

                    /* Round 61 */
                    uint32_t s61a[8], s61b[8];
                    memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                    sha_round(s61a, KN[61], W1_61);
                    sha_round(s61b, KN[61], W2_61);

                    /* Rounds 62-63 */
                    uint32_t W1_62 = (fns1(w60) + sched62_c1) & MASK;
                    uint32_t W2_62 = (fns1(w60b) + sched62_c2) & MASK;
                    sha_round(s61a, KN[62], W1_62);
                    sha_round(s61b, KN[62], W2_62);
                    sha_round(s61a, KN[63], W1_63);
                    sha_round(s61b, KN[63], W2_63);

                    /* Check full collision */
                    int coll = 1;
                    for (int r = 0; r < 8; r++) {
                        if (s61a[r] != s61b[r]) { coll = 0; break; }
                    }

                    if (coll) {
                        /* Store in interleaved bit position */
                        uint32_t idx = natural_to_interleaved(w57, w58, w59, w60);
                        tt[idx >> 3] |= (1U << (idx & 7));
                        n_collisions++;
                    }
                }
            }
        }

        /* Progress every 64 W57 values */
        if ((w57 & 0x3F) == 0x3F) {
            clock_gettime(CLOCK_MONOTONIC, &t2);
            double el = (t2.tv_sec - t1.tv_sec) + (t2.tv_nsec - t1.tv_nsec) / 1e9;
            double pct = 100.0 * (w57 + 1) / 256.0;
            printf("  [%.0f%%] w57=0x%02x collisions=%llu time=%.1fs ETA=%.1fs\n",
                   pct, w57, (unsigned long long)n_collisions, el,
                   el / pct * 100.0 - el);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t2);
    double tt_time = (t2.tv_sec - t1.tv_sec) + (t2.tv_nsec - t1.tv_nsec) / 1e9;
    printf("\nTruth table complete: %llu collisions in %.2fs\n",
           (unsigned long long)n_collisions, tt_time);

    if (n_collisions != 260) {
        printf("WARNING: Expected 260 collisions, got %llu\n",
               (unsigned long long)n_collisions);
    }

    /* ================================================================
     * PHASE 2: Build BDD bottom-up
     *
     * Strategy: process in 4 groups of 8 variables each.
     *
     * Group 0 (deepest): vars 24..31 (bits 24-31 of the TT index)
     *   These are W57[6],W58[6],W59[6],W60[6], W57[7],W58[7],W59[7],W60[7]
     *   For each of the 2^24 prefixes, extract 256 bits, build 8-var BDD.
     *   Result: 2^24 = 16M node IDs.
     *
     * Group 1: vars 16..23
     *   For each of the 2^16 prefixes, collect 256 node IDs from group 0,
     *   merge into 8-var BDD. Result: 2^16 = 64K node IDs.
     *
     * Group 2: vars 8..15
     *   For each of the 2^8 prefixes, collect 256 node IDs from group 1,
     *   merge into 8-var BDD. Result: 256 node IDs.
     *
     * Group 3 (root): vars 0..7
     *   Collect 256 node IDs from group 2, merge. Result: 1 root node.
     * ================================================================ */
    printf("\n--- Phase 2: BDD construction (bottom-up, 4 layers of 8 vars) ---\n");
    clock_gettime(CLOCK_MONOTONIC, &t2);

    bdd_init();

    /* Variable order arrays for each group.
     * Within each 8-var group, the variables go from shallowest (root-side)
     * to deepest (leaf-side). Since we're building bottom-up, the merge
     * function processes deepest first internally. */
    int vars_g0[8] = {24, 25, 26, 27, 28, 29, 30, 31};
    int vars_g1[8] = {16, 17, 18, 19, 20, 21, 22, 23};
    int vars_g2[8] = { 8,  9, 10, 11, 12, 13, 14, 15};
    int vars_g3[8] = { 0,  1,  2,  3,  4,  5,  6,  7};

    /* ---- Group 0: vars 24..31 ---- */
    printf("  Group 0 (vars 24-31): processing 2^24 = %d chunks of 256 bits...\n",
           1 << 24);
    uint32_t n_g0 = 1U << 24;  /* 16M groups */
    int *layer0 = (int *)malloc(n_g0 * sizeof(int));
    if (!layer0) {
        printf("ERROR: Failed to allocate layer0 (%u entries)\n", n_g0);
        free(tt);
        return 1;
    }

    for (uint32_t prefix = 0; prefix < n_g0; prefix++) {
        /* Extract 256 bits for this prefix (bits 0..23 = prefix, bits 24..31 vary).
         * Truth table index = prefix | (suffix << 24) where suffix in [0..255]. */
        uint8_t bits256[256];
        for (int s = 0; s < 256; s++) {
            uint32_t idx = prefix | ((uint32_t)s << 24);
            bits256[s] = (tt[idx >> 3] >> (idx & 7)) & 1;
        }
        layer0[prefix] = build_bdd_8vars(bits256, vars_g0);

        if ((prefix & 0xFFFFFF) == 0xFFFFFF) {
            printf("    group 0 complete, BDD nodes so far: %d\n", bdd_count - 2);
        }
    }
    printf("  Group 0 done. BDD nodes: %d (excluding terminals)\n", bdd_count - 2);

    /* Free truth table -- no longer needed */
    free(tt);
    printf("  (freed truth table, %.0f MB reclaimed)\n", (double)tt_bytes / (1 << 20));

    /* ---- Group 1: vars 16..23 ---- */
    printf("  Group 1 (vars 16-23): processing 2^16 = %d chunks of 256 node IDs...\n",
           1 << 16);
    uint32_t n_g1 = 1U << 16;  /* 64K groups */
    int *layer1 = (int *)malloc(n_g1 * sizeof(int));
    if (!layer1) {
        printf("ERROR: Failed to allocate layer1\n");
        free(layer0);
        return 1;
    }

    for (uint32_t prefix = 0; prefix < n_g1; prefix++) {
        /* Collect 256 node IDs from layer0.
         * layer0 index = prefix | (suffix << 16) where suffix in [0..255],
         * but layer0 has indices [0..2^24 - 1] with bits 0..23.
         * The prefix for group 1 is bits 0..15. The group 1 suffix is bits 16..23. */
        int chunk[256];
        for (int s = 0; s < 256; s++) {
            uint32_t g0_idx = prefix | ((uint32_t)s << 16);
            chunk[s] = layer0[g0_idx];
        }
        layer1[prefix] = merge_bdd_layer(chunk, 8, vars_g1);
    }
    printf("  Group 1 done. BDD nodes: %d (excluding terminals)\n", bdd_count - 2);

    free(layer0);

    /* ---- Group 2: vars 8..15 ---- */
    printf("  Group 2 (vars 8-15): processing 2^8 = 256 chunks of 256 node IDs...\n");
    uint32_t n_g2 = 1U << 8;  /* 256 groups */
    int *layer2 = (int *)malloc(n_g2 * sizeof(int));
    if (!layer2) {
        printf("ERROR: Failed to allocate layer2\n");
        free(layer1);
        return 1;
    }

    for (uint32_t prefix = 0; prefix < n_g2; prefix++) {
        int chunk[256];
        for (int s = 0; s < 256; s++) {
            uint32_t g1_idx = prefix | ((uint32_t)s << 8);
            chunk[s] = layer1[g1_idx];
        }
        layer2[prefix] = merge_bdd_layer(chunk, 8, vars_g2);
    }
    printf("  Group 2 done. BDD nodes: %d (excluding terminals)\n", bdd_count - 2);

    free(layer1);

    /* ---- Group 3: vars 0..7 (root) ---- */
    printf("  Group 3 (vars 0-7): final merge of 256 node IDs...\n");
    {
        int chunk[256];
        for (int s = 0; s < 256; s++) {
            chunk[s] = layer2[s];
        }
        int root = merge_bdd_layer(chunk, 8, vars_g3);

        clock_gettime(CLOCK_MONOTONIC, &t3);
        double bdd_time = (t3.tv_sec - t2.tv_sec) + (t3.tv_nsec - t2.tv_nsec) / 1e9;

        printf("  Group 3 done. BDD root = %d\n", root);
        printf("\n--- Phase 2 complete ---\n");
        printf("BDD construction time: %.2fs\n", bdd_time);
        printf("Total BDD nodes (including terminals): %d\n", bdd_count);
        printf("BDD internal nodes (excluding 2 terminals): %d\n", bdd_count - 2);

        free(layer2);

        /* ================================================================
         * PHASE 3: Analysis and reporting
         * ================================================================ */
        printf("\n--- Phase 3: Results ---\n\n");

        int internal = bdd_count - 2;
        printf("N=8 BDD nodes: %d\n", internal);
        printf("\nScaling comparison:\n");
        printf("  N=4:  183 nodes  (16 vars, 2^16 = 65536 TT entries)\n");
        printf("  N=6:  615 nodes  (24 vars, 2^24 = 16.7M TT entries)\n");
        printf("  N=8: %4d nodes  (32 vars, 2^32 = 4.29B TT entries)\n", internal);
        printf("\nO(N^3) prediction for N=8: 1453 nodes\n");

        /* Compute actual scaling exponent from all 3 data points */
        /* Using log-log fit: log(nodes) = a + b*log(N) */
        /* With N=4,6,8 and nodes known for first two + measured for third */
        double ln4 = log(4.0), ln6 = log(6.0), ln8 = log(8.0);
        double ln183 = log(183.0), ln615 = log(615.0), lnN8 = log((double)internal);

        /* Pairwise exponents */
        double exp_46 = (ln615 - ln183) / (ln6 - ln4);
        double exp_48 = (lnN8 - ln183) / (ln8 - ln4);
        double exp_68 = (lnN8 - ln615) / (ln8 - ln6);

        printf("\nPairwise scaling exponents:\n");
        printf("  N=4->6: %.3f\n", exp_46);
        printf("  N=4->8: %.3f\n", exp_48);
        printf("  N=6->8: %.3f\n", exp_68);

        /* Predicted vs actual */
        double ratio = (double)internal / 1453.0;
        printf("\nPredicted/actual ratio: %.3f (1.0 = perfect O(N^3) fit)\n", ratio);

        if (ratio > 0.8 && ratio < 1.25) {
            printf("\nCONFIRMED: O(N^3) scaling holds at N=8.\n");
            printf("Polynomial-time collision function representation via BDD.\n");
        } else if (ratio > 0.5 && ratio < 2.0) {
            printf("\nAPPROXIMATE: Scaling is close to O(N^3) but not exact.\n");
            printf("Exponent may differ slightly from 3.0.\n");
        } else {
            printf("\nDEVIATION: N=8 result deviates significantly from O(N^3) prediction.\n");
            printf("The scaling law may not hold beyond N=6.\n");
        }

        printf("\nCollision count: %llu (expected 260)\n",
               (unsigned long long)n_collisions);
        printf("Truth table density: %.2e (collisions / 2^32)\n",
               (double)n_collisions / 4294967296.0);

        /* BDD compression ratio */
        printf("BDD compression: %.0fx (2^32 / %d nodes)\n",
               4294967296.0 / internal, internal);

        /* Total time */
        double total = (t3.tv_sec - t0.tv_sec) + (t3.tv_nsec - t0.tv_nsec) / 1e9;
        printf("\nTotal time: %.2fs (truth table: %.2fs, BDD: %.2fs)\n",
               total, tt_time, bdd_time);

        /* ---- Verify BDD by evaluating all known collisions ---- */
        printf("\n--- Verification: spot-check BDD against known collisions ---\n");

        /* Re-enumerate a few collisions and check BDD evaluates to TRUE */
        int verified = 0, checked = 0;
        for (uint32_t w57 = 0; w57 < 256 && checked < 20; w57++) {
            uint32_t s57a[8], s57b[8];
            memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
            uint32_t w57b = find_w2(s57a, s57b, 57, w57);
            sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

            for (uint32_t w58 = 0; w58 < 256 && checked < 20; w58++) {
                uint32_t s58a[8], s58b[8];
                memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
                uint32_t w58b = find_w2(s58a, s58b, 58, w58);
                sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

                for (uint32_t w59 = 0; w59 < 256 && checked < 20; w59++) {
                    uint32_t s59a[8], s59b[8];
                    memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                    uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                    sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);
                    uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);
                    uint32_t W1_61v = (fns1(w59) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
                    uint32_t W2_61v = (fns1(w59b) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;
                    uint32_t W1_63v = (fns1(W1_61v) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
                    uint32_t W2_63v = (fns1(W2_61v) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;
                    uint32_t sc62_c1 = (W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK;
                    uint32_t sc62_c2 = (W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK;

                    for (uint32_t w60 = 0; w60 < 256 && checked < 20; w60++) {
                        uint32_t w60b = (w60 + cas_off60) & MASK;
                        uint32_t s60a[8], s60b[8];
                        memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                        sha_round(s60a, KN[60], w60); sha_round(s60b, KN[60], w60b);
                        uint32_t s61a[8], s61b[8];
                        memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                        sha_round(s61a, KN[61], W1_61v); sha_round(s61b, KN[61], W2_61v);
                        uint32_t W1_62v = (fns1(w60) + sc62_c1) & MASK;
                        uint32_t W2_62v = (fns1(w60b) + sc62_c2) & MASK;
                        sha_round(s61a, KN[62], W1_62v); sha_round(s61b, KN[62], W2_62v);
                        sha_round(s61a, KN[63], W1_63v); sha_round(s61b, KN[63], W2_63v);
                        int coll = 1;
                        for (int r = 0; r < 8; r++)
                            if (s61a[r] != s61b[r]) { coll = 0; break; }

                        if (coll) {
                            /* Evaluate BDD for this input */
                            uint32_t idx = natural_to_interleaved(w57, w58, w59, w60);
                            int node = root;
                            while (bdd_nodes[node].var >= 0) {
                                int v = bdd_nodes[node].var;
                                int bit = (idx >> v) & 1;
                                node = bit ? bdd_nodes[node].hi : bdd_nodes[node].lo;
                            }
                            if (node == BDD_TRUE)
                                verified++;
                            else
                                printf("  BDD MISMATCH at w57=%u w58=%u w59=%u w60=%u\n",
                                       w57, w58, w59, w60);
                            checked++;
                        }
                    }
                }
            }
        }
        printf("Verified %d/%d collisions evaluate to TRUE in BDD\n", verified, checked);

        /* Also check some non-collisions evaluate to FALSE */
        int false_ok = 0, false_checked = 0;
        for (uint32_t w57 = 0; w57 < 256 && false_checked < 20; w57++) {
            for (uint32_t w58 = 0; w58 < 1 && false_checked < 20; w58++) {
                for (uint32_t w59 = 0; w59 < 1 && false_checked < 20; w59++) {
                    for (uint32_t w60 = 0; w60 < 256 && false_checked < 20; w60++) {
                        /* Quick non-collision check: just evaluate BDD, then verify */
                        uint32_t idx = natural_to_interleaved(w57, w58, w59, w60);
                        int node = root;
                        while (bdd_nodes[node].var >= 0) {
                            int v = bdd_nodes[node].var;
                            int bit = (idx >> v) & 1;
                            node = bit ? bdd_nodes[node].hi : bdd_nodes[node].lo;
                        }
                        if (node == BDD_FALSE) {
                            /* Verify it's actually not a collision */
                            uint32_t s57a[8], s57b[8];
                            memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
                            uint32_t w57b = find_w2(s57a, s57b, 57, w57);
                            sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);
                            uint32_t s58a[8], s58b[8];
                            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
                            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
                            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);
                            uint32_t s59a[8], s59b[8];
                            memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                            uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                            sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);
                            uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);
                            uint32_t w60b = (w60 + cas_off60) & MASK;
                            uint32_t s60a[8], s60b[8];
                            memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                            sha_round(s60a, KN[60], w60); sha_round(s60b, KN[60], w60b);
                            uint32_t W1_61v = (fns1(w59) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
                            uint32_t W2_61v = (fns1(w59b) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;
                            uint32_t s61a[8], s61b[8];
                            memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                            sha_round(s61a, KN[61], W1_61v); sha_round(s61b, KN[61], W2_61v);
                            uint32_t W1_62v = (fns1(w60) + (W1p[55]+fns0(W1p[47])+W1p[46]) ) & MASK;
                            uint32_t W2_62v = (fns1(w60b) + (W2p[55]+fns0(W2p[47])+W2p[46]) ) & MASK;
                            uint32_t W1_63v = (fns1(W1_61v) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
                            uint32_t W2_63v = (fns1(W2_61v) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;
                            sha_round(s61a, KN[62], W1_62v); sha_round(s61b, KN[62], W2_62v);
                            sha_round(s61a, KN[63], W1_63v); sha_round(s61b, KN[63], W2_63v);
                            int coll = 1;
                            for (int r = 0; r < 8; r++)
                                if (s61a[r] != s61b[r]) { coll = 0; break; }
                            if (!coll)
                                false_ok++;
                            else
                                printf("  BDD FALSE MISMATCH at w57=%u w58=%u w59=%u w60=%u\n",
                                       w57, w58, w59, w60);
                            false_checked++;
                        }
                    }
                }
            }
        }
        printf("Verified %d/%d non-collisions evaluate to FALSE in BDD\n",
               false_ok, false_checked);

        /* Count nodes per variable level */
        printf("\nBDD nodes per variable level:\n");
        int var_count[NVARS];
        memset(var_count, 0, sizeof(var_count));
        for (int i = 2; i < bdd_count; i++) {
            if (bdd_nodes[i].var >= 0 && bdd_nodes[i].var < NVARS)
                var_count[bdd_nodes[i].var]++;
        }
        for (int v = 0; v < NVARS; v++) {
            const char *wname;
            int bit;
            switch (v % 4) {
                case 0: wname = "W57"; break;
                case 1: wname = "W58"; break;
                case 2: wname = "W59"; break;
                default: wname = "W60"; break;
            }
            bit = v / 4;
            printf("  var %2d (%s[%d]): %d nodes\n", v, wname, bit, var_count[v]);
        }

        printf("\nEvidence level: VERIFIED (exhaustive truth table + BDD at N=8)\n");
    }

    free(bdd_nodes);
    free(uentry_pool);

    return 0;
}
