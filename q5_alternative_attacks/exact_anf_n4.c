/*
 * Step 3: Exact ANF at N=4 via Moebius Transform
 *
 * Computes the complete truth table and exact Algebraic Normal Form
 * of every output bit of the sr=60 collision-difference function at
 * N=4 word width.
 *
 * Input space: 2 messages × 4 words × 4 bits = 32 bits → 2^32 evaluations
 * Output: 32 bits (4 bits × 8 registers of XOR difference)
 *
 * The Moebius transform converts a truth table to ANF coefficients:
 *   anf[m] = XOR over all x ⊆ m of f(x)
 * where ⊆ means x AND m = x (all set bits of x are set in m).
 *
 * Compile: gcc -O3 -march=native -o exact_anf_n4 exact_anf_n4.c -lm
 * Memory: 2^32 bits per output bit = 512 MB per bit, 32 bits = 16 GB
 *         TOO MUCH for macbook. Use bit-sliced approach: process 64 output
 *         bits at once using uint64_t, needing 512 MB total.
 *
 * Actually: 2^32 entries × 1 bit = 4 GB per truth table.
 * We have 32 output bits. Processing one at a time: 4 GB + 4 GB = 8 GB.
 * Tight for 16GB macbook. Use bit-packed arrays (2^32 / 8 = 512 MB per table).
 *
 * Alternatively: process ALL 32 output bits simultaneously by packing
 * them into uint32_t. One array of 2^32 × uint32_t = 16 GB. Too much.
 *
 * REVISED PLAN: Process output bits one at a time.
 * Each needs: 2^32 / 8 bytes = 512 MB for the truth table.
 * Moebius transform is in-place. Total memory: ~512 MB. Feasible.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 4
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define N_INPUT_BITS (2 * 4 * N)  /* 32 */
#define TABLE_SIZE (1ULL << N_INPUT_BITS)  /* 2^32 = 4 billion */
#define TABLE_BYTES (TABLE_SIZE / 8)  /* 512 MB for bit-packed */

/* Scaled rotation amounts for N=4 */
static int r_Sig0[3], r_Sig1[3], r_sig0[2], r_sig1[2], s_sig0, s_sig1;

static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N;
    return ((x >> k) | (x << (N - k))) & MASK;
}
static inline uint32_t fn_Sigma0(uint32_t a) { return ror_n(a,r_Sig0[0])^ror_n(a,r_Sig0[1])^ror_n(a,r_Sig0[2]); }
static inline uint32_t fn_Sigma1(uint32_t e) { return ror_n(e,r_Sig1[0])^ror_n(e,r_Sig1[1])^ror_n(e,r_Sig1[2]); }
static inline uint32_t fn_sigma0(uint32_t x) { return ror_n(x,r_sig0[0])^ror_n(x,r_sig0[1])^((x>>s_sig0)&MASK); }
static inline uint32_t fn_sigma1(uint32_t x) { return ror_n(x,r_sig1[0])^ror_n(x,r_sig1[1])^((x>>s_sig1)&MASK); }
static inline uint32_t fn_Ch(uint32_t e, uint32_t f, uint32_t g) { return ((e&f)^((~e)&g))&MASK; }
static inline uint32_t fn_Maj(uint32_t a, uint32_t b, uint32_t c) { return ((a&b)^(a&c)^(b&c))&MASK; }

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
static uint32_t state1[8], state2[8];
static uint32_t W1_pre[57], W2_pre[57];

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fn_sigma1(W[i-2]) + W[i-7] + fn_sigma0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fn_Sigma1(e) + fn_Ch(e,f,g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fn_Sigma0(a) + fn_Maj(a,b,c)) & MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/* Evaluate the collision difference for a single input.
 * Input: 32-bit value encoding (W1[57..60], W2[57..60]) as:
 *   bits  0-3:  W1[57]
 *   bits  4-7:  W1[58]
 *   bits  8-11: W1[59]
 *   bits 12-15: W1[60]
 *   bits 16-19: W2[57]
 *   bits 20-23: W2[58]
 *   bits 24-27: W2[59]
 *   bits 28-31: W2[60]
 * Returns: 32-bit value encoding the XOR difference (4 bits × 8 registers)
 */
static inline uint32_t eval_diff(uint32_t input) {
    uint32_t w1[4], w2[4];
    w1[0] = (input >>  0) & MASK;
    w1[1] = (input >>  4) & MASK;
    w1[2] = (input >>  8) & MASK;
    w1[3] = (input >> 12) & MASK;
    w2[0] = (input >> 16) & MASK;
    w2[1] = (input >> 20) & MASK;
    w2[2] = (input >> 24) & MASK;
    w2[3] = (input >> 28) & MASK;

    /* Build schedule tail */
    uint32_t W1[7], W2[7];
    for (int i = 0; i < 4; i++) { W1[i] = w1[i]; W2[i] = w2[i]; }
    W1[4] = (fn_sigma1(W1[2]) + W1_pre[54] + fn_sigma0(W1_pre[46]) + W1_pre[45]) & MASK;
    W2[4] = (fn_sigma1(W2[2]) + W2_pre[54] + fn_sigma0(W2_pre[46]) + W2_pre[45]) & MASK;
    W1[5] = (fn_sigma1(W1[3]) + W1_pre[55] + fn_sigma0(W1_pre[47]) + W1_pre[46]) & MASK;
    W2[5] = (fn_sigma1(W2[3]) + W2_pre[55] + fn_sigma0(W2_pre[47]) + W2_pre[46]) & MASK;
    W1[6] = (fn_sigma1(W1[4]) + W1_pre[56] + fn_sigma0(W1_pre[48]) + W1_pre[47]) & MASK;
    W2[6] = (fn_sigma1(W2[4]) + W2_pre[56] + fn_sigma0(W2_pre[48]) + W2_pre[47]) & MASK;

    /* Run 7 rounds for both messages */
    uint32_t a1=state1[0],b1=state1[1],c1=state1[2],d1=state1[3];
    uint32_t e1=state1[4],f1=state1[5],g1=state1[6],h1=state1[7];
    uint32_t a2=state2[0],b2=state2[1],c2=state2[2],d2=state2[3];
    uint32_t e2=state2[4],f2=state2[5],g2=state2[6],h2=state2[7];

    for (int i = 0; i < 7; i++) {
        uint32_t T1a = (h1+fn_Sigma1(e1)+fn_Ch(e1,f1,g1)+KN[57+i]+W1[i]) & MASK;
        uint32_t T2a = (fn_Sigma0(a1)+fn_Maj(a1,b1,c1)) & MASK;
        h1=g1;g1=f1;f1=e1;e1=(d1+T1a)&MASK;d1=c1;c1=b1;b1=a1;a1=(T1a+T2a)&MASK;
        uint32_t T1b = (h2+fn_Sigma1(e2)+fn_Ch(e2,f2,g2)+KN[57+i]+W2[i]) & MASK;
        uint32_t T2b = (fn_Sigma0(a2)+fn_Maj(a2,b2,c2)) & MASK;
        h2=g2;g2=f2;f2=e2;e2=(d2+T1b)&MASK;d2=c2;c2=b2;b2=a2;a2=(T1b+T2b)&MASK;
    }

    /* Pack 8 registers × 4 bits into 32 bits of XOR difference */
    return ((a1^a2) & MASK) | (((b1^b2) & MASK) << 4) | (((c1^c2) & MASK) << 8) |
           (((d1^d2) & MASK) << 12) | (((e1^e2) & MASK) << 16) | (((f1^f2) & MASK) << 20) |
           (((g1^g2) & MASK) << 24) | (((h1^h2) & MASK) << 28);
}

/* Bit manipulation for packed truth tables */
static inline int get_bit(const uint8_t *table, uint64_t idx) {
    return (table[idx >> 3] >> (idx & 7)) & 1;
}
static inline void set_bit(uint8_t *table, uint64_t idx, int val) {
    if (val)
        table[idx >> 3] |= (1 << (idx & 7));
    else
        table[idx >> 3] &= ~(1 << (idx & 7));
}
static inline void xor_bit(uint8_t *table, uint64_t idx, int val) {
    if (val)
        table[idx >> 3] ^= (1 << (idx & 7));
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    /* Initialize N=4 parameters */
    r_Sig0[0]=scale_rot(2); r_Sig0[1]=scale_rot(13); r_Sig0[2]=scale_rot(22);
    r_Sig1[0]=scale_rot(6); r_Sig1[1]=scale_rot(11); r_Sig1[2]=scale_rot(25);
    r_sig0[0]=scale_rot(7); r_sig0[1]=scale_rot(18); s_sig0=scale_rot(3);
    r_sig1[0]=scale_rot(17); r_sig1[1]=scale_rot(19); s_sig1=scale_rot(10);

    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & MASK;

    printf("Exact ANF at N=%d\n", N);
    printf("Rotation amounts: Sig0={%d,%d,%d} Sig1={%d,%d,%d}\n",
           r_Sig0[0],r_Sig0[1],r_Sig0[2], r_Sig1[0],r_Sig1[1],r_Sig1[2]);
    printf("  sig0={%d,%d,>>%d} sig1={%d,%d,>>%d}\n",
           r_sig0[0],r_sig0[1],s_sig0, r_sig1[0],r_sig1[1],s_sig1);
    printf("Input bits: %d, Output bits: %d\n", N_INPUT_BITS, 8*N);
    printf("Truth table: 2^%d = %llu entries\n", N_INPUT_BITS, TABLE_SIZE);
    printf("Memory per bit: %llu MB\n\n", TABLE_BYTES / (1024*1024));

    /* Find candidate: scan M[0] for da[56]=0 */
    printf("Finding candidate...\n");
    uint32_t m0_found = 0;
    int found = 0;
    for (uint32_t m0 = 0; m0 <= MASK && !found; m0++) {
        uint32_t M1[16], M2[16];
        for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
        M1[0] = m0; M2[0] = m0 ^ MSB; M2[9] = MASK ^ MSB;

        uint32_t s1[8], s2[8], w1[57], w2[57];
        precompute(M1, s1, w1);
        precompute(M2, s2, w2);

        if (s1[0] == s2[0]) {
            m0_found = m0;
            memcpy(state1, s1, sizeof(s1));
            memcpy(state2, s2, sizeof(s2));
            memcpy(W1_pre, w1, sizeof(w1));
            memcpy(W2_pre, w2, sizeof(w2));
            found = 1;
            printf("Candidate: M[0]=0x%x, da[56]=0x%x\n", m0, s1[0] ^ s2[0]);
        }
    }
    if (!found) {
        /* Try fill=0 */
        for (uint32_t m0 = 0; m0 <= MASK; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = 0; M2[i] = 0; }
            M1[0] = m0; M2[0] = m0 ^ MSB; M2[9] = MSB;
            uint32_t s1[8], s2[8], w1[57], w2[57];
            precompute(M1, s1, w1);
            precompute(M2, s2, w2);
            if (s1[0] == s2[0]) {
                m0_found = m0;
                memcpy(state1, s1, sizeof(s1));
                memcpy(state2, s2, sizeof(s2));
                memcpy(W1_pre, w1, sizeof(w1));
                memcpy(W2_pre, w2, sizeof(w2));
                found = 1;
                printf("Candidate (fill=0): M[0]=0x%x\n", m0);
                break;
            }
        }
    }
    if (!found) { printf("No candidate found!\n"); return 1; }

    /* Allocate truth table (bit-packed) */
    uint8_t *tt = (uint8_t *)calloc(TABLE_BYTES, 1);
    if (!tt) { printf("Failed to allocate %llu MB!\n", TABLE_BYTES/(1024*1024)); return 1; }

    /* Process each output bit */
    for (int out_bit = 0; out_bit < 8 * N; out_bit++) {
        int reg = out_bit / N;
        int pos = out_bit % N;

        printf("\nOutput bit %d (reg %c, pos %d):\n", out_bit, "abcdefgh"[reg], pos);

        /* Build truth table */
        time_t t0 = time(NULL);
        memset(tt, 0, TABLE_BYTES);

        uint64_t n_ones = 0;
        for (uint64_t input = 0; input < TABLE_SIZE; input++) {
            uint32_t diff = eval_diff((uint32_t)input);
            int bit_val = (diff >> out_bit) & 1;
            if (bit_val) {
                set_bit(tt, input, 1);
                n_ones++;
            }

            if ((input & 0x0FFFFFFF) == 0 && input > 0) {
                printf("  [%llu/%llu] %.0f%%\n", input, TABLE_SIZE,
                       100.0 * input / TABLE_SIZE);
            }
        }
        time_t t1 = time(NULL);
        printf("  Truth table: %llu ones / %llu total (%.4f bias) in %lds\n",
               n_ones, TABLE_SIZE, (double)n_ones / TABLE_SIZE - 0.5, (long)(t1-t0));

        /* Moebius transform (in-place) */
        printf("  Moebius transform...\n");
        t0 = time(NULL);
        for (int i = 0; i < N_INPUT_BITS; i++) {
            uint64_t step = 1ULL << i;
            /* For each block of size 2*step, XOR the first half into the second half */
            for (uint64_t j = 0; j < TABLE_SIZE; j += 2 * step) {
                for (uint64_t k = 0; k < step; k++) {
                    int val = get_bit(tt, j + k);
                    xor_bit(tt, j + k + step, val);
                }
            }
            if (i % 4 == 3) {
                printf("    dimension %d/%d done\n", i+1, N_INPUT_BITS);
            }
        }
        t1 = time(NULL);

        /* Analyze ANF */
        int degree = 0;
        uint64_t n_monomials = 0;
        int degree_histogram[N_INPUT_BITS + 1];
        memset(degree_histogram, 0, sizeof(degree_histogram));

        for (uint64_t idx = 0; idx < TABLE_SIZE; idx++) {
            if (get_bit(tt, idx)) {
                n_monomials++;
                int w = __builtin_popcount((uint32_t)idx);  /* weight of monomial */
                if (w > degree) degree = w;
                degree_histogram[w]++;
            }
        }

        printf("  ANF: degree=%d, monomials=%llu, transform time=%lds\n",
               degree, n_monomials, (long)(t1-t0));
        printf("  Degree distribution:\n");
        for (int d = 0; d <= degree; d++) {
            if (degree_histogram[d] > 0)
                printf("    deg %2d: %d monomials\n", d, degree_histogram[d]);
        }

        /* Check if degree is unexpectedly low */
        if (degree < N_INPUT_BITS / 2) {
            printf("  *** LOW DEGREE: %d / %d (%.0f%%) ***\n",
                   degree, N_INPUT_BITS, 100.0 * degree / N_INPUT_BITS);
        }
    }

    free(tt);
    printf("\nDone.\n");
    return 0;
}
