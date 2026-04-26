/*
 * singular_defect_rank.c
 *
 * Probe the local GF(2) derivative rank of the sr=61 cascade defect map:
 *
 *   D(W57,W58,W59) =
 *       (W2_sched60 - W1_sched60) - cascade_required_offset60 mod 2^32
 *
 * D=0 is the schedule/cascade compatibility event at the sr=61 boundary.
 * A local rank below 32 would be evidence of a lower-rank chamber and a
 * possible structural reduction of the 2^32 barrier.
 *
 * Compile from repo root:
 *   gcc -O3 -march=native -fopenmp -I. \
 *       headline_hunt/bets/singular_chamber_rank/tools/singular_defect_rank.c \
 *       lib/sha256.c -lm -o /tmp/singular_defect_rank
 *
 * Run:
 *   /tmp/singular_defect_rank 512
 *   /tmp/singular_defect_rank newton 1000 8 16
 *   /tmp/singular_defect_rank newtonfixed 0 0x370fef5f 512 8 24
 *   /tmp/singular_defect_rank schedsample 0 0x370fef5f 1000000 22
 *   /tmp/singular_defect_rank reqsample 0 0x370fef5f 0xf0f7e442 1000000 22
 *   /tmp/singular_defect_rank rankfixed58 0 0x370fef5f 0xf0f7e442 1024 8
 *   /tmp/singular_defect_rank defecthill58 0 0x370fef5f 0xf0f7e442 512 8 32
 *   /tmp/singular_defect_rank newtonpoint 0 0x370fef5f 0xf0f7e442 0x76712417 32
 *   /tmp/singular_defect_rank neighpoint 0 0x370fef5f 0xf0f7e442 0x76712417 4
 *   /tmp/singular_defect_rank neighallpoint 0 0x370fef5f 0xf0f7e442 0x76712417 4
 *   /tmp/singular_defect_rank newtonfixed58 0 0x370fef5f 0x12345678 512 8 24
 *   /tmp/singular_defect_rank off59hill 0 0x370fef5f 512 8 32
 *   /tmp/singular_defect_rank off58newton 0x0000000c 256 8 24
 *   /tmp/singular_defect_rank off58hill 64 8 32
 *   /tmp/singular_defect_rank point 0 0x66666666 0x39339339 0x8bb8bb8b
 *   /tmp/singular_defect_rank lift12 0
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "lib/sha256.h"

typedef struct {
    const char *id;
    uint32_t m0;
    uint32_t fill;
    int bit;
} candidate_t;

typedef struct {
    uint32_t key;
    uint32_t count;
    uint32_t first_value;
    uint8_t used;
} sample_bucket_t;

typedef struct {
    int valid;
    uint32_t defect;
    int ch_invisible_bits;
    int maj_a_invisible_bits;
    int maj_b_invisible_bits;
    int maj_c_invisible_bits;
    int defect_hw;
} eval_t;

typedef struct {
    const candidate_t *cand;
    int checked;
    int skipped;
    int rank_hist[33];
    int min_rank;
    uint32_t min_rank_x[3];
    uint32_t min_rank_defect;
    int min_rank_defect_hw;
    int min_rank_ch_inv;
    int min_rank_maj_a_inv;
    int min_defect_hw;
    int min_defect_rank;
    uint32_t min_defect_x[3];
    uint32_t min_defect_value;
    int min_defect_ch_inv;
    int min_defect_maj_a_inv;
    int min_word_rank[3];
    int min_pair_rank_without_word[3];
} summary_t;

static const candidate_t CANDIDATES[] = {
    {"msb_cert_m17149975_ff_bit31", 0x17149975U, 0xffffffffU, 31},
    {"bit19_m51ca0b34_55",         0x51ca0b34U, 0x55555555U, 19},
    {"msb_m9cfea9ce_00",           0x9cfea9ceU, 0x00000000U, 31},
    {"bit20_m294e1ea8_ff",         0x294e1ea8U, 0xffffffffU, 20},
    {"bit28_md1acca79_ff",         0xd1acca79U, 0xffffffffU, 28},
    {"bit28_m3e57289c_ff",         0x3e57289cU, 0xffffffffU, 28},
    {"bit18_m99bf552b_ff",         0x99bf552bU, 0xffffffffU, 18},
    {"bit18_mcbe11dc1_ff",         0xcbe11dc1U, 0xffffffffU, 18},
    {"bit3_m33ec77ca_ff",          0x33ec77caU, 0xffffffffU, 3},
    {"bit3_m5fa301aa_ff",          0x5fa301aaU, 0xffffffffU, 3},
    {"bit1_m6fbc8d8e_ff",          0x6fbc8d8eU, 0xffffffffU, 1},
    {"bit14_m67043cdd_ff",         0x67043cddU, 0xffffffffU, 14},
    {"bit14_mb5541a6e_ff",         0xb5541a6eU, 0xffffffffU, 14},
    {"bit14_m40fde4d2_ff",         0x40fde4d2U, 0xffffffffU, 14},
    {"bit25_ma2f498b1_ff",         0xa2f498b1U, 0xffffffffU, 25},
    {"bit4_m39a03c2d_ff",          0x39a03c2dU, 0xffffffffU, 4},
    {"bit29_m17454e4b_ff",         0x17454e4bU, 0xffffffffU, 29},
    {"bit15_m28c09a5a_ff",         0x28c09a5aU, 0xffffffffU, 15},
};

static inline uint32_t splitmix32(uint64_t *state) {
    uint64_t z = (*state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    z ^= z >> 31;
    return (uint32_t)z;
}

static inline int hw32(uint32_t x) {
    return __builtin_popcount(x);
}

static inline uint32_t cascade1_offset(const uint32_t s1[8], const uint32_t s2[8]) {
    uint32_t dh = s1[7] - s2[7];
    uint32_t dSig1 = sha256_Sigma1(s1[4]) - sha256_Sigma1(s2[4]);
    uint32_t dCh = sha256_Ch(s1[4], s1[5], s1[6]) - sha256_Ch(s2[4], s2[5], s2[6]);
    uint32_t dT2 = (sha256_Sigma0(s1[0]) + sha256_Maj(s1[0], s1[1], s1[2])) -
                   (sha256_Sigma0(s2[0]) + sha256_Maj(s2[0], s2[1], s2[2]));
    return dh + dSig1 + dCh + dT2;
}

static inline void apply_round(uint32_t s[8], uint32_t w, int r) {
    uint32_t a = s[0], b = s[1], c = s[2], d = s[3];
    uint32_t e = s[4], f = s[5], g = s[6], h = s[7];
    uint32_t T1 = h + sha256_Sigma1(e) + sha256_Ch(e, f, g) + sha256_K[r] + w;
    uint32_t T2 = sha256_Sigma0(a) + sha256_Maj(a, b, c);
    s[7] = g;
    s[6] = f;
    s[5] = e;
    s[4] = d + T1;
    s[3] = c;
    s[2] = b;
    s[1] = a;
    s[0] = T1 + T2;
}

static int prepare_candidate(const candidate_t *cand, sha256_precomp_t *p1, sha256_precomp_t *p2) {
    uint32_t M1[16], M2[16];
    uint32_t diff = 1U << cand->bit;
    for (int i = 0; i < 16; i++) {
        M1[i] = cand->fill;
        M2[i] = cand->fill;
    }
    M1[0] = cand->m0;
    M2[0] = cand->m0 ^ diff;
    M2[9] = cand->fill ^ diff;
    sha256_precompute(M1, p1);
    sha256_precompute(M2, p2);
    return p1->state[0] == p2->state[0];
}

static eval_t eval_defect(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                          const uint32_t x[3]) {
    uint32_t s1[8], s2[8];
    memcpy(s1, p1->state, sizeof(s1));
    memcpy(s2, p2->state, sizeof(s2));

    for (int i = 0; i < 3; i++) {
        uint32_t off = cascade1_offset(s1, s2);
        uint32_t w1 = x[i];
        uint32_t w2 = w1 + off;
        apply_round(s1, w1, 57 + i);
        apply_round(s2, w2, 57 + i);
    }

    uint32_t w1_sched60 = sha256_sigma1(x[1]) + p1->W[53] + sha256_sigma0(p1->W[45]) + p1->W[44];
    uint32_t w2_58 = x[1] + 0; /* overwritten below by replaying the r=58 offset is not needed:
                                * x[1] is W1[58], but W2[58] is not x[1]. */

    /* Recompute W2[58] cheaply by replaying only offsets up to r=58. This keeps
     * D exact without storing the intermediate words in eval_defect's first loop. */
    uint32_t t1[8], t2[8];
    memcpy(t1, p1->state, sizeof(t1));
    memcpy(t2, p2->state, sizeof(t2));
    uint32_t off57 = cascade1_offset(t1, t2);
    apply_round(t1, x[0], 57);
    apply_round(t2, x[0] + off57, 57);
    uint32_t off58 = cascade1_offset(t1, t2);
    w2_58 = x[1] + off58;

    uint32_t w2_sched60 = sha256_sigma1(w2_58) + p2->W[53] + sha256_sigma0(p2->W[45]) + p2->W[44];
    uint32_t sched_offset60 = w2_sched60 - w1_sched60;
    uint32_t req_offset60 = cascade1_offset(s1, s2);
    uint32_t defect = sched_offset60 - req_offset60;

    uint32_t both_ch_fg_eq = ~(s1[5] ^ s1[6]) & ~(s2[5] ^ s2[6]);
    uint32_t both_maj_bc_eq = ~(s1[1] ^ s1[2]) & ~(s2[1] ^ s2[2]);
    uint32_t both_maj_ac_eq = ~(s1[0] ^ s1[2]) & ~(s2[0] ^ s2[2]);
    uint32_t both_maj_ab_eq = ~(s1[0] ^ s1[1]) & ~(s2[0] ^ s2[1]);

    eval_t out;
    out.valid = 1;
    out.defect = defect;
    out.ch_invisible_bits = hw32(both_ch_fg_eq);
    out.maj_a_invisible_bits = hw32(both_maj_bc_eq);
    out.maj_b_invisible_bits = hw32(both_maj_ac_eq);
    out.maj_c_invisible_bits = hw32(both_maj_ab_eq);
    out.defect_hw = hw32(defect);
    return out;
}

static int rank32_vectors(const uint32_t *vecs, int n) {
    uint32_t basis[32];
    memset(basis, 0, sizeof(basis));
    int rank = 0;
    for (int i = 0; i < n; i++) {
        uint32_t v = vecs[i];
        for (int b = 31; b >= 0 && v; b--) {
            if (((v >> b) & 1U) == 0) continue;
            if (basis[b]) {
                v ^= basis[b];
            } else {
                basis[b] = v;
                rank++;
                break;
            }
        }
    }
    return rank;
}

static int solve_linear_columns(uint32_t target, const uint32_t *cols, int ncols,
                                uint64_t *solution, int *rank_out) {
    uint32_t basis[32];
    uint64_t combo[32];
    memset(basis, 0, sizeof(basis));
    memset(combo, 0, sizeof(combo));
    int rank = 0;

    for (int i = 0; i < ncols; i++) {
        uint32_t v = cols[i];
        uint64_t c = 1ULL << i;
        for (int b = 31; b >= 0 && v; b--) {
            if (((v >> b) & 1U) == 0) continue;
            if (basis[b]) {
                v ^= basis[b];
                c ^= combo[b];
            } else {
                basis[b] = v;
                combo[b] = c;
                rank++;
                break;
            }
        }
    }

    uint32_t t = target;
    uint64_t sol = 0;
    for (int b = 31; b >= 0 && t; b--) {
        if (((t >> b) & 1U) == 0) continue;
        if (!basis[b]) {
            if (rank_out) *rank_out = rank;
            return 0;
        }
        t ^= basis[b];
        sol ^= combo[b];
    }

    if (rank_out) *rank_out = rank;
    *solution = sol;
    return 1;
}

static int defect_newton_once(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                              uint32_t x[3], int max_iters, int *iters_out,
                              int *last_rank_out, uint32_t *last_defect_out) {
    for (int iter = 0; iter < max_iters; iter++) {
        eval_t base = eval_defect(p1, p2, x);
        if (base.defect == 0) {
            if (iters_out) *iters_out = iter;
            if (last_rank_out) *last_rank_out = 32;
            if (last_defect_out) *last_defect_out = 0;
            return 1;
        }

        uint32_t cols[64];
        for (int word = 1; word <= 2; word++) {
            for (int bit = 0; bit < 32; bit++) {
                uint32_t xf[3] = {x[0], x[1], x[2]};
                xf[word] ^= 1U << bit;
                eval_t y = eval_defect(p1, p2, xf);
                cols[(word - 1) * 32 + bit] = base.defect ^ y.defect;
            }
        }

        uint64_t delta = 0;
        int rank = 0;
        int solvable = solve_linear_columns(base.defect, cols, 64, &delta, &rank);
        if (last_rank_out) *last_rank_out = rank;
        if (last_defect_out) *last_defect_out = base.defect;
        if (!solvable) {
            if (iters_out) *iters_out = iter;
            return 0;
        }

        uint32_t old1 = x[1], old2 = x[2];
        for (int bit = 0; bit < 32; bit++) {
            if ((delta >> bit) & 1ULL) x[1] ^= 1U << bit;
            if ((delta >> (32 + bit)) & 1ULL) x[2] ^= 1U << bit;
        }

        if (x[1] == old1 && x[2] == old2) {
            if (iters_out) *iters_out = iter;
            return 0;
        }
    }

    eval_t last = eval_defect(p1, p2, x);
    if (iters_out) *iters_out = max_iters;
    if (last_defect_out) *last_defect_out = last.defect;
    return last.defect == 0;
}

static uint32_t compute_off58_for_w57(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                                      uint32_t w57) {
    uint32_t s1[8], s2[8];
    memcpy(s1, p1->state, sizeof(s1));
    memcpy(s2, p2->state, sizeof(s2));
    uint32_t off57 = cascade1_offset(s1, s2);
    apply_round(s1, w57, 57);
    apply_round(s2, w57 + off57, 57);
    return cascade1_offset(s1, s2);
}

static uint32_t sched_offset60_for_w57_w58(const sha256_precomp_t *p1,
                                           const sha256_precomp_t *p2,
                                           uint32_t w57, uint32_t w58,
                                           uint32_t *off58_out) {
    uint32_t s1[8], s2[8];
    memcpy(s1, p1->state, sizeof(s1));
    memcpy(s2, p2->state, sizeof(s2));
    uint32_t off57 = cascade1_offset(s1, s2);
    apply_round(s1, w57, 57);
    apply_round(s2, w57 + off57, 57);
    uint32_t off58 = cascade1_offset(s1, s2);
    if (off58_out) *off58_out = off58;
    uint32_t w2_58 = w58 + off58;
    uint32_t w1_sched60 = sha256_sigma1(w58) + p1->W[53] +
                           sha256_sigma0(p1->W[45]) + p1->W[44];
    uint32_t w2_sched60 = sha256_sigma1(w2_58) + p2->W[53] +
                           sha256_sigma0(p2->W[45]) + p2->W[44];
    return w2_sched60 - w1_sched60;
}

static void prepare_state_after_58(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                                   uint32_t w57, uint32_t w58,
                                   uint32_t s1_58[8], uint32_t s2_58[8],
                                   uint32_t *off58_out, uint32_t *off59_out) {
    memcpy(s1_58, p1->state, 8 * sizeof(uint32_t));
    memcpy(s2_58, p2->state, 8 * sizeof(uint32_t));
    uint32_t off57 = cascade1_offset(s1_58, s2_58);
    apply_round(s1_58, w57, 57);
    apply_round(s2_58, w57 + off57, 57);
    uint32_t off58 = cascade1_offset(s1_58, s2_58);
    apply_round(s1_58, w58, 58);
    apply_round(s2_58, w58 + off58, 58);
    if (off58_out) *off58_out = off58;
    if (off59_out) *off59_out = cascade1_offset(s1_58, s2_58);
}

static uint32_t req_offset60_from_state58(const uint32_t s1_58_base[8],
                                          const uint32_t s2_58_base[8],
                                          uint32_t off59, uint32_t w59) {
    uint32_t s1[8], s2[8];
    memcpy(s1, s1_58_base, 8 * sizeof(uint32_t));
    memcpy(s2, s2_58_base, 8 * sizeof(uint32_t));
    apply_round(s1, w59, 59);
    apply_round(s2, w59 + off59, 59);
    return cascade1_offset(s1, s2);
}

static uint32_t compute_off59_for_w57_w58(const sha256_precomp_t *p1,
                                          const sha256_precomp_t *p2,
                                          uint32_t w57, uint32_t w58,
                                          uint32_t *off58_out) {
    uint32_t s1_58[8], s2_58[8], off59 = 0;
    prepare_state_after_58(p1, p2, w57, w58, s1_58, s2_58, off58_out, &off59);
    return off59;
}

static int off58_newton_once(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                             uint32_t target, uint32_t *w57_io, int max_iters,
                             int *iters_out, int *last_rank_out,
                             uint32_t *last_off58_out) {
    uint32_t w57 = *w57_io;
    for (int iter = 0; iter < max_iters; iter++) {
        uint32_t off58 = compute_off58_for_w57(p1, p2, w57);
        if (off58 == target) {
            *w57_io = w57;
            if (iters_out) *iters_out = iter;
            if (last_rank_out) *last_rank_out = 32;
            if (last_off58_out) *last_off58_out = off58;
            return 1;
        }

        uint32_t cols[32];
        for (int bit = 0; bit < 32; bit++) {
            uint32_t off_flip = compute_off58_for_w57(p1, p2, w57 ^ (1U << bit));
            cols[bit] = off58 ^ off_flip;
        }

        uint64_t delta = 0;
        int rank = 0;
        int solvable = solve_linear_columns(off58 ^ target, cols, 32, &delta, &rank);
        if (last_rank_out) *last_rank_out = rank;
        if (last_off58_out) *last_off58_out = off58;
        if (!solvable || delta == 0) {
            *w57_io = w57;
            if (iters_out) *iters_out = iter;
            return 0;
        }

        w57 ^= (uint32_t)delta;
    }

    *w57_io = w57;
    if (iters_out) *iters_out = max_iters;
    if (last_off58_out) *last_off58_out = compute_off58_for_w57(p1, p2, w57);
    return *last_off58_out == target;
}

static int local_defect_rank(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                             const uint32_t x[3], eval_t *base_out,
                             int word_rank[3], int pair_rank_without_word[3]) {
    uint32_t vecs[96];
    eval_t base = eval_defect(p1, p2, x);
    if (base_out) *base_out = base;
    for (int word = 0; word < 3; word++) {
        for (int bit = 0; bit < 32; bit++) {
            uint32_t xf[3] = {x[0], x[1], x[2]};
            xf[word] ^= 1U << bit;
            eval_t y = eval_defect(p1, p2, xf);
            vecs[word * 32 + bit] = base.defect ^ y.defect;
        }
    }
    if (word_rank) {
        for (int word = 0; word < 3; word++) {
            word_rank[word] = rank32_vectors(&vecs[word * 32], 32);
        }
    }
    if (pair_rank_without_word) {
        uint32_t pair_vecs[64];
        for (int missing = 0; missing < 3; missing++) {
            int n = 0;
            for (int word = 0; word < 3; word++) {
                if (word == missing) continue;
                for (int bit = 0; bit < 32; bit++) {
                    pair_vecs[n++] = vecs[word * 32 + bit];
                }
            }
            pair_rank_without_word[missing] = rank32_vectors(pair_vecs, 64);
        }
    }
    return rank32_vectors(vecs, 96);
}

static void init_summary(summary_t *s, const candidate_t *cand) {
    memset(s, 0, sizeof(*s));
    s->cand = cand;
    s->min_rank = 99;
    s->min_defect_hw = 99;
    s->min_defect_rank = 99;
    for (int i = 0; i < 3; i++) {
        s->min_word_rank[i] = 99;
        s->min_pair_rank_without_word[i] = 99;
    }
}

static void merge_summary(summary_t *dst, const summary_t *src) {
    dst->checked += src->checked;
    dst->skipped += src->skipped;
    for (int i = 0; i <= 32; i++) dst->rank_hist[i] += src->rank_hist[i];
    if (src->min_rank < dst->min_rank) {
        dst->min_rank = src->min_rank;
        memcpy(dst->min_rank_x, src->min_rank_x, sizeof(dst->min_rank_x));
        dst->min_rank_defect = src->min_rank_defect;
        dst->min_rank_defect_hw = src->min_rank_defect_hw;
        dst->min_rank_ch_inv = src->min_rank_ch_inv;
        dst->min_rank_maj_a_inv = src->min_rank_maj_a_inv;
    }
    if (src->min_defect_hw < dst->min_defect_hw) {
        dst->min_defect_hw = src->min_defect_hw;
        dst->min_defect_rank = src->min_defect_rank;
        memcpy(dst->min_defect_x, src->min_defect_x, sizeof(dst->min_defect_x));
        dst->min_defect_value = src->min_defect_value;
        dst->min_defect_ch_inv = src->min_defect_ch_inv;
        dst->min_defect_maj_a_inv = src->min_defect_maj_a_inv;
    }
    for (int i = 0; i < 3; i++) {
        if (src->min_word_rank[i] < dst->min_word_rank[i]) {
            dst->min_word_rank[i] = src->min_word_rank[i];
        }
        if (src->min_pair_rank_without_word[i] < dst->min_pair_rank_without_word[i]) {
            dst->min_pair_rank_without_word[i] = src->min_pair_rank_without_word[i];
        }
    }
}

static void probe_candidate(const candidate_t *cand, int samples, int threads) {
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n", cand->id);
        return;
    }

    summary_t total;
    init_summary(&total, cand);

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        summary_t local;
        init_summary(&local, cand);
        uint64_t rng = 0x123456789abcdef0ULL ^
                       ((uint64_t)cand->m0 << 17) ^
                       ((uint64_t)cand->fill << 1) ^
                       ((uint64_t)cand->bit << 48) ^
                       (uint64_t)tid;

        #pragma omp for schedule(dynamic, 16)
        for (int i = 0; i < samples; i++) {
            uint32_t x[3] = {
                splitmix32(&rng),
                splitmix32(&rng),
                splitmix32(&rng)
            };

            /* Add a few structured chamber seeds at the beginning. They are
             * deliberately simple fill-like points, not a search over hours. */
            static const uint32_t patterns[] = {
                0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
            };
            if (i < 8) {
                x[0] = patterns[i];
                x[1] = patterns[(i + 3) & 7];
                x[2] = patterns[(i + 5) & 7];
            }

            eval_t base;
            int word_rank[3], pair_rank_without_word[3];
            int rank = local_defect_rank(&p1, &p2, x, &base, word_rank, pair_rank_without_word);
            local.checked++;
            if (rank >= 0 && rank <= 32) local.rank_hist[rank]++;
            for (int j = 0; j < 3; j++) {
                if (word_rank[j] < local.min_word_rank[j]) {
                    local.min_word_rank[j] = word_rank[j];
                }
                if (pair_rank_without_word[j] < local.min_pair_rank_without_word[j]) {
                    local.min_pair_rank_without_word[j] = pair_rank_without_word[j];
                }
            }
            if (rank < local.min_rank) {
                local.min_rank = rank;
                memcpy(local.min_rank_x, x, sizeof(local.min_rank_x));
                local.min_rank_defect = base.defect;
                local.min_rank_defect_hw = base.defect_hw;
                local.min_rank_ch_inv = base.ch_invisible_bits;
                local.min_rank_maj_a_inv = base.maj_a_invisible_bits;
            }
            if (base.defect_hw < local.min_defect_hw) {
                local.min_defect_hw = base.defect_hw;
                local.min_defect_rank = rank;
                memcpy(local.min_defect_x, x, sizeof(local.min_defect_x));
                local.min_defect_value = base.defect;
                local.min_defect_ch_inv = base.ch_invisible_bits;
                local.min_defect_maj_a_inv = base.maj_a_invisible_bits;
            }
        }

        #pragma omp critical
        merge_summary(&total, &local);
    }

    printf("{\"candidate\":\"%s\",\"m0\":\"0x%08x\",\"fill\":\"0x%08x\",\"bit\":%d,"
           "\"samples\":%d,\"min_rank\":%d,\"rank32\":%d,\"rank31\":%d,\"rank30_or_less\":%d,"
           "\"min_word_rank\":[%d,%d,%d],\"min_pair_rank_without_word\":[%d,%d,%d],"
           "\"min_rank_defect\":\"0x%08x\",\"min_rank_defect_hw\":%d,"
           "\"min_rank_ch_inv\":%d,\"min_rank_maj_a_inv\":%d,"
           "\"min_defect_hw\":%d,\"min_defect_rank\":%d,\"min_defect\":\"0x%08x\","
           "\"min_defect_ch_inv\":%d,\"min_defect_maj_a_inv\":%d,"
           "\"min_rank_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"min_defect_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, cand->m0, cand->fill, cand->bit,
           total.checked, total.min_rank, total.rank_hist[32], total.rank_hist[31],
           total.checked - total.rank_hist[32] - total.rank_hist[31],
           total.min_word_rank[0], total.min_word_rank[1], total.min_word_rank[2],
           total.min_pair_rank_without_word[0], total.min_pair_rank_without_word[1],
           total.min_pair_rank_without_word[2],
           total.min_rank_defect, total.min_rank_defect_hw,
           total.min_rank_ch_inv, total.min_rank_maj_a_inv,
           total.min_defect_hw, total.min_defect_rank, total.min_defect_value,
           total.min_defect_ch_inv, total.min_defect_maj_a_inv,
           total.min_rank_x[0], total.min_rank_x[1], total.min_rank_x[2],
           total.min_defect_x[0], total.min_defect_x[1], total.min_defect_x[2]);
}

static void newton_candidate(const candidate_t *cand, int trials, int threads, int max_iters) {
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n", cand->id);
        return;
    }

    int successes = 0;
    int rank_fail = 0;
    int total_iters_success = 0;
    int best_final_hw = 99;
    uint32_t best_final_defect = 0;
    uint32_t first_success_x[3] = {0, 0, 0};
    int first_success_iters = -1;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xfedcba9876543210ULL ^
                       ((uint64_t)cand->m0 << 9) ^
                       ((uint64_t)cand->fill << 3) ^
                       ((uint64_t)cand->bit << 43) ^
                       (uint64_t)tid;

        int local_successes = 0;
        int local_rank_fail = 0;
        int local_iters = 0;
        int local_best_hw = 99;
        uint32_t local_best_defect = 0;
        uint32_t local_first_x[3] = {0, 0, 0};
        int local_first_iters = -1;

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3] = {
                splitmix32(&rng),
                splitmix32(&rng),
                splitmix32(&rng)
            };
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                x[0] = patterns[i];
                x[1] = patterns[(i + 3) & 7];
                x[2] = patterns[(i + 5) & 7];
            }

            int iters = 0, last_rank = 0;
            uint32_t last_defect = 0;
            int ok = defect_newton_once(&p1, &p2, x, max_iters, &iters, &last_rank, &last_defect);
            if (ok) {
                local_successes++;
                local_iters += iters;
                if (local_first_iters < 0) {
                    local_first_iters = iters;
                    memcpy(local_first_x, x, sizeof(local_first_x));
                }
            } else {
                if (last_rank < 32) local_rank_fail++;
                int h = hw32(last_defect);
                if (h < local_best_hw) {
                    local_best_hw = h;
                    local_best_defect = last_defect;
                }
            }
        }

        #pragma omp critical
        {
            successes += local_successes;
            rank_fail += local_rank_fail;
            total_iters_success += local_iters;
            if (local_best_hw < best_final_hw) {
                best_final_hw = local_best_hw;
                best_final_defect = local_best_defect;
            }
            if (first_success_iters < 0 && local_first_iters >= 0) {
                first_success_iters = local_first_iters;
                memcpy(first_success_x, local_first_x, sizeof(first_success_x));
            }
        }
    }

    double avg_iters = successes ? (double)total_iters_success / (double)successes : 0.0;
    printf("{\"mode\":\"newton\",\"candidate\":\"%s\",\"m0\":\"0x%08x\",\"fill\":\"0x%08x\","
           "\"bit\":%d,\"trials\":%d,\"max_iters\":%d,\"successes\":%d,"
           "\"success_rate\":%.6f,\"avg_success_iters\":%.3f,\"rank_failures\":%d,"
           "\"best_final_hw\":%d,\"best_final_defect\":\"0x%08x\","
           "\"first_success_iters\":%d,\"first_success_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, cand->m0, cand->fill, cand->bit, trials, max_iters,
           successes, trials ? (double)successes / (double)trials : 0.0,
           avg_iters, rank_fail, best_final_hw, best_final_defect,
           first_success_iters, first_success_x[0], first_success_x[1], first_success_x[2]);
}

static void off58_newton_candidate(const candidate_t *cand, uint32_t target,
                                   int trials, int threads, int max_iters) {
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"off58newton\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    int successes = 0;
    int total_success_iters = 0;
    int rank_failures = 0;
    int best_hw = 99;
    uint32_t best_off58 = 0;
    uint32_t first_w57 = 0;
    int first_iters = -1;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x0f1e2d3c4b5a6978ULL ^
                       ((uint64_t)cand->m0 << 11) ^
                       ((uint64_t)cand->fill << 5) ^
                       ((uint64_t)cand->bit << 41) ^
                       (uint64_t)tid;
        int local_successes = 0;
        int local_iters = 0;
        int local_rank_failures = 0;
        int local_best_hw = 99;
        uint32_t local_best_off58 = 0;
        uint32_t local_first_w57 = 0;
        int local_first_iters = -1;

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t w57 = splitmix32(&rng);
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                w57 = patterns[i];
            }

            int iters = 0;
            int last_rank = 0;
            uint32_t last_off58 = 0;
            int ok = off58_newton_once(&p1, &p2, target, &w57, max_iters,
                                       &iters, &last_rank, &last_off58);
            if (ok) {
                local_successes++;
                local_iters += iters;
                if (local_first_iters < 0) {
                    local_first_iters = iters;
                    local_first_w57 = w57;
                }
            } else {
                if (last_rank < 32) local_rank_failures++;
                int h = hw32(last_off58 ^ target);
                if (h < local_best_hw) {
                    local_best_hw = h;
                    local_best_off58 = last_off58;
                }
            }
        }

        #pragma omp critical
        {
            successes += local_successes;
            total_success_iters += local_iters;
            rank_failures += local_rank_failures;
            if (local_best_hw < best_hw) {
                best_hw = local_best_hw;
                best_off58 = local_best_off58;
            }
            if (first_iters < 0 && local_first_iters >= 0) {
                first_iters = local_first_iters;
                first_w57 = local_first_w57;
            }
        }
    }

    printf("{\"mode\":\"off58newton\",\"candidate\":\"%s\",\"m0\":\"0x%08x\","
           "\"fill\":\"0x%08x\",\"bit\":%d,\"target\":\"0x%08x\","
           "\"trials\":%d,\"max_iters\":%d,\"successes\":%d,"
           "\"success_rate\":%.6f,\"avg_success_iters\":%.3f,"
           "\"rank_failures\":%d,\"first_iters\":%d,\"first_w57\":\"0x%08x\","
           "\"best_miss_hw\":%d,\"best_miss_off58\":\"0x%08x\"}\n",
           cand->id, cand->m0, cand->fill, cand->bit, target,
           trials, max_iters, successes,
           trials ? (double)successes / (double)trials : 0.0,
           successes ? (double)total_success_iters / (double)successes : 0.0,
           rank_failures, first_iters, first_w57, best_hw, best_off58);
}

static void off58_hill_candidate(const candidate_t *cand, int trials, int threads, int max_passes) {
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"off58hill\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    int best_hw = 99;
    uint32_t best_off58 = 0;
    uint32_t best_w57 = 0;
    int best_passes = 0;
    int total_evals = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xfeedfacecafebeefULL ^
                       ((uint64_t)cand->m0 << 13) ^
                       ((uint64_t)cand->fill << 7) ^
                       ((uint64_t)cand->bit << 39) ^
                       (uint64_t)tid;
        int local_best_hw = 99;
        uint32_t local_best_off58 = 0;
        uint32_t local_best_w57 = 0;
        int local_best_passes = 0;
        int local_evals = 0;

        #pragma omp for schedule(dynamic, 4)
        for (int i = 0; i < trials; i++) {
            uint32_t w57 = splitmix32(&rng);
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                w57 = patterns[i];
            }

            uint32_t off58 = compute_off58_for_w57(&p1, &p2, w57);
            local_evals++;
            int cur_hw = hw32(off58);
            int passes_used = 0;

            for (int pass = 0; pass < max_passes && cur_hw > 0; pass++) {
                uint32_t best_step_w57 = w57;
                uint32_t best_step_off58 = off58;
                int best_step_hw = cur_hw;

                for (int bit = 0; bit < 32; bit++) {
                    uint32_t wf = w57 ^ (1U << bit);
                    uint32_t of = compute_off58_for_w57(&p1, &p2, wf);
                    local_evals++;
                    int h = hw32(of);
                    if (h < best_step_hw ||
                        (h == best_step_hw && of < best_step_off58)) {
                        best_step_hw = h;
                        best_step_w57 = wf;
                        best_step_off58 = of;
                    }
                }

                if (best_step_hw >= cur_hw) break;
                w57 = best_step_w57;
                off58 = best_step_off58;
                cur_hw = best_step_hw;
                passes_used = pass + 1;
            }

            if (cur_hw < local_best_hw ||
                (cur_hw == local_best_hw && off58 < local_best_off58)) {
                local_best_hw = cur_hw;
                local_best_off58 = off58;
                local_best_w57 = w57;
                local_best_passes = passes_used;
            }
        }

        #pragma omp critical
        {
            total_evals += local_evals;
            if (local_best_hw < best_hw ||
                (local_best_hw == best_hw && local_best_off58 < best_off58)) {
                best_hw = local_best_hw;
                best_off58 = local_best_off58;
                best_w57 = local_best_w57;
                best_passes = local_best_passes;
            }
        }
    }

    printf("{\"mode\":\"off58hill\",\"candidate\":\"%s\",\"m0\":\"0x%08x\","
           "\"fill\":\"0x%08x\",\"bit\":%d,\"trials\":%d,\"max_passes\":%d,"
           "\"best_hw\":%d,\"best_off58\":\"0x%08x\",\"best_w57\":\"0x%08x\","
           "\"best_passes\":%d,\"evals\":%d}\n",
           cand->id, cand->m0, cand->fill, cand->bit, trials, max_passes,
           best_hw, best_off58, best_w57, best_passes, total_evals);
}

static void newton_fixed_w57_candidate(int idx, uint32_t fixed_w57,
                                       int trials, int threads, int max_iters) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"newtonfixed\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58 = compute_off58_for_w57(&p1, &p2, fixed_w57);
    int successes = 0;
    int total_success_iters = 0;
    int rank_failures = 0;
    int best_final_hw = 99;
    uint32_t best_final_defect = 0;
    uint32_t best_x[3] = {fixed_w57, 0, 0};
    uint32_t first_success_x[3] = {fixed_w57, 0, 0};
    int first_success_iters = -1;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xa55a1234fedc9876ULL ^
                       ((uint64_t)cand->m0 << 15) ^
                       ((uint64_t)fixed_w57 << 1) ^
                       (uint64_t)tid;

        int local_successes = 0;
        int local_iters = 0;
        int local_rank_failures = 0;
        int local_best_hw = 99;
        uint32_t local_best_defect = 0;
        uint32_t local_best_x[3] = {fixed_w57, 0, 0};
        uint32_t local_first_x[3] = {fixed_w57, 0, 0};
        int local_first_iters = -1;

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3] = {
                fixed_w57,
                splitmix32(&rng),
                splitmix32(&rng)
            };
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                x[1] = patterns[(i + 3) & 7];
                x[2] = patterns[(i + 5) & 7];
            }

            int iters = 0, last_rank = 0;
            uint32_t last_defect = 0;
            int ok = defect_newton_once(&p1, &p2, x, max_iters, &iters,
                                        &last_rank, &last_defect);
            if (ok) {
                local_successes++;
                local_iters += iters;
                if (local_first_iters < 0) {
                    local_first_iters = iters;
                    memcpy(local_first_x, x, sizeof(local_first_x));
                }
            } else {
                if (last_rank < 32) local_rank_failures++;
                int h = hw32(last_defect);
                if (h < local_best_hw) {
                    local_best_hw = h;
                    local_best_defect = last_defect;
                    memcpy(local_best_x, x, sizeof(local_best_x));
                }
            }
        }

        #pragma omp critical
        {
            successes += local_successes;
            total_success_iters += local_iters;
            rank_failures += local_rank_failures;
            if (local_best_hw < best_final_hw) {
                best_final_hw = local_best_hw;
                best_final_defect = local_best_defect;
                memcpy(best_x, local_best_x, sizeof(best_x));
            }
            if (first_success_iters < 0 && local_first_iters >= 0) {
                first_success_iters = local_first_iters;
                memcpy(first_success_x, local_first_x, sizeof(first_success_x));
            }
        }
    }

    printf("{\"mode\":\"newtonfixed\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"m0\":\"0x%08x\",\"fill\":\"0x%08x\",\"bit\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"trials\":%d,\"max_iters\":%d,\"successes\":%d,"
           "\"success_rate\":%.6f,\"avg_success_iters\":%.3f,"
           "\"rank_failures\":%d,\"best_final_hw\":%d,"
           "\"best_final_defect\":\"0x%08x\","
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"first_success_iters\":%d,"
           "\"first_success_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx, cand->m0, cand->fill, cand->bit,
           fixed_w57, off58, hw32(off58),
           trials, max_iters, successes,
           trials ? (double)successes / (double)trials : 0.0,
           successes ? (double)total_success_iters / (double)successes : 0.0,
           rank_failures, best_final_hw, best_final_defect,
           best_x[0], best_x[1], best_x[2],
           first_success_iters,
           first_success_x[0], first_success_x[1], first_success_x[2]);
}

static uint32_t sample_insert_with_first(sample_bucket_t *table, uint32_t table_mask,
                                         uint32_t key, uint32_t first_value,
                                         uint32_t *unique) {
    uint32_t pos = (key * 2654435761U) & table_mask;
    while (table[pos].used && table[pos].key != key) {
        pos = (pos + 1U) & table_mask;
    }
    if (!table[pos].used) {
        table[pos].used = 1;
        table[pos].key = key;
        table[pos].first_value = first_value;
        table[pos].count = 1;
        (*unique)++;
        return 1;
    }
    table[pos].count++;
    return table[pos].count;
}

static void sched_sample_candidate(int idx, uint32_t fixed_w57,
                                   uint32_t samples, int table_bits) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (table_bits < 10) table_bits = 10;
    if (table_bits > 28) table_bits = 28;
    uint32_t table_size = 1U << table_bits;
    sample_bucket_t *table = calloc((size_t)table_size, sizeof(sample_bucket_t));
    if (!table) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"schedsample\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        free(table);
        return;
    }

    uint32_t off58 = compute_off58_for_w57(&p1, &p2, fixed_w57);
    uint64_t rng = 0x51ced15ca11ab1e5ULL ^ ((uint64_t)fixed_w57 << 19) ^ (uint64_t)cand->m0;
    uint32_t unique = 0;
    uint32_t max_count = 0;
    uint32_t max_key = 0;
    uint32_t max_first = 0;
    uint32_t table_mask = table_size - 1U;

    for (uint32_t i = 0; i < samples; i++) {
        uint32_t w58 = splitmix32(&rng);
        uint32_t sched = sched_offset60_for_w57_w58(&p1, &p2, fixed_w57, w58, NULL);
        uint32_t c = sample_insert_with_first(table, table_mask, sched, w58, &unique);
        if (c > max_count) {
            max_count = c;
            max_key = sched;
            max_first = w58;
        }
    }

    uint32_t top_key[16], top_count[16], top_first[16];
    memset(top_key, 0, sizeof(top_key));
    memset(top_count, 0, sizeof(top_count));
    memset(top_first, 0, sizeof(top_first));
    for (uint32_t i = 0; i < table_size; i++) {
        if (!table[i].used) continue;
        uint32_t c = table[i].count;
        for (int k = 0; k < 16; k++) {
            if (c > top_count[k]) {
                for (int j = 15; j > k; j--) {
                    top_count[j] = top_count[j - 1];
                    top_key[j] = top_key[j - 1];
                    top_first[j] = top_first[j - 1];
                }
                top_count[k] = c;
                top_key[k] = table[i].key;
                top_first[k] = table[i].first_value;
                break;
            }
        }
    }

    printf("{\"mode\":\"schedsample\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"samples\":%u,\"unique_sched\":%u,\"unique_rate\":%.9f,"
           "\"max_sched\":\"0x%08x\",\"max_count\":%u,\"max_first_w58\":\"0x%08x\","
           "\"top\":[",
           cand->id, idx, fixed_w57, off58, hw32(off58),
           samples, unique, samples ? (double)unique / (double)samples : 0.0,
           max_key, max_count, max_first);
    for (int i = 0; i < 16; i++) {
        if (i) printf(",");
        printf("{\"sched\":\"0x%08x\",\"count\":%u,\"first_w58\":\"0x%08x\"}",
               top_key[i], top_count[i], top_first[i]);
    }
    printf("]}\n");
    free(table);
}

static void req_sample_candidate(int idx, uint32_t fixed_w57, uint32_t fixed_w58,
                                 uint32_t samples, int table_bits) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (table_bits < 10) table_bits = 10;
    if (table_bits > 28) table_bits = 28;
    uint32_t table_size = 1U << table_bits;
    sample_bucket_t *table = calloc((size_t)table_size, sizeof(sample_bucket_t));
    if (!table) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"reqsample\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        free(table);
        return;
    }

    uint32_t off58 = 0, off59 = 0;
    uint32_t s1_58[8], s2_58[8];
    prepare_state_after_58(&p1, &p2, fixed_w57, fixed_w58,
                           s1_58, s2_58, &off58, &off59);
    uint32_t sched = sched_offset60_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, NULL);

    uint64_t rng = 0xdecafbad12345678ULL ^
                   ((uint64_t)fixed_w57 << 9) ^
                   ((uint64_t)fixed_w58 << 21) ^
                   (uint64_t)cand->m0;
    uint32_t unique = 0;
    uint32_t target_hits = 0;
    uint32_t max_count = 0;
    uint32_t max_key = 0;
    uint32_t max_first = 0;
    uint32_t table_mask = table_size - 1U;

    for (uint32_t i = 0; i < samples; i++) {
        uint32_t w59 = splitmix32(&rng);
        uint32_t req = req_offset60_from_state58(s1_58, s2_58, off59, w59);
        if (req == sched) target_hits++;
        uint32_t c = sample_insert_with_first(table, table_mask, req, w59, &unique);
        if (c > max_count) {
            max_count = c;
            max_key = req;
            max_first = w59;
        }
    }

    uint32_t target_count = 0;
    uint32_t pos = (sched * 2654435761U) & table_mask;
    while (table[pos].used) {
        if (table[pos].key == sched) {
            target_count = table[pos].count;
            break;
        }
        pos = (pos + 1U) & table_mask;
    }

    uint32_t top_key[16], top_count[16], top_first[16];
    memset(top_key, 0, sizeof(top_key));
    memset(top_count, 0, sizeof(top_count));
    memset(top_first, 0, sizeof(top_first));
    for (uint32_t i = 0; i < table_size; i++) {
        if (!table[i].used) continue;
        uint32_t c = table[i].count;
        for (int k = 0; k < 16; k++) {
            if (c > top_count[k]) {
                for (int j = 15; j > k; j--) {
                    top_count[j] = top_count[j - 1];
                    top_key[j] = top_key[j - 1];
                    top_first[j] = top_first[j - 1];
                }
                top_count[k] = c;
                top_key[k] = table[i].key;
                top_first[k] = table[i].first_value;
                break;
            }
        }
    }

    printf("{\"mode\":\"reqsample\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"fixed_w58\":\"0x%08x\","
           "\"off58\":\"0x%08x\",\"off58_hw\":%d,\"off59\":\"0x%08x\",\"off59_hw\":%d,"
           "\"sched_offset60\":\"0x%08x\",\"samples\":%u,"
           "\"unique_req\":%u,\"unique_rate\":%.9f,"
           "\"target_hits\":%u,\"target_rate\":%.9f,\"target_table_count\":%u,"
           "\"max_req\":\"0x%08x\",\"max_count\":%u,\"max_first_w59\":\"0x%08x\","
           "\"top\":[",
           cand->id, idx, fixed_w57, fixed_w58,
           off58, hw32(off58), off59, hw32(off59),
           sched, samples, unique, samples ? (double)unique / (double)samples : 0.0,
           target_hits, samples ? (double)target_hits / (double)samples : 0.0,
           target_count, max_key, max_count, max_first);
    for (int i = 0; i < 16; i++) {
        if (i) printf(",");
        printf("{\"req\":\"0x%08x\",\"count\":%u,\"first_w59\":\"0x%08x\"}",
               top_key[i], top_count[i], top_first[i]);
    }
    printf("]}\n");
    free(table);
}

static void off59_hill_candidate(int idx, uint32_t fixed_w57,
                                 int trials, int threads, int max_passes) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"off59hill\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t fixed_off58 = compute_off58_for_w57(&p1, &p2, fixed_w57);
    int best_hw = 99;
    uint32_t best_off59 = 0;
    uint32_t best_w58 = 0;
    uint32_t best_sched = 0;
    int best_passes = 0;
    int total_evals = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x59595959b17b17b1ULL ^
                       ((uint64_t)cand->m0 << 17) ^
                       ((uint64_t)fixed_w57 << 3) ^
                       (uint64_t)tid;
        int local_best_hw = 99;
        uint32_t local_best_off59 = 0;
        uint32_t local_best_w58 = 0;
        uint32_t local_best_sched = 0;
        int local_best_passes = 0;
        int local_evals = 0;

        #pragma omp for schedule(dynamic, 4)
        for (int i = 0; i < trials; i++) {
            uint32_t w58 = splitmix32(&rng);
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                w58 = patterns[i];
            }

            uint32_t off58 = 0;
            uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, fixed_w57, w58, &off58);
            local_evals++;
            int cur_hw = hw32(off59);
            int passes_used = 0;

            for (int pass = 0; pass < max_passes && cur_hw > 0; pass++) {
                uint32_t best_step_w58 = w58;
                uint32_t best_step_off59 = off59;
                int best_step_hw = cur_hw;

                for (int bit = 0; bit < 32; bit++) {
                    uint32_t wf = w58 ^ (1U << bit);
                    uint32_t of = compute_off59_for_w57_w58(&p1, &p2, fixed_w57, wf, NULL);
                    local_evals++;
                    int h = hw32(of);
                    if (h < best_step_hw ||
                        (h == best_step_hw && of < best_step_off59)) {
                        best_step_hw = h;
                        best_step_w58 = wf;
                        best_step_off59 = of;
                    }
                }

                if (best_step_hw >= cur_hw) break;
                w58 = best_step_w58;
                off59 = best_step_off59;
                cur_hw = best_step_hw;
                passes_used = pass + 1;
            }

            uint32_t sched = sched_offset60_for_w57_w58(&p1, &p2, fixed_w57, w58, NULL);
            if (cur_hw < local_best_hw ||
                (cur_hw == local_best_hw && off59 < local_best_off59)) {
                local_best_hw = cur_hw;
                local_best_off59 = off59;
                local_best_w58 = w58;
                local_best_sched = sched;
                local_best_passes = passes_used;
            }
        }

        #pragma omp critical
        {
            total_evals += local_evals;
            if (local_best_hw < best_hw ||
                (local_best_hw == best_hw && local_best_off59 < best_off59)) {
                best_hw = local_best_hw;
                best_off59 = local_best_off59;
                best_w58 = local_best_w58;
                best_sched = local_best_sched;
                best_passes = local_best_passes;
            }
        }
    }

    printf("{\"mode\":\"off59hill\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"trials\":%d,\"max_passes\":%d,"
           "\"best_w58\":\"0x%08x\",\"best_off59\":\"0x%08x\",\"best_off59_hw\":%d,"
           "\"best_sched\":\"0x%08x\",\"best_passes\":%d,\"evals\":%d}\n",
           cand->id, idx, fixed_w57, fixed_off58, hw32(fixed_off58),
           trials, max_passes, best_w58, best_off59, best_hw,
           best_sched, best_passes, total_evals);
}

static void rank_fixed58_candidate(int idx, uint32_t fixed_w57, uint32_t fixed_w58,
                                   int samples, int threads) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"rankfixed58\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58 = 0;
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, &off58);
    uint32_t sched = sched_offset60_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, NULL);

    int rank_hist[33];
    memset(rank_hist, 0, sizeof(rank_hist));
    int min_rank = 99;
    uint32_t min_rank_w59 = 0;
    uint32_t min_rank_defect = 0;
    int min_rank_defect_hw = 99;
    int min_defect_hw = 99;
    uint32_t min_defect_w59 = 0;
    uint32_t min_defect = 0;

    #pragma omp parallel num_threads(threads)
    {
        int local_rank_hist[33];
        memset(local_rank_hist, 0, sizeof(local_rank_hist));
        int local_min_rank = 99;
        uint32_t local_min_rank_w59 = 0;
        uint32_t local_min_rank_defect = 0;
        int local_min_rank_defect_hw = 99;
        int local_min_defect_hw = 99;
        uint32_t local_min_defect_w59 = 0;
        uint32_t local_min_defect = 0;

        int tid = omp_get_thread_num();
        uint64_t rng = 0x12344321aaaabbbbULL ^
                       ((uint64_t)fixed_w57 << 5) ^
                       ((uint64_t)fixed_w58 << 23) ^
                       (uint64_t)tid;

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < samples; i++) {
            uint32_t w59 = splitmix32(&rng);
            uint32_t x[3] = {fixed_w57, fixed_w58, w59};
            eval_t base = eval_defect(&p1, &p2, x);
            uint32_t cols[32];
            for (int bit = 0; bit < 32; bit++) {
                uint32_t xf[3] = {fixed_w57, fixed_w58, w59 ^ (1U << bit)};
                eval_t y = eval_defect(&p1, &p2, xf);
                cols[bit] = base.defect ^ y.defect;
            }
            int rank = rank32_vectors(cols, 32);
            if (rank >= 0 && rank <= 32) local_rank_hist[rank]++;
            if (rank < local_min_rank) {
                local_min_rank = rank;
                local_min_rank_w59 = w59;
                local_min_rank_defect = base.defect;
                local_min_rank_defect_hw = base.defect_hw;
            }
            if (base.defect_hw < local_min_defect_hw) {
                local_min_defect_hw = base.defect_hw;
                local_min_defect_w59 = w59;
                local_min_defect = base.defect;
            }
        }

        #pragma omp critical
        {
            for (int i = 0; i <= 32; i++) rank_hist[i] += local_rank_hist[i];
            if (local_min_rank < min_rank) {
                min_rank = local_min_rank;
                min_rank_w59 = local_min_rank_w59;
                min_rank_defect = local_min_rank_defect;
                min_rank_defect_hw = local_min_rank_defect_hw;
            }
            if (local_min_defect_hw < min_defect_hw) {
                min_defect_hw = local_min_defect_hw;
                min_defect_w59 = local_min_defect_w59;
                min_defect = local_min_defect;
            }
        }
    }

    printf("{\"mode\":\"rankfixed58\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"fixed_w58\":\"0x%08x\","
           "\"off58\":\"0x%08x\",\"off58_hw\":%d,\"off59\":\"0x%08x\",\"off59_hw\":%d,"
           "\"sched_offset60\":\"0x%08x\",\"samples\":%d,"
           "\"rank_hist\":{",
           cand->id, idx, fixed_w57, fixed_w58,
           off58, hw32(off58), off59, hw32(off59), sched, samples);
    int first = 1;
    for (int r = 0; r <= 32; r++) {
        if (!rank_hist[r]) continue;
        if (!first) printf(",");
        printf("\"%d\":%d", r, rank_hist[r]);
        first = 0;
    }
    printf("},\"min_rank\":%d,\"min_rank_w59\":\"0x%08x\","
           "\"min_rank_defect\":\"0x%08x\",\"min_rank_defect_hw\":%d,"
           "\"min_defect_hw\":%d,\"min_defect\":\"0x%08x\","
           "\"min_defect_w59\":\"0x%08x\"}\n",
           min_rank, min_rank_w59, min_rank_defect, min_rank_defect_hw,
           min_defect_hw, min_defect, min_defect_w59);
}

static void defect_hill_fixed58_candidate(int idx, uint32_t fixed_w57, uint32_t fixed_w58,
                                          int trials, int threads, int max_passes) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"defecthill58\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58 = 0;
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, &off58);
    uint32_t sched = sched_offset60_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, NULL);
    int best_hw = 99;
    uint32_t best_defect = 0;
    uint32_t best_w59 = 0;
    int best_passes = 0;
    int total_evals = 0;
    int exact_hits = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xdefec7ed01234567ULL ^
                       ((uint64_t)fixed_w57 << 13) ^
                       ((uint64_t)fixed_w58 << 27) ^
                       (uint64_t)tid;
        int local_best_hw = 99;
        uint32_t local_best_defect = 0;
        uint32_t local_best_w59 = 0;
        int local_best_passes = 0;
        int local_evals = 0;
        int local_exact_hits = 0;

        #pragma omp for schedule(dynamic, 4)
        for (int i = 0; i < trials; i++) {
            uint32_t w59 = splitmix32(&rng);
            uint32_t x[3] = {fixed_w57, fixed_w58, w59};
            eval_t base = eval_defect(&p1, &p2, x);
            local_evals++;
            int cur_hw = base.defect_hw;
            uint32_t cur_defect = base.defect;
            int passes_used = 0;

            for (int pass = 0; pass < max_passes && cur_hw > 0; pass++) {
                uint32_t best_step_w59 = w59;
                uint32_t best_step_defect = cur_defect;
                int best_step_hw = cur_hw;

                for (int bit = 0; bit < 32; bit++) {
                    uint32_t wf = w59 ^ (1U << bit);
                    uint32_t xf[3] = {fixed_w57, fixed_w58, wf};
                    eval_t y = eval_defect(&p1, &p2, xf);
                    local_evals++;
                    if (y.defect_hw < best_step_hw ||
                        (y.defect_hw == best_step_hw && y.defect < best_step_defect)) {
                        best_step_hw = y.defect_hw;
                        best_step_defect = y.defect;
                        best_step_w59 = wf;
                    }
                }

                if (best_step_hw >= cur_hw) break;
                w59 = best_step_w59;
                cur_defect = best_step_defect;
                cur_hw = best_step_hw;
                passes_used = pass + 1;
            }

            if (cur_hw == 0) local_exact_hits++;
            if (cur_hw < local_best_hw ||
                (cur_hw == local_best_hw && cur_defect < local_best_defect)) {
                local_best_hw = cur_hw;
                local_best_defect = cur_defect;
                local_best_w59 = w59;
                local_best_passes = passes_used;
            }
        }

        #pragma omp critical
        {
            total_evals += local_evals;
            exact_hits += local_exact_hits;
            if (local_best_hw < best_hw ||
                (local_best_hw == best_hw && local_best_defect < best_defect)) {
                best_hw = local_best_hw;
                best_defect = local_best_defect;
                best_w59 = local_best_w59;
                best_passes = local_best_passes;
            }
        }
    }

    printf("{\"mode\":\"defecthill58\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"fixed_w58\":\"0x%08x\","
           "\"off58\":\"0x%08x\",\"off58_hw\":%d,\"off59\":\"0x%08x\",\"off59_hw\":%d,"
           "\"sched_offset60\":\"0x%08x\",\"trials\":%d,\"max_passes\":%d,"
           "\"exact_hits\":%d,\"best_hw\":%d,\"best_defect\":\"0x%08x\","
           "\"best_w59\":\"0x%08x\",\"best_passes\":%d,\"evals\":%d}\n",
           cand->id, idx, fixed_w57, fixed_w58,
           off58, hw32(off58), off59, hw32(off59), sched,
           trials, max_passes, exact_hits, best_hw, best_defect,
           best_w59, best_passes, total_evals);
}

static uint64_t next_combination64(uint64_t x) {
    uint64_t u = x & (0ULL - x);
    uint64_t v = u + x;
    if (v == 0) return 0;
    return v + (((v ^ x) / u) >> 2);
}

static void apply_combo_to_x(const uint32_t base[3], uint64_t combo, uint32_t x[3]) {
    x[0] = base[0];
    x[1] = base[1] ^ (uint32_t)(combo & 0xffffffffULL);
    x[2] = base[2] ^ (uint32_t)(combo >> 32);
}

static void neighbor_point_search(int idx, uint32_t base_x[3], int max_k) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_k < 0) max_k = 0;
    if (max_k > 6) max_k = 6;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"neighpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    eval_t base_eval = eval_defect(&p1, &p2, base_x);
    int best_hw = base_eval.defect_hw;
    uint32_t best_defect = base_eval.defect;
    uint32_t best_x[3] = {base_x[0], base_x[1], base_x[2]};
    int best_k = 0;
    uint64_t best_combo = 0;
    uint64_t tested = 1;
    int exact = (base_eval.defect == 0);

    for (int k = 1; k <= max_k && !exact; k++) {
        uint64_t combo = (k == 64) ? UINT64_MAX : ((1ULL << k) - 1ULL);
        while (combo && !exact) {
            uint32_t x[3];
            apply_combo_to_x(base_x, combo, x);
            eval_t y = eval_defect(&p1, &p2, x);
            tested++;
            if (y.defect_hw < best_hw ||
                (y.defect_hw == best_hw && y.defect < best_defect)) {
                best_hw = y.defect_hw;
                best_defect = y.defect;
                memcpy(best_x, x, sizeof(best_x));
                best_k = k;
                best_combo = combo;
            }
            if (y.defect == 0) {
                exact = 1;
                best_hw = 0;
                best_defect = 0;
                memcpy(best_x, x, sizeof(best_x));
                best_k = k;
                best_combo = combo;
                break;
            }
            uint64_t next = next_combination64(combo);
            if (!next || next < combo) break;
            combo = next;
        }
    }

    uint32_t off58 = compute_off58_for_w57(&p1, &p2, best_x[0]);
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, best_x[0], best_x[1], NULL);
    printf("{\"mode\":\"neighpoint\",\"candidate_index\":%d,\"candidate\":\"%s\","
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_defect\":\"0x%08x\",\"base_hw\":%d,\"max_k\":%d,"
           "\"tested\":%llu,\"exact\":%d,\"best_k\":%d,\"best_combo\":\"0x%016llx\","
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_defect\":\"0x%08x\",\"best_hw\":%d,"
           "\"best_off58\":\"0x%08x\",\"best_off59\":\"0x%08x\"}\n",
           idx, cand->id, base_x[0], base_x[1], base_x[2],
           base_eval.defect, base_eval.defect_hw, max_k,
           (unsigned long long)tested, exact, best_k, (unsigned long long)best_combo,
           best_x[0], best_x[1], best_x[2], best_defect, best_hw, off58, off59);
}

typedef struct {
    const sha256_precomp_t *p1;
    const sha256_precomp_t *p2;
    uint32_t base_x[3];
    uint32_t work_x[3];
    uint32_t best_x[3];
    uint32_t best_defect;
    uint64_t tested;
    uint64_t best_mask_low;
    uint32_t best_mask_high;
    int best_hw;
    int best_k;
    int exact;
} neigh_all_ctx_t;

static void flip_global_bit(uint32_t x[3], int bit) {
    int word = bit / 32;
    int b = bit & 31;
    x[word] ^= 1U << b;
}

static void record_global_bit(neigh_all_ctx_t *ctx, int bit) {
    if (bit < 64) {
        ctx->best_mask_low ^= 1ULL << bit;
    } else {
        ctx->best_mask_high ^= 1U << (bit - 64);
    }
}

static void search_neigh_all_rec(neigh_all_ctx_t *ctx, int start_bit, int depth, int k) {
    if (ctx->exact) return;
    if (depth == k) {
        eval_t y = eval_defect(ctx->p1, ctx->p2, ctx->work_x);
        ctx->tested++;
        if (y.defect_hw < ctx->best_hw ||
            (y.defect_hw == ctx->best_hw && y.defect < ctx->best_defect)) {
            ctx->best_hw = y.defect_hw;
            ctx->best_defect = y.defect;
            memcpy(ctx->best_x, ctx->work_x, sizeof(ctx->best_x));
            ctx->best_k = k;
            ctx->best_mask_low = 0;
            ctx->best_mask_high = 0;
            for (int w = 0; w < 3; w++) {
                uint32_t diff = ctx->base_x[w] ^ ctx->work_x[w];
                for (int b = 0; b < 32; b++) {
                    if ((diff >> b) & 1U) record_global_bit(ctx, w * 32 + b);
                }
            }
        }
        if (y.defect == 0) ctx->exact = 1;
        return;
    }

    for (int bit = start_bit; bit <= 96 - (k - depth); bit++) {
        flip_global_bit(ctx->work_x, bit);
        search_neigh_all_rec(ctx, bit + 1, depth + 1, k);
        flip_global_bit(ctx->work_x, bit);
        if (ctx->exact) return;
    }
}

static void neighbor_all_point_search(int idx, uint32_t base_x[3], int max_k) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_k < 0) max_k = 0;
    if (max_k > 5) max_k = 5;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"neighallpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    eval_t base_eval = eval_defect(&p1, &p2, base_x);
    neigh_all_ctx_t ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.p1 = &p1;
    ctx.p2 = &p2;
    memcpy(ctx.base_x, base_x, sizeof(ctx.base_x));
    memcpy(ctx.work_x, base_x, sizeof(ctx.work_x));
    memcpy(ctx.best_x, base_x, sizeof(ctx.best_x));
    ctx.best_defect = base_eval.defect;
    ctx.best_hw = base_eval.defect_hw;
    ctx.tested = 1;
    ctx.exact = (base_eval.defect == 0);

    for (int k = 1; k <= max_k && !ctx.exact; k++) {
        memcpy(ctx.work_x, base_x, sizeof(ctx.work_x));
        search_neigh_all_rec(&ctx, 0, 0, k);
    }

    uint32_t off58 = compute_off58_for_w57(&p1, &p2, ctx.best_x[0]);
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, ctx.best_x[0], ctx.best_x[1], NULL);
    printf("{\"mode\":\"neighallpoint\",\"candidate_index\":%d,\"candidate\":\"%s\","
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_defect\":\"0x%08x\",\"base_hw\":%d,\"max_k\":%d,"
           "\"tested\":%llu,\"exact\":%d,\"best_k\":%d,"
           "\"best_mask_low\":\"0x%016llx\",\"best_mask_high\":\"0x%08x\","
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_defect\":\"0x%08x\",\"best_hw\":%d,"
           "\"best_off58\":\"0x%08x\",\"best_off59\":\"0x%08x\"}\n",
           idx, cand->id, base_x[0], base_x[1], base_x[2],
           base_eval.defect, base_eval.defect_hw, max_k,
           (unsigned long long)ctx.tested, ctx.exact, ctx.best_k,
           (unsigned long long)ctx.best_mask_low, ctx.best_mask_high,
           ctx.best_x[0], ctx.best_x[1], ctx.best_x[2],
           ctx.best_defect, ctx.best_hw, off58, off59);
}

static int defect_newton_fixed58_once(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                                      uint32_t x[3], int max_iters, int *iters_out,
                                      int *last_rank_out, uint32_t *last_defect_out) {
    for (int iter = 0; iter < max_iters; iter++) {
        eval_t base = eval_defect(p1, p2, x);
        if (base.defect == 0) {
            if (iters_out) *iters_out = iter;
            if (last_rank_out) *last_rank_out = 32;
            if (last_defect_out) *last_defect_out = 0;
            return 1;
        }

        uint32_t cols[32];
        for (int bit = 0; bit < 32; bit++) {
            uint32_t xf[3] = {x[0], x[1], x[2] ^ (1U << bit)};
            eval_t y = eval_defect(p1, p2, xf);
            cols[bit] = base.defect ^ y.defect;
        }

        uint64_t delta = 0;
        int rank = 0;
        int solvable = solve_linear_columns(base.defect, cols, 32, &delta, &rank);
        if (last_rank_out) *last_rank_out = rank;
        if (last_defect_out) *last_defect_out = base.defect;
        if (!solvable || delta == 0) {
            if (iters_out) *iters_out = iter;
            return 0;
        }
        x[2] ^= (uint32_t)delta;
    }

    eval_t last = eval_defect(p1, p2, x);
    if (iters_out) *iters_out = max_iters;
    if (last_defect_out) *last_defect_out = last.defect;
    return last.defect == 0;
}

static void newton_fixed58_candidate(int idx, uint32_t fixed_w57, uint32_t fixed_w58,
                                     int trials, int threads, int max_iters) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"newtonfixed58\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58 = 0;
    uint32_t sched = sched_offset60_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, &off58);
    int successes = 0;
    int rank_failures = 0;
    int total_success_iters = 0;
    int best_hw = 99;
    uint32_t best_defect = 0;
    uint32_t best_x[3] = {fixed_w57, fixed_w58, 0};
    uint32_t first_success_x[3] = {fixed_w57, fixed_w58, 0};
    int first_success_iters = -1;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xc001d00d5eed1234ULL ^
                       ((uint64_t)fixed_w57 << 7) ^
                       ((uint64_t)fixed_w58 << 29) ^
                       (uint64_t)tid;
        int local_successes = 0;
        int local_rank_failures = 0;
        int local_iters = 0;
        int local_best_hw = 99;
        uint32_t local_best_defect = 0;
        uint32_t local_best_x[3] = {fixed_w57, fixed_w58, 0};
        uint32_t local_first_x[3] = {fixed_w57, fixed_w58, 0};
        int local_first_iters = -1;

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3] = {fixed_w57, fixed_w58, splitmix32(&rng)};
            int iters = 0, last_rank = 0;
            uint32_t last_defect = 0;
            int ok = defect_newton_fixed58_once(&p1, &p2, x, max_iters,
                                                &iters, &last_rank, &last_defect);
            if (ok) {
                local_successes++;
                local_iters += iters;
                if (local_first_iters < 0) {
                    local_first_iters = iters;
                    memcpy(local_first_x, x, sizeof(local_first_x));
                }
            } else {
                if (last_rank < 32) local_rank_failures++;
                int h = hw32(last_defect);
                if (h < local_best_hw) {
                    local_best_hw = h;
                    local_best_defect = last_defect;
                    memcpy(local_best_x, x, sizeof(local_best_x));
                }
            }
        }

        #pragma omp critical
        {
            successes += local_successes;
            rank_failures += local_rank_failures;
            total_success_iters += local_iters;
            if (local_best_hw < best_hw) {
                best_hw = local_best_hw;
                best_defect = local_best_defect;
                memcpy(best_x, local_best_x, sizeof(best_x));
            }
            if (first_success_iters < 0 && local_first_iters >= 0) {
                first_success_iters = local_first_iters;
                memcpy(first_success_x, local_first_x, sizeof(first_success_x));
            }
        }
    }

    printf("{\"mode\":\"newtonfixed58\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"fixed_w58\":\"0x%08x\","
           "\"off58\":\"0x%08x\",\"off58_hw\":%d,\"sched_offset60\":\"0x%08x\","
           "\"trials\":%d,\"max_iters\":%d,\"successes\":%d,"
           "\"success_rate\":%.6f,\"avg_success_iters\":%.3f,"
           "\"rank_failures\":%d,\"best_hw\":%d,\"best_defect\":\"0x%08x\","
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"first_success_iters\":%d,"
           "\"first_success_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx, fixed_w57, fixed_w58, off58, hw32(off58), sched,
           trials, max_iters, successes,
           trials ? (double)successes / (double)trials : 0.0,
           successes ? (double)total_success_iters / (double)successes : 0.0,
           rank_failures, best_hw, best_defect,
           best_x[0], best_x[1], best_x[2],
           first_success_iters,
           first_success_x[0], first_success_x[1], first_success_x[2]);
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "neighallpoint") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_k = (argc >= 7) ? atoi(argv[6]) : 4;
        sha256_init(32);
        neighbor_all_point_search(idx, x, max_k);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "neighpoint") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_k = (argc >= 7) ? atoi(argv[6]) : 4;
        sha256_init(32);
        neighbor_point_search(idx, x, max_k);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "newtonpoint") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_iters = (argc >= 7) ? atoi(argv[6]) : 32;
        int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
        if (idx < 0 || idx >= n_cands) {
            fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
            return 2;
        }
        sha256_init(32);
        sha256_precomp_t p1, p2;
        const candidate_t *cand = &CANDIDATES[idx];
        if (!prepare_candidate(cand, &p1, &p2)) {
            printf("{\"mode\":\"newtonpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
                   cand->id);
            return 1;
        }
        uint32_t start[3] = {x[0], x[1], x[2]};
        uint32_t start_off58 = compute_off58_for_w57(&p1, &p2, x[0]);
        uint32_t start_off59 = compute_off59_for_w57_w58(&p1, &p2, x[0], x[1], NULL);
        eval_t start_eval = eval_defect(&p1, &p2, x);
        int iters = 0, last_rank = 0;
        uint32_t last_defect = 0;
        int ok = defect_newton_once(&p1, &p2, x, max_iters, &iters, &last_rank, &last_defect);
        eval_t final_eval = eval_defect(&p1, &p2, x);
        uint32_t final_off58 = compute_off58_for_w57(&p1, &p2, x[0]);
        uint32_t final_off59 = compute_off59_for_w57_w58(&p1, &p2, x[0], x[1], NULL);
        printf("{\"mode\":\"newtonpoint\",\"candidate_index\":%d,\"candidate\":\"%s\","
               "\"start_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"start_defect\":\"0x%08x\",\"start_hw\":%d,"
               "\"start_off58\":\"0x%08x\",\"start_off59\":\"0x%08x\","
               "\"ok\":%d,\"iters\":%d,\"last_rank\":%d,\"last_defect\":\"0x%08x\","
               "\"final_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"final_defect\":\"0x%08x\",\"final_hw\":%d,"
               "\"final_off58\":\"0x%08x\",\"final_off59\":\"0x%08x\"}\n",
               idx, cand->id, start[0], start[1], start[2],
               start_eval.defect, start_eval.defect_hw, start_off58, start_off59,
               ok, iters, last_rank, last_defect,
               x[0], x[1], x[2], final_eval.defect, final_eval.defect_hw,
               final_off58, final_off59);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "defecthill58") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        uint32_t fixed_w58 = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0;
        int trials = (argc >= 6) ? atoi(argv[5]) : 512;
        int threads = (argc >= 7) ? atoi(argv[6]) : 8;
        int max_passes = (argc >= 8) ? atoi(argv[7]) : 32;
        sha256_init(32);
        defect_hill_fixed58_candidate(idx, fixed_w57, fixed_w58, trials, threads, max_passes);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "rankfixed58") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        uint32_t fixed_w58 = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0;
        int samples = (argc >= 6) ? atoi(argv[5]) : 1024;
        int threads = (argc >= 7) ? atoi(argv[6]) : 8;
        sha256_init(32);
        rank_fixed58_candidate(idx, fixed_w57, fixed_w58, samples, threads);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "off59hill") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        int trials = (argc >= 5) ? atoi(argv[4]) : 512;
        int threads = (argc >= 6) ? atoi(argv[5]) : 8;
        int max_passes = (argc >= 7) ? atoi(argv[6]) : 32;
        sha256_init(32);
        off59_hill_candidate(idx, fixed_w57, trials, threads, max_passes);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "reqsample") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        uint32_t fixed_w58 = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0;
        uint32_t samples = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 1000000U;
        int table_bits = (argc >= 7) ? atoi(argv[6]) : 22;
        sha256_init(32);
        req_sample_candidate(idx, fixed_w57, fixed_w58, samples, table_bits);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "newtonfixed58") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        uint32_t fixed_w58 = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0;
        int trials = (argc >= 6) ? atoi(argv[5]) : 512;
        int threads = (argc >= 7) ? atoi(argv[6]) : 8;
        int max_iters = (argc >= 8) ? atoi(argv[7]) : 24;
        sha256_init(32);
        newton_fixed58_candidate(idx, fixed_w57, fixed_w58, trials, threads, max_iters);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "schedsample") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        uint32_t samples = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 1000000U;
        int table_bits = (argc >= 6) ? atoi(argv[5]) : 22;
        sha256_init(32);
        sched_sample_candidate(idx, fixed_w57, samples, table_bits);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "newtonfixed") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        int trials = (argc >= 5) ? atoi(argv[4]) : 512;
        int threads = (argc >= 6) ? atoi(argv[5]) : 8;
        int max_iters = (argc >= 7) ? atoi(argv[6]) : 24;
        sha256_init(32);
        newton_fixed_w57_candidate(idx, fixed_w57, trials, threads, max_iters);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "off58hill") == 0) {
        int trials = (argc >= 3) ? atoi(argv[2]) : 64;
        int threads = (argc >= 4) ? atoi(argv[3]) : 8;
        int max_passes = (argc >= 5) ? atoi(argv[4]) : 32;
        sha256_init(32);
        int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
        for (int i = 0; i < n_cands; i++) {
            off58_hill_candidate(&CANDIDATES[i], trials, threads, max_passes);
        }
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "off58newton") == 0) {
        uint32_t target = (argc >= 3) ? (uint32_t)strtoul(argv[2], NULL, 0) : 0x0000000cU;
        int trials = (argc >= 4) ? atoi(argv[3]) : 256;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int max_iters = (argc >= 6) ? atoi(argv[5]) : 24;
        sha256_init(32);
        int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
        for (int i = 0; i < n_cands; i++) {
            off58_newton_candidate(&CANDIDATES[i], target, trials, threads, max_iters);
        }
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "lift12") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
        if (idx < 0 || idx >= n_cands) {
            fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
            return 2;
        }
        sha256_init(32);
        sha256_precomp_t p1, p2;
        const candidate_t *cand = &CANDIDATES[idx];
        if (!prepare_candidate(cand, &p1, &p2)) {
            printf("{\"mode\":\"lift12\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n", cand->id);
            return 1;
        }
        uint32_t w58_12[] = {
            0x393,0x3b3,0x793,0x7b3,0x6b3,0x493,0x293,0x392,
            0x7f3,0x7d3,0x88d,0xbbe,0x8f3,0xd89,0x093,0x773
        };
        uint32_t w59_12[] = {
            0x369,0x8bb,0x8c3,0x8d3,0x8da,0x8e2,0x9bb,0x9c3,
            0x9d3,0x9da,0x9e2,0xcbb,0xcc3,0xcca,0xcda,0xce2,
            0xdbb,0xdc3,0xdca,0xdda,0xde2
        };
        #define REP12(x) (((uint32_t)(x) & 0xfffU) | (((uint32_t)(x) & 0xfffU) << 12) | (((uint32_t)(x) & 0xffU) << 24))
        uint32_t best_x[3] = {REP12(0x666), 0, 0};
        uint32_t best_defect = 0;
        int best_hw = 99;
        int best_rank = 0;
        int best_wr[3] = {0,0,0};
        int best_pr[3] = {0,0,0};
        for (size_t i = 0; i < sizeof(w58_12)/sizeof(w58_12[0]); i++) {
            for (size_t j = 0; j < sizeof(w59_12)/sizeof(w59_12[0]); j++) {
                uint32_t x[3] = {REP12(0x666), REP12(w58_12[i]), REP12(w59_12[j])};
                eval_t base;
                int wr[3], pr[3];
                int rank = local_defect_rank(&p1, &p2, x, &base, wr, pr);
                if (base.defect_hw < best_hw) {
                    best_hw = base.defect_hw;
                    best_defect = base.defect;
                    best_rank = rank;
                    memcpy(best_x, x, sizeof(best_x));
                    memcpy(best_wr, wr, sizeof(best_wr));
                    memcpy(best_pr, pr, sizeof(best_pr));
                }
            }
        }
        printf("{\"mode\":\"lift12\",\"candidate_index\":%d,\"candidate\":\"%s\","
               "\"tested\":%zu,\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"best_defect\":\"0x%08x\",\"best_hw\":%d,\"rank\":%d,"
               "\"word_rank\":[%d,%d,%d],\"pair_rank_without_word\":[%d,%d,%d]}\n",
               idx, cand->id,
               (sizeof(w58_12)/sizeof(w58_12[0])) * (sizeof(w59_12)/sizeof(w59_12[0])),
               best_x[0], best_x[1], best_x[2],
               best_defect, best_hw, best_rank,
               best_wr[0], best_wr[1], best_wr[2],
               best_pr[0], best_pr[1], best_pr[2]);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
        if (idx < 0 || idx >= n_cands) {
            fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
            return 2;
        }
        sha256_init(32);
        sha256_precomp_t p1, p2;
        const candidate_t *cand = &CANDIDATES[idx];
        if (!prepare_candidate(cand, &p1, &p2)) {
            printf("{\"mode\":\"point\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n", cand->id);
            return 1;
        }
        eval_t base;
        int word_rank[3], pair_rank_without_word[3];
        int rank = local_defect_rank(&p1, &p2, x, &base, word_rank, pair_rank_without_word);
        printf("{\"mode\":\"point\",\"candidate_index\":%d,\"candidate\":\"%s\","
               "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"defect\":\"0x%08x\",\"defect_hw\":%d,\"rank\":%d,"
               "\"word_rank\":[%d,%d,%d],\"pair_rank_without_word\":[%d,%d,%d],"
               "\"ch_inv\":%d,\"maj_a_inv\":%d,\"maj_b_inv\":%d,\"maj_c_inv\":%d}\n",
               idx, cand->id, x[0], x[1], x[2],
               base.defect, base.defect_hw, rank,
               word_rank[0], word_rank[1], word_rank[2],
               pair_rank_without_word[0], pair_rank_without_word[1], pair_rank_without_word[2],
               base.ch_invisible_bits, base.maj_a_invisible_bits,
               base.maj_b_invisible_bits, base.maj_c_invisible_bits);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "newton") == 0) {
        int trials = (argc >= 3) ? atoi(argv[2]) : 100;
        int threads = (argc >= 4) ? atoi(argv[3]) : 8;
        int max_iters = (argc >= 5) ? atoi(argv[4]) : 16;
        if (trials < 1) trials = 1;
        if (threads < 1) threads = 1;
        if (threads > 16) threads = 16;
        if (max_iters < 1) max_iters = 1;
        sha256_init(32);
        fprintf(stderr, "singular_defect_rank:newton candidates=%zu trials=%d threads=%d max_iters=%d\n",
                sizeof(CANDIDATES) / sizeof(CANDIDATES[0]), trials, threads, max_iters);
        for (size_t i = 0; i < sizeof(CANDIDATES) / sizeof(CANDIDATES[0]); i++) {
            newton_candidate(&CANDIDATES[i], trials, threads, max_iters);
            fflush(stdout);
        }
        return 0;
    }

    int samples = (argc >= 2) ? atoi(argv[1]) : 256;
    int threads = (argc >= 3) ? atoi(argv[2]) : 8;
    if (samples < 1) samples = 1;
    if (threads < 1) threads = 1;
    if (threads > 16) threads = 16;

    sha256_init(32);
    fprintf(stderr, "singular_defect_rank: candidates=%zu samples=%d threads=%d\n",
            sizeof(CANDIDATES) / sizeof(CANDIDATES[0]), samples, threads);

    for (size_t i = 0; i < sizeof(CANDIDATES) / sizeof(CANDIDATES[0]); i++) {
        probe_candidate(&CANDIDATES[i], samples, threads);
        fflush(stdout);
    }

    return 0;
}
