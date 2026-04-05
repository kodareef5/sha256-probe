/*
 * Script 54: Decoupled Padding Cooler
 *
 * FIXING THE GENETIC ALGORITHM'S DESIGN FLAW:
 * The old GA put the 2^31 M[0] scan INSIDE the fitness loop.
 * Finding da[56]=0 is ~2^-31, so most evaluations got zero signal.
 *
 * THE FIX: Keep M[0] = 0x17149975 (known da[56]=0 for all-ones).
 * Only vary M[14] and M[15] (late injection "sponge words").
 * Check if da[56]=0 SURVIVES the padding change, and if so,
 * measure the thermodynamic floor.
 *
 * M[14] and M[15] are injected at rounds 14-15 — the LATEST input words.
 * They undergo minimal ARX scrambling before schedule expansion begins.
 * Zeroing the early words (M[1..13]) and using M[14,15] as sponge
 * variables might dramatically change the thermodynamic landscape.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o padding_cooler 54_padding_cooler.c
 * Run:     ./padding_cooler
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

int main() {
    printf("==============================================\n");
    printf("DECOUPLED PADDING COOLER\n");
    printf("  Fixed M[0] = 0x17149975\n");
    printf("  Testing 3 padding strategies:\n");
    printf("    A) M[1..13]=0, vary M[14]+M[15] (sponge words)\n");
    printf("    B) M[1..13]=0xFFFFFFFF, vary M[14]+M[15]\n");
    printf("    C) Vary ALL of M[1..15] randomly (broad search)\n");
    printf("==============================================\n\n");
    fflush(stdout);

    int mc_shots = 500;
    int best_min_hw = 256;
    uint32_t best_m14 = 0, best_m15 = 0;
    int best_strategy = -1;
    int n_da56_hits = 0;

    /* Strategy A: zeros + sponge words M[14], M[15] */
    printf("--- Strategy A: M[1..13]=0, scan M[14] x M[15] ---\n"); fflush(stdout);
    time_t t0 = time(NULL);

    #pragma omp parallel for schedule(dynamic, 256) collapse(2)
    for (uint32_t m14 = 0; m14 < 65536; m14 += 1) {
        for (uint32_t m15 = 0; m15 < 65536; m15 += 1) {
            uint32_t M1[16] = {0x17149975, 0,0,0,0,0,0,0,0,0,0,0,0,0, m14, m15};
            uint32_t M2[16];
            memcpy(M2, M1, sizeof(M1));
            M2[0] ^= 0x80000000;
            M2[9] ^= 0x80000000;

            uint32_t s1[8], s2[8];
            compress_57(M1, s1);
            compress_57(M2, s2);

            if (s1[0] != s2[0]) continue;

            int hw56 = 0;
            for (int r = 0; r < 8; r++) hw56 += hw32(s1[r] ^ s2[r]);

            /* Quick MC */
            uint32_t rng = m14 * 65536 + m15 + 1;
            int min_hw = 256;
            for (int mc = 0; mc < mc_shots; mc++) {
                uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
                uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
                for (int i = 0; i < 4; i++) {
                    uint32_t w1 = xorshift32(&rng), w2 = xorshift32(&rng);
                    uint32_t T1=h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+w1;
                    uint32_t T2=Sigma0(a1)+Maj(a1,b1,c1);
                    h1=g1;g1=f1;f1=e1;e1=d1+T1;d1=c1;c1=b1;b1=a1;a1=T1+T2;
                    T1=h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+w2;
                    T2=Sigma0(a2)+Maj(a2,b2,c2);
                    h2=g2;g2=f2;f2=e2;e2=d2+T1;d2=c2;c2=b2;b2=a2;a2=T1+T2;
                }
                int hw = hw32(a1^a2)+hw32(b1^b2)+hw32(c1^c2)+hw32(d1^d2)+
                         hw32(e1^e2)+hw32(f1^f2)+hw32(g1^g2)+hw32(h1^h2);
                if (hw < min_hw) min_hw = hw;
            }

            #pragma omp critical
            {
                n_da56_hits++;
                if (min_hw < best_min_hw) {
                    best_min_hw = min_hw;
                    best_m14 = m14; best_m15 = m15;
                    best_strategy = 0;
                    printf("  A: M[14]=0x%04x M[15]=0x%04x  hw56=%d  min_hw60=%d",
                           m14, m15, hw56, min_hw);
                    if (min_hw < 80) printf(" <-- COOLER!");
                    if (min_hw < 50) printf(" <-- COLD!!");
                    printf("\n"); fflush(stdout);
                }
            }
        }
    }

    printf("  Strategy A: %d da[56]=0 hits, best min_hw60=%d (%.0fs)\n",
           n_da56_hits, best_min_hw, difftime(time(NULL), t0));
    fflush(stdout);

    /* Strategy B: all-ones + sponge (sample, not full 2^32) */
    printf("\n--- Strategy B: M[1..13]=0xFFFFFFFF, sample M[14] x M[15] ---\n"); fflush(stdout);
    t0 = time(NULL);
    int n_hits_b = 0;

    #pragma omp parallel
    {
        uint32_t rng = (uint32_t)(time(NULL) ^ omp_get_thread_num() * 1337);
        #pragma omp for schedule(dynamic, 1000)
        for (int trial = 0; trial < 10000000; trial++) {
            uint32_t m14 = xorshift32(&rng);
            uint32_t m15 = xorshift32(&rng);
            uint32_t M1[16];
            for (int i = 0; i < 16; i++) M1[i] = 0xffffffff;
            M1[0] = 0x17149975; M1[14] = m14; M1[15] = m15;
            uint32_t M2[16]; memcpy(M2, M1, sizeof(M1));
            M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;

            uint32_t s1[8], s2[8];
            compress_57(M1, s1); compress_57(M2, s2);
            if (s1[0] != s2[0]) continue;

            int hw56 = 0;
            for (int r = 0; r < 8; r++) hw56 += hw32(s1[r] ^ s2[r]);

            int min_hw = 256;
            for (int mc = 0; mc < mc_shots; mc++) {
                uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
                uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
                for (int i = 0; i < 4; i++) {
                    uint32_t w1=xorshift32(&rng), w2=xorshift32(&rng);
                    uint32_t T1=h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+w1;
                    uint32_t T2=Sigma0(a1)+Maj(a1,b1,c1);
                    h1=g1;g1=f1;f1=e1;e1=d1+T1;d1=c1;c1=b1;b1=a1;a1=T1+T2;
                    T1=h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+w2;
                    T2=Sigma0(a2)+Maj(a2,b2,c2);
                    h2=g2;g2=f2;f2=e2;e2=d2+T1;d2=c2;c2=b2;b2=a2;a2=T1+T2;
                }
                int hw = hw32(a1^a2)+hw32(b1^b2)+hw32(c1^c2)+hw32(d1^d2)+
                         hw32(e1^e2)+hw32(f1^f2)+hw32(g1^g2)+hw32(h1^h2);
                if (hw < min_hw) min_hw = hw;
            }

            #pragma omp critical
            {
                n_hits_b++;
                if (min_hw < best_min_hw) {
                    best_min_hw = min_hw;
                    best_m14 = m14; best_m15 = m15;
                    best_strategy = 1;
                    printf("  B: M[14]=0x%08x M[15]=0x%08x  hw56=%d  min_hw60=%d",
                           m14, m15, hw56, min_hw);
                    if (min_hw < 80) printf(" <-- COOLER!");
                    printf("\n"); fflush(stdout);
                }
            }
        }
    }

    printf("  Strategy B: %d da[56]=0 hits, best min_hw60=%d (%.0fs)\n",
           n_hits_b, best_min_hw, difftime(time(NULL), t0));

    printf("\n==============================================\n");
    printf("OVERALL BEST: min_hw60=%d (strategy %c)\n", best_min_hw, "ABC"[best_strategy]);
    printf("  M[14]=0x%08x M[15]=0x%08x\n", best_m14, best_m15);
    printf("  Reference: MSB kernel all-ones = min_hw60 ~ 99\n");
    printf("==============================================\n");

    return 0;
}
