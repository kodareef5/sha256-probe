/*
 * free_word_mitm_reducedn.c
 *
 * Reduced-width prototype for the "shape the remaining free words, then meet
 * in the middle" route from sr=60 toward sr=61.
 *
 * Model:
 *   - mini-SHA word width N with scaled rotations and truncated constants
 *   - MSB kernel: dM[0] = dM[9] = 2^(N-1)
 *   - cascade-shaped free words W57,W58,W59
 *   - W2[57..59] chosen so the a-register is zeroed each round
 *   - W60 is not free; it is schedule-derived from W58
 *
 * Interface:
 *   D60 = W2_sched60 - W2_required60  mod 2^N
 *
 * D60=0 means the schedule-derived W60 is exactly the word that the cascade
 * needs to start the e-register zeroing wave. The tool counts those matches,
 * measures the D60 fiber structure, and checks whether the tail closes through
 * rounds 60..63.
 *
 * Compile:
 *   gcc -O3 -march=native -o /tmp/free_word_mitm_reducedn \
 *     headline_hunt/bets/mitm_residue/prototypes/free_word_mitm_reducedn.c -lm
 *
 * Run:
 *   /tmp/free_word_mitm_reducedn 8
 *   /tmp/free_word_mitm_reducedn 10 65536
 */

#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static int gN;
static uint32_t gMASK;
static uint32_t gMSB;
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static uint32_t KN[64], IVN[8];

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

typedef struct {
    uint32_t w57, w58, w59;
    uint32_t w2_57, w2_58, w2_59;
    uint32_t d60;
    int r61_hw;
    int tail_hw;
} witness_t;

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * (double)gN / 32.0);
    return r < 1 ? 1 : r;
}

static void setup_width(int N) {
    gN = N;
    gMASK = (N == 32) ? 0xffffffffu : ((1u << N) - 1u);
    gMSB = 1u << (N - 1);

    rS0[0] = scale_rot(2);  rS0[1] = scale_rot(13); rS0[2] = scale_rot(22);
    rS1[0] = scale_rot(6);  rS1[1] = scale_rot(11); rS1[2] = scale_rot(25);
    rs0[0] = scale_rot(7);  rs0[1] = scale_rot(18); ss0 = scale_rot(3);
    rs1[0] = scale_rot(17); rs1[1] = scale_rot(19); ss1 = scale_rot(10);

    for (int i = 0; i < 64; i++) KN[i] = K32[i] & gMASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & gMASK;
}

static inline uint32_t ror_n(uint32_t x, int k) {
    k %= gN;
    return ((x >> k) | (x << (gN - k))) & gMASK;
}

static inline uint32_t S0(uint32_t x) {
    return (ror_n(x, rS0[0]) ^ ror_n(x, rS0[1]) ^ ror_n(x, rS0[2])) & gMASK;
}

static inline uint32_t S1(uint32_t x) {
    return (ror_n(x, rS1[0]) ^ ror_n(x, rS1[1]) ^ ror_n(x, rS1[2])) & gMASK;
}

static inline uint32_t s0(uint32_t x) {
    return (ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ (x >> ss0)) & gMASK;
}

static inline uint32_t s1(uint32_t x) {
    return (ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ (x >> ss1)) & gMASK;
}

static inline uint32_t ch(uint32_t e, uint32_t f, uint32_t g) {
    return ((e & f) ^ ((~e) & g)) & gMASK;
}

static inline uint32_t maj(uint32_t a, uint32_t b, uint32_t c) {
    return ((a & b) ^ (a & c) ^ (b & c)) & gMASK;
}

static inline int hw(uint32_t x) {
    return __builtin_popcount(x & gMASK);
}

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & gMASK;
    for (int i = 16; i < 57; i++)
        W[i] = (s1(W[i-2]) + W[i-7] + s0(W[i-15]) + W[i-16]) & gMASK;

    uint32_t a = IVN[0], b = IVN[1], c = IVN[2], d = IVN[3];
    uint32_t e = IVN[4], f = IVN[5], g = IVN[6], h = IVN[7];

    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + S1(e) + ch(e, f, g) + KN[i] + W[i]) & gMASK;
        uint32_t T2 = (S0(a) + maj(a, b, c)) & gMASK;
        h = g; g = f; f = e; e = (d + T1) & gMASK;
        d = c; c = b; b = a; a = (T1 + T2) & gMASK;
    }

    st[0] = a; st[1] = b; st[2] = c; st[3] = d;
    st[4] = e; st[5] = f; st[6] = g; st[7] = h;
}

static inline void sha_round(uint32_t st[8], int round_idx, uint32_t W) {
    uint32_t T1 = (st[7] + S1(st[4]) + ch(st[4], st[5], st[6]) + KN[round_idx] + W) & gMASK;
    uint32_t T2 = (S0(st[0]) + maj(st[0], st[1], st[2])) & gMASK;
    st[7] = st[6]; st[6] = st[5]; st[5] = st[4]; st[4] = (st[3] + T1) & gMASK;
    st[3] = st[2]; st[2] = st[1]; st[1] = st[0]; st[0] = (T1 + T2) & gMASK;
}

static inline uint32_t w2_for_zero_a(const uint32_t s1v[8], const uint32_t s2v[8],
                                      int round_idx, uint32_t w1) {
    uint32_t base1 = (s1v[7] + S1(s1v[4]) + ch(s1v[4], s1v[5], s1v[6]) + KN[round_idx]) & gMASK;
    uint32_t base2 = (s2v[7] + S1(s2v[4]) + ch(s2v[4], s2v[5], s2v[6]) + KN[round_idx]) & gMASK;
    uint32_t T21 = (S0(s1v[0]) + maj(s1v[0], s1v[1], s1v[2])) & gMASK;
    uint32_t T22 = (S0(s2v[0]) + maj(s2v[0], s2v[1], s2v[2])) & gMASK;
    return (w1 + base1 - base2 + T21 - T22) & gMASK;
}

static inline uint32_t w2_for_zero_e(const uint32_t s1v[8], const uint32_t s2v[8],
                                      int round_idx, uint32_t w1) {
    uint32_t base1 = (s1v[7] + S1(s1v[4]) + ch(s1v[4], s1v[5], s1v[6]) + KN[round_idx]) & gMASK;
    uint32_t base2 = (s2v[7] + S1(s2v[4]) + ch(s2v[4], s2v[5], s2v[6]) + KN[round_idx]) & gMASK;
    return (w1 + s1v[3] - s2v[3] + base1 - base2) & gMASK;
}

static int state_diff_hw(const uint32_t a[8], const uint32_t b[8]) {
    int out = 0;
    for (int i = 0; i < 8; i++) out += hw(a[i] ^ b[i]);
    return out;
}

static void copy_state(uint32_t dst[8], const uint32_t src[8]) {
    memcpy(dst, src, 8 * sizeof(uint32_t));
}

static int find_candidate(uint32_t *out_m0, uint32_t M1[16], uint32_t M2[16],
                          uint32_t st1[8], uint32_t st2[8],
                          uint32_t W1[64], uint32_t W2[64]) {
    uint64_t limit = (uint64_t)gMASK + 1u;
    for (uint64_t m0 = 0; m0 < limit; m0++) {
        for (int i = 0; i < 16; i++) M1[i] = gMASK;
        M1[0] = (uint32_t)m0;
        memcpy(M2, M1, 16 * sizeof(uint32_t));
        M2[0] ^= gMSB;
        M2[9] ^= gMSB;

        precompute(M1, st1, W1);
        precompute(M2, st2, W2);
        if (st1[0] == st2[0]) {
            *out_m0 = (uint32_t)m0;
            return 1;
        }
    }
    return 0;
}

static int eval_tail(const uint32_t init1[8], const uint32_t init2[8],
                     const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                     uint32_t w57, uint32_t w58, uint32_t w59,
                     witness_t *wit, uint32_t *d60_out) {
    uint32_t s1v[8], s2v[8];
    copy_state(s1v, init1);
    copy_state(s2v, init2);

    uint32_t w2_57 = w2_for_zero_a(s1v, s2v, 57, w57);
    sha_round(s1v, 57, w57);
    sha_round(s2v, 57, w2_57);

    uint32_t w2_58 = w2_for_zero_a(s1v, s2v, 58, w58);
    sha_round(s1v, 58, w58);
    sha_round(s2v, 58, w2_58);

    uint32_t W60_1 = (s1(w58) + Wpre1[53] + s0(Wpre1[45]) + Wpre1[44]) & gMASK;
    uint32_t W60_2 = (s1(w2_58) + Wpre2[53] + s0(Wpre2[45]) + Wpre2[44]) & gMASK;

    uint32_t w2_59 = w2_for_zero_a(s1v, s2v, 59, w59);
    sha_round(s1v, 59, w59);
    sha_round(s2v, 59, w2_59);

    uint32_t req_w2_60 = w2_for_zero_e(s1v, s2v, 60, W60_1);
    uint32_t d60 = (W60_2 - req_w2_60) & gMASK;
    *d60_out = d60;

    if (d60 != 0) {
        return -1;
    }

    uint32_t W61_1 = (s1(w59) + Wpre1[54] + s0(Wpre1[46]) + Wpre1[45]) & gMASK;
    uint32_t W61_2 = (s1(w2_59) + Wpre2[54] + s0(Wpre2[46]) + Wpre2[45]) & gMASK;
    uint32_t W62_1 = (s1(W60_1) + Wpre1[55] + s0(Wpre1[47]) + Wpre1[46]) & gMASK;
    uint32_t W62_2 = (s1(W60_2) + Wpre2[55] + s0(Wpre2[47]) + Wpre2[46]) & gMASK;
    uint32_t W63_1 = (s1(W61_1) + Wpre1[56] + s0(Wpre1[48]) + Wpre1[47]) & gMASK;
    uint32_t W63_2 = (s1(W61_2) + Wpre2[56] + s0(Wpre2[48]) + Wpre2[47]) & gMASK;

    sha_round(s1v, 60, W60_1);
    sha_round(s2v, 60, W60_2);
    sha_round(s1v, 61, W61_1);
    sha_round(s2v, 61, W61_2);
    int r61_hw = state_diff_hw(s1v, s2v);
    sha_round(s1v, 62, W62_1);
    sha_round(s2v, 62, W62_2);
    sha_round(s1v, 63, W63_1);
    sha_round(s2v, 63, W63_2);

    int tail_hw = state_diff_hw(s1v, s2v);
    if (wit) {
        wit->w57 = w57; wit->w58 = w58; wit->w59 = w59;
        wit->w2_57 = w2_57; wit->w2_58 = w2_58; wit->w2_59 = w2_59;
        wit->d60 = d60; wit->r61_hw = r61_hw; wit->tail_hw = tail_hw;
    }
    return tail_hw;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s N [prefix_limit]\n", argv[0]);
        fprintf(stderr, "  prefix_limit=0 or omitted means all W57,W58 prefixes.\n");
        return 2;
    }

    int N = atoi(argv[1]);
    if (N < 4 || N > 20) {
        fprintf(stderr, "N must be in [4,20] for this prototype.\n");
        return 2;
    }
    setup_width(N);

    uint64_t prefix_space = 1ull << (2 * N);
    uint64_t prefix_limit = prefix_space;
    if (argc >= 3) {
        prefix_limit = strtoull(argv[2], NULL, 0);
        if (prefix_limit == 0 || prefix_limit > prefix_space) prefix_limit = prefix_space;
    }
    uint64_t word_space = 1ull << N;

    uint32_t M1[16], M2[16], init1[8], init2[8], Wpre1[64] = {0}, Wpre2[64] = {0};
    uint32_t m0 = 0;
    if (!find_candidate(&m0, M1, M2, init1, init2, Wpre1, Wpre2)) {
        fprintf(stderr, "No da56=0 candidate found at N=%d.\n", N);
        return 1;
    }

    uint64_t *d_hist = calloc((size_t)word_space, sizeof(uint64_t));
    uint64_t *fiber_hist = calloc((size_t)(word_space + 1u), sizeof(uint64_t));
    if (!d_hist || !fiber_hist) {
        fprintf(stderr, "Allocation failed.\n");
        free(d_hist); free(fiber_hist);
        return 1;
    }

    uint64_t d_hw_hist[33] = {0};
    uint64_t total = 0;
    uint64_t d0 = 0;
    uint64_t collision = 0;
    uint64_t prefixes_with_d0 = 0;
    uint64_t max_d0_per_prefix = 0;
    uint32_t max_pref_w57 = 0, max_pref_w58 = 0;
    int min_d_hw = 99;
    int min_r61_hw = 999;
    int min_tail_hw = 999;
    witness_t best_r61 = {0};
    witness_t best_tail = {0};
    witness_t first_collision = {0};

    clock_t t0 = clock();

    uint64_t perm_step = 11400714819323198485ull;
    const char *prefix_mode = (prefix_limit == prefix_space) ? "exact" : "permuted-prefix-sample";

    for (uint64_t i = 0; i < prefix_limit; i++) {
        uint64_t p = (prefix_limit == prefix_space) ? i : ((i * perm_step) & (prefix_space - 1u));
        uint32_t w57 = (uint32_t)(p & gMASK);
        uint32_t w58 = (uint32_t)((p >> N) & gMASK);
        uint64_t prefix_d0 = 0;

        for (uint64_t w = 0; w < word_space; w++) {
            uint32_t d60 = 0;
            witness_t wit;
            int tail_hw = eval_tail(init1, init2, Wpre1, Wpre2, w57, w58, (uint32_t)w, &wit, &d60);
            total++;
            d_hist[d60]++;
            int dhw = hw(d60);
            d_hw_hist[dhw]++;
            if (dhw < min_d_hw) min_d_hw = dhw;

            if (d60 == 0) {
                d0++;
                prefix_d0++;
                if (wit.r61_hw < min_r61_hw) {
                    min_r61_hw = wit.r61_hw;
                    best_r61 = wit;
                }
                if (tail_hw >= 0 && tail_hw < min_tail_hw) {
                    min_tail_hw = tail_hw;
                    best_tail = wit;
                }
                if (tail_hw == 0) {
                    if (collision == 0) first_collision = wit;
                    collision++;
                }
            }
        }

        if (prefix_d0) {
            prefixes_with_d0++;
            fiber_hist[prefix_d0]++;
            if (prefix_d0 > max_d0_per_prefix) {
                max_d0_per_prefix = prefix_d0;
                max_pref_w57 = w57;
                max_pref_w58 = w58;
            }
        }
    }

    uint64_t max_bucket = 0;
    uint32_t max_bucket_d = 0;
    for (uint64_t d = 0; d < word_space; d++) {
        if (d_hist[d] > max_bucket) {
            max_bucket = d_hist[d];
            max_bucket_d = (uint32_t)d;
        }
    }

    double elapsed = (double)(clock() - t0) / (double)CLOCKS_PER_SEC;
    double expected_d0 = (double)total / (double)word_space;

    printf("free_word_mitm_reducedn\n");
    printf("N=%d mask=0x%x msb=0x%x\n", N, gMASK, gMSB);
    printf("candidate: M0=0x%x fill=0x%x kernel=dM0=dM9=0x%x\n", m0, gMASK, gMSB);
    printf("prefixes=%" PRIu64 "/%" PRIu64 " mode=%s w59_per_prefix=%" PRIu64 " total=%" PRIu64 "\n",
           prefix_limit, prefix_space, prefix_mode, word_space, total);
    printf("elapsed=%.3fs rate=%.2f Mtriples/s\n", elapsed, elapsed > 0.0 ? (double)total / elapsed / 1e6 : 0.0);
    printf("\nD60 interface\n");
    printf("  D60=0 matches: %" PRIu64 " (random expectation %.1f, enrichment %.3fx)\n",
           d0, expected_d0, expected_d0 > 0.0 ? (double)d0 / expected_d0 : 0.0);
    printf("  prefixes with D60=0: %" PRIu64 "\n", prefixes_with_d0);
    printf("  max D60=0 fiber per prefix: %" PRIu64 " at W57=0x%x W58=0x%x\n",
           max_d0_per_prefix, max_pref_w57, max_pref_w58);
    printf("  largest D60 bucket: D=0x%x count=%" PRIu64 "\n", max_bucket_d, max_bucket);
    printf("  min D60 HW: %d\n", min_d_hw);
    printf("  D60 HW histogram:");
    for (int i = 0; i <= N; i++) {
        if (d_hw_hist[i]) printf(" %d:%" PRIu64, i, d_hw_hist[i]);
    }
    printf("\n");

    printf("\nTail closure among D60=0 matches\n");
    printf("  final tail collisions: %" PRIu64 "\n", collision);
    if (min_r61_hw < 999) {
        printf("  best r61 HW: %d\n", min_r61_hw);
        printf("  best r61 W1[57..59]=0x%x,0x%x,0x%x\n", best_r61.w57, best_r61.w58, best_r61.w59);
        printf("  best r61 W2[57..59]=0x%x,0x%x,0x%x\n", best_r61.w2_57, best_r61.w2_58, best_r61.w2_59);
    } else {
        printf("  best r61 HW: n/a (no D60=0 matches)\n");
    }
    if (min_tail_hw < 999) {
        printf("  best tail HW: %d\n", min_tail_hw);
        printf("  best tail r61 HW: %d\n", best_tail.r61_hw);
        printf("  best W1[57..59]=0x%x,0x%x,0x%x\n", best_tail.w57, best_tail.w58, best_tail.w59);
        printf("  best W2[57..59]=0x%x,0x%x,0x%x\n", best_tail.w2_57, best_tail.w2_58, best_tail.w2_59);
    } else {
        printf("  best tail HW: n/a (no D60=0 matches)\n");
    }
    if (collision) {
        printf("  first collision W1[57..59]=0x%x,0x%x,0x%x\n",
               first_collision.w57, first_collision.w58, first_collision.w59);
        printf("  first collision W2[57..59]=0x%x,0x%x,0x%x\n",
               first_collision.w2_57, first_collision.w2_58, first_collision.w2_59);
    }

    printf("\nD60=0 fiber histogram:");
    int printed = 0;
    for (uint64_t i = 1; i <= word_space; i++) {
        if (fiber_hist[i]) {
            printf(" %" PRIu64 ":%" PRIu64, i, fiber_hist[i]);
            printed++;
            if (printed >= 24) break;
        }
    }
    if (!printed) printf(" empty");
    printf("\n");

    free(d_hist);
    free(fiber_hist);
    return 0;
}
