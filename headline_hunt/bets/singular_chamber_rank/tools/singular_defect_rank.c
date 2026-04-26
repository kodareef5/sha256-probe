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

int main(int argc, char **argv) {
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
