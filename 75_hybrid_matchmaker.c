/*
 * Script 75: Hybrid C-SAT Matchmaker
 *
 * Fuses C brute-force (for padding search) with the MITM geometry insight.
 *
 * The MITM anchor at round 60 aligns 232/256 bits easily. The last 24 bits
 * (in g60 and h60) are the bottleneck. g60=e58, h60=e57 — they carry the
 * oldest e-register differences.
 *
 * Strategy:
 *   1. Fix M[0]=0x17149975
 *   2. Vary M[14] and M[15] (late injection sponge words)
 *   3. For each padding that produces da[56]=0:
 *      a. Randomize W[57..59] (10K shots)
 *      b. Push forward to round 60
 *      c. Measure HW(dg60) + HW(dh60) — the MITM bottleneck registers
 *      d. Keep the padding with the lowest bottleneck HW
 *
 * The paper's candidate has bottleneck HW floor ~18/64. If we find a
 * padding with floor <5, the MITM SAT instance should close.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o hybrid_match 75_hybrid_matchmaker.c
 * Run:     ./hybrid_match [mc_shots]
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

/* Push forward 4 rounds (57-60) and return g60+h60 diff HW */
static int eval_gh60(const uint32_t s1[8], const uint32_t s2[8],
                     uint32_t w57_1, uint32_t w58_1, uint32_t w59_1, uint32_t w60_1,
                     uint32_t w57_2, uint32_t w58_2, uint32_t w59_2, uint32_t w60_2) {
    uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
    uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
    uint32_t W1[4]={w57_1,w58_1,w59_1,w60_1}, W2[4]={w57_2,w58_2,w59_2,w60_2};
    for (int i=0;i<4;i++) {
        uint32_t T1=h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+W1[i];
        uint32_t T2=Sigma0(a1)+Maj(a1,b1,c1);
        h1=g1;g1=f1;f1=e1;e1=d1+T1;d1=c1;c1=b1;b1=a1;a1=T1+T2;
        T1=h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+W2[i];
        T2=Sigma0(a2)+Maj(a2,b2,c2);
        h2=g2;g2=f2;f2=e2;e2=d2+T1;d2=c2;c2=b2;b2=a2;a2=T1+T2;
    }
    return hw32(g1^g2) + hw32(h1^h2);
}

/* Also return total HW for diagnostics */
static int eval_total60(const uint32_t s1[8], const uint32_t s2[8],
                        uint32_t w57_1, uint32_t w58_1, uint32_t w59_1, uint32_t w60_1,
                        uint32_t w57_2, uint32_t w58_2, uint32_t w59_2, uint32_t w60_2) {
    uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
    uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
    uint32_t W1[4]={w57_1,w58_1,w59_1,w60_1}, W2[4]={w57_2,w58_2,w59_2,w60_2};
    for (int i=0;i<4;i++) {
        uint32_t T1=h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+W1[i];
        uint32_t T2=Sigma0(a1)+Maj(a1,b1,c1);
        h1=g1;g1=f1;f1=e1;e1=d1+T1;d1=c1;c1=b1;b1=a1;a1=T1+T2;
        T1=h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+W2[i];
        T2=Sigma0(a2)+Maj(a2,b2,c2);
        h2=g2;g2=f2;f2=e2;e2=d2+T1;d2=c2;c2=b2;b2=a2;a2=T1+T2;
    }
    return hw32(a1^a2)+hw32(b1^b2)+hw32(c1^c2)+hw32(d1^d2)+
           hw32(e1^e2)+hw32(f1^f2)+hw32(g1^g2)+hw32(h1^h2);
}

typedef struct {
    uint32_t m14, m15;
    int min_gh_hw;
    int min_total_hw;
    int hw56;
} hit_t;

int main(int argc, char *argv[]) {
    int mc_shots = argc > 1 ? atoi(argv[1]) : 5000;

    printf("==============================================\n");
    printf("HYBRID C-SAT MATCHMAKER\n");
    printf("  Target: minimize g60+h60 diff HW\n");
    printf("  Baseline (all-ones): g60+h60 floor ~18/64\n");
    printf("  Target: <5/64 for MITM to close\n");
    printf("  MC shots per hit: %d\n", mc_shots);
    printf("==============================================\n\n");
    fflush(stdout);

    /* First, establish baseline with all-ones padding */
    {
        uint32_t M1[16] = {0x17149975};
        uint32_t M2[16];
        for (int i=1;i<16;i++) M1[i] = 0xffffffff;
        memcpy(M2, M1, sizeof(M1));
        M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;
        uint32_t s1[8], s2[8];
        compress_57(M1, s1); compress_57(M2, s2);
        uint32_t rng = 42;
        int min_gh = 64;
        for (int mc=0; mc<mc_shots; mc++) {
            int gh = eval_gh60(s1, s2,
                xorshift32(&rng),xorshift32(&rng),xorshift32(&rng),xorshift32(&rng),
                xorshift32(&rng),xorshift32(&rng),xorshift32(&rng),xorshift32(&rng));
            if (gh < min_gh) min_gh = gh;
        }
        printf("  Baseline (all-ones): min g60+h60 HW = %d/64\n\n", min_gh);
        fflush(stdout);
    }

    hit_t best;
    best.min_gh_hw = 64;
    int n_hits = 0;
    time_t start = time(NULL);

    /* Scan M[14] x M[15] with M[1..13]=0xFFFFFFFF, M[0] fixed */
    /* Full 2^64 is impossible. Sample randomly. */
    long n_trials = 100000000L; /* 100M random (M14,M15) pairs */

    printf("  Scanning %ld random (M[14],M[15]) pairs...\n", n_trials);
    fflush(stdout);

    #pragma omp parallel
    {
        uint32_t rng = (uint32_t)(time(NULL) ^ omp_get_thread_num() * 7919);
        uint32_t M1[16], M2[16], s1[8], s2[8];

        for (int i=0;i<16;i++) M1[i] = 0xffffffff;
        M1[0] = 0x17149975;

        #pragma omp for schedule(dynamic, 10000)
        for (long trial = 0; trial < n_trials; trial++) {
            uint32_t m14 = xorshift32(&rng);
            uint32_t m15 = xorshift32(&rng);
            M1[14] = m14; M1[15] = m15;
            memcpy(M2, M1, sizeof(M1));
            M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;

            compress_57(M1, s1); compress_57(M2, s2);
            if (s1[0] != s2[0]) continue; /* da[56] != 0 */

            int hw56 = 0;
            for (int r=0;r<8;r++) hw56 += hw32(s1[r]^s2[r]);

            /* MC evaluation for g60+h60 */
            int min_gh = 64, min_total = 256;
            for (int mc=0; mc<mc_shots; mc++) {
                int gh = eval_gh60(s1, s2,
                    xorshift32(&rng),xorshift32(&rng),xorshift32(&rng),xorshift32(&rng),
                    xorshift32(&rng),xorshift32(&rng),xorshift32(&rng),xorshift32(&rng));
                if (gh < min_gh) min_gh = gh;
            }

            #pragma omp critical
            {
                n_hits++;
                if (min_gh < best.min_gh_hw) {
                    best.m14 = m14; best.m15 = m15;
                    best.min_gh_hw = min_gh;
                    best.hw56 = hw56;
                    printf("  HIT #%d: M14=0x%08x M15=0x%08x  hw56=%d  min_gh60=%d",
                           n_hits, m14, m15, hw56, min_gh);
                    if (min_gh < 10) printf(" <-- COLD!");
                    if (min_gh < 5) printf(" *** TARGET! ***");
                    printf("  [NEW BEST]\n"); fflush(stdout);
                } else if (n_hits <= 3) {
                    printf("  HIT #%d: M14=0x%08x M15=0x%08x  hw56=%d  min_gh60=%d\n",
                           n_hits, m14, m15, hw56, min_gh); fflush(stdout);
                }
            }
        }
    }

    time_t end = time(NULL);
    printf("\n==============================================\n");
    printf("RESULTS: %d da[56]=0 hits from %ld trials (%.0fs)\n",
           n_hits, n_trials, difftime(end, start));
    printf("  Best: M14=0x%08x M15=0x%08x  hw56=%d  min_gh60=%d/64\n",
           best.m14, best.m15, best.hw56, best.min_gh_hw);
    printf("  Baseline (all-ones): min_gh60 ~18/64\n");
    if (best.min_gh_hw < 18)
        printf("  IMPROVEMENT over baseline!\n");
    if (best.min_gh_hw < 5)
        printf("  [!!!] TARGET REACHED — feed to MITM SAT solver!\n");
    printf("==============================================\n");

    return 0;
}
