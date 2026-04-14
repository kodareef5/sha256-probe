/*
 * A-Path Gaussian Elimination Collision Finder for N=4 Mini-SHA
 *
 * Uses the cascade DP structure (W2 determined from W1) to enumerate all
 * collisions across rounds 57-63.  The key MEASUREMENT is the W60 solution
 * structure: for each (w57, w58, w59) triple, how many W60 values produce a
 * collision?  If successful triples always have exactly 1 W60 solution, that
 * solution might be algebraically computable, eliminating the inner loop
 * entirely.
 *
 * Measurements reported:
 *   1. Per-w57 collision counts (should match de58 analysis)
 *   2. Per-(w57,w58,w59) collision counts
 *   3. W60 success rate: fraction of triples yielding any collision
 *   4. W60 multiplicity distribution: how many W60 values work per triple
 *   5. Modular spacing of successful W60 values within a triple
 *   6. GF(2) rank analysis of successful W60 bit patterns
 *
 * N=4, MSB kernel, M[0]=0x0, fill=0xf.
 * Compile: gcc -O3 -march=native -o apath_gauss apath_gauss.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 4
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define NVALS (1U << N)       /* 16 values per word */

/* --- Mini-SHA primitives (N-bit, rotation-scaled) --- */

static int r_Sig0[3], r_Sig1[3], r_sig0[2], r_sig1[2], s_sig0, s_sig1;

static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N;
    return ((x >> k) | (x << (N - k))) & MASK;
}
static inline uint32_t fn_S0(uint32_t a) {
    return ror_n(a, r_Sig0[0]) ^ ror_n(a, r_Sig0[1]) ^ ror_n(a, r_Sig0[2]);
}
static inline uint32_t fn_S1(uint32_t e) {
    return ror_n(e, r_Sig1[0]) ^ ror_n(e, r_Sig1[1]) ^ ror_n(e, r_Sig1[2]);
}
static inline uint32_t fn_s0(uint32_t x) {
    return ror_n(x, r_sig0[0]) ^ ror_n(x, r_sig0[1]) ^ ((x >> s_sig0) & MASK);
}
static inline uint32_t fn_s1(uint32_t x) {
    return ror_n(x, r_sig1[0]) ^ ror_n(x, r_sig1[1]) ^ ((x >> s_sig1) & MASK);
}
static inline uint32_t fn_Ch(uint32_t e, uint32_t f, uint32_t g) {
    return ((e & f) ^ ((~e) & g)) & MASK;
}
static inline uint32_t fn_Maj(uint32_t a, uint32_t b, uint32_t c) {
    return ((a & b) ^ (a & c) ^ (b & c)) & MASK;
}

/* --- Constants --- */

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
static uint32_t state1[8], state2[8], W1_pre[57], W2_pre[57];

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

/* --- Precompute 57 rounds --- */

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fn_s1(W[i-2]) + W[i-7] + fn_s0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a = IVN[0], b = IVN[1], c = IVN[2], d = IVN[3];
    uint32_t e = IVN[4], f = IVN[5], g = IVN[6], h = IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fn_S1(e) + fn_Ch(e, f, g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fn_S0(a) + fn_Maj(a, b, c)) & MASK;
        h = g; g = f; f = e; e = (d + T1) & MASK;
        d = c; c = b; b = a; a = (T1 + T2) & MASK;
    }
    st[0] = a; st[1] = b; st[2] = c; st[3] = d;
    st[4] = e; st[5] = f; st[6] = g; st[7] = h;
}

/* --- SHA round --- */

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fn_S1(s[4]) + fn_Ch(s[4], s[5], s[6]) + k + w) & MASK;
    uint32_t T2 = (fn_S0(s[0]) + fn_Maj(s[0], s[1], s[2])) & MASK;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = (s[3] + T1) & MASK;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = (T1 + T2) & MASK;
}

/* --- Cascade offset: find W2[k] that makes da=0 at round k --- */

static uint32_t find_w2(uint32_t s1[8], uint32_t s2[8], uint32_t rnd, uint32_t w1) {
    uint32_t rest1 = (s1[7] + fn_S1(s1[4]) + fn_Ch(s1[4], s1[5], s1[6]) + KN[rnd]) & MASK;
    uint32_t rest2 = (s2[7] + fn_S1(s2[4]) + fn_Ch(s2[4], s2[5], s2[6]) + KN[rnd]) & MASK;
    uint32_t T2_1 = (fn_S0(s1[0]) + fn_Maj(s1[0], s1[1], s1[2])) & MASK;
    uint32_t T2_2 = (fn_S0(s2[0]) + fn_Maj(s2[0], s2[1], s2[2])) & MASK;
    return (w1 + rest1 - rest2 + T2_1 - T2_2) & MASK;
}

/* --- GF(2) rank computation --- */

static int gf2_rank(uint32_t *vals, int count) {
    uint32_t basis[N];     /* basis[i] has pivot at bit i (or 0 if unused) */
    int rank = 0;
    memset(basis, 0, sizeof(basis));
    for (int i = 0; i < count; i++) {
        uint32_t v = vals[i];
        for (int b = 0; b < N; b++)
            if ((v >> b) & 1)
                if (basis[b])
                    v ^= basis[b];
        if (v) {
            int pos = __builtin_ctz(v);
            basis[pos] = v;
            /* re-reduce older basis vectors against this new pivot */
            for (int b = 0; b < N; b++)
                if (b != pos && basis[b] && ((basis[b] >> pos) & 1))
                    basis[b] ^= v;
            rank++;
        }
    }
    return rank;
}

int main(void) {
    setbuf(stdout, NULL);

    /* --- Initialize rotation parameters --- */
    r_Sig0[0] = scale_rot(2);  r_Sig0[1] = scale_rot(13); r_Sig0[2] = scale_rot(22);
    r_Sig1[0] = scale_rot(6);  r_Sig1[1] = scale_rot(11); r_Sig1[2] = scale_rot(25);
    r_sig0[0] = scale_rot(7);  r_sig0[1] = scale_rot(18); s_sig0 = scale_rot(3);
    r_sig1[0] = scale_rot(17); r_sig1[1] = scale_rot(19); s_sig1 = scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & MASK;

    printf("A-Path Gaussian Elimination Collision Finder\n");
    printf("N=%d, MSB kernel, M[0]=0x0, fill=0xf\n", N);
    printf("Rotations: Sig0={%d,%d,%d} Sig1={%d,%d,%d} sig0={%d,%d,>>%d} sig1={%d,%d,>>%d}\n",
           r_Sig0[0], r_Sig0[1], r_Sig0[2],
           r_Sig1[0], r_Sig1[1], r_Sig1[2],
           r_sig0[0], r_sig0[1], s_sig0,
           r_sig1[0], r_sig1[1], s_sig1);

    /* --- Set up messages: M[0]=0x0, fill=0xf, MSB kernel --- */
    uint32_t M1[16], M2[16];
    for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
    M1[0] = 0x0;
    M2[0] = 0x0 ^ MSB;     /* MSB flip in M[0] */
    M2[9] = MASK ^ MSB;    /* MSB flip in M[9] (da[56]=0 condition) */

    precompute(M1, state1, W1_pre);
    precompute(M2, state2, W2_pre);

    /* Verify da[56]=0 (state registers should match for register 'a') */
    printf("\nState after 57 rounds:\n");
    printf("  Path 1: a=%x b=%x c=%x d=%x e=%x f=%x g=%x h=%x\n",
           state1[0],state1[1],state1[2],state1[3],
           state1[4],state1[5],state1[6],state1[7]);
    printf("  Path 2: a=%x b=%x c=%x d=%x e=%x f=%x g=%x h=%x\n",
           state2[0],state2[1],state2[2],state2[3],
           state2[4],state2[5],state2[6],state2[7]);
    printf("  da[56]=0 check: a1==a2? %s\n", state1[0] == state2[0] ? "YES" : "NO");
    if (state1[0] != state2[0]) {
        printf("ERROR: da[56]!=0, candidate invalid\n");
        return 1;
    }

    /* --- Statistics accumulators --- */

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    uint64_t total_tested = 0;
    uint64_t total_collisions = 0;

    /* Per-w57 collision counts */
    uint64_t w57_collisions[NVALS];
    memset(w57_collisions, 0, sizeof(w57_collisions));

    /* W60 multiplicity distribution: mult_dist[k] = number of triples
     * with exactly k successful W60 values (0 <= k <= NVALS) */
    uint64_t mult_dist[NVALS + 1];
    memset(mult_dist, 0, sizeof(mult_dist));

    uint64_t total_triples = 0;
    uint64_t successful_triples = 0;

    /* W60 modular difference accumulator: for triples with 2+ solutions,
     * record the XOR of all pairs of successful W60 values */
    uint32_t w60_diff_xor_vals[4096];  /* enough for N=4: 16^3=4096 triples */
    int w60_diff_count = 0;

    /* Collect all successful W60 values for GF(2) rank analysis */
    uint32_t all_w60_hits[65536];  /* max possible collisions */
    int all_w60_hit_count = 0;

    /* Per-bit W60 success counts: how often is each bit 0 vs 1 in
     * successful W60 values */
    uint64_t w60_bit_one[N];
    memset(w60_bit_one, 0, sizeof(w60_bit_one));

    /* --- Main cascade DP loop --- */

    printf("\nSearching 2^%d = %u candidates...\n\n", 4*N, 1U << (4*N));

    for (uint32_t w57 = 0; w57 < NVALS; w57++) {
        uint32_t s1_57[8], s2_57[8];
        memcpy(s1_57, state1, 32);
        memcpy(s2_57, state2, 32);
        uint32_t w2_57 = find_w2(s1_57, s2_57, 57, w57);
        sha_round(s1_57, KN[57], w57);
        sha_round(s2_57, KN[57], w2_57);

        for (uint32_t w58 = 0; w58 < NVALS; w58++) {
            uint32_t s1_58[8], s2_58[8];
            memcpy(s1_58, s1_57, 32);
            memcpy(s2_58, s2_57, 32);
            uint32_t w2_58 = find_w2(s1_58, s2_58, 58, w58);
            sha_round(s1_58, KN[58], w58);
            sha_round(s2_58, KN[58], w2_58);

            for (uint32_t w59 = 0; w59 < NVALS; w59++) {
                uint32_t s1_59[8], s2_59[8];
                memcpy(s1_59, s1_58, 32);
                memcpy(s2_59, s2_58, 32);
                uint32_t w2_59 = find_w2(s1_59, s2_59, 59, w59);
                sha_round(s1_59, KN[59], w59);
                sha_round(s2_59, KN[59], w2_59);

                /* For this (w57,w58,w59) triple, try all W60 values */
                uint32_t w60_hits[NVALS];
                int n_hits = 0;

                total_triples++;

                for (uint32_t w60 = 0; w60 < NVALS; w60++) {
                    uint32_t s1_60[8], s2_60[8];
                    memcpy(s1_60, s1_59, 32);
                    memcpy(s2_60, s2_59, 32);
                    uint32_t w2_60 = find_w2(s1_60, s2_60, 60, w60);
                    sha_round(s1_60, KN[60], w60);
                    sha_round(s2_60, KN[60], w2_60);

                    /* Schedule-determined rounds 61-63 */
                    uint32_t W1f[7] = {w57, w58, w59, w60, 0, 0, 0};
                    uint32_t W2f[7] = {w2_57, w2_58, w2_59, w2_60, 0, 0, 0};

                    /* W[61] = s1(W[59]) + W[54] + s0(W[46]) + W[45] */
                    W1f[4] = (fn_s1(W1f[2]) + W1_pre[54] + fn_s0(W1_pre[46]) + W1_pre[45]) & MASK;
                    W2f[4] = (fn_s1(W2f[2]) + W2_pre[54] + fn_s0(W2_pre[46]) + W2_pre[45]) & MASK;
                    /* W[62] = s1(W[60]) + W[55] + s0(W[47]) + W[46] */
                    W1f[5] = (fn_s1(W1f[3]) + W1_pre[55] + fn_s0(W1_pre[47]) + W1_pre[46]) & MASK;
                    W2f[5] = (fn_s1(W2f[3]) + W2_pre[55] + fn_s0(W2_pre[47]) + W2_pre[46]) & MASK;
                    /* W[63] = s1(W[61]) + W[56] + s0(W[48]) + W[47] */
                    W1f[6] = (fn_s1(W1f[4]) + W1_pre[56] + fn_s0(W1_pre[48]) + W1_pre[47]) & MASK;
                    W2f[6] = (fn_s1(W2f[4]) + W2_pre[56] + fn_s0(W2_pre[48]) + W2_pre[47]) & MASK;

                    /* Run rounds 61-63 */
                    uint32_t fs1[8], fs2[8];
                    memcpy(fs1, s1_60, 32);
                    memcpy(fs2, s2_60, 32);
                    for (int r = 4; r < 7; r++) {
                        sha_round(fs1, KN[57 + r], W1f[r]);
                        sha_round(fs2, KN[57 + r], W2f[r]);
                    }

                    total_tested++;
                    int ok = 1;
                    for (int r = 0; r < 8; r++)
                        if (fs1[r] != fs2[r]) { ok = 0; break; }

                    if (ok) {
                        w60_hits[n_hits++] = w60;
                        total_collisions++;
                        w57_collisions[w57]++;

                        /* Track W60 bit pattern */
                        for (int b = 0; b < N; b++)
                            if ((w60 >> b) & 1) w60_bit_one[b]++;

                        if (all_w60_hit_count < 65536)
                            all_w60_hits[all_w60_hit_count++] = w60;
                    }
                }

                /* Record multiplicity for this triple */
                mult_dist[n_hits]++;
                if (n_hits > 0) successful_triples++;

                /* For triples with 2+ solutions, record pairwise XOR diffs */
                if (n_hits >= 2 && w60_diff_count < 4096) {
                    for (int i = 0; i < n_hits; i++)
                        for (int j = i + 1; j < n_hits; j++)
                            if (w60_diff_count < 4096)
                                w60_diff_xor_vals[w60_diff_count++] =
                                    (w60_hits[i] ^ w60_hits[j]) & MASK;
                }
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    /* ================================================================== */
    /*                          REPORT                                     */
    /* ================================================================== */

    printf("=== BASIC RESULTS ===\n");
    printf("Tested:     %llu (2^%d = %u)\n",
           (unsigned long long)total_tested, 4*N, 1U << (4*N));
    printf("Collisions: %llu\n", (unsigned long long)total_collisions);
    printf("Time:       %.6f seconds\n\n", elapsed);

    /* --- Measurement 1: Per-w57 collision counts --- */
    printf("=== MEASUREMENT 1: Per-W57 Collision Counts ===\n");
    for (uint32_t w = 0; w < NVALS; w++)
        printf("  w57=0x%x: %llu collisions\n", w, (unsigned long long)w57_collisions[w]);
    printf("\n");

    /* --- Measurement 2/3: W60 success rate --- */
    printf("=== MEASUREMENT 2/3: W60 Success Rate ===\n");
    printf("Total (w57,w58,w59) triples: %llu\n", (unsigned long long)total_triples);
    printf("Triples with >= 1 collision: %llu  (%.2f%%)\n",
           (unsigned long long)successful_triples,
           100.0 * successful_triples / total_triples);
    printf("Triples with 0 collisions:   %llu  (%.2f%%)\n",
           (unsigned long long)(total_triples - successful_triples),
           100.0 * (total_triples - successful_triples) / total_triples);
    printf("\n");

    /* --- Measurement 4: W60 multiplicity distribution --- */
    printf("=== MEASUREMENT 4: W60 Multiplicity Distribution ===\n");
    printf("(How many W60 values produce a collision per triple)\n");
    for (uint32_t k = 0; k <= NVALS; k++) {
        if (mult_dist[k] > 0)
            printf("  %2u W60 solutions: %5llu triples  (%.2f%%)\n",
                   k, (unsigned long long)mult_dist[k],
                   100.0 * mult_dist[k] / total_triples);
    }
    if (successful_triples > 0) {
        double avg_w60 = (double)total_collisions / successful_triples;
        printf("Average W60 solutions per successful triple: %.3f\n", avg_w60);
    }
    printf("\n");

    /* --- Measurement 5: W60 modular difference analysis --- */
    printf("=== MEASUREMENT 5: W60 Pairwise XOR Differences ===\n");
    if (w60_diff_count == 0) {
        printf("  No multi-solution triples found.\n");
    } else {
        printf("  %d pairwise XOR diffs from multi-solution triples:\n", w60_diff_count);
        /* Count each XOR diff value */
        uint32_t diff_counts[NVALS];
        memset(diff_counts, 0, sizeof(diff_counts));
        for (int i = 0; i < w60_diff_count; i++)
            diff_counts[w60_diff_xor_vals[i]]++;
        for (uint32_t d = 0; d < NVALS; d++)
            if (diff_counts[d] > 0)
                printf("    XOR diff 0x%x (hw=%d): %u times\n",
                       d, __builtin_popcount(d), diff_counts[d]);

        /* GF(2) rank of the XOR diffs */
        int drank = gf2_rank(w60_diff_xor_vals, w60_diff_count);
        printf("  GF(2) rank of XOR diffs: %d/%d\n", drank, N);
        if (drank < N)
            printf("  *** Diffs confined to %d-dim subspace! ***\n", drank);
    }
    printf("\n");

    /* --- Measurement 6: W60 bit-pattern analysis --- */
    printf("=== MEASUREMENT 6: W60 Bit-Pattern Analysis ===\n");
    printf("  Successful W60 values: %d total\n", all_w60_hit_count);
    if (all_w60_hit_count > 0) {
        printf("  Per-bit frequency (bit is 1):\n");
        for (int b = 0; b < N; b++)
            printf("    bit %d: %llu / %llu  (%.1f%%)\n",
                   b, (unsigned long long)w60_bit_one[b],
                   (unsigned long long)all_w60_hit_count,
                   100.0 * w60_bit_one[b] / all_w60_hit_count);

        /* GF(2) rank of successful W60 values */
        int wrank = gf2_rank(all_w60_hits, all_w60_hit_count);
        printf("  GF(2) rank of successful W60 values: %d/%d\n", wrank, N);
        if (wrank < N)
            printf("  *** W60 solutions confined to %d-dim subspace! ***\n", wrank);

        /* Distribution of successful W60 values */
        uint32_t w60_val_counts[NVALS];
        memset(w60_val_counts, 0, sizeof(w60_val_counts));
        for (int i = 0; i < all_w60_hit_count; i++)
            w60_val_counts[all_w60_hits[i]]++;
        printf("  W60 value distribution:\n");
        for (uint32_t v = 0; v < NVALS; v++)
            if (w60_val_counts[v] > 0)
                printf("    W60=0x%x: %u times\n", v, w60_val_counts[v]);
    }
    printf("\n");

    /* --- Modular difference (additive) analysis for multi-solution triples --- */
    printf("=== MEASUREMENT 7: W60 Additive Spacing ===\n");
    if (w60_diff_count == 0) {
        printf("  (No multi-solution triples)\n");
    } else {
        /* Recompute with additive differences */
        printf("  Additive diffs (mod %d) from multi-solution triples:\n", NVALS);
        uint32_t add_diff_counts[NVALS];
        memset(add_diff_counts, 0, sizeof(add_diff_counts));

        /* Re-scan triples to get additive diffs */
        for (uint32_t w57 = 0; w57 < NVALS; w57++) {
            uint32_t s1_57[8], s2_57[8];
            memcpy(s1_57, state1, 32); memcpy(s2_57, state2, 32);
            uint32_t w2_57 = find_w2(s1_57, s2_57, 57, w57);
            sha_round(s1_57, KN[57], w57); sha_round(s2_57, KN[57], w2_57);
            for (uint32_t w58 = 0; w58 < NVALS; w58++) {
                uint32_t s1_58[8], s2_58[8];
                memcpy(s1_58, s1_57, 32); memcpy(s2_58, s2_57, 32);
                uint32_t w2_58 = find_w2(s1_58, s2_58, 58, w58);
                sha_round(s1_58, KN[58], w58); sha_round(s2_58, KN[58], w2_58);
                for (uint32_t w59 = 0; w59 < NVALS; w59++) {
                    uint32_t s1_59[8], s2_59[8];
                    memcpy(s1_59, s1_58, 32); memcpy(s2_59, s2_58, 32);
                    uint32_t w2_59 = find_w2(s1_59, s2_59, 59, w59);
                    sha_round(s1_59, KN[59], w59); sha_round(s2_59, KN[59], w2_59);

                    uint32_t hits[NVALS];
                    int nh = 0;
                    for (uint32_t w60 = 0; w60 < NVALS; w60++) {
                        uint32_t s1_60[8], s2_60[8];
                        memcpy(s1_60, s1_59, 32); memcpy(s2_60, s2_59, 32);
                        uint32_t w2_60 = find_w2(s1_60, s2_60, 60, w60);
                        sha_round(s1_60, KN[60], w60); sha_round(s2_60, KN[60], w2_60);

                        uint32_t W1f[7] = {w57, w58, w59, w60, 0, 0, 0};
                        uint32_t W2f[7] = {w2_57, w2_58, w2_59, w2_60, 0, 0, 0};
                        W1f[4] = (fn_s1(W1f[2]) + W1_pre[54] + fn_s0(W1_pre[46]) + W1_pre[45]) & MASK;
                        W2f[4] = (fn_s1(W2f[2]) + W2_pre[54] + fn_s0(W2_pre[46]) + W2_pre[45]) & MASK;
                        W1f[5] = (fn_s1(W1f[3]) + W1_pre[55] + fn_s0(W1_pre[47]) + W1_pre[46]) & MASK;
                        W2f[5] = (fn_s1(W2f[3]) + W2_pre[55] + fn_s0(W2_pre[47]) + W2_pre[46]) & MASK;
                        W1f[6] = (fn_s1(W1f[4]) + W1_pre[56] + fn_s0(W1_pre[48]) + W1_pre[47]) & MASK;
                        W2f[6] = (fn_s1(W2f[4]) + W2_pre[56] + fn_s0(W2_pre[48]) + W2_pre[47]) & MASK;

                        uint32_t fs1[8], fs2[8];
                        memcpy(fs1, s1_60, 32); memcpy(fs2, s2_60, 32);
                        for (int r = 4; r < 7; r++) {
                            sha_round(fs1, KN[57 + r], W1f[r]);
                            sha_round(fs2, KN[57 + r], W2f[r]);
                        }
                        int ok = 1;
                        for (int r = 0; r < 8; r++)
                            if (fs1[r] != fs2[r]) { ok = 0; break; }
                        if (ok) hits[nh++] = w60;
                    }
                    if (nh >= 2) {
                        for (int i = 0; i < nh; i++)
                            for (int j = i + 1; j < nh; j++) {
                                uint32_t d = (hits[j] - hits[i]) & MASK;
                                add_diff_counts[d]++;
                                /* Also record reverse diff */
                                uint32_t dr = (hits[i] - hits[j]) & MASK;
                                if (dr != d) add_diff_counts[dr]++;
                            }
                    }
                }
            }
        }

        for (uint32_t d = 0; d < NVALS; d++)
            if (add_diff_counts[d] > 0)
                printf("    diff=%2u (0x%x): %u times\n", d, d, add_diff_counts[d]);
    }
    printf("\n");

    /* --- Summary / algebraic feasibility --- */
    printf("=== SUMMARY: Algebraic Feasibility ===\n");
    if (successful_triples > 0) {
        double avg = (double)total_collisions / successful_triples;
        printf("Average W60 solutions per successful triple: %.3f\n", avg);
        if (avg < 1.1)
            printf("FINDING: Nearly every successful triple has exactly 1 W60 solution.\n"
                   "         This suggests W60 is UNIQUELY DETERMINED by (w57,w58,w59)\n"
                   "         and may be computable algebraically (no search needed).\n");
        else if (avg < 2.0)
            printf("FINDING: Most successful triples have 1 W60 solution, some have 2.\n"
                   "         Algebraic computation feasible with small correction term.\n");
        else
            printf("FINDING: Multiple W60 solutions per triple (avg %.1f).\n"
                   "         Algebraic shortcut less obvious, but subspace confinement\n"
                   "         may still reduce search.\n", avg);
    }
    printf("Total collisions: %llu (expected 49 at N=4)\n",
           (unsigned long long)total_collisions);
    if (total_collisions == 49)
        printf("*** VERIFIED: All 49 collisions found ***\n");
    printf("Time: %.6f seconds\n", elapsed);

    printf("\nDone.\n");
    return 0;
}
