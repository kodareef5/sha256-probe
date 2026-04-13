/*
 * exotic_kernel.c — Explore exotic differential kernels at small N
 *
 * Tests non-standard differential configurations:
 * 1. Multi-bit deltas: dM[0] = 0x03 (bits 0+1), 0x05 (bits 0+2), etc.
 * 2. Asymmetric deltas: dM[0] != dM[9]
 * 3. Non-(0,9) word pairs: dM[i] + dM[j] for various i,j
 * 4. Three-word deltas: dM[i] + dM[j] + dM[k]
 * 5. Rotation-aligned: delta chosen to align with Sigma rotation positions
 *
 * The cascade constraint requires da[56]=0. For non-standard kernels,
 * we search for (M[0], fill) combinations that satisfy da[56]=0 for each
 * kernel configuration.
 *
 * Compile: gcc -O3 -march=native -o exotic_kernel exotic_kernel.c -lm
 * Usage: ./exotic_kernel [N]  (default N=4)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

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

static uint32_t W1pre[57], W2pre[57], st1[8], st2[8];

static void precompute(const uint32_t M[16], uint32_t state[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & gMASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],
             e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
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

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd]) & gMASK;
    uint32_t r2 = (s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd]) & gMASK;
    uint32_t T21 = (fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2])) & gMASK;
    uint32_t T22 = (fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2])) & gMASK;
    return (w1 + r1 - r2 + T21 - T22) & gMASK;
}

/* Count collisions for the current st1/st2/W1pre/W2pre */
static int count_collisions(void) {
    int nc = 0;
    for (uint32_t w57 = 0; w57 < (1U << gN); w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, st1, 32); memcpy(s57b, st2, 32);
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
                for (uint32_t w60 = 0; w60 < (1U << gN); w60++) {
                    uint32_t fa[8], fb[8];
                    memcpy(fa, s59a, 32); memcpy(fb, s59b, 32);
                    uint32_t w60b = find_w2(fa, fb, 60, w60);
                    sha_round(fa, KN[60], w60); sha_round(fb, KN[60], w60b);
                    uint32_t W1[7]={w57,w58,w59,w60,0,0,0};
                    uint32_t W2[7]={w57b,w58b,w59b,w60b,0,0,0};
                    W1[4]=(fns1(W1[2])+W1pre[54]+fns0(W1pre[46])+W1pre[45])&gMASK;
                    W2[4]=(fns1(W2[2])+W2pre[54]+fns0(W2pre[46])+W2pre[45])&gMASK;
                    W1[5]=(fns1(W1[3])+W1pre[55]+fns0(W1pre[47])+W1pre[46])&gMASK;
                    W2[5]=(fns1(W2[3])+W2pre[55]+fns0(W2pre[47])+W2pre[46])&gMASK;
                    W1[6]=(fns1(W1[4])+W1pre[56]+fns0(W1pre[48])+W1pre[47])&gMASK;
                    W2[6]=(fns1(W2[4])+W2pre[56]+fns0(W2pre[48])+W2pre[47])&gMASK;
                    for (int r = 4; r < 7; r++) {
                        sha_round(fa, KN[57+r], W1[r]);
                        sha_round(fb, KN[57+r], W2[r]);
                    }
                    int ok = 1;
                    for (int r = 0; r < 8; r++) if (fa[r] != fb[r]) { ok = 0; break; }
                    if (ok) nc++;
                }
            }
        }
    }
    return nc;
}

/*
 * Test a kernel configuration:
 * - dM[word_indices[i]] ^= deltas[i] for i=0..n_words-1
 * - Try multiple fills
 * - Return best collision count
 */
typedef struct {
    int n_words;
    int word_indices[4]; /* which message words to flip (0..15) */
    uint32_t deltas[4];  /* XOR delta for each word */
    char desc[64];       /* human-readable description */
} kernel_config_t;

static int test_kernel(const kernel_config_t *k) {
    uint32_t fills[] = {gMASK, 0, gMASK >> 1, 1U << (gN-1)};
    int nfills = 4;
    int best_nc = 0;

    for (int fi = 0; fi < nfills; fi++) {
        /* Try multiple M[0] values */
        for (uint32_t m0 = 0; m0 <= gMASK; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fills[fi]; M2[i] = fills[fi]; }
            M1[0] = m0; M2[0] = m0;

            /* Apply kernel deltas */
            for (int w = 0; w < k->n_words; w++) {
                M2[k->word_indices[w]] ^= k->deltas[w];
            }

            /* Also ensure M1[0] varies to get different candidates */
            precompute(M1, st1, W1pre);
            precompute(M2, st2, W2pre);
            if (st1[0] != st2[0]) continue; /* da[56] != 0 */

            int nc = count_collisions();
            if (nc > best_nc) best_nc = nc;
            if (nc > 0) break; /* take first candidate per fill with collisions */
        }
    }
    return best_nc;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    gN = argc > 1 ? atoi(argv[1]) : 4;
    if (gN > 8) { printf("N must be <= 8 for scalar exploration\n"); return 1; }
    gMASK = (1U << gN) - 1;

    rS0[0]=scale_rot(2); rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6); rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7); rs0[1]=scale_rot(18); ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19); ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & gMASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & gMASK;

    printf("Exotic Kernel Explorer at N=%d\n", gN);
    printf("Rotations: S0={%d,%d,%d} S1={%d,%d,%d}\n\n",
           rS0[0], rS0[1], rS0[2], rS1[0], rS1[1], rS1[2]);

    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    int global_best = 0;
    char global_desc[64] = "";

    printf("%-45s  Coll   Best?\n", "Configuration");
    printf("%-45s  ----   -----\n", "-------------");

    /* ===== Category 1: Standard single-bit kernels (baseline) ===== */
    printf("\n--- Standard single-bit kernels dM[0]=dM[9]=2^bit ---\n");
    for (int bit = 0; bit < gN; bit++) {
        kernel_config_t k = {
            .n_words = 2,
            .word_indices = {0, 9},
            .deltas = {1U << bit, 1U << bit}
        };
        snprintf(k.desc, sizeof(k.desc), "dM[0]=dM[9]=2^%d", bit);
        int nc = test_kernel(&k);
        char tag[8] = "";
        if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
        printf("  %-43s  %4d%s\n", k.desc, nc, tag);
    }

    /* ===== Category 2: Multi-bit deltas ===== */
    printf("\n--- Multi-bit deltas dM[0]=dM[9]=delta ---\n");
    /* Test all 2-bit combinations */
    for (int b1 = 0; b1 < gN; b1++) {
        for (int b2 = b1+1; b2 < gN; b2++) {
            uint32_t delta = (1U << b1) | (1U << b2);
            kernel_config_t k = {
                .n_words = 2,
                .word_indices = {0, 9},
                .deltas = {delta, delta}
            };
            snprintf(k.desc, sizeof(k.desc), "dM[0]=dM[9]=2^%d+2^%d (0x%x)", b1, b2, delta);
            int nc = test_kernel(&k);
            char tag[8] = "";
            if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
            printf("  %-43s  %4d%s\n", k.desc, nc, tag);
        }
    }
    /* Test 3-bit combos at N=4 */
    if (gN <= 5) {
        for (int b1 = 0; b1 < gN; b1++) {
            for (int b2 = b1+1; b2 < gN; b2++) {
                for (int b3 = b2+1; b3 < gN; b3++) {
                    uint32_t delta = (1U << b1) | (1U << b2) | (1U << b3);
                    kernel_config_t k = {
                        .n_words = 2,
                        .word_indices = {0, 9},
                        .deltas = {delta, delta}
                    };
                    snprintf(k.desc, sizeof(k.desc), "dM[0]=dM[9]=2^%d+2^%d+2^%d", b1, b2, b3);
                    int nc = test_kernel(&k);
                    char tag[8] = "";
                    if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
                    printf("  %-43s  %4d%s\n", k.desc, nc, tag);
                }
            }
        }
    }

    /* ===== Category 3: Asymmetric deltas ===== */
    printf("\n--- Asymmetric deltas dM[0] != dM[9] ---\n");
    for (int b0 = 0; b0 < gN; b0++) {
        for (int b9 = 0; b9 < gN; b9++) {
            if (b0 == b9) continue; /* symmetric already tested */
            kernel_config_t k = {
                .n_words = 2,
                .word_indices = {0, 9},
                .deltas = {1U << b0, 1U << b9}
            };
            snprintf(k.desc, sizeof(k.desc), "dM[0]=2^%d, dM[9]=2^%d", b0, b9);
            int nc = test_kernel(&k);
            char tag[8] = "";
            if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
            printf("  %-43s  %4d%s\n", k.desc, nc, tag);
        }
    }

    /* ===== Category 4: Non-(0,9) word pairs ===== */
    printf("\n--- Non-(0,9) word pairs dM[i]=dM[j]=MSB ---\n");
    /* The Viragh paper uses (0,9) because sigma0(M[1])=sigma0(M[1]+delta)
     * when delta is in the right position. But other pairs might work too. */
    int word_pairs[][2] = {{0,1},{0,4},{0,5},{0,8},{0,10},{0,14},{1,9},{1,10},
                           {2,9},{3,9},{4,9},{5,9},{0,13},{1,14},{2,11},{3,12}};
    int npairs = sizeof(word_pairs) / sizeof(word_pairs[0]);
    for (int p = 0; p < npairs; p++) {
        int i = word_pairs[p][0], j = word_pairs[p][1];
        for (int bit = 0; bit < gN; bit++) {
            kernel_config_t k = {
                .n_words = 2,
                .word_indices = {i, j},
                .deltas = {1U << bit, 1U << bit}
            };
            snprintf(k.desc, sizeof(k.desc), "dM[%d]=dM[%d]=2^%d", i, j, bit);
            int nc = test_kernel(&k);
            char tag[8] = "";
            if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
            if (nc > 0)
                printf("  %-43s  %4d%s\n", k.desc, nc, tag);
        }
    }

    /* ===== Category 5: Three-word deltas ===== */
    printf("\n--- Three-word deltas ---\n");
    int triples[][3] = {{0,4,9},{0,5,9},{0,1,9},{0,9,14},{1,4,9},{0,8,9}};
    int ntriples = sizeof(triples) / sizeof(triples[0]);
    for (int t = 0; t < ntriples; t++) {
        int i = triples[t][0], j = triples[t][1], k_idx = triples[t][2];
        for (int bit = 0; bit < gN; bit++) {
            kernel_config_t k = {
                .n_words = 3,
                .word_indices = {i, j, k_idx},
                .deltas = {1U << bit, 1U << bit, 1U << bit}
            };
            snprintf(k.desc, sizeof(k.desc), "dM[%d]=dM[%d]=dM[%d]=2^%d", i, j, k_idx, bit);
            int nc = test_kernel(&k);
            char tag[8] = "";
            if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
            if (nc > 0)
                printf("  %-43s  %4d%s\n", k.desc, nc, tag);
        }
    }

    /* ===== Category 6: Single-word deltas ===== */
    printf("\n--- Single-word deltas dM[i]=2^bit (word 0 only) ---\n");
    for (int bit = 0; bit < gN; bit++) {
        kernel_config_t k = {
            .n_words = 1,
            .word_indices = {0},
            .deltas = {1U << bit}
        };
        snprintf(k.desc, sizeof(k.desc), "dM[0]=2^%d only (no dM[9])", bit);
        int nc = test_kernel(&k);
        char tag[8] = "";
        if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
        if (nc > 0)
            printf("  %-43s  %4d%s\n", k.desc, nc, tag);
    }

    /* ===== Category 7: Rotation-aligned kernels ===== */
    printf("\n--- Rotation-aligned kernels ---\n");
    /* Choose delta bits that align with the Sigma rotation amounts */
    {
        /* Try delta that is exactly sigma0(2^bit) */
        for (int bit = 0; bit < gN; bit++) {
            uint32_t d = fns0(1U << bit);
            kernel_config_t k = {
                .n_words = 2,
                .word_indices = {0, 9},
                .deltas = {d, d}
            };
            snprintf(k.desc, sizeof(k.desc), "dM=sigma0(2^%d)=0x%x", bit, d);
            int nc = test_kernel(&k);
            char tag[8] = "";
            if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
            printf("  %-43s  %4d%s\n", k.desc, nc, tag);
        }
        /* Try delta that is Sigma0(2^bit) */
        for (int bit = 0; bit < gN; bit++) {
            uint32_t d = fnS0(1U << bit);
            kernel_config_t k = {
                .n_words = 2,
                .word_indices = {0, 9},
                .deltas = {d, d}
            };
            snprintf(k.desc, sizeof(k.desc), "dM=Sigma0(2^%d)=0x%x", bit, d);
            int nc = test_kernel(&k);
            char tag[8] = "";
            if (nc > global_best) { global_best = nc; strcpy(global_desc, k.desc); strcpy(tag, " <<<"); }
            printf("  %-43s  %4d%s\n", k.desc, nc, tag);
        }
    }

    struct timespec t1;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double el = (t1.tv_sec-t0.tv_sec) + (t1.tv_nsec-t0.tv_nsec)/1e9;

    printf("\n=== Summary ===\n");
    printf("Best overall: %d collisions\n", global_best);
    printf("Configuration: %s\n", global_desc);
    printf("Total time: %.1fs\n", el);
    printf("\nCategories tested: single-bit, multi-bit, asymmetric, non-(0,9),\n");
    printf("  three-word, single-word, rotation-aligned\n");

    return 0;
}
