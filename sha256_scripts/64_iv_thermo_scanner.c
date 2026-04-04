/*
 * Script 64: IV Thermodynamic Scanner
 *
 * Semi-free-start: the IV is a free parameter!
 * Generate random IVs, check if da[56]=0, measure Round 60 HW.
 *
 * With 256 bits of IV freedom, we should find da[56]=0 IVs much
 * more easily than scanning 32-bit M[0] (which has P~2^-31).
 * The IV directly controls the initial state, so different IVs
 * produce fundamentally different thermodynamic landscapes.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o iv_scanner 64_iv_thermo_scanner.c
 * Run:     ./iv_scanner [n_trials] [mc_shots]
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

static void compress_with_iv(const uint32_t M[16], const uint32_t iv[8],
                              int n_rounds, uint32_t st[8]) {
    uint32_t W[64];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < n_rounds && i < 64; i++)
        W[i] = sigma1f(W[i-2]) + W[i-7] + sigma0f(W[i-15]) + W[i-16];

    uint32_t a=iv[0],b=iv[1],c=iv[2],d=iv[3],e=iv[4],f=iv[5],g=iv[6],h=iv[7];
    for (int i = 0; i < n_rounds; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

typedef struct {
    uint32_t iv[8];
    int hw56;
    int min_hw60;
    int n_zero_regs;
} hit_t;

int main(int argc, char *argv[]) {
    long n_trials = argc > 1 ? atol(argv[1]) : 100000000L;
    int mc_shots = argc > 2 ? atoi(argv[2]) : 200;

    uint32_t M1[16] = {0x17149975};
    uint32_t M2[16];
    for (int i = 1; i < 16; i++) M1[i] = 0xffffffff;
    memcpy(M2, M1, sizeof(M1));
    M2[0] ^= 0x80000000;
    M2[9] ^= 0x80000000;

    printf("==============================================\n");
    printf("IV THERMODYNAMIC SCANNER\n");
    printf("  M[0] = 0x%08x (MSB kernel)\n", M1[0]);
    printf("  Trials: %ld random IVs\n", n_trials);
    printf("  MC shots per hit: %d\n", mc_shots);
    printf("  Reference: standard IV -> da[56]=0, hw56=104, min_hw60~99\n");
    printf("==============================================\n\n");
    fflush(stdout);

    hit_t best;
    best.min_hw60 = 256;
    best.n_zero_regs = 0;
    long n_hits = 0;
    time_t start = time(NULL);

    #pragma omp parallel
    {
        uint32_t rng = (uint32_t)(time(NULL) ^ omp_get_thread_num() * 7919 + 1);
        uint32_t iv[8], s1[8], s2[8];

        #pragma omp for schedule(dynamic, 10000)
        for (long trial = 0; trial < n_trials; trial++) {
            /* Generate random IV */
            for (int i = 0; i < 8; i++) iv[i] = xorshift32(&rng);

            /* Compress 57 rounds with both messages */
            compress_with_iv(M1, iv, 57, s1);
            compress_with_iv(M2, iv, 57, s2);

            /* Check da[56] */
            if (s1[0] != s2[0]) continue;

            /* da[56] = 0 hit! Count zero regs */
            int hw56 = 0;
            int n_zero = 0;
            for (int r = 0; r < 8; r++) {
                uint32_t d = s1[r] ^ s2[r];
                hw56 += hw32(d);
                if (d == 0) n_zero++;
            }

            /* Monte Carlo for min_hw60 */
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
                n_hits++;
                int is_best = 0;
                if (n_zero > best.n_zero_regs ||
                    (n_zero == best.n_zero_regs && min_hw < best.min_hw60)) {
                    memcpy(best.iv, iv, sizeof(iv));
                    best.hw56 = hw56;
                    best.min_hw60 = min_hw;
                    best.n_zero_regs = n_zero;
                    is_best = 1;
                }

                if (is_best || n_hits <= 5 || (n_hits % 100 == 0)) {
                    printf("  HIT #%ld: hw56=%d zero_regs=%d min_hw60=%d",
                           n_hits, hw56, n_zero, min_hw);
                    if (n_zero >= 2) printf(" <-- MULTI-ZERO!");
                    if (min_hw < 80) printf(" <-- COLD!");
                    if (min_hw < 50) printf(" *** GOLDEN ***");
                    if (is_best) printf(" [NEW BEST]");
                    printf("\n"); fflush(stdout);
                }
            }
        }
    }

    time_t end = time(NULL);
    double elapsed = difftime(end, start);

    printf("\n==============================================\n");
    printf("RESULTS: %ld hits from %ld trials (%.0fs)\n", n_hits, n_trials, elapsed);
    printf("  P(da[56]=0) ~ %.2e\n", (double)n_hits / n_trials);
    printf("  Best: zero_regs=%d hw56=%d min_hw60=%d\n",
           best.n_zero_regs, best.hw56, best.min_hw60);
    printf("  Best IV:\n");
    for (int i = 0; i < 8; i++)
        printf("    IV[%d] = 0x%08x\n", i, best.iv[i]);
    printf("  Reference: standard IV -> hw56=104, min_hw60=99\n");
    printf("==============================================\n");

    return 0;
}
