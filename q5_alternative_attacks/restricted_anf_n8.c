/*
 * Restricted Exact ANF at N=8: Cascade Words Only
 *
 * Computes exact Moebius transform for the sr=60 collision-difference
 * function at N=8, with W[58] and W[59] FIXED to constants.
 *
 * Free variables: W1[57](8b), W1[60](8b), W2[57](8b), W2[60](8b) = 32 bits
 * Fixed: W1[58], W1[59], W2[58], W2[59] (from a known collision or random)
 *
 * Input space: 2^32 (same as full N=4 exact ANF)
 * Output: 64 bits (8 registers × 8 bits of XOR difference)
 * Memory: 512 MB per output bit (bit-packed truth table)
 *
 * This gives EXACT algebraic degree for the cascade-only subproblem at N=8,
 * bypassing the flawed restriction test heuristic.
 *
 * Compile: gcc -O3 -march=native -o restricted_anf_n8 restricted_anf_n8.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 8
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define N_INPUT_BITS 32  /* 4 free words × 8 bits = 32 bits */
#define TABLE_SIZE (1ULL << N_INPUT_BITS)
#define TABLE_BYTES (TABLE_SIZE / 8)  /* 512 MB */

/* Scaled rotation amounts for N=8 */
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

/* Fixed compatibility words */
static uint32_t W1_58_fix, W1_59_fix, W2_58_fix, W2_59_fix;

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

/*
 * Input encoding (32 bits):
 *   bits  0-7:  W1[57]
 *   bits  8-15: W1[60]
 *   bits 16-23: W2[57]
 *   bits 24-31: W2[60]
 *
 * W1[58], W1[59], W2[58], W2[59] are fixed global constants.
 *
 * Returns: 64-bit value encoding the XOR difference (8 bits × 8 registers)
 */
static inline uint64_t eval_diff(uint32_t input) {
    uint32_t w1_57 = (input >>  0) & MASK;
    uint32_t w1_60 = (input >>  8) & MASK;
    uint32_t w2_57 = (input >> 16) & MASK;
    uint32_t w2_60 = (input >> 24) & MASK;

    /* Build schedule tail */
    uint32_t W1[7], W2[7];
    W1[0] = w1_57;       W2[0] = w2_57;
    W1[1] = W1_58_fix;   W2[1] = W2_58_fix;
    W1[2] = W1_59_fix;   W2[2] = W2_59_fix;
    W1[3] = w1_60;       W2[3] = w2_60;

    /* W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45] — schedule-determined */
    W1[4] = (fn_sigma1(W1[2]) + W1_pre[54] + fn_sigma0(W1_pre[46]) + W1_pre[45]) & MASK;
    W2[4] = (fn_sigma1(W2[2]) + W2_pre[54] + fn_sigma0(W2_pre[46]) + W2_pre[45]) & MASK;
    /* W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46] */
    W1[5] = (fn_sigma1(W1[3]) + W1_pre[55] + fn_sigma0(W1_pre[47]) + W1_pre[46]) & MASK;
    W2[5] = (fn_sigma1(W2[3]) + W2_pre[55] + fn_sigma0(W2_pre[47]) + W2_pre[46]) & MASK;
    /* W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47] */
    W1[6] = (fn_sigma1(W1[4]) + W1_pre[56] + fn_sigma0(W1_pre[48]) + W1_pre[47]) & MASK;
    W2[6] = (fn_sigma1(W2[4]) + W2_pre[56] + fn_sigma0(W2_pre[48]) + W2_pre[47]) & MASK;

    /* Run 7 rounds */
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

    /* Pack 8 regs × 8 bits into 64 bits of XOR difference */
    uint64_t diff = 0;
    diff |= (uint64_t)((a1^a2) & MASK);
    diff |= (uint64_t)((b1^b2) & MASK) << 8;
    diff |= (uint64_t)((c1^c2) & MASK) << 16;
    diff |= (uint64_t)((d1^d2) & MASK) << 24;
    diff |= (uint64_t)((e1^e2) & MASK) << 32;
    diff |= (uint64_t)((f1^f2) & MASK) << 40;
    diff |= (uint64_t)((g1^g2) & MASK) << 48;
    diff |= (uint64_t)((h1^h2) & MASK) << 56;
    return diff;
}

/* Bit manipulation for packed truth tables */
static inline int get_bit(const uint8_t *table, uint64_t idx) {
    return (table[idx >> 3] >> (idx & 7)) & 1;
}
static inline void xor_bit(uint8_t *table, uint64_t idx) {
    table[idx >> 3] ^= (1 << (idx & 7));
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    /* Parse args: restricted_anf_n8 [W1_58 W1_59 W2_58 W2_59] */
    /* Default: use collision certificate values or random */
    int use_random_fix = 1;
    if (argc >= 5) {
        W1_58_fix = (uint32_t)strtoul(argv[1], NULL, 0) & MASK;
        W1_59_fix = (uint32_t)strtoul(argv[2], NULL, 0) & MASK;
        W2_58_fix = (uint32_t)strtoul(argv[3], NULL, 0) & MASK;
        W2_59_fix = (uint32_t)strtoul(argv[4], NULL, 0) & MASK;
        use_random_fix = 0;
    }

    /* Init N=8 rotation amounts */
    r_Sig0[0]=scale_rot(2); r_Sig0[1]=scale_rot(13); r_Sig0[2]=scale_rot(22);
    r_Sig1[0]=scale_rot(6); r_Sig1[1]=scale_rot(11); r_Sig1[2]=scale_rot(25);
    r_sig0[0]=scale_rot(7); r_sig0[1]=scale_rot(18); s_sig0=scale_rot(3);
    r_sig1[0]=scale_rot(17); r_sig1[1]=scale_rot(19); s_sig1=scale_rot(10);

    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & MASK;

    printf("Restricted Exact ANF at N=%d (Cascade Words Only)\n", N);
    printf("Rotation amounts: Sig0={%d,%d,%d} Sig1={%d,%d,%d}\n",
           r_Sig0[0],r_Sig0[1],r_Sig0[2],r_Sig1[0],r_Sig1[1],r_Sig1[2]);
    printf("  sig0={%d,%d,>>%d} sig1={%d,%d,>>%d}\n",
           r_sig0[0],r_sig0[1],s_sig0,r_sig1[0],r_sig1[1],s_sig1);
    printf("Free: W1[57](8b), W1[60](8b), W2[57](8b), W2[60](8b) = 32 bits\n");
    printf("Truth table: 2^32 = 4294967296 entries\n");
    printf("Memory per bit: 512 MB\n\n");

    /* Find candidate M[0] */
    printf("Finding candidate...\n");
    int found = 0;
    for (uint32_t m0 = 0; m0 <= MASK && !found; m0++) {
        uint32_t M1[16], M2[16];
        for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
        M1[0] = m0; M2[0] = m0 ^ MSB; M2[9] = MASK ^ MSB;
        precompute(M1, state1, W1_pre);
        precompute(M2, state2, W2_pre);
        if (state1[0] == state2[0]) {
            printf("Candidate: M[0]=0x%x, da[56]=0x0\n", m0);
            found = 1;
        }
    }
    if (!found) { printf("No candidate found!\n"); return 1; }

    /* Set fixed compatibility words */
    if (use_random_fix) {
        /* Use deterministic "random" values */
        W1_58_fix = 0x42 & MASK;
        W1_59_fix = 0x7A & MASK;
        W2_58_fix = 0x3F & MASK;
        W2_59_fix = 0x91 & MASK;
    }
    printf("Fixed: W1[58]=0x%02x, W1[59]=0x%02x, W2[58]=0x%02x, W2[59]=0x%02x\n\n",
           W1_58_fix, W1_59_fix, W2_58_fix, W2_59_fix);

    /* Allocate truth table (512 MB) */
    uint8_t *table = (uint8_t *)calloc(TABLE_BYTES, 1);
    if (!table) {
        printf("Failed to allocate %llu bytes for truth table\n", (unsigned long long)TABLE_BYTES);
        return 1;
    }

    /* Process each output bit */
    const char *reg_names[] = {"a","b","c","d","e","f","g","h"};
    for (int out_bit = 0; out_bit < 8 * N; out_bit++) {
        int reg = out_bit / N;
        int pos = out_bit % N;

        printf("Output bit %d (reg %s, pos %d):\n", out_bit, reg_names[reg], pos);

        /* Build truth table */
        memset(table, 0, TABLE_BYTES);
        time_t t0 = time(NULL);
        uint64_t n_ones = 0;

        for (uint64_t inp = 0; inp < TABLE_SIZE; inp++) {
            uint64_t diff = eval_diff((uint32_t)inp);
            int bit_val = (diff >> out_bit) & 1;
            if (bit_val) {
                xor_bit(table, inp);
                n_ones++;
            }
            if ((inp & 0x0FFFFFFF) == 0 && inp > 0) {
                printf("  [%llu/%llu] %llu%%\n",
                       (unsigned long long)inp, (unsigned long long)TABLE_SIZE,
                       (unsigned long long)(100*inp/TABLE_SIZE));
            }
        }
        time_t t_table = time(NULL) - t0;
        double bias = (double)n_ones / TABLE_SIZE - 0.5;
        printf("  Truth table: %llu ones / %llu total (%.4f bias) in %lds\n",
               (unsigned long long)n_ones, (unsigned long long)TABLE_SIZE, bias, t_table);

        /* Moebius transform */
        printf("  Moebius transform...\n");
        t0 = time(NULL);
        for (int dim = 0; dim < N_INPUT_BITS; dim++) {
            uint64_t stride = 1ULL << dim;
            /* For each block of 2*stride elements, XOR the lower half into upper */
            for (uint64_t base = 0; base < TABLE_SIZE; base += 2 * stride) {
                for (uint64_t j = 0; j < stride; j++) {
                    uint64_t lo = base + j;
                    uint64_t hi = lo + stride;
                    /* Byte-level optimization when stride >= 8 */
                    if (stride >= 8) {
                        uint64_t lo_byte = lo >> 3;
                        uint64_t hi_byte = hi >> 3;
                        uint64_t n_bytes = stride >> 3;
                        for (uint64_t b = 0; b < n_bytes; b++) {
                            table[hi_byte + b] ^= table[lo_byte + b];
                        }
                        j += stride - 1; /* skip to next block */
                    } else {
                        if (get_bit(table, lo)) {
                            xor_bit(table, hi);
                        }
                    }
                }
            }
            if ((dim + 1) % 4 == 0) {
                printf("    dimension %d/%d done\n", dim + 1, N_INPUT_BITS);
            }
        }
        time_t t_moebius = time(NULL) - t0;

        /* Analyze ANF */
        int max_degree = 0;
        uint64_t total_monomials = 0;
        int deg_dist[N_INPUT_BITS + 1];
        memset(deg_dist, 0, sizeof(deg_dist));

        for (uint64_t m = 0; m < TABLE_SIZE; m++) {
            if (get_bit(table, m)) {
                int deg = __builtin_popcount((uint32_t)m);  /* works for 32 bits */
                deg_dist[deg]++;
                total_monomials++;
                if (deg > max_degree) max_degree = deg;
            }
        }

        printf("  ANF: degree=%d, monomials=%llu, transform time=%lds\n",
               max_degree, (unsigned long long)total_monomials, t_moebius);
        printf("  Degree distribution:\n");
        for (int d = 0; d <= max_degree; d++) {
            if (deg_dist[d] > 0) {
                printf("    deg %2d: %d monomials\n", d, deg_dist[d]);
            }
        }

        if (max_degree < N_INPUT_BITS / 2) {
            printf("  *** LOW DEGREE: %d / %d (%d%%) ***\n",
                   max_degree, N_INPUT_BITS, 100*max_degree/N_INPUT_BITS);
        }
        printf("\n");

        /* Early exit option: only compute first few and last few bits */
        if (out_bit == 7 && argc > 5 && strcmp(argv[5], "--quick") == 0) {
            printf("Quick mode: skipping to h register...\n\n");
            out_bit = 55;  /* will increment to 56 = h[0] */
        }
    }

    free(table);
    printf("Done.\n");
    return 0;
}
