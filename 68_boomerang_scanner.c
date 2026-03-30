/*
 * Script 68: Boomerang Gap Scanner
 *
 * THE ALGEBRAIC FILTER: For sr=60 viability, a candidate needs:
 *   1. da[56] = 0 (existing condition)
 *   2. Boomerang gap = 0: Maj(a,b1,c1)-Maj(a,b2,c2) == d1-d2 at Round 56
 *
 * The paper's candidate has gap HW=9 (9-bit algebraic contradiction).
 * We need gap HW=0 for a perfect candidate, or HW<=2 for a near-miss
 * that the SAT solver might absorb.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o boomerang_scanner 68_boomerang_scanner.c
 * Run:     ./boomerang_scanner
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#ifdef _OPENMP
#include <omp.h>
#endif

static inline uint32_t ROR(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e & f) ^ (~e & g); }
static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline uint32_t Sigma0(uint32_t a) { return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22); }
static inline uint32_t Sigma1(uint32_t e) { return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25); }
static inline uint32_t sigma0f(uint32_t x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline uint32_t sigma1f(uint32_t x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }
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

static void compress_57(const uint32_t M[16], uint32_t st[8]) {
    uint32_t W[57];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++)
        W[i] = sigma1f(W[i-2]) + W[i-7] + sigma0f(W[i-15]) + W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

typedef struct {
    uint32_t m0;
    uint32_t gap;
    int gap_hw;
    int hw56;
    uint32_t dT2;
    uint32_t dd;
} hit_t;

int main() {
    printf("==============================================\n");
    printf("BOOMERANG GAP SCANNER\n");
    printf("  Filter: da[56]=0 AND Boomerang gap HW\n");
    printf("  Gap = |Maj(a,b1,c1)-Maj(a,b2,c2) - (d1-d2)|\n");
    printf("  Paper's candidate: gap HW=9 (UNSAT)\n");
    printf("  Target: gap HW=0 (algebraically perfect)\n");
    printf("==============================================\n\n");
    fflush(stdout);

    hit_t best[10];
    int n_best = 0;
    int n_da56 = 0;
    time_t start = time(NULL);

    #pragma omp parallel
    {
        uint32_t M1[16], M2[16], s1[8], s2[8];
        for (int i = 0; i < 16; i++) M1[i] = 0xffffffff;
        memcpy(M2, M1, sizeof(M1));

        #pragma omp for schedule(dynamic, 4096)
        for (uint64_t m0 = 0; m0 < 0x100000000ULL; m0++) {
            M1[0] = (uint32_t)m0;
            M2[0] = M1[0] ^ 0x80000000;
            M1[9] = 0xffffffff;
            M2[9] = 0x7fffffff;

            compress_57(M1, s1);
            compress_57(M2, s2);

            if (s1[0] != s2[0]) continue; /* da[56] != 0 */

            /* da[56] = 0 hit! Compute boomerang gap */
            uint32_t a = s1[0]; /* = s2[0] since da=0 */
            uint32_t delta_Maj = Maj(a, s1[1], s1[2]) - Maj(a, s2[1], s2[2]);
            uint32_t delta_d = s1[3] - s2[3];
            uint32_t gap = delta_Maj ^ delta_d; /* XOR to measure bitwise disagreement */
            /* Actually we want arithmetic gap: delta_Maj - delta_d */
            uint32_t arith_gap = delta_Maj - delta_d;
            int gap_hw = hw32(arith_gap);

            int hw56 = 0;
            for (int r = 0; r < 8; r++) hw56 += hw32(s1[r] ^ s2[r]);

            #pragma omp critical
            {
                n_da56++;
                int is_new_best = 0;
                if (n_best < 10 || gap_hw < best[n_best-1].gap_hw) {
                    int pos = n_best < 10 ? n_best : 9;
                    for (int i = pos; i > 0 && gap_hw < best[i-1].gap_hw; i--) {
                        best[i] = best[i-1]; pos = i-1;
                    }
                    best[pos].m0 = (uint32_t)m0;
                    best[pos].gap = arith_gap;
                    best[pos].gap_hw = gap_hw;
                    best[pos].hw56 = hw56;
                    best[pos].dT2 = delta_Maj;
                    best[pos].dd = delta_d;
                    if (n_best < 10) n_best++;
                    is_new_best = 1;
                }

                printf("  da56=0 #%d: M[0]=0x%08x  gap_hw=%d  hw56=%d",
                       n_da56, (uint32_t)m0, gap_hw, hw56);
                if (gap_hw == 0) printf("  *** PERFECT BOOMERANG! ***");
                else if (gap_hw <= 2) printf("  <-- NEAR PERFECT!");
                else if (gap_hw < 9) printf("  <-- BETTER THAN PAPER");
                if (is_new_best) printf("  [NEW BEST]");
                printf("\n"); fflush(stdout);
            }
        }
    }

    time_t end = time(NULL);
    printf("\n==============================================\n");
    printf("RESULTS: %d da[56]=0 candidates in %.0fs\n", n_da56, difftime(end, start));
    printf("==============================================\n");
    printf("%-12s %8s %6s %6s %10s %10s\n",
           "M[0]", "gap_hw", "hw56", "arith_gap", "dT2", "dd");
    for (int i = 0; i < n_best; i++) {
        printf("0x%08x  %4d     %4d   0x%08x  0x%08x  0x%08x",
               best[i].m0, best[i].gap_hw, best[i].hw56,
               best[i].gap, best[i].dT2, best[i].dd);
        if (best[i].gap_hw == 0) printf("  *** GOLDEN ***");
        else if (best[i].gap_hw <= 2) printf("  ** NEAR **");
        printf("\n");
    }

    if (n_best > 0 && best[0].gap_hw == 0) {
        printf("\n[!!!] PERFECT BOOMERANG CANDIDATE FOUND!\n");
        printf("M[0] = 0x%08x\n", best[0].m0);
        printf("Feed to: python3 43_candidate_validator.py %08x\n", best[0].m0);
    } else if (n_best > 0) {
        printf("\nBest gap HW: %d (paper's candidate: 9)\n", best[0].gap_hw);
        if (best[0].gap_hw < 9)
            printf("IMPROVEMENT over paper! Feed to validator for UNSAT rate check.\n");
    }

    return 0;
}
