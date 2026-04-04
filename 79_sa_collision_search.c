/*
 * Script 79: Simulated Annealing Collision Search for sr=60
 *
 * Fast SA over the 256-bit (W1[57..60], W2[57..60]) space.
 * Objective: minimize total state diff HW at round 63.
 * If HW=0 is found → sr=60 collision!
 *
 * Key insight from differential analysis:
 *   - sr=59 collision zeros one register per free round
 *   - sr=60 loses control of W[61], which breaks the zeroing pattern
 *   - We need W[57..60] values where the schedule-determined W[61..63]
 *     still produce zero state diff at round 63
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *   -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *   -o sa_search 79_sa_collision_search.c -lm
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

#define MASK 0xFFFFFFFFU

static inline uint32_t ror(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e & f) ^ (~e & g); }
static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline uint32_t S0(uint32_t a) { return ror(a,2) ^ ror(a,13) ^ ror(a,22); }
static inline uint32_t S1(uint32_t e) { return ror(e,6) ^ ror(e,11) ^ ror(e,25); }
static inline uint32_t s0(uint32_t x) { return ror(x,7) ^ ror(x,18) ^ (x>>3); }
static inline uint32_t s1(uint32_t x) { return ror(x,17) ^ ror(x,19) ^ (x>>10); }
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

typedef struct {
    uint32_t state[8];
    uint32_t W_pre[57];
} precomp_t;

static void precompute(const uint32_t M[16], precomp_t *out) {
    for (int i = 0; i < 16; i++) out->W_pre[i] = M[i];
    for (int i = 16; i < 57; i++)
        out->W_pre[i] = s1(out->W_pre[i-2]) + out->W_pre[i-7] + s0(out->W_pre[i-15]) + out->W_pre[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + S1(e) + Ch(e,f,g) + K[i] + out->W_pre[i];
        uint32_t T2 = S0(a) + Maj(a,b,c);
        h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;
    }
    out->state[0]=a; out->state[1]=b; out->state[2]=c; out->state[3]=d;
    out->state[4]=e; out->state[5]=f; out->state[6]=g; out->state[7]=h;
}

/* Evaluate round-63 state diff HW given free W[57..60] for both messages */
static int eval_hw63(const precomp_t *p1, const precomp_t *p2,
                     const uint32_t w1[4], const uint32_t w2[4]) {
    /* Build schedule tail: W[61], W[62], W[63] */
    uint32_t W1[7], W2[7];
    for (int i = 0; i < 4; i++) { W1[i] = w1[i]; W2[i] = w2[i]; }

    /* W[61] = s1(W[59]) + W_pre[54] + s0(W_pre[46]) + W_pre[45] */
    W1[4] = s1(W1[2]) + p1->W_pre[54] + s0(p1->W_pre[46]) + p1->W_pre[45];
    W2[4] = s1(W2[2]) + p2->W_pre[54] + s0(p2->W_pre[46]) + p2->W_pre[45];
    /* W[62] = s1(W[60]) + W_pre[55] + s0(W_pre[47]) + W_pre[46] */
    W1[5] = s1(W1[3]) + p1->W_pre[55] + s0(p1->W_pre[47]) + p1->W_pre[46];
    W2[5] = s1(W2[3]) + p2->W_pre[55] + s0(p2->W_pre[47]) + p2->W_pre[46];
    /* W[63] = s1(W[61]) + W_pre[56] + s0(W_pre[48]) + W_pre[47] */
    W1[6] = s1(W1[4]) + p1->W_pre[56] + s0(p1->W_pre[48]) + p1->W_pre[47];
    W2[6] = s1(W2[4]) + p2->W_pre[56] + s0(p2->W_pre[48]) + p2->W_pre[47];

    /* Run 7 rounds (57-63) for both messages */
    uint32_t a1=p1->state[0],b1=p1->state[1],c1=p1->state[2],d1=p1->state[3];
    uint32_t e1=p1->state[4],f1=p1->state[5],g1=p1->state[6],h1=p1->state[7];
    uint32_t a2=p2->state[0],b2=p2->state[1],c2=p2->state[2],d2=p2->state[3];
    uint32_t e2=p2->state[4],f2=p2->state[5],g2=p2->state[6],h2=p2->state[7];

    for (int i = 0; i < 7; i++) {
        uint32_t T1a = h1 + S1(e1) + Ch(e1,f1,g1) + K[57+i] + W1[i];
        uint32_t T2a = S0(a1) + Maj(a1,b1,c1);
        h1=g1;g1=f1;f1=e1;e1=d1+T1a;d1=c1;c1=b1;b1=a1;a1=T1a+T2a;

        uint32_t T1b = h2 + S1(e2) + Ch(e2,f2,g2) + K[57+i] + W2[i];
        uint32_t T2b = S0(a2) + Maj(a2,b2,c2);
        h2=g2;g2=f2;f2=e2;e2=d2+T1b;d2=c2;c2=b2;b2=a2;a2=T1b+T2b;
    }

    return hw32(a1^a2) + hw32(b1^b2) + hw32(c1^c2) + hw32(d1^d2) +
           hw32(e1^e2) + hw32(f1^f2) + hw32(g1^g2) + hw32(h1^h2);
}

/* xoshiro128** PRNG (fast, good quality) */
typedef struct { uint32_t s[4]; } rng_t;

static inline uint32_t rng_rotl(uint32_t x, int k) { return (x << k) | (x >> (32 - k)); }

static inline uint32_t rng_next(rng_t *r) {
    uint32_t result = rng_rotl(r->s[1] * 5, 7) * 9;
    uint32_t t = r->s[1] << 9;
    r->s[2] ^= r->s[0]; r->s[3] ^= r->s[1];
    r->s[1] ^= r->s[2]; r->s[0] ^= r->s[3];
    r->s[2] ^= t; r->s[3] = rng_rotl(r->s[3], 11);
    return result;
}

static void rng_seed(rng_t *r, uint64_t seed) {
    r->s[0] = (uint32_t)(seed); r->s[1] = (uint32_t)(seed >> 32);
    r->s[2] = r->s[0] ^ 0x9e3779b9; r->s[3] = r->s[1] ^ 0x6a09e667;
    for (int i = 0; i < 8; i++) rng_next(r);
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    uint32_t m0 = 0x17149975;
    uint32_t fill = 0xffffffff;
    int n_restarts = 1000;
    int steps_per_restart = 100000;
    double T_start = 30.0;
    double T_end = 0.01;

    if (argc > 1) n_restarts = atoi(argv[1]);
    if (argc > 2) steps_per_restart = atoi(argv[2]);
    if (argc > 3) m0 = (uint32_t)strtoul(argv[3], NULL, 0);
    if (argc > 4) fill = (uint32_t)strtoul(argv[4], NULL, 0);

    printf("SA Collision Search for sr=60\n");
    printf("  M[0] = 0x%08x, fill = 0x%08x\n", m0, fill);
    printf("  Restarts: %d, Steps/restart: %d\n", n_restarts, steps_per_restart);
    printf("  Temperature: %.1f -> %.3f\n\n", T_start, T_end);

    /* Precompute states */
    uint32_t M1[16], M2[16];
    M1[0] = m0; M1[1] = fill;
    for (int i = 2; i < 16; i++) M1[i] = fill;
    memcpy(M2, M1, sizeof(M1));
    M2[0] ^= 0x80000000;
    M2[9] ^= 0x80000000;

    precomp_t p1, p2;
    precompute(M1, &p1);
    precompute(M2, &p2);

    if (p1.state[0] != p2.state[0]) {
        printf("ERROR: da[56] != 0 for M[0]=0x%08x with fill=0x%08x\n", m0, fill);
        return 1;
    }

    int global_best = 256;
    uint32_t best_w1[4], best_w2[4];
    time_t t0 = time(NULL);

    #pragma omp parallel
    {
        int tid = 0;
        #ifdef _OPENMP
        tid = omp_get_thread_num();
        #endif
        rng_t rng;
        rng_seed(&rng, time(NULL) ^ ((uint64_t)tid << 32));

        int local_best = 256;
        uint32_t local_best_w1[4], local_best_w2[4];

        #pragma omp for schedule(dynamic, 1)
        for (int restart = 0; restart < n_restarts; restart++) {
            /* Random starting point */
            uint32_t w1[4], w2[4];
            for (int i = 0; i < 4; i++) { w1[i] = rng_next(&rng); w2[i] = rng_next(&rng); }

            int cur_hw = eval_hw63(&p1, &p2, w1, w2);
            int restart_best = cur_hw;

            double cooling = pow(T_end / T_start, 1.0 / steps_per_restart);

            double T = T_start;
            for (int step = 0; step < steps_per_restart; step++) {
                /* Perturbation: flip 1-3 random bits */
                uint32_t trial_w1[4], trial_w2[4];
                memcpy(trial_w1, w1, sizeof(w1));
                memcpy(trial_w2, w2, sizeof(w2));

                int n_flips = 1 + (rng_next(&rng) % 3);
                for (int f = 0; f < n_flips; f++) {
                    uint32_t r = rng_next(&rng);
                    int word_idx = r & 3;
                    int bit = (r >> 2) & 31;
                    if ((r >> 7) & 1) {
                        trial_w1[word_idx] ^= (1U << bit);
                    } else {
                        trial_w2[word_idx] ^= (1U << bit);
                    }
                }

                int new_hw = eval_hw63(&p1, &p2, trial_w1, trial_w2);
                int delta = new_hw - cur_hw;

                /* Accept if improving or with SA probability */
                if (delta <= 0 || (T > 0.001 && ((double)rng_next(&rng) / 4294967296.0) < exp(-delta / T))) {
                    memcpy(w1, trial_w1, sizeof(w1));
                    memcpy(w2, trial_w2, sizeof(w2));
                    cur_hw = new_hw;
                    if (cur_hw < restart_best) restart_best = cur_hw;
                }

                T *= cooling;

                if (cur_hw == 0) break;
            }

            if (restart_best < local_best) {
                local_best = restart_best;
                memcpy(local_best_w1, w1, sizeof(w1));
                memcpy(local_best_w2, w2, sizeof(w2));
            }

            #pragma omp critical
            {
                if (restart_best < global_best) {
                    global_best = restart_best;
                    memcpy(best_w1, w1, sizeof(w1));
                    memcpy(best_w2, w2, sizeof(w2));
                    time_t now = time(NULL);
                    printf("[%lds] Restart %d: NEW BEST HW=%d\n", (long)(now-t0), restart, global_best);
                    printf("  W1 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n", w1[0], w1[1], w1[2], w1[3]);
                    printf("  W2 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n", w2[0], w2[1], w2[2], w2[3]);
                    if (global_best == 0) {
                        printf("\n*** sr=60 COLLISION FOUND! ***\n");
                    }
                }
                if (restart % 100 == 99) {
                    time_t now = time(NULL);
                    printf("[%lds] %d/%d restarts done, global best=%d\n",
                           (long)(now-t0), restart+1, n_restarts, global_best);
                }
            }
        }
    }

    time_t tend = time(NULL);
    printf("\n==========================\n");
    printf("FINAL: best HW=%d in %lds\n", global_best, (long)(tend-t0));
    printf("  W1 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n", best_w1[0], best_w1[1], best_w1[2], best_w1[3]);
    printf("  W2 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n", best_w2[0], best_w2[1], best_w2[2], best_w2[3]);
    if (global_best == 0) printf("*** COLLISION! ***\n");
    return 0;
}
