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
    for (uint32_t w59 = 0; w59 < limit; w59++) {
        uint32_t s1_59[8], s2_59[8];
        memcpy(s1_59, s1_58, sizeof(s1_59));
        memcpy(s2_59, s2_58, sizeof(s2_59));
        uint32_t off59 = cascade1_offset(s1_59, s2_59);
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
        }
    }
    printf("],\"count\":%llu,"
           "\"avg_all_ch_inv\":%.3f,\"avg_hit_ch_inv\":%.3f,"
           "\"avg_all_maj_a_inv\":%.3f,\"avg_hit_maj_a_inv\":%.3f,"
           "\"avg_all_maj_b_inv\":%.3f,\"avg_hit_maj_b_inv\":%.3f,"
           "\"avg_all_maj_c_inv\":%.3f,\"avg_hit_maj_c_inv\":%.3f}\n",
           (unsigned long long)hits,
           (double)all_ch_inv / (double)limit,
           hits ? (double)hit_ch_inv / (double)hits : 0.0,
           (double)all_maj_a_inv / (double)limit,
           hits ? (double)hit_maj_a_inv / (double)hits : 0.0,
           (double)all_maj_b_inv / (double)limit,
           hits ? (double)hit_maj_b_inv / (double)hits : 0.0,
           (double)all_maj_c_inv / (double)limit,
           hits ? (double)hit_maj_c_inv / (double)hits : 0.0);
}

int main(int argc, char **argv) {
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
