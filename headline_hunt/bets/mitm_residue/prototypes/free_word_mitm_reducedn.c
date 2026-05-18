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
 *   /tmp/free_word_mitm_reducedn 12 262144 50000000 512 0
 *   /tmp/free_word_mitm_reducedn 12 262144 0 1024 524288 scan
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
    uint32_t gh60_key;
    uint64_t r61_mask_lo, r61_mask_hi;
    uint64_t tail_carry_sig;
    int r61_hw;
    int tail_hw;
} witness_t;

typedef struct {
    uint64_t lo, hi;
    uint32_t count;
    uint8_t best_tail;
    uint8_t best_r61;
    uint8_t used;
} mask_bucket_t;

typedef struct {
    uint64_t sig;
    uint32_t count;
    uint8_t best_tail;
    uint8_t used;
} sig_bucket_t;

typedef struct {
    uint64_t key;
    uint64_t sum_tail;
    uint32_t count;
    uint32_t low8, low12, low16, low20, low24, low32;
    uint8_t best_tail;
    uint8_t used;
} miner_bucket_t;

static const int MINER_FAMILIES = 10;
static const char *miner_family_names[10] = {
    "gh60",
    "gh60+r61_hw",
    "gh60+reg6hw+reg7hw",
    "gh60+late_fold8",
    "gh60+reg6_low8",
    "gh60+reg7_low8",
    "gh60+reg6_high8",
    "gh60+reg7_high8",
    "r61hw+reg_hw+fold8",
    "reg_hw+late_fold8"
};

typedef struct {
    witness_t wit;
    uint8_t used;
} refine_seed_t;

typedef struct {
    uint64_t tested;
    uint64_t d0;
    uint64_t collision;
    uint64_t phase_tested[4];
    uint64_t phase_d0[4];
    uint64_t repairable;
    uint64_t prefix_enums;
    uint64_t seed_inserts;
    uint64_t tail_improvements;
    uint64_t r61_improvements;
    uint64_t joint_improvements;
    int best_tail;
    int best_r61;
    int best_joint_score;
    int best_joint_max;
    int min_d_hw;
    uint32_t min_d60;
    uint32_t min_d_w57, min_d_w58, min_d_w59;
    witness_t best_tail_wit;
    witness_t best_r61_wit;
    witness_t best_joint_wit;
    witness_t first_collision;
} refine_stats_t;

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

static void active_mask(const uint32_t a[8], const uint32_t b[8],
                        uint64_t *lo, uint64_t *hi) {
    uint64_t l = 0, h = 0;
    for (int r = 0; r < 8; r++) {
        uint32_t d = (a[r] ^ b[r]) & gMASK;
        for (int bit = 0; bit < gN; bit++) {
            if ((d >> bit) & 1u) {
                int idx = r * gN + bit;
                if (idx < 64) l |= 1ull << idx;
                else h |= 1ull << (idx - 64);
            }
        }
    }
    *lo = l;
    *hi = h;
}

static uint64_t mix64(uint64_t x) {
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    x ^= x >> 31;
    return x;
}

static uint64_t next_pow2_u64(uint64_t x) {
    uint64_t p = 1;
    while (p < x) p <<= 1;
    return p;
}

static void mask_table_insert(mask_bucket_t *tab, uint64_t cap,
                              uint64_t lo, uint64_t hi,
                              int r61_hw, int tail_hw) {
    uint64_t h = mix64(lo ^ (hi * 0x9e3779b97f4a7c15ULL));
    uint64_t pos = h & (cap - 1u);
    while (tab[pos].used && (tab[pos].lo != lo || tab[pos].hi != hi)) {
        pos = (pos + 1u) & (cap - 1u);
    }
    if (!tab[pos].used) {
        tab[pos].used = 1;
        tab[pos].lo = lo;
        tab[pos].hi = hi;
        tab[pos].count = 0;
        tab[pos].best_tail = 255;
        tab[pos].best_r61 = 255;
    }
    tab[pos].count++;
    if (tail_hw < tab[pos].best_tail) tab[pos].best_tail = (uint8_t)tail_hw;
    if (r61_hw < tab[pos].best_r61) tab[pos].best_r61 = (uint8_t)r61_hw;
}

static void sig_table_insert(sig_bucket_t *tab, uint64_t cap,
                             uint64_t sig, int tail_hw) {
    uint64_t pos = mix64(sig) & (cap - 1u);
    while (tab[pos].used && tab[pos].sig != sig) {
        pos = (pos + 1u) & (cap - 1u);
    }
    if (!tab[pos].used) {
        tab[pos].used = 1;
        tab[pos].sig = sig;
        tab[pos].count = 0;
        tab[pos].best_tail = 255;
    }
    tab[pos].count++;
    if (tail_hw < tab[pos].best_tail) tab[pos].best_tail = (uint8_t)tail_hw;
}

static void miner_insert(miner_bucket_t *tab, uint64_t cap, uint64_t key, int tail_hw) {
    uint64_t pos = mix64(key) & (cap - 1u);
    while (tab[pos].used && tab[pos].key != key) {
        pos = (pos + 1u) & (cap - 1u);
    }
    if (!tab[pos].used) {
        tab[pos].used = 1;
        tab[pos].key = key;
        tab[pos].sum_tail = 0;
        tab[pos].count = 0;
        tab[pos].low8 = tab[pos].low12 = tab[pos].low16 = 0;
        tab[pos].low20 = tab[pos].low24 = tab[pos].low32 = 0;
        tab[pos].best_tail = 255;
    }
    tab[pos].count++;
    tab[pos].sum_tail += (uint64_t)tail_hw;
    if (tail_hw <= 8) tab[pos].low8++;
    if (tail_hw <= 12) tab[pos].low12++;
    if (tail_hw <= 16) tab[pos].low16++;
    if (tail_hw <= 20) tab[pos].low20++;
    if (tail_hw <= 24) tab[pos].low24++;
    if (tail_hw <= 32) tab[pos].low32++;
    if (tail_hw < tab[pos].best_tail) tab[pos].best_tail = (uint8_t)tail_hw;
}

static inline uint64_t miner_key(int family, uint64_t data) {
    return ((uint64_t)family << 56) | (data & 0x00ffffffffffffffULL);
}

static uint32_t miner_low_count(const miner_bucket_t *b, int threshold) {
    if (threshold <= 8) return b->low8;
    if (threshold <= 12) return b->low12;
    if (threshold <= 16) return b->low16;
    if (threshold <= 20) return b->low20;
    if (threshold <= 24) return b->low24;
    return b->low32;
}

static void fold_carry_diff(uint64_t *sig, uint32_t a1, uint32_t b1,
                            uint32_t a2, uint32_t b2, int tag) {
    uint32_t c1 = 0, c2 = 0;
    for (int bit = 0; bit < gN; bit++) {
        uint32_t s1b = ((a1 >> bit) & 1u) + ((b1 >> bit) & 1u) + c1;
        uint32_t s2b = ((a2 >> bit) & 1u) + ((b2 >> bit) & 1u) + c2;
        c1 = s1b >> 1;
        c2 = s2b >> 1;
        uint64_t token = (uint64_t)(c1 ^ c2) | ((uint64_t)tag << 1) | ((uint64_t)bit << 9);
        *sig ^= token;
        *sig *= 1099511628211ULL;
    }
}

static void sha_round_pair_sig(uint32_t p1[8], uint32_t p2[8], int round_idx,
                               uint32_t W1, uint32_t W2, uint64_t *sig) {
    uint32_t sig1_1 = S1(p1[4]), sig1_2 = S1(p2[4]);
    uint32_t ch1 = ch(p1[4], p1[5], p1[6]);
    uint32_t ch2 = ch(p2[4], p2[5], p2[6]);
    uint32_t sig0_1 = S0(p1[0]), sig0_2 = S0(p2[0]);
    uint32_t maj1 = maj(p1[0], p1[1], p1[2]);
    uint32_t maj2 = maj(p2[0], p2[1], p2[2]);

    uint32_t t10_1 = (p1[7] + sig1_1) & gMASK;
    uint32_t t10_2 = (p2[7] + sig1_2) & gMASK;
    fold_carry_diff(sig, p1[7], sig1_1, p2[7], sig1_2, (round_idx - 60) * 7 + 0);

    uint32_t t11_1 = (t10_1 + ch1) & gMASK;
    uint32_t t11_2 = (t10_2 + ch2) & gMASK;
    fold_carry_diff(sig, t10_1, ch1, t10_2, ch2, (round_idx - 60) * 7 + 1);

    uint32_t t12_1 = (t11_1 + KN[round_idx]) & gMASK;
    uint32_t t12_2 = (t11_2 + KN[round_idx]) & gMASK;
    fold_carry_diff(sig, t11_1, KN[round_idx], t11_2, KN[round_idx], (round_idx - 60) * 7 + 2);

    uint32_t T1_1 = (t12_1 + W1) & gMASK;
    uint32_t T1_2 = (t12_2 + W2) & gMASK;
    fold_carry_diff(sig, t12_1, W1, t12_2, W2, (round_idx - 60) * 7 + 3);

    uint32_t T2_1 = (sig0_1 + maj1) & gMASK;
    uint32_t T2_2 = (sig0_2 + maj2) & gMASK;
    fold_carry_diff(sig, sig0_1, maj1, sig0_2, maj2, (round_idx - 60) * 7 + 4);

    fold_carry_diff(sig, p1[3], T1_1, p2[3], T1_2, (round_idx - 60) * 7 + 5);
    fold_carry_diff(sig, T1_1, T2_1, T1_2, T2_2, (round_idx - 60) * 7 + 6);

    p1[7] = p1[6]; p1[6] = p1[5]; p1[5] = p1[4]; p1[4] = (p1[3] + T1_1) & gMASK;
    p1[3] = p1[2]; p1[2] = p1[1]; p1[1] = p1[0]; p1[0] = (T1_1 + T2_1) & gMASK;
    p2[7] = p2[6]; p2[6] = p2[5]; p2[5] = p2[4]; p2[4] = (p2[3] + T1_2) & gMASK;
    p2[3] = p2[2]; p2[2] = p2[1]; p2[1] = p2[0]; p2[0] = (T1_2 + T2_2) & gMASK;
}

static void copy_state(uint32_t dst[8], const uint32_t src[8]) {
    memcpy(dst, src, 8 * sizeof(uint32_t));
}

static int find_candidate(uint32_t *out_m0, int *out_mode,
                          uint32_t M1[16], uint32_t M2[16],
                          uint32_t st1[8], uint32_t st2[8],
                          uint32_t W1[64], uint32_t W2[64]) {
    uint64_t limit = (uint64_t)gMASK + 1u;
    if (out_mode) *out_mode = 0;
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
            if (out_mode) *out_mode = 0;
            return 1;
        }
    }

    uint64_t random_limit = 1ull << 24;
    for (uint64_t trial = 0; trial < random_limit; trial++) {
        for (int i = 0; i < 16; i++) {
            uint64_t x = mix64(trial ^ (0x9e3779b97f4a7c15ULL * (uint64_t)(i + 1)));
            M1[i] = (uint32_t)x & gMASK;
        }
        memcpy(M2, M1, 16 * sizeof(uint32_t));
        M2[0] ^= gMSB;
        M2[9] ^= gMSB;

        precompute(M1, st1, W1);
        precompute(M2, st2, W2);
        if (st1[0] == st2[0]) {
            *out_m0 = M1[0];
            if (out_mode) *out_mode = 1;
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

    uint64_t tail_carry_sig = 14695981039346656037ULL;

    sha_round_pair_sig(s1v, s2v, 60, W60_1, W60_2, &tail_carry_sig);
    uint32_t gh60_key = (((s1v[6] ^ s2v[6]) & gMASK) << gN) | ((s1v[7] ^ s2v[7]) & gMASK);

    sha_round_pair_sig(s1v, s2v, 61, W61_1, W61_2, &tail_carry_sig);
    int r61_hw = state_diff_hw(s1v, s2v);
    uint64_t r61_mask_lo = 0, r61_mask_hi = 0;
    active_mask(s1v, s2v, &r61_mask_lo, &r61_mask_hi);

    sha_round_pair_sig(s1v, s2v, 62, W62_1, W62_2, &tail_carry_sig);
    sha_round_pair_sig(s1v, s2v, 63, W63_1, W63_2, &tail_carry_sig);

    int tail_hw = state_diff_hw(s1v, s2v);
    if (wit) {
        wit->w57 = w57; wit->w58 = w58; wit->w59 = w59;
        wit->w2_57 = w2_57; wit->w2_58 = w2_58; wit->w2_59 = w2_59;
        wit->d60 = d60; wit->gh60_key = gh60_key;
        wit->r61_mask_lo = r61_mask_lo; wit->r61_mask_hi = r61_mask_hi;
        wit->tail_carry_sig = tail_carry_sig;
        wit->r61_hw = r61_hw; wit->tail_hw = tail_hw;
    }
    return tail_hw;
}

static int eval_repaired_tail(const uint32_t init1[8], const uint32_t init2[8],
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

    uint32_t repaired_W60_2 = req_w2_60;
    uint32_t W61_1 = (s1(w59) + Wpre1[54] + s0(Wpre1[46]) + Wpre1[45]) & gMASK;
    uint32_t W61_2 = (s1(w2_59) + Wpre2[54] + s0(Wpre2[46]) + Wpre2[45]) & gMASK;
    uint32_t W62_1 = (s1(W60_1) + Wpre1[55] + s0(Wpre1[47]) + Wpre1[46]) & gMASK;
    uint32_t W62_2 = (s1(repaired_W60_2) + Wpre2[55] + s0(Wpre2[47]) + Wpre2[46]) & gMASK;
    uint32_t W63_1 = (s1(W61_1) + Wpre1[56] + s0(Wpre1[48]) + Wpre1[47]) & gMASK;
    uint32_t W63_2 = (s1(W61_2) + Wpre2[56] + s0(Wpre2[48]) + Wpre2[47]) & gMASK;

    uint64_t tail_carry_sig = 14695981039346656037ULL;

    sha_round_pair_sig(s1v, s2v, 60, W60_1, repaired_W60_2, &tail_carry_sig);
    uint32_t gh60_key = (((s1v[6] ^ s2v[6]) & gMASK) << gN) | ((s1v[7] ^ s2v[7]) & gMASK);

    sha_round_pair_sig(s1v, s2v, 61, W61_1, W61_2, &tail_carry_sig);
    int r61_hw = state_diff_hw(s1v, s2v);
    uint64_t r61_mask_lo = 0, r61_mask_hi = 0;
    active_mask(s1v, s2v, &r61_mask_lo, &r61_mask_hi);

    sha_round_pair_sig(s1v, s2v, 62, W62_1, W62_2, &tail_carry_sig);
    sha_round_pair_sig(s1v, s2v, 63, W63_1, W63_2, &tail_carry_sig);

    int tail_hw = state_diff_hw(s1v, s2v);
    if (wit) {
        wit->w57 = w57; wit->w58 = w58; wit->w59 = w59;
        wit->w2_57 = w2_57; wit->w2_58 = w2_58; wit->w2_59 = w2_59;
        wit->d60 = d60; wit->gh60_key = gh60_key;
        wit->r61_mask_lo = r61_mask_lo; wit->r61_mask_hi = r61_mask_hi;
        wit->tail_carry_sig = tail_carry_sig;
        wit->r61_hw = r61_hw; wit->tail_hw = tail_hw;
    }
    return tail_hw;
}

static int refine_seed_cmp(const void *a, const void *b) {
    const refine_seed_t *sa = (const refine_seed_t *)a;
    const refine_seed_t *sb = (const refine_seed_t *)b;
    if (sa->wit.tail_hw != sb->wit.tail_hw) return sa->wit.tail_hw - sb->wit.tail_hw;
    if (sa->wit.r61_hw != sb->wit.r61_hw) return sa->wit.r61_hw - sb->wit.r61_hw;
    if (sa->wit.w57 != sb->wit.w57) return (sa->wit.w57 < sb->wit.w57) ? -1 : 1;
    if (sa->wit.w58 != sb->wit.w58) return (sa->wit.w58 < sb->wit.w58) ? -1 : 1;
    if (sa->wit.w59 != sb->wit.w59) return (sa->wit.w59 < sb->wit.w59) ? -1 : 1;
    return 0;
}

static int refine_seed_r61_cmp(const void *a, const void *b) {
    const refine_seed_t *sa = (const refine_seed_t *)a;
    const refine_seed_t *sb = (const refine_seed_t *)b;
    if (sa->wit.r61_hw != sb->wit.r61_hw) return sa->wit.r61_hw - sb->wit.r61_hw;
    if (sa->wit.tail_hw != sb->wit.tail_hw) return sa->wit.tail_hw - sb->wit.tail_hw;
    if (sa->wit.w57 != sb->wit.w57) return (sa->wit.w57 < sb->wit.w57) ? -1 : 1;
    if (sa->wit.w58 != sb->wit.w58) return (sa->wit.w58 < sb->wit.w58) ? -1 : 1;
    if (sa->wit.w59 != sb->wit.w59) return (sa->wit.w59 < sb->wit.w59) ? -1 : 1;
    return 0;
}

static int witness_joint_score(const witness_t *wit) {
    if (wit->tail_hw < 0 || wit->r61_hw < 0) return 999;
    return wit->tail_hw + wit->r61_hw;
}

static int witness_joint_max(const witness_t *wit) {
    if (wit->tail_hw < 0 || wit->r61_hw < 0) return 999;
    return wit->tail_hw > wit->r61_hw ? wit->tail_hw : wit->r61_hw;
}

static int refine_seed_joint_cmp(const void *a, const void *b) {
    const refine_seed_t *sa = (const refine_seed_t *)a;
    const refine_seed_t *sb = (const refine_seed_t *)b;
    int score_a = witness_joint_score(&sa->wit);
    int score_b = witness_joint_score(&sb->wit);
    int max_a = witness_joint_max(&sa->wit);
    int max_b = witness_joint_max(&sb->wit);
    if (score_a != score_b) return score_a - score_b;
    if (max_a != max_b) return max_a - max_b;
    if (sa->wit.tail_hw != sb->wit.tail_hw) return sa->wit.tail_hw - sb->wit.tail_hw;
    if (sa->wit.r61_hw != sb->wit.r61_hw) return sa->wit.r61_hw - sb->wit.r61_hw;
    if (sa->wit.w57 != sb->wit.w57) return (sa->wit.w57 < sb->wit.w57) ? -1 : 1;
    if (sa->wit.w58 != sb->wit.w58) return (sa->wit.w58 < sb->wit.w58) ? -1 : 1;
    if (sa->wit.w59 != sb->wit.w59) return (sa->wit.w59 < sb->wit.w59) ? -1 : 1;
    return 0;
}

static int same_witness_words(const witness_t *a, const witness_t *b) {
    return a->w57 == b->w57 && a->w58 == b->w58 && a->w59 == b->w59;
}

static int witness_better_joint(const witness_t *wit, int best_score,
                                int best_max, const witness_t *best_wit) {
    int score = witness_joint_score(wit);
    int max_hw = witness_joint_max(wit);
    if (score != best_score) return score < best_score;
    if (max_hw != best_max) return max_hw < best_max;
    if (wit->tail_hw != best_wit->tail_hw) return wit->tail_hw < best_wit->tail_hw;
    if (wit->r61_hw != best_wit->r61_hw) return wit->r61_hw < best_wit->r61_hw;
    if (wit->w57 != best_wit->w57) return wit->w57 < best_wit->w57;
    if (wit->w58 != best_wit->w58) return wit->w58 < best_wit->w58;
    if (wit->w59 != best_wit->w59) return wit->w59 < best_wit->w59;
    return 0;
}

static void refine_stats_init_best(refine_stats_t *stats,
                                   const witness_t *scan_best_tail,
                                   const witness_t *scan_best_r61,
                                   const witness_t *scan_best_joint) {
    stats->best_tail = scan_best_tail ? scan_best_tail->tail_hw : 999;
    stats->best_r61 = scan_best_r61 ? scan_best_r61->r61_hw : 999;
    stats->best_joint_score = scan_best_joint ? witness_joint_score(scan_best_joint) : 999;
    stats->best_joint_max = scan_best_joint ? witness_joint_max(scan_best_joint) : 999;
    stats->min_d_hw = 999;
    if (scan_best_tail) stats->best_tail_wit = *scan_best_tail;
    if (scan_best_r61) stats->best_r61_wit = *scan_best_r61;
    if (scan_best_joint) stats->best_joint_wit = *scan_best_joint;
}

static void refine_stats_consider_joint(refine_stats_t *stats, const witness_t *wit) {
    if (witness_better_joint(wit, stats->best_joint_score,
                             stats->best_joint_max, &stats->best_joint_wit)) {
        stats->best_joint_score = witness_joint_score(wit);
        stats->best_joint_max = witness_joint_max(wit);
        stats->best_joint_wit = *wit;
        stats->joint_improvements++;
    }
}

static int refine_seed_insert_ordered(refine_seed_t *seeds, int *seed_count, int seed_cap,
                                      const witness_t *wit, int rank_mode) {
    if (!seeds || seed_cap <= 0 || wit->tail_hw < 0) return 0;
    for (int i = 0; i < *seed_count; i++) {
        if (same_witness_words(&seeds[i].wit, wit)) return 0;
    }
    int (*cmp)(const void *, const void *) = refine_seed_cmp;
    if (rank_mode == 1) cmp = refine_seed_r61_cmp;
    if (rank_mode == 2) cmp = refine_seed_joint_cmp;
    if (*seed_count < seed_cap) {
        seeds[*seed_count].wit = *wit;
        seeds[*seed_count].used = 1;
        (*seed_count)++;
        qsort(seeds, (size_t)*seed_count, sizeof(refine_seed_t), cmp);
        return 1;
    }
    refine_seed_t *worst = &seeds[*seed_count - 1];
    refine_seed_t candidate = { .wit = *wit, .used = 1 };
    if (cmp(&candidate, worst) >= 0) return 0;
    worst->wit = *wit;
    worst->used = 1;
    qsort(seeds, (size_t)*seed_count, sizeof(refine_seed_t), cmp);
    return 1;
}

static int refine_seed_insert(refine_seed_t *seeds, int *seed_count, int seed_cap,
                              const witness_t *wit) {
    return refine_seed_insert_ordered(seeds, seed_count, seed_cap, wit, 0);
}

static int refine_seed_insert_r61(refine_seed_t *seeds, int *seed_count, int seed_cap,
                                  const witness_t *wit) {
    return refine_seed_insert_ordered(seeds, seed_count, seed_cap, wit, 1);
}

static void flip_local_bit(uint32_t words[3], int idx) {
    int word = idx / gN;
    int bit = idx % gN;
    words[word] = (words[word] ^ (1u << bit)) & gMASK;
}

static int refine_test_candidate(const uint32_t init1[8], const uint32_t init2[8],
                                 const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                                 uint32_t w57, uint32_t w58, uint32_t w59,
                                 int phase, uint64_t budget,
                                 refine_seed_t *seeds, int *seed_count, int seed_cap,
                                 refine_stats_t *stats) {
    if (stats->tested >= budget) return -1;

    uint32_t d60 = 0;
    witness_t wit;
    int tail_hw = eval_tail(init1, init2, Wpre1, Wpre2, w57, w58, w59, &wit, &d60);
    stats->tested++;
    if (phase >= 0 && phase < 4) stats->phase_tested[phase]++;

    int dhw = hw(d60);
    if (dhw < stats->min_d_hw) {
        stats->min_d_hw = dhw;
        stats->min_d60 = d60;
        stats->min_d_w57 = w57;
        stats->min_d_w58 = w58;
        stats->min_d_w59 = w59;
    }

    if (d60 != 0) return dhw;
    stats->d0++;
    if (phase >= 0 && phase < 4) stats->phase_d0[phase]++;

    if (refine_seed_insert(seeds, seed_count, seed_cap, &wit)) stats->seed_inserts++;
    if (tail_hw == 0) {
        if (stats->collision == 0) stats->first_collision = wit;
        stats->collision++;
    }
    if (tail_hw >= 0 && tail_hw < stats->best_tail) {
        stats->best_tail = tail_hw;
        stats->best_tail_wit = wit;
        stats->tail_improvements++;
    }
    if (wit.r61_hw < stats->best_r61) {
        stats->best_r61 = wit.r61_hw;
        stats->best_r61_wit = wit;
        stats->r61_improvements++;
    }
    refine_stats_consider_joint(stats, &wit);
    return dhw;
}

static void repair_refine_consider_wit(const witness_t *wit, int phase,
                                       refine_seed_t *seeds, int *seed_count, int seed_cap,
                                       int seed_rank_mode,
                                       refine_seed_t *r61_seeds, int *r61_seed_count,
                                       refine_stats_t *stats) {
    stats->repairable++;
    if (phase >= 0 && phase < 4) stats->phase_d0[phase]++;
    if (seeds && refine_seed_insert_ordered(seeds, seed_count, seed_cap, wit, seed_rank_mode)) {
        stats->seed_inserts++;
    }
    if (r61_seeds) {
        refine_seed_insert_r61(r61_seeds, r61_seed_count, seed_cap, wit);
    }
    if (wit->tail_hw == 0) {
        if (stats->collision == 0) stats->first_collision = *wit;
        stats->collision++;
    }
    if (wit->tail_hw < stats->best_tail) {
        stats->best_tail = wit->tail_hw;
        stats->best_tail_wit = *wit;
        stats->tail_improvements++;
    }
    if (wit->r61_hw < stats->best_r61) {
        stats->best_r61 = wit->r61_hw;
        stats->best_r61_wit = *wit;
        stats->r61_improvements++;
    }
    refine_stats_consider_joint(stats, wit);
}

static int repair_refine_test_candidate(const uint32_t init1[8], const uint32_t init2[8],
                                        const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                                        uint32_t w57, uint32_t w58, uint32_t w59,
                                        int repair_hw_limit, int phase, uint64_t budget,
                                        refine_seed_t *seeds, int *seed_count, int seed_cap,
                                        int seed_rank_mode,
                                        refine_seed_t *r61_seeds, int *r61_seed_count,
                                        refine_stats_t *stats) {
    if (stats->tested >= budget) return -1;

    uint32_t d60 = 0;
    witness_t exact_wit;
    int exact_tail = eval_tail(init1, init2, Wpre1, Wpre2, w57, w58, w59, &exact_wit, &d60);
    stats->tested++;
    if (phase >= 0 && phase < 4) stats->phase_tested[phase]++;

    int dhw = hw(d60);
    if (dhw < stats->min_d_hw) {
        stats->min_d_hw = dhw;
        stats->min_d60 = d60;
        stats->min_d_w57 = w57;
        stats->min_d_w58 = w58;
        stats->min_d_w59 = w59;
    }

    if (d60 == 0) {
        stats->d0++;
        if (exact_tail >= 0) {
            repair_refine_consider_wit(&exact_wit, phase, seeds, seed_count, seed_cap,
                                       seed_rank_mode,
                                       r61_seeds, r61_seed_count, stats);
        }
        return dhw;
    }
    if (dhw > repair_hw_limit) return dhw;

    uint32_t repaired_d60 = 0;
    witness_t repair_wit;
    eval_repaired_tail(init1, init2, Wpre1, Wpre2, w57, w58, w59,
                       &repair_wit, &repaired_d60);
    repair_refine_consider_wit(&repair_wit, phase, seeds, seed_count, seed_cap,
                               seed_rank_mode,
                               r61_seeds, r61_seed_count, stats);
    return dhw;
}

static void mutate_random_words(const uint32_t base[3], uint64_t ctr,
                                uint32_t *w57, uint32_t *w58, uint32_t *w59) {
    uint32_t words[3] = { base[0], base[1], base[2] };
    uint64_t x = mix64(ctr ^ ((uint64_t)base[0] << 32) ^
                       ((uint64_t)base[1] << 16) ^ (uint64_t)base[2]);
    int flips = 1 + (int)(x & 3u);
    int bits = 3 * gN;
    for (int i = 0; i < flips; i++) {
        x = mix64(x + 0x9e3779b97f4a7c15ULL + (uint64_t)i);
        flip_local_bit(words, (int)(x % (uint64_t)bits));
    }
    *w57 = words[0] & gMASK;
    *w58 = words[1] & gMASK;
    *w59 = words[2] & gMASK;
}

static void refine_scan_prefix(const uint32_t init1[8], const uint32_t init2[8],
                               const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                               uint32_t w57, uint32_t w58,
                               uint64_t budget,
                               refine_seed_t *seeds, int *seed_count, int seed_cap,
                               refine_stats_t *stats) {
    if (stats->tested >= budget) return;
    stats->prefix_enums++;
    uint64_t word_space = 1ull << gN;
    for (uint64_t w59 = 0; w59 < word_space && stats->tested < budget; w59++) {
        refine_test_candidate(init1, init2, Wpre1, Wpre2, w57, w58, (uint32_t)w59,
                              3, budget, seeds, seed_count, seed_cap, stats);
    }
}

static void repair_refine_scan_prefix(const uint32_t init1[8], const uint32_t init2[8],
                                      const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                                      uint32_t w57, uint32_t w58,
                                      int repair_hw_limit, uint64_t budget,
                                      refine_seed_t *seeds, int *seed_count, int seed_cap,
                                      int seed_rank_mode,
                                      refine_seed_t *r61_seeds, int *r61_seed_count,
                                      refine_stats_t *stats) {
    if (stats->tested >= budget) return;
    stats->prefix_enums++;
    uint64_t word_space = 1ull << gN;
    for (uint64_t w59 = 0; w59 < word_space && stats->tested < budget; w59++) {
        repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                     w57, w58, (uint32_t)w59,
                                     repair_hw_limit, 3, budget,
                                     seeds, seed_count, seed_cap,
                                     seed_rank_mode,
                                     r61_seeds, r61_seed_count, stats);
    }
}

static void flip_prefix_bit(uint32_t words[2], int idx) {
    int word = idx / gN;
    int bit = idx % gN;
    words[word] = (words[word] ^ (1u << bit)) & gMASK;
}

static void mutate_random_prefix(const witness_t *seed, uint64_t ctr,
                                 uint32_t *w57, uint32_t *w58) {
    uint32_t words[2] = { seed->w57, seed->w58 };
    uint64_t x = mix64(ctr ^ ((uint64_t)seed->w57 << 32) ^
                       ((uint64_t)seed->w58 << 1));
    int flips = 1 + (int)(x & 3u);
    int bits = 2 * gN;
    for (int i = 0; i < flips; i++) {
        x = mix64(x + 0x517cc1b727220a95ULL + (uint64_t)i);
        flip_prefix_bit(words, (int)(x % (uint64_t)bits));
    }
    *w57 = words[0] & gMASK;
    *w58 = words[1] & gMASK;
}

static void run_refinement(const uint32_t init1[8], const uint32_t init2[8],
                           const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                           refine_seed_t *seeds, int *seed_count, int seed_cap,
                           uint64_t budget, const witness_t *scan_best_tail,
                           const witness_t *scan_best_r61,
                           const witness_t *scan_best_joint,
                           refine_stats_t *stats) {
    memset(stats, 0, sizeof(*stats));
    refine_stats_init_best(stats, scan_best_tail, scan_best_r61, scan_best_joint);
    if (!seeds || *seed_count <= 0 || budget == 0) return;

    int bits = 3 * gN;
    int prefix_bits = 2 * gN;
    int initial_seed_count = *seed_count;
    for (int s = 0; s < initial_seed_count && stats->tested < budget; s++) {
        const witness_t seed = seeds[s].wit;
        refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                           seed.w57, seed.w58, budget,
                           seeds, seed_count, seed_cap, stats);
        for (int b = 0; b < prefix_bits && stats->tested < budget; b++) {
            uint32_t pwords[2] = { seed.w57, seed.w58 };
            flip_prefix_bit(pwords, b);
            refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                               pwords[0], pwords[1], budget,
                               seeds, seed_count, seed_cap, stats);
        }
        for (int b1 = 0; b1 < prefix_bits && stats->tested < budget; b1++) {
            for (int b2 = b1 + 1; b2 < prefix_bits && stats->tested < budget; b2++) {
                uint32_t pwords[2] = { seed.w57, seed.w58 };
                flip_prefix_bit(pwords, b1);
                flip_prefix_bit(pwords, b2);
                refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                                   pwords[0], pwords[1], budget,
                                   seeds, seed_count, seed_cap, stats);
            }
        }
        for (int b = 0; b < bits && stats->tested < budget; b++) {
            uint32_t words[3] = { seed.w57, seed.w58, seed.w59 };
            flip_local_bit(words, b);
            refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                  words[0], words[1], words[2], 0, budget,
                                  seeds, seed_count, seed_cap, stats);
        }
        for (int b1 = 0; b1 < bits && stats->tested < budget; b1++) {
            for (int b2 = b1 + 1; b2 < bits && stats->tested < budget; b2++) {
                uint32_t words[3] = { seed.w57, seed.w58, seed.w59 };
                flip_local_bit(words, b1);
                flip_local_bit(words, b2);
                refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                      words[0], words[1], words[2], 1, budget,
                                      seeds, seed_count, seed_cap, stats);
            }
        }
    }

    uint64_t prefix_ctr = 0;
    while (stats->tested + (1ull << gN) <= budget && *seed_count > 0) {
        uint64_t r = mix64(0xc6a4a7935bd1e995ULL ^ prefix_ctr);
        int s = (int)(r % (uint64_t)*seed_count);
        uint32_t w57, w58;
        mutate_random_prefix(&seeds[s].wit, prefix_ctr, &w57, &w58);
        refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                           w57, w58, budget,
                           seeds, seed_count, seed_cap, stats);
        prefix_ctr++;
    }

    uint64_t ctr = 0;
    uint32_t cur[3] = { seeds[0].wit.w57, seeds[0].wit.w58, seeds[0].wit.w59 };
    int cur_dhw = 0;
    uint64_t since_restart = 0;
    while (stats->tested < budget && *seed_count > 0) {
        uint64_t r = mix64(0xd1b54a32d192ed03ULL ^ ctr);
        if (since_restart == 0 || since_restart >= 4096) {
            int s = (int)(r % (uint64_t)*seed_count);
            cur[0] = seeds[s].wit.w57;
            cur[1] = seeds[s].wit.w58;
            cur[2] = seeds[s].wit.w59;
            cur_dhw = 0;
            since_restart = 1;
        }

        uint32_t w57, w58, w59;
        mutate_random_words(cur, ctr, &w57, &w58, &w59);
        int cand_dhw = refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                             w57, w58, w59, 2, budget,
                                             seeds, seed_count, seed_cap, stats);
        if (cand_dhw >= 0) {
            int delta = cand_dhw - cur_dhw;
            uint64_t coin = mix64(r ^ 0x94d049bb133111ebULL) & 255u;
            uint64_t accept_bar = (delta <= 0) ? 256u : (64u / (uint64_t)(delta + 1));
            if (delta <= 0 || coin < accept_bar) {
                cur[0] = w57;
                cur[1] = w58;
                cur[2] = w59;
                cur_dhw = cand_dhw;
                since_restart = 1;
            } else {
                since_restart++;
            }
        }
        ctr++;
    }
}

static void run_repair_refinement(const uint32_t init1[8], const uint32_t init2[8],
                                  const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                                  refine_seed_t *seeds, int *seed_count, int seed_cap,
                                  int seed_rank_mode,
                                  refine_seed_t *r61_seeds, int *r61_seed_count,
                                  uint64_t budget, int repair_hw_limit,
                                  const witness_t *scan_best_tail,
                                  const witness_t *scan_best_r61,
                                  const witness_t *scan_best_joint,
                                  refine_stats_t *stats) {
    memset(stats, 0, sizeof(*stats));
    refine_stats_init_best(stats, scan_best_tail, scan_best_r61, scan_best_joint);
    if (!seeds || *seed_count <= 0 || budget == 0) return;

    int bits = 3 * gN;
    int prefix_bits = 2 * gN;
    int initial_seed_count = *seed_count;
    for (int s = 0; s < initial_seed_count && stats->tested < budget; s++) {
        const witness_t seed = seeds[s].wit;
        repair_refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                                  seed.w57, seed.w58, repair_hw_limit, budget,
                                  seeds, seed_count, seed_cap,
                                  seed_rank_mode,
                                  r61_seeds, r61_seed_count, stats);
        for (int b = 0; b < prefix_bits && stats->tested < budget; b++) {
            uint32_t pwords[2] = { seed.w57, seed.w58 };
            flip_prefix_bit(pwords, b);
            repair_refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                                      pwords[0], pwords[1], repair_hw_limit, budget,
                                      seeds, seed_count, seed_cap,
                                      seed_rank_mode,
                                      r61_seeds, r61_seed_count, stats);
        }
        for (int b1 = 0; b1 < prefix_bits && stats->tested < budget; b1++) {
            for (int b2 = b1 + 1; b2 < prefix_bits && stats->tested < budget; b2++) {
                uint32_t pwords[2] = { seed.w57, seed.w58 };
                flip_prefix_bit(pwords, b1);
                flip_prefix_bit(pwords, b2);
                repair_refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                                          pwords[0], pwords[1], repair_hw_limit, budget,
                                          seeds, seed_count, seed_cap,
                                          seed_rank_mode,
                                          r61_seeds, r61_seed_count, stats);
            }
        }
        for (int b = 0; b < bits && stats->tested < budget; b++) {
            uint32_t words[3] = { seed.w57, seed.w58, seed.w59 };
            flip_local_bit(words, b);
            repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                         words[0], words[1], words[2],
                                         repair_hw_limit, 0, budget,
                                         seeds, seed_count, seed_cap,
                                         seed_rank_mode,
                                         r61_seeds, r61_seed_count, stats);
        }
        for (int b1 = 0; b1 < bits && stats->tested < budget; b1++) {
            for (int b2 = b1 + 1; b2 < bits && stats->tested < budget; b2++) {
                uint32_t words[3] = { seed.w57, seed.w58, seed.w59 };
                flip_local_bit(words, b1);
                flip_local_bit(words, b2);
                repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                             words[0], words[1], words[2],
                                             repair_hw_limit, 1, budget,
                                             seeds, seed_count, seed_cap,
                                             seed_rank_mode,
                                             r61_seeds, r61_seed_count, stats);
            }
        }
    }

    uint64_t prefix_ctr = 0;
    while (stats->tested + (1ull << gN) <= budget && *seed_count > 0) {
        uint64_t r = mix64(0x91e10da5c79e7b1dULL ^ prefix_ctr);
        int s = (int)(r % (uint64_t)*seed_count);
        uint32_t w57, w58;
        mutate_random_prefix(&seeds[s].wit, prefix_ctr, &w57, &w58);
        repair_refine_scan_prefix(init1, init2, Wpre1, Wpre2,
                                  w57, w58, repair_hw_limit, budget,
                                  seeds, seed_count, seed_cap,
                                  seed_rank_mode,
                                  r61_seeds, r61_seed_count, stats);
        prefix_ctr++;
    }

    uint64_t ctr = 0;
    uint32_t cur[3] = { seeds[0].wit.w57, seeds[0].wit.w58, seeds[0].wit.w59 };
    int cur_dhw = hw(seeds[0].wit.d60);
    uint64_t since_restart = 0;
    while (stats->tested < budget && *seed_count > 0) {
        uint64_t r = mix64(0x6a09e667f3bcc909ULL ^ ctr);
        if (since_restart == 0 || since_restart >= 4096) {
            int s = (int)(r % (uint64_t)*seed_count);
            cur[0] = seeds[s].wit.w57;
            cur[1] = seeds[s].wit.w58;
            cur[2] = seeds[s].wit.w59;
            cur_dhw = hw(seeds[s].wit.d60);
            since_restart = 1;
        }

        uint32_t w57, w58, w59;
        mutate_random_words(cur, ctr, &w57, &w58, &w59);
        int cand_dhw = repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                                    w57, w58, w59,
                                                    repair_hw_limit, 2, budget,
                                                    seeds, seed_count, seed_cap,
                                                    seed_rank_mode,
                                                    r61_seeds, r61_seed_count, stats);
        if (cand_dhw >= 0) {
            int delta = cand_dhw - cur_dhw;
            uint64_t coin = mix64(r ^ 0x94d049bb133111ebULL) & 255u;
            uint64_t accept_bar = (delta <= 0) ? 256u : (64u / (uint64_t)(delta + 1));
            if (delta <= 0 || coin < accept_bar) {
                cur[0] = w57;
                cur[1] = w58;
                cur[2] = w59;
                cur_dhw = cand_dhw;
                since_restart = 1;
            } else {
                since_restart++;
            }
        }
        ctr++;
    }
}

static void run_repair_wordwalk(const uint32_t init1[8], const uint32_t init2[8],
                                const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                                refine_seed_t *seeds, int *seed_count, int seed_cap,
                                int seed_rank_mode,
                                refine_seed_t *r61_seeds, int *r61_seed_count,
                                uint64_t budget, int repair_hw_limit,
                                uint64_t walk_nonce,
                                const witness_t *scan_best_tail,
                                const witness_t *scan_best_r61,
                                const witness_t *scan_best_joint,
                                refine_stats_t *stats) {
    memset(stats, 0, sizeof(*stats));
    refine_stats_init_best(stats, scan_best_tail, scan_best_r61, scan_best_joint);
    if (!seeds || *seed_count <= 0 || budget == 0) return;

    int bits = 3 * gN;
    int initial_seed_count = *seed_count;
    for (int s = 0; s < initial_seed_count && stats->tested < budget; s++) {
        const witness_t seed = seeds[s].wit;
        repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                     seed.w57, seed.w58, seed.w59,
                                     repair_hw_limit, 0, budget,
                                     seeds, seed_count, seed_cap,
                                     seed_rank_mode,
                                     r61_seeds, r61_seed_count, stats);
        for (int b = 0; b < bits && stats->tested < budget; b++) {
            uint32_t words[3] = { seed.w57, seed.w58, seed.w59 };
            flip_local_bit(words, b);
            repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                         words[0], words[1], words[2],
                                         repair_hw_limit, 0, budget,
                                         seeds, seed_count, seed_cap,
                                         seed_rank_mode,
                                         r61_seeds, r61_seed_count, stats);
        }
        for (int b1 = 0; b1 < bits && stats->tested < budget; b1++) {
            for (int b2 = b1 + 1; b2 < bits && stats->tested < budget; b2++) {
                uint32_t words[3] = { seed.w57, seed.w58, seed.w59 };
                flip_local_bit(words, b1);
                flip_local_bit(words, b2);
                repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                             words[0], words[1], words[2],
                                             repair_hw_limit, 1, budget,
                                             seeds, seed_count, seed_cap,
                                             seed_rank_mode,
                                             r61_seeds, r61_seed_count, stats);
            }
        }
    }

    uint64_t ctr = 0;
    uint32_t cur[3] = { seeds[0].wit.w57, seeds[0].wit.w58, seeds[0].wit.w59 };
    int cur_dhw = hw(seeds[0].wit.d60);
    uint64_t since_restart = 0;
    while (stats->tested < budget && *seed_count > 0) {
        uint64_t walk_ctr = ctr ^ (walk_nonce * 0x9e3779b97f4a7c15ULL);
        uint64_t r = mix64(0x9e3779b97f4a7c15ULL ^ walk_ctr);
        if (since_restart == 0 || since_restart >= 4096) {
            int s = (int)(r % (uint64_t)*seed_count);
            cur[0] = seeds[s].wit.w57;
            cur[1] = seeds[s].wit.w58;
            cur[2] = seeds[s].wit.w59;
            cur_dhw = hw(seeds[s].wit.d60);
            since_restart = 1;
        }

        uint32_t w57, w58, w59;
        mutate_random_words(cur, walk_ctr, &w57, &w58, &w59);
        int cand_dhw = repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                                    w57, w58, w59,
                                                    repair_hw_limit, 2, budget,
                                                    seeds, seed_count, seed_cap,
                                                    seed_rank_mode,
                                                    r61_seeds, r61_seed_count, stats);
        if (cand_dhw >= 0) {
            int delta = cand_dhw - cur_dhw;
            uint64_t coin = mix64(r ^ 0xd1b54a32d192ed03ULL) & 255u;
            uint64_t accept_bar = (delta <= 0) ? 256u : (64u / (uint64_t)(delta + 1));
            if (delta <= 0 || coin < accept_bar) {
                cur[0] = w57;
                cur[1] = w58;
                cur[2] = w59;
                cur_dhw = cand_dhw;
                since_restart = 1;
            } else {
                since_restart++;
            }
        }
        ctr++;
    }
}

static void enumerate_repair_word_ball(const uint32_t init1[8], const uint32_t init2[8],
                                       const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                                       uint32_t words[3], int bits, int start_bit,
                                       int remaining, int repair_hw_limit,
                                       int phase, uint64_t budget,
                                       refine_seed_t *seeds, int *seed_count, int seed_cap,
                                       int seed_rank_mode,
                                       refine_seed_t *r61_seeds, int *r61_seed_count,
                                       refine_stats_t *stats) {
    if (stats->tested >= budget) return;
    if (remaining == 0) {
        repair_refine_test_candidate(init1, init2, Wpre1, Wpre2,
                                     words[0], words[1], words[2],
                                     repair_hw_limit, phase, budget,
                                     seeds, seed_count, seed_cap,
                                     seed_rank_mode,
                                     r61_seeds, r61_seed_count, stats);
        return;
    }

    for (int bit = start_bit; bit <= bits - remaining && stats->tested < budget; bit++) {
        flip_local_bit(words, bit);
        enumerate_repair_word_ball(init1, init2, Wpre1, Wpre2,
                                   words, bits, bit + 1, remaining - 1,
                                   repair_hw_limit, phase, budget,
                                   seeds, seed_count, seed_cap,
                                   seed_rank_mode,
                                   r61_seeds, r61_seed_count, stats);
        flip_local_bit(words, bit);
    }
}

static void run_repair_wordball(const uint32_t init1[8], const uint32_t init2[8],
                                const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                                refine_seed_t *seeds, int *seed_count, int seed_cap,
                                int seed_rank_mode,
                                refine_seed_t *r61_seeds, int *r61_seed_count,
                                uint64_t budget, int repair_hw_limit,
                                uint64_t max_radius,
                                const witness_t *scan_best_tail,
                                const witness_t *scan_best_r61,
                                const witness_t *scan_best_joint,
                                refine_stats_t *stats) {
    memset(stats, 0, sizeof(*stats));
    refine_stats_init_best(stats, scan_best_tail, scan_best_r61, scan_best_joint);
    if (!seeds || *seed_count <= 0 || budget == 0) return;

    int bits = 3 * gN;
    if (max_radius > (uint64_t)bits) max_radius = (uint64_t)bits;
    int initial_seed_count = *seed_count;
    for (int s = 0; s < initial_seed_count && stats->tested < budget; s++) {
        const witness_t seed = seeds[s].wit;
        for (uint64_t radius = 0; radius <= max_radius && stats->tested < budget; radius++) {
            uint32_t words[3] = { seed.w57, seed.w58, seed.w59 };
            int phase = radius <= 1 ? 0 : (radius == 2 ? 1 : 2);
            enumerate_repair_word_ball(init1, init2, Wpre1, Wpre2,
                                       words, bits, 0, (int)radius,
                                       repair_hw_limit, phase, budget,
                                       seeds, seed_count, seed_cap,
                                       seed_rank_mode,
                                       r61_seeds, r61_seed_count, stats);
        }
    }
}

static int parse_seed_arg(const char *arg, uint32_t *w57, uint32_t *w58, uint32_t *w59) {
    char *end = NULL;
    unsigned long v57 = strtoul(arg, &end, 0);
    if (!end || *end != ',') return 0;
    unsigned long v58 = strtoul(end + 1, &end, 0);
    if (!end || *end != ',') return 0;
    unsigned long v59 = strtoul(end + 1, &end, 0);
    if (!end || *end != '\0') return 0;
    *w57 = (uint32_t)v57 & gMASK;
    *w58 = (uint32_t)v58 & gMASK;
    *w59 = (uint32_t)v59 & gMASK;
    return 1;
}

static int run_repair_seed_mode(int N, uint64_t refine_budget, int refine_seed_cap,
                                int repair_hw_limit, int argc, char **argv,
                                int seed_arg_start, int seed_mode,
                                uint64_t mode_param,
                                const uint32_t init1[8], const uint32_t init2[8],
                                const uint32_t Wpre1[64], const uint32_t Wpre2[64]) {
    refine_seed_t *repair_seeds = calloc((size_t)refine_seed_cap, sizeof(refine_seed_t));
    refine_seed_t *repair_r61_seeds = calloc((size_t)refine_seed_cap, sizeof(refine_seed_t));
    if (!repair_seeds || !repair_r61_seeds) {
        fprintf(stderr, "Repair seed allocation failed.\n");
        free(repair_seeds);
        free(repair_r61_seeds);
        return 1;
    }

    int repair_seed_count = 0;
    int repair_r61_seed_count = 0;
    int seed_inputs = 0;
    int seed_parse_errors = 0;
    int seed_best_tail = 999;
    int seed_best_r61 = 999;
    int seed_best_joint_score = 999;
    int seed_best_joint_max = 999;
    witness_t seed_best_tail_wit = {0};
    witness_t seed_best_r61_wit = {0};
    witness_t seed_best_joint_wit = {0};

    const char *seed_mode_name = seed_mode == 3 ? "repair_seed_joint_walk" :
                                 (seed_mode == 2 ? "repair_seed_ball" :
                                  (seed_mode == 1 ? "repair_seed_walk" : "repair_seed"));
    int primary_seed_rank = seed_mode == 3 ? 2 : 0;
    printf("free_word_mitm_reducedn %s\n", seed_mode_name);
    printf("N=%d mask=0x%x msb=0x%x\n", N, gMASK, gMSB);
    printf("repair_d60_hw_limit=%d seed_cap=%d budget=%" PRIu64
           " seed_mode=%d mode_param=%" PRIu64 "\n",
           repair_hw_limit, refine_seed_cap, refine_budget, seed_mode, mode_param);

    for (int i = seed_arg_start; i < argc; i++) {
        uint32_t w57 = 0, w58 = 0, w59 = 0;
        if (!parse_seed_arg(argv[i], &w57, &w58, &w59)) {
            fprintf(stderr, "Bad repair seed '%s'; expected W57,W58,W59.\n", argv[i]);
            seed_parse_errors++;
            continue;
        }

        uint32_t d60 = 0;
        witness_t wit;
        eval_repaired_tail(init1, init2, Wpre1, Wpre2, w57, w58, w59, &wit, &d60);
        seed_inputs++;
        if (wit.tail_hw < seed_best_tail) {
            seed_best_tail = wit.tail_hw;
            seed_best_tail_wit = wit;
        }
        if (wit.r61_hw < seed_best_r61) {
            seed_best_r61 = wit.r61_hw;
            seed_best_r61_wit = wit;
        }
        if (witness_better_joint(&wit, seed_best_joint_score,
                                 seed_best_joint_max, &seed_best_joint_wit)) {
            seed_best_joint_score = witness_joint_score(&wit);
            seed_best_joint_max = witness_joint_max(&wit);
            seed_best_joint_wit = wit;
        }
        refine_seed_insert_ordered(repair_seeds, &repair_seed_count, refine_seed_cap,
                                   &wit, primary_seed_rank);
        refine_seed_insert_r61(repair_r61_seeds, &repair_r61_seed_count, refine_seed_cap, &wit);
        printf("seed[%02d] repaired_tail=%d r61=%d d60=0x%x d60_hw=%d gh60=0x%x "
               "W1=0x%x,0x%x,0x%x W2=0x%x,0x%x,0x%x\n",
               seed_inputs - 1, wit.tail_hw, wit.r61_hw, wit.d60, hw(wit.d60),
               wit.gh60_key, wit.w57, wit.w58, wit.w59,
               wit.w2_57, wit.w2_58, wit.w2_59);
    }

    if (seed_parse_errors || seed_inputs == 0) {
        free(repair_seeds);
        free(repair_r61_seeds);
        return seed_inputs == 0 ? 2 : 1;
    }

    refine_stats_t stats;
    memset(&stats, 0, sizeof(stats));
    clock_t tr0 = clock();
    if (seed_mode == 2) {
        run_repair_wordball(init1, init2, Wpre1, Wpre2,
                            repair_seeds, &repair_seed_count, refine_seed_cap,
                            primary_seed_rank,
                            repair_r61_seeds, &repair_r61_seed_count,
                            refine_budget, repair_hw_limit, mode_param,
                            &seed_best_tail_wit, &seed_best_r61_wit,
                            &seed_best_joint_wit,
                            &stats);
    } else if (seed_mode == 1 || seed_mode == 3) {
        run_repair_wordwalk(init1, init2, Wpre1, Wpre2,
                            repair_seeds, &repair_seed_count, refine_seed_cap,
                            primary_seed_rank,
                            repair_r61_seeds, &repair_r61_seed_count,
                            refine_budget, repair_hw_limit, mode_param,
                            &seed_best_tail_wit, &seed_best_r61_wit,
                            &seed_best_joint_wit,
                            &stats);
    } else {
        run_repair_refinement(init1, init2, Wpre1, Wpre2,
                              repair_seeds, &repair_seed_count, refine_seed_cap,
                              primary_seed_rank,
                              repair_r61_seeds, &repair_r61_seed_count,
                              refine_budget, repair_hw_limit,
                              &seed_best_tail_wit, &seed_best_r61_wit,
                              &seed_best_joint_wit,
                              &stats);
    }
    double repair_refine_elapsed = (double)(clock() - tr0) / (double)CLOCKS_PER_SEC;

    int final_tail = stats.best_tail;
    int final_r61 = stats.best_r61;
    int final_joint_score = stats.best_joint_score;
    int final_joint_max = stats.best_joint_max;
    witness_t final_tail_wit = stats.best_tail_wit;
    witness_t final_r61_wit = stats.best_r61_wit;
    witness_t final_joint_wit = stats.best_joint_wit;

    printf("\nD60 repair seed refinement\n");
    printf("  input_seeds=%d retained_tail_seeds=%d retained_r61_seeds=%d\n",
           seed_inputs, repair_seed_count, repair_r61_seed_count);
    printf("  elapsed=%.3fs budget=%" PRIu64 " tested=%" PRIu64
           " repairable=%" PRIu64 " exact_D60=0=%" PRIu64
           " collisions=%" PRIu64 " seed_inserts=%" PRIu64
           " prefix_enums=%" PRIu64 "\n",
           repair_refine_elapsed, refine_budget, stats.tested, stats.repairable,
           stats.d0, stats.collision, stats.seed_inserts, stats.prefix_enums);
    if (stats.tested) {
        printf("  rate=%.2f Mtests/s repairable_rate=%.6f\n",
               repair_refine_elapsed > 0.0
                   ? (double)stats.tested / repair_refine_elapsed / 1e6
                   : 0.0,
               (double)stats.repairable / (double)stats.tested);
        printf("  phase tested/repairable: single=%" PRIu64 "/%" PRIu64
               " double=%" PRIu64 "/%" PRIu64
               " walk=%" PRIu64 "/%" PRIu64
               " prefix=%" PRIu64 "/%" PRIu64 "\n",
               stats.phase_tested[0], stats.phase_d0[0],
               stats.phase_tested[1], stats.phase_d0[1],
               stats.phase_tested[2], stats.phase_d0[2],
               stats.phase_tested[3], stats.phase_d0[3]);
        printf("  min refined D60 HW: %d d60=0x%x at W1[57..59]=0x%x,0x%x,0x%x\n",
               stats.min_d_hw, stats.min_d60,
               stats.min_d_w57, stats.min_d_w58, stats.min_d_w59);
    }
    printf("  best repaired tail HW: %d d60=0x%x d60_hw=%d r61=%d gh60=0x%x\n",
           final_tail, final_tail_wit.d60, hw(final_tail_wit.d60),
           final_tail_wit.r61_hw, final_tail_wit.gh60_key);
    printf("  best repaired tail W1[57..59]=0x%x,0x%x,0x%x\n",
           final_tail_wit.w57, final_tail_wit.w58, final_tail_wit.w59);
    printf("  best repaired tail W2[57..59]=0x%x,0x%x,0x%x\n",
           final_tail_wit.w2_57, final_tail_wit.w2_58, final_tail_wit.w2_59);
    printf("  best repaired r61 HW: %d d60=0x%x d60_hw=%d tail=%d gh60=0x%x\n",
           final_r61, final_r61_wit.d60, hw(final_r61_wit.d60),
           final_r61_wit.tail_hw, final_r61_wit.gh60_key);
    printf("  best repaired r61 W1[57..59]=0x%x,0x%x,0x%x\n",
           final_r61_wit.w57, final_r61_wit.w58, final_r61_wit.w59);
    printf("  best repaired r61 W2[57..59]=0x%x,0x%x,0x%x\n",
           final_r61_wit.w2_57, final_r61_wit.w2_58, final_r61_wit.w2_59);
    printf("  best repaired joint score: %d max=%d tail=%d r61=%d d60=0x%x d60_hw=%d gh60=0x%x improvements=%" PRIu64 "\n",
           final_joint_score, final_joint_max, final_joint_wit.tail_hw,
           final_joint_wit.r61_hw, final_joint_wit.d60, hw(final_joint_wit.d60),
           final_joint_wit.gh60_key, stats.joint_improvements);
    printf("  best repaired joint W1[57..59]=0x%x,0x%x,0x%x\n",
           final_joint_wit.w57, final_joint_wit.w58, final_joint_wit.w59);
    printf("  best repaired joint W2[57..59]=0x%x,0x%x,0x%x\n",
           final_joint_wit.w2_57, final_joint_wit.w2_58, final_joint_wit.w2_59);

    printf("\nSUMMARY N=%d sample_start=0 prefixes=0 total=%" PRIu64
           " d0=%" PRIu64 " best_tail=%d tail_r61=%d best_r61=%d"
           " best_joint=%d joint_max=%d joint_tail=%d joint_r61=%d"
           " tail_W1=0x%x,0x%x,0x%x tail_W2=0x%x,0x%x,0x%x"
           " joint_W1=0x%x,0x%x,0x%x joint_W2=0x%x,0x%x,0x%x"
           " r61_W1=0x%x,0x%x,0x%x r61_W2=0x%x,0x%x,0x%x\n",
           N, stats.tested, stats.d0, final_tail, final_tail_wit.r61_hw,
           final_r61, final_joint_score, final_joint_max,
           final_joint_wit.tail_hw, final_joint_wit.r61_hw,
           final_tail_wit.w57, final_tail_wit.w58,
           final_tail_wit.w59, final_tail_wit.w2_57, final_tail_wit.w2_58,
           final_tail_wit.w2_59, final_joint_wit.w57, final_joint_wit.w58,
           final_joint_wit.w59, final_joint_wit.w2_57, final_joint_wit.w2_58,
           final_joint_wit.w2_59, final_r61_wit.w57, final_r61_wit.w58,
           final_r61_wit.w59, final_r61_wit.w2_57, final_r61_wit.w2_58,
           final_r61_wit.w2_59);

    free(repair_seeds);
    free(repair_r61_seeds);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s N [prefix_limit] [refine_budget] [refine_seed_cap] [sample_start] [mode]\n", argv[0]);
        fprintf(stderr, "  prefix_limit=0 or omitted means all W57,W58 prefixes.\n");
        fprintf(stderr, "  refinement scans neighboring (W57,W58) prefixes over all W59 first.\n");
        fprintf(stderr, "  sample_start shifts permuted-prefix samples; ignored for exact scans.\n");
        fprintf(stderr, "  refine_budget=0 or omitted disables second-stage local refinement.\n");
        fprintf(stderr, "  mode=scan disables heavy profiling and keeps a compact witness registry.\n");
        fprintf(stderr, "  mode=repair also probes low-HW nonzero D60 as if W60 were repairable.\n");
        fprintf(stderr, "  mode=repair_seed skips scanning and refines explicit W57,W58,W59 seed triples.\n");
        fprintf(stderr, "  mode=repair_seed_walk only mutates explicit seed triples; it skips prefix sweeps.\n");
        fprintf(stderr, "  mode=repair_seed_joint_walk is repair_seed_walk with joint-ranked restarts.\n");
        fprintf(stderr, "  mode=repair_seed_ball enumerates a Hamming ball around explicit seed triples; sample_start is max_radius.\n");
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
    uint64_t refine_budget = 0;
    int refine_seed_cap = 128;
    if (argc >= 4) refine_budget = strtoull(argv[3], NULL, 0);
    if (argc >= 5) refine_seed_cap = atoi(argv[4]);
    if (refine_seed_cap < 1) refine_seed_cap = 1;
    if (refine_seed_cap > 4096) refine_seed_cap = 4096;
    uint64_t sample_start = 0;
    if (argc >= 6) sample_start = strtoull(argv[5], NULL, 0) & (prefix_space - 1u);
    const char *mode = (argc >= 7) ? argv[6] : "";
    int repair_enabled = (strcmp(mode, "repair") == 0);
    int repair_seed_mode = (strcmp(mode, "repair_seed") == 0);
    int repair_seed_walk_mode = (strcmp(mode, "repair_seed_walk") == 0);
    int repair_seed_joint_walk_mode = (strcmp(mode, "repair_seed_joint_walk") == 0);
    int repair_seed_ball_mode = (strcmp(mode, "repair_seed_ball") == 0);
    int scan_only = (strcmp(mode, "scan") == 0) || repair_enabled ||
        repair_seed_mode || repair_seed_walk_mode || repair_seed_joint_walk_mode ||
        repair_seed_ball_mode;
    int profile_enabled = !scan_only;
    int repair_hw_limit = 1;
    if (argc >= 8) repair_hw_limit = atoi(argv[7]);
    if (repair_hw_limit < 0) repair_hw_limit = 0;
    if (repair_hw_limit > N) repair_hw_limit = N;
    uint64_t word_space = 1ull << N;

    uint32_t M1[16], M2[16], init1[8], init2[8], Wpre1[64] = {0}, Wpre2[64] = {0};
    uint32_t m0 = 0;
    int candidate_mode = 0;
    if (!find_candidate(&m0, &candidate_mode, M1, M2, init1, init2, Wpre1, Wpre2)) {
        fprintf(stderr, "No da56=0 candidate found at N=%d.\n", N);
        return 1;
    }

    if (repair_seed_mode || repair_seed_walk_mode || repair_seed_joint_walk_mode || repair_seed_ball_mode) {
        if (argc < 9) {
            fprintf(stderr, "%s mode expects: %s N prefix_limit refine_budget refine_seed_cap sample_start %s repair_hw_limit W57,W58,W59 [...]\n",
                    mode, argv[0], mode);
            return 2;
        }
        int seed_mode = repair_seed_joint_walk_mode ? 3 :
                        (repair_seed_ball_mode ? 2 : (repair_seed_walk_mode ? 1 : 0));
        return run_repair_seed_mode(N, refine_budget, refine_seed_cap, repair_hw_limit,
                                    argc, argv, 8, seed_mode,
                                    sample_start,
                                    init1, init2, Wpre1, Wpre2);
    }

    uint64_t *d_hist = calloc((size_t)word_space, sizeof(uint64_t));
    uint64_t *fiber_hist = calloc((size_t)(word_space + 1u), sizeof(uint64_t));
    if (!d_hist || !fiber_hist) {
        fprintf(stderr, "Allocation failed.\n");
        free(d_hist); free(fiber_hist);
        return 1;
    }

    uint64_t gh_space = (profile_enabled && 2 * N <= 26) ? (1ull << (2 * N)) : 0;
    uint32_t *gh_count = NULL;
    uint8_t *gh_best_tail = NULL;
    uint8_t *gh_best_r61 = NULL;
    if (gh_space) {
        gh_count = calloc((size_t)gh_space, sizeof(uint32_t));
        gh_best_tail = malloc((size_t)gh_space);
        gh_best_r61 = malloc((size_t)gh_space);
        if (!gh_count || !gh_best_tail || !gh_best_r61) {
            fprintf(stderr, "GH table allocation failed.\n");
            free(d_hist); free(fiber_hist);
            free(gh_count); free(gh_best_tail); free(gh_best_r61);
            return 1;
        }
        memset(gh_best_tail, 255, (size_t)gh_space);
        memset(gh_best_r61, 255, (size_t)gh_space);
    }

    uint64_t table_cap = next_pow2_u64(prefix_limit * 2u + 1024u);
    mask_bucket_t *mask_table = NULL;
    sig_bucket_t *sig_table = NULL;
    sig_bucket_t *coarse_table = NULL;
    miner_bucket_t *miner_table = NULL;
    uint64_t miner_cap = profile_enabled
        ? next_pow2_u64(prefix_limit * (uint64_t)MINER_FAMILIES * 2u + 4096u)
        : 0;
    if (miner_cap > (1ull << 25)) miner_cap = 0;
    if (profile_enabled && table_cap <= (1ull << 25)) {
        mask_table = calloc((size_t)table_cap, sizeof(mask_bucket_t));
        sig_table = calloc((size_t)table_cap, sizeof(sig_bucket_t));
        coarse_table = calloc((size_t)table_cap, sizeof(sig_bucket_t));
        if (!mask_table || !sig_table || !coarse_table) {
            fprintf(stderr, "Enhanced-key table allocation failed.\n");
            free(d_hist); free(fiber_hist);
            free(gh_count); free(gh_best_tail); free(gh_best_r61);
            free(mask_table); free(sig_table); free(coarse_table);
            return 1;
        }
    }
    if (miner_cap) {
        miner_table = calloc((size_t)miner_cap, sizeof(miner_bucket_t));
        if (!miner_table) {
            fprintf(stderr, "Miner table allocation failed.\n");
            free(d_hist); free(fiber_hist);
            free(gh_count); free(gh_best_tail); free(gh_best_r61);
            free(mask_table); free(sig_table); free(coarse_table);
            return 1;
        }
    }

    uint64_t d_hw_hist[33] = {0};
    uint64_t r61_hw_hist[257] = {0};
    uint64_t tail_hw_hist[257] = {0};
    uint8_t best_tail_by_r61_hw[257];
    memset(best_tail_by_r61_hw, 255, sizeof(best_tail_by_r61_hw));
    uint64_t bit_active_count[128] = {0};
    uint64_t bit_active_tail_sum[128] = {0};
    uint8_t bit_active_best_tail[128];
    memset(bit_active_best_tail, 255, sizeof(bit_active_best_tail));
    uint64_t total_tail_sum = 0;
    int late_bits = 2 * N;
    int late_pair_count = late_bits * (late_bits - 1) / 2;
    uint64_t *pair_count = calloc((size_t)late_pair_count * 4u, sizeof(uint64_t));
    uint64_t *pair_tail_sum = calloc((size_t)late_pair_count * 4u, sizeof(uint64_t));
    uint8_t *pair_best_tail = malloc((size_t)late_pair_count * 4u);
    if (!pair_count || !pair_tail_sum || !pair_best_tail) {
        fprintf(stderr, "Pair-feature allocation failed.\n");
        free(d_hist); free(fiber_hist);
        free(gh_count); free(gh_best_tail); free(gh_best_r61);
        free(mask_table); free(sig_table); free(coarse_table);
        free(pair_count); free(pair_tail_sum); free(pair_best_tail);
        return 1;
    }
    memset(pair_best_tail, 255, (size_t)late_pair_count * 4u);

    refine_seed_t *refine_seeds = NULL;
    refine_seed_t *r61_refine_seeds = NULL;
    refine_seed_t *repair_seeds = NULL;
    refine_seed_t *repair_r61_seeds = NULL;
    int refine_seed_count = 0;
    int r61_refine_seed_count = 0;
    int repair_seed_count = 0;
    int repair_r61_seed_count = 0;
    if (refine_budget || scan_only) {
        refine_seeds = calloc((size_t)refine_seed_cap, sizeof(refine_seed_t));
        r61_refine_seeds = calloc((size_t)refine_seed_cap, sizeof(refine_seed_t));
        if (!refine_seeds || !r61_refine_seeds) {
            fprintf(stderr, "Refinement seed allocation failed.\n");
            free(d_hist); free(fiber_hist);
            free(gh_count); free(gh_best_tail); free(gh_best_r61);
            free(mask_table); free(sig_table); free(coarse_table);
            free(miner_table);
            free(pair_count); free(pair_tail_sum); free(pair_best_tail);
            free(refine_seeds); free(r61_refine_seeds);
            return 1;
        }
    }
    if (repair_enabled) {
        repair_seeds = calloc((size_t)refine_seed_cap, sizeof(refine_seed_t));
        repair_r61_seeds = calloc((size_t)refine_seed_cap, sizeof(refine_seed_t));
        if (!repair_seeds || !repair_r61_seeds) {
            fprintf(stderr, "Repair seed allocation failed.\n");
            free(d_hist); free(fiber_hist);
            free(gh_count); free(gh_best_tail); free(gh_best_r61);
            free(mask_table); free(sig_table); free(coarse_table);
            free(miner_table);
            free(pair_count); free(pair_tail_sum); free(pair_best_tail);
            free(refine_seeds); free(r61_refine_seeds);
            free(repair_seeds); free(repair_r61_seeds);
            return 1;
        }
    }

    uint64_t total = 0;
    uint64_t d0 = 0;
    uint64_t collision = 0;
    uint64_t prefixes_with_d0 = 0;
    uint64_t max_d0_per_prefix = 0;
    uint32_t max_pref_w57 = 0, max_pref_w58 = 0;
    int min_d_hw = 99;
    int min_r61_hw = 999;
    int min_tail_hw = 999;
    uint64_t repair_candidates = 0;
    int repair_min_tail_hw = 999;
    int repair_min_r61_hw = 999;
    witness_t best_r61 = {0};
    witness_t best_tail = {0};
    witness_t repair_best_tail = {0};
    witness_t repair_best_r61 = {0};
    witness_t first_collision = {0};

    clock_t t0 = clock();

    uint64_t perm_step = 11400714819323198485ull;
    const char *prefix_mode = (prefix_limit == prefix_space) ? "exact" : "permuted-prefix-sample";

    for (uint64_t i = 0; i < prefix_limit; i++) {
        uint64_t p = (prefix_limit == prefix_space)
            ? i
            : (((sample_start + i) * perm_step) & (prefix_space - 1u));
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

            if (repair_enabled && d60 != 0 && dhw <= repair_hw_limit) {
                uint32_t repaired_d60 = 0;
                witness_t repair_wit;
                int repaired_tail = eval_repaired_tail(
                    init1, init2, Wpre1, Wpre2, w57, w58, (uint32_t)w,
                    &repair_wit, &repaired_d60);
                (void)repaired_d60;
                repair_candidates++;
                if (repaired_tail < repair_min_tail_hw) {
                    repair_min_tail_hw = repaired_tail;
                    repair_best_tail = repair_wit;
                }
                if (repair_wit.r61_hw < repair_min_r61_hw) {
                    repair_min_r61_hw = repair_wit.r61_hw;
                    repair_best_r61 = repair_wit;
                }
                if (repair_seeds) {
                    refine_seed_insert(repair_seeds, &repair_seed_count,
                                       refine_seed_cap, &repair_wit);
                }
                if (repair_r61_seeds) {
                    refine_seed_insert_r61(repair_r61_seeds, &repair_r61_seed_count,
                                           refine_seed_cap, &repair_wit);
                }
            }

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
                if (refine_seeds && tail_hw >= 0) {
                    refine_seed_insert(refine_seeds, &refine_seed_count, refine_seed_cap, &wit);
                }
                if (r61_refine_seeds && tail_hw >= 0) {
                    refine_seed_insert_r61(r61_refine_seeds, &r61_refine_seed_count,
                                           refine_seed_cap, &wit);
                }
                if (profile_enabled && wit.r61_hw >= 0 && wit.r61_hw < 257) {
                    r61_hw_hist[wit.r61_hw]++;
                    if (tail_hw >= 0 && tail_hw < best_tail_by_r61_hw[wit.r61_hw])
                        best_tail_by_r61_hw[wit.r61_hw] = (uint8_t)tail_hw;
                }
                if (profile_enabled && tail_hw >= 0 && tail_hw < 257) tail_hw_hist[tail_hw]++;
                if (profile_enabled && tail_hw >= 0) {
                    total_tail_sum += (uint64_t)tail_hw;
                    for (int bit = 0; bit < 8 * N && bit < 128; bit++) {
                        uint64_t active = (bit < 64)
                            ? ((wit.r61_mask_lo >> bit) & 1ull)
                            : ((wit.r61_mask_hi >> (bit - 64)) & 1ull);
                        if (!active) continue;
                        bit_active_count[bit]++;
                        bit_active_tail_sum[bit] += (uint64_t)tail_hw;
                        if (tail_hw < bit_active_best_tail[bit])
                            bit_active_best_tail[bit] = (uint8_t)tail_hw;
                    }
                    uint64_t late_mask = 0;
                    for (int lb = 0; lb < late_bits; lb++) {
                        int global_bit = 6 * N + lb;
                        uint64_t active = (global_bit < 64)
                            ? ((wit.r61_mask_lo >> global_bit) & 1ull)
                            : ((wit.r61_mask_hi >> (global_bit - 64)) & 1ull);
                        if (active) late_mask |= 1ull << lb;
                    }
                    uint64_t reg_mask = (gN == 32) ? 0xffffffffULL : ((1ull << gN) - 1ull);
                    uint64_t reg6_mask = late_mask & reg_mask;
                    uint64_t reg7_mask = (late_mask >> gN) & reg_mask;
                    int reg6_hw = __builtin_popcountll(reg6_mask);
                    int reg7_hw = __builtin_popcountll(reg7_mask);
                    uint64_t fold8 = 0;
                    for (int lb = 0; lb < late_bits; lb++) {
                        if ((late_mask >> lb) & 1ull) fold8 ^= 1ull << (lb & 7);
                    }
                    uint64_t gh = wit.gh60_key;
                    uint64_t shift = (uint64_t)(2 * gN);
                    uint64_t reg6_low8 = reg6_mask & 0xffu;
                    uint64_t reg7_low8 = reg7_mask & 0xffu;
                    uint64_t reg6_high8 = (gN > 8) ? ((reg6_mask >> (gN - 8)) & 0xffu) : reg6_low8;
                    uint64_t reg7_high8 = (gN > 8) ? ((reg7_mask >> (gN - 8)) & 0xffu) : reg7_low8;
                    if (miner_table) {
                        miner_insert(miner_table, miner_cap, miner_key(0, gh), tail_hw);
                        miner_insert(miner_table, miner_cap, miner_key(1, gh | ((uint64_t)(wit.r61_hw & 0xff) << shift)), tail_hw);
                        miner_insert(miner_table, miner_cap, miner_key(2, gh | ((uint64_t)reg6_hw << shift) | ((uint64_t)reg7_hw << (shift + 5))), tail_hw);
                        miner_insert(miner_table, miner_cap, miner_key(3, gh | (fold8 << shift)), tail_hw);
                        miner_insert(miner_table, miner_cap, miner_key(4, gh | (reg6_low8 << shift)), tail_hw);
                        miner_insert(miner_table, miner_cap, miner_key(5, gh | (reg7_low8 << shift)), tail_hw);
                        miner_insert(miner_table, miner_cap, miner_key(6, gh | (reg6_high8 << shift)), tail_hw);
                        miner_insert(miner_table, miner_cap, miner_key(7, gh | (reg7_high8 << shift)), tail_hw);
                        miner_insert(miner_table, miner_cap,
                                     miner_key(8, (uint64_t)(wit.r61_hw & 0xff) |
                                                    ((uint64_t)reg6_hw << 8) |
                                                    ((uint64_t)reg7_hw << 13) |
                                                    (fold8 << 18)),
                                     tail_hw);
                        miner_insert(miner_table, miner_cap,
                                     miner_key(9, (uint64_t)reg6_hw |
                                                    ((uint64_t)reg7_hw << 5) |
                                                    (fold8 << 10)),
                                     tail_hw);
                    }
                    int pair_idx = 0;
                    for (int a = 0; a < late_bits; a++) {
                        int abit = (late_mask >> a) & 1u;
                        for (int b = a + 1; b < late_bits; b++, pair_idx++) {
                            int bbit = (late_mask >> b) & 1u;
                            int state = (abit << 1) | bbit;
                            size_t idx = (size_t)pair_idx * 4u + (size_t)state;
                            pair_count[idx]++;
                            pair_tail_sum[idx] += (uint64_t)tail_hw;
                            if (tail_hw < pair_best_tail[idx])
                                pair_best_tail[idx] = (uint8_t)tail_hw;
                        }
                    }
                }
                if (gh_space) {
                    gh_count[wit.gh60_key]++;
                    if (tail_hw >= 0 && tail_hw < gh_best_tail[wit.gh60_key])
                        gh_best_tail[wit.gh60_key] = (uint8_t)tail_hw;
                    if (wit.r61_hw >= 0 && wit.r61_hw < gh_best_r61[wit.gh60_key])
                        gh_best_r61[wit.gh60_key] = (uint8_t)wit.r61_hw;
                }
                if (mask_table)
                    mask_table_insert(mask_table, table_cap, wit.r61_mask_lo, wit.r61_mask_hi, wit.r61_hw, tail_hw);
                if (sig_table)
                    sig_table_insert(sig_table, table_cap, wit.tail_carry_sig, tail_hw);
                if (coarse_table) {
                    uint64_t coarse_key = ((uint64_t)wit.gh60_key << 8) | (uint64_t)(wit.r61_hw & 0xff);
                    sig_table_insert(coarse_table, table_cap, coarse_key, tail_hw);
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

    uint64_t gh_unique = 0, gh_max_count = 0;
    uint32_t gh_max_key = 0;
    int gh_max_best_tail = 999, gh_global_best_tail = 999;
    if (gh_space) {
        for (uint64_t i = 0; i < gh_space; i++) {
            if (!gh_count[i]) continue;
            gh_unique++;
            if (gh_best_tail[i] < gh_global_best_tail) gh_global_best_tail = gh_best_tail[i];
            if (gh_count[i] > gh_max_count) {
                gh_max_count = gh_count[i];
                gh_max_key = (uint32_t)i;
                gh_max_best_tail = gh_best_tail[i];
            }
        }
    }

    uint64_t mask_unique = 0, mask_max_count = 0;
    int mask_max_best_tail = 999, mask_global_best_tail = 999;
    uint64_t mask_max_lo = 0, mask_max_hi = 0;
    if (mask_table) {
        for (uint64_t i = 0; i < table_cap; i++) {
            if (!mask_table[i].used) continue;
            mask_unique++;
            if (mask_table[i].best_tail < mask_global_best_tail) mask_global_best_tail = mask_table[i].best_tail;
            if (mask_table[i].count > mask_max_count) {
                mask_max_count = mask_table[i].count;
                mask_max_best_tail = mask_table[i].best_tail;
                mask_max_lo = mask_table[i].lo;
                mask_max_hi = mask_table[i].hi;
            }
        }
    }

    uint64_t sig_unique = 0, sig_max_count = 0, sig_max = 0;
    int sig_max_best_tail = 999, sig_global_best_tail = 999;
    if (sig_table) {
        for (uint64_t i = 0; i < table_cap; i++) {
            if (!sig_table[i].used) continue;
            sig_unique++;
            if (sig_table[i].best_tail < sig_global_best_tail) sig_global_best_tail = sig_table[i].best_tail;
            if (sig_table[i].count > sig_max_count) {
                sig_max_count = sig_table[i].count;
                sig_max_best_tail = sig_table[i].best_tail;
                sig_max = sig_table[i].sig;
            }
        }
    }

    uint64_t coarse_unique = 0, coarse_max_count = 0, coarse_max = 0;
    int coarse_max_best_tail = 999, coarse_global_best_tail = 999;
    if (coarse_table) {
        for (uint64_t i = 0; i < table_cap; i++) {
            if (!coarse_table[i].used) continue;
            coarse_unique++;
            if (coarse_table[i].best_tail < coarse_global_best_tail)
                coarse_global_best_tail = coarse_table[i].best_tail;
            if (coarse_table[i].count > coarse_max_count) {
                coarse_max_count = coarse_table[i].count;
                coarse_max_best_tail = coarse_table[i].best_tail;
                coarse_max = coarse_table[i].sig;
            }
        }
    }

    int top_bits[8];
    double top_gain[8];
    for (int i = 0; i < 8; i++) {
        top_bits[i] = -1;
        top_gain[i] = -1e100;
    }
    for (int bit = 0; bit < 8 * N && bit < 128; bit++) {
        uint64_t on = bit_active_count[bit];
        uint64_t off = d0 - on;
        if (on < 16 || off < 16) continue;
        double on_mean = (double)bit_active_tail_sum[bit] / (double)on;
        double off_mean = (double)(total_tail_sum - bit_active_tail_sum[bit]) / (double)off;
        double gain = off_mean - on_mean;
        for (int k = 0; k < 8; k++) {
            if (gain > top_gain[k]) {
                for (int j = 7; j > k; j--) {
                    top_gain[j] = top_gain[j - 1];
                    top_bits[j] = top_bits[j - 1];
                }
                top_gain[k] = gain;
                top_bits[k] = bit;
                break;
            }
        }
    }

    int top_pair_a[8], top_pair_b[8], top_pair_state[8];
    double top_pair_gain[8];
    for (int i = 0; i < 8; i++) {
        top_pair_a[i] = -1;
        top_pair_b[i] = -1;
        top_pair_state[i] = -1;
        top_pair_gain[i] = -1e100;
    }
    int pair_idx = 0;
    for (int a = 0; a < late_bits; a++) {
        for (int b = a + 1; b < late_bits; b++, pair_idx++) {
            for (int state = 0; state < 4; state++) {
                size_t idx = (size_t)pair_idx * 4u + (size_t)state;
                uint64_t on = pair_count[idx];
                uint64_t off = d0 - on;
                if (on < 32 || off < 32) continue;
                double on_mean = (double)pair_tail_sum[idx] / (double)on;
                double off_mean = (double)(total_tail_sum - pair_tail_sum[idx]) / (double)off;
                double gain = off_mean - on_mean;
                for (int k = 0; k < 8; k++) {
                    if (gain > top_pair_gain[k]) {
                        for (int j = 7; j > k; j--) {
                            top_pair_gain[j] = top_pair_gain[j - 1];
                            top_pair_a[j] = top_pair_a[j - 1];
                            top_pair_b[j] = top_pair_b[j - 1];
                            top_pair_state[j] = top_pair_state[j - 1];
                        }
                        top_pair_gain[k] = gain;
                        top_pair_a[k] = a;
                        top_pair_b[k] = b;
                        top_pair_state[k] = state;
                        break;
                    }
                }
            }
        }
    }

    int miner_threshold = min_tail_hw + 5;
    if (miner_threshold <= 8) miner_threshold = 8;
    else if (miner_threshold <= 12) miner_threshold = 12;
    else if (miner_threshold <= 16) miner_threshold = 16;
    else if (miner_threshold <= 20) miner_threshold = 20;
    else if (miner_threshold <= 24) miner_threshold = 24;
    else miner_threshold = 32;

    uint64_t miner_unique = 0;
    int top_rate_idx[8], top_best_idx[8], top_score_idx[8];
    double top_rate[8], top_score[8];
    for (int i = 0; i < 8; i++) {
        top_rate_idx[i] = top_best_idx[i] = top_score_idx[i] = -1;
        top_rate[i] = top_score[i] = -1e100;
    }
    if (miner_table) {
        for (uint64_t i = 0; i < miner_cap; i++) {
            if (!miner_table[i].used) continue;
            miner_unique++;
            uint32_t cnt = miner_table[i].count;
            uint32_t low = miner_low_count(&miner_table[i], miner_threshold);
            double rate = cnt ? (double)low / (double)cnt : 0.0;
            double score = rate * log((double)cnt + 1.0);

            if (cnt >= 32 && low > 0) {
                for (int k = 0; k < 8; k++) {
                    if (rate > top_rate[k]) {
                        for (int j = 7; j > k; j--) {
                            top_rate[j] = top_rate[j - 1];
                            top_rate_idx[j] = top_rate_idx[j - 1];
                        }
                        top_rate[k] = rate;
                        top_rate_idx[k] = (int)i;
                        break;
                    }
                }
            }
            if (cnt >= 16) {
                for (int k = 0; k < 8; k++) {
                    int cur = top_best_idx[k];
                    if (cur < 0 ||
                        miner_table[i].best_tail < miner_table[cur].best_tail ||
                        (miner_table[i].best_tail == miner_table[cur].best_tail &&
                         miner_table[i].count > miner_table[cur].count)) {
                        for (int j = 7; j > k; j--) top_best_idx[j] = top_best_idx[j - 1];
                        top_best_idx[k] = (int)i;
                        break;
                    }
                }
            }
            if (cnt >= 32 && low > 0) {
                for (int k = 0; k < 8; k++) {
                    if (score > top_score[k]) {
                        for (int j = 7; j > k; j--) {
                            top_score[j] = top_score[j - 1];
                            top_score_idx[j] = top_score_idx[j - 1];
                        }
                        top_score[k] = score;
                        top_score_idx[k] = (int)i;
                        break;
                    }
                }
            }
        }
    }

    double scan_elapsed = (double)(clock() - t0) / (double)CLOCKS_PER_SEC;
    refine_stats_t refine_stats;
    memset(&refine_stats, 0, sizeof(refine_stats));
    refine_stats_t repair_refine_stats;
    memset(&repair_refine_stats, 0, sizeof(repair_refine_stats));
    double refine_elapsed = 0.0;
    double repair_refine_elapsed = 0.0;
    int repair_scan_best_tail_hw = repair_min_tail_hw;
    int repair_scan_best_r61_hw = repair_min_r61_hw;
    if (refine_budget && refine_seed_count > 0 && min_tail_hw < 999) {
        clock_t tr0 = clock();
        run_refinement(init1, init2, Wpre1, Wpre2,
                       refine_seeds, &refine_seed_count, refine_seed_cap,
                       refine_budget, &best_tail, &best_r61, &best_tail,
                       &refine_stats);
        refine_elapsed = (double)(clock() - tr0) / (double)CLOCKS_PER_SEC;
    }
    if (repair_enabled && refine_budget && repair_seed_count > 0 && repair_min_tail_hw < 999) {
        clock_t tr0 = clock();
        run_repair_refinement(init1, init2, Wpre1, Wpre2,
                              repair_seeds, &repair_seed_count, refine_seed_cap,
                              0,
                              repair_r61_seeds, &repair_r61_seed_count,
                              refine_budget, repair_hw_limit,
                              &repair_best_tail, &repair_best_r61,
                              &repair_best_tail,
                              &repair_refine_stats);
        repair_refine_elapsed = (double)(clock() - tr0) / (double)CLOCKS_PER_SEC;
        if (repair_refine_stats.best_tail < repair_min_tail_hw) {
            repair_min_tail_hw = repair_refine_stats.best_tail;
            repair_best_tail = repair_refine_stats.best_tail_wit;
        }
        if (repair_refine_stats.best_r61 < repair_min_r61_hw) {
            repair_min_r61_hw = repair_refine_stats.best_r61;
            repair_best_r61 = repair_refine_stats.best_r61_wit;
        }
    }
    double elapsed = scan_elapsed + refine_elapsed + repair_refine_elapsed;
    double expected_d0 = (double)total / (double)word_space;

    printf("free_word_mitm_reducedn\n");
    printf("N=%d mask=0x%x msb=0x%x\n", N, gMASK, gMSB);
    printf("candidate: M0=0x%x mode=%s fill=0x%x kernel=dM0=dM9=0x%x\n",
           m0, candidate_mode ? "random-fallback" : "fixed-fill", gMASK, gMSB);
    printf("prefixes=%" PRIu64 "/%" PRIu64 " mode=%s w59_per_prefix=%" PRIu64 " total=%" PRIu64 "\n",
           prefix_limit, prefix_space, prefix_mode, word_space, total);
    if (scan_only) {
        printf("run_mode=%s registry_cap=%d\n", repair_enabled ? "repair" : "scan", refine_seed_cap);
        if (repair_enabled) printf("repair_d60_hw_limit=%d\n", repair_hw_limit);
    }
    if (prefix_limit != prefix_space) {
        printf("sample_start=%" PRIu64 "\n", sample_start);
    }
    printf("scan_elapsed=%.3fs rate=%.2f Mtriples/s\n",
           scan_elapsed, scan_elapsed > 0.0 ? (double)total / scan_elapsed / 1e6 : 0.0);
    if (refine_budget) {
        printf("refine_elapsed=%.3fs repair_refine_elapsed=%.3fs total_elapsed=%.3fs\n",
               refine_elapsed, repair_refine_elapsed, elapsed);
    }
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

    printf("\nSUMMARY N=%d sample_start=%" PRIu64 " prefixes=%" PRIu64
           " total=%" PRIu64 " d0=%" PRIu64 " best_tail=%d tail_r61=%d"
           " best_r61=%d tail_W1=0x%x,0x%x,0x%x tail_W2=0x%x,0x%x,0x%x"
           " r61_W1=0x%x,0x%x,0x%x r61_W2=0x%x,0x%x,0x%x\n",
           N, sample_start, prefix_limit, total, d0,
           min_tail_hw < 999 ? min_tail_hw : -1,
           min_tail_hw < 999 ? best_tail.r61_hw : -1,
           min_r61_hw < 999 ? min_r61_hw : -1,
           best_tail.w57, best_tail.w58, best_tail.w59,
           best_tail.w2_57, best_tail.w2_58, best_tail.w2_59,
           best_r61.w57, best_r61.w58, best_r61.w59,
           best_r61.w2_57, best_r61.w2_58, best_r61.w2_59);

    if (scan_only && refine_seeds) {
        printf("\nScan-only witness registry\n");
        printf("  registry_count=%d registry_cap=%d\n", refine_seed_count, refine_seed_cap);
        int show = refine_seed_count < 16 ? refine_seed_count : 16;
        for (int i = 0; i < show; i++) {
            witness_t *sw = &refine_seeds[i].wit;
            printf("  witness[%02d] tail=%d r61=%d gh60=0x%x W1=0x%x,0x%x,0x%x W2=0x%x,0x%x,0x%x\n",
                   i, sw->tail_hw, sw->r61_hw, sw->gh60_key,
                   sw->w57, sw->w58, sw->w59,
                   sw->w2_57, sw->w2_58, sw->w2_59);
        }
    }

    if (scan_only && r61_refine_seeds) {
        printf("\nScan-only r61 registry\n");
        printf("  registry_count=%d registry_cap=%d\n", r61_refine_seed_count, refine_seed_cap);
        int show = r61_refine_seed_count < 16 ? r61_refine_seed_count : 16;
        for (int i = 0; i < show; i++) {
            witness_t *sw = &r61_refine_seeds[i].wit;
            printf("  r61_witness[%02d] r61=%d tail=%d gh60=0x%x W1=0x%x,0x%x,0x%x W2=0x%x,0x%x,0x%x\n",
                   i, sw->r61_hw, sw->tail_hw, sw->gh60_key,
                   sw->w57, sw->w58, sw->w59,
                   sw->w2_57, sw->w2_58, sw->w2_59);
        }
    }

    if (repair_enabled) {
        printf("\nD60 repair probe registry\n");
        printf("  repair_candidates=%" PRIu64 " d60_hw_limit=%d\n",
               repair_candidates, repair_hw_limit);
        if (repair_min_tail_hw < 999) {
            printf("  best repaired tail HW: %d d60=0x%x d60_hw=%d r61=%d gh60=0x%x\n",
                   repair_min_tail_hw, repair_best_tail.d60, hw(repair_best_tail.d60),
                   repair_best_tail.r61_hw, repair_best_tail.gh60_key);
            printf("  best repaired tail W1[57..59]=0x%x,0x%x,0x%x\n",
                   repair_best_tail.w57, repair_best_tail.w58, repair_best_tail.w59);
            printf("  best repaired tail W2[57..59]=0x%x,0x%x,0x%x\n",
                   repair_best_tail.w2_57, repair_best_tail.w2_58, repair_best_tail.w2_59);
        }
        if (repair_min_r61_hw < 999) {
            printf("  best repaired r61 HW: %d d60=0x%x d60_hw=%d tail=%d gh60=0x%x\n",
                   repair_min_r61_hw, repair_best_r61.d60, hw(repair_best_r61.d60),
                   repair_best_r61.tail_hw, repair_best_r61.gh60_key);
            printf("  best repaired r61 W1[57..59]=0x%x,0x%x,0x%x\n",
                   repair_best_r61.w57, repair_best_r61.w58, repair_best_r61.w59);
            printf("  best repaired r61 W2[57..59]=0x%x,0x%x,0x%x\n",
                   repair_best_r61.w2_57, repair_best_r61.w2_58, repair_best_r61.w2_59);
        }
        if (repair_seeds) {
            printf("  repaired_tail_registry_count=%d registry_cap=%d\n",
                   repair_seed_count, refine_seed_cap);
            int show = repair_seed_count < 16 ? repair_seed_count : 16;
            for (int i = 0; i < show; i++) {
                witness_t *sw = &repair_seeds[i].wit;
                printf("  repair_witness[%02d] tail=%d r61=%d d60=0x%x d60_hw=%d gh60=0x%x W1=0x%x,0x%x,0x%x W2=0x%x,0x%x,0x%x\n",
                       i, sw->tail_hw, sw->r61_hw, sw->d60, hw(sw->d60), sw->gh60_key,
                       sw->w57, sw->w58, sw->w59,
                       sw->w2_57, sw->w2_58, sw->w2_59);
            }
        }
        if (repair_r61_seeds) {
            printf("  repaired_r61_registry_count=%d registry_cap=%d\n",
                   repair_r61_seed_count, refine_seed_cap);
            int show = repair_r61_seed_count < 16 ? repair_r61_seed_count : 16;
            for (int i = 0; i < show; i++) {
                witness_t *sw = &repair_r61_seeds[i].wit;
                printf("  repair_r61_witness[%02d] r61=%d tail=%d d60=0x%x d60_hw=%d gh60=0x%x W1=0x%x,0x%x,0x%x W2=0x%x,0x%x,0x%x\n",
                       i, sw->r61_hw, sw->tail_hw, sw->d60, hw(sw->d60), sw->gh60_key,
                       sw->w57, sw->w58, sw->w59,
                       sw->w2_57, sw->w2_58, sw->w2_59);
            }
        }
        if (refine_budget) {
            printf("\nD60 repair second-stage local refinement\n");
            printf("  seed pool: count=%d cap=%d\n", repair_seed_count, refine_seed_cap);
            printf("  budget=%" PRIu64 " tested=%" PRIu64 " repairable=%" PRIu64
                   " exact_D60=0=%" PRIu64 " collisions=%" PRIu64
                   " seed_inserts=%" PRIu64 " prefix_enums=%" PRIu64 "\n",
                   refine_budget, repair_refine_stats.tested, repair_refine_stats.repairable,
                   repair_refine_stats.d0, repair_refine_stats.collision,
                   repair_refine_stats.seed_inserts, repair_refine_stats.prefix_enums);
            if (repair_refine_stats.tested) {
                printf("  repairable rate: %.6f\n",
                       (double)repair_refine_stats.repairable /
                       (double)repair_refine_stats.tested);
                printf("  phase tested/repairable: single=%" PRIu64 "/%" PRIu64
                       " double=%" PRIu64 "/%" PRIu64
                       " walk=%" PRIu64 "/%" PRIu64
                       " prefix=%" PRIu64 "/%" PRIu64 "\n",
                       repair_refine_stats.phase_tested[0], repair_refine_stats.phase_d0[0],
                       repair_refine_stats.phase_tested[1], repair_refine_stats.phase_d0[1],
                       repair_refine_stats.phase_tested[2], repair_refine_stats.phase_d0[2],
                       repair_refine_stats.phase_tested[3], repair_refine_stats.phase_d0[3]);
                printf("  min refined D60 HW: %d d60=0x%x at W1[57..59]=0x%x,0x%x,0x%x\n",
                       repair_refine_stats.min_d_hw, repair_refine_stats.min_d60,
                       repair_refine_stats.min_d_w57, repair_refine_stats.min_d_w58,
                       repair_refine_stats.min_d_w59);
                printf("  best refined repaired tail HW: %d (scan repair best %d, improvements=%" PRIu64 ")\n",
                       repair_refine_stats.best_tail, repair_scan_best_tail_hw,
                       repair_refine_stats.tail_improvements);
                printf("  best refined repaired tail W1[57..59]=0x%x,0x%x,0x%x\n",
                       repair_refine_stats.best_tail_wit.w57,
                       repair_refine_stats.best_tail_wit.w58,
                       repair_refine_stats.best_tail_wit.w59);
                printf("  best refined repaired tail W2[57..59]=0x%x,0x%x,0x%x\n",
                       repair_refine_stats.best_tail_wit.w2_57,
                       repair_refine_stats.best_tail_wit.w2_58,
                       repair_refine_stats.best_tail_wit.w2_59);
                printf("  best refined repaired r61 HW: %d (scan repair best %d, improvements=%" PRIu64 ")\n",
                       repair_refine_stats.best_r61, repair_scan_best_r61_hw,
                       repair_refine_stats.r61_improvements);
            }
        }
    }

    if (refine_budget) {
        printf("\nSecond-stage local refinement\n");
        printf("  seed pool: count=%d cap=%d\n", refine_seed_count, refine_seed_cap);
        if (refine_seed_count > 0) {
            int show = refine_seed_count < 8 ? refine_seed_count : 8;
            printf("  top seeds:");
            for (int i = 0; i < show; i++) {
                witness_t *sw = &refine_seeds[i].wit;
                printf(" [tail%d/r61%d W=0x%x,0x%x,0x%x]",
                       sw->tail_hw, sw->r61_hw, sw->w57, sw->w58, sw->w59);
            }
            printf("\n");
        }
        printf("  budget=%" PRIu64 " tested=%" PRIu64 " D60=0=%" PRIu64
               " collisions=%" PRIu64 " seed_inserts=%" PRIu64
               " prefix_enums=%" PRIu64 "\n",
               refine_budget, refine_stats.tested, refine_stats.d0,
               refine_stats.collision, refine_stats.seed_inserts,
               refine_stats.prefix_enums);
        if (refine_stats.tested) {
            printf("  D60=0 rate: %.6f\n", (double)refine_stats.d0 / (double)refine_stats.tested);
            printf("  phase tested/D60=0: single=%" PRIu64 "/%" PRIu64
                   " double=%" PRIu64 "/%" PRIu64
                   " walk=%" PRIu64 "/%" PRIu64
                   " prefix=%" PRIu64 "/%" PRIu64 "\n",
                   refine_stats.phase_tested[0], refine_stats.phase_d0[0],
                   refine_stats.phase_tested[1], refine_stats.phase_d0[1],
                   refine_stats.phase_tested[2], refine_stats.phase_d0[2],
                   refine_stats.phase_tested[3], refine_stats.phase_d0[3]);
            printf("  min refined D60 HW: %d d60=0x%x at W1[57..59]=0x%x,0x%x,0x%x\n",
                   refine_stats.min_d_hw, refine_stats.min_d60,
                   refine_stats.min_d_w57, refine_stats.min_d_w58, refine_stats.min_d_w59);
            printf("  best refined tail HW: %d (scan best %d, improvements=%" PRIu64 ")\n",
                   refine_stats.best_tail, min_tail_hw, refine_stats.tail_improvements);
            printf("  best refined tail W1[57..59]=0x%x,0x%x,0x%x\n",
                   refine_stats.best_tail_wit.w57, refine_stats.best_tail_wit.w58,
                   refine_stats.best_tail_wit.w59);
            printf("  best refined tail W2[57..59]=0x%x,0x%x,0x%x\n",
                   refine_stats.best_tail_wit.w2_57, refine_stats.best_tail_wit.w2_58,
                   refine_stats.best_tail_wit.w2_59);
            printf("  best refined r61 HW: %d (scan best %d, improvements=%" PRIu64 ")\n",
                   refine_stats.best_r61, min_r61_hw, refine_stats.r61_improvements);
        }
    }

    if (profile_enabled) {
        printf("\nEnhanced key profile among D60=0 matches\n");
        printf("  r61 HW histogram:");
        for (int i = 0; i <= 8 * N && i < 257; i++) {
            if (r61_hw_hist[i]) {
                int bt = best_tail_by_r61_hw[i] == 255 ? -1 : best_tail_by_r61_hw[i];
                printf(" %d:%" PRIu64 "/bt%d", i, r61_hw_hist[i], bt);
            }
        }
        printf("\n");
        printf("  tail HW histogram:");
        for (int i = 0; i <= 8 * N && i < 257; i++) {
            if (tail_hw_hist[i]) printf(" %d:%" PRIu64, i, tail_hw_hist[i]);
        }
        printf("\n");
        if (gh_space) {
            uint32_t max_dg = (gh_max_key >> N) & gMASK;
            uint32_t max_dh = gh_max_key & gMASK;
            printf("  gh60 buckets: unique=%" PRIu64 "/%" PRIu64
                   " max_count=%" PRIu64 " key=(0x%x,0x%x) max_bucket_best_tail=%d global_best_tail=%d\n",
                   gh_unique, gh_space, gh_max_count, max_dg, max_dh,
                   gh_max_best_tail, gh_global_best_tail);
        } else {
            printf("  gh60 buckets: skipped (2N key too large for dense table)\n");
        }
        if (mask_table) {
            printf("  r61 active-mask buckets: unique=%" PRIu64 " table_cap=%" PRIu64
                   " max_count=%" PRIu64 " max_bucket_best_tail=%d global_best_tail=%d"
                   " max_mask_lo=0x%016" PRIx64 " max_mask_hi=0x%016" PRIx64 "\n",
                   mask_unique, table_cap, mask_max_count, mask_max_best_tail,
                   mask_global_best_tail, mask_max_lo, mask_max_hi);
        } else {
            printf("  r61 active-mask buckets: skipped (table cap would be too large)\n");
        }
        if (sig_table) {
            printf("  tail carry-signature buckets: unique=%" PRIu64 " table_cap=%" PRIu64
                   " max_count=%" PRIu64 " max_bucket_best_tail=%d global_best_tail=%d"
                   " max_sig=0x%016" PRIx64 "\n",
                   sig_unique, table_cap, sig_max_count, sig_max_best_tail,
                   sig_global_best_tail, sig_max);
        } else {
            printf("  tail carry-signature buckets: skipped (table cap would be too large)\n");
        }
        if (coarse_table) {
            uint32_t coarse_gh = (uint32_t)(coarse_max >> 8);
            int coarse_r61 = (int)(coarse_max & 0xffu);
            printf("  coarse gh60+r61_hw buckets: unique=%" PRIu64 " table_cap=%" PRIu64
                   " max_count=%" PRIu64 " max_bucket_best_tail=%d global_best_tail=%d"
                   " max_key_gh=(0x%x,0x%x) max_key_r61=%d\n",
                   coarse_unique, table_cap, coarse_max_count, coarse_max_best_tail,
                   coarse_global_best_tail, (coarse_gh >> N) & gMASK, coarse_gh & gMASK,
                   coarse_r61);
        } else {
            printf("  coarse gh60+r61_hw buckets: skipped (table cap would be too large)\n");
        }
        printf("  top r61 active-bit mean-tail gains:");
        for (int k = 0; k < 8; k++) {
            int bit = top_bits[k];
            if (bit < 0) continue;
            uint64_t on = bit_active_count[bit];
            uint64_t off = d0 - on;
            double on_mean = (double)bit_active_tail_sum[bit] / (double)on;
            double off_mean = (double)(total_tail_sum - bit_active_tail_sum[bit]) / (double)off;
            int reg = bit / N;
            int reg_bit = bit % N;
            printf(" r%d.b%d:on%" PRIu64 ":mean%.2f/off%.2f:best%d",
                   reg, reg_bit, on, on_mean, off_mean, bit_active_best_tail[bit]);
        }
        printf("\n");
        printf("  top late r61 pair-state mean-tail gains:");
        for (int k = 0; k < 8; k++) {
            if (top_pair_a[k] < 0) continue;
            int a = top_pair_a[k], b = top_pair_b[k], state = top_pair_state[k];
            int pair_idx2 = a * (late_bits - 1) - (a * (a - 1)) / 2 + (b - a - 1);
            size_t idx = (size_t)pair_idx2 * 4u + (size_t)state;
            uint64_t on = pair_count[idx];
            uint64_t off = d0 - on;
            double on_mean = (double)pair_tail_sum[idx] / (double)on;
            double off_mean = (double)(total_tail_sum - pair_tail_sum[idx]) / (double)off;
            int reg_a = 6 + a / N, bit_a = a % N;
            int reg_b = 6 + b / N, bit_b = b % N;
            printf(" r%d.b%d/r%d.b%d=s%d:on%" PRIu64 ":mean%.2f/off%.2f:best%d",
                   reg_a, bit_a, reg_b, bit_b, state, on, on_mean, off_mean,
                   pair_best_tail[idx]);
        }
        printf("\n");
        if (miner_table) {
            printf("  streaming top-k bucket miner: unique=%" PRIu64 " cap=%" PRIu64
                   " low_threshold<=%d min_count_rate=32 min_count_best=16\n",
                   miner_unique, miner_cap, miner_threshold);
            printf("    top low-rate buckets:");
            for (int k = 0; k < 8; k++) {
                int idx = top_rate_idx[k];
                if (idx < 0) continue;
                miner_bucket_t *b = &miner_table[idx];
                int fam = (int)(b->key >> 56);
                uint32_t low = miner_low_count(b, miner_threshold);
                double rate = (double)low / (double)b->count;
                double mean = (double)b->sum_tail / (double)b->count;
                printf(" [%s key=0x%014" PRIx64 " cnt=%u low=%u rate=%.3f mean=%.2f best=%u]",
                       miner_family_names[fam], b->key & 0x00ffffffffffffffULL,
                       b->count, low, rate, mean, b->best_tail);
            }
            printf("\n");
            printf("    top score buckets:");
            for (int k = 0; k < 8; k++) {
                int idx = top_score_idx[k];
                if (idx < 0) continue;
                miner_bucket_t *b = &miner_table[idx];
                int fam = (int)(b->key >> 56);
                uint32_t low = miner_low_count(b, miner_threshold);
                double rate = (double)low / (double)b->count;
                double mean = (double)b->sum_tail / (double)b->count;
                printf(" [%s key=0x%014" PRIx64 " cnt=%u low=%u rate=%.3f mean=%.2f best=%u score=%.3f]",
                       miner_family_names[fam], b->key & 0x00ffffffffffffffULL,
                       b->count, low, rate, mean, b->best_tail, top_score[k]);
            }
            printf("\n");
            printf("    top best-tail buckets:");
            for (int k = 0; k < 8; k++) {
                int idx = top_best_idx[k];
                if (idx < 0) continue;
                miner_bucket_t *b = &miner_table[idx];
                int fam = (int)(b->key >> 56);
                uint32_t low = miner_low_count(b, miner_threshold);
                double rate = (double)low / (double)b->count;
                double mean = (double)b->sum_tail / (double)b->count;
                printf(" [%s key=0x%014" PRIx64 " cnt=%u low=%u rate=%.3f mean=%.2f best=%u]",
                       miner_family_names[fam], b->key & 0x00ffffffffffffffULL,
                       b->count, low, rate, mean, b->best_tail);
            }
            printf("\n");
        } else {
            printf("  streaming top-k bucket miner: skipped (table cap would be too large)\n");
        }
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
    free(gh_count);
    free(gh_best_tail);
    free(gh_best_r61);
    free(mask_table);
    free(sig_table);
    free(coarse_table);
    free(miner_table);
    free(refine_seeds);
    free(r61_refine_seeds);
    free(repair_seeds);
    free(repair_r61_seeds);
    free(pair_count);
    free(pair_tail_sum);
    free(pair_best_tail);
    return 0;
}
