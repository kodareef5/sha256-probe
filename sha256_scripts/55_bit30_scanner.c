/*
 * Script 55: Bit-30 Kernel Scanner
 *
 * The MSB kernel (bit 31) has a thermodynamic floor of HW~100 at Round 60.
 * Bit 31 is perfectly carry-free (0x80000000 + 0x80000000 = 0 mod 2^32).
 * But that "cleanliness" traps us — the early-round dynamics are too uniform.
 *
 * Bit 30 (0x40000000) introduces 50% carry probability at the MSB.
 * This creates more complex early-round differential dynamics that might
 * break the thermodynamic floor.
 *
 * dM[0] = dM[9] = 0x40000000 (Bit 30 kernel)
 *
 * Compile: gcc -O3 -march=native -fopenmp -o bit30_scanner 55_bit30_scanner.c
 * Run:     ./bit30_scanner [mc_shots]
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
static inline uint32_t xorshift32(uint32_t *s) {
    uint32_t x = *s; x ^= x<<13; x ^= x>>17; x ^= x<<5; *s = x; return x;
}

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
    int hw56;
    int min_hw60;
    int mean_hw60;
} hit_t;

int main(int argc, char *argv[]) {
    int mc_shots = argc > 1 ? atoi(argv[1]) : 1000;
    uint32_t KERNEL = 0x40000000;  /* Bit 30 */

    printf("==============================================\n");
    printf("BIT-30 KERNEL SCANNER\n");
    printf("  Kernel: dM[0] = dM[9] = 0x%08x (Bit 30)\n", KERNEL);
    printf("  Monte Carlo shots: %d\n", mc_shots);
    printf("  Scanning M[0] over 2^32 values\n");
    printf("==============================================\n\n");
    fflush(stdout);

    /* Also compare with MSB kernel baseline */
    printf("Reference: MSB kernel (Bit 31) candidate 0x17149975 has min_hw60 ~ 99\n\n");
    fflush(stdout);

    hit_t best[16];
    int n_best = 0;
    int n_hits = 0;
    time_t start = time(NULL);

    #pragma omp parallel
    {
        uint32_t M1[16], M2[16], s1[8], s2[8];
        for (int i = 0; i < 16; i++) M1[i] = 0xffffffff;
        memcpy(M2, M1, sizeof(M1));

        uint32_t rng = (uint32_t)(time(NULL) ^ omp_get_thread_num() * 7919);

        #pragma omp for schedule(dynamic, 4096)
        for (uint64_t m0 = 0; m0 < 0x100000000ULL; m0++) {
            M1[0] = (uint32_t)m0;
            M2[0] = M1[0] ^ KERNEL;
            M1[9] = 0xffffffff;
            M2[9] = 0xffffffff ^ KERNEL;

            compress_57(M1, s1);
            compress_57(M2, s2);

            if (s1[0] != s2[0]) continue;

            /* da[56] = 0 hit! */
            int hw56 = 0;
            for (int r = 0; r < 8; r++) hw56 += hw32(s1[r] ^ s2[r]);

            /* Monte Carlo */
            int min_hw = 256;
            long sum_hw = 0;
            for (int mc = 0; mc < mc_shots; mc++) {
                uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
                uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
                for (int i = 0; i < 4; i++) {
                    uint32_t w1 = xorshift32(&rng), w2 = xorshift32(&rng);
                    uint32_t T1 = h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+w1;
                    uint32_t T2 = Sigma0(a1)+Maj(a1,b1,c1);
                    h1=g1;g1=f1;f1=e1;e1=d1+T1;d1=c1;c1=b1;b1=a1;a1=T1+T2;
                    T1 = h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+w2;
                    T2 = Sigma0(a2)+Maj(a2,b2,c2);
                    h2=g2;g2=f2;f2=e2;e2=d2+T1;d2=c2;c2=b2;b2=a2;a2=T1+T2;
                }
                int hw = hw32(a1^a2)+hw32(b1^b2)+hw32(c1^c2)+hw32(d1^d2)+
                         hw32(e1^e2)+hw32(f1^f2)+hw32(g1^g2)+hw32(h1^h2);
                if (hw < min_hw) min_hw = hw;
                sum_hw += hw;
            }

            int mean_hw = (int)(sum_hw / mc_shots);

            #pragma omp critical
            {
                n_hits++;
                printf("  HIT #%d: M[0]=0x%08x  hw56=%d  min_hw60=%d  mean_hw60=%d",
                       n_hits, (uint32_t)m0, hw56, min_hw, mean_hw);
                if (min_hw < 80) printf("  <-- COOLER!");
                if (min_hw < 50) printf("  <-- COLD!!");
                if (min_hw < 30) printf("  *** GOLDEN ***");
                printf("\n"); fflush(stdout);

                if (n_best < 16 || min_hw < best[n_best-1].min_hw60) {
                    int pos = n_best < 16 ? n_best : 15;
                    for (int i = pos; i > 0 && min_hw < best[i-1].min_hw60; i--) {
                        best[i] = best[i-1]; pos = i-1;
                    }
                    best[pos].m0 = (uint32_t)m0;
                    best[pos].hw56 = hw56;
                    best[pos].min_hw60 = min_hw;
                    best[pos].mean_hw60 = mean_hw;
                    if (n_best < 16) n_best++;
                }
            }
        }
    }

    time_t end = time(NULL);
    printf("\n==============================================\n");
    printf("RESULTS: Bit-30 Kernel (%d hits in %.0fs)\n", n_hits, difftime(end, start));
    printf("==============================================\n");
    printf("%-12s %5s %8s %8s  %s\n", "M[0]", "hw56", "min60", "mean60", "vs MSB(99)");
    for (int i = 0; i < n_best; i++) {
        const char *cmp = best[i].min_hw60 < 99 ? "BETTER" :
                         (best[i].min_hw60 == 99 ? "SAME" : "WORSE");
        printf("0x%08x  %4d   %4d     %4d   %s\n",
               best[i].m0, best[i].hw56, best[i].min_hw60, best[i].mean_hw60, cmp);
    }

    return 0;
}
