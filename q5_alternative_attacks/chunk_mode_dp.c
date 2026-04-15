/*
 * chunk_mode_dp.c — Chunk-mode DP boundary-state deduplication measurement
 *
 * GPT-5.4 prescribed algorithm (measurement prototype):
 * At N=8 with B=4 bit chunks, measure whether projecting to boundary
 * carry states at bit 4 yields effective deduplication.
 *
 * Strategy: two-phase approach.
 *
 * Phase 1 (fast): Run the standard cascade DP. Find all 260 collisions.
 * For each collision: extract all 98 boundary carries (49 per path).
 * Determine which carries are invariant across all collisions.
 * Result: the "variable carry mask" at the boundary.
 *
 * Phase 2 (full enumeration): For all 2^32 configs, extract ONLY the
 * variable boundary carries (the reduced state). Count unique reduced states.
 * This avoids the 98-bit-state explosion problem. If variable carries
 * number V, unique states fit in 2^V which is manageable.
 *
 * Also: verify all 260 collisions have unique reduced boundary states.
 *
 * N=8, MSB kernel, M[0]=0x67, fill=0xff.
 * Compile: gcc -O3 -march=native -o chunk_mode_dp chunk_mode_dp.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 8
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define ROUNDS 7
#define ADDS_PER_ROUND 7
#define TOTAL_ADDS (ROUNDS * ADDS_PER_ROUND)  /* 49 carry bits per path */
#define BOUNDARY_BIT 4
#define LOW_MASK ((1U << BOUNDARY_BIT) - 1)  /* 0xF */

/* --- SHA-256 mini primitives (N-bit) --- */
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static int SR(int k) { int r = (int)rint((double)k * N / 32.0); return r < 1 ? 1 : r; }
static inline uint32_t ror_n(uint32_t x, int k) { k %= N; return ((x >> k) | (x << (N - k))) & MASK; }
static inline uint32_t fnS0(uint32_t a) { return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & MASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & MASK); }
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e & f) ^ ((~e) & g)) & MASK; }
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & MASK; }

static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};
static uint32_t KN[64], IVN[8];
static uint32_t state1[8], state2[8], W1p[57], W2p[57];

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],
             e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fnS1(e) + fnCh(e,f,g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fnS0(a) + fnMj(a,b,c)) & MASK;
        h=g; g=f; f=e; e=(d+T1)&MASK; d=c; c=b; b=a; a=(T1+T2)&MASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

/* sha_round without carry extraction — kept for verification use */
__attribute__((unused))
static void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w) & MASK;
    uint32_t T2 = (fnS0(s[0])+fnMj(s[0],s[1],s[2])) & MASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
}

static uint32_t find_w2(uint32_t s1[8], uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd]) & MASK;
    uint32_t r2 = (s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd]) & MASK;
    uint32_t T21 = (fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T22 = (fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + r1 - r2 + T21 - T22) & MASK;
}

/*
 * SHA round with inline carry extraction at chunk boundary.
 * Performs the round AND returns 7 boundary carry bits packed into a uint64_t
 * starting at bit position `base`.
 */
static inline uint64_t sha_round_carries(uint32_t s[8], uint32_t k, uint32_t w,
                                          int base) {
    uint32_t sig1_e = fnS1(s[4]);
    uint32_t ch_efg = fnCh(s[4], s[5], s[6]);
    uint32_t sig0_a = fnS0(s[0]);
    uint32_t maj_abc = fnMj(s[0], s[1], s[2]);
    uint32_t t0 = (s[7] + sig1_e) & MASK;
    uint32_t t1 = (t0 + ch_efg) & MASK;
    uint32_t t2 = (t1 + k) & MASK;
    uint32_t T1 = (t2 + w) & MASK;
    uint32_t T2 = (sig0_a + maj_abc) & MASK;

    uint64_t c = 0;
    c |= (uint64_t)((((s[7]&LOW_MASK)+(sig1_e&LOW_MASK))>>BOUNDARY_BIT)&1) << (base+0);
    c |= (uint64_t)((((t0&LOW_MASK)+(ch_efg&LOW_MASK))>>BOUNDARY_BIT)&1) << (base+1);
    c |= (uint64_t)((((t1&LOW_MASK)+(k&LOW_MASK))>>BOUNDARY_BIT)&1) << (base+2);
    c |= (uint64_t)((((t2&LOW_MASK)+(w&LOW_MASK))>>BOUNDARY_BIT)&1) << (base+3);
    c |= (uint64_t)((((sig0_a&LOW_MASK)+(maj_abc&LOW_MASK))>>BOUNDARY_BIT)&1) << (base+4);
    c |= (uint64_t)((((s[3]&LOW_MASK)+(T1&LOW_MASK))>>BOUNDARY_BIT)&1) << (base+5);
    c |= (uint64_t)((((T1&LOW_MASK)+(T2&LOW_MASK))>>BOUNDARY_BIT)&1) << (base+6);

    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
    return c;
}

/* ========== Types ========== */
typedef struct {
    uint64_t carries_p1;  /* 49 boundary carry bits, path 1 */
    uint64_t carries_p2;  /* 49 boundary carry bits, path 2 */
} BoundaryState;

/* ========== Collision storage ========== */
#define MAX_COLL 4096
static int n_coll = 0;
static uint32_t coll_w1[MAX_COLL][4], coll_w2[MAX_COLL][4];
static BoundaryState coll_bs[MAX_COLL];

/* ========== Hash map for reduced state counting ========== */
/* After Phase 1 determines variable carries, the reduced state is at most
 * ~30 bits. We use a direct-mapped counting table where possible,
 * or a hash table if the reduced state is >24 bits. */

/* For the general case: hash table with 32-bit keys (projected state) */
#define HT_BITS 24
#define HT_SIZE (1U << HT_BITS)
#define HT_MASK (HT_SIZE - 1)

typedef struct {
    uint32_t key;
    uint32_t count;
    uint8_t coll_flag; /* has at least one collision */
    uint8_t occupied;
} HTEntry;

static HTEntry *ht;
static uint64_t ht_used = 0;

static int ht_insert(uint32_t key, int is_coll) {
    uint32_t h = key * 2654435761U; /* Knuth multiplicative hash */
    uint32_t idx = (h >> (32 - HT_BITS)) & HT_MASK;
    for (;;) {
        if (!ht[idx].occupied) {
            ht[idx].key = key;
            ht[idx].count = 1;
            ht[idx].coll_flag = is_coll ? 1 : 0;
            ht[idx].occupied = 1;
            ht_used++;
            return 1; /* new */
        }
        if (ht[idx].key == key) {
            ht[idx].count++;
            if (is_coll) ht[idx].coll_flag = 1;
            return 0; /* existing */
        }
        idx = (idx + 1) & HT_MASK;
    }
}

/* ========== Main ========== */
int main() {
    setbuf(stdout, NULL);

    rS0[0]=SR(2); rS0[1]=SR(13); rS0[2]=SR(22);
    rS1[0]=SR(6); rS1[1]=SR(11); rS1[2]=SR(25);
    rs0[0]=SR(7); rs0[1]=SR(18); ss0=SR(3);
    rs1[0]=SR(17); rs1[1]=SR(19); ss1=SR(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & MASK;

    /* Find candidate */
    int found = 0;
    for (uint32_t m0 = 0; m0 <= MASK && !found; m0++) {
        uint32_t M1[16], M2[16];
        for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
        M1[0] = m0; M2[0] = m0 ^ MSB; M2[9] = MASK ^ MSB;
        precompute(M1, state1, W1p);
        precompute(M2, state2, W2p);
        if (state1[0] == state2[0]) {
            printf("Candidate: N=%d M[0]=0x%02x fill=0xff\n", N, m0);
            found = 1;
        }
    }
    if (!found) { printf("No candidate\n"); return 1; }

    printf("\n========================================\n");
    printf(" Phase 1: Find collisions + extract full boundary carries\n");
    printf("========================================\n\n");

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t n_tested = 0;

    /* Phase 1: enumerate all, collect collisions + boundary carries */
    for (uint32_t w57 = 0; w57 < (1U << N); w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        uint64_t c57a = sha_round_carries(s57a, KN[57], w57, 0);
        uint64_t c57b = sha_round_carries(s57b, KN[57], w57b, 0);

        for (uint32_t w58 = 0; w58 < (1U << N); w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            uint64_t c58a = c57a | sha_round_carries(s58a, KN[58], w58, 1*ADDS_PER_ROUND);
            uint64_t c58b = c57b | sha_round_carries(s58b, KN[58], w58b, 1*ADDS_PER_ROUND);

            for (uint32_t w59 = 0; w59 < (1U << N); w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                uint64_t c59a = c58a | sha_round_carries(s59a, KN[59], w59, 2*ADDS_PER_ROUND);
                uint64_t c59b = c58b | sha_round_carries(s59b, KN[59], w59b, 2*ADDS_PER_ROUND);

                for (uint32_t w60 = 0; w60 < (1U << N); w60++) {
                    uint32_t s60a[8], s60b[8];
                    memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                    uint32_t w60b = find_w2(s60a, s60b, 60, w60);
                    uint64_t ca = c59a | sha_round_carries(s60a, KN[60], w60, 3*ADDS_PER_ROUND);
                    uint64_t cb = c59b | sha_round_carries(s60b, KN[60], w60b, 3*ADDS_PER_ROUND);

                    uint32_t Wa[7]={w57,w58,w59,w60,0,0,0};
                    uint32_t Wb[7]={w57b,w58b,w59b,w60b,0,0,0};
                    Wa[4]=(fns1(Wa[2])+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                    Wb[4]=(fns1(Wb[2])+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                    Wa[5]=(fns1(Wa[3])+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                    Wb[5]=(fns1(Wb[3])+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                    Wa[6]=(fns1(Wa[4])+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                    Wb[6]=(fns1(Wb[4])+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;

                    uint32_t fa[8], fb[8];
                    memcpy(fa, s60a, 32); memcpy(fb, s60b, 32);
                    for (int r = 4; r < 7; r++) {
                        ca |= sha_round_carries(fa, KN[57+r], Wa[r], r*ADDS_PER_ROUND);
                        cb |= sha_round_carries(fb, KN[57+r], Wb[r], r*ADDS_PER_ROUND);
                    }

                    int is_coll = 1;
                    for (int r = 0; r < 8; r++)
                        if (fa[r] != fb[r]) { is_coll = 0; break; }

                    if (is_coll && n_coll < MAX_COLL) {
                        coll_w1[n_coll][0]=w57; coll_w1[n_coll][1]=w58;
                        coll_w1[n_coll][2]=w59; coll_w1[n_coll][3]=w60;
                        coll_w2[n_coll][0]=w57b; coll_w2[n_coll][1]=w58b;
                        coll_w2[n_coll][2]=w59b; coll_w2[n_coll][3]=w60b;
                        coll_bs[n_coll].carries_p1 = ca;
                        coll_bs[n_coll].carries_p2 = cb;
                        n_coll++;
                    }
                    n_tested++;
                }
            }
        }
        if ((w57 & 0xF) == 0xF) {
            clock_gettime(CLOCK_MONOTONIC, &t1);
            double el = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
            double pct = 100.0*(w57+1)/(1<<N);
            printf("  [%5.1f%%] w57=0x%02x coll=%d | %.1fs ETA %.0fs | %.1fM/s\n",
                   pct, w57, n_coll, el, el/pct*100-el, n_tested/el/1e6);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ph1_time = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;

    printf("\nPhase 1 complete: %llu configs, %d collisions, %.2fs\n\n",
           (unsigned long long)n_tested, n_coll, ph1_time);

    /* ========== Analyze collision boundary states ========== */
    printf("========================================\n");
    printf(" Phase 1 Analysis: Boundary Carry Structure\n");
    printf("========================================\n\n");

    /* Check uniqueness of collision boundary states */
    int unique_coll = 0;
    for (int i = 0; i < n_coll; i++) {
        int dup = 0;
        for (int j = 0; j < i; j++) {
            if (coll_bs[i].carries_p1 == coll_bs[j].carries_p1 &&
                coll_bs[i].carries_p2 == coll_bs[j].carries_p2) {
                dup = 1; break;
            }
        }
        if (!dup) unique_coll++;
    }
    printf("Unique collision boundary states (full 98-bit): %d / %d\n",
           unique_coll, n_coll);
    printf("All unique? %s\n\n",
           unique_coll == n_coll ? "YES (perfect permutation at boundary)" : "NO");

    /* Determine invariant carries across all collisions */
    uint64_t active_mask = (1ULL << TOTAL_ADDS) - 1;
    uint64_t inv_p1 = active_mask, inv_p2 = active_mask;
    if (n_coll > 0) {
        uint64_t ref_p1 = coll_bs[0].carries_p1;
        uint64_t ref_p2 = coll_bs[0].carries_p2;
        for (int i = 1; i < n_coll; i++) {
            inv_p1 &= ~(coll_bs[i].carries_p1 ^ ref_p1);
            inv_p2 &= ~(coll_bs[i].carries_p2 ^ ref_p2);
        }
    }
    uint64_t var_p1 = active_mask & ~inv_p1;
    uint64_t var_p2 = active_mask & ~inv_p2;
    int n_inv_p1 = __builtin_popcountll(inv_p1 & active_mask);
    int n_inv_p2 = __builtin_popcountll(inv_p2 & active_mask);
    int n_var_p1 = TOTAL_ADDS - n_inv_p1;
    int n_var_p2 = TOTAL_ADDS - n_inv_p2;
    int n_var_total = n_var_p1 + n_var_p2;

    printf("--- Invariant analysis ---\n");
    printf("Path 1: %d/%d invariant, %d variable\n", n_inv_p1, TOTAL_ADDS, n_var_p1);
    printf("Path 2: %d/%d invariant, %d variable\n", n_inv_p2, TOTAL_ADDS, n_var_p2);
    printf("Total variable carries: %d (this is the reduced state dimensionality)\n",
           n_var_total);
    printf("Reduced state space: 2^%d = %llu (vs 2^98 full)\n\n",
           n_var_total, (unsigned long long)1ULL << (n_var_total < 63 ? n_var_total : 63));

    /* Carry-diff among collisions */
    int unique_diffs = 0;
    uint64_t diff_seen[MAX_COLL];
    for (int i = 0; i < n_coll; i++) {
        uint64_t d = coll_bs[i].carries_p1 ^ coll_bs[i].carries_p2;
        int dup = 0;
        for (int j = 0; j < unique_diffs; j++)
            if (diff_seen[j] == d) { dup = 1; break; }
        if (!dup) diff_seen[unique_diffs++] = d;
    }
    printf("Unique carry-diffs (p1 XOR p2) among collisions: %d\n", unique_diffs);
    for (int i = 0; i < unique_diffs && i < 5; i++)
        printf("  diff[%d] = 0x%012llx (%d bits set)\n",
               i, (unsigned long long)diff_seen[i],
               __builtin_popcountll(diff_seen[i]));

    /* Per-addition breakdown */
    const char *add_names[ADDS_PER_ROUND] = {
        "h+Sig1(e)", "+Ch(efg)", "+K[r]", "+W[r]",
        "Sig0+Maj", "d+T1=e'", "T1+T2=a'"
    };
    printf("\nPer-addition invariance (across %d collisions):\n", n_coll);
    printf("Round  Addition       P1    P2\n");
    for (int r = 0; r < ROUNDS; r++) {
        for (int a = 0; a < ADDS_PER_ROUND; a++) {
            int bit = r * ADDS_PER_ROUND + a;
            printf("  r%d   %-14s   %s    %s\n",
                   57+r, add_names[a],
                   ((inv_p1 >> bit) & 1) ? "INV" : "var",
                   ((inv_p2 >> bit) & 1) ? "INV" : "var");
        }
    }

    /* Build variable-carry index maps for compact projection */
    int var_idx_p1[TOTAL_ADDS], var_idx_p2[TOTAL_ADDS];
    int vi1 = 0, vi2 = 0;
    for (int i = 0; i < TOTAL_ADDS; i++) {
        var_idx_p1[i] = ((var_p1 >> i) & 1) ? vi1++ : -1;
        var_idx_p2[i] = ((var_p2 >> i) & 1) ? vi2++ : -1;
    }

    /* Project collision boundary states to reduced form (128-bit for safety) */
    typedef struct { uint64_t lo, hi; } Proj128;
    printf("\n--- Reduced boundary states for collisions ---\n");
    Proj128 coll_reduced[MAX_COLL];
    int unique_reduced_coll = 0;
    for (int c = 0; c < n_coll; c++) {
        uint64_t lo = 0, hi = 0;
        int bit_pos = 0;
        for (int i = 0; i < TOTAL_ADDS; i++) {
            if ((var_p1 >> i) & 1) {
                uint64_t v = (coll_bs[c].carries_p1 >> i) & 1;
                if (bit_pos < 64) lo |= v << bit_pos;
                else hi |= v << (bit_pos - 64);
                bit_pos++;
            }
        }
        for (int i = 0; i < TOTAL_ADDS; i++) {
            if ((var_p2 >> i) & 1) {
                uint64_t v = (coll_bs[c].carries_p2 >> i) & 1;
                if (bit_pos < 64) lo |= v << bit_pos;
                else hi |= v << (bit_pos - 64);
                bit_pos++;
            }
        }
        coll_reduced[c].lo = lo;
        coll_reduced[c].hi = hi;

        int dup = 0;
        for (int j = 0; j < c; j++)
            if (coll_reduced[j].lo == lo && coll_reduced[j].hi == hi) { dup = 1; break; }
        if (!dup) unique_reduced_coll++;
    }
    printf("Unique reduced collision boundary states: %d / %d\n",
           unique_reduced_coll, n_coll);
    printf("All unique? %s\n", unique_reduced_coll == n_coll ? "YES" : "NO");

    /* Print first few reduced states */
    for (int i = 0; i < n_coll && i < 5; i++)
        printf("  Coll #%3d: W1=[%02x,%02x,%02x,%02x] reduced=(0x%016llx,0x%06llx)\n",
               i+1, coll_w1[i][0], coll_w1[i][1], coll_w1[i][2], coll_w1[i][3],
               (unsigned long long)coll_reduced[i].lo, (unsigned long long)coll_reduced[i].hi);

    /* ========== Phase 2: Full enumeration with reduced states ========== */
    if (n_var_total > 24) {
        printf("\n========================================\n");
        printf(" Phase 2: SKIPPED (reduced state has %d bits > 24)\n", n_var_total);
        printf("========================================\n");
        printf("Hash table deduplication would require 2^%d entries.\n", n_var_total);
        printf("Instead, reporting Phase 1 results as the main finding.\n");

        /* Sample-based uniqueness measurement using full 98-bit boundary state.
         * Since the full state is 98 bits and almost all are variable (88),
         * use a hash-based approach: hash to 64 bits, count unique hashes
         * in a small hash set. */
        printf("\n--- Sample-based unique count estimate ---\n");
        #define SAMPLE_HT_BITS 20
        #define SAMPLE_HT_SIZE (1U << SAMPLE_HT_BITS)
        #define SAMPLE_HT_MASK (SAMPLE_HT_SIZE - 1)
        uint64_t *sample_ht = calloc(SAMPLE_HT_SIZE, sizeof(uint64_t));
        uint8_t *sample_occ = calloc(SAMPLE_HT_SIZE, 1);
        int sample_unique = 0;
        uint32_t sample_count = 1U << 20;
        uint64_t rng = 0x12345678DEADBEEFULL;
        printf("Sampling %u random configs...\n", sample_count);

        for (uint32_t s = 0; s < sample_count; s++) {
            rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
            uint32_t w57 = (rng >> 0) & MASK;
            uint32_t w58 = (rng >> 8) & MASK;
            uint32_t w59 = (rng >> 16) & MASK;
            uint32_t w60 = (rng >> 24) & MASK;

            uint32_t sa[8], sb[8];
            memcpy(sa, state1, 32); memcpy(sb, state2, 32);
            uint32_t w57b = find_w2(sa, sb, 57, w57);
            uint64_t ca = sha_round_carries(sa, KN[57], w57, 0);
            uint64_t cb = sha_round_carries(sb, KN[57], w57b, 0);
            uint32_t w58b = find_w2(sa, sb, 58, w58);
            ca |= sha_round_carries(sa, KN[58], w58, ADDS_PER_ROUND);
            cb |= sha_round_carries(sb, KN[58], w58b, ADDS_PER_ROUND);
            uint32_t w59b = find_w2(sa, sb, 59, w59);
            ca |= sha_round_carries(sa, KN[59], w59, 2*ADDS_PER_ROUND);
            cb |= sha_round_carries(sb, KN[59], w59b, 2*ADDS_PER_ROUND);
            uint32_t w60b = find_w2(sa, sb, 60, w60);
            ca |= sha_round_carries(sa, KN[60], w60, 3*ADDS_PER_ROUND);
            cb |= sha_round_carries(sb, KN[60], w60b, 3*ADDS_PER_ROUND);

            uint32_t Wa[7]={w57,w58,w59,w60,0,0,0};
            uint32_t Wb[7]={w57b,w58b,w59b,w60b,0,0,0};
            Wa[4]=(fns1(Wa[2])+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
            Wb[4]=(fns1(Wb[2])+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
            Wa[5]=(fns1(Wa[3])+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
            Wb[5]=(fns1(Wb[3])+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
            Wa[6]=(fns1(Wa[4])+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
            Wb[6]=(fns1(Wb[4])+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;

            uint32_t fa[8], fb[8];
            memcpy(fa, sa, 32); memcpy(fb, sb, 32);
            for (int r = 4; r < 7; r++) {
                ca |= sha_round_carries(fa, KN[57+r], Wa[r], r*ADDS_PER_ROUND);
                cb |= sha_round_carries(fb, KN[57+r], Wb[r], r*ADDS_PER_ROUND);
            }

            /* Hash the full 98-bit state (ca,cb) to a 64-bit fingerprint */
            uint64_t fp = ca * 6364136223846793005ULL + cb * 1442695040888963407ULL;
            fp ^= fp >> 33; fp *= 0xff51afd7ed558ccdULL;
            fp ^= fp >> 33;

            /* Insert into sample hash table */
            uint32_t idx = (uint32_t)(fp & SAMPLE_HT_MASK);
            for (;;) {
                if (!sample_occ[idx]) {
                    sample_ht[idx] = fp;
                    sample_occ[idx] = 1;
                    sample_unique++;
                    break;
                }
                if (sample_ht[idx] == fp) break; /* duplicate */
                idx = (idx + 1) & SAMPLE_HT_MASK;
            }
        }
        printf("Sample: %u configs, %d unique boundary states (full 98-bit hashed)\n",
               sample_count, sample_unique);
        double dup_rate = 1.0 - (double)sample_unique / sample_count;
        printf("Duplicate rate: %.4f\n", dup_rate);
        if (dup_rate > 0.001) {
            /* Good's estimate: N_unique ~ n / (1 - f_1/n) where f_1 = singletons */
            double est_total = (double)sample_count * sample_count /
                               (2.0 * (sample_count - sample_unique) + 1);
            printf("Estimated total unique (capture-recapture): ~%.0f\n", est_total);
            printf("Estimated dedup ratio: %.1fx over 2^32\n",
                   (double)(1ULL<<32) / est_total);
        } else {
            printf("Almost all unique -> dedup ratio ~1x at boundary\n");
        }
        free(sample_ht);
        free(sample_occ);
    } else {
        printf("\n========================================\n");
        printf(" Phase 2: Full enumeration with %d-bit reduced state\n", n_var_total);
        printf("========================================\n\n");

        ht = calloc(HT_SIZE, sizeof(HTEntry));
        if (!ht) { printf("OOM\n"); return 1; }

        clock_gettime(CLOCK_MONOTONIC, &t0);
        n_tested = 0;

        for (uint32_t w57 = 0; w57 < (1U << N); w57++) {
            uint32_t s57a[8], s57b[8];
            memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
            uint32_t w57b = find_w2(s57a, s57b, 57, w57);
            uint64_t c57a = sha_round_carries(s57a, KN[57], w57, 0);
            uint64_t c57b = sha_round_carries(s57b, KN[57], w57b, 0);
            for (uint32_t w58 = 0; w58 < (1U << N); w58++) {
                uint32_t s58a[8], s58b[8];
                memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
                uint32_t w58b = find_w2(s58a, s58b, 58, w58);
                uint64_t c58a = c57a | sha_round_carries(s58a, KN[58], w58, ADDS_PER_ROUND);
                uint64_t c58b = c57b | sha_round_carries(s58b, KN[58], w58b, ADDS_PER_ROUND);
                for (uint32_t w59 = 0; w59 < (1U << N); w59++) {
                    uint32_t s59a[8], s59b[8];
                    memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                    uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                    uint64_t c59a = c58a | sha_round_carries(s59a, KN[59], w59, 2*ADDS_PER_ROUND);
                    uint64_t c59b = c58b | sha_round_carries(s59b, KN[59], w59b, 2*ADDS_PER_ROUND);
                    for (uint32_t w60 = 0; w60 < (1U << N); w60++) {
                        uint32_t s60a[8], s60b[8];
                        memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                        uint32_t w60b = find_w2(s60a, s60b, 60, w60);
                        uint64_t ca = c59a | sha_round_carries(s60a, KN[60], w60, 3*ADDS_PER_ROUND);
                        uint64_t cb = c59b | sha_round_carries(s60b, KN[60], w60b, 3*ADDS_PER_ROUND);

                        uint32_t Wa[7]={w57,w58,w59,w60,0,0,0};
                        uint32_t Wb[7]={w57b,w58b,w59b,w60b,0,0,0};
                        Wa[4]=(fns1(Wa[2])+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                        Wb[4]=(fns1(Wb[2])+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                        Wa[5]=(fns1(Wa[3])+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                        Wb[5]=(fns1(Wb[3])+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                        Wa[6]=(fns1(Wa[4])+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                        Wb[6]=(fns1(Wb[4])+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;

                        uint32_t fa[8], fb[8];
                        memcpy(fa, s60a, 32); memcpy(fb, s60b, 32);
                        for (int r = 4; r < 7; r++) {
                            ca |= sha_round_carries(fa, KN[57+r], Wa[r], r*ADDS_PER_ROUND);
                            cb |= sha_round_carries(fb, KN[57+r], Wb[r], r*ADDS_PER_ROUND);
                        }

                        int is_coll = 1;
                        for (int r = 0; r < 8; r++)
                            if (fa[r] != fb[r]) { is_coll = 0; break; }

                        /* Project to reduced state */
                        uint32_t proj = 0;
                        int bp = 0;
                        for (int i = 0; i < TOTAL_ADDS; i++)
                            if ((var_p1 >> i) & 1) {
                                proj |= (uint32_t)((ca >> i) & 1) << bp++;
                            }
                        for (int i = 0; i < TOTAL_ADDS; i++)
                            if ((var_p2 >> i) & 1) {
                                proj |= (uint32_t)((cb >> i) & 1) << bp++;
                            }

                        ht_insert(proj, is_coll);
                        n_tested++;
                    }
                }
            }
            if ((w57 & 0xF) == 0xF) {
                clock_gettime(CLOCK_MONOTONIC, &t1);
                double el = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
                double pct = 100.0*(w57+1)/(1<<N);
                printf("  [%5.1f%%] unique_reduced=%llu | %.1fs ETA %.0fs\n",
                       pct, (unsigned long long)ht_used, el, el/pct*100-el);
            }
        }
        clock_gettime(CLOCK_MONOTONIC, &t1);
        double ph2_time = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;

        printf("\nPhase 2: %llu configs, %llu unique reduced states, %.2fs\n\n",
               (unsigned long long)n_tested, (unsigned long long)ht_used, ph2_time);

        printf("--- Deduplication ---\n");
        printf("Total configs:          %llu (2^%d)\n", (unsigned long long)n_tested, 4*N);
        printf("Unique reduced states:  %llu\n", (unsigned long long)ht_used);
        printf("Dedup ratio:            %.1fx\n", (double)n_tested / ht_used);
        printf("log2(unique):           %.2f (vs log2(total)=%d)\n",
               log2((double)ht_used), 4*N);
        printf("Bits saved:             %.1f\n", 4.0*N - log2((double)ht_used));

        /* Distribution */
        uint64_t max_c=0, coll_bearing=0;
        for (uint32_t i = 0; i < HT_SIZE; i++) {
            if (!ht[i].occupied) continue;
            if (ht[i].count > max_c) max_c = ht[i].count;
            if (ht[i].coll_flag) coll_bearing++;
        }
        printf("Max configs/state:      %llu\n", (unsigned long long)max_c);
        printf("Collision-bearing:      %llu (1 in %.0f)\n",
               (unsigned long long)coll_bearing,
               (double)ht_used / (coll_bearing > 0 ? coll_bearing : 1));

        free(ht);
    }

    /* ========== Final summary ========== */
    printf("\n=============================================================\n");
    printf("  CHUNK-MODE DP SUMMARY (N=%d, B=%d)\n", N, BOUNDARY_BIT);
    printf("=============================================================\n\n");
    printf("Collisions:                 %d\n", n_coll);
    printf("Full boundary state:        98 bits (49 per path)\n");
    printf("Invariant carries:          %d (P1) + %d (P2) = %d\n",
           n_inv_p1, n_inv_p2, n_inv_p1 + n_inv_p2);
    printf("Variable carries:           %d (P1) + %d (P2) = %d\n",
           n_var_p1, n_var_p2, n_var_total);
    printf("Reduced state dimension:    %d bits\n", n_var_total);
    printf("Collision BS all unique?    %s (full 98-bit) / %s (reduced %d-bit)\n",
           unique_coll == n_coll ? "YES" : "NO",
           unique_reduced_coll == n_coll ? "YES" : "NO",
           n_var_total);
    printf("Carry-diff classes:         %d\n", unique_diffs);
    printf("\nDone.\n");
    return 0;
}
