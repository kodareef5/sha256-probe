/*
 * non_msb_kernel_scanner.c — Issue #20: scan single-bit non-MSB kernels.
 *
 * Every prior candidate uses dM[0] = dM[9] = 0x80000000 (MSB).
 * Test bit positions 0..30 to see:
 *   1. Do non-MSB kernels admit da[56]=0 candidates at all?
 *   2. How does the candidate density compare to MSB?
 *   3. What's the typical state HW at round 56 for non-MSB hits?
 *
 * For each kernel bit position b in {0..31}:
 *   For each M[0] in {0..2^32}:
 *     Compute dM[0]=dM[9]=(1<<b)
 *     Check da[56]=0
 *     Record state HW
 *
 * Output: candidate counts per kernel position, best HW per position.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o /tmp/nmk_scan q5_alternative_attacks/non_msb_kernel_scanner.c
 * Run: /tmp/nmk_scan [bit_position] [fill]
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

static void compress_to_56(const uint32_t M[16], uint32_t state[8]) {
    uint32_t W[57];
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

int main(int argc, char **argv) {
    int bit_pos = argc > 1 ? atoi(argv[1]) : 30;
    uint32_t fill = argc > 2 ? (uint32_t)strtoul(argv[2], NULL, 16) : 0xffffffff;
    long max_m0 = argc > 3 ? atol(argv[3]) : (1L << 32);

    uint32_t kernel_diff = 1U << bit_pos;
    fprintf(stderr, "Non-MSB kernel scanner\n");
    fprintf(stderr, "Bit position: %d (kernel diff = 0x%08x)\n", bit_pos, kernel_diff);
    fprintf(stderr, "Fill: 0x%08x\n", fill);
    fprintf(stderr, "Max M[0]: 0x%lx\n\n", max_m0);

    long da56_hits = 0;
    int best_hw = 256;
    uint32_t best_m0 = 0;
    int hw_dist[257] = {0};

    time_t t0 = time(NULL);

    #pragma omp parallel for schedule(dynamic, 1<<16) reduction(+:da56_hits)
    for (long m0v = 0; m0v < max_m0; m0v++) {
        uint32_t m0 = (uint32_t)m0v;
        uint32_t M1[16], M2[16];
        M1[0] = m0;
        for (int i = 1; i < 16; i++) M1[i] = fill;
        memcpy(M2, M1, sizeof(M2));
        M2[0] ^= kernel_diff;
        M2[9] ^= kernel_diff;

        uint32_t s1[8], s2[8];
        compress_to_56(M1, s1);
        compress_to_56(M2, s2);

        if (s1[0] != s2[0]) continue;

        int hw_total = 0;
        for (int r = 0; r < 8; r++) hw_total += hw(s1[r] ^ s2[r]);

        #pragma omp atomic
        hw_dist[hw_total]++;

        da56_hits++;

        if (hw_total < best_hw) {
            #pragma omp critical
            {
                if (hw_total < best_hw) {
                    best_hw = hw_total;
                    best_m0 = m0;
                    fprintf(stderr, "  m0=0x%08x: hw=%d\n", m0, hw_total);
                }
            }
        }
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "\nDone in %lds\n", (long)(t1-t0));
    fprintf(stderr, "Total da[56]=0 candidates: %ld\n", da56_hits);
    fprintf(stderr, "Best state HW: %d\n", best_hw);
    fprintf(stderr, "Best M[0]: 0x%08x\n", best_m0);

    /* Print HW distribution */
    fprintf(stderr, "\nHW distribution:\n");
    for (int h = 0; h < 257; h++) {
        if (hw_dist[h] > 0) {
            fprintf(stderr, "  HW=%3d: %d\n", h, hw_dist[h]);
        }
    }

    /* Output for parsing */
    printf("BIT %d FILL 0x%08x HITS %ld BEST_HW %d BEST_M0 0x%08x\n",
           bit_pos, fill, da56_hits, best_hw, best_m0);

    return 0;
}
