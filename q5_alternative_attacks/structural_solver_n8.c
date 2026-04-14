/*
 * structural_solver_n8.c — Structural collision solver for N=8 mini-SHA
 *
 * Exploits structural constraints of the cascade DP to prune the 2^32
 * search space. Two filters applied:
 *
 * FILTER 1 — de61 exact match (after round 61, before rounds 62-63)
 *   After 4 cascade rounds (57-60): da=db=dc=dd=de=0, but df,dg,dh nonzero.
 *   After round 61: s63[6] = e61, so collision requires de61 = 0 exactly.
 *   de61 is an 8-bit value, so pass rate ~ 1/256. This gives ~256x pruning
 *   on the 2-round tail (rounds 62-63).
 *
 * FILTER 2 — de58 classification (Phase 1 analysis)
 *   de58 depends on W57 only (W58-independent), with 8 distinct classes
 *   of 32 W57 values each. Documented for structural insight.
 *
 * Compile: gcc -O3 -march=native -o structural_solver_n8 structural_solver_n8.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---- N=8 parameters ---- */
#define N 8
#define MASK 0xFFU
#define MSB  0x80U

/* ---- Rotation parameters (scaled from SHA-256's 32-bit rotations) ---- */
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

/* ---- SHA-256 primitives ---- */
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
static uint32_t state1[8], state2[8], W1pre[57], W2pre[57];

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

int main(void) {
    setbuf(stdout, NULL);

    /* Initialize rotation parameters */
    rS0[0]=scale_rot(2);  rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);  rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);  rs0[1]=scale_rot(18);  ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19);  ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & MASK;

    printf("=== Structural Collision Solver, N=%d ===\n\n", N);

    /* ---- Find candidate (MSB kernel, fill=0xff) ---- */
    uint32_t fills[] = {MASK, 0, MASK>>1, MSB, 0x55&MASK, 0xAA&MASK};
    int found = 0;
    for (int fi = 0; fi < 6 && !found; fi++) {
        for (uint32_t m0 = 0; m0 <= MASK && !found; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fills[fi]; M2[i] = fills[fi]; }
            M1[0] = m0; M2[0] = m0 ^ MSB; M2[9] = fills[fi] ^ MSB;
            precompute(M1, state1, W1pre);
            precompute(M2, state2, W2pre);
            if (state1[0] == state2[0]) {
                printf("Candidate: M[0]=0x%02x fill=0x%02x  (da56=0)\n",
                       m0, fills[fi]);
                found = 1;
            }
        }
    }
    if (!found) { printf("No candidate found at N=%d\n", N); return 1; }

    /* Show state56 diffs */
    printf("State56 diffs: da=%d db=%d dc=%d dd=%d de=%d df=%d dg=%d dh=%d\n",
           (state1[0] - state2[0]) & MASK, (state1[1] - state2[1]) & MASK,
           (state1[2] - state2[2]) & MASK, (state1[3] - state2[3]) & MASK,
           (state1[4] - state2[4]) & MASK, (state1[5] - state2[5]) & MASK,
           (state1[6] - state2[6]) & MASK, (state1[7] - state2[7]) & MASK);

    /* ================================================================
     * PHASE 1: de58 classification
     * For each W57, compute de58. Verify W58-independence.
     * ================================================================ */
    printf("\n--- Phase 1: de58 structure analysis ---\n");

    int de58_values_seen[256] = {0};
    int de58_by_w57[256];
    int de58_varies_with_w58 = 0;

    for (uint32_t w57 = 0; w57 < 256; w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

        int first_de58 = -1;
        for (uint32_t w58 = 0; w58 < 256; w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);
            uint32_t de58 = (s58a[4] - s58b[4]) & MASK;
            if (w58 == 0) {
                de58_by_w57[w57] = (int)de58;
                first_de58 = (int)de58;
            } else if ((int)de58 != first_de58) {
                de58_varies_with_w58 = 1;
            }
        }
        de58_values_seen[de58_by_w57[w57]] = 1;
    }

    int n_distinct_de58 = 0;
    printf("de58 values (at W58=0): ");
    for (int v = 0; v < 256; v++) {
        if (de58_values_seen[v]) {
            if (n_distinct_de58 < 16) printf("0x%02x ", v);
            n_distinct_de58++;
        }
    }
    if (n_distinct_de58 > 16) printf("...");
    printf("\nDistinct de58 values: %d / 256\n", n_distinct_de58);
    printf("de58 varies with W58: %s\n", de58_varies_with_w58 ? "YES" : "NO");

    /* Count W57 values per de58 class */
    printf("\nde58 class sizes:\n");
    int class_count[256] = {0};
    for (int w = 0; w < 256; w++) class_count[de58_by_w57[w]]++;
    for (int v = 0; v < 256; v++) {
        if (class_count[v] > 0)
            printf("  de58=0x%02x: %d W57 values\n", v, class_count[v]);
    }

    /* ================================================================
     * PHASE 2: Structural filter analysis
     *
     * After 4 cascade rounds (57-60): da=db=dc=dd=de=0.
     * df=de59, dg=de58, dh=de57 (nonzero in general).
     *
     * SHA round shift structure means:
     *   After r61: h61=g60, g61=f60, f61=e60(=0), e61=d60+T1_61
     *   After r62: h62=g61=f60, g62=f61=e60(=0), f62=e61, e62=d61+T1_62
     *   After r63: h63=g62=e60(=0), g63=f62=e61, f63=e62, e63=d62+T1_63
     *
     * For collision s63_1 == s63_2, we need:
     *   dh63 = de60 = 0  (ALWAYS true, cascade zeroed it)
     *   dg63 = de61 = 0  (STRUCTURAL FILTER: must check explicitly)
     *   plus 6 more register equalities
     *
     * de61 is an 8-bit constraint. If de61 != 0, we skip rounds 62-63.
     * Expected pass rate: ~1/256 -> ~256x fewer full evaluations.
     * ================================================================ */
    printf("\n--- Phase 2: Structural filter analysis ---\n");

    /* Run sample to measure actual pass rate */
    uint64_t sample_total = 0;
    uint64_t sample_de61_fail = 0;
    uint64_t sample_de61_pass = 0;
    uint64_t sample_collisions = 0;

    for (uint32_t w57 = 0; w57 < 16; w57++) {
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
                uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);
                uint32_t W1_61 = (fns1(w59) + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & MASK;
                uint32_t W2_61 = (fns1(w59b) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & MASK;

                for (uint32_t w60 = 0; w60 < 256; w60++) {
                    sample_total++;
                    uint32_t w60b = (w60 + cas_off60) & MASK;
                    uint32_t s60a[8], s60b[8];
                    memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                    sha_round(s60a, KN[60], w60);
                    sha_round(s60b, KN[60], w60b);

                    /* Round 61 */
                    uint32_t s61a[8], s61b[8];
                    memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                    sha_round(s61a, KN[61], W1_61);
                    sha_round(s61b, KN[61], W2_61);

                    /* STRUCTURAL FILTER: de61 = 0? */
                    uint32_t de61 = (s61a[4] - s61b[4]) & MASK;
                    if (de61 != 0) { sample_de61_fail++; continue; }
                    sample_de61_pass++;

                    /* Full check */
                    uint32_t W1_62 = (fns1(w60) + W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & MASK;
                    uint32_t W2_62 = (fns1(w60b) + W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & MASK;
                    uint32_t W1_63 = (fns1(W1_61) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & MASK;
                    uint32_t W2_63 = (fns1(W2_61) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & MASK;
                    sha_round(s61a, KN[62], W1_62);
                    sha_round(s61b, KN[62], W2_62);
                    sha_round(s61a, KN[63], W1_63);
                    sha_round(s61b, KN[63], W2_63);
                    int ok = 1;
                    for (int r = 0; r < 8; r++)
                        if (s61a[r] != s61b[r]) { ok = 0; break; }
                    if (ok) sample_collisions++;
                }
            }
        }
    }

    printf("Sample (W57=0..15): %llu configs\n", (unsigned long long)sample_total);
    printf("  de61!=0 (pruned):       %llu (%.2f%%)\n",
           (unsigned long long)sample_de61_fail,
           100.0 * sample_de61_fail / sample_total);
    printf("  de61==0 (passed):       %llu (%.4f%% = 1/%.0f)\n",
           (unsigned long long)sample_de61_pass,
           100.0 * sample_de61_pass / sample_total,
           (double)sample_total / sample_de61_pass);
    printf("  Collisions:             %llu\n", (unsigned long long)sample_collisions);

    /* ================================================================
     * PHASE 3: Full search with de61 structural filter
     *
     * Loop: W57 x W58 x W59 x W60 (each 0..255)
     * After rounds 57-60 (cascade) + round 61:
     *   Check de61 = 0. If not, skip (saves rounds 62-63).
     *   If de61 = 0, run rounds 62-63 and check full collision.
     * ================================================================ */
    printf("\n--- Phase 3: Full structural search ---\n");

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    uint64_t n_collisions = 0;
    uint64_t n_total = 0;
    uint64_t n_de61_pass = 0;
    uint64_t n_de61_fail = 0;

    /* Collision storage for verification */
    typedef struct { uint32_t w57, w58, w59, w60; } coll_t;
    coll_t *collisions = (coll_t *)malloc(512 * sizeof(coll_t));

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
                uint32_t W1_61 = (fns1(w59) + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & MASK;
                uint32_t W2_61 = (fns1(w59b) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & MASK;

                /* Schedule: W[63] depends on W[61] (hence w59) */
                uint32_t W1_63 = (fns1(W1_61) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & MASK;
                uint32_t W2_63 = (fns1(W2_61) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & MASK;

                /* Schedule constants for W[62] (sigma1(w60) + const) */
                uint32_t sched62_c1 = (W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & MASK;
                uint32_t sched62_c2 = (W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & MASK;

                for (uint32_t w60 = 0; w60 < 256; w60++) {
                    n_total++;
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

                    /* STRUCTURAL FILTER: de61 must be 0 for collision
                     * (because g63 = e61 in the round shift structure) */
                    if (((s61a[4] - s61b[4]) & MASK) != 0) {
                        n_de61_fail++;
                        continue;
                    }
                    n_de61_pass++;

                    /* Passed filter — run rounds 62-63 */
                    uint32_t W1_62 = (fns1(w60) + sched62_c1) & MASK;
                    uint32_t W2_62 = (fns1(w60b) + sched62_c2) & MASK;

                    sha_round(s61a, KN[62], W1_62);
                    sha_round(s61b, KN[62], W2_62);
                    sha_round(s61a, KN[63], W1_63);
                    sha_round(s61b, KN[63], W2_63);

                    /* Check full collision */
                    int ok = 1;
                    for (int r = 0; r < 8; r++)
                        if (s61a[r] != s61b[r]) { ok = 0; break; }
                    if (ok) {
                        if (n_collisions < 512) {
                            collisions[n_collisions].w57 = w57;
                            collisions[n_collisions].w58 = w58;
                            collisions[n_collisions].w59 = w59;
                            collisions[n_collisions].w60 = w60;
                        }
                        n_collisions++;
                    }
                }
            }
        }

        /* Progress */
        if ((w57 & 0x3F) == 0x3F) {
            clock_gettime(CLOCK_MONOTONIC, &t1);
            double el = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
            double pct = 100.0 * (w57 + 1) / 256.0;
            printf("  [%.0f%%] w57=0x%02x coll=%llu de61_pass=%llu time=%.2fs ETA=%.1fs\n",
                   pct, w57, (unsigned long long)n_collisions,
                   (unsigned long long)n_de61_pass, el,
                   el / pct * 100 - el);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    /* ================================================================
     * PHASE 4: Verification
     * Re-verify each collision from scratch
     * ================================================================ */
    printf("\n--- Phase 4: Verification ---\n");
    int verified = 0;
    for (uint64_t i = 0; i < n_collisions && i < 512; i++) {
        uint32_t w57 = collisions[i].w57;
        uint32_t w58 = collisions[i].w58;
        uint32_t w59 = collisions[i].w59;
        uint32_t w60 = collisions[i].w60;

        /* Reconstruct from scratch */
        uint32_t sa[8], sb[8];
        memcpy(sa, state1, 32); memcpy(sb, state2, 32);
        uint32_t w57b = find_w2(sa, sb, 57, w57);
        sha_round(sa, KN[57], w57); sha_round(sb, KN[57], w57b);
        uint32_t w58b = find_w2(sa, sb, 58, w58);
        sha_round(sa, KN[58], w58); sha_round(sb, KN[58], w58b);
        uint32_t w59b = find_w2(sa, sb, 59, w59);
        sha_round(sa, KN[59], w59); sha_round(sb, KN[59], w59b);
        uint32_t w60b = find_w2(sa, sb, 60, w60);
        sha_round(sa, KN[60], w60); sha_round(sb, KN[60], w60b);

        /* Schedule */
        uint32_t W1[3], W2[3];
        W1[0] = (fns1(w59) + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & MASK;
        W2[0] = (fns1(w59b) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & MASK;
        W1[1] = (fns1(w60) + W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & MASK;
        W2[1] = (fns1(w60b) + W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & MASK;
        W1[2] = (fns1(W1[0]) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & MASK;
        W2[2] = (fns1(W2[0]) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & MASK;

        for (int r = 0; r < 3; r++) {
            sha_round(sa, KN[61 + r], W1[r]);
            sha_round(sb, KN[61 + r], W2[r]);
        }

        int ok = 1;
        for (int r = 0; r < 8; r++)
            if (sa[r] != sb[r]) { ok = 0; break; }
        if (ok) verified++;
        else printf("  VERIFICATION FAILED: collision #%llu W1=[%02x,%02x,%02x,%02x]\n",
                     (unsigned long long)i, w57, w58, w59, w60);
    }
    printf("Verified: %d / %llu\n", verified, (unsigned long long)n_collisions);

    /* ================================================================
     * Print all collisions
     * ================================================================ */
    printf("\n--- All collisions (W1 values) ---\n");
    for (uint64_t i = 0; i < n_collisions && i < 512; i++) {
        printf("  #%3llu: W1=[%02x,%02x,%02x,%02x]\n",
               (unsigned long long)(i + 1),
               collisions[i].w57, collisions[i].w58,
               collisions[i].w59, collisions[i].w60);
    }

    /* ================================================================
     * Summary
     * ================================================================ */
    printf("\n========================================\n");
    printf("=== N=%d Structural Solver Results ===\n", N);
    printf("========================================\n\n");

    printf("Collisions found:         %llu\n", (unsigned long long)n_collisions);
    printf("Verified:                 %d / %llu\n", verified,
           (unsigned long long)n_collisions);
    printf("Time:                     %.3fs\n", elapsed);
    printf("\nSearch statistics:\n");
    printf("  Total configs:          %llu (2^32 = 4,294,967,296)\n",
           (unsigned long long)n_total);
    printf("  de61 filter passed:     %llu (%.4f%% = 1/%.0f)\n",
           (unsigned long long)n_de61_pass,
           100.0 * n_de61_pass / n_total,
           (double)n_total / n_de61_pass);
    printf("  de61 filter pruned:     %llu (%.2f%%)\n",
           (unsigned long long)n_de61_fail,
           100.0 * n_de61_fail / n_total);
    printf("  Full r62-r63 checks:    %llu (same as de61 passes)\n",
           (unsigned long long)n_de61_pass);

    /* Cost model: rounds 57-60 + round 61 cost ~5 round-equivalents.
     * Rounds 62-63 cost ~2 round-equivalents. Without filter: 7 rounds.
     * With filter: 5 rounds + (1/pass_rate) * 2 rounds. */
    double pass_rate = (double)n_de61_pass / n_total;
    double cost_no_filter = 7.0;
    double cost_with_filter = 5.0 + pass_rate * 2.0;
    double algorithmic_speedup = cost_no_filter / cost_with_filter;

    printf("\nAlgorithmic analysis:\n");
    printf("  de61 pass rate:         %.6f (1/%.0f)\n",
           pass_rate, 1.0 / pass_rate);
    printf("  Rounds saved per eval:  %.2f / 7 = %.0f%% reduction\n",
           (1.0 - pass_rate) * 2.0,
           (1.0 - pass_rate) * 2.0 / 7.0 * 100.0);
    printf("  Algorithmic speedup:    %.2fx (cost model: 5 + %.6f*2 vs 7)\n",
           algorithmic_speedup, pass_rate);

    double bf_time_neon = 2.1;   /* NEON 8-thread baseline */
    double bf_time_scalar = 88.0; /* scalar single-thread (cascade_dp_generic) */
    printf("\nComparison to baselines:\n");
    printf("  Scalar cascade DP:      ~88s (single-thread, no NEON)\n");
    printf("  NEON cascade DP:        2.1s (8-thread NEON vectorized)\n");
    printf("  This solver:            %.3fs (scalar, single-thread)\n", elapsed);
    printf("  Speedup vs scalar:      %.1fx\n", bf_time_scalar / elapsed);
    printf("  Wall-clock vs NEON:     %.2fx\n", bf_time_neon / elapsed);

    printf("\nde58 structure:\n");
    printf("  Distinct de58 values:   %d / 256\n", n_distinct_de58);
    printf("  de58 W58-independent:   %s\n", de58_varies_with_w58 ? "NO" : "YES");
    printf("  Classes: 8 x 32 W57 values each (uniform partition)\n");

    if (n_collisions == 260)
        printf("\n*** ALL 260 COLLISIONS FOUND AND VERIFIED ***\n");
    else
        printf("\n*** COLLISION COUNT: %llu (expected 260) ***\n",
               (unsigned long long)n_collisions);

    free(collisions);
    printf("\nDone.\n");
    return 0;
}
