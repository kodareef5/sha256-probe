/*
 * mitm_scanner.c — Candidate scanner with MITM-aware scoring
 *
 * Scans M[0] over 2^32 with OpenMP, finds da[56]=0 candidates,
 * then scores each by:
 *   1. hw56: total state diff HW at round 56
 *   2. dW61_C_hw: HW of the constant part of dW[61] (lower = better)
 *   3. boomerang_gap: depth-1 dW[57] contradiction HW
 *   4. dg60_hw, dh60_hw: Monte Carlo min HW of the MITM hard residue
 *   5. min_hw63: Monte Carlo best total HW after all 7 tail rounds
 *
 * Usage: ./mitm_scanner [fill] [n_monte_carlo]
 *   fill: hex value for M[1..15], default 0xffffffff
 *   n_monte_carlo: random trials per candidate, default 5000
 *
 * Output: CSV to stdout, progress to stderr
 *
 * Compile: gcc -O3 -march=native -fopenmp -o mitm_scanner q3_candidate_families/mitm_scanner.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#define MASK 0xFFFFFFFFU

static inline uint32_t ROR(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e & f) ^ (~e & g); }
static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline uint32_t Sigma0(uint32_t a) { return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22); }
static inline uint32_t Sigma1(uint32_t e) { return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25); }
static inline uint32_t sigma0(uint32_t x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline uint32_t sigma1(uint32_t x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }
static inline int hw(uint32_t x) { return __builtin_popcount(x); }

static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

/* Precompute 57 rounds. Returns state[8] and W[57]. */
static void precompute(const uint32_t M[16], uint32_t state[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];

    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=d+T1; d=c; c=b; b=a; a=T1+T2;
    }
    state[0]=a; state[1]=b; state[2]=c; state[3]=d;
    state[4]=e; state[5]=f; state[6]=g; state[7]=h;
}

/* Run 7 tail rounds (57-63) with 4 free words.
 * Returns per-register diffs in diff_out[8] and total HW. */
static int eval_tail_full(const uint32_t s1[8], const uint32_t s2[8],
                          const uint32_t W1pre[57], const uint32_t W2pre[57],
                          const uint32_t w1[4], const uint32_t w2[4],
                          uint32_t diff_out[8]) {
    uint32_t W1[7], W2[7];
    for (int i = 0; i < 4; i++) { W1[i] = w1[i]; W2[i] = w2[i]; }

    /* W[61] from schedule */
    W1[4] = sigma1(W1[2]) + W1pre[54] + sigma0(W1pre[46]) + W1pre[45];
    W2[4] = sigma1(W2[2]) + W2pre[54] + sigma0(W2pre[46]) + W2pre[45];
    /* W[62] */
    W1[5] = sigma1(W1[3]) + W1pre[55] + sigma0(W1pre[47]) + W1pre[46];
    W2[5] = sigma1(W2[3]) + W2pre[55] + sigma0(W2pre[47]) + W2pre[46];
    /* W[63] */
    W1[6] = sigma1(W1[4]) + W1pre[56] + sigma0(W1pre[48]) + W1pre[47];
    W2[6] = sigma1(W2[4]) + W2pre[56] + sigma0(W2pre[48]) + W2pre[47];

    uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
    uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];

    for (int i = 0; i < 7; i++) {
        uint32_t T1a = h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+W1[i];
        uint32_t T2a = Sigma0(a1)+Maj(a1,b1,c1);
        h1=g1;g1=f1;f1=e1;e1=d1+T1a;d1=c1;c1=b1;b1=a1;a1=T1a+T2a;

        uint32_t T1b = h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+W2[i];
        uint32_t T2b = Sigma0(a2)+Maj(a2,b2,c2);
        h2=g2;g2=f2;f2=e2;e2=d2+T1b;d2=c2;c2=b2;b2=a2;a2=T1b+T2b;
    }

    diff_out[0]=a1^a2; diff_out[1]=b1^b2; diff_out[2]=c1^c2; diff_out[3]=d1^d2;
    diff_out[4]=e1^e2; diff_out[5]=f1^f2; diff_out[6]=g1^g2; diff_out[7]=h1^h2;

    int total = 0;
    for (int i = 0; i < 8; i++) total += hw(diff_out[i]);
    return total;
}

/* Compute state at round 60 (4 rounds from state56) for register extraction */
static void eval_round60(const uint32_t s[8], const uint32_t w[4],
                         uint32_t out[8]) {
    uint32_t a=s[0],b=s[1],c=s[2],d=s[3],e=s[4],f=s[5],g=s[6],h=s[7];
    for (int i = 0; i < 4; i++) {
        uint32_t T1 = h+Sigma1(e)+Ch(e,f,g)+K[57+i]+w[i];
        uint32_t T2 = Sigma0(a)+Maj(a,b,c);
        h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;
    }
    out[0]=a; out[1]=b; out[2]=c; out[3]=d;
    out[4]=e; out[5]=f; out[6]=g; out[7]=h;
}

/* xorshift PRNG */
static inline uint32_t xorshift(uint32_t *s) {
    uint32_t x = *s;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    *s = x;
    return x;
}

typedef struct {
    uint32_t m0;
    uint32_t fill;
    int hw56;           /* total state diff HW at round 56 */
    int dw61_C_hw;      /* HW of constant part of dW[61] */
    int boomerang_hw;   /* depth-1 boomerang gap HW */
    int min_dg60_hw;    /* MC: best g60 diff HW */
    int min_dh60_hw;    /* MC: best h60 diff HW */
    int min_gh60_hw;    /* MC: best g60+h60 combined diff HW */
    int min_hw63;       /* MC: best total HW after 7 tail rounds */
    int mean_hw63;      /* MC: mean total HW after 7 tail rounds */
} candidate_result_t;

/* Maximum candidates we store */
#define MAX_RESULTS 256

static candidate_result_t results[MAX_RESULTS];
static int n_results = 0;
static int total_hits = 0;

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);

    uint32_t fill = 0xffffffff;
    int n_mc = 5000;
    if (argc > 1) fill = (uint32_t)strtoul(argv[1], NULL, 0);
    if (argc > 2) n_mc = atoi(argv[2]);

    fprintf(stderr, "MITM Scanner: fill=0x%08x, mc=%d, threads=%d\n",
            fill, n_mc,
#ifdef _OPENMP
            omp_get_max_threads()
#else
            1
#endif
    );

    /* CSV header */
    printf("m0,fill,hw56,dw61_C_hw,boomerang_hw,min_dg60,min_dh60,min_gh60,min_hw63,mean_hw63\n");

    time_t t0 = time(NULL);

    #pragma omp parallel
    {
#ifdef _OPENMP
        uint32_t rng = (uint32_t)(time(NULL) ^ (omp_get_thread_num() * 7919 + 1));
#else
        uint32_t rng = (uint32_t)time(NULL);
#endif

        uint32_t M1[16], M2[16];
        uint32_t s1[8], s2[8], W1[57], W2[57];

        for (int i = 1; i < 16; i++) { M1[i] = fill; M2[i] = fill; }
        M2[9] = fill ^ 0x80000000;

        #pragma omp for schedule(dynamic, 4096)
        for (uint64_t m0v = 0; m0v < 0x100000000ULL; m0v++) {
            M1[0] = (uint32_t)m0v;
            M2[0] = M1[0] ^ 0x80000000;

            precompute(M1, s1, W1);
            precompute(M2, s2, W2);

            if (s1[0] != s2[0]) continue; /* da[56] != 0 */

            /* === da[56] = 0 hit! Compute all metrics === */

            /* 1. hw56: total state diff at round 56 */
            int hw56 = 0;
            for (int r = 0; r < 8; r++) hw56 += hw(s1[r] ^ s2[r]);

            /* 2. dW[61] constant C:
             * dW[61] = [sigma1(W1[59]) - sigma1(W2[59])] + C
             * C = (W1[54]-W2[54]) + (sigma0(W1[46])-sigma0(W2[46])) + (W1[45]-W2[45]) */
            uint32_t C = (W1[54] - W2[54]) + (sigma0(W1[46]) - sigma0(W2[46])) + (W1[45] - W2[45]);
            int dw61_C_hw = hw(C);

            /* 3. Boomerang gap: depth-1 dW[57] contradiction.
             * h60 = e57 requires dW57 = C_e = (known from state56 e-register update)
             * d60 = a57 requires dW57 = C_a = (known from state56 a-register update)
             * gap = C_e XOR C_a (XOR of the two required additive diffs — approximation) */
            /* More precisely:
             * e57 = d56 + T1_57, where T1_57 = h56 + Sigma1(e56) + Ch(e56,f56,g56) + K[57] + W[57]
             * For de57=0: dT1_57 = -dd56 (mod 2^32)
             * similarly for da57=0: dT1_57 + dT2_57 = 0
             * The boomerang is |C_e - C_a| where C_e and C_a are the W[57]-independent parts */
            uint32_t dh56 = s1[7] ^ s2[7]; /* note: XOR diff, not additive — approximation */
            uint32_t de56 = s1[4] ^ s2[4];
            /* Better: compute what dW57 needs to be for each register to zero */
            /* For e57 = d56 + h56 + Sigma1(e56) + Ch(e56,f56,g56) + K57 + W57:
             * Need d1_56 + T1_57_msg1 = d2_56 + T1_57_msg2
             * i.e., dW57 = -(d_diff + h_diff + Sigma1_diff + Ch_diff) (mod 2^32) */
            uint32_t T1_const1_e = s1[7] + Sigma1(s1[4]) + Ch(s1[4],s1[5],s1[6]) + K[57];
            uint32_t T1_const2_e = s2[7] + Sigma1(s2[4]) + Ch(s2[4],s2[5],s2[6]) + K[57];
            /* Need: (s1[3] + T1_const1_e + W1_57) == (s2[3] + T1_const2_e + W2_57)
             * i.e., dW57 = (s2[3]+T1_const2_e) - (s1[3]+T1_const1_e)  for e-path */
            uint32_t need_dw57_e = (s2[3] + T1_const2_e) - (s1[3] + T1_const1_e);

            /* For a57: need T1+T2 to match. T2 = Sigma0(a56) + Maj(a56,b56,c56)
             * Since da56=0, dSigma0(a56)=0 and dMaj depends on db56, dc56 */
            uint32_t T2_1 = Sigma0(s1[0]) + Maj(s1[0],s1[1],s1[2]);
            uint32_t T2_2 = Sigma0(s2[0]) + Maj(s2[0],s2[1],s2[2]);
            /* Need: (T1_const1_a + W1_57 + T2_1) == (T1_const2_a + W2_57 + T2_2)
             * T1_const_a is same as T1_const_e */
            uint32_t need_dw57_a = (T1_const2_e + T2_2) - (T1_const1_e + T2_1);

            int boomerang_hw = hw(need_dw57_e ^ need_dw57_a);
            /* Note: XOR of additive diffs is an approximation.
             * True gap is |need_dw57_e - need_dw57_a| but HW of additive diff is harder */

            /* 4-5. Monte Carlo: g60/h60 diffs and full tail HW */
            int min_dg60 = 32, min_dh60 = 32, min_gh60 = 64;
            int min_hw63 = 256;
            long sum_hw63 = 0;

            for (int mc = 0; mc < n_mc; mc++) {
                uint32_t w1[4], w2[4];
                for (int j = 0; j < 4; j++) { w1[j] = xorshift(&rng); w2[j] = xorshift(&rng); }

                /* Round 60 state for g60/h60 analysis */
                uint32_t r60_1[8], r60_2[8];
                eval_round60(s1, w1, r60_1);
                eval_round60(s2, w2, r60_2);
                int dg = hw(r60_1[6] ^ r60_2[6]);
                int dh = hw(r60_1[7] ^ r60_2[7]);
                if (dg < min_dg60) min_dg60 = dg;
                if (dh < min_dh60) min_dh60 = dh;
                if (dg + dh < min_gh60) min_gh60 = dg + dh;

                /* Full 7-round tail for total collision HW */
                uint32_t diff[8];
                int total = eval_tail_full(s1, s2, W1, W2, w1, w2, diff);
                if (total < min_hw63) min_hw63 = total;
                sum_hw63 += total;
            }
            int mean_hw63 = (int)(sum_hw63 / n_mc);

            #pragma omp critical
            {
                total_hits++;
                /* Output CSV row */
                printf("0x%08x,0x%08x,%d,%d,%d,%d,%d,%d,%d,%d\n",
                       (uint32_t)m0v, fill, hw56, dw61_C_hw, boomerang_hw,
                       min_dg60, min_dh60, min_gh60, min_hw63, mean_hw63);

                /* Progress */
                if (total_hits <= 10 || total_hits % 5 == 0) {
                    time_t now = time(NULL);
                    fprintf(stderr, "  HIT #%d: M[0]=0x%08x hw56=%d dW61_C=%d boom=%d gh60=%d hw63=%d\n",
                            total_hits, (uint32_t)m0v, hw56, dw61_C_hw, boomerang_hw,
                            min_gh60, min_hw63);
                }
            }
        }
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "\nDone: %d candidates in %lds\n", total_hits, (long)(t1-t0));
    return 0;
}
