/*
 * carry_polynomial.c — Express SHA-256 cascade collision as Boolean polynomial system
 *
 * At N=4, the collision problem has 16 Boolean variables (bit k of W1[57..60],
 * k=0..3). The collision condition gives 32 equations (4 bits x 8 registers).
 * Carry propagation introduces quadratic terms (degree 2).
 *
 * This tool:
 * 1. Enumerates all 2^16 = 65536 variable assignments
 * 2. For each, evaluates the collision condition
 * 3. Identifies which equations are linear, which are quadratic/higher
 * 4. Builds the Algebraic Normal Form (ANF) of each equation
 * 5. Applies the a-path carry invariance to eliminate variables
 * 6. Measures the residual nonlinear system complexity
 *
 * The goal is to prove that the collision system can be solved faster than
 * brute force by exploiting the polynomial structure.
 *
 * Compile: gcc -O3 -march=native -o carry_polynomial carry_polynomial.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define N 4
#define MASK ((1U << N) - 1)
#define NVARS (4 * N)  /* 16 free Boolean variables */
#define SPACE (1U << NVARS)  /* 65536 assignments */

static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static int SR(int k) { int r = (int)rint((double)k * N / 32.0); return r < 1 ? 1 : r; }
static uint32_t KN[64], IVN[8];
static inline uint32_t ror_n(uint32_t x, int k) { k %= N; return ((x >> k) | (x << (N - k))) & MASK; }
static inline uint32_t fnS0(uint32_t a) { return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & MASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & MASK); }
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e & f) ^ ((~e) & g)) & MASK; }
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & MASK; }
static const uint32_t K32[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static uint32_t state1[8], state2[8], W1pre[57], W2pre[57];

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],
             e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i]) & MASK;
        uint32_t T2 = (fnS0(a)+fnMj(a,b,c)) & MASK;
        h=g; g=f; f=e; e=(d+T1)&MASK; d=c; c=b; b=a; a=(T1+T2)&MASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w) & MASK;
    uint32_t T2 = (fnS0(s[0])+fnMj(s[0],s[1],s[2])) & MASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
}

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd]) & MASK;
    uint32_t r2 = (s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd]) & MASK;
    uint32_t T21 = (fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T22 = (fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + r1 - r2 + T21 - T22) & MASK;
}

/*
 * Evaluate collision for a given assignment of the 16 free variables.
 * Variables: x[0..3] = bits 0..3 of W1[57]
 *            x[4..7] = bits 0..3 of W1[58]
 *            x[8..11] = bits 0..3 of W1[59]
 *            x[12..15] = bits 0..3 of W1[60]
 *
 * Returns a 32-bit mask: bit (r*4+k) = 1 iff register r differs at bit k.
 * A collision has mask = 0.
 */
static uint32_t eval_collision(uint32_t assignment) {
    uint32_t w57 = assignment & MASK;
    uint32_t w58 = (assignment >> N) & MASK;
    uint32_t w59 = (assignment >> (2*N)) & MASK;
    uint32_t w60 = (assignment >> (3*N)) & MASK;

    uint32_t s1[8], s2[8];
    memcpy(s1, state1, 32); memcpy(s2, state2, 32);

    uint32_t w57b = find_w2(s1, s2, 57, w57);
    sha_round(s1, KN[57], w57); sha_round(s2, KN[57], w57b);
    uint32_t w58b = find_w2(s1, s2, 58, w58);
    sha_round(s1, KN[58], w58); sha_round(s2, KN[58], w58b);
    uint32_t w59b = find_w2(s1, s2, 59, w59);
    sha_round(s1, KN[59], w59); sha_round(s2, KN[59], w59b);
    uint32_t w60b = find_w2(s1, s2, 60, w60);
    sha_round(s1, KN[60], w60); sha_round(s2, KN[60], w60b);

    /* Schedule: W[61]..W[63] */
    uint32_t W1[7] = {w57, w58, w59, w60, 0, 0, 0};
    uint32_t W2[7] = {w57b, w58b, w59b, w60b, 0, 0, 0};
    W1[4] = (fns1(W1[2]) + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & MASK;
    W2[4] = (fns1(W2[2]) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & MASK;
    W1[5] = (fns1(W1[3]) + W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & MASK;
    W2[5] = (fns1(W2[3]) + W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & MASK;
    W1[6] = (fns1(W1[4]) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & MASK;
    W2[6] = (fns1(W2[4]) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & MASK;

    for (int r = 4; r < 7; r++) {
        sha_round(s1, KN[57+r], W1[r]);
        sha_round(s2, KN[57+r], W2[r]);
    }

    uint32_t diff_mask = 0;
    for (int r = 0; r < 8; r++) {
        uint32_t d = s1[r] ^ s2[r];
        for (int k = 0; k < N; k++) {
            if (d & (1U << k))
                diff_mask |= 1U << (r * N + k);
        }
    }
    return diff_mask;
}

/*
 * ANF (Algebraic Normal Form) representation.
 * For N=4 with 16 variables, ANF terms are subsets of {0..15}.
 * Each subset is encoded as a 16-bit bitmask.
 * A Boolean function f is represented as XOR of ANF terms:
 *   f(x) = XOR of { product of x_i for i in S } for each S in the ANF
 *
 * We compute the ANF using the Mobius transform:
 *   ANF[S] = XOR over T subset S of f(T)
 */
#define MAX_TERMS 65536
static uint8_t truth_table[SPACE]; /* truth table of one output bit */

/* Compute ANF from truth table using fast Mobius transform */
static void mobius_transform(uint8_t *tt, int n) {
    for (int i = 0; i < n; i++) {
        for (uint32_t x = 0; x < (1U << n); x++) {
            if (x & (1U << i))
                tt[x] ^= tt[x ^ (1U << i)];
        }
    }
}

/* Count the number of variables in a monomial (its degree) */
static int popcount(uint32_t x) {
    int c = 0;
    while (x) { c += x & 1; x >>= 1; }
    return c;
}

int main() {
    setbuf(stdout, NULL);

    /* Setup */
    rS0[0]=SR(2); rS0[1]=SR(13); rS0[2]=SR(22);
    rS1[0]=SR(6); rS1[1]=SR(11); rS1[2]=SR(25);
    rs0[0]=SR(7); rs0[1]=SR(18); ss0=SR(3);
    rs1[0]=SR(17); rs1[1]=SR(19); ss1=SR(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & MASK;

    printf("Carry Polynomial Analysis at N=%d\n", N);
    printf("Variables: %d (bits of W1[57..60])\n", NVARS);
    printf("Search space: 2^%d = %u\n\n", NVARS, SPACE);

    /* Find candidate */
    uint32_t fills[] = {MASK, 0};
    int found = 0;
    for (int fi = 0; fi < 2 && !found; fi++) {
        for (uint32_t m0 = 0; m0 <= MASK && !found; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fills[fi]; M2[i] = fills[fi]; }
            M1[0] = m0; M2[0] = m0 ^ (1U << (N-1)); M2[9] = fills[fi] ^ (1U << (N-1));
            precompute(M1, state1, W1pre);
            precompute(M2, state2, W2pre);
            if (state1[0] == state2[0]) {
                printf("Candidate: M[0]=0x%x fill=0x%x\n\n", m0, fills[fi]);
                found = 1;
            }
        }
    }
    if (!found) { printf("No candidate\n"); return 1; }

    /* Phase 1: Evaluate collision for all 2^16 assignments */
    printf("=== Phase 1: Truth Table Construction ===\n");
    int n_coll = 0;
    uint32_t diff_masks[SPACE];
    for (uint32_t x = 0; x < SPACE; x++) {
        diff_masks[x] = eval_collision(x);
        if (diff_masks[x] == 0) n_coll++;
    }
    printf("Collisions: %d / %u\n\n", n_coll, SPACE);

    /* Phase 2: ANF for each output bit */
    printf("=== Phase 2: ANF (Algebraic Normal Form) of Each Output Bit ===\n\n");

    /* 8 registers x 4 bits = 32 output bits */
    int total_linear = 0, total_quadratic = 0, total_higher = 0, total_constant = 0;
    int total_terms = 0;
    int max_degree = 0;

    printf("Register  Bit  Constant  Linear  Quad  Cubic  Deg4+  Total  MaxDeg\n");

    for (int reg = 0; reg < 8; reg++) {
        for (int bit = 0; bit < N; bit++) {
            int out_idx = reg * N + bit;

            /* Build truth table for this output bit */
            for (uint32_t x = 0; x < SPACE; x++)
                truth_table[x] = (diff_masks[x] >> out_idx) & 1;

            /* ANF via Mobius transform */
            mobius_transform(truth_table, NVARS);

            /* Count terms by degree */
            int d0=0, d1=0, d2=0, d3=0, d4plus=0, nt=0, md=0;
            for (uint32_t S = 0; S < SPACE; S++) {
                if (truth_table[S]) {
                    int deg = popcount(S);
                    if (deg == 0) d0++;
                    else if (deg == 1) d1++;
                    else if (deg == 2) d2++;
                    else if (deg == 3) d3++;
                    else d4plus++;
                    nt++;
                    if (deg > md) md = deg;
                }
            }

            total_constant += d0;
            total_linear += d1;
            total_quadratic += d2;
            total_higher += d3 + d4plus;
            total_terms += nt;
            if (md > max_degree) max_degree = md;

            const char *regnames[] = {"a","b","c","d","e","f","g","h"};
            printf("  %s       %d     %d       %3d    %3d   %3d    %3d   %4d     %d\n",
                   regnames[reg], bit, d0, d1, d2, d3, d4plus, nt, md);
        }
    }

    printf("\nSummary:\n");
    printf("  Total output bits: %d\n", 8 * N);
    printf("  Total ANF terms: %d\n", total_terms);
    printf("  Constant: %d, Linear: %d, Quadratic: %d, Higher: %d\n",
           total_constant, total_linear, total_quadratic, total_higher);
    printf("  Max degree: %d\n", max_degree);
    printf("  Avg terms per output: %.1f\n", (double)total_terms / (8 * N));

    /* Phase 3: GF(2) linear system analysis */
    printf("\n=== Phase 3: Linear Subspace Analysis ===\n\n");

    /* Extract the linear part of the ANF system.
     * For each output bit, the linear terms form a row of a GF(2) matrix.
     * If the linear system has rank r, we can eliminate r variables. */
    uint32_t linear_matrix[32]; /* 32 rows (output bits), 16 columns (variables) */
    uint32_t constants[32]; /* constant term for each output */
    memset(linear_matrix, 0, sizeof(linear_matrix));
    memset(constants, 0, sizeof(constants));

    for (int reg = 0; reg < 8; reg++) {
        for (int bit = 0; bit < N; bit++) {
            int out_idx = reg * N + bit;

            /* Rebuild truth table */
            for (uint32_t x = 0; x < SPACE; x++)
                truth_table[x] = (diff_masks[x] >> out_idx) & 1;
            mobius_transform(truth_table, NVARS);

            /* Extract linear terms */
            uint32_t row = 0;
            for (int v = 0; v < NVARS; v++) {
                if (truth_table[1U << v])
                    row |= (1U << v);
            }
            linear_matrix[out_idx] = row;
            constants[out_idx] = truth_table[0]; /* constant term */
        }
    }

    /* GF(2) Gaussian elimination on the linear part */
    uint32_t mat[32];
    int pivots[32];
    memcpy(mat, linear_matrix, sizeof(mat));
    int rank = 0;
    for (int col = 0; col < NVARS; col++) {
        /* Find pivot */
        int piv = -1;
        for (int row = rank; row < 8 * N; row++) {
            if (mat[row] & (1U << col)) { piv = row; break; }
        }
        if (piv < 0) continue;
        /* Swap */
        uint32_t tmp = mat[rank]; mat[rank] = mat[piv]; mat[piv] = tmp;
        pivots[rank] = col;
        /* Eliminate */
        for (int row = 0; row < 8 * N; row++) {
            if (row != rank && (mat[row] & (1U << col)))
                mat[row] ^= mat[rank];
        }
        rank++;
    }

    printf("Linear part GF(2) rank: %d / %d (of %d output equations)\n",
           rank, NVARS, 8 * N);
    printf("Linear variables eliminable: %d\n", rank);
    printf("Remaining nonlinear DOF: %d\n", NVARS - rank);
    printf("Expected collisions from linear part: 2^%d = %d\n",
           NVARS - rank, 1 << (NVARS - rank));
    printf("Actual collisions: %d\n", n_coll);
    printf("Nonlinear pruning factor: 2^%d / %d = %.1f\n",
           NVARS - rank, n_coll, (double)(1 << (NVARS - rank)) / n_coll);

    /* Phase 4: Per-register analysis */
    printf("\n=== Phase 4: Per-Register Degree Analysis ===\n\n");

    /* Which registers have the lowest-degree collision equations? */
    for (int reg = 0; reg < 8; reg++) {
        int max_reg_deg = 0, total_reg_terms = 0;
        for (int bit = 0; bit < N; bit++) {
            int out_idx = reg * N + bit;
            for (uint32_t x = 0; x < SPACE; x++)
                truth_table[x] = (diff_masks[x] >> out_idx) & 1;
            mobius_transform(truth_table, NVARS);
            for (uint32_t S = 0; S < SPACE; S++) {
                if (truth_table[S]) {
                    int deg = popcount(S);
                    if (deg > max_reg_deg) max_reg_deg = deg;
                    total_reg_terms++;
                }
            }
        }
        const char *regnames[] = {"a","b","c","d","e","f","g","h"};
        printf("  d%s: max degree %d, total terms %d\n",
               regnames[reg], max_reg_deg, total_reg_terms);
    }

    /* Phase 5: Check which variable pairs appear in quadratic terms */
    printf("\n=== Phase 5: Quadratic Interaction Map ===\n");
    printf("(Which variable pairs appear together in degree-2 terms)\n\n");

    int interactions[NVARS][NVARS];
    memset(interactions, 0, sizeof(interactions));

    for (int out_idx = 0; out_idx < 8 * N; out_idx++) {
        for (uint32_t x = 0; x < SPACE; x++)
            truth_table[x] = (diff_masks[x] >> out_idx) & 1;
        mobius_transform(truth_table, NVARS);

        for (uint32_t S = 0; S < SPACE; S++) {
            if (truth_table[S] && popcount(S) == 2) {
                /* Find the two variables */
                int v1 = -1, v2 = -1;
                for (int v = 0; v < NVARS; v++) {
                    if (S & (1U << v)) {
                        if (v1 < 0) v1 = v; else v2 = v;
                    }
                }
                interactions[v1][v2]++;
                interactions[v2][v1]++;
            }
        }
    }

    /* Print interaction matrix (which W[r] bits interact) */
    printf("Variable groups: 0-3=W57 bits, 4-7=W58, 8-11=W59, 12-15=W60\n\n");
    int total_interactions = 0;
    int cross_word = 0, within_word = 0;
    for (int i = 0; i < NVARS; i++) {
        for (int j = i+1; j < NVARS; j++) {
            if (interactions[i][j] > 0) {
                total_interactions++;
                if (i / N != j / N) cross_word++;
                else within_word++;
            }
        }
    }
    printf("Total interacting pairs: %d / %d possible\n",
           total_interactions, NVARS * (NVARS-1) / 2);
    printf("Within-word: %d, Cross-word: %d\n", within_word, cross_word);

    /* Show densest interactions */
    printf("\nDensest interactions (count > 5):\n");
    for (int i = 0; i < NVARS; i++) {
        for (int j = i+1; j < NVARS; j++) {
            if (interactions[i][j] > 5) {
                printf("  x%d (W%d[%d]) x x%d (W%d[%d]): appears in %d output equations\n",
                       i, 57 + i/N, i%N, j, 57 + j/N, j%N, interactions[i][j]);
            }
        }
    }

    printf("\n=== Done ===\n");
    return 0;
}
