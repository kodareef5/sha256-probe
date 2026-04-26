/*
 * defect_fiber_counter.c
 *
 * Reduced-N exact fiber counter for the sr=61 cascade-defect map.
 *
 * For fixed W57, count all (W58,W59) pairs satisfying:
 *
 *   D(W57,W58,W59) =
 *       (W2_sched60 - W1_sched60) - cascade_required_offset60 == 0 mod 2^N
 *
 * This tests whether the defect map has fat global fibers even when local
 * derivative rank is full.
 *
 * Compile from repo root:
 *   gcc -O3 -march=native -fopenmp -I. \
 *     headline_hunt/bets/singular_chamber_rank/tools/defect_fiber_counter.c \
 *     lib/sha256.c -lm -o /tmp/defect_fiber_counter
 *
 * Usage:
 *   /tmp/defect_fiber_counter N BIT FILL_HEX W57_LIMIT
 *   /tmp/defect_fiber_counter single N BIT FILL_HEX W57
 *   /tmp/defect_fiber_counter hits N BIT FILL_HEX W57 W58
 *   /tmp/defect_fiber_counter suffix N BIT FILL_HEX W57 SUFFIX_BITS
 *   /tmp/defect_fiber_counter suffixscan N BIT FILL_HEX SUFFIX_BITS W57_LIMIT
 *   /tmp/defect_fiber_counter carrybias N BIT FILL_HEX W57 W58
 *   /tmp/defect_fiber_counter defecthist N BIT FILL_HEX W57
 *   /tmp/defect_fiber_counter reqhist N BIT FILL_HEX W57 W58
 *   /tmp/defect_fiber_counter schedscan N BIT FILL_HEX W57
 *   /tmp/defect_fiber_counter sigmadiff N DELTA_HEX
 *   /tmp/defect_fiber_counter sigmaparts N DELTA_HEX
 *   /tmp/defect_fiber_counter sigmasample N DELTA_HEX SAMPLES TABLE_BITS
 *   /tmp/defect_fiber_counter off58scan N BIT FILL_HEX W57_LIMIT
 *   /tmp/defect_fiber_counter off58find N BIT FILL_HEX OFF58_HEX
 *
 * Examples:
 *   /tmp/defect_fiber_counter 8  7 0xfff 0
 *   /tmp/defect_fiber_counter 10 9 0x3ff 64
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "lib/sha256.h"

typedef struct {
    uint32_t key;
    uint32_t count;
    uint8_t used;
} sample_bucket_t;

typedef struct {
    uint64_t total_pairs;
    uint64_t total_hits;
    long double sum_hits_sq;
    uint64_t nonempty_w57;
    uint64_t max_hits;
    uint32_t max_w57;
    uint64_t low8_hist[256];
    uint64_t hw_hist[33];
} fiber_summary_t;

static inline uint32_t maskn(void) {
    return sha256_MASK;
}

static inline uint32_t splitmix32_local(uint64_t *state) {
    uint64_t z = (*state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    z ^= z >> 31;
    return (uint32_t)z;
}

static inline int hw(uint32_t x) {
    return __builtin_popcount(x & maskn());
}

static inline uint32_t addn(uint32_t a, uint32_t b) {
    return (a + b) & maskn();
}

static inline uint32_t subn(uint32_t a, uint32_t b) {
    return (a - b) & maskn();
}

static inline uint32_t cascade1_offset(const uint32_t s1[8], const uint32_t s2[8]) {
    uint32_t dh = subn(s1[7], s2[7]);
    uint32_t dSig1 = subn(sha256_Sigma1(s1[4]), sha256_Sigma1(s2[4]));
    uint32_t dCh = subn(sha256_Ch(s1[4], s1[5], s1[6]), sha256_Ch(s2[4], s2[5], s2[6]));
    uint32_t dT2 = subn(addn(sha256_Sigma0(s1[0]), sha256_Maj(s1[0], s1[1], s1[2])),
                        addn(sha256_Sigma0(s2[0]), sha256_Maj(s2[0], s2[1], s2[2])));
    return (dh + dSig1 + dCh + dT2) & maskn();
}

static inline uint32_t carry_mask_add(uint32_t a, uint32_t b) {
    uint32_t carry = 0;
    uint32_t mask = 0;
    for (int i = 0; i < sha256_N; i++) {
        uint32_t ai = (a >> i) & 1U;
        uint32_t bi = (b >> i) & 1U;
        uint32_t co = (ai & bi) | (ai & carry) | (bi & carry);
        if (co) mask |= 1U << i;
        carry = co;
    }
    return mask & maskn();
}

static inline void cascade1_offset_carry_masks(const uint32_t s1[8], const uint32_t s2[8],
                                               uint32_t cm[3]) {
    uint32_t dh = subn(s1[7], s2[7]);
    uint32_t dSig1 = subn(sha256_Sigma1(s1[4]), sha256_Sigma1(s2[4]));
    uint32_t dCh = subn(sha256_Ch(s1[4], s1[5], s1[6]), sha256_Ch(s2[4], s2[5], s2[6]));
    uint32_t dT2 = subn(addn(sha256_Sigma0(s1[0]), sha256_Maj(s1[0], s1[1], s1[2])),
                        addn(sha256_Sigma0(s2[0]), sha256_Maj(s2[0], s2[1], s2[2])));
    uint32_t s01 = addn(dh, dSig1);
    uint32_t s012 = addn(s01, dCh);
    cm[0] = carry_mask_add(dh, dSig1);
    cm[1] = carry_mask_add(s01, dCh);
    cm[2] = carry_mask_add(s012, dT2);
}

static inline void apply_round(uint32_t s[8], uint32_t w, int r) {
    uint32_t a = s[0], b = s[1], c = s[2], d = s[3];
    uint32_t e = s[4], f = s[5], g = s[6], h = s[7];
    uint32_t T1 = (h + sha256_Sigma1(e) + sha256_Ch(e, f, g) + sha256_K[r] + w) & maskn();
    uint32_t T2 = (sha256_Sigma0(a) + sha256_Maj(a, b, c)) & maskn();
    s[7] = g;
    s[6] = f;
    s[5] = e;
    s[4] = (d + T1) & maskn();
    s[3] = c;
    s[2] = b;
    s[1] = a;
    s[0] = (T1 + T2) & maskn();
}

static int prepare_candidate(int N, int bit, uint32_t fill, uint32_t *m0_out,
                             sha256_precomp_t *p1, sha256_precomp_t *p2) {
    uint32_t limit = (N >= 32) ? 0xffffffffU : (1U << N);
    uint32_t diff = 1U << bit;
    uint32_t M1[16], M2[16];

    for (uint32_t m0 = 0; m0 < limit; m0++) {
        for (int i = 0; i < 16; i++) {
            M1[i] = fill & maskn();
            M2[i] = fill & maskn();
        }
        M1[0] = m0;
        M2[0] = (m0 ^ diff) & maskn();
        M2[9] = (fill ^ diff) & maskn();
        sha256_precompute(M1, p1);
        sha256_precompute(M2, p2);
        if (p1->state[0] == p2->state[0]) {
            *m0_out = m0;
            return 1;
        }
    }
    return 0;
}

static uint64_t count_fiber_for_w57(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                                    uint32_t w57, uint64_t low8_hist[256],
                                    uint64_t hw_hist[33]) {
    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1->state, sizeof(s1_57));
    memcpy(s2_57, p2->state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57, 57);
    apply_round(s2_57, (w57 + off57) & maskn(), 57);

    uint32_t limit = (sha256_N >= 32) ? 0xffffffffU : (1U << sha256_N);
    uint64_t hits = 0;

    for (uint32_t w58 = 0; w58 < limit; w58++) {
        uint32_t s1_58[8], s2_58[8];
        memcpy(s1_58, s1_57, sizeof(s1_58));
        memcpy(s2_58, s2_57, sizeof(s2_58));

        uint32_t off58 = cascade1_offset(s1_58, s2_58);
        uint32_t w2_58 = (w58 + off58) & maskn();
        apply_round(s1_58, w58, 58);
        apply_round(s2_58, w2_58, 58);

        uint32_t w1_sched60 = (sha256_sigma1(w58) + p1->W[53] +
                               sha256_sigma0(p1->W[45]) + p1->W[44]) & maskn();
        uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2->W[53] +
                               sha256_sigma0(p2->W[45]) + p2->W[44]) & maskn();
        uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);

        for (uint32_t w59 = 0; w59 < limit; w59++) {
            uint32_t s1_59[8], s2_59[8];
            memcpy(s1_59, s1_58, sizeof(s1_59));
            memcpy(s2_59, s2_58, sizeof(s2_59));

            uint32_t off59 = cascade1_offset(s1_59, s2_59);
            apply_round(s1_59, w59, 59);
            apply_round(s2_59, (w59 + off59) & maskn(), 59);

            uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
            uint32_t defect = subn(sched_offset60, req_offset60);
            low8_hist[defect & 0xffU]++;
            hw_hist[hw(defect)]++;
            if (defect == 0) hits++;
        }
    }

    return hits;
}

static void merge_summary(fiber_summary_t *dst, const fiber_summary_t *src) {
    dst->total_pairs += src->total_pairs;
    dst->total_hits += src->total_hits;
    dst->sum_hits_sq += src->sum_hits_sq;
    dst->nonempty_w57 += src->nonempty_w57;
    if (src->max_hits > dst->max_hits) {
        dst->max_hits = src->max_hits;
        dst->max_w57 = src->max_w57;
    }
    for (int i = 0; i < 256; i++) dst->low8_hist[i] += src->low8_hist[i];
    for (int i = 0; i <= 32; i++) dst->hw_hist[i] += src->hw_hist[i];
}

static void count_nested_single_w57(int N, int bit, uint32_t fill, uint32_t w57) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    w57 &= maskn();

    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1.state, sizeof(s1_57));
    memcpy(s2_57, p2.state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57, 57);
    apply_round(s2_57, (w57 + off57) & maskn(), 57);

    uint64_t total_hits = 0;
    long double sum_sq = 0.0L;
    uint64_t max_hits = 0;
    uint32_t max_w58 = 0;
    uint64_t nonempty_w58 = 0;
    uint64_t top_hits[16];
    uint32_t top_w58[16];
    memset(top_hits, 0, sizeof(top_hits));
    memset(top_w58, 0, sizeof(top_w58));

    #pragma omp parallel
    {
        uint64_t local_total = 0;
        long double local_sq = 0.0L;
        uint64_t local_max = 0;
        uint32_t local_max_w58 = 0;
        uint64_t local_nonempty = 0;
        uint64_t local_top_hits[16];
        uint32_t local_top_w58[16];
        memset(local_top_hits, 0, sizeof(local_top_hits));
        memset(local_top_w58, 0, sizeof(local_top_w58));

        #pragma omp for schedule(dynamic, 1)
        for (uint32_t w58 = 0; w58 < limit; w58++) {
            uint32_t s1_58[8], s2_58[8];
            memcpy(s1_58, s1_57, sizeof(s1_58));
            memcpy(s2_58, s2_57, sizeof(s2_58));

            uint32_t off58 = cascade1_offset(s1_58, s2_58);
            uint32_t w2_58 = (w58 + off58) & maskn();
            apply_round(s1_58, w58, 58);
            apply_round(s2_58, w2_58, 58);

            uint32_t w1_sched60 = (sha256_sigma1(w58) + p1.W[53] +
                                   sha256_sigma0(p1.W[45]) + p1.W[44]) & maskn();
            uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2.W[53] +
                                   sha256_sigma0(p2.W[45]) + p2.W[44]) & maskn();
            uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);

            uint64_t hits = 0;
            for (uint32_t w59 = 0; w59 < limit; w59++) {
                uint32_t s1_59[8], s2_59[8];
                memcpy(s1_59, s1_58, sizeof(s1_59));
                memcpy(s2_59, s2_58, sizeof(s2_59));

                uint32_t off59 = cascade1_offset(s1_59, s2_59);
                apply_round(s1_59, w59, 59);
                apply_round(s2_59, (w59 + off59) & maskn(), 59);

                uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
                uint32_t defect = subn(sched_offset60, req_offset60);
                if (defect == 0) hits++;
            }

            local_total += hits;
            local_sq += (long double)hits * (long double)hits;
            if (hits) local_nonempty++;
            if (hits > local_max) {
                local_max = hits;
                local_max_w58 = w58;
            }
            for (int k = 0; k < 16; k++) {
                if (hits > local_top_hits[k]) {
                    for (int j = 15; j > k; j--) {
                        local_top_hits[j] = local_top_hits[j - 1];
                        local_top_w58[j] = local_top_w58[j - 1];
                    }
                    local_top_hits[k] = hits;
                    local_top_w58[k] = w58;
                    break;
                }
            }
        }

        #pragma omp critical
        {
            total_hits += local_total;
            sum_sq += local_sq;
            nonempty_w58 += local_nonempty;
            if (local_max > max_hits) {
                max_hits = local_max;
                max_w58 = local_max_w58;
            }
            for (int t = 0; t < 16; t++) {
                uint64_t h = local_top_hits[t];
                uint32_t w = local_top_w58[t];
                for (int k = 0; k < 16; k++) {
                    if (h > top_hits[k]) {
                        for (int j = 15; j > k; j--) {
                            top_hits[j] = top_hits[j - 1];
                            top_w58[j] = top_w58[j - 1];
                        }
                        top_hits[k] = h;
                        top_w58[k] = w;
                        break;
                    }
                }
            }
        }
    }

    long double mean = (long double)total_hits / (long double)limit;
    long double variance = sum_sq / (long double)limit - mean * mean;
    if (variance < 0.0L) variance = 0.0L;
    long double fano = mean > 0.0L ? variance / mean : 0.0L;

    printf("{\"mode\":\"single\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57\":\"0x%x\",\"total_hits\":%llu,\"expected_total\":%u,"
           "\"enrichment\":%.6Lf,\"nonempty_w58\":%llu,\"avg_hits_per_w58\":%.6Lf,"
           "\"variance\":%.6Lf,\"fano\":%.6Lf,\"max_hits_w58\":%llu,"
           "\"max_w58\":\"0x%x\",\"max_w58_enrichment\":%.6Lf,\"top_w58\":[",
           N, bit, fill, m0, w57,
           (unsigned long long)total_hits, limit,
           (long double)total_hits / (long double)limit,
           (unsigned long long)nonempty_w58, mean, variance, fano,
           (unsigned long long)max_hits, max_w58,
           mean > 0.0L ? (long double)max_hits / mean : 0.0L);
    for (int i = 0; i < 16; i++) {
        if (i) printf(",");
        printf("{\"w58\":\"0x%x\",\"hits\":%llu}", top_w58[i], (unsigned long long)top_hits[i]);
    }
    printf("]}\n");
}

static void list_hits_for_w57_w58(int N, int bit, uint32_t fill, uint32_t w57, uint32_t w58) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    w57 &= maskn();
    w58 &= maskn();

    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1.state, sizeof(s1_57));
    memcpy(s2_57, p2.state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57, 57);
    apply_round(s2_57, (w57 + off57) & maskn(), 57);

    uint32_t s1_58[8], s2_58[8];
    memcpy(s1_58, s1_57, sizeof(s1_58));
    memcpy(s2_58, s2_57, sizeof(s2_58));
    uint32_t off58 = cascade1_offset(s1_58, s2_58);
    uint32_t w2_58 = (w58 + off58) & maskn();
    apply_round(s1_58, w58, 58);
    apply_round(s2_58, w2_58, 58);
    uint32_t off59 = cascade1_offset(s1_58, s2_58);

    uint32_t w1_sched60 = (sha256_sigma1(w58) + p1.W[53] +
                           sha256_sigma0(p1.W[45]) + p1.W[44]) & maskn();
    uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2.W[53] +
                           sha256_sigma0(p2.W[45]) + p2.W[44]) & maskn();
    uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);

    printf("{\"mode\":\"hits\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57\":\"0x%x\",\"w58\":\"0x%x\",\"hits\":[",
           N, bit, fill, m0, w57, w58);
    int first = 1;
    uint64_t hits = 0;
    uint64_t all_ch_inv = 0, all_maj_a_inv = 0, all_maj_b_inv = 0, all_maj_c_inv = 0;
    uint64_t hit_ch_inv = 0, hit_maj_a_inv = 0, hit_maj_b_inv = 0, hit_maj_c_inv = 0;
    uint32_t all_cm_or[3] = {0, 0, 0};
    uint32_t all_cm_and[3] = {maskn(), maskn(), maskn()};
    uint32_t hit_cm_or[3] = {0, 0, 0};
    uint32_t hit_cm_and[3] = {maskn(), maskn(), maskn()};
    for (uint32_t w59 = 0; w59 < limit; w59++) {
        uint32_t s1_59[8], s2_59[8];
        memcpy(s1_59, s1_58, sizeof(s1_59));
        memcpy(s2_59, s2_58, sizeof(s2_59));
        apply_round(s1_59, w59, 59);
        apply_round(s2_59, (w59 + off59) & maskn(), 59);
        int ch_inv = hw((~(s1_59[5] ^ s1_59[6]) & ~(s2_59[5] ^ s2_59[6])) & maskn());
        int maj_a_inv = hw((~(s1_59[1] ^ s1_59[2]) & ~(s2_59[1] ^ s2_59[2])) & maskn());
        int maj_b_inv = hw((~(s1_59[0] ^ s1_59[2]) & ~(s2_59[0] ^ s2_59[2])) & maskn());
        int maj_c_inv = hw((~(s1_59[0] ^ s1_59[1]) & ~(s2_59[0] ^ s2_59[1])) & maskn());
        all_ch_inv += (uint64_t)ch_inv;
        all_maj_a_inv += (uint64_t)maj_a_inv;
        all_maj_b_inv += (uint64_t)maj_b_inv;
        all_maj_c_inv += (uint64_t)maj_c_inv;
        uint32_t cm[3];
        cascade1_offset_carry_masks(s1_59, s2_59, cm);
        for (int j = 0; j < 3; j++) {
            all_cm_or[j] |= cm[j];
            all_cm_and[j] &= cm[j];
        }
        uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
        uint32_t defect = subn(sched_offset60, req_offset60);
        if (defect == 0) {
            if (!first) printf(",");
            printf("\"0x%x\"", w59);
            first = 0;
            hits++;
            hit_ch_inv += (uint64_t)ch_inv;
            hit_maj_a_inv += (uint64_t)maj_a_inv;
            hit_maj_b_inv += (uint64_t)maj_b_inv;
            hit_maj_c_inv += (uint64_t)maj_c_inv;
            for (int j = 0; j < 3; j++) {
                hit_cm_or[j] |= cm[j];
                hit_cm_and[j] &= cm[j];
            }
        }
    }
    int all_carry_inv[3];
    int hit_carry_inv[3];
    for (int j = 0; j < 3; j++) {
        all_carry_inv[j] = sha256_N - hw((all_cm_or[j] ^ all_cm_and[j]) & maskn());
        hit_carry_inv[j] = hits ? sha256_N - hw((hit_cm_or[j] ^ hit_cm_and[j]) & maskn()) : 0;
    }
    printf("],\"count\":%llu,"
           "\"avg_all_ch_inv\":%.3f,\"avg_hit_ch_inv\":%.3f,"
           "\"avg_all_maj_a_inv\":%.3f,\"avg_hit_maj_a_inv\":%.3f,"
           "\"avg_all_maj_b_inv\":%.3f,\"avg_hit_maj_b_inv\":%.3f,"
           "\"avg_all_maj_c_inv\":%.3f,\"avg_hit_maj_c_inv\":%.3f,"
           "\"all_carry_inv\":[%d,%d,%d],\"hit_carry_inv\":[%d,%d,%d],"
           "\"hit_carry_and\":[\"0x%x\",\"0x%x\",\"0x%x\"],"
           "\"hit_carry_or\":[\"0x%x\",\"0x%x\",\"0x%x\"]}\n",
           (unsigned long long)hits,
           (double)all_ch_inv / (double)limit,
           hits ? (double)hit_ch_inv / (double)hits : 0.0,
           (double)all_maj_a_inv / (double)limit,
           hits ? (double)hit_maj_a_inv / (double)hits : 0.0,
           (double)all_maj_b_inv / (double)limit,
           hits ? (double)hit_maj_b_inv / (double)hits : 0.0,
           (double)all_maj_c_inv / (double)limit,
           hits ? (double)hit_maj_c_inv / (double)hits : 0.0,
           all_carry_inv[0], all_carry_inv[1], all_carry_inv[2],
           hit_carry_inv[0], hit_carry_inv[1], hit_carry_inv[2],
           hit_cm_and[0], hit_cm_and[1], hit_cm_and[2],
           hit_cm_or[0], hit_cm_or[1], hit_cm_or[2]);
}

static uint64_t count_hits_for_w57_w58(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                                       uint32_t w57, uint32_t w58) {
    uint32_t limit = 1U << sha256_N;
    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1->state, sizeof(s1_57));
    memcpy(s2_57, p2->state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57 & maskn(), 57);
    apply_round(s2_57, ((w57 & maskn()) + off57) & maskn(), 57);

    uint32_t s1_58[8], s2_58[8];
    memcpy(s1_58, s1_57, sizeof(s1_58));
    memcpy(s2_58, s2_57, sizeof(s2_58));
    uint32_t off58 = cascade1_offset(s1_58, s2_58);
    uint32_t w2_58 = ((w58 & maskn()) + off58) & maskn();
    apply_round(s1_58, w58 & maskn(), 58);
    apply_round(s2_58, w2_58, 58);

    uint32_t w1_sched60 = (sha256_sigma1(w58 & maskn()) + p1->W[53] +
                           sha256_sigma0(p1->W[45]) + p1->W[44]) & maskn();
    uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2->W[53] +
                           sha256_sigma0(p2->W[45]) + p2->W[44]) & maskn();
    uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);

    uint64_t hits = 0;
    for (uint32_t w59 = 0; w59 < limit; w59++) {
        uint32_t s1_59[8], s2_59[8];
        memcpy(s1_59, s1_58, sizeof(s1_59));
        memcpy(s2_59, s2_58, sizeof(s2_59));
        uint32_t off59 = cascade1_offset(s1_59, s2_59);
        apply_round(s1_59, w59, 59);
        apply_round(s2_59, (w59 + off59) & maskn(), 59);
        uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
        if (subn(sched_offset60, req_offset60) == 0) hits++;
    }
    return hits;
}

static void suffix_profile_single_w57(int N, int bit, uint32_t fill, uint32_t w57, int suffix_bits) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }
    if (suffix_bits < 1) suffix_bits = 1;
    if (suffix_bits > N) suffix_bits = N;
    int groups = 1 << suffix_bits;
    uint64_t *group_hits = calloc((size_t)groups, sizeof(uint64_t));
    uint64_t *group_count = calloc((size_t)groups, sizeof(uint64_t));
    if (!group_hits || !group_count) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    uint32_t limit = 1U << N;
    uint32_t suffix_mask = (1U << suffix_bits) - 1U;

    #pragma omp parallel
    {
        uint64_t *local_hits = calloc((size_t)groups, sizeof(uint64_t));
        uint64_t *local_count = calloc((size_t)groups, sizeof(uint64_t));
        if (!local_hits || !local_count) {
            fprintf(stderr, "thread allocation failed\n");
            exit(2);
        }
        #pragma omp for schedule(dynamic, 1)
        for (uint32_t w58 = 0; w58 < limit; w58++) {
            uint64_t hits = count_hits_for_w57_w58(&p1, &p2, w57 & maskn(), w58);
            uint32_t suffix = w58 & suffix_mask;
            local_hits[suffix] += hits;
            local_count[suffix]++;
        }
        #pragma omp critical
        {
            for (int i = 0; i < groups; i++) {
                group_hits[i] += local_hits[i];
                group_count[i] += local_count[i];
            }
        }
        free(local_hits);
        free(local_count);
    }

    uint64_t total_hits = 0;
    for (int i = 0; i < groups; i++) total_hits += group_hits[i];
    long double global_mean = (long double)total_hits / (long double)limit;

    int top_suffix[16];
    long double top_avg[16];
    uint64_t top_hits[16];
    for (int i = 0; i < 16; i++) {
        top_suffix[i] = 0;
        top_avg[i] = -1.0L;
        top_hits[i] = 0;
    }
    for (int s = 0; s < groups; s++) {
        long double avg = group_count[s] ? (long double)group_hits[s] / (long double)group_count[s] : 0.0L;
        for (int k = 0; k < 16; k++) {
            if (avg > top_avg[k]) {
                for (int j = 15; j > k; j--) {
                    top_avg[j] = top_avg[j - 1];
                    top_suffix[j] = top_suffix[j - 1];
                    top_hits[j] = top_hits[j - 1];
                }
                top_avg[k] = avg;
                top_suffix[k] = s;
                top_hits[k] = group_hits[s];
                break;
            }
        }
    }

    printf("{\"mode\":\"suffix\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57\":\"0x%x\",\"suffix_bits\":%d,\"global_mean\":%.6Lf,\"top\":[",
           N, bit, fill, m0, w57 & maskn(), suffix_bits, global_mean);
    for (int i = 0; i < 16 && i < groups; i++) {
        if (i) printf(",");
        printf("{\"suffix\":\"0x%x\",\"avg_hits\":%.6Lf,\"enrichment\":%.6Lf,\"total_hits\":%llu}",
               top_suffix[i], top_avg[i],
               global_mean > 0.0L ? top_avg[i] / global_mean : 0.0L,
               (unsigned long long)top_hits[i]);
    }
    printf("]}\n");

    free(group_hits);
    free(group_count);
}

static void suffix_scan_w57_range(int N, int bit, uint32_t fill, int suffix_bits, int w57_limit_arg) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }
    if (suffix_bits < 1) suffix_bits = 1;
    if (suffix_bits > N) suffix_bits = N;

    uint32_t limit = 1U << N;
    int w57_limit = (w57_limit_arg <= 0 || w57_limit_arg > (int)limit) ? (int)limit : w57_limit_arg;
    int groups = 1 << suffix_bits;
    uint32_t suffix_mask = (1U << suffix_bits) - 1U;
    uint64_t *group_hits = calloc((size_t)groups, sizeof(uint64_t));
    if (!group_hits) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    uint64_t total_hits = 0;

    #pragma omp parallel
    {
        uint64_t *local_hits = calloc((size_t)groups, sizeof(uint64_t));
        if (!local_hits) {
            fprintf(stderr, "thread allocation failed\n");
            exit(2);
        }
        uint64_t local_total = 0;

        #pragma omp for schedule(dynamic, 1)
        for (int w57_i = 0; w57_i < w57_limit; w57_i++) {
            uint32_t s1_57[8], s2_57[8];
            memcpy(s1_57, p1.state, sizeof(s1_57));
            memcpy(s2_57, p2.state, sizeof(s2_57));
            uint32_t off57 = cascade1_offset(s1_57, s2_57);
            apply_round(s1_57, (uint32_t)w57_i, 57);
            apply_round(s2_57, ((uint32_t)w57_i + off57) & maskn(), 57);

            for (uint32_t w58 = 0; w58 < limit; w58++) {
                uint32_t s1_58[8], s2_58[8];
                memcpy(s1_58, s1_57, sizeof(s1_58));
                memcpy(s2_58, s2_57, sizeof(s2_58));

                uint32_t off58 = cascade1_offset(s1_58, s2_58);
                uint32_t w2_58 = (w58 + off58) & maskn();
                apply_round(s1_58, w58, 58);
                apply_round(s2_58, w2_58, 58);

                uint32_t w1_sched60 = (sha256_sigma1(w58) + p1.W[53] +
                                       sha256_sigma0(p1.W[45]) + p1.W[44]) & maskn();
                uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2.W[53] +
                                       sha256_sigma0(p2.W[45]) + p2.W[44]) & maskn();
                uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);
                uint32_t suffix = w58 & suffix_mask;

                for (uint32_t w59 = 0; w59 < limit; w59++) {
                    uint32_t s1_59[8], s2_59[8];
                    memcpy(s1_59, s1_58, sizeof(s1_59));
                    memcpy(s2_59, s2_58, sizeof(s2_59));

                    uint32_t off59 = cascade1_offset(s1_59, s2_59);
                    apply_round(s1_59, w59, 59);
                    apply_round(s2_59, (w59 + off59) & maskn(), 59);

                    uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
                    uint32_t defect = subn(sched_offset60, req_offset60);
                    if (defect == 0) {
                        local_hits[suffix]++;
                        local_total++;
                    }
                }
            }
        }

        #pragma omp critical
        {
            total_hits += local_total;
            for (int i = 0; i < groups; i++) group_hits[i] += local_hits[i];
        }
        free(local_hits);
    }

    uint64_t group_count = (uint64_t)w57_limit * (uint64_t)(limit >> suffix_bits);
    long double global_mean = (long double)total_hits / ((long double)w57_limit * (long double)limit);
    long double sum_avg = 0.0L;
    long double sum_avg_sq = 0.0L;
    for (int s = 0; s < groups; s++) {
        long double avg = group_count ? (long double)group_hits[s] / (long double)group_count : 0.0L;
        sum_avg += avg;
        sum_avg_sq += avg * avg;
    }
    long double suffix_variance = sum_avg_sq / (long double)groups -
                                  (sum_avg / (long double)groups) * (sum_avg / (long double)groups);
    if (suffix_variance < 0.0L) suffix_variance = 0.0L;

    int top_suffix[16];
    long double top_avg[16];
    uint64_t top_hits[16];
    for (int i = 0; i < 16; i++) {
        top_suffix[i] = 0;
        top_avg[i] = -1.0L;
        top_hits[i] = 0;
    }
    for (int s = 0; s < groups; s++) {
        long double avg = group_count ? (long double)group_hits[s] / (long double)group_count : 0.0L;
        for (int k = 0; k < 16; k++) {
            if (avg > top_avg[k]) {
                for (int j = 15; j > k; j--) {
                    top_avg[j] = top_avg[j - 1];
                    top_suffix[j] = top_suffix[j - 1];
                    top_hits[j] = top_hits[j - 1];
                }
                top_avg[k] = avg;
                top_suffix[k] = s;
                top_hits[k] = group_hits[s];
                break;
            }
        }
    }

    printf("{\"mode\":\"suffixscan\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"suffix_bits\":%d,\"w57_checked\":%d,\"total_hits\":%llu,"
           "\"global_mean\":%.6Lf,\"suffix_variance\":%.6Lf,\"top\":[",
           N, bit, fill, m0, suffix_bits, w57_limit,
           (unsigned long long)total_hits, global_mean, suffix_variance);
    for (int i = 0; i < 16 && i < groups; i++) {
        if (i) printf(",");
        printf("{\"suffix\":\"0x%x\",\"avg_hits\":%.6Lf,\"enrichment\":%.6Lf,\"total_hits\":%llu}",
               top_suffix[i], top_avg[i],
               global_mean > 0.0L ? top_avg[i] / global_mean : 0.0L,
               (unsigned long long)top_hits[i]);
    }
    printf("]}\n");

    free(group_hits);
}

static void carry_bias_for_w57_w58(int N, int bit, uint32_t fill, uint32_t w57, uint32_t w58) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    w57 &= maskn();
    w58 &= maskn();

    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1.state, sizeof(s1_57));
    memcpy(s2_57, p2.state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57, 57);
    apply_round(s2_57, (w57 + off57) & maskn(), 57);

    uint32_t s1_58[8], s2_58[8];
    memcpy(s1_58, s1_57, sizeof(s1_58));
    memcpy(s2_58, s2_57, sizeof(s2_58));
    uint32_t off58 = cascade1_offset(s1_58, s2_58);
    uint32_t w2_58 = (w58 + off58) & maskn();
    apply_round(s1_58, w58, 58);
    apply_round(s2_58, w2_58, 58);

    uint32_t w1_sched60 = (sha256_sigma1(w58) + p1.W[53] +
                           sha256_sigma0(p1.W[45]) + p1.W[44]) & maskn();
    uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2.W[53] +
                           sha256_sigma0(p2.W[45]) + p2.W[44]) & maskn();
    uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);

    uint64_t all_one[3][32];
    uint64_t hit_one[3][32];
    memset(all_one, 0, sizeof(all_one));
    memset(hit_one, 0, sizeof(hit_one));
    uint32_t hit_cm_or[3] = {0, 0, 0};
    uint32_t hit_cm_and[3] = {maskn(), maskn(), maskn()};
    uint64_t hits = 0;

    for (uint32_t w59 = 0; w59 < limit; w59++) {
        uint32_t s1_59[8], s2_59[8];
        memcpy(s1_59, s1_58, sizeof(s1_59));
        memcpy(s2_59, s2_58, sizeof(s2_59));
        uint32_t off59 = cascade1_offset(s1_59, s2_59);
        apply_round(s1_59, w59, 59);
        apply_round(s2_59, (w59 + off59) & maskn(), 59);

        uint32_t cm[3];
        cascade1_offset_carry_masks(s1_59, s2_59, cm);
        for (int j = 0; j < 3; j++) {
            for (int b = 0; b < N; b++) {
                if ((cm[j] >> b) & 1U) all_one[j][b]++;
            }
        }

        uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
        uint32_t defect = subn(sched_offset60, req_offset60);
        if (defect == 0) {
            hits++;
            for (int j = 0; j < 3; j++) {
                hit_cm_or[j] |= cm[j];
                hit_cm_and[j] &= cm[j];
            }
            for (int j = 0; j < 3; j++) {
                for (int b = 0; b < N; b++) {
                    if ((cm[j] >> b) & 1U) hit_one[j][b]++;
                }
            }
        }
    }

    uint64_t carry_filter_support = 0;
    uint64_t carry_filter_hits = 0;
    if (hits) {
        uint32_t fixed_mask[3];
        for (int j = 0; j < 3; j++) fixed_mask[j] = ~(hit_cm_or[j] ^ hit_cm_and[j]) & maskn();

        for (uint32_t w59 = 0; w59 < limit; w59++) {
            uint32_t s1_59[8], s2_59[8];
            memcpy(s1_59, s1_58, sizeof(s1_59));
            memcpy(s2_59, s2_58, sizeof(s2_59));
            uint32_t off59 = cascade1_offset(s1_59, s2_59);
            apply_round(s1_59, w59, 59);
            apply_round(s2_59, (w59 + off59) & maskn(), 59);

            uint32_t cm[3];
            cascade1_offset_carry_masks(s1_59, s2_59, cm);
            int pass = 1;
            for (int j = 0; j < 3; j++) {
                if (((cm[j] ^ hit_cm_and[j]) & fixed_mask[j]) != 0) {
                    pass = 0;
                    break;
                }
            }
            if (!pass) continue;

            carry_filter_support++;
            uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
            uint32_t defect = subn(sched_offset60, req_offset60);
            if (defect == 0) carry_filter_hits++;
        }
    }

    int top_j[24];
    int top_b[24];
    long double top_score[24];
    for (int i = 0; i < 24; i++) {
        top_j[i] = 0;
        top_b[i] = 0;
        top_score[i] = -1.0L;
    }
    if (hits) {
        for (int j = 0; j < 3; j++) {
            for (int b = 0; b < N; b++) {
                long double all_rate = (long double)all_one[j][b] / (long double)limit;
                long double hit_rate = (long double)hit_one[j][b] / (long double)hits;
                long double score = hit_rate > all_rate ? hit_rate - all_rate : all_rate - hit_rate;
                for (int k = 0; k < 24; k++) {
                    if (score > top_score[k]) {
                        for (int t = 23; t > k; t--) {
                            top_score[t] = top_score[t - 1];
                            top_j[t] = top_j[t - 1];
                            top_b[t] = top_b[t - 1];
                        }
                        top_score[k] = score;
                        top_j[k] = j;
                        top_b[k] = b;
                        break;
                    }
                }
            }
        }
    }

    printf("{\"mode\":\"carrybias\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57\":\"0x%x\",\"w58\":\"0x%x\",\"hits\":%llu,"
           "\"hit_carry_and\":[\"0x%x\",\"0x%x\",\"0x%x\"],"
           "\"hit_carry_or\":[\"0x%x\",\"0x%x\",\"0x%x\"],"
           "\"carry_filter_support\":%llu,\"carry_filter_hits\":%llu,"
           "\"carry_filter_precision\":%.6Lf,\"carry_filter_reduction\":%.6Lf,\"top\":[",
           N, bit, fill, m0, w57, w58, (unsigned long long)hits,
           hit_cm_and[0], hit_cm_and[1], hit_cm_and[2],
           hit_cm_or[0], hit_cm_or[1], hit_cm_or[2],
           (unsigned long long)carry_filter_support,
           (unsigned long long)carry_filter_hits,
           carry_filter_support ? (long double)carry_filter_hits / (long double)carry_filter_support : 0.0L,
           carry_filter_support ? (long double)limit / (long double)carry_filter_support : 0.0L);
    for (int i = 0; i < 24 && i < 3 * N && hits; i++) {
        int j = top_j[i];
        int b = top_b[i];
        if (i) printf(",");
        long double all_rate = (long double)all_one[j][b] / (long double)limit;
        long double hit_rate = (long double)hit_one[j][b] / (long double)hits;
        printf("{\"adder\":%d,\"bit\":%d,\"all_rate\":%.6Lf,\"hit_rate\":%.6Lf,"
               "\"delta\":%.6Lf,\"hit_ones\":%llu}",
               j, b, all_rate, hit_rate, hit_rate - all_rate,
               (unsigned long long)hit_one[j][b]);
    }
    printf("]}\n");
}

static void defect_histogram_for_w57(int N, int bit, uint32_t fill, uint32_t w57) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    size_t hist_len = (size_t)limit;
    uint64_t *hist = calloc(hist_len, sizeof(uint64_t));
    if (!hist) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    w57 &= maskn();

    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1.state, sizeof(s1_57));
    memcpy(s2_57, p2.state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57, 57);
    apply_round(s2_57, (w57 + off57) & maskn(), 57);

    #pragma omp parallel
    {
        uint64_t *local_hist = calloc(hist_len, sizeof(uint64_t));
        if (!local_hist) {
            fprintf(stderr, "thread allocation failed\n");
            exit(2);
        }

        #pragma omp for schedule(dynamic, 1)
        for (uint32_t w58 = 0; w58 < limit; w58++) {
            uint32_t s1_58[8], s2_58[8];
            memcpy(s1_58, s1_57, sizeof(s1_58));
            memcpy(s2_58, s2_57, sizeof(s2_58));

            uint32_t off58 = cascade1_offset(s1_58, s2_58);
            uint32_t w2_58 = (w58 + off58) & maskn();
            apply_round(s1_58, w58, 58);
            apply_round(s2_58, w2_58, 58);

            uint32_t w1_sched60 = (sha256_sigma1(w58) + p1.W[53] +
                                   sha256_sigma0(p1.W[45]) + p1.W[44]) & maskn();
            uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2.W[53] +
                                   sha256_sigma0(p2.W[45]) + p2.W[44]) & maskn();
            uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);

            for (uint32_t w59 = 0; w59 < limit; w59++) {
                uint32_t s1_59[8], s2_59[8];
                memcpy(s1_59, s1_58, sizeof(s1_59));
                memcpy(s2_59, s2_58, sizeof(s2_59));

                uint32_t off59 = cascade1_offset(s1_59, s2_59);
                apply_round(s1_59, w59, 59);
                apply_round(s2_59, (w59 + off59) & maskn(), 59);

                uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
                uint32_t defect = subn(sched_offset60, req_offset60);
                local_hist[defect]++;
            }
        }

        #pragma omp critical
        {
            for (uint32_t i = 0; i < limit; i++) hist[i] += local_hist[i];
        }
        free(local_hist);
    }

    uint64_t total = (uint64_t)limit * (uint64_t)limit;
    long double mean = (long double)total / (long double)limit;
    long double sum_sq = 0.0L;
    uint64_t max_count = 0;
    uint32_t max_defect = 0;
    uint64_t min_count = UINT64_MAX;
    uint32_t min_defect = 0;
    uint64_t zero_count = hist[0];
    int zero_rank = 1;

    int top_defect[16];
    uint64_t top_count[16];
    for (int i = 0; i < 16; i++) {
        top_defect[i] = 0;
        top_count[i] = 0;
    }

    for (uint32_t d = 0; d < limit; d++) {
        uint64_t c = hist[d];
        sum_sq += (long double)c * (long double)c;
        if (c > max_count) {
            max_count = c;
            max_defect = d;
        }
        if (c < min_count) {
            min_count = c;
            min_defect = d;
        }
        if (c > zero_count) zero_rank++;
        for (int k = 0; k < 16; k++) {
            if (c > top_count[k]) {
                for (int j = 15; j > k; j--) {
                    top_count[j] = top_count[j - 1];
                    top_defect[j] = top_defect[j - 1];
                }
                top_count[k] = c;
                top_defect[k] = (int)d;
                break;
            }
        }
    }

    long double variance = sum_sq / (long double)limit - mean * mean;
    if (variance < 0.0L) variance = 0.0L;
    long double fano = mean > 0.0L ? variance / mean : 0.0L;

    printf("{\"mode\":\"defecthist\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57\":\"0x%x\",\"mean\":%.6Lf,\"variance\":%.6Lf,\"fano\":%.6Lf,"
           "\"zero_count\":%llu,\"zero_enrichment\":%.6Lf,\"zero_rank\":%d,"
           "\"max_defect\":\"0x%x\",\"max_count\":%llu,\"max_enrichment\":%.6Lf,"
           "\"min_defect\":\"0x%x\",\"min_count\":%llu,\"top\":[",
           N, bit, fill, m0, w57, mean, variance, fano,
           (unsigned long long)zero_count,
           mean > 0.0L ? (long double)zero_count / mean : 0.0L,
           zero_rank, max_defect, (unsigned long long)max_count,
           mean > 0.0L ? (long double)max_count / mean : 0.0L,
           min_defect, (unsigned long long)min_count);
    for (int i = 0; i < 16 && i < (int)limit; i++) {
        if (i) printf(",");
        printf("{\"defect\":\"0x%x\",\"count\":%llu,\"enrichment\":%.6Lf}",
               top_defect[i], (unsigned long long)top_count[i],
               mean > 0.0L ? (long double)top_count[i] / mean : 0.0L);
    }
    printf("]}\n");

    free(hist);
}

static void req_histogram_for_w57_w58(int N, int bit, uint32_t fill, uint32_t w57, uint32_t w58) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    uint64_t *hist = calloc((size_t)limit, sizeof(uint64_t));
    if (!hist) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    w57 &= maskn();
    w58 &= maskn();

    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1.state, sizeof(s1_57));
    memcpy(s2_57, p2.state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57, 57);
    apply_round(s2_57, (w57 + off57) & maskn(), 57);

    uint32_t s1_58[8], s2_58[8];
    memcpy(s1_58, s1_57, sizeof(s1_58));
    memcpy(s2_58, s2_57, sizeof(s2_58));
    uint32_t off58 = cascade1_offset(s1_58, s2_58);
    uint32_t w2_58 = (w58 + off58) & maskn();
    apply_round(s1_58, w58, 58);
    apply_round(s2_58, w2_58, 58);

    uint32_t w1_sched60 = (sha256_sigma1(w58) + p1.W[53] +
                           sha256_sigma0(p1.W[45]) + p1.W[44]) & maskn();
    uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2.W[53] +
                           sha256_sigma0(p2.W[45]) + p2.W[44]) & maskn();
    uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);
    uint32_t off59 = cascade1_offset(s1_58, s2_58);

    for (uint32_t w59 = 0; w59 < limit; w59++) {
        uint32_t s1_59[8], s2_59[8];
        memcpy(s1_59, s1_58, sizeof(s1_59));
        memcpy(s2_59, s2_58, sizeof(s2_59));
        apply_round(s1_59, w59, 59);
        apply_round(s2_59, (w59 + off59) & maskn(), 59);
        uint32_t req_offset60 = cascade1_offset(s1_59, s2_59);
        hist[req_offset60]++;
    }

    long double mean = 1.0L;
    long double sum_sq = 0.0L;
    uint64_t max_count = 0;
    uint32_t max_req = 0;
    uint64_t min_count = UINT64_MAX;
    uint32_t min_req = 0;
    uint64_t target_count = hist[sched_offset60];
    int target_rank = 1;

    int top_req[16];
    uint64_t top_count[16];
    for (int i = 0; i < 16; i++) {
        top_req[i] = 0;
        top_count[i] = 0;
    }

    for (uint32_t r = 0; r < limit; r++) {
        uint64_t c = hist[r];
        sum_sq += (long double)c * (long double)c;
        if (c > max_count) {
            max_count = c;
            max_req = r;
        }
        if (c < min_count) {
            min_count = c;
            min_req = r;
        }
        if (c > target_count) target_rank++;
        for (int k = 0; k < 16; k++) {
            if (c > top_count[k]) {
                for (int j = 15; j > k; j--) {
                    top_count[j] = top_count[j - 1];
                    top_req[j] = top_req[j - 1];
                }
                top_count[k] = c;
                top_req[k] = (int)r;
                break;
            }
        }
    }

    long double variance = sum_sq / (long double)limit - mean * mean;
    if (variance < 0.0L) variance = 0.0L;
    long double fano = mean > 0.0L ? variance / mean : 0.0L;

    printf("{\"mode\":\"reqhist\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57\":\"0x%x\",\"w58\":\"0x%x\",\"off58\":\"0x%x\",\"off59\":\"0x%x\","
           "\"sched_offset60\":\"0x%x\","
           "\"mean\":%.6Lf,\"variance\":%.6Lf,\"fano\":%.6Lf,"
           "\"target_count\":%llu,\"target_rank\":%d,"
           "\"max_req\":\"0x%x\",\"max_count\":%llu,"
           "\"min_req\":\"0x%x\",\"min_count\":%llu,\"top\":[",
           N, bit, fill, m0, w57, w58, off58, off59, sched_offset60,
           mean, variance, fano,
           (unsigned long long)target_count, target_rank,
           max_req, (unsigned long long)max_count,
           min_req, (unsigned long long)min_count);
    for (int i = 0; i < 16 && i < (int)limit; i++) {
        if (i) printf(",");
        printf("{\"req\":\"0x%x\",\"count\":%llu}",
               top_req[i], (unsigned long long)top_count[i]);
    }
    printf("]}\n");

    free(hist);
}

static void sched_offset_scan_for_w57(int N, int bit, uint32_t fill, uint32_t w57) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    uint64_t *hist = calloc((size_t)limit, sizeof(uint64_t));
    uint32_t *first_w58 = calloc((size_t)limit, sizeof(uint32_t));
    if (!hist || !first_w58) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }
    for (uint32_t i = 0; i < limit; i++) first_w58[i] = UINT32_MAX;

    w57 &= maskn();

    uint32_t s1_57[8], s2_57[8];
    memcpy(s1_57, p1.state, sizeof(s1_57));
    memcpy(s2_57, p2.state, sizeof(s2_57));
    uint32_t off57 = cascade1_offset(s1_57, s2_57);
    apply_round(s1_57, w57, 57);
    apply_round(s2_57, (w57 + off57) & maskn(), 57);
    uint32_t off58 = cascade1_offset(s1_57, s2_57);

    for (uint32_t w58 = 0; w58 < limit; w58++) {
        uint32_t s1_58[8], s2_58[8];
        memcpy(s1_58, s1_57, sizeof(s1_58));
        memcpy(s2_58, s2_57, sizeof(s2_58));

        uint32_t w2_58 = (w58 + off58) & maskn();
        apply_round(s1_58, w58, 58);
        apply_round(s2_58, w2_58, 58);

        uint32_t w1_sched60 = (sha256_sigma1(w58) + p1.W[53] +
                               sha256_sigma0(p1.W[45]) + p1.W[44]) & maskn();
        uint32_t w2_sched60 = (sha256_sigma1(w2_58) + p2.W[53] +
                               sha256_sigma0(p2.W[45]) + p2.W[44]) & maskn();
        uint32_t sched_offset60 = subn(w2_sched60, w1_sched60);
        if (hist[sched_offset60] == 0) first_w58[sched_offset60] = w58;
        hist[sched_offset60]++;
    }

    long double mean = 1.0L;
    long double sum_sq = 0.0L;
    uint64_t max_count = 0;
    uint32_t max_offset = 0;
    uint64_t min_nonzero = UINT64_MAX;
    uint32_t min_nonzero_offset = 0;
    uint64_t occupied = 0;

    int top_offset[16];
    uint64_t top_count[16];
    uint32_t top_first_w58[16];
    for (int i = 0; i < 16; i++) {
        top_offset[i] = 0;
        top_count[i] = 0;
        top_first_w58[i] = 0;
    }

    for (uint32_t off = 0; off < limit; off++) {
        uint64_t c = hist[off];
        sum_sq += (long double)c * (long double)c;
        if (c) {
            occupied++;
            if (c < min_nonzero) {
                min_nonzero = c;
                min_nonzero_offset = off;
            }
        }
        if (c > max_count) {
            max_count = c;
            max_offset = off;
        }
        for (int k = 0; k < 16; k++) {
            if (c > top_count[k]) {
                for (int j = 15; j > k; j--) {
                    top_count[j] = top_count[j - 1];
                    top_offset[j] = top_offset[j - 1];
                    top_first_w58[j] = top_first_w58[j - 1];
                }
                top_count[k] = c;
                top_offset[k] = (int)off;
                top_first_w58[k] = first_w58[off];
                break;
            }
        }
    }

    long double variance = sum_sq / (long double)limit - mean * mean;
    if (variance < 0.0L) variance = 0.0L;
    long double fano = mean > 0.0L ? variance / mean : 0.0L;

    printf("{\"mode\":\"schedscan\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57\":\"0x%x\",\"off57\":\"0x%x\",\"off58\":\"0x%x\","
           "\"mean\":%.6Lf,\"variance\":%.6Lf,\"fano\":%.6Lf,"
           "\"occupied_offsets\":%llu,\"max_offset\":\"0x%x\",\"max_count\":%llu,"
           "\"min_nonzero_offset\":\"0x%x\",\"min_nonzero_count\":%llu,\"top\":[",
           N, bit, fill, m0, w57, off57, off58, mean, variance, fano,
           (unsigned long long)occupied, max_offset, (unsigned long long)max_count,
           min_nonzero_offset, (unsigned long long)min_nonzero);
    for (int i = 0; i < 16 && i < (int)limit; i++) {
        if (i) printf(",");
        printf("{\"offset\":\"0x%x\",\"count\":%llu,\"first_w58\":\"0x%x\"}",
               top_offset[i], (unsigned long long)top_count[i], top_first_w58[i]);
    }
    printf("]}\n");

    free(hist);
    free(first_w58);
}

static void sigma_diff_scan(int N, uint32_t delta) {
    if (N < 4 || N > 24) {
        fprintf(stderr, "sigmadiff mode requires N=4..24.\n");
        exit(2);
    }
    sha256_init(N);
    delta &= maskn();
    uint32_t limit = 1U << N;
    uint64_t *hist = calloc((size_t)limit, sizeof(uint64_t));
    uint32_t *first_w = calloc((size_t)limit, sizeof(uint32_t));
    if (!hist || !first_w) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }
    for (uint32_t i = 0; i < limit; i++) first_w[i] = UINT32_MAX;

    for (uint32_t w = 0; w < limit; w++) {
        uint32_t y = subn(sha256_sigma1((w + delta) & maskn()), sha256_sigma1(w));
        if (hist[y] == 0) first_w[y] = w;
        hist[y]++;
    }

    long double mean = 1.0L;
    long double sum_sq = 0.0L;
    uint64_t occupied = 0;
    uint64_t max_count = 0;
    uint32_t max_value = 0;
    uint64_t min_nonzero = UINT64_MAX;
    uint32_t min_nonzero_value = 0;

    int top_value[16];
    uint64_t top_count[16];
    uint32_t top_first_w[16];
    for (int i = 0; i < 16; i++) {
        top_value[i] = 0;
        top_count[i] = 0;
        top_first_w[i] = 0;
    }

    for (uint32_t y = 0; y < limit; y++) {
        uint64_t c = hist[y];
        sum_sq += (long double)c * (long double)c;
        if (c) {
            occupied++;
            if (c < min_nonzero) {
                min_nonzero = c;
                min_nonzero_value = y;
            }
        }
        if (c > max_count) {
            max_count = c;
            max_value = y;
        }
        for (int k = 0; k < 16; k++) {
            if (c > top_count[k]) {
                for (int j = 15; j > k; j--) {
                    top_count[j] = top_count[j - 1];
                    top_value[j] = top_value[j - 1];
                    top_first_w[j] = top_first_w[j - 1];
                }
                top_count[k] = c;
                top_value[k] = (int)y;
                top_first_w[k] = first_w[y];
                break;
            }
        }
    }

    long double variance = sum_sq / (long double)limit - mean * mean;
    if (variance < 0.0L) variance = 0.0L;
    long double fano = mean > 0.0L ? variance / mean : 0.0L;

    printf("{\"mode\":\"sigmadiff\",\"N\":%d,\"delta\":\"0x%x\","
           "\"rot_rs1\":[%d,%d],\"shift_ss1\":%d,"
           "\"mean\":%.6Lf,\"variance\":%.6Lf,\"fano\":%.6Lf,"
           "\"occupied_values\":%llu,\"image_fraction\":%.9Lf,"
           "\"max_value\":\"0x%x\",\"max_count\":%llu,"
           "\"min_nonzero_value\":\"0x%x\",\"min_nonzero_count\":%llu,\"top\":[",
           N, delta, sha256_rs1[0], sha256_rs1[1], sha256_ss1,
           mean, variance, fano,
           (unsigned long long)occupied, (long double)occupied / (long double)limit,
           max_value, (unsigned long long)max_count,
           min_nonzero_value, (unsigned long long)min_nonzero);
    for (int i = 0; i < 16 && i < (int)limit; i++) {
        if (i) printf(",");
        printf("{\"value\":\"0x%x\",\"count\":%llu,\"first_w\":\"0x%x\"}",
               top_value[i], (unsigned long long)top_count[i], top_first_w[i]);
    }
    printf("]}\n");

    free(hist);
    free(first_w);
}

static void sigma_diff_parts_scan(int N, uint32_t delta) {
    if (N < 4 || N > 22) {
        fprintf(stderr, "sigmaparts mode requires N=4..22.\n");
        exit(2);
    }
    sha256_init(N);
    delta &= maskn();
    uint32_t limit = 1U << N;
    uint64_t *q_hist = calloc((size_t)limit, sizeof(uint64_t));
    uint64_t *lin_hist = calloc((size_t)limit, sizeof(uint64_t));
    uint64_t *arith_hist = calloc((size_t)limit, sizeof(uint64_t));
    if (!q_hist || !lin_hist || !arith_hist) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    for (uint32_t w = 0; w < limit; w++) {
        uint32_t wp = (w + delta) & maskn();
        uint32_t q = (wp ^ w) & maskn();
        uint32_t lin = (sha256_sigma1(wp) ^ sha256_sigma1(w)) & maskn();
        uint32_t arith = subn(sha256_sigma1(wp), sha256_sigma1(w));
        q_hist[q]++;
        lin_hist[lin]++;
        arith_hist[arith]++;
    }

    uint64_t q_occ = 0, lin_occ = 0, arith_occ = 0;
    uint64_t q_max = 0, lin_max = 0, arith_max = 0;
    uint32_t q_max_v = 0, lin_max_v = 0, arith_max_v = 0;
    long double q_sq = 0.0L, lin_sq = 0.0L, arith_sq = 0.0L;

    for (uint32_t v = 0; v < limit; v++) {
        uint64_t c = q_hist[v];
        q_sq += (long double)c * (long double)c;
        if (c) q_occ++;
        if (c > q_max) {
            q_max = c;
            q_max_v = v;
        }

        c = lin_hist[v];
        lin_sq += (long double)c * (long double)c;
        if (c) lin_occ++;
        if (c > lin_max) {
            lin_max = c;
            lin_max_v = v;
        }

        c = arith_hist[v];
        arith_sq += (long double)c * (long double)c;
        if (c) arith_occ++;
        if (c > arith_max) {
            arith_max = c;
            arith_max_v = v;
        }
    }

    long double mean = 1.0L;
    long double q_fano = q_sq / (long double)limit - mean * mean;
    long double lin_fano = lin_sq / (long double)limit - mean * mean;
    long double arith_fano = arith_sq / (long double)limit - mean * mean;
    if (q_fano < 0.0L) q_fano = 0.0L;
    if (lin_fano < 0.0L) lin_fano = 0.0L;
    if (arith_fano < 0.0L) arith_fano = 0.0L;

    printf("{\"mode\":\"sigmaparts\",\"N\":%d,\"delta\":\"0x%x\","
           "\"q_occupied\":%llu,\"q_fraction\":%.9Lf,\"q_max\":\"0x%x\",\"q_max_count\":%llu,\"q_fano\":%.6Lf,"
           "\"lin_occupied\":%llu,\"lin_fraction\":%.9Lf,\"lin_max\":\"0x%x\",\"lin_max_count\":%llu,\"lin_fano\":%.6Lf,"
           "\"arith_occupied\":%llu,\"arith_fraction\":%.9Lf,\"arith_max\":\"0x%x\",\"arith_max_count\":%llu,\"arith_fano\":%.6Lf}\n",
           N, delta,
           (unsigned long long)q_occ, (long double)q_occ / (long double)limit,
           q_max_v, (unsigned long long)q_max, q_fano,
           (unsigned long long)lin_occ, (long double)lin_occ / (long double)limit,
           lin_max_v, (unsigned long long)lin_max, lin_fano,
           (unsigned long long)arith_occ, (long double)arith_occ / (long double)limit,
           arith_max_v, (unsigned long long)arith_max, arith_fano);

    free(q_hist);
    free(lin_hist);
    free(arith_hist);
}

static uint32_t sample_table_insert(sample_bucket_t *table, uint32_t table_mask,
                                    uint32_t key, uint32_t *unique) {
    uint32_t pos = (key * 2654435761U) & table_mask;
    while (table[pos].used && table[pos].key != key) {
        pos = (pos + 1U) & table_mask;
    }
    if (!table[pos].used) {
        table[pos].used = 1;
        table[pos].key = key;
        table[pos].count = 1;
        (*unique)++;
        return 1;
    }
    table[pos].count++;
    return table[pos].count;
}

static void sigma_diff_sample(int N, uint32_t delta, uint32_t samples, int table_bits) {
    if (N < 4 || N > 32) {
        fprintf(stderr, "sigmasample mode requires N=4..32.\n");
        exit(2);
    }
    if (table_bits < 10) table_bits = 10;
    if (table_bits > 28) table_bits = 28;
    if (samples == 0) samples = 1;
    uint32_t table_size = 1U << table_bits;
    if (samples * 2U > table_size && table_bits < 28) {
        fprintf(stderr, "warning: table load factor may be high; increase TABLE_BITS\n");
    }

    sha256_init(N);
    delta &= maskn();

    sample_bucket_t *q_table = calloc((size_t)table_size, sizeof(sample_bucket_t));
    sample_bucket_t *lin_table = calloc((size_t)table_size, sizeof(sample_bucket_t));
    sample_bucket_t *arith_table = calloc((size_t)table_size, sizeof(sample_bucket_t));
    if (!q_table || !lin_table || !arith_table) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }

    uint32_t table_mask = table_size - 1U;
    uint32_t q_unique = 0, lin_unique = 0, arith_unique = 0;
    uint32_t q_max = 0, lin_max = 0, arith_max = 0;
    uint32_t q_max_key = 0, lin_max_key = 0, arith_max_key = 0;
    uint64_t rng = 0x1234abcd9876fedcULL ^ ((uint64_t)delta << 17) ^ (uint64_t)N;

    for (uint32_t i = 0; i < samples; i++) {
        uint32_t w = splitmix32_local(&rng) & maskn();
        uint32_t wp = (w + delta) & maskn();
        uint32_t q = (wp ^ w) & maskn();
        uint32_t lin = (sha256_sigma1(wp) ^ sha256_sigma1(w)) & maskn();
        uint32_t arith = subn(sha256_sigma1(wp), sha256_sigma1(w));

        uint32_t c = sample_table_insert(q_table, table_mask, q, &q_unique);
        if (c > q_max) {
            q_max = c;
            q_max_key = q;
        }
        c = sample_table_insert(lin_table, table_mask, lin, &lin_unique);
        if (c > lin_max) {
            lin_max = c;
            lin_max_key = lin;
        }
        c = sample_table_insert(arith_table, table_mask, arith, &arith_unique);
        if (c > arith_max) {
            arith_max = c;
            arith_max_key = arith;
        }
    }

    printf("{\"mode\":\"sigmasample\",\"N\":%d,\"delta\":\"0x%x\","
           "\"samples\":%u,\"table_bits\":%d,"
           "\"q_unique\":%u,\"q_unique_rate\":%.9f,\"q_max\":\"0x%x\",\"q_max_count\":%u,"
           "\"lin_unique\":%u,\"lin_unique_rate\":%.9f,\"lin_max\":\"0x%x\",\"lin_max_count\":%u,"
           "\"arith_unique\":%u,\"arith_unique_rate\":%.9f,\"arith_max\":\"0x%x\",\"arith_max_count\":%u}\n",
           N, delta, samples, table_bits,
           q_unique, (double)q_unique / (double)samples, q_max_key, q_max,
           lin_unique, (double)lin_unique / (double)samples, lin_max_key, lin_max,
           arith_unique, (double)arith_unique / (double)samples, arith_max_key, arith_max);

    free(q_table);
    free(lin_table);
    free(arith_table);
}

static void off58_scan(int N, int bit, uint32_t fill, int w57_limit_arg) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    int w57_limit = (w57_limit_arg <= 0 || w57_limit_arg > (int)limit) ? (int)limit : w57_limit_arg;
    uint64_t *hist = calloc((size_t)limit, sizeof(uint64_t));
    uint32_t *first_w57 = calloc((size_t)limit, sizeof(uint32_t));
    if (!hist || !first_w57) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }
    for (uint32_t i = 0; i < limit; i++) first_w57[i] = UINT32_MAX;

    uint64_t hw_le_1 = 0;
    uint64_t hw_le_2 = 0;
    uint64_t hw_le_4 = 0;
    uint64_t msb_set = 0;
    uint64_t exact_msb = 0;
    uint64_t zero = 0;

    for (int w57_i = 0; w57_i < w57_limit; w57_i++) {
        uint32_t s1_57[8], s2_57[8];
        memcpy(s1_57, p1.state, sizeof(s1_57));
        memcpy(s2_57, p2.state, sizeof(s2_57));
        uint32_t off57 = cascade1_offset(s1_57, s2_57);
        apply_round(s1_57, (uint32_t)w57_i, 57);
        apply_round(s2_57, ((uint32_t)w57_i + off57) & maskn(), 57);
        uint32_t off58 = cascade1_offset(s1_57, s2_57);

        if (hist[off58] == 0) first_w57[off58] = (uint32_t)w57_i;
        hist[off58]++;

        int h = hw(off58);
        if (h <= 1) hw_le_1++;
        if (h <= 2) hw_le_2++;
        if (h <= 4) hw_le_4++;
        if (off58 & sha256_MSB) msb_set++;
        if (off58 == sha256_MSB) exact_msb++;
        if (off58 == 0) zero++;
    }

    uint64_t occupied = 0;
    uint64_t max_count = 0;
    uint32_t max_off58 = 0;

    int top_off58[16];
    uint64_t top_count[16];
    uint32_t top_first_w57[16];
    for (int i = 0; i < 16; i++) {
        top_off58[i] = 0;
        top_count[i] = 0;
        top_first_w57[i] = 0;
    }

    for (uint32_t off = 0; off < limit; off++) {
        uint64_t c = hist[off];
        if (c) occupied++;
        if (c > max_count) {
            max_count = c;
            max_off58 = off;
        }
        for (int k = 0; k < 16; k++) {
            if (c > top_count[k]) {
                for (int j = 15; j > k; j--) {
                    top_count[j] = top_count[j - 1];
                    top_off58[j] = top_off58[j - 1];
                    top_first_w57[j] = top_first_w57[j - 1];
                }
                top_count[k] = c;
                top_off58[k] = (int)off;
                top_first_w57[k] = first_w57[off];
                break;
            }
        }
    }

    printf("{\"mode\":\"off58scan\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57_checked\":%d,\"occupied_off58\":%llu,\"max_off58\":\"0x%x\","
           "\"max_count\":%llu,\"hw_le_1\":%llu,\"hw_le_2\":%llu,\"hw_le_4\":%llu,"
           "\"msb_set\":%llu,\"exact_msb\":%llu,\"zero\":%llu,\"top\":[",
           N, bit, fill, m0, w57_limit, (unsigned long long)occupied,
           max_off58, (unsigned long long)max_count,
           (unsigned long long)hw_le_1, (unsigned long long)hw_le_2,
           (unsigned long long)hw_le_4, (unsigned long long)msb_set,
           (unsigned long long)exact_msb, (unsigned long long)zero);
    for (int i = 0; i < 16 && i < (int)limit; i++) {
        if (i) printf(",");
        printf("{\"off58\":\"0x%x\",\"count\":%llu,\"first_w57\":\"0x%x\",\"hw\":%d}",
               top_off58[i], (unsigned long long)top_count[i],
               top_first_w57[i], hw((uint32_t)top_off58[i]));
    }
    printf("]}\n");

    free(hist);
    free(first_w57);
}

static void off58_find(int N, int bit, uint32_t fill, uint32_t target_off58) {
    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return;
    }

    uint32_t limit = 1U << N;
    target_off58 &= maskn();
    uint64_t count = 0;
    uint32_t first[32];
    for (int i = 0; i < 32; i++) first[i] = 0;

    for (uint32_t w57 = 0; w57 < limit; w57++) {
        uint32_t s1_57[8], s2_57[8];
        memcpy(s1_57, p1.state, sizeof(s1_57));
        memcpy(s2_57, p2.state, sizeof(s2_57));
        uint32_t off57 = cascade1_offset(s1_57, s2_57);
        apply_round(s1_57, w57, 57);
        apply_round(s2_57, (w57 + off57) & maskn(), 57);
        uint32_t off58 = cascade1_offset(s1_57, s2_57);
        if (off58 == target_off58) {
            if (count < 32) first[count] = w57;
            count++;
        }
    }

    printf("{\"mode\":\"off58find\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"target_off58\":\"0x%x\",\"count\":%llu,\"first_w57\":[",
           N, bit, fill, m0, target_off58, (unsigned long long)count);
    for (uint64_t i = 0; i < count && i < 32; i++) {
        if (i) printf(",");
        printf("\"0x%x\"", first[i]);
    }
    printf("]}\n");
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "sigmasample") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 32;
        uint32_t delta = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 1;
        uint32_t samples = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 1000000U;
        int table_bits = (argc >= 6) ? atoi(argv[5]) : 22;
        sigma_diff_sample(N, delta, samples, table_bits);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "sigmaparts") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        uint32_t delta = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 1;
        sigma_diff_parts_scan(N, delta);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "off58find") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t target_off58 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : (1U << (N - 1));
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "off58find mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        off58_find(N, bit, fill, target_off58);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "off58scan") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        int w57_limit = (argc >= 6) ? atoi(argv[5]) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "off58scan mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        off58_scan(N, bit, fill, w57_limit);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "sigmadiff") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        uint32_t delta = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 1;
        sigma_diff_scan(N, delta);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "schedscan") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t w57 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "schedscan mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        sched_offset_scan_for_w57(N, bit, fill, w57);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "reqhist") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t w57 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        uint32_t w58 = (argc >= 7) ? (uint32_t)strtoul(argv[6], NULL, 0) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "reqhist mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        req_histogram_for_w57_w58(N, bit, fill, w57, w58);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "defecthist") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t w57 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "defecthist mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        defect_histogram_for_w57(N, bit, fill, w57);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "carrybias") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t w57 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        uint32_t w58 = (argc >= 7) ? (uint32_t)strtoul(argv[6], NULL, 0) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "carrybias mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        carry_bias_for_w57_w58(N, bit, fill, w57, w58);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "suffixscan") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        int suffix_bits = (argc >= 6) ? atoi(argv[5]) : 8;
        int w57_limit = (argc >= 7) ? atoi(argv[6]) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "suffixscan mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        suffix_scan_w57_range(N, bit, fill, suffix_bits, w57_limit);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "suffix") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t w57 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        int suffix_bits = (argc >= 7) ? atoi(argv[6]) : 8;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "suffix mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        suffix_profile_single_w57(N, bit, fill, w57, suffix_bits);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "hits") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t w57 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        uint32_t w58 = (argc >= 7) ? (uint32_t)strtoul(argv[6], NULL, 0) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "hits mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        list_hits_for_w57_w58(N, bit, fill, w57, w58);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "single") == 0) {
        int N = (argc >= 3) ? atoi(argv[2]) : 12;
        int bit = (argc >= 4) ? atoi(argv[3]) : (N - 1);
        uint32_t fill = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : ((1U << N) - 1);
        uint32_t w57 = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        if (N < 4 || N > 16 || bit < 0 || bit >= N) {
            fprintf(stderr, "single mode requires N=4..16 and bit=0..N-1.\n");
            return 2;
        }
        sha256_init(N);
        fill &= maskn();
        count_nested_single_w57(N, bit, fill, w57);
        return 0;
    }

    int N = (argc >= 2) ? atoi(argv[1]) : 8;
    int bit = (argc >= 3) ? atoi(argv[2]) : (N - 1);
    uint32_t fill = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : ((1U << N) - 1);
    int w57_limit_arg = (argc >= 5) ? atoi(argv[4]) : 0;

    if (N < 4 || N > 16) {
        fprintf(stderr, "N must be 4..16 for this exact counter.\n");
        return 2;
    }
    if (bit < 0 || bit >= N) {
        fprintf(stderr, "bit must be in 0..N-1.\n");
        return 2;
    }

    sha256_init(N);
    uint32_t limit = 1U << N;
    fill &= maskn();
    int w57_limit = (w57_limit_arg <= 0 || w57_limit_arg > (int)limit) ? (int)limit : w57_limit_arg;

    sha256_precomp_t p1, p2;
    uint32_t m0 = 0;
    if (!prepare_candidate(N, bit, fill, &m0, &p1, &p2)) {
        printf("{\"error\":\"no_cascade_candidate\",\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\"}\n",
               N, bit, fill);
        return 1;
    }

    fprintf(stderr, "defect_fiber_counter N=%d bit=%d fill=0x%x m0=0x%x w57_limit=%d threads=%d\n",
            N, bit, fill, m0, w57_limit, omp_get_max_threads());

    fiber_summary_t total;
    memset(&total, 0, sizeof(total));

    #pragma omp parallel
    {
        fiber_summary_t local;
        memset(&local, 0, sizeof(local));

        #pragma omp for schedule(dynamic, 1)
        for (int w57_i = 0; w57_i < w57_limit; w57_i++) {
            uint64_t hits = count_fiber_for_w57(&p1, &p2, (uint32_t)w57_i,
                                                local.low8_hist, local.hw_hist);
            local.total_pairs += (uint64_t)limit * (uint64_t)limit;
            local.total_hits += hits;
            local.sum_hits_sq += (long double)hits * (long double)hits;
            if (hits) local.nonempty_w57++;
            if (hits > local.max_hits) {
                local.max_hits = hits;
                local.max_w57 = (uint32_t)w57_i;
            }
        }

        #pragma omp critical
        merge_summary(&total, &local);
    }

    double expected_per_w57 = (double)limit;
    double avg_per_w57 = (double)total.total_hits / (double)w57_limit;
    double enrichment = expected_per_w57 > 0.0 ? avg_per_w57 / expected_per_w57 : 0.0;
    long double mean = (long double)total.total_hits / (long double)w57_limit;
    long double variance = total.sum_hits_sq / (long double)w57_limit - mean * mean;
    if (variance < 0.0L) variance = 0.0L;
    long double fano = mean > 0.0L ? variance / mean : 0.0L;
    long double max_enrichment = expected_per_w57 > 0.0 ? (long double)total.max_hits / (long double)expected_per_w57 : 0.0L;

    int min_hw_seen = -1;
    for (int i = 0; i <= N; i++) {
        if (total.hw_hist[i]) {
            min_hw_seen = i;
            break;
        }
    }

    uint64_t low8_min = total.low8_hist[0], low8_max = total.low8_hist[0];
    int low8_min_bucket = 0, low8_max_bucket = 0;
    for (int i = 1; i < 256; i++) {
        if (total.low8_hist[i] < low8_min) {
            low8_min = total.low8_hist[i];
            low8_min_bucket = i;
        }
        if (total.low8_hist[i] > low8_max) {
            low8_max = total.low8_hist[i];
            low8_max_bucket = i;
        }
    }

    printf("{\"N\":%d,\"bit\":%d,\"fill\":\"0x%x\",\"m0\":\"0x%x\","
           "\"w57_checked\":%d,\"total_pairs\":%llu,\"total_hits\":%llu,"
           "\"expected_hits_per_w57\":%.1f,\"avg_hits_per_w57\":%.3f,"
           "\"enrichment\":%.6f,\"variance\":%.3Lf,\"fano\":%.3Lf,"
           "\"nonempty_w57\":%llu,\"max_hits\":%llu,\"max_enrichment\":%.6Lf,"
           "\"max_w57\":\"0x%x\",\"min_defect_hw_seen\":%d,"
           "\"low8_zero_count\":%llu,\"low8_min\":%llu,\"low8_min_bucket\":%d,"
           "\"low8_max\":%llu,\"low8_max_bucket\":%d}\n",
           N, bit, fill, m0,
           w57_limit, (unsigned long long)total.total_pairs,
           (unsigned long long)total.total_hits,
           expected_per_w57, avg_per_w57, enrichment,
           variance, fano,
           (unsigned long long)total.nonempty_w57,
           (unsigned long long)total.max_hits, max_enrichment, total.max_w57,
           min_hw_seen,
           (unsigned long long)total.low8_hist[0],
           (unsigned long long)low8_min, low8_min_bucket,
           (unsigned long long)low8_max, low8_max_bucket);

    return 0;
}
