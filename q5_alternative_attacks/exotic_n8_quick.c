/*
 * exotic_n8_quick.c — Test top exotic kernels from N=4 at N=8
 *
 * Tests only the most promising configurations from the N=4 sweep:
 * - Standard (0,9) bit-6 (1644 collisions, the champion)
 * - (0,1) word pair (131 at N=4 — 2nd best!)
 * - (0,14) word pair (100 at N=4)
 * - (1,4,9) triple (128 at N=4)
 * - (0,5,9) triple (94 at N=4)
 * - Single-word dM[0] only (50 at N=4)
 *
 * Uses NEON+OpenMP for speed.
 *
 * Compile:
 *   gcc -O3 -march=native -Xclang -fopenmp \
 *       -I/opt/homebrew/opt/libomp/include \
 *       -L/opt/homebrew/opt/libomp/lib -lomp \
 *       -o exotic_n8_quick exotic_n8_quick.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <arm_neon.h>

#define MAX_N 16
static int gN;
static uint32_t gMASK;
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static uint32_t KN[64], IVN[8];

static inline uint32_t ror_n(uint32_t x, int k) { k %= gN; return ((x >> k) | (x << (gN - k))) & gMASK; }
static inline uint32_t fnS0(uint32_t a) { return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & gMASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & gMASK); }
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e & f) ^ ((~e) & g)) & gMASK; }
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & gMASK; }
static const uint32_t K32[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static int scale_rot(int k32) { int r = (int)rint((double)k32 * gN / 32.0); return r < 1 ? 1 : r; }

static uint32_t g_W1pre[57], g_W2pre[57], g_state1[8], g_state2[8];

static void precompute(const uint32_t M[16], uint32_t state[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & gMASK;
    for (int i = 16; i < 57; i++) W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i]) & gMASK;
        uint32_t T2 = (fnS0(a)+fnMj(a,b,c)) & gMASK;
        h=g; g=f; f=e; e=(d+T1)&gMASK; d=c; c=b; b=a; a=(T1+T2)&gMASK;
    }
    state[0]=a; state[1]=b; state[2]=c; state[3]=d;
    state[4]=e; state[5]=f; state[6]=g; state[7]=h;
}

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w) & gMASK;
    uint32_t T2 = (fnS0(s[0])+fnMj(s[0],s[1],s[2])) & gMASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&gMASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&gMASK;
}

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd]) & gMASK;
    uint32_t r2 = (s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd]) & gMASK;
    uint32_t T21 = (fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2])) & gMASK;
    uint32_t T22 = (fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2])) & gMASK;
    return (w1 + r1 - r2 + T21 - T22) & gMASK;
}

/* NEON engine */
static int16x8_t rot_neg[16], rot_pos[16];
static uint16x8_t mask_vec;
static void init_neon(void) {
    mask_vec = vdupq_n_u16((uint16_t)gMASK);
    for (int k = 0; k < 16; k++) {
        int kk = k % gN;
        rot_neg[k] = vdupq_n_s16((int16_t)(-kk));
        rot_pos[k] = vdupq_n_s16((int16_t)(gN - kk));
    }
}
static inline uint16x8_t neon_ror(uint16x8_t x, int k) { return vandq_u16(vorrq_u16(vshlq_u16(x, rot_neg[k]), vshlq_u16(x, rot_pos[k])), mask_vec); }
static inline uint16x8_t neon_S0(uint16x8_t a) { return veorq_u16(veorq_u16(neon_ror(a, rS0[0]), neon_ror(a, rS0[1])), neon_ror(a, rS0[2])); }
static inline uint16x8_t neon_S1(uint16x8_t e) { return veorq_u16(veorq_u16(neon_ror(e, rS1[0]), neon_ror(e, rS1[1])), neon_ror(e, rS1[2])); }
static inline uint16x8_t neon_s1(uint16x8_t x) { int16x8_t ns = vdupq_n_s16((int16_t)(-ss1)); return veorq_u16(veorq_u16(neon_ror(x, rs1[0]), neon_ror(x, rs1[1])), vandq_u16(vshlq_u16(x, ns), mask_vec)); }
static inline uint16x8_t neon_Ch(uint16x8_t e, uint16x8_t f, uint16x8_t g) { return veorq_u16(vandq_u16(e, f), vbicq_u16(g, e)); }
static inline uint16x8_t neon_Mj(uint16x8_t a, uint16x8_t b, uint16x8_t c) { return veorq_u16(veorq_u16(vandq_u16(a, b), vandq_u16(a, c)), vandq_u16(b, c)); }
static inline void neon_round(uint16x8_t s[8], uint16x8_t k, uint16x8_t w) {
    uint16x8_t T1 = vandq_u16(vaddq_u16(vaddq_u16(vaddq_u16(s[7], neon_S1(s[4])), neon_Ch(s[4], s[5], s[6])), vaddq_u16(k, w)), mask_vec);
    uint16x8_t T2 = vandq_u16(vaddq_u16(neon_S0(s[0]), neon_Mj(s[0], s[1], s[2])), mask_vec);
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=vandq_u16(vaddq_u16(s[3],T1),mask_vec);
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=vandq_u16(vaddq_u16(T1,T2),mask_vec);
}

/* Count collisions with NEON+OpenMP */
static int neon_count(int nthreads) {
    uint64_t n = 0;
    #pragma omp parallel num_threads(nthreads) reduction(+:n)
    {
        #pragma omp for schedule(dynamic, 1)
        for (uint32_t w57 = 0; w57 < (1U << gN); w57++) {
            uint32_t s57a[8], s57b[8];
            memcpy(s57a, g_state1, 32); memcpy(s57b, g_state2, 32);
            uint32_t w57b = find_w2(s57a, s57b, 57, w57);
            sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);
            for (uint32_t w58 = 0; w58 < (1U << gN); w58++) {
                uint32_t s58a[8], s58b[8];
                memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
                uint32_t w58b = find_w2(s58a, s58b, 58, w58);
                sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);
                for (uint32_t w59 = 0; w59 < (1U << gN); w59++) {
                    uint32_t s59a[8], s59b[8];
                    memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                    uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                    sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);
                    uint32_t co60 = find_w2(s59a, s59b, 60, 0);
                    uint32_t W1_61 = (fns1(w59) + g_W1pre[54] + fns0(g_W1pre[46]) + g_W1pre[45]) & gMASK;
                    uint32_t W2_61 = (fns1(w59b) + g_W2pre[54] + fns0(g_W2pre[46]) + g_W2pre[45]) & gMASK;
                    uint32_t W1_63 = (fns1(W1_61) + g_W1pre[56] + fns0(g_W1pre[48]) + g_W1pre[47]) & gMASK;
                    uint32_t W2_63 = (fns1(W2_61) + g_W2pre[56] + fns0(g_W2pre[48]) + g_W2pre[47]) & gMASK;
                    uint16x8_t k60=vdupq_n_u16(KN[60]),k61=vdupq_n_u16(KN[61]),k62=vdupq_n_u16(KN[62]),k63=vdupq_n_u16(KN[63]);
                    uint16x8_t w61a=vdupq_n_u16(W1_61),w61b=vdupq_n_u16(W2_61),w63a=vdupq_n_u16(W1_63),w63b=vdupq_n_u16(W2_63);
                    uint16x8_t cov=vdupq_n_u16(co60);
                    uint16x8_t b1[8],b2[8];
                    for (int r=0;r<8;r++){b1[r]=vdupq_n_u16(s59a[r]);b2[r]=vdupq_n_u16(s59b[r]);}
                    uint32_t sc1=(g_W1pre[55]+fns0(g_W1pre[47])+g_W1pre[46])&gMASK;
                    uint32_t sc2=(g_W2pre[55]+fns0(g_W2pre[47])+g_W2pre[46])&gMASK;
                    uint16x8_t sv1=vdupq_n_u16(sc1),sv2=vdupq_n_u16(sc2);
                    for (uint32_t w60b=0;w60b<(1U<<gN);w60b+=8) {
                        uint16_t v[8]; for(int i=0;i<8;i++)v[i]=(w60b+i)&gMASK;
                        uint16x8_t wv=vld1q_u16(v);
                        uint16x8_t wv2=vandq_u16(vaddq_u16(wv,cov),mask_vec);
                        uint16x8_t s1[8],s2[8];
                        for(int r=0;r<8;r++){s1[r]=b1[r];s2[r]=b2[r];}
                        neon_round(s1,k60,wv); neon_round(s2,k60,wv2);
                        uint16x8_t w62a=vandq_u16(vaddq_u16(neon_s1(wv),sv1),mask_vec);
                        uint16x8_t w62b=vandq_u16(vaddq_u16(neon_s1(wv2),sv2),mask_vec);
                        neon_round(s1,k61,w61a); neon_round(s2,k61,w61b);
                        neon_round(s1,k62,w62a); neon_round(s2,k62,w62b);
                        neon_round(s1,k63,w63a); neon_round(s2,k63,w63b);
                        uint16x8_t m=vceqq_u16(s1[0],s2[0]);
                        if(!vmaxvq_u16(m))continue;
                        for(int r=1;r<8;r++){m=vandq_u16(m,vceqq_u16(s1[r],s2[r]));if(!vmaxvq_u16(m))break;}
                        if(vmaxvq_u16(m)){uint16_t mm[8];vst1q_u16(mm,m);for(int i=0;i<8;i++)if(mm[i])n++;}
                    }
                }
            }
        }
    }
    return (int)n;
}

typedef struct {
    int n_words;
    int word_indices[4];
    uint32_t deltas[4];
    char desc[80];
} kernel_config_t;

static int test_kernel(const kernel_config_t *kc, int nthreads) {
    uint32_t fills[] = {gMASK, 0, gMASK>>1};
    int best = 0;
    for (int fi = 0; fi < 3; fi++) {
        for (uint32_t m0 = 0; m0 <= gMASK; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fills[fi]; M2[i] = fills[fi]; }
            M1[0] = m0; M2[0] = m0;
            for (int w = 0; w < kc->n_words; w++)
                M2[kc->word_indices[w]] ^= kc->deltas[w];
            precompute(M1, g_state1, g_W1pre);
            precompute(M2, g_state2, g_W2pre);
            if (g_state1[0] != g_state2[0]) continue;
            int nc = neon_count(nthreads);
            if (nc > best) best = nc;
            if (nc > 0) break; /* first candidate per fill */
        }
    }
    return best;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    gN = 8;
    int nthreads = argc > 1 ? atoi(argv[1]) : 2;
    gMASK = (1U << gN) - 1;
    rS0[0]=scale_rot(2); rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6); rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7); rs0[1]=scale_rot(18); ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19); ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & gMASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & gMASK;
    init_neon();

    printf("Exotic kernel test at N=8 (%d threads)\n", nthreads);
    printf("Testing top configurations from N=4 sweep\n\n");

    kernel_config_t tests[] = {
        /* Standard champion for comparison */
        {2, {0,9}, {1U<<6, 1U<<6}, "Standard: dM[0]=dM[9]=2^6 (champion)"},
        {2, {0,9}, {1U<<7, 1U<<7}, "Standard: dM[0]=dM[9]=2^7 (MSB)"},
        /* Non-(0,9) pairs — the big discovery */
        {2, {0,1}, {1U<<6, 1U<<6}, "NEW: dM[0]=dM[1]=2^6"},
        {2, {0,1}, {1U<<2, 1U<<2}, "NEW: dM[0]=dM[1]=2^2 (best at N=4)"},
        {2, {0,14}, {1U<<6, 1U<<6}, "NEW: dM[0]=dM[14]=2^6"},
        {2, {0,14}, {1U<<1, 1U<<1}, "NEW: dM[0]=dM[14]=2^1"},
        {2, {5,9}, {1U<<6, 1U<<6}, "NEW: dM[5]=dM[9]=2^6"},
        {2, {5,9}, {1U<<1, 1U<<1}, "NEW: dM[5]=dM[9]=2^1"},
        /* Three-word */
        {3, {1,4,9}, {1U<<6, 1U<<6, 1U<<6}, "3-word: dM[1]=dM[4]=dM[9]=2^6"},
        {3, {1,4,9}, {1U<<1, 1U<<1, 1U<<1}, "3-word: dM[1]=dM[4]=dM[9]=2^1"},
        {3, {0,5,9}, {1U<<6, 1U<<6, 1U<<6}, "3-word: dM[0]=dM[5]=dM[9]=2^6"},
        /* Single-word */
        {1, {0}, {1U<<6}, "1-word: dM[0]=2^6 only"},
        {1, {0}, {1U<<1}, "1-word: dM[0]=2^1 only"},
    };
    int ntests = sizeof(tests) / sizeof(tests[0]);

    int best = 0;
    for (int t = 0; t < ntests; t++) {
        struct timespec t0, t1;
        clock_gettime(CLOCK_MONOTONIC, &t0);
        int nc = test_kernel(&tests[t], nthreads);
        clock_gettime(CLOCK_MONOTONIC, &t1);
        double el = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
        char tag[8] = "";
        if (nc > best) { best = nc; strcpy(tag, " <<<"); }
        printf("  %-45s  %5d  (%.1fs)%s\n", tests[t].desc, nc, el, tag);
    }

    printf("\nBest: %d collisions\n", best);
    return 0;
}
