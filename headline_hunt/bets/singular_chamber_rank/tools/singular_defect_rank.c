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
 *   /tmp/singular_defect_rank defecthill57 3 0xe28da599 4096 8 48
 *   /tmp/singular_defect_rank defecthill58 0 0x370fef5f 0xf0f7e442 512 8 32
 *   /tmp/singular_defect_rank newtonpoint 0 0x370fef5f 0xf0f7e442 0x76712417 32
 *   /tmp/singular_defect_rank neighpoint 0 0x370fef5f 0xf0f7e442 0x76712417 4
 *   /tmp/singular_defect_rank neighallpoint 0 0x370fef5f 0xf0f7e442 0x76712417 4
 *   /tmp/singular_defect_rank tracepoint 3 0xe28da599 0x233e4216 0xda9932f8
 *   /tmp/singular_defect_rank tailpoint 3 0xe28da599 0xa3110717 0x1afa1270
 *   /tmp/singular_defect_rank manifold61point 3 0xe28da599 0x5e06f0a7 0x28859825
 *   /tmp/singular_defect_rank kernel61neighpoint 3 0xe28da599 0x5e06f0a7 0x28859825 4
 *   /tmp/singular_defect_rank tailneighpoint 3 0xe28da599 0x5e06f0a7 0x28859825 5
 *   /tmp/singular_defect_rank tailhill57 3 0xe28da599 4096 8 64
 *   /tmp/singular_defect_rank tailhill58 0 0x370fef5f 0x0e4363c9 4096 8 64
 *   /tmp/singular_defect_rank newton61point 0 0x370fef5f 0x0e4363c9 0xfe337af3 32
 *   /tmp/singular_defect_rank carryjump61point 0 0x370fef5f 0x0e4363c9 0xfe337af3
 *   /tmp/singular_defect_rank kernel61linearpoint 8 0xaf07f044 0xe98d86d0 0xc778e588
 *   /tmp/singular_defect_rank surface61walk 8 0xaf07f044 0xe98d86d0 0xc778e588 65536 8 24 6
 *   /tmp/singular_defect_rank surface61sample 8 0xaf07f044 65536 8 24
 *   /tmp/singular_defect_rank surface61greedywalk 8 0xaf07f044 0xe98d86d0 0xc778e588 65536 8 64 12
 *   /tmp/singular_defect_rank newton61fixed57 3 0xe28da599 2048 8 32
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
    uint32_t w1[7];
    uint32_t w2[7];
    uint32_t offsets[7];
    uint32_t defects[7];
    uint32_t parts[7][4];
    uint32_t sums[7][3];
    uint32_t carries[7][3];
    uint32_t pairdiff[7][8];
    uint32_t s1_before[7][8];
    uint32_t s2_before[7][8];
} tail_trace_t;

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

static inline uint32_t carry_mask_add(uint32_t a, uint32_t b) {
    uint32_t carry = 0;
    uint32_t mask = 0;
    for (int i = 0; i < 32; i++) {
        uint32_t ai = (a >> i) & 1U;
        uint32_t bi = (b >> i) & 1U;
        uint32_t co = (ai & bi) | (ai & carry) | (bi & carry);
        if (co) mask |= 1U << i;
        carry = co;
    }
    return mask;
}

static inline void cascade1_offset_parts(const uint32_t s1[8], const uint32_t s2[8],
                                         uint32_t parts[4], uint32_t sums[3],
                                         uint32_t carries[3]) {
    parts[0] = s1[7] - s2[7];
    parts[1] = sha256_Sigma1(s1[4]) - sha256_Sigma1(s2[4]);
    parts[2] = sha256_Ch(s1[4], s1[5], s1[6]) - sha256_Ch(s2[4], s2[5], s2[6]);
    parts[3] = (sha256_Sigma0(s1[0]) + sha256_Maj(s1[0], s1[1], s1[2])) -
               (sha256_Sigma0(s2[0]) + sha256_Maj(s2[0], s2[1], s2[2]));
    sums[0] = parts[0] + parts[1];
    sums[1] = sums[0] + parts[2];
    sums[2] = sums[1] + parts[3];
    carries[0] = carry_mask_add(parts[0], parts[1]);
    carries[1] = carry_mask_add(sums[0], parts[2]);
    carries[2] = carry_mask_add(sums[1], parts[3]);
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

static int rank64_vectors(const uint64_t *vecs, int n) {
    uint64_t basis[64];
    memset(basis, 0, sizeof(basis));
    int rank = 0;
    for (int i = 0; i < n; i++) {
        uint64_t v = vecs[i];
        for (int b = 63; b >= 0 && v; b--) {
            if (((v >> b) & 1ULL) == 0) continue;
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

static int kernel_basis_columns32(const uint32_t *cols, int ncols,
                                  uint64_t *kernel, int *rank_out) {
    uint32_t basis[32];
    uint64_t combo[32];
    memset(basis, 0, sizeof(basis));
    memset(combo, 0, sizeof(combo));
    int rank = 0;
    int kernel_dim = 0;

    for (int i = 0; i < ncols; i++) {
        uint32_t v = cols[i];
        uint64_t c = 1ULL << i;
        int inserted = 0;
        for (int b = 31; b >= 0 && v; b--) {
            if (((v >> b) & 1U) == 0) continue;
            if (basis[b]) {
                v ^= basis[b];
                c ^= combo[b];
            } else {
                basis[b] = v;
                combo[b] = c;
                rank++;
                inserted = 1;
                break;
            }
        }
        if (!inserted) {
            kernel[kernel_dim++] = c;
        }
    }

    if (rank_out) *rank_out = rank;
    return kernel_dim;
}

static int solve_linear_columns64(uint64_t target, const uint64_t *cols, int ncols,
                                  uint64_t *solution, int *rank_out) {
    uint64_t basis[64];
    uint64_t combo[64];
    memset(basis, 0, sizeof(basis));
    memset(combo, 0, sizeof(combo));
    int rank = 0;

    for (int i = 0; i < ncols; i++) {
        uint64_t v = cols[i];
        uint64_t c = 1ULL << i;
        for (int b = 63; b >= 0 && v; b--) {
            if (((v >> b) & 1ULL) == 0) continue;
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

    uint64_t t = target;
    uint64_t sol = 0;
    for (int b = 63; b >= 0 && t; b--) {
        if (((t >> b) & 1ULL) == 0) continue;
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

static uint32_t combo_effect32(uint64_t combo, const uint32_t *cols) {
    uint32_t out = 0;
    while (combo) {
        int bit = __builtin_ctzll(combo);
        out ^= cols[bit];
        combo &= combo - 1;
    }
    return out;
}

static uint64_t combine_kernel_selection(uint64_t selection,
                                         const uint64_t *kernel_basis) {
    uint64_t out = 0;
    while (selection) {
        int bit = __builtin_ctzll(selection);
        out ^= kernel_basis[bit];
        selection &= selection - 1;
    }
    return out;
}

static int solve_d60_d61_via_d60_kernel(uint32_t target60, uint32_t target61,
                                        const uint32_t cols60[64],
                                        const uint32_t cols61[64],
                                        uint64_t *delta_out,
                                        int *rank60_out,
                                        int *kernel_dim_out,
                                        int *rank61_kernel_out) {
    uint64_t particular = 0;
    int rank60 = 0;
    if (!solve_linear_columns(target60, cols60, 64, &particular, &rank60)) {
        if (rank60_out) *rank60_out = rank60;
        if (kernel_dim_out) *kernel_dim_out = 0;
        if (rank61_kernel_out) *rank61_kernel_out = 0;
        *delta_out = 0;
        return 0;
    }

    uint64_t kernel[64];
    int kernel_rank = 0;
    int kernel_dim = kernel_basis_columns32(cols60, 64, kernel, &kernel_rank);
    uint32_t kernel_cols61[64];
    for (int i = 0; i < kernel_dim; i++) {
        kernel_cols61[i] = combo_effect32(kernel[i], cols61);
    }

    uint32_t residual61 = target61 ^ combo_effect32(particular, cols61);
    uint64_t kernel_selection = 0;
    int rank61_kernel = 0;
    int ok = solve_linear_columns(residual61, kernel_cols61, kernel_dim,
                                  &kernel_selection, &rank61_kernel);

    if (rank60_out) *rank60_out = rank60;
    if (kernel_dim_out) *kernel_dim_out = kernel_dim;
    if (rank61_kernel_out) *rank61_kernel_out = rank61_kernel;
    if (!ok) {
        *delta_out = particular;
        return 0;
    }

    *delta_out = particular ^ combine_kernel_selection(kernel_selection, kernel);
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

static void tail_defects_for_x(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                               const uint32_t x[3], uint32_t defects[7]) {
    uint32_t s1[8], s2[8];
    memcpy(s1, p1->state, sizeof(s1));
    memcpy(s2, p2->state, sizeof(s2));

    uint32_t w1[7], w2[7], offsets[7];
    for (int i = 0; i < 3; i++) {
        offsets[i] = cascade1_offset(s1, s2);
        w1[i] = x[i];
        w2[i] = x[i] + offsets[i];
        apply_round(s1, w1[i], 57 + i);
        apply_round(s2, w2[i], 57 + i);
        defects[i] = 0;
    }
    offsets[3] = cascade1_offset(s1, s2);

    w1[3] = sha256_sigma1(w1[1]) + p1->W[53] +
            sha256_sigma0(p1->W[45]) + p1->W[44];
    w2[3] = sha256_sigma1(w2[1]) + p2->W[53] +
            sha256_sigma0(p2->W[45]) + p2->W[44];
    w1[4] = sha256_sigma1(w1[2]) + p1->W[54] +
            sha256_sigma0(p1->W[46]) + p1->W[45];
    w2[4] = sha256_sigma1(w2[2]) + p2->W[54] +
            sha256_sigma0(p2->W[46]) + p2->W[45];
    w1[5] = sha256_sigma1(w1[3]) + p1->W[55] +
            sha256_sigma0(p1->W[47]) + p1->W[46];
    w2[5] = sha256_sigma1(w2[3]) + p2->W[55] +
            sha256_sigma0(p2->W[47]) + p2->W[46];
    w1[6] = sha256_sigma1(w1[4]) + p1->W[56] +
            sha256_sigma0(p1->W[48]) + p1->W[47];
    w2[6] = sha256_sigma1(w2[4]) + p2->W[56] +
            sha256_sigma0(p2->W[48]) + p2->W[47];

    memcpy(s1, p1->state, sizeof(s1));
    memcpy(s2, p2->state, sizeof(s2));
    for (int i = 0; i < 7; i++) {
        offsets[i] = cascade1_offset(s1, s2);
        defects[i] = (w2[i] - w1[i]) - offsets[i];
        apply_round(s1, w1[i], 57 + i);
        apply_round(s2, w2[i], 57 + i);
    }
}

static void tail_trace_for_x(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                             const uint32_t x[3], tail_trace_t *trace) {
    memset(trace, 0, sizeof(*trace));

    uint32_t s1[8], s2[8];
    memcpy(s1, p1->state, sizeof(s1));
    memcpy(s2, p2->state, sizeof(s2));

    for (int i = 0; i < 3; i++) {
        trace->offsets[i] = cascade1_offset(s1, s2);
        trace->w1[i] = x[i];
        trace->w2[i] = x[i] + trace->offsets[i];
        apply_round(s1, trace->w1[i], 57 + i);
        apply_round(s2, trace->w2[i], 57 + i);
    }

    trace->w1[3] = sha256_sigma1(trace->w1[1]) + p1->W[53] +
                   sha256_sigma0(p1->W[45]) + p1->W[44];
    trace->w2[3] = sha256_sigma1(trace->w2[1]) + p2->W[53] +
                   sha256_sigma0(p2->W[45]) + p2->W[44];
    trace->w1[4] = sha256_sigma1(trace->w1[2]) + p1->W[54] +
                   sha256_sigma0(p1->W[46]) + p1->W[45];
    trace->w2[4] = sha256_sigma1(trace->w2[2]) + p2->W[54] +
                   sha256_sigma0(p2->W[46]) + p2->W[45];
    trace->w1[5] = sha256_sigma1(trace->w1[3]) + p1->W[55] +
                   sha256_sigma0(p1->W[47]) + p1->W[46];
    trace->w2[5] = sha256_sigma1(trace->w2[3]) + p2->W[55] +
                   sha256_sigma0(p2->W[47]) + p2->W[46];
    trace->w1[6] = sha256_sigma1(trace->w1[4]) + p1->W[56] +
                   sha256_sigma0(p1->W[48]) + p1->W[47];
    trace->w2[6] = sha256_sigma1(trace->w2[4]) + p2->W[56] +
                   sha256_sigma0(p2->W[48]) + p2->W[47];

    memcpy(s1, p1->state, sizeof(s1));
    memcpy(s2, p2->state, sizeof(s2));
    for (int i = 0; i < 7; i++) {
        memcpy(trace->s1_before[i], s1, sizeof(s1));
        memcpy(trace->s2_before[i], s2, sizeof(s2));
        for (int j = 0; j < 8; j++) {
            trace->pairdiff[i][j] = s1[j] ^ s2[j];
        }
        cascade1_offset_parts(s1, s2, trace->parts[i],
                              trace->sums[i], trace->carries[i]);
        trace->offsets[i] = trace->sums[i][2];
        trace->defects[i] = (trace->w2[i] - trace->w1[i]) - trace->offsets[i];
        apply_round(s1, trace->w1[i], 57 + i);
        apply_round(s2, trace->w2[i], 57 + i);
    }
}

static inline uint64_t defect60_61_vec(const sha256_precomp_t *p1,
                                       const sha256_precomp_t *p2,
                                       const uint32_t x[3]) {
    uint32_t defects[7];
    tail_defects_for_x(p1, p2, x, defects);
    return ((uint64_t)defects[4] << 32) | (uint64_t)defects[3];
}

static void defect60_61_columns(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                                const uint32_t x[3], uint32_t *d60_out,
                                uint32_t *d61_out, uint32_t cols60[64],
                                uint32_t cols61[64], uint64_t cols_pair[64]) {
    uint64_t base = defect60_61_vec(p1, p2, x);
    if (d60_out) *d60_out = (uint32_t)base;
    if (d61_out) *d61_out = (uint32_t)(base >> 32);

    for (int bit = 0; bit < 64; bit++) {
        uint32_t xf[3] = {x[0], x[1], x[2]};
        if (bit < 32) xf[1] ^= 1U << bit;
        else xf[2] ^= 1U << (bit - 32);
        uint64_t col = base ^ defect60_61_vec(p1, p2, xf);
        cols60[bit] = (uint32_t)col;
        cols61[bit] = (uint32_t)(col >> 32);
        cols_pair[bit] = col;
    }
}

static void apply_delta58_59(const uint32_t in[3], uint64_t delta, uint32_t out[3]) {
    out[0] = in[0];
    out[1] = in[1] ^ (uint32_t)(delta & 0xffffffffULL);
    out[2] = in[2] ^ (uint32_t)(delta >> 32);
}

static uint64_t next_combination64(uint64_t x);
static void apply_combo_to_x(const uint32_t base[3], uint64_t combo, uint32_t x[3]);
static inline int score60_61(uint32_t d60, uint32_t d61);

static void manifold61_point(int idx, const uint32_t x[3]) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"manifold61point\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t defects[7];
    tail_defects_for_x(&p1, &p2, x, defects);

    uint32_t cols60[64], cols61[64];
    uint64_t cols_pair[64];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns(&p1, &p2, x, &d60, &d61, cols60, cols61, cols_pair);

    int rank60 = rank32_vectors(cols60, 64);
    int rank61 = rank32_vectors(cols61, 64);
    int rank_pair = rank64_vectors(cols_pair, 64);

    uint64_t kernel[64];
    int kernel_rank = 0;
    int kernel_dim = kernel_basis_columns32(cols60, 64, kernel, &kernel_rank);
    uint32_t kernel_cols61[64];
    for (int i = 0; i < kernel_dim; i++) {
        kernel_cols61[i] = combo_effect32(kernel[i], cols61);
    }
    int rank61_kernel = rank32_vectors(kernel_cols61, kernel_dim);

    uint64_t pair_delta = 0;
    int pair_solve_rank = 0;
    int pair_solvable = solve_linear_columns64(((uint64_t)d61 << 32) | d60,
                                               cols_pair, 64,
                                               &pair_delta, &pair_solve_rank);
    uint32_t pair_step[3] = {x[0], x[1], x[2]};
    uint32_t pair_step_defects[7] = {0};
    if (pair_solvable) {
        apply_delta58_59(x, pair_delta, pair_step);
        tail_defects_for_x(&p1, &p2, pair_step, pair_step_defects);
    }

    uint64_t kernel_delta = 0;
    int k_rank60 = 0, k_dim = 0, k_rank61 = 0;
    int kernel_solvable = solve_d60_d61_via_d60_kernel(0, d61, cols60, cols61,
                                                       &kernel_delta, &k_rank60,
                                                       &k_dim, &k_rank61);
    uint32_t kernel_step[3] = {x[0], x[1], x[2]};
    uint32_t kernel_step_defects[7] = {0};
    if (kernel_solvable) {
        apply_delta58_59(x, kernel_delta, kernel_step);
        tail_defects_for_x(&p1, &p2, kernel_step, kernel_step_defects);
    }

    uint32_t off58 = 0;
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, x[0], x[1], &off58);
    printf("{\"mode\":\"manifold61point\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"off59\":\"0x%08x\",\"off59_hw\":%d,"
           "\"defect60\":\"0x%08x\",\"defect60_hw\":%d,"
           "\"defect61\":\"0x%08x\",\"defect61_hw\":%d,"
           "\"tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"rank60\":%d,\"rank61\":%d,\"rank_pair\":%d,"
           "\"kernel_dim\":%d,\"rank61_on_kernel\":%d,"
           "\"pair_solvable\":%d,\"pair_solve_rank\":%d,\"pair_delta_hw\":%d,"
           "\"pair_step_defect60\":\"0x%08x\",\"pair_step_defect61\":\"0x%08x\","
           "\"kernel_solvable\":%d,\"kernel_delta_hw\":%d,"
           "\"kernel_step_defect60\":\"0x%08x\",\"kernel_step_defect61\":\"0x%08x\"}\n",
           cand->id, idx,
           x[0], x[1], x[2],
           off58, hw32(off58), off59, hw32(off59),
           d60, hw32(d60), d61, hw32(d61),
           defects[0], defects[1], defects[2], defects[3],
           defects[4], defects[5], defects[6],
           rank60, rank61, rank_pair, kernel_dim, rank61_kernel,
           pair_solvable, pair_solve_rank, pair_solvable ? hw32((uint32_t)pair_delta) + hw32((uint32_t)(pair_delta >> 32)) : 0,
           pair_step_defects[3], pair_step_defects[4],
           kernel_solvable, kernel_solvable ? hw32((uint32_t)kernel_delta) + hw32((uint32_t)(kernel_delta >> 32)) : 0,
           kernel_step_defects[3], kernel_step_defects[4]);
}

static void carryjump61_point(int idx, const uint32_t x[3]) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"carryjump61point\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[64], cols61[64];
    uint64_t cols_pair[64];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns(&p1, &p2, x, &d60, &d61, cols60, cols61, cols_pair);

    uint64_t delta = 0;
    int rank = 0;
    int solvable = solve_linear_columns64(((uint64_t)d61 << 32) | d60,
                                          cols_pair, 64, &delta, &rank);
    uint32_t jump_x[3] = {x[0], x[1], x[2]};
    uint32_t linear_d60 = d60;
    uint32_t linear_d61 = d61;
    if (solvable) {
        apply_delta58_59(x, delta, jump_x);
        linear_d60 ^= combo_effect32(delta, cols60);
        linear_d61 ^= combo_effect32(delta, cols61);
    }

    tail_trace_t src, jump;
    tail_trace_for_x(&p1, &p2, x, &src);
    tail_trace_for_x(&p1, &p2, jump_x, &jump);

    int r60 = 3;
    int r61 = 4;
    printf("{\"mode\":\"carryjump61point\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"solvable\":%d,\"rank\":%d,\"delta\":\"0x%016llx\",\"delta_hw\":%d,"
           "\"jump_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"linear_after\":[\"0x%08x\",\"0x%08x\"],"
           "\"actual_before\":[\"0x%08x\",\"0x%08x\"],"
           "\"actual_after\":[\"0x%08x\",\"0x%08x\"],"
           "\"round60\":{\"src_sched\":\"0x%08x\",\"src_req\":\"0x%08x\","
           "\"jump_sched\":\"0x%08x\",\"jump_req\":\"0x%08x\","
           "\"src_parts\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"jump_parts\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"parts_xor_hw\":[%d,%d,%d,%d],"
           "\"src_carries\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"jump_carries\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"carry_xor_hw\":[%d,%d,%d],"
           "\"pairdiff_xor_hw\":[%d,%d,%d,%d,%d,%d,%d,%d]},"
           "\"round61\":{\"src_sched\":\"0x%08x\",\"src_req\":\"0x%08x\","
           "\"jump_sched\":\"0x%08x\",\"jump_req\":\"0x%08x\","
           "\"src_parts\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"jump_parts\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"parts_xor_hw\":[%d,%d,%d,%d],"
           "\"src_carries\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"jump_carries\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"carry_xor_hw\":[%d,%d,%d],"
           "\"pairdiff_xor_hw\":[%d,%d,%d,%d,%d,%d,%d,%d]}}\n",
           cand->id, idx,
           x[0], x[1], x[2],
           solvable, rank, (unsigned long long)delta,
           solvable ? hw32((uint32_t)delta) + hw32((uint32_t)(delta >> 32)) : 0,
           jump_x[0], jump_x[1], jump_x[2],
           linear_d60, linear_d61,
           src.defects[r60], src.defects[r61],
           jump.defects[r60], jump.defects[r61],
           src.w2[r60] - src.w1[r60], src.offsets[r60],
           jump.w2[r60] - jump.w1[r60], jump.offsets[r60],
           src.parts[r60][0], src.parts[r60][1], src.parts[r60][2], src.parts[r60][3],
           jump.parts[r60][0], jump.parts[r60][1], jump.parts[r60][2], jump.parts[r60][3],
           hw32(src.parts[r60][0] ^ jump.parts[r60][0]),
           hw32(src.parts[r60][1] ^ jump.parts[r60][1]),
           hw32(src.parts[r60][2] ^ jump.parts[r60][2]),
           hw32(src.parts[r60][3] ^ jump.parts[r60][3]),
           src.carries[r60][0], src.carries[r60][1], src.carries[r60][2],
           jump.carries[r60][0], jump.carries[r60][1], jump.carries[r60][2],
           hw32(src.carries[r60][0] ^ jump.carries[r60][0]),
           hw32(src.carries[r60][1] ^ jump.carries[r60][1]),
           hw32(src.carries[r60][2] ^ jump.carries[r60][2]),
           hw32(src.pairdiff[r60][0] ^ jump.pairdiff[r60][0]),
           hw32(src.pairdiff[r60][1] ^ jump.pairdiff[r60][1]),
           hw32(src.pairdiff[r60][2] ^ jump.pairdiff[r60][2]),
           hw32(src.pairdiff[r60][3] ^ jump.pairdiff[r60][3]),
           hw32(src.pairdiff[r60][4] ^ jump.pairdiff[r60][4]),
           hw32(src.pairdiff[r60][5] ^ jump.pairdiff[r60][5]),
           hw32(src.pairdiff[r60][6] ^ jump.pairdiff[r60][6]),
           hw32(src.pairdiff[r60][7] ^ jump.pairdiff[r60][7]),
           src.w2[r61] - src.w1[r61], src.offsets[r61],
           jump.w2[r61] - jump.w1[r61], jump.offsets[r61],
           src.parts[r61][0], src.parts[r61][1], src.parts[r61][2], src.parts[r61][3],
           jump.parts[r61][0], jump.parts[r61][1], jump.parts[r61][2], jump.parts[r61][3],
           hw32(src.parts[r61][0] ^ jump.parts[r61][0]),
           hw32(src.parts[r61][1] ^ jump.parts[r61][1]),
           hw32(src.parts[r61][2] ^ jump.parts[r61][2]),
           hw32(src.parts[r61][3] ^ jump.parts[r61][3]),
           src.carries[r61][0], src.carries[r61][1], src.carries[r61][2],
           jump.carries[r61][0], jump.carries[r61][1], jump.carries[r61][2],
           hw32(src.carries[r61][0] ^ jump.carries[r61][0]),
           hw32(src.carries[r61][1] ^ jump.carries[r61][1]),
           hw32(src.carries[r61][2] ^ jump.carries[r61][2]),
           hw32(src.pairdiff[r61][0] ^ jump.pairdiff[r61][0]),
           hw32(src.pairdiff[r61][1] ^ jump.pairdiff[r61][1]),
           hw32(src.pairdiff[r61][2] ^ jump.pairdiff[r61][2]),
           hw32(src.pairdiff[r61][3] ^ jump.pairdiff[r61][3]),
           hw32(src.pairdiff[r61][4] ^ jump.pairdiff[r61][4]),
           hw32(src.pairdiff[r61][5] ^ jump.pairdiff[r61][5]),
           hw32(src.pairdiff[r61][6] ^ jump.pairdiff[r61][6]),
           hw32(src.pairdiff[r61][7] ^ jump.pairdiff[r61][7]));
}

static void kernel61_linear_point(int idx, const uint32_t x[3]) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"kernel61linearpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[64], cols61[64];
    uint64_t cols_pair[64];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns(&p1, &p2, x, &d60, &d61, cols60, cols61, cols_pair);

    uint64_t kernel[64];
    int rank60 = 0;
    int kernel_dim = kernel_basis_columns32(cols60, 64, kernel, &rank60);
    uint32_t kernel_cols61[64];
    for (int i = 0; i < kernel_dim; i++) {
        kernel_cols61[i] = combo_effect32(kernel[i], cols61);
    }
    int rank61_kernel = rank32_vectors(kernel_cols61, kernel_dim);

    int solvable_targets = 0;
    int best_actual_score = score60_61(d60, d61);
    int best_linear_residual_hw = hw32(d61);
    uint32_t best_linear_residual = d61;
    uint64_t best_selection = 0;
    uint64_t best_delta = 0;
    uint32_t best_x[3] = {x[0], x[1], x[2]};
    uint32_t best_defects[7];
    tail_defects_for_x(&p1, &p2, x, best_defects);

    int best_exact_d61_hw = (d60 == 0) ? hw32(d61) : 99;
    uint32_t best_exact_x[3] = {x[0], x[1], x[2]};
    uint32_t best_exact_defects[7];
    memcpy(best_exact_defects, best_defects, sizeof(best_exact_defects));
    uint64_t best_exact_delta = 0;
    uint32_t best_exact_linear_residual = d61;
    int best_moved_score = 9999;
    uint32_t best_moved_linear_residual = 0;
    uint64_t best_moved_delta = 0;
    uint32_t best_moved_x[3] = {x[0], x[1], x[2]};
    uint32_t best_moved_defects[7] = {0};

    for (int residual_bit = -1; residual_bit < 32; residual_bit++) {
        uint32_t residual = (residual_bit < 0) ? 0U : (1U << residual_bit);
        uint32_t target = d61 ^ residual;
        uint64_t selection = 0;
        int rank = 0;
        int ok = solve_linear_columns(target, kernel_cols61, kernel_dim,
                                      &selection, &rank);
        if (!ok) continue;
        solvable_targets++;
        uint64_t delta = combine_kernel_selection(selection, kernel);
        uint32_t y[3];
        uint32_t defects[7];
        apply_delta58_59(x, delta, y);
        tail_defects_for_x(&p1, &p2, y, defects);

        int actual_score = score60_61(defects[3], defects[4]);
        if (delta != 0 && (actual_score < best_moved_score ||
                           (actual_score == best_moved_score &&
                            defects[4] < best_moved_defects[4]))) {
            best_moved_score = actual_score;
            best_moved_linear_residual = residual;
            best_moved_delta = delta;
            memcpy(best_moved_x, y, sizeof(best_moved_x));
            memcpy(best_moved_defects, defects, sizeof(best_moved_defects));
        }
        int residual_hw = hw32(residual);
        if (actual_score < best_actual_score ||
            (actual_score == best_actual_score && residual_hw < best_linear_residual_hw) ||
            (actual_score == best_actual_score && residual_hw == best_linear_residual_hw &&
             defects[4] < best_defects[4])) {
            best_actual_score = actual_score;
            best_linear_residual_hw = residual_hw;
            best_linear_residual = residual;
            best_selection = selection;
            best_delta = delta;
            memcpy(best_x, y, sizeof(best_x));
            memcpy(best_defects, defects, sizeof(best_defects));
        }

        if (defects[3] == 0) {
            int d61_hw = hw32(defects[4]);
            if (d61_hw < best_exact_d61_hw ||
                (d61_hw == best_exact_d61_hw && defects[4] < best_exact_defects[4])) {
                best_exact_d61_hw = d61_hw;
                best_exact_delta = delta;
                best_exact_linear_residual = residual;
                memcpy(best_exact_x, y, sizeof(best_exact_x));
                memcpy(best_exact_defects, defects, sizeof(best_exact_defects));
            }
        }
    }

    printf("{\"mode\":\"kernel61linearpoint\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_defect60\":\"0x%08x\",\"base_defect61\":\"0x%08x\","
           "\"rank60\":%d,\"kernel_dim\":%d,\"rank61_on_kernel\":%d,"
           "\"solvable_targets\":%d,"
           "\"best_actual_score\":%d,\"best_linear_residual\":\"0x%08x\","
           "\"best_linear_residual_hw\":%d,"
           "\"best_delta\":\"0x%016llx\",\"best_delta_hw\":%d,"
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_moved_score\":%d,"
           "\"best_moved_linear_residual\":\"0x%08x\","
           "\"best_moved_delta\":\"0x%016llx\","
           "\"best_moved_delta_hw\":%d,"
           "\"best_moved_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_moved_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_d61_hw\":%d,"
           "\"best_exact_linear_residual\":\"0x%08x\","
           "\"best_exact_delta\":\"0x%016llx\","
           "\"best_exact_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx,
           x[0], x[1], x[2],
           d60, d61, rank60, kernel_dim, rank61_kernel, solvable_targets,
           best_actual_score, best_linear_residual, best_linear_residual_hw,
           (unsigned long long)best_delta,
           hw32((uint32_t)best_delta) + hw32((uint32_t)(best_delta >> 32)),
           best_x[0], best_x[1], best_x[2],
           best_defects[0], best_defects[1], best_defects[2], best_defects[3],
           best_defects[4], best_defects[5], best_defects[6],
           best_moved_score,
           best_moved_linear_residual,
           (unsigned long long)best_moved_delta,
           hw32((uint32_t)best_moved_delta) + hw32((uint32_t)(best_moved_delta >> 32)),
           best_moved_x[0], best_moved_x[1], best_moved_x[2],
           best_moved_defects[0], best_moved_defects[1], best_moved_defects[2],
           best_moved_defects[3], best_moved_defects[4], best_moved_defects[5],
           best_moved_defects[6],
           best_exact_d61_hw,
           best_exact_linear_residual,
           (unsigned long long)best_exact_delta,
           best_exact_x[0], best_exact_x[1], best_exact_x[2],
           best_exact_defects[0], best_exact_defects[1], best_exact_defects[2],
           best_exact_defects[3], best_exact_defects[4], best_exact_defects[5],
           best_exact_defects[6]);
}

static void kernel61_neighbor_point(int idx, const uint32_t x[3], int max_k) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_k < 1) max_k = 1;
    if (max_k > 6) max_k = 6;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"kernel61neighpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[64], cols61[64];
    uint64_t cols_pair[64];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns(&p1, &p2, x, &d60, &d61, cols60, cols61, cols_pair);

    uint64_t kernel[64];
    int rank60 = 0;
    int kernel_dim = kernel_basis_columns32(cols60, 64, kernel, &rank60);

    uint64_t checked = 1;
    uint64_t exact60 = (d60 == 0) ? 1 : 0;
    int best_exact_d61_hw = (d60 == 0) ? hw32(d61) : 99;
    uint32_t best_exact_d61 = d61;
    uint64_t best_exact_selection = 0;
    uint64_t best_exact_delta = 0;
    uint32_t best_exact_x[3] = {x[0], x[1], x[2]};
    uint32_t best_exact_defects[7] = {0};
    if (d60 == 0) {
        tail_defects_for_x(&p1, &p2, x, best_exact_defects);
    }

    int best_score = hw32(d60) * 64 + hw32(d61);
    uint32_t best_any_defects[7] = {0};
    uint32_t best_any_x[3] = {x[0], x[1], x[2]};
    uint64_t best_any_selection = 0;
    uint64_t best_any_delta = 0;
    tail_defects_for_x(&p1, &p2, x, best_any_defects);

    uint64_t limit = (kernel_dim >= 64) ? 0 : (1ULL << kernel_dim);
    for (int k = 1; k <= max_k && k <= kernel_dim; k++) {
        uint64_t selection = (1ULL << k) - 1ULL;
        while (selection && (limit == 0 || selection < limit)) {
            uint64_t delta = combine_kernel_selection(selection, kernel);
            uint32_t y[3];
            uint32_t defects[7];
            apply_delta58_59(x, delta, y);
            tail_defects_for_x(&p1, &p2, y, defects);
            checked++;

            int score = hw32(defects[3]) * 64 + hw32(defects[4]);
            if (score < best_score ||
                (score == best_score && defects[4] < best_any_defects[4])) {
                best_score = score;
                best_any_selection = selection;
                best_any_delta = delta;
                memcpy(best_any_x, y, sizeof(best_any_x));
                memcpy(best_any_defects, defects, sizeof(best_any_defects));
            }

            if (defects[3] == 0) {
                exact60++;
                int d61_hw = hw32(defects[4]);
                if (d61_hw < best_exact_d61_hw ||
                    (d61_hw == best_exact_d61_hw && defects[4] < best_exact_d61)) {
                    best_exact_d61_hw = d61_hw;
                    best_exact_d61 = defects[4];
                    best_exact_selection = selection;
                    best_exact_delta = delta;
                    memcpy(best_exact_x, y, sizeof(best_exact_x));
                    memcpy(best_exact_defects, defects, sizeof(best_exact_defects));
                }
            }

            selection = next_combination64(selection);
        }
    }

    printf("{\"mode\":\"kernel61neighpoint\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_defect60\":\"0x%08x\",\"base_defect61\":\"0x%08x\","
           "\"base_hw\":[%d,%d],\"rank60\":%d,\"kernel_dim\":%d,"
           "\"max_k\":%d,\"checked\":%llu,\"exact60\":%llu,"
           "\"best_exact_d61\":\"0x%08x\",\"best_exact_d61_hw\":%d,"
           "\"best_exact_selection\":\"0x%016llx\",\"best_exact_delta\":\"0x%016llx\","
           "\"best_exact_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_any_score\":%d,\"best_any_selection\":\"0x%016llx\","
           "\"best_any_delta\":\"0x%016llx\","
           "\"best_any_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_any_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx,
           x[0], x[1], x[2],
           d60, d61, hw32(d60), hw32(d61), rank60, kernel_dim,
           max_k, (unsigned long long)checked, (unsigned long long)exact60,
           best_exact_d61, best_exact_d61_hw,
           (unsigned long long)best_exact_selection,
           (unsigned long long)best_exact_delta,
           best_exact_x[0], best_exact_x[1], best_exact_x[2],
           best_exact_defects[0], best_exact_defects[1], best_exact_defects[2],
           best_exact_defects[3], best_exact_defects[4], best_exact_defects[5],
           best_exact_defects[6],
           best_score,
           (unsigned long long)best_any_selection,
           (unsigned long long)best_any_delta,
           best_any_x[0], best_any_x[1], best_any_x[2],
           best_any_defects[0], best_any_defects[1], best_any_defects[2],
           best_any_defects[3], best_any_defects[4], best_any_defects[5],
           best_any_defects[6]);
}

static void tail_neighbor_point(int idx, const uint32_t base_x[3], int max_k) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_k < 1) max_k = 1;
    if (max_k > 5) max_k = 5;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"tailneighpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t base_defects[7];
    tail_defects_for_x(&p1, &p2, base_x, base_defects);
    uint64_t checked = 1;
    uint64_t exact60 = (base_defects[3] == 0) ? 1 : 0;

    int best_exact_d61_hw = (base_defects[3] == 0) ? hw32(base_defects[4]) : 99;
    uint32_t best_exact_d61 = base_defects[4];
    uint32_t best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
    uint32_t best_exact_defects[7];
    memcpy(best_exact_defects, base_defects, sizeof(best_exact_defects));
    int best_exact_k = 0;
    uint64_t best_exact_combo = 0;

    int best_score = hw32(base_defects[3]) * 64 + hw32(base_defects[4]);
    uint32_t best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
    uint32_t best_any_defects[7];
    memcpy(best_any_defects, base_defects, sizeof(best_any_defects));
    int best_any_k = 0;
    uint64_t best_any_combo = 0;

    for (int k = 1; k <= max_k; k++) {
        uint64_t combo = (1ULL << k) - 1ULL;
        while (combo) {
            uint32_t x[3];
            uint32_t defects[7];
            apply_combo_to_x(base_x, combo, x);
            tail_defects_for_x(&p1, &p2, x, defects);
            checked++;

            int score = hw32(defects[3]) * 64 + hw32(defects[4]);
            if (score < best_score ||
                (score == best_score && defects[4] < best_any_defects[4])) {
                best_score = score;
                best_any_k = k;
                best_any_combo = combo;
                memcpy(best_any_x, x, sizeof(best_any_x));
                memcpy(best_any_defects, defects, sizeof(best_any_defects));
            }

            if (defects[3] == 0) {
                exact60++;
                int d61_hw = hw32(defects[4]);
                if (d61_hw < best_exact_d61_hw ||
                    (d61_hw == best_exact_d61_hw && defects[4] < best_exact_d61)) {
                    best_exact_d61_hw = d61_hw;
                    best_exact_d61 = defects[4];
                    best_exact_k = k;
                    best_exact_combo = combo;
                    memcpy(best_exact_x, x, sizeof(best_exact_x));
                    memcpy(best_exact_defects, defects, sizeof(best_exact_defects));
                }
            }

            uint64_t next = next_combination64(combo);
            if (!next || next < combo) break;
            combo = next;
        }
    }

    printf("{\"mode\":\"tailneighpoint\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"max_k\":%d,\"checked\":%llu,\"exact60\":%llu,"
           "\"best_exact_k\":%d,\"best_exact_combo\":\"0x%016llx\","
           "\"best_exact_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_d61_hw\":%d,"
           "\"best_any_score\":%d,\"best_any_k\":%d,"
           "\"best_any_combo\":\"0x%016llx\","
           "\"best_any_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_any_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx,
           base_x[0], base_x[1], base_x[2],
           base_defects[0], base_defects[1], base_defects[2], base_defects[3],
           base_defects[4], base_defects[5], base_defects[6],
           max_k, (unsigned long long)checked, (unsigned long long)exact60,
           best_exact_k, (unsigned long long)best_exact_combo,
           best_exact_x[0], best_exact_x[1], best_exact_x[2],
           best_exact_defects[0], best_exact_defects[1], best_exact_defects[2],
           best_exact_defects[3], best_exact_defects[4], best_exact_defects[5],
           best_exact_defects[6],
           best_exact_d61_hw,
           best_score, best_any_k, (unsigned long long)best_any_combo,
           best_any_x[0], best_any_x[1], best_any_x[2],
           best_any_defects[0], best_any_defects[1], best_any_defects[2],
           best_any_defects[3], best_any_defects[4], best_any_defects[5],
           best_any_defects[6]);
}

static inline int score60_61(uint32_t d60, uint32_t d61) {
    return hw32(d60) * 64 + hw32(d61);
}

static void tail_hill_fixed57_candidate(int idx, uint32_t fixed_w57,
                                        int trials, int threads, int max_passes) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"tailhill57\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58_fixed = compute_off58_for_w57(&p1, &p2, fixed_w57);
    int best_score = 9999;
    uint32_t best_x[3] = {fixed_w57, 0, 0};
    uint32_t best_defects[7] = {0};
    int best_passes = 0;
    int best_exact_d61_hw = 99;
    uint32_t best_exact_x[3] = {fixed_w57, 0, 0};
    uint32_t best_exact_defects[7] = {0};
    int exact60_hits = 0;
    int exact61_hits = 0;
    int total_evals = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x616d706c69667921ULL ^
                       ((uint64_t)cand->m0 << 17) ^
                       ((uint64_t)fixed_w57 << 5) ^
                       (uint64_t)tid;
        int local_best_score = 9999;
        uint32_t local_best_x[3] = {fixed_w57, 0, 0};
        uint32_t local_best_defects[7] = {0};
        int local_best_passes = 0;
        int local_best_exact_d61_hw = 99;
        uint32_t local_best_exact_x[3] = {fixed_w57, 0, 0};
        uint32_t local_best_exact_defects[7] = {0};
        int local_exact60_hits = 0;
        int local_exact61_hits = 0;
        int local_evals = 0;

        #pragma omp for schedule(dynamic, 4)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3] = {fixed_w57, splitmix32(&rng), splitmix32(&rng)};
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                x[1] = patterns[(i + 3) & 7];
                x[2] = patterns[(i + 5) & 7];
            }

            uint32_t cur_defects[7];
            tail_defects_for_x(&p1, &p2, x, cur_defects);
            local_evals++;
            int cur_score = score60_61(cur_defects[3], cur_defects[4]);
            int passes_used = 0;

            for (int pass = 0; pass < max_passes && cur_score > 0; pass++) {
                uint32_t best_step_x[3] = {x[0], x[1], x[2]};
                uint32_t best_step_defects[7];
                memcpy(best_step_defects, cur_defects, sizeof(best_step_defects));
                int best_step_score = cur_score;

                for (int bit = 0; bit < 64; bit++) {
                    uint32_t xf[3] = {x[0], x[1], x[2]};
                    if (bit < 32) xf[1] ^= 1U << bit;
                    else xf[2] ^= 1U << (bit - 32);
                    uint32_t defects[7];
                    tail_defects_for_x(&p1, &p2, xf, defects);
                    local_evals++;
                    int score = score60_61(defects[3], defects[4]);
                    if (score < best_step_score ||
                        (score == best_step_score && defects[4] < best_step_defects[4])) {
                        best_step_score = score;
                        memcpy(best_step_x, xf, sizeof(best_step_x));
                        memcpy(best_step_defects, defects, sizeof(best_step_defects));
                    }
                }

                if (best_step_score >= cur_score) break;
                memcpy(x, best_step_x, sizeof(x));
                memcpy(cur_defects, best_step_defects, sizeof(cur_defects));
                cur_score = best_step_score;
                passes_used = pass + 1;
            }

            if (cur_defects[3] == 0) {
                local_exact60_hits++;
                int d61_hw = hw32(cur_defects[4]);
                if (cur_defects[4] == 0) local_exact61_hits++;
                if (d61_hw < local_best_exact_d61_hw ||
                    (d61_hw == local_best_exact_d61_hw &&
                     cur_defects[4] < local_best_exact_defects[4])) {
                    local_best_exact_d61_hw = d61_hw;
                    memcpy(local_best_exact_x, x, sizeof(local_best_exact_x));
                    memcpy(local_best_exact_defects, cur_defects, sizeof(local_best_exact_defects));
                }
            }

            if (cur_score < local_best_score ||
                (cur_score == local_best_score && cur_defects[4] < local_best_defects[4])) {
                local_best_score = cur_score;
                memcpy(local_best_x, x, sizeof(local_best_x));
                memcpy(local_best_defects, cur_defects, sizeof(local_best_defects));
                local_best_passes = passes_used;
            }
        }

        #pragma omp critical
        {
            total_evals += local_evals;
            exact60_hits += local_exact60_hits;
            exact61_hits += local_exact61_hits;
            if (local_best_exact_d61_hw < best_exact_d61_hw ||
                (local_best_exact_d61_hw == best_exact_d61_hw &&
                 local_best_exact_defects[4] < best_exact_defects[4])) {
                best_exact_d61_hw = local_best_exact_d61_hw;
                memcpy(best_exact_x, local_best_exact_x, sizeof(best_exact_x));
                memcpy(best_exact_defects, local_best_exact_defects, sizeof(best_exact_defects));
            }
            if (local_best_score < best_score ||
                (local_best_score == best_score &&
                 local_best_defects[4] < best_defects[4])) {
                best_score = local_best_score;
                memcpy(best_x, local_best_x, sizeof(best_x));
                memcpy(best_defects, local_best_defects, sizeof(best_defects));
                best_passes = local_best_passes;
            }
        }
    }

    printf("{\"mode\":\"tailhill57\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"trials\":%d,\"max_passes\":%d,\"exact60_hits\":%d,"
           "\"exact61_hits\":%d,\"best_score\":%d,"
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_hw60_61\":[%d,%d],\"best_passes\":%d,"
           "\"best_exact_d61_hw\":%d,"
           "\"best_exact_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"evals\":%d}\n",
           cand->id, idx, fixed_w57, off58_fixed, hw32(off58_fixed),
           trials, max_passes, exact60_hits, exact61_hits, best_score,
           best_x[0], best_x[1], best_x[2],
           best_defects[0], best_defects[1], best_defects[2], best_defects[3],
           best_defects[4], best_defects[5], best_defects[6],
           hw32(best_defects[3]), hw32(best_defects[4]), best_passes,
           best_exact_d61_hw,
           best_exact_x[0], best_exact_x[1], best_exact_x[2],
           best_exact_defects[0], best_exact_defects[1], best_exact_defects[2],
           best_exact_defects[3], best_exact_defects[4], best_exact_defects[5],
           best_exact_defects[6],
           total_evals);
}

static void tail_hill_fixed58_candidate(int idx, uint32_t fixed_w57, uint32_t fixed_w58,
                                        int trials, int threads, int max_passes) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"tailhill58\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58 = 0;
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, &off58);
    uint32_t sched60 = sched_offset60_for_w57_w58(&p1, &p2, fixed_w57, fixed_w58, NULL);
    int best_score = 9999;
    uint32_t best_w59 = 0;
    uint32_t best_defects[7] = {0};
    int best_passes = 0;
    int best_exact_d61_hw = 99;
    uint32_t best_exact_w59 = 0;
    uint32_t best_exact_defects[7] = {0};
    int exact60_hits = 0;
    int exact61_hits = 0;
    int total_evals = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x3538353835353835ULL ^
                       ((uint64_t)fixed_w57 << 9) ^
                       ((uint64_t)fixed_w58 << 21) ^
                       (uint64_t)tid;
        int local_best_score = 9999;
        uint32_t local_best_w59 = 0;
        uint32_t local_best_defects[7] = {0};
        int local_best_passes = 0;
        int local_best_exact_d61_hw = 99;
        uint32_t local_best_exact_w59 = 0;
        uint32_t local_best_exact_defects[7] = {0};
        int local_exact60_hits = 0;
        int local_exact61_hits = 0;
        int local_evals = 0;

        #pragma omp for schedule(dynamic, 4)
        for (int i = 0; i < trials; i++) {
            uint32_t w59 = splitmix32(&rng);
            uint32_t x[3] = {fixed_w57, fixed_w58, w59};
            uint32_t cur_defects[7];
            tail_defects_for_x(&p1, &p2, x, cur_defects);
            local_evals++;
            int cur_score = score60_61(cur_defects[3], cur_defects[4]);
            int passes_used = 0;

            for (int pass = 0; pass < max_passes && cur_score > 0; pass++) {
                uint32_t best_step_w59 = w59;
                uint32_t best_step_defects[7];
                memcpy(best_step_defects, cur_defects, sizeof(best_step_defects));
                int best_step_score = cur_score;

                for (int bit = 0; bit < 32; bit++) {
                    uint32_t wf = w59 ^ (1U << bit);
                    uint32_t xf[3] = {fixed_w57, fixed_w58, wf};
                    uint32_t defects[7];
                    tail_defects_for_x(&p1, &p2, xf, defects);
                    local_evals++;
                    int score = score60_61(defects[3], defects[4]);
                    if (score < best_step_score ||
                        (score == best_step_score && defects[4] < best_step_defects[4])) {
                        best_step_score = score;
                        best_step_w59 = wf;
                        memcpy(best_step_defects, defects, sizeof(best_step_defects));
                    }
                }

                if (best_step_score >= cur_score) break;
                w59 = best_step_w59;
                memcpy(cur_defects, best_step_defects, sizeof(cur_defects));
                cur_score = best_step_score;
                passes_used = pass + 1;
            }

            if (cur_defects[3] == 0) {
                local_exact60_hits++;
                int d61_hw = hw32(cur_defects[4]);
                if (cur_defects[4] == 0) local_exact61_hits++;
                if (d61_hw < local_best_exact_d61_hw ||
                    (d61_hw == local_best_exact_d61_hw &&
                     cur_defects[4] < local_best_exact_defects[4])) {
                    local_best_exact_d61_hw = d61_hw;
                    local_best_exact_w59 = w59;
                    memcpy(local_best_exact_defects, cur_defects, sizeof(local_best_exact_defects));
                }
            }

            if (cur_score < local_best_score ||
                (cur_score == local_best_score && cur_defects[4] < local_best_defects[4])) {
                local_best_score = cur_score;
                local_best_w59 = w59;
                memcpy(local_best_defects, cur_defects, sizeof(local_best_defects));
                local_best_passes = passes_used;
            }
        }

        #pragma omp critical
        {
            total_evals += local_evals;
            exact60_hits += local_exact60_hits;
            exact61_hits += local_exact61_hits;
            if (local_best_exact_d61_hw < best_exact_d61_hw ||
                (local_best_exact_d61_hw == best_exact_d61_hw &&
                 local_best_exact_defects[4] < best_exact_defects[4])) {
                best_exact_d61_hw = local_best_exact_d61_hw;
                best_exact_w59 = local_best_exact_w59;
                memcpy(best_exact_defects, local_best_exact_defects, sizeof(best_exact_defects));
            }
            if (local_best_score < best_score ||
                (local_best_score == best_score &&
                 local_best_defects[4] < best_defects[4])) {
                best_score = local_best_score;
                best_w59 = local_best_w59;
                memcpy(best_defects, local_best_defects, sizeof(best_defects));
                best_passes = local_best_passes;
            }
        }
    }

    printf("{\"mode\":\"tailhill58\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"fixed_w58\":\"0x%08x\","
           "\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"off59\":\"0x%08x\",\"off59_hw\":%d,"
           "\"sched_offset60\":\"0x%08x\",\"trials\":%d,"
           "\"max_passes\":%d,\"exact60_hits\":%d,\"exact61_hits\":%d,"
           "\"best_score\":%d,\"best_w59\":\"0x%08x\","
           "\"best_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_hw60_61\":[%d,%d],\"best_passes\":%d,"
           "\"best_exact_d61_hw\":%d,\"best_exact_w59\":\"0x%08x\","
           "\"best_exact_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"evals\":%d}\n",
           cand->id, idx, fixed_w57, fixed_w58,
           off58, hw32(off58), off59, hw32(off59), sched60,
           trials, max_passes, exact60_hits, exact61_hits,
           best_score, best_w59,
           best_defects[0], best_defects[1], best_defects[2], best_defects[3],
           best_defects[4], best_defects[5], best_defects[6],
           hw32(best_defects[3]), hw32(best_defects[4]), best_passes,
           best_exact_d61_hw, best_exact_w59,
           best_exact_defects[0], best_exact_defects[1], best_exact_defects[2],
           best_exact_defects[3], best_exact_defects[4], best_exact_defects[5],
           best_exact_defects[6],
           total_evals);
}

static void surface61_walk_candidate(int idx, const uint32_t base_x[3],
                                     int trials, int threads, int max_iters,
                                     int max_flips) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 16) max_flips = 16;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"surface61walk\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t base_defects[7];
    tail_defects_for_x(&p1, &p2, base_x, base_defects);
    int best_d61_hw = (base_defects[3] == 0) ? hw32(base_defects[4]) : 99;
    uint32_t best_x[3] = {base_x[0], base_x[1], base_x[2]};
    uint32_t best_defects[7];
    memcpy(best_defects, base_defects, sizeof(best_defects));
    int best_iters = 0;
    int exact60_hits = (base_defects[3] == 0) ? 1 : 0;
    int exact61_hits = (base_defects[3] == 0 && base_defects[4] == 0) ? 1 : 0;
    int projection_failures = 0;
    int total_iters = 0;
    int changed_exact60_hits = 0;
    int max_exact_distance = 0;
    int d61_hw_hist[33];
    memset(d61_hw_hist, 0, sizeof(d61_hw_hist));
    if (base_defects[3] == 0) d61_hw_hist[hw32(base_defects[4])]++;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x7375726661636531ULL ^
                       ((uint64_t)cand->m0 << 15) ^
                       ((uint64_t)base_x[1] << 7) ^
                       ((uint64_t)base_x[2] << 29) ^
                       (uint64_t)tid;
        int local_best_d61_hw = best_d61_hw;
        uint32_t local_best_x[3] = {base_x[0], base_x[1], base_x[2]};
        uint32_t local_best_defects[7];
        memcpy(local_best_defects, base_defects, sizeof(local_best_defects));
        int local_best_iters = 0;
        int local_exact60_hits = 0;
        int local_exact61_hits = 0;
        int local_projection_failures = 0;
        int local_total_iters = 0;
        int local_changed_exact60_hits = 0;
        int local_max_exact_distance = 0;
        int local_d61_hw_hist[33];
        memset(local_d61_hw_hist, 0, sizeof(local_d61_hw_hist));

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3];
            if (local_best_d61_hw < 99 && (splitmix32(&rng) & 1U)) {
                memcpy(x, local_best_x, sizeof(x));
            } else {
                memcpy(x, base_x, 3 * sizeof(uint32_t));
            }

            int flips = 1 + (int)(splitmix32(&rng) % (uint32_t)max_flips);
            for (int f = 0; f < flips; f++) {
                int bit = (int)(splitmix32(&rng) & 63U);
                if (bit < 32) x[1] ^= 1U << bit;
                else x[2] ^= 1U << (bit - 32);
            }

            int iters = 0, last_rank = 0;
            uint32_t last_defect = 0;
            int ok = defect_newton_once(&p1, &p2, x, max_iters,
                                        &iters, &last_rank, &last_defect);
            local_total_iters += iters;
            if (!ok) {
                local_projection_failures++;
                continue;
            }

            uint32_t defects[7];
            tail_defects_for_x(&p1, &p2, x, defects);
            if (defects[3] != 0) {
                local_projection_failures++;
                continue;
            }

            local_exact60_hits++;
            int d61_hw = hw32(defects[4]);
            int exact_distance = hw32(x[1] ^ base_x[1]) + hw32(x[2] ^ base_x[2]);
            if (exact_distance > 0) local_changed_exact60_hits++;
            if (exact_distance > local_max_exact_distance) {
                local_max_exact_distance = exact_distance;
            }
            local_d61_hw_hist[d61_hw]++;
            if (defects[4] == 0) local_exact61_hits++;
            if (d61_hw < local_best_d61_hw ||
                (d61_hw == local_best_d61_hw && defects[4] < local_best_defects[4])) {
                local_best_d61_hw = d61_hw;
                memcpy(local_best_x, x, sizeof(local_best_x));
                memcpy(local_best_defects, defects, sizeof(local_best_defects));
                local_best_iters = iters;
            }
        }

        #pragma omp critical
        {
            exact60_hits += local_exact60_hits;
            exact61_hits += local_exact61_hits;
            projection_failures += local_projection_failures;
            total_iters += local_total_iters;
            changed_exact60_hits += local_changed_exact60_hits;
            if (local_max_exact_distance > max_exact_distance) {
                max_exact_distance = local_max_exact_distance;
            }
            for (int h = 0; h <= 32; h++) {
                d61_hw_hist[h] += local_d61_hw_hist[h];
            }
            if (local_best_d61_hw < best_d61_hw ||
                (local_best_d61_hw == best_d61_hw &&
                 local_best_defects[4] < best_defects[4])) {
                best_d61_hw = local_best_d61_hw;
                memcpy(best_x, local_best_x, sizeof(best_x));
                memcpy(best_defects, local_best_defects, sizeof(best_defects));
                best_iters = local_best_iters;
            }
        }
    }

    uint32_t off58 = 0;
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, best_x[0], best_x[1], &off58);
    printf("{\"mode\":\"surface61walk\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"trials\":%d,\"max_iters\":%d,\"max_flips\":%d,"
           "\"exact60_hits\":%d,\"exact61_hits\":%d,"
           "\"changed_exact60_hits\":%d,\"max_exact_distance\":%d,"
           "\"projection_failures\":%d,\"avg_projection_iters\":%.3f,"
           "\"d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_d61_hw\":%d,\"best_iters\":%d,"
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_off58\":\"0x%08x\",\"best_off59\":\"0x%08x\","
           "\"best_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx,
           base_x[0], base_x[1], base_x[2],
           base_defects[0], base_defects[1], base_defects[2], base_defects[3],
           base_defects[4], base_defects[5], base_defects[6],
           trials, max_iters, max_flips, exact60_hits, exact61_hits,
           changed_exact60_hits, max_exact_distance,
           projection_failures,
           trials ? (double)total_iters / (double)trials : 0.0,
           d61_hw_hist[0], d61_hw_hist[1], d61_hw_hist[2], d61_hw_hist[3],
           d61_hw_hist[4], d61_hw_hist[5], d61_hw_hist[6], d61_hw_hist[7],
           d61_hw_hist[8], d61_hw_hist[9], d61_hw_hist[10], d61_hw_hist[11],
           d61_hw_hist[12], d61_hw_hist[13], d61_hw_hist[14], d61_hw_hist[15],
           d61_hw_hist[16], d61_hw_hist[17], d61_hw_hist[18], d61_hw_hist[19],
           d61_hw_hist[20], d61_hw_hist[21], d61_hw_hist[22], d61_hw_hist[23],
           d61_hw_hist[24], d61_hw_hist[25], d61_hw_hist[26], d61_hw_hist[27],
           d61_hw_hist[28], d61_hw_hist[29], d61_hw_hist[30], d61_hw_hist[31],
           d61_hw_hist[32],
           best_d61_hw, best_iters,
           best_x[0], best_x[1], best_x[2], off58, off59,
           best_defects[0], best_defects[1], best_defects[2], best_defects[3],
           best_defects[4], best_defects[5], best_defects[6]);
}

static void surface61_sample_fixed57_candidate(int idx, uint32_t fixed_w57,
                                               int trials, int threads,
                                               int max_iters) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"surface61sample\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58 = compute_off58_for_w57(&p1, &p2, fixed_w57);
    int successes = 0;
    int exact61_hits = 0;
    int projection_failures = 0;
    int rank_failures = 0;
    int total_success_iters = 0;
    int d61_hw_hist[33];
    memset(d61_hw_hist, 0, sizeof(d61_hw_hist));

    int best_d61_hw = 99;
    uint32_t best_x[3] = {fixed_w57, 0, 0};
    uint32_t best_defects[7] = {0};
    int best_iters = 0;
    int best_tail_hw = 999;
    uint32_t best_tail_x[3] = {fixed_w57, 0, 0};
    uint32_t best_tail_defects[7] = {0};

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x6578616374737572ULL ^
                       ((uint64_t)cand->m0 << 11) ^
                       ((uint64_t)fixed_w57 << 19) ^
                       (uint64_t)tid;
        int local_successes = 0;
        int local_exact61_hits = 0;
        int local_projection_failures = 0;
        int local_rank_failures = 0;
        int local_total_success_iters = 0;
        int local_d61_hw_hist[33];
        memset(local_d61_hw_hist, 0, sizeof(local_d61_hw_hist));

        int local_best_d61_hw = 99;
        uint32_t local_best_x[3] = {fixed_w57, 0, 0};
        uint32_t local_best_defects[7] = {0};
        int local_best_iters = 0;
        int local_best_tail_hw = 999;
        uint32_t local_best_tail_x[3] = {fixed_w57, 0, 0};
        uint32_t local_best_tail_defects[7] = {0};

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3] = {fixed_w57, splitmix32(&rng), splitmix32(&rng)};
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
            int ok = defect_newton_once(&p1, &p2, x, max_iters,
                                        &iters, &last_rank, &last_defect);
            if (!ok) {
                local_projection_failures++;
                if (last_rank < 32) local_rank_failures++;
                continue;
            }

            uint32_t defects[7];
            tail_defects_for_x(&p1, &p2, x, defects);
            if (defects[3] != 0) {
                local_projection_failures++;
                continue;
            }

            local_successes++;
            local_total_success_iters += iters;
            int d61_hw = hw32(defects[4]);
            local_d61_hw_hist[d61_hw]++;
            if (defects[4] == 0) local_exact61_hits++;
            if (d61_hw < local_best_d61_hw ||
                (d61_hw == local_best_d61_hw && defects[4] < local_best_defects[4])) {
                local_best_d61_hw = d61_hw;
                memcpy(local_best_x, x, sizeof(local_best_x));
                memcpy(local_best_defects, defects, sizeof(local_best_defects));
                local_best_iters = iters;
            }

            tail_trace_t trace;
            tail_trace_for_x(&p1, &p2, x, &trace);
            int tail_hw = sha256_eval_tail(&p1, &p2, trace.w1, trace.w2);
            if (tail_hw < local_best_tail_hw ||
                (tail_hw == local_best_tail_hw && d61_hw < hw32(local_best_tail_defects[4]))) {
                local_best_tail_hw = tail_hw;
                memcpy(local_best_tail_x, x, sizeof(local_best_tail_x));
                memcpy(local_best_tail_defects, defects, sizeof(local_best_tail_defects));
            }
        }

        #pragma omp critical
        {
            successes += local_successes;
            exact61_hits += local_exact61_hits;
            projection_failures += local_projection_failures;
            rank_failures += local_rank_failures;
            total_success_iters += local_total_success_iters;
            for (int h = 0; h <= 32; h++) {
                d61_hw_hist[h] += local_d61_hw_hist[h];
            }
            if (local_best_d61_hw < best_d61_hw ||
                (local_best_d61_hw == best_d61_hw &&
                 local_best_defects[4] < best_defects[4])) {
                best_d61_hw = local_best_d61_hw;
                memcpy(best_x, local_best_x, sizeof(best_x));
                memcpy(best_defects, local_best_defects, sizeof(best_defects));
                best_iters = local_best_iters;
            }
            if (local_best_tail_hw < best_tail_hw ||
                (local_best_tail_hw == best_tail_hw &&
                 hw32(local_best_tail_defects[4]) < hw32(best_tail_defects[4]))) {
                best_tail_hw = local_best_tail_hw;
                memcpy(best_tail_x, local_best_tail_x, sizeof(best_tail_x));
                memcpy(best_tail_defects, local_best_tail_defects, sizeof(best_tail_defects));
            }
        }
    }

    uint32_t best_off59 = compute_off59_for_w57_w58(&p1, &p2, best_x[0], best_x[1], NULL);
    uint32_t best_tail_off59 = compute_off59_for_w57_w58(&p1, &p2,
                                                         best_tail_x[0],
                                                         best_tail_x[1], NULL);
    printf("{\"mode\":\"surface61sample\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"trials\":%d,\"max_iters\":%d,\"successes\":%d,"
           "\"success_rate\":%.6f,\"avg_success_iters\":%.3f,"
           "\"projection_failures\":%d,\"rank_failures\":%d,"
           "\"exact61_hits\":%d,"
           "\"d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_d61_hw\":%d,\"best_iters\":%d,"
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_off59\":\"0x%08x\","
           "\"best_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_tail_hw\":%d,"
           "\"best_tail_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_tail_off59\":\"0x%08x\","
           "\"best_tail_point_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx, fixed_w57, off58, hw32(off58),
           trials, max_iters, successes,
           trials ? (double)successes / (double)trials : 0.0,
           successes ? (double)total_success_iters / (double)successes : 0.0,
           projection_failures, rank_failures, exact61_hits,
           d61_hw_hist[0], d61_hw_hist[1], d61_hw_hist[2], d61_hw_hist[3],
           d61_hw_hist[4], d61_hw_hist[5], d61_hw_hist[6], d61_hw_hist[7],
           d61_hw_hist[8], d61_hw_hist[9], d61_hw_hist[10], d61_hw_hist[11],
           d61_hw_hist[12], d61_hw_hist[13], d61_hw_hist[14], d61_hw_hist[15],
           d61_hw_hist[16], d61_hw_hist[17], d61_hw_hist[18], d61_hw_hist[19],
           d61_hw_hist[20], d61_hw_hist[21], d61_hw_hist[22], d61_hw_hist[23],
           d61_hw_hist[24], d61_hw_hist[25], d61_hw_hist[26], d61_hw_hist[27],
           d61_hw_hist[28], d61_hw_hist[29], d61_hw_hist[30], d61_hw_hist[31],
           d61_hw_hist[32],
           best_d61_hw, best_iters,
           best_x[0], best_x[1], best_x[2], best_off59,
           best_defects[0], best_defects[1], best_defects[2], best_defects[3],
           best_defects[4], best_defects[5], best_defects[6],
           best_tail_hw,
           best_tail_x[0], best_tail_x[1], best_tail_x[2], best_tail_off59,
           best_tail_defects[0], best_tail_defects[1], best_tail_defects[2],
           best_tail_defects[3], best_tail_defects[4], best_tail_defects[5],
           best_tail_defects[6]);
}

static void surface61_greedy_walk_candidate(int idx, const uint32_t base_x[3],
                                            int trials, int threads,
                                            int max_passes, int max_flips) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 32) max_flips = 32;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"surface61greedywalk\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t base_defects[7];
    tail_defects_for_x(&p1, &p2, base_x, base_defects);
    int best_d61_hw = (base_defects[3] == 0) ? hw32(base_defects[4]) : 99;
    uint32_t best_x[3] = {base_x[0], base_x[1], base_x[2]};
    uint32_t best_defects[7];
    memcpy(best_defects, base_defects, sizeof(best_defects));
    int best_passes = 0;
    int best_changed_d61_hw = 99;
    uint32_t best_changed_x[3] = {base_x[0], base_x[1], base_x[2]};
    uint32_t best_changed_defects[7] = {0};
    int best_changed_passes = 0;
    int best_exact_tail_hw = 999;
    uint32_t best_exact_tail_x[3] = {base_x[0], base_x[1], base_x[2]};
    uint32_t best_exact_tail_defects[7] = {0};
    int best_changed_tail_hw = 999;
    uint32_t best_changed_tail_x[3] = {base_x[0], base_x[1], base_x[2]};
    uint32_t best_changed_tail_defects[7] = {0};
    int exact60_hits = (base_defects[3] == 0) ? 1 : 0;
    int exact61_hits = (base_defects[3] == 0 && base_defects[4] == 0) ? 1 : 0;
    int changed_exact60_hits = 0;
    int projection_failures = 0;
    int max_exact_distance = 0;
    int d61_hw_hist[33];
    memset(d61_hw_hist, 0, sizeof(d61_hw_hist));
    if (base_defects[3] == 0) d61_hw_hist[hw32(base_defects[4])]++;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x6772656564793631ULL ^
                       ((uint64_t)cand->m0 << 23) ^
                       ((uint64_t)base_x[1] << 3) ^
                       ((uint64_t)base_x[2] << 31) ^
                       (uint64_t)tid;
        int local_best_d61_hw = best_d61_hw;
        uint32_t local_best_x[3] = {base_x[0], base_x[1], base_x[2]};
        uint32_t local_best_defects[7];
        memcpy(local_best_defects, base_defects, sizeof(local_best_defects));
        int local_best_passes = 0;
        int local_best_changed_d61_hw = 99;
        uint32_t local_best_changed_x[3] = {base_x[0], base_x[1], base_x[2]};
        uint32_t local_best_changed_defects[7] = {0};
        int local_best_changed_passes = 0;
        int local_best_exact_tail_hw = 999;
        uint32_t local_best_exact_tail_x[3] = {base_x[0], base_x[1], base_x[2]};
        uint32_t local_best_exact_tail_defects[7] = {0};
        int local_best_changed_tail_hw = 999;
        uint32_t local_best_changed_tail_x[3] = {base_x[0], base_x[1], base_x[2]};
        uint32_t local_best_changed_tail_defects[7] = {0};
        int local_exact60_hits = 0;
        int local_exact61_hits = 0;
        int local_changed_exact60_hits = 0;
        int local_projection_failures = 0;
        int local_max_exact_distance = 0;
        int local_d61_hw_hist[33];
        memset(local_d61_hw_hist, 0, sizeof(local_d61_hw_hist));

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3];
            if (local_best_d61_hw < 99 && (splitmix32(&rng) & 1U)) {
                memcpy(x, local_best_x, sizeof(x));
            } else {
                memcpy(x, base_x, 3 * sizeof(uint32_t));
            }

            int flips = 1 + (int)(splitmix32(&rng) % (uint32_t)max_flips);
            for (int f = 0; f < flips; f++) {
                int bit = (int)(splitmix32(&rng) & 63U);
                if (bit < 32) x[1] ^= 1U << bit;
                else x[2] ^= 1U << (bit - 32);
            }

            eval_t cur = eval_defect(&p1, &p2, x);
            int passes_used = 0;
            for (int pass = 0; pass < max_passes && cur.defect != 0; pass++) {
                uint32_t best_step_x[3] = {x[0], x[1], x[2]};
                eval_t best_step = cur;

                for (int bit = 0; bit < 64; bit++) {
                    uint32_t xf[3] = {x[0], x[1], x[2]};
                    if (bit < 32) xf[1] ^= 1U << bit;
                    else xf[2] ^= 1U << (bit - 32);
                    eval_t y = eval_defect(&p1, &p2, xf);
                    if (y.defect_hw < best_step.defect_hw ||
                        (y.defect_hw == best_step.defect_hw &&
                         y.defect < best_step.defect)) {
                        best_step = y;
                        best_step_x[1] = xf[1];
                        best_step_x[2] = xf[2];
                    }
                }

                if (best_step.defect_hw >= cur.defect_hw) break;
                x[1] = best_step_x[1];
                x[2] = best_step_x[2];
                cur = best_step;
                passes_used = pass + 1;
            }

            if (cur.defect != 0) {
                local_projection_failures++;
                continue;
            }

            uint32_t defects[7];
            tail_defects_for_x(&p1, &p2, x, defects);
            tail_trace_t trace;
            tail_trace_for_x(&p1, &p2, x, &trace);
            int tail_hw = sha256_eval_tail(&p1, &p2, trace.w1, trace.w2);
            local_exact60_hits++;
            int d61_hw = hw32(defects[4]);
            local_d61_hw_hist[d61_hw]++;
            if (defects[4] == 0) local_exact61_hits++;
            int exact_distance = hw32(x[1] ^ base_x[1]) + hw32(x[2] ^ base_x[2]);
            if (exact_distance > 0) local_changed_exact60_hits++;
            if (exact_distance > local_max_exact_distance) {
                local_max_exact_distance = exact_distance;
            }
            if (tail_hw < local_best_exact_tail_hw ||
                (tail_hw == local_best_exact_tail_hw &&
                 d61_hw < hw32(local_best_exact_tail_defects[4]))) {
                local_best_exact_tail_hw = tail_hw;
                memcpy(local_best_exact_tail_x, x, sizeof(local_best_exact_tail_x));
                memcpy(local_best_exact_tail_defects, defects, sizeof(local_best_exact_tail_defects));
            }
            if (exact_distance > 0 &&
                (tail_hw < local_best_changed_tail_hw ||
                 (tail_hw == local_best_changed_tail_hw &&
                  d61_hw < hw32(local_best_changed_tail_defects[4])))) {
                local_best_changed_tail_hw = tail_hw;
                memcpy(local_best_changed_tail_x, x, sizeof(local_best_changed_tail_x));
                memcpy(local_best_changed_tail_defects, defects, sizeof(local_best_changed_tail_defects));
            }
            if (exact_distance > 0 &&
                (d61_hw < local_best_changed_d61_hw ||
                 (d61_hw == local_best_changed_d61_hw &&
                  defects[4] < local_best_changed_defects[4]))) {
                local_best_changed_d61_hw = d61_hw;
                memcpy(local_best_changed_x, x, sizeof(local_best_changed_x));
                memcpy(local_best_changed_defects, defects, sizeof(local_best_changed_defects));
                local_best_changed_passes = passes_used;
            }
            if (d61_hw < local_best_d61_hw ||
                (d61_hw == local_best_d61_hw && defects[4] < local_best_defects[4])) {
                local_best_d61_hw = d61_hw;
                memcpy(local_best_x, x, sizeof(local_best_x));
                memcpy(local_best_defects, defects, sizeof(local_best_defects));
                local_best_passes = passes_used;
            }
        }

        #pragma omp critical
        {
            exact60_hits += local_exact60_hits;
            exact61_hits += local_exact61_hits;
            changed_exact60_hits += local_changed_exact60_hits;
            projection_failures += local_projection_failures;
            if (local_max_exact_distance > max_exact_distance) {
                max_exact_distance = local_max_exact_distance;
            }
            for (int h = 0; h <= 32; h++) {
                d61_hw_hist[h] += local_d61_hw_hist[h];
            }
            if (local_best_d61_hw < best_d61_hw ||
                (local_best_d61_hw == best_d61_hw &&
                 local_best_defects[4] < best_defects[4])) {
                best_d61_hw = local_best_d61_hw;
                memcpy(best_x, local_best_x, sizeof(best_x));
                memcpy(best_defects, local_best_defects, sizeof(best_defects));
                best_passes = local_best_passes;
            }
            if (local_best_changed_d61_hw < best_changed_d61_hw ||
                (local_best_changed_d61_hw == best_changed_d61_hw &&
                 local_best_changed_defects[4] < best_changed_defects[4])) {
                best_changed_d61_hw = local_best_changed_d61_hw;
                memcpy(best_changed_x, local_best_changed_x, sizeof(best_changed_x));
                memcpy(best_changed_defects, local_best_changed_defects, sizeof(best_changed_defects));
                best_changed_passes = local_best_changed_passes;
            }
            if (local_best_exact_tail_hw < best_exact_tail_hw ||
                (local_best_exact_tail_hw == best_exact_tail_hw &&
                 hw32(local_best_exact_tail_defects[4]) < hw32(best_exact_tail_defects[4]))) {
                best_exact_tail_hw = local_best_exact_tail_hw;
                memcpy(best_exact_tail_x, local_best_exact_tail_x, sizeof(best_exact_tail_x));
                memcpy(best_exact_tail_defects, local_best_exact_tail_defects, sizeof(best_exact_tail_defects));
            }
            if (local_best_changed_tail_hw < best_changed_tail_hw ||
                (local_best_changed_tail_hw == best_changed_tail_hw &&
                 hw32(local_best_changed_tail_defects[4]) < hw32(best_changed_tail_defects[4]))) {
                best_changed_tail_hw = local_best_changed_tail_hw;
                memcpy(best_changed_tail_x, local_best_changed_tail_x, sizeof(best_changed_tail_x));
                memcpy(best_changed_tail_defects, local_best_changed_tail_defects, sizeof(best_changed_tail_defects));
            }
        }
    }

    uint32_t off58 = 0;
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, best_x[0], best_x[1], &off58);
    uint32_t changed_off58 = 0;
    uint32_t changed_off59 = compute_off59_for_w57_w58(&p1, &p2,
                                                       best_changed_x[0],
                                                       best_changed_x[1],
                                                       &changed_off58);
    tail_trace_t trace;
    tail_trace_for_x(&p1, &p2, best_x, &trace);
    int best_tail_hw = sha256_eval_tail(&p1, &p2, trace.w1, trace.w2);
    int best_changed_d61_tail_hw = 999;
    if (best_changed_d61_hw < 99) {
        tail_trace_for_x(&p1, &p2, best_changed_x, &trace);
        best_changed_d61_tail_hw = sha256_eval_tail(&p1, &p2, trace.w1, trace.w2);
    }

    printf("{\"mode\":\"surface61greedywalk\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"trials\":%d,\"max_passes\":%d,\"max_flips\":%d,"
           "\"exact60_hits\":%d,\"exact61_hits\":%d,"
           "\"changed_exact60_hits\":%d,\"max_exact_distance\":%d,"
           "\"projection_failures\":%d,"
           "\"d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_d61_hw\":%d,\"best_passes\":%d,"
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_off58\":\"0x%08x\",\"best_off59\":\"0x%08x\","
           "\"best_tail_hw\":%d,"
           "\"best_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_changed_d61_hw\":%d,\"best_changed_passes\":%d,"
           "\"best_changed_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_changed_off58\":\"0x%08x\",\"best_changed_off59\":\"0x%08x\","
           "\"best_changed_tail_hw\":%d,"
           "\"best_changed_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_tail_hw\":%d,"
           "\"best_exact_tail_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_exact_tail_point_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_changed_tail_selected_hw\":%d,"
           "\"best_changed_tail_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_changed_tail_selected_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"]}\n",
           cand->id, idx,
           base_x[0], base_x[1], base_x[2],
           base_defects[0], base_defects[1], base_defects[2], base_defects[3],
           base_defects[4], base_defects[5], base_defects[6],
           trials, max_passes, max_flips,
           exact60_hits, exact61_hits, changed_exact60_hits,
           max_exact_distance, projection_failures,
           d61_hw_hist[0], d61_hw_hist[1], d61_hw_hist[2], d61_hw_hist[3],
           d61_hw_hist[4], d61_hw_hist[5], d61_hw_hist[6], d61_hw_hist[7],
           d61_hw_hist[8], d61_hw_hist[9], d61_hw_hist[10], d61_hw_hist[11],
           d61_hw_hist[12], d61_hw_hist[13], d61_hw_hist[14], d61_hw_hist[15],
           d61_hw_hist[16], d61_hw_hist[17], d61_hw_hist[18], d61_hw_hist[19],
           d61_hw_hist[20], d61_hw_hist[21], d61_hw_hist[22], d61_hw_hist[23],
           d61_hw_hist[24], d61_hw_hist[25], d61_hw_hist[26], d61_hw_hist[27],
           d61_hw_hist[28], d61_hw_hist[29], d61_hw_hist[30], d61_hw_hist[31],
           d61_hw_hist[32],
           best_d61_hw, best_passes,
           best_x[0], best_x[1], best_x[2], off58, off59, best_tail_hw,
           best_defects[0], best_defects[1], best_defects[2], best_defects[3],
           best_defects[4], best_defects[5], best_defects[6],
           best_changed_d61_hw, best_changed_passes,
           best_changed_x[0], best_changed_x[1], best_changed_x[2],
           changed_off58, changed_off59, best_changed_d61_tail_hw,
           best_changed_defects[0], best_changed_defects[1], best_changed_defects[2],
           best_changed_defects[3], best_changed_defects[4],
           best_changed_defects[5], best_changed_defects[6],
           best_exact_tail_hw,
           best_exact_tail_x[0], best_exact_tail_x[1], best_exact_tail_x[2],
           best_exact_tail_defects[0], best_exact_tail_defects[1],
           best_exact_tail_defects[2], best_exact_tail_defects[3],
           best_exact_tail_defects[4], best_exact_tail_defects[5],
           best_exact_tail_defects[6],
           best_changed_tail_hw,
           best_changed_tail_x[0], best_changed_tail_x[1], best_changed_tail_x[2],
           best_changed_tail_defects[0], best_changed_tail_defects[1],
           best_changed_tail_defects[2], best_changed_tail_defects[3],
           best_changed_tail_defects[4], best_changed_tail_defects[5],
           best_changed_tail_defects[6]);
}

static int newton61_fixed57_once(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                                 uint32_t x[3], int max_iters, int *iters_out,
                                 int *last_rank_out, uint64_t *last_vec_out) {
    for (int iter = 0; iter < max_iters; iter++) {
        uint64_t base = defect60_61_vec(p1, p2, x);
        if (base == 0) {
            if (iters_out) *iters_out = iter;
            if (last_rank_out) *last_rank_out = 64;
            if (last_vec_out) *last_vec_out = 0;
            return 1;
        }

        uint64_t cols[64];
        for (int bit = 0; bit < 64; bit++) {
            uint32_t xf[3] = {x[0], x[1], x[2]};
            if (bit < 32) xf[1] ^= 1U << bit;
            else xf[2] ^= 1U << (bit - 32);
            cols[bit] = base ^ defect60_61_vec(p1, p2, xf);
        }

        uint64_t delta = 0;
        int rank = 0;
        int solvable = solve_linear_columns64(base, cols, 64, &delta, &rank);
        if (last_rank_out) *last_rank_out = rank;
        if (last_vec_out) *last_vec_out = base;
        if (!solvable || delta == 0) {
            if (iters_out) *iters_out = iter;
            return 0;
        }

        x[1] ^= (uint32_t)(delta & 0xffffffffULL);
        x[2] ^= (uint32_t)(delta >> 32);
    }

    uint64_t last = defect60_61_vec(p1, p2, x);
    if (iters_out) *iters_out = max_iters;
    if (last_vec_out) *last_vec_out = last;
    return last == 0;
}

static void newton61_point(int idx, uint32_t x[3], int max_iters) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"newton61point\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t start_x[3] = {x[0], x[1], x[2]};
    uint64_t start_vec = defect60_61_vec(&p1, &p2, x);
    int iters = 0, last_rank = 0;
    uint64_t last_vec = 0;
    int ok = newton61_fixed57_once(&p1, &p2, x, max_iters,
                                   &iters, &last_rank, &last_vec);
    uint32_t final_defects[7];
    tail_defects_for_x(&p1, &p2, x, final_defects);
    uint32_t off58 = 0;
    uint32_t off59 = compute_off59_for_w57_w58(&p1, &p2, x[0], x[1], &off58);

    printf("{\"mode\":\"newton61point\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"start_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"start_defect60\":\"0x%08x\",\"start_defect61\":\"0x%08x\","
           "\"start_hw60_61\":[%d,%d],"
           "\"ok\":%d,\"iters\":%d,\"last_rank\":%d,"
           "\"last_defect60\":\"0x%08x\",\"last_defect61\":\"0x%08x\","
           "\"final_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"final_off58\":\"0x%08x\",\"final_off59\":\"0x%08x\","
           "\"final_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"final_hw60_61\":[%d,%d]}\n",
           cand->id, idx,
           start_x[0], start_x[1], start_x[2],
           (uint32_t)start_vec, (uint32_t)(start_vec >> 32),
           hw32((uint32_t)start_vec), hw32((uint32_t)(start_vec >> 32)),
           ok, iters, last_rank,
           (uint32_t)last_vec, (uint32_t)(last_vec >> 32),
           x[0], x[1], x[2], off58, off59,
           final_defects[0], final_defects[1], final_defects[2],
           final_defects[3], final_defects[4], final_defects[5],
           final_defects[6],
           hw32(final_defects[3]), hw32(final_defects[4]));
}

static void defect_hill_fixed57_candidate(int idx, uint32_t fixed_w57,
                                          int trials, int threads, int max_passes) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"defecthill57\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58_fixed = compute_off58_for_w57(&p1, &p2, fixed_w57);
    int best_hw = 99;
    uint32_t best_defect = 0;
    uint32_t best_x[3] = {fixed_w57, 0, 0};
    int best_passes = 0;
    int total_evals = 0;
    int exact_hits = 0;
    int best_exact_d61_hw = 99;
    uint32_t best_exact_d61 = 0;
    uint32_t best_exact_x[3] = {fixed_w57, 0, 0};

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x57575757abcdef01ULL ^
                       ((uint64_t)cand->m0 << 11) ^
                       ((uint64_t)fixed_w57 << 25) ^
                       (uint64_t)tid;
        int local_best_hw = 99;
        uint32_t local_best_defect = 0;
        uint32_t local_best_x[3] = {fixed_w57, 0, 0};
        int local_best_passes = 0;
        int local_evals = 0;
        int local_exact_hits = 0;
        int local_best_exact_d61_hw = 99;
        uint32_t local_best_exact_d61 = 0;
        uint32_t local_best_exact_x[3] = {fixed_w57, 0, 0};

        #pragma omp for schedule(dynamic, 4)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3] = {fixed_w57, splitmix32(&rng), splitmix32(&rng)};
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                x[1] = patterns[(i + 3) & 7];
                x[2] = patterns[(i + 5) & 7];
            }

            eval_t base = eval_defect(&p1, &p2, x);
            local_evals++;
            int cur_hw = base.defect_hw;
            uint32_t cur_defect = base.defect;
            int passes_used = 0;

            for (int pass = 0; pass < max_passes && cur_hw > 0; pass++) {
                uint32_t best_step_x[3] = {x[0], x[1], x[2]};
                uint32_t best_step_defect = cur_defect;
                int best_step_hw = cur_hw;

                for (int bit = 0; bit < 64; bit++) {
                    uint32_t xf[3] = {x[0], x[1], x[2]};
                    if (bit < 32) xf[1] ^= 1U << bit;
                    else xf[2] ^= 1U << (bit - 32);
                    eval_t y = eval_defect(&p1, &p2, xf);
                    local_evals++;
                    if (y.defect_hw < best_step_hw ||
                        (y.defect_hw == best_step_hw && y.defect < best_step_defect)) {
                        best_step_hw = y.defect_hw;
                        best_step_defect = y.defect;
                        best_step_x[1] = xf[1];
                        best_step_x[2] = xf[2];
                    }
                }

                if (best_step_hw >= cur_hw) break;
                x[1] = best_step_x[1];
                x[2] = best_step_x[2];
                cur_defect = best_step_defect;
                cur_hw = best_step_hw;
                passes_used = pass + 1;
            }

            if (cur_hw == 0) {
                uint32_t defects[7];
                local_exact_hits++;
                tail_defects_for_x(&p1, &p2, x, defects);
                int d61_hw = hw32(defects[4]);
                if (d61_hw < local_best_exact_d61_hw ||
                    (d61_hw == local_best_exact_d61_hw && defects[4] < local_best_exact_d61)) {
                    local_best_exact_d61_hw = d61_hw;
                    local_best_exact_d61 = defects[4];
                    memcpy(local_best_exact_x, x, sizeof(local_best_exact_x));
                }
            }
            if (cur_hw < local_best_hw ||
                (cur_hw == local_best_hw && cur_defect < local_best_defect)) {
                local_best_hw = cur_hw;
                local_best_defect = cur_defect;
                memcpy(local_best_x, x, sizeof(local_best_x));
                local_best_passes = passes_used;
            }
        }

        #pragma omp critical
        {
            total_evals += local_evals;
            exact_hits += local_exact_hits;
            if (local_best_exact_d61_hw < best_exact_d61_hw ||
                (local_best_exact_d61_hw == best_exact_d61_hw &&
                 local_best_exact_d61 < best_exact_d61)) {
                best_exact_d61_hw = local_best_exact_d61_hw;
                best_exact_d61 = local_best_exact_d61;
                memcpy(best_exact_x, local_best_exact_x, sizeof(best_exact_x));
            }
            if (local_best_hw < best_hw ||
                (local_best_hw == best_hw && local_best_defect < best_defect)) {
                best_hw = local_best_hw;
                best_defect = local_best_defect;
                memcpy(best_x, local_best_x, sizeof(best_x));
                best_passes = local_best_passes;
            }
        }
    }

    uint32_t best_off59 = compute_off59_for_w57_w58(&p1, &p2, best_x[0], best_x[1], NULL);
    uint32_t best_sched = sched_offset60_for_w57_w58(&p1, &p2, best_x[0], best_x[1], NULL);
    printf("{\"mode\":\"defecthill57\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"trials\":%d,\"max_passes\":%d,\"exact_hits\":%d,"
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_hw\":%d,\"best_defect\":\"0x%08x\","
           "\"best_off59\":\"0x%08x\",\"best_off59_hw\":%d,"
           "\"best_sched\":\"0x%08x\",\"best_passes\":%d,"
           "\"best_exact_d61\":\"0x%08x\",\"best_exact_d61_hw\":%d,"
           "\"best_exact_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"evals\":%d}\n",
           cand->id, idx, fixed_w57, off58_fixed, hw32(off58_fixed),
           trials, max_passes, exact_hits,
           best_x[0], best_x[1], best_x[2], best_hw, best_defect,
           best_off59, hw32(best_off59), best_sched, best_passes,
           best_exact_d61, best_exact_d61_hw,
           best_exact_x[0], best_exact_x[1], best_exact_x[2],
           total_evals);
}

static void newton61_fixed57_candidate(int idx, uint32_t fixed_w57,
                                       int trials, int threads, int max_iters) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"newton61fixed57\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t off58 = compute_off58_for_w57(&p1, &p2, fixed_w57);
    int successes = 0;
    int rank_failures = 0;
    int total_success_iters = 0;
    int best_pair_hw = 99;
    uint64_t best_vec = 0;
    uint32_t best_x[3] = {fixed_w57, 0, 0};
    uint32_t first_success_x[3] = {fixed_w57, 0, 0};
    int first_success_iters = -1;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x616161615eedf00dULL ^
                       ((uint64_t)cand->m0 << 13) ^
                       ((uint64_t)fixed_w57 << 3) ^
                       (uint64_t)tid;
        int local_successes = 0;
        int local_rank_failures = 0;
        int local_iters = 0;
        int local_best_pair_hw = 99;
        uint64_t local_best_vec = 0;
        uint32_t local_best_x[3] = {fixed_w57, 0, 0};
        uint32_t local_first_x[3] = {fixed_w57, 0, 0};
        int local_first_iters = -1;

        #pragma omp for schedule(dynamic, 4)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3] = {fixed_w57, splitmix32(&rng), splitmix32(&rng)};
            if (i < 8) {
                static const uint32_t patterns[] = {
                    0x00000000U, 0xffffffffU, 0x55555555U, 0xaaaaaaaaU,
                    0x33333333U, 0xccccccccU, 0x0f0f0f0fU, 0xf0f0f0f0U
                };
                x[1] = patterns[(i + 3) & 7];
                x[2] = patterns[(i + 5) & 7];
            }

            int iters = 0, last_rank = 0;
            uint64_t last_vec = 0;
            int ok = newton61_fixed57_once(&p1, &p2, x, max_iters,
                                           &iters, &last_rank, &last_vec);
            if (ok) {
                local_successes++;
                local_iters += iters;
                if (local_first_iters < 0) {
                    local_first_iters = iters;
                    memcpy(local_first_x, x, sizeof(local_first_x));
                }
            } else {
                if (last_rank < 64) local_rank_failures++;
                int h = hw32((uint32_t)last_vec) + hw32((uint32_t)(last_vec >> 32));
                if (h < local_best_pair_hw) {
                    local_best_pair_hw = h;
                    local_best_vec = last_vec;
                    memcpy(local_best_x, x, sizeof(local_best_x));
                }
            }
        }

        #pragma omp critical
        {
            successes += local_successes;
            rank_failures += local_rank_failures;
            total_success_iters += local_iters;
            if (local_best_pair_hw < best_pair_hw) {
                best_pair_hw = local_best_pair_hw;
                best_vec = local_best_vec;
                memcpy(best_x, local_best_x, sizeof(best_x));
            }
            if (first_success_iters < 0 && local_first_iters >= 0) {
                first_success_iters = local_first_iters;
                memcpy(first_success_x, local_first_x, sizeof(first_success_x));
            }
        }
    }

    uint32_t first_off59 = 0;
    if (first_success_iters >= 0) {
        first_off59 = compute_off59_for_w57_w58(&p1, &p2,
                                                first_success_x[0],
                                                first_success_x[1], NULL);
    }
    printf("{\"mode\":\"newton61fixed57\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\",\"off58\":\"0x%08x\",\"off58_hw\":%d,"
           "\"trials\":%d,\"max_iters\":%d,\"successes\":%d,"
           "\"success_rate\":%.6f,\"avg_success_iters\":%.3f,"
           "\"rank_failures\":%d,\"best_pair_hw\":%d,"
           "\"best_defect60\":\"0x%08x\",\"best_defect61\":\"0x%08x\","
           "\"best_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"first_success_iters\":%d,"
           "\"first_success_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"first_success_off59\":\"0x%08x\"}\n",
           cand->id, idx, fixed_w57, off58, hw32(off58),
           trials, max_iters, successes,
           trials ? (double)successes / (double)trials : 0.0,
           successes ? (double)total_success_iters / (double)successes : 0.0,
           rank_failures, best_pair_hw,
           (uint32_t)best_vec, (uint32_t)(best_vec >> 32),
           best_x[0], best_x[1], best_x[2],
           first_success_iters,
           first_success_x[0], first_success_x[1], first_success_x[2],
           first_off59);
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
    if (argc >= 2 && strcmp(argv[1], "surface61greedywalk") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int trials = (argc >= 7) ? atoi(argv[6]) : 65536;
        int threads = (argc >= 8) ? atoi(argv[7]) : 8;
        int max_passes = (argc >= 9) ? atoi(argv[8]) : 64;
        int max_flips = (argc >= 10) ? atoi(argv[9]) : 12;
        sha256_init(32);
        surface61_greedy_walk_candidate(idx, x, trials, threads,
                                        max_passes, max_flips);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "surface61sample") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        int trials = (argc >= 5) ? atoi(argv[4]) : 65536;
        int threads = (argc >= 6) ? atoi(argv[5]) : 8;
        int max_iters = (argc >= 7) ? atoi(argv[6]) : 24;
        sha256_init(32);
        surface61_sample_fixed57_candidate(idx, fixed_w57,
                                           trials, threads, max_iters);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "kernel61linearpoint") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        sha256_init(32);
        kernel61_linear_point(idx, x);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "surface61walk") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int trials = (argc >= 7) ? atoi(argv[6]) : 65536;
        int threads = (argc >= 8) ? atoi(argv[7]) : 8;
        int max_iters = (argc >= 9) ? atoi(argv[8]) : 24;
        int max_flips = (argc >= 10) ? atoi(argv[9]) : 6;
        sha256_init(32);
        surface61_walk_candidate(idx, x, trials, threads, max_iters, max_flips);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "tailhill58") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        uint32_t fixed_w58 = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0;
        int trials = (argc >= 6) ? atoi(argv[5]) : 4096;
        int threads = (argc >= 7) ? atoi(argv[6]) : 8;
        int max_passes = (argc >= 8) ? atoi(argv[7]) : 64;
        sha256_init(32);
        tail_hill_fixed58_candidate(idx, fixed_w57, fixed_w58,
                                    trials, threads, max_passes);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "carryjump61point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        sha256_init(32);
        carryjump61_point(idx, x);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "newton61point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_iters = (argc >= 7) ? atoi(argv[6]) : 32;
        sha256_init(32);
        newton61_point(idx, x, max_iters);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "tailhill57") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        int trials = (argc >= 5) ? atoi(argv[4]) : 4096;
        int threads = (argc >= 6) ? atoi(argv[5]) : 8;
        int max_passes = (argc >= 7) ? atoi(argv[6]) : 64;
        sha256_init(32);
        tail_hill_fixed57_candidate(idx, fixed_w57, trials, threads, max_passes);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "tailneighpoint") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_k = (argc >= 7) ? atoi(argv[6]) : 5;
        sha256_init(32);
        tail_neighbor_point(idx, x, max_k);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "kernel61neighpoint") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_k = (argc >= 7) ? atoi(argv[6]) : 4;
        sha256_init(32);
        kernel61_neighbor_point(idx, x, max_k);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "manifold61point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        sha256_init(32);
        manifold61_point(idx, x);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "newton61fixed57") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        int trials = (argc >= 5) ? atoi(argv[4]) : 2048;
        int threads = (argc >= 6) ? atoi(argv[5]) : 8;
        int max_iters = (argc >= 7) ? atoi(argv[6]) : 32;
        sha256_init(32);
        newton61_fixed57_candidate(idx, fixed_w57, trials, threads, max_iters);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "tailpoint") == 0) {
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
            printf("{\"mode\":\"tailpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
                   cand->id);
            return 1;
        }

        uint32_t s1[8], s2[8];
        memcpy(s1, p1.state, sizeof(s1));
        memcpy(s2, p2.state, sizeof(s2));
        uint32_t offsets[4];
        for (int i = 0; i < 3; i++) {
            offsets[i] = cascade1_offset(s1, s2);
            apply_round(s1, x[i], 57 + i);
            apply_round(s2, x[i] + offsets[i], 57 + i);
        }
        offsets[3] = cascade1_offset(s1, s2);

        uint32_t w1[7], w2[7];
        w1[0] = x[0];
        w1[1] = x[1];
        w1[2] = x[2];
        w1[3] = sha256_sigma1(w1[1]) + p1.W[53] +
                sha256_sigma0(p1.W[45]) + p1.W[44];
        w2[0] = x[0] + offsets[0];
        w2[1] = x[1] + offsets[1];
        w2[2] = x[2] + offsets[2];
        w2[3] = sha256_sigma1(w2[1]) + p2.W[53] +
                sha256_sigma0(p2.W[45]) + p2.W[44];
        w1[4] = sha256_sigma1(w1[2]) + p1.W[54] +
                sha256_sigma0(p1.W[46]) + p1.W[45];
        w2[4] = sha256_sigma1(w2[2]) + p2.W[54] +
                sha256_sigma0(p2.W[46]) + p2.W[45];
        w1[5] = sha256_sigma1(w1[3]) + p1.W[55] +
                sha256_sigma0(p1.W[47]) + p1.W[46];
        w2[5] = sha256_sigma1(w2[3]) + p2.W[55] +
                sha256_sigma0(p2.W[47]) + p2.W[46];
        w1[6] = sha256_sigma1(w1[4]) + p1.W[56] +
                sha256_sigma0(p1.W[48]) + p1.W[47];
        w2[6] = sha256_sigma1(w2[4]) + p2.W[56] +
                sha256_sigma0(p2.W[48]) + p2.W[47];

        int tail_hw = sha256_eval_tail(&p1, &p2, w1, w2);

        uint32_t ts1[8], ts2[8], tail_offsets[7], tail_defects[7];
        memcpy(ts1, p1.state, sizeof(ts1));
        memcpy(ts2, p2.state, sizeof(ts2));
        for (int i = 0; i < 7; i++) {
            tail_offsets[i] = cascade1_offset(ts1, ts2);
            tail_defects[i] = (w2[i] - w1[i]) - tail_offsets[i];
            apply_round(ts1, w1[i], 57 + i);
            apply_round(ts2, w2[i], 57 + i);
        }

        printf("{\"mode\":\"tailpoint\",\"candidate_index\":%d,\"candidate\":\"%s\","
               "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"tail_offsets\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
               "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
               "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"w1_tail\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
               "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"w2_tail\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
               "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"tail_hw\":%d}\n",
               idx, cand->id, x[0], x[1], x[2],
               tail_offsets[0], tail_offsets[1], tail_offsets[2], tail_offsets[3],
               tail_offsets[4], tail_offsets[5], tail_offsets[6],
               tail_defects[0], tail_defects[1], tail_defects[2], tail_defects[3],
               tail_defects[4], tail_defects[5], tail_defects[6],
               w1[0], w1[1], w1[2], w1[3], w1[4], w1[5], w1[6],
               w2[0], w2[1], w2[2], w2[3], w2[4], w2[5], w2[6],
               tail_hw);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "defecthill57") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        int trials = (argc >= 5) ? atoi(argv[4]) : 4096;
        int threads = (argc >= 6) ? atoi(argv[5]) : 8;
        int max_passes = (argc >= 7) ? atoi(argv[6]) : 48;
        sha256_init(32);
        defect_hill_fixed57_candidate(idx, fixed_w57, trials, threads, max_passes);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "tracepoint") == 0) {
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
            printf("{\"mode\":\"tracepoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
                   cand->id);
            return 1;
        }

        uint32_t s1[8], s2[8];
        memcpy(s1, p1.state, sizeof(s1));
        memcpy(s2, p2.state, sizeof(s2));
        uint32_t offsets[3];
        for (int i = 0; i < 3; i++) {
            offsets[i] = cascade1_offset(s1, s2);
            apply_round(s1, x[i], 57 + i);
            apply_round(s2, x[i] + offsets[i], 57 + i);
        }

        uint32_t w1_sched60 = sha256_sigma1(x[1]) + p1.W[53] +
                               sha256_sigma0(p1.W[45]) + p1.W[44];
        uint32_t w2_58 = x[1] + offsets[1];
        uint32_t w2_sched60 = sha256_sigma1(w2_58) + p2.W[53] +
                               sha256_sigma0(p2.W[45]) + p2.W[44];
        uint32_t sched_offset60 = w2_sched60 - w1_sched60;

        uint32_t parts[4], sums[3], carries[3];
        cascade1_offset_parts(s1, s2, parts, sums, carries);
        uint32_t req_offset60 = sums[2];
        uint32_t defect = sched_offset60 - req_offset60;
        uint32_t delta_to_req = req_offset60 - sched_offset60;

        printf("{\"mode\":\"tracepoint\",\"candidate_index\":%d,\"candidate\":\"%s\","
               "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"offsets57_59\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"sched_offset60\":\"0x%08x\",\"req_offset60\":\"0x%08x\","
               "\"defect\":\"0x%08x\",\"defect_hw\":%d,"
               "\"delta_req_minus_sched\":\"0x%08x\","
               "\"req_parts\":{\"dh\":\"0x%08x\",\"dSig1\":\"0x%08x\","
               "\"dCh\":\"0x%08x\",\"dT2\":\"0x%08x\"},"
               "\"req_sums\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"req_carries\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"req_carry_hw\":[%d,%d,%d],"
               "\"state_xor_hw_after59\":[%d,%d,%d,%d,%d,%d,%d,%d]}\n",
               idx, cand->id, x[0], x[1], x[2],
               offsets[0], offsets[1], offsets[2],
               sched_offset60, req_offset60, defect, hw32(defect), delta_to_req,
               parts[0], parts[1], parts[2], parts[3],
               sums[0], sums[1], sums[2],
               carries[0], carries[1], carries[2],
               hw32(carries[0]), hw32(carries[1]), hw32(carries[2]),
               hw32(s1[0] ^ s2[0]), hw32(s1[1] ^ s2[1]),
               hw32(s1[2] ^ s2[2]), hw32(s1[3] ^ s2[3]),
               hw32(s1[4] ^ s2[4]), hw32(s1[5] ^ s2[5]),
               hw32(s1[6] ^ s2[6]), hw32(s1[7] ^ s2[7]));
        return 0;
    }

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
