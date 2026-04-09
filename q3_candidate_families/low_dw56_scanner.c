/*
 * Low hw(dW[56]) candidate scanner.
 *
 * Hypothesis: candidates with lower hw(dW[56]) are more likely to be sr=60/61 SAT.
 * Our sole verified sr=60 SAT candidate has hw_dW56=7 (lowest of 12 by 6 bits).
 *
 * Scans M[0] over full 2^32 range for given fill, filtering:
 *   1. da[56] == 0 (candidate property)
 *   2. hw(dW[56]) <= threshold
 *
 * Compile: gcc -O3 -march=native -fopenmp -o low_dw56_scanner low_dw56_scanner.c
 * Run:     ./low_dw56_scanner [fill_hex] [hw_threshold]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

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

/* Compress 57 rounds, return state and W[56] */
static void compress_57(const uint32_t M[16], uint32_t state[8], uint32_t *w56_out) {
    uint32_t W[64];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i <= 56; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];

    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=(d+T1)&MASK; d=c; c=b; b=a; a=(T1+T2)&MASK;
    }
    state[0]=a; state[1]=b; state[2]=c; state[3]=d;
    state[4]=e; state[5]=f; state[6]=g; state[7]=h;
    *w56_out = W[56];
}

int main(int argc, char **argv) {
    uint32_t fill = 0xffffffff;
    int hw_thresh = 8;

    if (argc > 1) fill = (uint32_t)strtoul(argv[1], NULL, 16);
    if (argc > 2) hw_thresh = atoi(argv[2]);

    printf("Low hw(dW[56]) Scanner\n");
    printf("Fill: 0x%08x, HW threshold: %d\n", fill, hw_thresh);
    printf("Scanning full 2^32 M[0] range...\n\n");
    printf("%-12s %-12s %-8s %-8s\n", "M[0]", "fill", "hw_dW56", "hw_da56");
    printf("%-12s %-12s %-8s %-8s\n", "----", "----", "-------", "-------");
    fflush(stdout);

    long total_da56_hits = 0;
    long total_low_hw_hits = 0;

    #pragma omp parallel for schedule(dynamic, 1<<16) reduction(+:total_da56_hits,total_low_hw_hits)
    for (long m0_long = 0; m0_long < (1L << 32); m0_long++) {
        uint32_t m0 = (uint32_t)m0_long;

        uint32_t M1[16], M2[16];
        M1[0] = m0;
        for (int i = 1; i < 16; i++) M1[i] = fill;
        memcpy(M2, M1, sizeof(M2));
        M2[0] ^= 0x80000000;
        M2[9] ^= 0x80000000;

        uint32_t s1[8], s2[8], w56_1, w56_2;
        compress_57(M1, s1, &w56_1);
        compress_57(M2, s2, &w56_2);

        /* Check da[56] == 0 (state[0] = a register after 57 rounds) */
        uint32_t da56 = s1[0] - s2[0];
        if (da56 != 0) continue;

        total_da56_hits++;

        /* Compute dW[56] = W1[56] XOR W2[56] */
        uint32_t dw56 = w56_1 ^ w56_2;
        int hw_dw56 = hw32(dw56);

        if (hw_dw56 <= hw_thresh) {
            total_low_hw_hits++;
            #pragma omp critical
            {
                printf("0x%08x   0x%08x   %-8d %-8d  %s\n",
                       m0, fill, hw_dw56, 0,
                       hw_dw56 <= 5 ? "*** EXCELLENT ***" :
                       hw_dw56 <= 7 ? "** GOOD **" : "");
                fflush(stdout);
            }
        }

        /* Progress */
        if ((m0 & 0x0FFFFFFF) == 0) {
            #pragma omp critical
            {
                fprintf(stderr, "  Progress: 0x%08x (%.0f%%), da56_hits=%ld, low_hw=%ld\n",
                        m0, 100.0 * m0_long / (1L << 32), total_da56_hits, total_low_hw_hits);
            }
        }
    }

    printf("\n========================================\n");
    printf("COMPLETE: fill=0x%08x\n", fill);
    printf("Total da[56]=0 candidates: %ld\n", total_da56_hits);
    printf("Total with hw(dW[56]) <= %d: %ld\n", hw_thresh, total_low_hw_hits);
    printf("========================================\n");

    return 0;
}
