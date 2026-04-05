/*
 * Script 80: Parametric N-bit Mini-SHA-256 SA Collision Search
 *
 * Validates the SA approach at reduced word widths where SAT finds solutions.
 * If SA finds HW=0 at N=10-12, the approach works and the N=32 floor is real.
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *   -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *   -o mini_sa 80_mini_sa_search.c -lm
 *
 * Usage: ./mini_sa [N] [restarts] [steps] [fill]
 *   N = word width (8-32, default 10)
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#ifdef _OPENMP
#include <omp.h>
#endif

static int N_BITS;
static uint32_t WMASK;
static uint32_t MSB_BIT;

/* Scaled rotation: round(k * N / 32), minimum 1 */
static int scale_rot(int k32, int N) {
    int r = (int)(0.5 + (double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

/* N-bit rotation amounts (computed at startup) */
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;

static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N_BITS;
    return ((x >> k) | (x << (N_BITS - k))) & WMASK;
}
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e & f) ^ (~e & g) & WMASK; }
static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline uint32_t S0(uint32_t a) { return ror_n(a,rS0[0]) ^ ror_n(a,rS0[1]) ^ ror_n(a,rS0[2]); }
static inline uint32_t S1(uint32_t e) { return ror_n(e,rS1[0]) ^ ror_n(e,rS1[1]) ^ ror_n(e,rS1[2]); }
static inline uint32_t s0f(uint32_t x) { return ror_n(x,rs0[0]) ^ ror_n(x,rs0[1]) ^ ((x >> ss0) & WMASK); }
static inline uint32_t s1f(uint32_t x) { return ror_n(x,rs1[0]) ^ ror_n(x,rs1[1]) ^ ((x >> ss1) & WMASK); }
static inline int hw(uint32_t x) { return __builtin_popcount(x & WMASK); }

static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

static uint32_t KN[64], IVN[8];

typedef struct {
    uint32_t state[8];
    uint32_t W_pre[57];
} precomp_t;

static void precompute(const uint32_t M[16], precomp_t *out) {
    for (int i = 0; i < 16; i++) out->W_pre[i] = M[i] & WMASK;
    for (int i = 16; i < 57; i++)
        out->W_pre[i] = (s1f(out->W_pre[i-2]) + out->W_pre[i-7] + s0f(out->W_pre[i-15]) + out->W_pre[i-16]) & WMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + S1(e) + Ch(e,f,g) + KN[i] + out->W_pre[i]) & WMASK;
        uint32_t T2 = (S0(a) + Maj(a,b,c)) & WMASK;
        h=g;g=f;f=e;e=(d+T1)&WMASK;d=c;c=b;b=a;a=(T1+T2)&WMASK;
    }
    out->state[0]=a; out->state[1]=b; out->state[2]=c; out->state[3]=d;
    out->state[4]=e; out->state[5]=f; out->state[6]=g; out->state[7]=h;
}

static int eval_hw63(const precomp_t *p1, const precomp_t *p2,
                     const uint32_t w1[4], const uint32_t w2[4]) {
    uint32_t W1[7], W2[7];
    for (int i = 0; i < 4; i++) { W1[i] = w1[i] & WMASK; W2[i] = w2[i] & WMASK; }
    W1[4] = (s1f(W1[2]) + p1->W_pre[54] + s0f(p1->W_pre[46]) + p1->W_pre[45]) & WMASK;
    W2[4] = (s1f(W2[2]) + p2->W_pre[54] + s0f(p2->W_pre[46]) + p2->W_pre[45]) & WMASK;
    W1[5] = (s1f(W1[3]) + p1->W_pre[55] + s0f(p1->W_pre[47]) + p1->W_pre[46]) & WMASK;
    W2[5] = (s1f(W2[3]) + p2->W_pre[55] + s0f(p2->W_pre[47]) + p2->W_pre[46]) & WMASK;
    W1[6] = (s1f(W1[4]) + p1->W_pre[56] + s0f(p1->W_pre[48]) + p1->W_pre[47]) & WMASK;
    W2[6] = (s1f(W2[4]) + p2->W_pre[56] + s0f(p2->W_pre[48]) + p2->W_pre[47]) & WMASK;

    uint32_t a1=p1->state[0],b1=p1->state[1],c1=p1->state[2],d1=p1->state[3];
    uint32_t e1=p1->state[4],f1=p1->state[5],g1=p1->state[6],h1=p1->state[7];
    uint32_t a2=p2->state[0],b2=p2->state[1],c2=p2->state[2],d2=p2->state[3];
    uint32_t e2=p2->state[4],f2=p2->state[5],g2=p2->state[6],h2=p2->state[7];

    for (int i = 0; i < 7; i++) {
        uint32_t T1a = (h1 + S1(e1) + Ch(e1,f1,g1) + KN[57+i] + W1[i]) & WMASK;
        uint32_t T2a = (S0(a1) + Maj(a1,b1,c1)) & WMASK;
        h1=g1;g1=f1;f1=e1;e1=(d1+T1a)&WMASK;d1=c1;c1=b1;b1=a1;a1=(T1a+T2a)&WMASK;
        uint32_t T1b = (h2 + S1(e2) + Ch(e2,f2,g2) + KN[57+i] + W2[i]) & WMASK;
        uint32_t T2b = (S0(a2) + Maj(a2,b2,c2)) & WMASK;
        h2=g2;g2=f2;f2=e2;e2=(d2+T1b)&WMASK;d2=c2;c2=b2;b2=a2;a2=(T1b+T2b)&WMASK;
    }
    return hw(a1^a2)+hw(b1^b2)+hw(c1^c2)+hw(d1^d2)+hw(e1^e2)+hw(f1^f2)+hw(g1^g2)+hw(h1^h2);
}

/* xoshiro128** */
typedef struct { uint32_t s[4]; } rng_t;
static inline uint32_t rng_rotl(uint32_t x, int k) { return (x<<k)|(x>>(32-k)); }
static inline uint32_t rng_next(rng_t *r) {
    uint32_t result = rng_rotl(r->s[1]*5,7)*9;
    uint32_t t = r->s[1]<<9;
    r->s[2]^=r->s[0]; r->s[3]^=r->s[1]; r->s[1]^=r->s[2]; r->s[0]^=r->s[3];
    r->s[2]^=t; r->s[3]=rng_rotl(r->s[3],11);
    return result;
}
static void rng_seed(rng_t *r, uint64_t seed) {
    r->s[0]=(uint32_t)seed; r->s[1]=(uint32_t)(seed>>32);
    r->s[2]=r->s[0]^0x9e3779b9; r->s[3]=r->s[1]^0x6a09e667;
    for (int i=0;i<8;i++) rng_next(r);
}

/* Scan for da[56]=0 candidate at N bits */
static int find_candidate(uint32_t fill, uint32_t *out_m0) {
    uint32_t M1[16], M2[16];
    uint32_t max_m0 = WMASK; /* scan full N-bit range */

    for (uint32_t m0 = 0; m0 <= max_m0; m0++) {
        for (int i = 0; i < 16; i++) { M1[i] = fill & WMASK; M2[i] = fill & WMASK; }
        M1[0] = m0; M2[0] = m0 ^ MSB_BIT; M2[9] = (fill ^ MSB_BIT) & WMASK;

        precomp_t p1, p2;
        precompute(M1, &p1);
        precompute(M2, &p2);

        if (p1.state[0] == p2.state[0]) {
            *out_m0 = m0;
            return 1;
        }
    }
    return 0;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    N_BITS = argc > 1 ? atoi(argv[1]) : 10;
    int n_restarts = argc > 2 ? atoi(argv[2]) : 5000;
    int steps = argc > 3 ? atoi(argv[3]) : 200000;
    uint32_t fill_arg = argc > 4 ? (uint32_t)strtoul(argv[4], NULL, 0) : 0xFFFFFFFF;

    WMASK = (1U << N_BITS) - 1;
    MSB_BIT = 1U << (N_BITS - 1);

    /* Initialize scaled rotation amounts */
    rS0[0]=scale_rot(2,N_BITS); rS0[1]=scale_rot(13,N_BITS); rS0[2]=scale_rot(22,N_BITS);
    rS1[0]=scale_rot(6,N_BITS); rS1[1]=scale_rot(11,N_BITS); rS1[2]=scale_rot(25,N_BITS);
    rs0[0]=scale_rot(7,N_BITS); rs0[1]=scale_rot(18,N_BITS); ss0=scale_rot(3,N_BITS);
    rs1[0]=scale_rot(17,N_BITS); rs1[1]=scale_rot(19,N_BITS); ss1=scale_rot(10,N_BITS);

    /* Truncate constants */
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & WMASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & WMASK;

    uint32_t fill = fill_arg & WMASK;

    printf("Mini-SHA-256 SA Search (N=%d bits)\n", N_BITS);
    printf("  Word mask: 0x%x, MSB: 0x%x\n", WMASK, MSB_BIT);
    printf("  Rotations S0: %d,%d,%d  S1: %d,%d,%d\n", rS0[0],rS0[1],rS0[2], rS1[0],rS1[1],rS1[2]);
    printf("  Rotations s0: %d,%d,>>%d  s1: %d,%d,>>%d\n", rs0[0],rs0[1],ss0, rs1[0],rs1[1],ss1);
    printf("  Fill: 0x%x\n", fill);

    /* Find candidate */
    printf("\nScanning for da[56]=0 candidate...\n");
    uint32_t m0;
    if (!find_candidate(fill, &m0)) {
        /* Try other fills */
        uint32_t fills[] = {WMASK, 0, WMASK>>1, MSB_BIT, 0x55&WMASK, 0xAA&WMASK};
        int found = 0;
        for (int f = 0; f < 6 && !found; f++) {
            if (fills[f] == fill) continue;
            fill = fills[f];
            found = find_candidate(fill, &m0);
        }
        if (!found) {
            printf("No da[56]=0 candidate found at N=%d!\n", N_BITS);
            return 1;
        }
    }
    printf("Found: M[0]=0x%x, fill=0x%x\n", m0, fill);

    /* Precompute for both messages */
    uint32_t M1[16], M2[16];
    for (int i = 0; i < 16; i++) { M1[i] = fill; M2[i] = fill; }
    M1[0] = m0; M2[0] = m0 ^ MSB_BIT; M2[9] = (fill ^ MSB_BIT) & WMASK;

    precomp_t p1, p2;
    precompute(M1, &p1);
    precompute(M2, &p2);

    printf("State1[0] = 0x%x, State2[0] = 0x%x (should match)\n", p1.state[0], p2.state[0]);

    /* SA search */
    int global_best = 8 * N_BITS; /* max possible HW */
    uint32_t best_w1[4], best_w2[4];
    time_t t0 = time(NULL);

    #pragma omp parallel
    {
        int tid = 0;
        #ifdef _OPENMP
        tid = omp_get_thread_num();
        #endif
        rng_t rng;
        rng_seed(&rng, time(NULL) ^ ((uint64_t)tid << 32) ^ ((uint64_t)N_BITS << 48));

        #pragma omp for schedule(dynamic, 1)
        for (int restart = 0; restart < n_restarts; restart++) {
            uint32_t w1[4], w2[4];
            for (int i = 0; i < 4; i++) { w1[i] = rng_next(&rng) & WMASK; w2[i] = rng_next(&rng) & WMASK; }

            int cur_hw = eval_hw63(&p1, &p2, w1, w2);
            double T = 15.0;
            double cooling = pow(0.001 / 15.0, 1.0 / steps);

            for (int step = 0; step < steps; step++) {
                uint32_t tw1[4], tw2[4];
                memcpy(tw1, w1, sizeof(w1)); memcpy(tw2, w2, sizeof(w2));

                int nf = 1 + (rng_next(&rng) % 3);
                for (int f = 0; f < nf; f++) {
                    uint32_t r = rng_next(&rng);
                    int wi = r & 3;
                    int bit = (r >> 2) % N_BITS;
                    if ((r >> 7) & 1) tw1[wi] ^= (1U << bit);
                    else tw2[wi] ^= (1U << bit);
                }

                int new_hw = eval_hw63(&p1, &p2, tw1, tw2);
                int delta = new_hw - cur_hw;
                if (delta <= 0 || ((double)rng_next(&rng)/4294967296.0) < exp(-delta/T)) {
                    memcpy(w1, tw1, sizeof(w1)); memcpy(w2, tw2, sizeof(w2));
                    cur_hw = new_hw;
                }
                T *= cooling;
                if (cur_hw == 0) break;
            }

            #pragma omp critical
            {
                if (cur_hw < global_best) {
                    global_best = cur_hw;
                    memcpy(best_w1, w1, sizeof(w1)); memcpy(best_w2, w2, sizeof(w2));
                    time_t now = time(NULL);
                    printf("[%lds] Restart %d: NEW BEST HW=%d", (long)(now-t0), restart, global_best);
                    if (global_best == 0) printf("  *** COLLISION FOUND! ***");
                    printf("\n");
                }
                if (restart % 500 == 499) {
                    time_t now = time(NULL);
                    printf("[%lds] %d/%d done, best=%d\n", (long)(now-t0), restart+1, n_restarts, global_best);
                }
            }
            if (global_best == 0) continue; /* can't break OMP loop */
        }
    }

    time_t tend = time(NULL);
    printf("\n===== N=%d RESULT =====\n", N_BITS);
    printf("Best HW: %d (out of %d max)\n", global_best, 8*N_BITS);
    printf("Time: %lds\n", (long)(tend-t0));
    printf("W1 = {0x%x, 0x%x, 0x%x, 0x%x}\n", best_w1[0], best_w1[1], best_w1[2], best_w1[3]);
    printf("W2 = {0x%x, 0x%x, 0x%x, 0x%x}\n", best_w2[0], best_w2[1], best_w2[2], best_w2[3]);
    if (global_best == 0) printf("*** sr=60 COLLISION at N=%d! ***\n", N_BITS);
    return 0;
}
