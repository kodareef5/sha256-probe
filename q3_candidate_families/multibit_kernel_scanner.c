/*
 * multibit_kernel_scanner.c — Test multi-bit kernels for da[56]=0 candidates
 *
 * The MSB kernel (0x80000000) is the unique CARRY-FREE single-bit kernel.
 * Multi-bit kernels (2-3 bits set) break carry-freeness but may produce
 * candidates with different thermodynamic properties.
 *
 * Tests:
 * 1. All C(32,2)=496 two-bit kernels
 * 2. Selected three-bit kernels around the MSB
 * 3. For each kernel, scans M[0] over 2^24 (fast) or 2^32 (thorough)
 * 4. Scores hits by hw56, dW61_C, and Monte Carlo hw63
 *
 * Key difference from MSB kernel: multi-bit kernels have dM[0] with
 * multiple bits set, so M1[0] XOR M2[0] is not just the MSB. This
 * means the additive and XOR differences diverge early, creating
 * qualitatively different differential propagation.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o multibit_scanner q3_candidate_families/multibit_kernel_scanner.c -lm
 * Usage: ./multibit_scanner [mode] [fill]
 *   mode: "2bit" (all 496 two-bit kernels) or "3bit" (selected three-bit)
 *   fill: hex value for M[1..15], default 0xffffffff
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
    state[0]=a;state[1]=b;state[2]=c;state[3]=d;
    state[4]=e;state[5]=f;state[6]=g;state[7]=h;
}

static inline uint32_t xorshift(uint32_t *s) {
    uint32_t x = *s; x ^= x<<13; x ^= x>>17; x ^= x<<5; *s = x; return x;
}

/* Scan one kernel over M[0] range, report any da[56]=0 hits */
static int scan_kernel(uint32_t kernel, uint32_t fill, uint64_t max_m0, int n_mc) {
    int hits = 0;

    #pragma omp parallel reduction(+:hits)
    {
#ifdef _OPENMP
        uint32_t rng = (uint32_t)(time(NULL) ^ omp_get_thread_num() * 7919 + 1);
#else
        uint32_t rng = (uint32_t)time(NULL);
#endif
        uint32_t M1[16], M2[16], s1[8], s2[8], W1[57], W2[57];

        for (int i = 1; i < 16; i++) { M1[i] = fill; M2[i] = fill; }
        M2[9] = fill ^ kernel;  /* kernel applied to word 9 */

        #pragma omp for schedule(dynamic, 4096)
        for (uint64_t m0v = 0; m0v < max_m0; m0v++) {
            M1[0] = (uint32_t)m0v;
            M2[0] = M1[0] ^ kernel;  /* kernel applied to word 0 */

            precompute(M1, s1, W1);
            precompute(M2, s2, W2);

            if (s1[0] != s2[0]) continue;

            /* da[56]=0 hit */
            hits++;
            int hw56 = 0;
            for (int r = 0; r < 8; r++) hw56 += hw(s1[r] ^ s2[r]);

            uint32_t C = (W1[54]-W2[54]) + (sigma0(W1[46])-sigma0(W2[46])) + (W1[45]-W2[45]);
            int dw61_hw = hw(C);

            /* Quick MC */
            int min_hw63 = 256;
            for (int mc = 0; mc < n_mc; mc++) {
                uint32_t w1[4], w2[4];
                for (int j = 0; j < 4; j++) { w1[j] = xorshift(&rng); w2[j] = xorshift(&rng); }

                uint32_t W1t[7], W2t[7];
                for (int j = 0; j < 4; j++) { W1t[j]=w1[j]; W2t[j]=w2[j]; }
                W1t[4]=sigma1(W1t[2])+W1[54]+sigma0(W1[46])+W1[45];
                W2t[4]=sigma1(W2t[2])+W2[54]+sigma0(W2[46])+W2[45];
                W1t[5]=sigma1(W1t[3])+W1[55]+sigma0(W1[47])+W1[46];
                W2t[5]=sigma1(W2t[3])+W2[55]+sigma0(W2[47])+W2[46];
                W1t[6]=sigma1(W1t[4])+W1[56]+sigma0(W1[48])+W1[47];
                W2t[6]=sigma1(W2t[4])+W2[56]+sigma0(W2[48])+W2[47];

                uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
                uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
                for (int i = 0; i < 7; i++) {
                    uint32_t T1a=h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+W1t[i];
                    uint32_t T2a=Sigma0(a1)+Maj(a1,b1,c1);
                    h1=g1;g1=f1;f1=e1;e1=d1+T1a;d1=c1;c1=b1;b1=a1;a1=T1a+T2a;
                    uint32_t T1b=h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+W2t[i];
                    uint32_t T2b=Sigma0(a2)+Maj(a2,b2,c2);
                    h2=g2;g2=f2;f2=e2;e2=d2+T1b;d2=c2;c2=b2;b2=a2;a2=T1b+T2b;
                }
                int thw = hw(a1^a2)+hw(b1^b2)+hw(c1^c2)+hw(d1^d2)+
                          hw(e1^e2)+hw(f1^f2)+hw(g1^g2)+hw(h1^h2);
                if (thw < min_hw63) min_hw63 = thw;
            }

            #pragma omp critical
            {
                printf("0x%08x,0x%08x,0x%08x,%d,%d,%d,%d\n",
                       kernel, (uint32_t)m0v, fill, hw(kernel), hw56, dw61_hw, min_hw63);
                fprintf(stderr, "  kernel=0x%08x m0=0x%08x hw56=%d dW61=%d hw63=%d\n",
                        kernel, (uint32_t)m0v, hw56, dw61_hw, min_hw63);
            }
        }
    }
    return hits;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);

    const char *mode = argc > 1 ? argv[1] : "2bit";
    uint32_t fill = argc > 2 ? (uint32_t)strtoul(argv[2], NULL, 0) : 0xffffffff;
    /* Use 2^28 for 2-bit sweep (fast, 496 kernels) or 2^32 for targeted */
    uint64_t max_m0 = 1ULL << 28;
    int n_mc = 1000;

    if (argc > 3) max_m0 = 1ULL << atoi(argv[3]);
    if (argc > 4) n_mc = atoi(argv[4]);

    printf("kernel,m0,fill,kernel_hw,hw56,dw61_C_hw,min_hw63\n");

    time_t t0 = time(NULL);
    int total_hits = 0;

    if (strcmp(mode, "2bit") == 0) {
        fprintf(stderr, "2-bit kernel sweep: 496 kernels × 2^%d M[0] × fill=0x%08x\n",
                (int)(log2(max_m0)+0.5), fill);

        for (int i = 31; i >= 1; i--) {
            for (int j = i - 1; j >= 0; j--) {
                uint32_t kernel = (1U << i) | (1U << j);
                int h = scan_kernel(kernel, fill, max_m0, n_mc);
                total_hits += h;
                if (h > 0) {
                    fprintf(stderr, "  ** kernel 0x%08x (bits %d,%d): %d hits **\n",
                            kernel, i, j, h);
                }
            }
        }
    } else if (strcmp(mode, "3bit") == 0) {
        fprintf(stderr, "3-bit kernel sweep (selected): fill=0x%08x\n", fill);

        /* Test 3-bit kernels with MSB set (most promising) */
        for (int i = 30; i >= 0; i--) {
            for (int j = i - 1; j >= 0; j--) {
                uint32_t kernel = 0x80000000U | (1U << i) | (1U << j);
                int h = scan_kernel(kernel, fill, max_m0, n_mc);
                total_hits += h;
                if (h > 0) {
                    fprintf(stderr, "  ** kernel 0x%08x: %d hits **\n", kernel, h);
                }
            }
        }
    } else if (strcmp(mode, "single") == 0) {
        /* Test a single specified kernel */
        uint32_t kernel = (uint32_t)strtoul(mode, NULL, 0);
        if (argc > 1) kernel = (uint32_t)strtoul(argv[1], NULL, 0);
        max_m0 = 1ULL << 32;
        fprintf(stderr, "Single kernel 0x%08x: full 2^32 scan\n", kernel);
        total_hits = scan_kernel(kernel, fill, max_m0, n_mc);
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "\nDone: %d total hits in %lds\n", total_hits, (long)(t1-t0));
    return 0;
}
