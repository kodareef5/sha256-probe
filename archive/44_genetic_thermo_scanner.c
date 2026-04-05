/*
 * Script 44: Thermodynamic Genetic Algorithm Scanner
 *
 * Evolves M[1..15] padding to find "cold" candidates where the
 * Round 60 state difference HW is minimized under random free words.
 *
 * Fitness = -(min Hamming weight at Round 60 over N Monte Carlo shots)
 * Lower min_hw60 = better fitness = closer to sr=60 collision
 *
 * The paper used M[1..15] = 0xFFFFFFFF (lazy). We evolve the padding
 * to find thermodynamically favorable initial conditions.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o genetic_scanner 44_genetic_thermo_scanner.c -lm
 * Run:     ./genetic_scanner [pop_size] [generations] [mc_shots]
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
#define POP_SIZE 64
#define N_ELITE 8
#define N_CHILDREN 56

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

static inline uint32_t xorshift32(uint32_t *s) {
    uint32_t x = *s; x ^= x<<13; x ^= x>>17; x ^= x<<5; *s = x; return x;
}

typedef struct {
    uint32_t padding[15];  /* M[1..15] */
    uint32_t m0;           /* Best M[0] found for this padding */
    int hw56;              /* State diff HW at round 56 */
    int min_hw60;          /* Best (lowest) HW at round 60 over MC shots */
    int mean_hw60;
    int found;             /* Whether da[56]=0 was found */
} individual_t;

/* Compress N rounds */
static void compress_n(const uint32_t M[16], int n, uint32_t st[8]) {
    uint32_t W[64];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < n && i < 64; i++)
        W[i] = sigma1f(W[i-2]) + W[i-7] + sigma0f(W[i-15]) + W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < n; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=d+T1; d=c; c=b; b=a; a=T1+T2;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/* Evaluate fitness: scan M[0] for da[56]=0, then MC for min_hw60 */
static void evaluate(individual_t *ind, int mc_shots, uint32_t *rng) {
    uint32_t M1[16], M2[16], s1[8], s2[8];

    /* Set up message with this individual's padding */
    for (int i = 1; i < 16; i++) M1[i] = ind->padding[i-1];
    memcpy(M2, M1, sizeof(M1));

    ind->found = 0;
    ind->min_hw60 = 256;
    ind->mean_hw60 = 128;

    /* Scan a subset of M[0] (not full 2^32 — too slow for genetic algo) */
    /* Use 2^24 random M[0] values instead */
    for (int trial = 0; trial < (1 << 24); trial++) {
        uint32_t m0 = xorshift32(rng);
        M1[0] = m0;
        M2[0] = m0 ^ 0x80000000;
        M2[9] = M1[9] ^ 0x80000000;

        compress_n(M1, 57, s1);
        compress_n(M2, 57, s2);

        if (s1[0] != s2[0]) continue; /* da[56] != 0 */

        /* Found a hit! */
        ind->found = 1;
        ind->m0 = m0;

        int hw56 = 0;
        for (int r = 0; r < 8; r++) hw56 += hw32(s1[r] ^ s2[r]);
        ind->hw56 = hw56;

        /* Monte Carlo evaluation */
        int min_hw = 256;
        long sum_hw = 0;

        for (int mc = 0; mc < mc_shots; mc++) {
            uint32_t w[8]; /* W1[57..60], W2[57..60] */
            for (int i = 0; i < 8; i++) w[i] = xorshift32(rng);

            /* Run 4 rounds for both messages */
            uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
            for (int i = 0; i < 4; i++) {
                uint32_t T1 = h1+Sigma1(e1)+Ch(e1,f1,g1)+K[57+i]+w[i];
                uint32_t T2 = Sigma0(a1)+Maj(a1,b1,c1);
                h1=g1;g1=f1;f1=e1;e1=d1+T1;d1=c1;c1=b1;b1=a1;a1=T1+T2;
            }
            uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
            for (int i = 0; i < 4; i++) {
                uint32_t T1 = h2+Sigma1(e2)+Ch(e2,f2,g2)+K[57+i]+w[4+i];
                uint32_t T2 = Sigma0(a2)+Maj(a2,b2,c2);
                h2=g2;g2=f2;f2=e2;e2=d2+T1;d2=c2;c2=b2;b2=a2;a2=T1+T2;
            }

            int hw = hw32(a1^a2)+hw32(b1^b2)+hw32(c1^c2)+hw32(d1^d2)+
                     hw32(e1^e2)+hw32(f1^f2)+hw32(g1^g2)+hw32(h1^h2);
            if (hw < min_hw) min_hw = hw;
            sum_hw += hw;
        }

        ind->min_hw60 = min_hw;
        ind->mean_hw60 = (int)(sum_hw / mc_shots);
        break; /* Use first hit */
    }
}

/* Crossover: uniform crossover of padding words */
static void crossover(const individual_t *p1, const individual_t *p2,
                      individual_t *child, uint32_t *rng) {
    for (int i = 0; i < 15; i++) {
        if (xorshift32(rng) & 1)
            child->padding[i] = p1->padding[i];
        else
            child->padding[i] = p2->padding[i];
    }
}

/* Mutation: flip random bits */
static void mutate(individual_t *ind, int n_mutations, uint32_t *rng) {
    for (int m = 0; m < n_mutations; m++) {
        int word = xorshift32(rng) % 15;
        int bit = xorshift32(rng) % 32;
        ind->padding[word] ^= (1U << bit);
    }
}

/* Sort population by fitness (lower min_hw60 = better) */
static int cmp_fitness(const void *a, const void *b) {
    const individual_t *ia = (const individual_t *)a;
    const individual_t *ib = (const individual_t *)b;
    /* Unfound individuals go to the end */
    if (!ia->found && !ib->found) return 0;
    if (!ia->found) return 1;
    if (!ib->found) return -1;
    return ia->min_hw60 - ib->min_hw60;
}

int main(int argc, char *argv[]) {
    int pop_size = argc > 1 ? atoi(argv[1]) : POP_SIZE;
    int n_gen = argc > 2 ? atoi(argv[2]) : 200;
    int mc_shots = argc > 3 ? atoi(argv[3]) : 500;

    printf("==============================================\n");
    printf("GENETIC THERMODYNAMIC SCANNER\n");
    printf("  Population: %d, Generations: %d, MC shots: %d\n", pop_size, n_gen, mc_shots);
    printf("  Evolving M[1..15] to minimize Round 60 HW\n");
    printf("==============================================\n\n");
    fflush(stdout);

    individual_t *pop = calloc(pop_size, sizeof(individual_t));

    /* Initialize population */
    uint32_t master_rng = (uint32_t)time(NULL);
    for (int i = 0; i < pop_size; i++) {
        for (int w = 0; w < 15; w++)
            pop[i].padding[w] = xorshift32(&master_rng);
        /* Include the paper's all-ones padding as individual 0 */
        if (i == 0) {
            for (int w = 0; w < 15; w++)
                pop[i].padding[w] = 0xFFFFFFFF;
        }
        /* Include all-zeros as individual 1 */
        if (i == 1) {
            for (int w = 0; w < 15; w++)
                pop[i].padding[w] = 0x00000000;
        }
    }

    time_t start = time(NULL);

    for (int gen = 0; gen < n_gen; gen++) {
        /* Evaluate population in parallel */
        #pragma omp parallel for schedule(dynamic, 1)
        for (int i = 0; i < pop_size; i++) {
            uint32_t rng = (uint32_t)(time(NULL) ^ (gen * 1000 + i) * 7919);
            evaluate(&pop[i], mc_shots, &rng);
        }

        /* Sort by fitness */
        qsort(pop, pop_size, sizeof(individual_t), cmp_fitness);

        /* Report */
        time_t now = time(NULL);
        double elapsed = difftime(now, start);
        int n_found = 0;
        for (int i = 0; i < pop_size; i++) if (pop[i].found) n_found++;

        printf("Gen %3d: best_hw60=%3d mean_hw60=%3d hw56=%3d m0=0x%08x found=%d/%d (%.0fs)\n",
               gen, pop[n_found > 0 ? 0 : 0].min_hw60,
               pop[n_found > 0 ? 0 : 0].mean_hw60,
               pop[n_found > 0 ? 0 : 0].hw56,
               pop[n_found > 0 ? 0 : 0].m0,
               n_found, pop_size, elapsed);
        fflush(stdout);

        if (n_found > 0 && pop[0].min_hw60 < 30) {
            printf("\n[!!!] VERY COLD CANDIDATE FOUND!\n");
            printf("  M[0] = 0x%08x, min_hw60 = %d\n", pop[0].m0, pop[0].min_hw60);
            printf("  Padding M[1..15]:\n  ");
            for (int w = 0; w < 15; w++) printf("0x%08x ", pop[0].padding[w]);
            printf("\n");
            fflush(stdout);
        }

        /* Breed next generation */
        /* Keep top N_ELITE, breed N_CHILDREN from them */
        int n_elite = pop_size < N_ELITE ? pop_size / 2 : N_ELITE;
        for (int i = n_elite; i < pop_size; i++) {
            int p1 = xorshift32(&master_rng) % n_elite;
            int p2 = xorshift32(&master_rng) % n_elite;
            crossover(&pop[p1], &pop[p2], &pop[i], &master_rng);

            /* Mutation rate: 1-3 bit flips */
            int n_mut = 1 + (xorshift32(&master_rng) % 3);
            mutate(&pop[i], n_mut, &master_rng);
        }
    }

    /* Final report */
    printf("\n==============================================\n");
    printf("FINAL RESULTS (top 10)\n");
    printf("==============================================\n");
    printf("%-12s %5s %8s %8s\n", "M[0]", "hw56", "min60", "mean60");
    for (int i = 0; i < 10 && i < pop_size && pop[i].found; i++) {
        printf("0x%08x  %4d   %4d     %4d\n",
               pop[i].m0, pop[i].hw56, pop[i].min_hw60, pop[i].mean_hw60);
    }

    if (pop[0].found && pop[0].min_hw60 < 50) {
        printf("\nBest padding M[1..15]:\n");
        for (int w = 0; w < 15; w++)
            printf("  M[%2d] = 0x%08x\n", w+1, pop[0].padding[w]);
        printf("\nFeed to: python3 43_candidate_validator.py %08x\n", pop[0].m0);
    }

    free(pop);
    return 0;
}
