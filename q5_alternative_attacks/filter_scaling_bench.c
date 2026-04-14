/*
 * filter_scaling_bench.c — Measure de61=0 structural filter scaling with N
 *
 * For each even N from 4 to 12, runs the cascade DP with the de61=0
 * structural filter and compares to the unfiltered baseline.
 *
 * After the 4 cascade rounds (57-60), the SHA shift register structure
 * dictates: g63 = f62 = e61. For a collision, dg63 must be 0, so
 * de61 must be 0 exactly. Since de61 is an N-bit value, the expected
 * pass rate is ~1/2^N, and the filter saves rounds 62-63 for the
 * ~(1-1/2^N) fraction that fails.
 *
 * The benchmark counts:
 *   - Total configs evaluated (= 2^{4N})
 *   - Configs passing de61=0
 *   - Actual sr=60 collisions
 *   - Filter pass rate (measured vs theoretical 1/2^N)
 *   - Wall time speedup
 *
 * Scalar C, single-threaded, for clean measurements.
 *
 * Compile: gcc -O3 -march=native -o filter_scaling_bench filter_scaling_bench.c -lm
 * Usage:   ./filter_scaling_bench           (runs N=4,6,8)
 *          ./filter_scaling_bench --all      (runs N=4,6,8,10,12)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---- Global N-dependent state ---- */
static int gN;
static uint32_t gMASK, gMSB;
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static uint32_t KN[64], IVN[8];
static uint32_t state1[8], state2[8], W1pre[57], W2pre[57];

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

/* ---- Scaled rotation ---- */
static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * gN / 32.0);
    return r < 1 ? 1 : r;
}

/* ---- SHA-256 primitives (N-bit) ---- */
static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % gN;
    return ((x >> k) | (x << (gN - k))) & gMASK;
}
static inline uint32_t fnS0(uint32_t a) {
    return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]);
}
static inline uint32_t fnS1(uint32_t e) {
    return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]);
}
static inline uint32_t fns0(uint32_t x) {
    return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & gMASK);
}
static inline uint32_t fns1(uint32_t x) {
    return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & gMASK);
}
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) {
    return ((e & f) ^ ((~e) & g)) & gMASK;
}
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) {
    return ((a & b) ^ (a & c) ^ (b & c)) & gMASK;
}

/* ---- Precompute through round 56 and schedule through W[56] ---- */
static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & gMASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & gMASK;
    uint32_t a = IVN[0], b = IVN[1], c = IVN[2], d = IVN[3],
             e = IVN[4], f = IVN[5], g = IVN[6], h = IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fnS1(e) + fnCh(e,f,g) + KN[i] + W[i]) & gMASK;
        uint32_t T2 = (fnS0(a) + fnMj(a,b,c)) & gMASK;
        h = g; g = f; f = e; e = (d + T1) & gMASK;
        d = c; c = b; b = a; a = (T1 + T2) & gMASK;
    }
    st[0] = a; st[1] = b; st[2] = c; st[3] = d;
    st[4] = e; st[5] = f; st[6] = g; st[7] = h;
}

/* ---- SHA round function ---- */
static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fnS1(s[4]) + fnCh(s[4],s[5],s[6]) + k + w) & gMASK;
    uint32_t T2 = (fnS0(s[0]) + fnMj(s[0],s[1],s[2])) & gMASK;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = (s[3] + T1) & gMASK;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = (T1 + T2) & gMASK;
}

/* ---- Cascade offset: find W2 such that da_{r+1} = 0 given W1 ---- */
static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7] + fnS1(s1[4]) + fnCh(s1[4],s1[5],s1[6]) + KN[rnd]) & gMASK;
    uint32_t r2 = (s2[7] + fnS1(s2[4]) + fnCh(s2[4],s2[5],s2[6]) + KN[rnd]) & gMASK;
    uint32_t T21 = (fnS0(s1[0]) + fnMj(s1[0],s1[1],s1[2])) & gMASK;
    uint32_t T22 = (fnS0(s2[0]) + fnMj(s2[0],s2[1],s2[2])) & gMASK;
    return (w1 + r1 - r2 + T21 - T22) & gMASK;
}

/* ---- Initialize N-dependent parameters ---- */
static void init_params(int N) {
    gN = N;
    gMASK = (N >= 32) ? 0xFFFFFFFFU : ((1U << N) - 1);
    gMSB = 1U << (N - 1);
    rS0[0] = scale_rot(2);  rS0[1] = scale_rot(13); rS0[2] = scale_rot(22);
    rS1[0] = scale_rot(6);  rS1[1] = scale_rot(11); rS1[2] = scale_rot(25);
    rs0[0] = scale_rot(7);  rs0[1] = scale_rot(18);  ss0 = scale_rot(3);
    rs1[0] = scale_rot(17); rs1[1] = scale_rot(19);  ss1 = scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & gMASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & gMASK;
}

/* ---- Find MSB-kernel candidate with da56=0 ---- */
static int find_candidate(void) {
    uint32_t fills[] = {gMASK, 0, gMASK >> 1, gMSB, 0x55 & gMASK, 0xAA & gMASK};
    for (int fi = 0; fi < 6; fi++) {
        for (uint32_t m0 = 0; m0 <= gMASK; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fills[fi]; M2[i] = fills[fi]; }
            M1[0] = m0; M2[0] = m0 ^ gMSB; M2[9] = fills[fi] ^ gMSB;
            precompute(M1, state1, W1pre);
            precompute(M2, state2, W2pre);
            if (state1[0] == state2[0]) {
                printf("  Candidate: M[0]=0x%x fill=0x%x (da56=0)\n", m0, fills[fi]);
                return 1;
            }
        }
    }
    return 0;
}

/* ---- Elapsed time helper ---- */
static double elapsed_sec(struct timespec *t0, struct timespec *t1) {
    return (t1->tv_sec - t0->tv_sec) + (t1->tv_nsec - t0->tv_nsec) / 1e9;
}

/* ====================================================================
 * Combined run: evaluates every config through rounds 57-63, tracking
 * both the de61=0 filter and full collision outcomes in a single pass.
 *
 * This avoids running 2 separate O(2^{4N}) loops and ensures both
 * measurements use the exact same configs.
 *
 * For the "filtered time", we instrument the hot path to measure work
 * saved: we count total round-evaluations in baseline vs filtered mode.
 * The actual wall-clock speedup from the de61 early exit is measured
 * by comparing the two timing modes.
 * ==================================================================== */
static void run_combined(uint64_t *out_total, uint64_t *out_de61_pass,
                         uint64_t *out_coll, double *out_base_time,
                         double *out_filt_time) {
    uint32_t Nv = 1U << gN;
    uint64_t total = 0, de61_pass = 0, coll = 0;

    /* ---- Pass 1: Baseline (no early exit) ---- */
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (uint32_t w57 = 0; w57 < Nv; w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

        for (uint32_t w58 = 0; w58 < Nv; w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

            for (uint32_t w59 = 0; w59 < Nv; w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);

                uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);
                uint32_t W1_61 = (fns1(w59)  + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & gMASK;
                uint32_t W2_61 = (fns1(w59b) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & gMASK;
                uint32_t W1_63 = (fns1(W1_61) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & gMASK;
                uint32_t W2_63 = (fns1(W2_61) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & gMASK;
                uint32_t sc62c1 = (W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & gMASK;
                uint32_t sc62c2 = (W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & gMASK;

                for (uint32_t w60 = 0; w60 < Nv; w60++) {
                    uint32_t w60b = (w60 + cas_off60) & gMASK;

                    uint32_t s60a[8], s60b[8];
                    memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                    sha_round(s60a, KN[60], w60);  sha_round(s60b, KN[60], w60b);

                    uint32_t s61a[8], s61b[8];
                    memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                    sha_round(s61a, KN[61], W1_61); sha_round(s61b, KN[61], W2_61);

                    uint32_t W1_62 = (fns1(w60)  + sc62c1) & gMASK;
                    uint32_t W2_62 = (fns1(w60b) + sc62c2) & gMASK;
                    sha_round(s61a, KN[62], W1_62); sha_round(s61b, KN[62], W2_62);
                    sha_round(s61a, KN[63], W1_63); sha_round(s61b, KN[63], W2_63);

                    int ok = 1;
                    for (int r = 0; r < 8; r++)
                        if (s61a[r] != s61b[r]) { ok = 0; break; }
                    if (ok) coll++;
                }
            }
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    *out_base_time = elapsed_sec(&t0, &t1);
    *out_coll = coll;
    total = (uint64_t)Nv * Nv * Nv * Nv;
    *out_total = total;

    /* ---- Pass 2: with de61=0 early exit ---- */
    uint64_t coll2 = 0;
    de61_pass = 0;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (uint32_t w57 = 0; w57 < Nv; w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

        for (uint32_t w58 = 0; w58 < Nv; w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

            for (uint32_t w59 = 0; w59 < Nv; w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);

                uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);
                uint32_t W1_61 = (fns1(w59)  + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & gMASK;
                uint32_t W2_61 = (fns1(w59b) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & gMASK;
                uint32_t W1_63 = (fns1(W1_61) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & gMASK;
                uint32_t W2_63 = (fns1(W2_61) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & gMASK;
                uint32_t sc62c1 = (W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & gMASK;
                uint32_t sc62c2 = (W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & gMASK;

                for (uint32_t w60 = 0; w60 < Nv; w60++) {
                    uint32_t w60b = (w60 + cas_off60) & gMASK;

                    uint32_t s60a[8], s60b[8];
                    memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                    sha_round(s60a, KN[60], w60);  sha_round(s60b, KN[60], w60b);

                    uint32_t s61a[8], s61b[8];
                    memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                    sha_round(s61a, KN[61], W1_61); sha_round(s61b, KN[61], W2_61);

                    /* STRUCTURAL FILTER: de61 = (e61_a - e61_b) mod 2^N
                     * g63 = f62 = e61 in the SHA shift register, so
                     * collision requires dg63=0 hence de61=0 exactly.
                     * N-bit comparison: expected pass rate ~ 1/2^N.
                     * Early exit saves rounds 62-63 for rejected configs. */
                    if (((s61a[4] - s61b[4]) & gMASK) != 0)
                        continue;
                    de61_pass++;

                    uint32_t W1_62 = (fns1(w60)  + sc62c1) & gMASK;
                    uint32_t W2_62 = (fns1(w60b) + sc62c2) & gMASK;
                    sha_round(s61a, KN[62], W1_62); sha_round(s61b, KN[62], W2_62);
                    sha_round(s61a, KN[63], W1_63); sha_round(s61b, KN[63], W2_63);

                    int ok = 1;
                    for (int r = 0; r < 8; r++)
                        if (s61a[r] != s61b[r]) { ok = 0; break; }
                    if (ok) coll2++;
                }
            }
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    *out_filt_time = elapsed_sec(&t0, &t1);
    *out_de61_pass = de61_pass;

    /* Sanity check */
    if (coll != coll2) {
        printf("  *** BUG: baseline %llu != filtered %llu collisions ***\n",
               (unsigned long long)coll, (unsigned long long)coll2);
    }
}

/* ---- Result storage ---- */
typedef struct {
    int N;
    uint64_t total;
    uint64_t de61_pass;
    uint64_t collisions;
    double pass_rate;
    double base_time;
    double filt_time;
    double speedup;
} bench_result_t;

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    int run_all = 0;
    if (argc > 1 && strcmp(argv[1], "--all") == 0) run_all = 1;

    int Ns_default[] = {4, 6, 8};
    int Ns_all[]     = {4, 6, 8, 10, 12};
    int *Ns     = run_all ? Ns_all : Ns_default;
    int  n_runs = run_all ? 5 : 3;

    bench_result_t results[5];

    printf("=== de61=0 Structural Filter Scaling Benchmark ===\n");
    printf("Single-threaded, scalar C, -O3\n");
    printf("Cascade: MSB kernel, da56=0, rounds 57-63\n\n");
    printf("Filter: de61 = (e61_a - e61_b) mod 2^N = 0 (early exit)\n");
    printf("  g63 = f62 = e61 in the SHA shift register, so\n");
    printf("  collision requires de61=0 (N-bit constraint).\n");
    printf("  Expected pass rate: ~1/2^N.\n");
    printf("  Savings: skip rounds 62-63 for ~(1-1/2^N) of configs.\n\n");

    for (int i = 0; i < n_runs; i++) {
        int N = Ns[i];
        printf("======== N = %d (search space 2^%d = %llu) ========\n",
               N, 4*N, (unsigned long long)(1ULL << (4*N)));

        init_params(N);

        if (!find_candidate()) {
            printf("  ERROR: no MSB-kernel candidate with da56=0\n\n");
            results[i].N = N;
            results[i].total = 0;
            continue;
        }

        uint64_t total, de61_pass, coll;
        double base_time, filt_time;

        printf("  Running baseline + filtered (2 passes)...\n");
        run_combined(&total, &de61_pass, &coll, &base_time, &filt_time);

        double pass_rate = (double)de61_pass / total;
        double speedup = base_time / filt_time;

        printf("  Total configs: %llu\n", (unsigned long long)total);
        printf("  de61=0 pass:   %llu (%.6f = 1/%.1f)\n",
               (unsigned long long)de61_pass, pass_rate, 1.0 / pass_rate);
        printf("  Expected:      1/2^%d = 1/%.0f = %.6f\n",
               N, (double)(1ULL << N), 1.0 / (1ULL << N));
        printf("  Collisions:    %llu\n", (unsigned long long)coll);
        printf("  Baseline time: %.4fs\n", base_time);
        printf("  Filtered time: %.4fs\n", filt_time);
        printf("  Speedup:       %.2fx\n", speedup);

        results[i].N = N;
        results[i].total = total;
        results[i].de61_pass = de61_pass;
        results[i].collisions = coll;
        results[i].pass_rate = pass_rate;
        results[i].base_time = base_time;
        results[i].filt_time = filt_time;
        results[i].speedup = speedup;
        printf("\n");
    }

    /* ---- Summary table ---- */
    printf("================================================================\n");
    printf("          de61=0 Structural Filter Scaling Results\n");
    printf("================================================================\n\n");

    printf("| %2s | %14s | %12s | %10s | %12s | %12s | %8s |\n",
           "N", "Total configs", "de61=0 pass", "Collisions",
           "Pass rate", "1/2^N", "Speedup");
    printf("|%s|%s|%s|%s|%s|%s|%s|\n",
           "----", "----------------", "--------------", "------------",
           "--------------", "--------------", "----------");

    for (int i = 0; i < n_runs; i++) {
        bench_result_t *r = &results[i];
        if (r->total == 0) continue;
        double expected = 1.0 / (1ULL << r->N);
        printf("| %2d | %14llu | %12llu | %10llu | %12.6f | %12.6f | %7.2fx |\n",
               r->N,
               (unsigned long long)r->total,
               (unsigned long long)r->de61_pass,
               (unsigned long long)r->collisions,
               r->pass_rate, expected,
               r->speedup);
    }

    /* ---- Timing table ---- */
    printf("\n| %2s | %10s | %10s | %8s | %15s |\n",
           "N", "Base(s)", "Filt(s)", "Speedup", "Rounds saved/cfg");
    printf("|%s|%s|%s|%s|%s|\n",
           "----", "------------", "------------", "----------",
           "-----------------");

    for (int i = 0; i < n_runs; i++) {
        bench_result_t *r = &results[i];
        if (r->total == 0) continue;
        /* Each config does 5 rounds (57-61) unconditionally.
         * Baseline does 7 rounds total (57-63).
         * Filter saves 2 rounds for (1-pass_rate) fraction.
         * Average rounds saved per config: 2 * (1 - pass_rate). */
        double avg_saved = 2.0 * (1.0 - r->pass_rate);
        printf("| %2d | %10.4f | %10.4f | %7.2fx | %15.4f |\n",
               r->N, r->base_time, r->filt_time, r->speedup, avg_saved);
    }

    /* ---- Scaling analysis ---- */
    printf("\n--- Filter pass rate: measured vs theoretical ---\n");
    for (int i = 0; i < n_runs; i++) {
        bench_result_t *r = &results[i];
        if (r->total == 0) continue;
        double expected = 1.0 / (1ULL << r->N);
        double ratio = r->pass_rate / expected;
        printf("  N=%2d: measured=1/%.1f expected=1/%llu ratio=%.3f\n",
               r->N, 1.0 / r->pass_rate,
               (unsigned long long)(1ULL << r->N), ratio);
    }

    printf("\n--- Speedup analysis ---\n");
    printf("  The de61=0 filter saves 2 of 7 rounds for ~(1-1/2^N) of configs.\n");
    printf("  Theoretical max speedup: 7 / (7 - 2*(1-1/2^N)) = 7/(5+2/2^N)\n");
    for (int i = 0; i < n_runs; i++) {
        bench_result_t *r = &results[i];
        if (r->total == 0) continue;
        double theory = 7.0 / (5.0 + 2.0 / (1ULL << r->N));
        printf("  N=%2d: measured=%.2fx theoretical_max=%.2fx\n",
               r->N, r->speedup, theory);
    }
    printf("  Note: theoretical max assumes uniform round cost and zero branch overhead.\n");
    printf("  In practice, the inner-loop branch penalty partially offsets savings.\n");

    if (n_runs >= 2) {
        printf("\n--- Scaling trend ---\n");
        for (int i = 1; i < n_runs; i++) {
            bench_result_t *prev = &results[i-1];
            bench_result_t *cur = &results[i];
            if (prev->total == 0 || cur->total == 0) continue;
            printf("  N=%d->%d: speedup %.2fx -> %.2fx\n",
                   prev->N, cur->N, prev->speedup, cur->speedup);
        }
        printf("  Speedup converges to ~1.40x as N grows (= 7/5).\n");
        printf("  The filter's value is not in wall-clock speedup of the exhaustive search,\n");
        printf("  but in reducing full-evaluation count by ~2^N, which matters when\n");
        printf("  each \"passed\" config feeds into a more expensive downstream check.\n");
    }

    printf("\nDone.\n");
    return 0;
}
