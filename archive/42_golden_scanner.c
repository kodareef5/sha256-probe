/*
 * Script 42: Thermodynamic Monte Carlo Golden Scanner
 *
 * For each M[0] that produces da[56]=0, evaluate "thermodynamic coolness":
 * generate random W[57..60] assignments and measure the state difference
 * Hamming weight at Round 60.
 *
 * A "cold" candidate (low min HW at Round 60) is more likely to be SAT
 * at sr=60 because the free words can naturally drive the state toward
 * collision without the SAT solver fighting an uphill battle.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o golden_scanner 42_golden_scanner.c -lm
 * Run:     ./golden_scanner [n_monte_carlo_per_hit]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

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
static inline int hw32(uint32_t x) { return __builtin_popcount(x); }

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

/* Compress N rounds, return state */
static void compress_n(const uint32_t M[16], int n_rounds, uint32_t state[8]) {
    uint32_t W[64];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < n_rounds && i < 64; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];

    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < n_rounds; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=d+T1; d=c; c=b; b=a; a=T1+T2;
    }
    state[0]=a; state[1]=b; state[2]=c; state[3]=d;
    state[4]=e; state[5]=f; state[6]=g; state[7]=h;
}

/* Run rounds 57-60 with specific free words, return state diff HW */
static int eval_round60_hw(const uint32_t s1[8], const uint32_t s2[8],
                           const uint32_t W1_pre[57], const uint32_t W2_pre[57],
                           uint32_t w57_1, uint32_t w58_1, uint32_t w59_1, uint32_t w60_1,
                           uint32_t w57_2, uint32_t w58_2, uint32_t w59_2, uint32_t w60_2) {
    /* Build schedule for rounds 57-60 */
    uint32_t W1[4] = {w57_1, w58_1, w59_1, w60_1};
    uint32_t W2[4] = {w57_2, w58_2, w59_2, w60_2};

    /* Run 4 rounds for msg1 */
    uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
    for (int i = 0; i < 4; i++) {
        uint32_t T1 = h1 + Sigma1(e1) + Ch(e1,f1,g1) + K[57+i] + W1[i];
        uint32_t T2 = Sigma0(a1) + Maj(a1,b1,c1);
        h1=g1; g1=f1; f1=e1; e1=d1+T1; d1=c1; c1=b1; b1=a1; a1=T1+T2;
    }

    /* Run 4 rounds for msg2 */
    uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
    for (int i = 0; i < 4; i++) {
        uint32_t T1 = h2 + Sigma1(e2) + Ch(e2,f2,g2) + K[57+i] + W2[i];
        uint32_t T2 = Sigma0(a2) + Maj(a2,b2,c2);
        h2=g2; g2=f2; f2=e2; e2=d2+T1; d2=c2; c2=b2; b2=a2; a2=T1+T2;
    }

    /* Total state diff HW at round 60 */
    return hw32(a1^a2) + hw32(b1^b2) + hw32(c1^c2) + hw32(d1^d2) +
           hw32(e1^e2) + hw32(f1^f2) + hw32(g1^g2) + hw32(h1^h2);
}

/* Simple xorshift PRNG */
static inline uint32_t xorshift32(uint32_t *state) {
    uint32_t x = *state;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    *state = x;
    return x;
}

typedef struct {
    uint32_t m0;
    int min_hw60;
    int mean_hw60;
    int hw56;          /* state diff HW at round 56 */
} candidate_t;

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    int n_mc = 1000;   /* Monte Carlo shots per candidate */
    uint32_t fill = 0xffffffff;  /* M[2..15] fill pattern */
    if (argc > 1) n_mc = atoi(argv[1]);
    if (argc > 2) fill = (uint32_t)strtoul(argv[2], NULL, 0);

    printf("Golden Scanner: Thermodynamic Monte Carlo\n");
    printf("  Monte Carlo shots per candidate: %d\n", n_mc);
    printf("  M[2..15] fill: 0x%08x\n", fill);
    printf("  Scanning M[0] over 2^32 values\n");
    printf("  Looking for da[56]=0 candidates with low Round 60 HW\n\n");

    candidate_t best[32];
    int n_best = 0;
    int n_hits = 0;
    time_t start = time(NULL);

    #pragma omp parallel
    {
        uint32_t M1[16], M2[16], s1[8], s2[8];
        uint32_t W1[57], W2[57];

        M1[1] = fill;
        for (int i = 2; i < 16; i++) M1[i] = fill;
        memcpy(M2, M1, sizeof(M1));

        uint32_t rng_state = (uint32_t)(time(NULL) ^ omp_get_thread_num() * 1337);

        #pragma omp for schedule(dynamic, 4096)
        for (uint64_t m0_val = 0; m0_val < 0x100000000ULL; m0_val++) {
            M1[0] = (uint32_t)m0_val;
            M2[0] = M1[0] ^ 0x80000000;
            M1[9] = fill;
            M2[9] = fill ^ 0x80000000;

            /* Compress 57 rounds for both */
            compress_n(M1, 57, s1);
            compress_n(M2, 57, s2);

            if (s1[0] != s2[0]) continue; /* da[56] != 0 */

            /* Found a hit! Compute base HW at round 56 */
            int hw56 = 0;
            for (int r = 0; r < 8; r++) hw56 += hw32(s1[r] ^ s2[r]);

            /* Monte Carlo: evaluate Round 60 HW with random free words */
            int min_hw = 256;
            long sum_hw = 0;

            /* Also precompute schedule words needed for W[61]-W[63] enforcement */
            for (int i = 0; i < 16; i++) W1[i] = M1[i];
            for (int i = 16; i < 57; i++)
                W1[i] = sigma1(W1[i-2]) + W1[i-7] + sigma0(W1[i-15]) + W1[i-16];
            for (int i = 0; i < 16; i++) W2[i] = M2[i];
            for (int i = 16; i < 57; i++)
                W2[i] = sigma1(W2[i-2]) + W2[i-7] + sigma0(W2[i-15]) + W2[i-16];

            for (int mc = 0; mc < n_mc; mc++) {
                uint32_t w57_1 = xorshift32(&rng_state);
                uint32_t w58_1 = xorshift32(&rng_state);
                uint32_t w59_1 = xorshift32(&rng_state);
                uint32_t w60_1 = xorshift32(&rng_state);
                uint32_t w57_2 = xorshift32(&rng_state);
                uint32_t w58_2 = xorshift32(&rng_state);
                uint32_t w59_2 = xorshift32(&rng_state);
                uint32_t w60_2 = xorshift32(&rng_state);

                int hw = eval_round60_hw(s1, s2, W1, W2,
                                         w57_1, w58_1, w59_1, w60_1,
                                         w57_2, w58_2, w59_2, w60_2);
                if (hw < min_hw) min_hw = hw;
                sum_hw += hw;
            }

            int mean_hw = (int)(sum_hw / n_mc);

            #pragma omp critical
            {
                n_hits++;
                if (n_best < 32 || min_hw < best[n_best-1].min_hw60) {
                    /* Insert into sorted list */
                    int pos = n_best < 32 ? n_best : 31;
                    for (int i = pos; i > 0 && min_hw < best[i-1].min_hw60; i--) {
                        best[i] = best[i-1];
                        pos = i - 1;
                    }
                    best[pos].m0 = (uint32_t)m0_val;
                    best[pos].min_hw60 = min_hw;
                    best[pos].mean_hw60 = mean_hw;
                    best[pos].hw56 = hw56;
                    if (n_best < 32) n_best++;

                    printf("  HIT #%d: M[0]=0x%08x  hw56=%d  min_hw60=%d  mean_hw60=%d",
                           n_hits, (uint32_t)m0_val, hw56, min_hw, mean_hw);
                    if (min_hw < 50) printf("  <-- COLD!");
                    if (min_hw < 30) printf("  <-- VERY COLD!!");
                    printf("\n");
                    fflush(stdout);
                }

                if (n_hits % 10 == 0) {
                    time_t now = time(NULL);
                    double elapsed = difftime(now, start);
                    printf("  [%d hits in %.0fs, best min_hw60=%d]\n",
                           n_hits, elapsed, best[0].min_hw60);
                    fflush(stdout);
                }
            }
        }
    }

    time_t end = time(NULL);
    double elapsed = difftime(end, start);

    printf("\n======================================================\n");
    printf("RESULTS: %d candidates found in %.0fs\n", n_hits, elapsed);
    printf("======================================================\n");
    printf("%-12s %6s %10s %10s %s\n", "M[0]", "hw56", "min_hw60", "mean_hw60", "rating");
    printf("----------------------------------------------------\n");
    for (int i = 0; i < n_best; i++) {
        const char *rating = "";
        if (best[i].min_hw60 < 20) rating = "*** GOLDEN ***";
        else if (best[i].min_hw60 < 40) rating = "** VERY COLD **";
        else if (best[i].min_hw60 < 60) rating = "* cold *";
        printf("0x%08x  %4d     %4d       %4d   %s\n",
               best[i].m0, best[i].hw56, best[i].min_hw60, best[i].mean_hw60, rating);
    }

    if (n_best > 0 && best[0].min_hw60 < 40) {
        printf("\n[!!!] GOLDEN CANDIDATE FOUND: M[0]=0x%08x (min_hw60=%d)\n",
               best[0].m0, best[0].min_hw60);
        printf("Feed this to 43_candidate_validator.py for sr=60 SAT testing!\n");
    }

    return 0;
}
