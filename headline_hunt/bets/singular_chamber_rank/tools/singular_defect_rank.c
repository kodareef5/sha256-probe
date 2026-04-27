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
 *   /tmp/singular_defect_rank frontier61pool 8 65536 8 72 32 0xaf07f044 0x73db5ecf 0xb767da21 0xaf07f044 0x73db5f4f 0xa7679a23
 *   /tmp/singular_defect_rank bridge61point 8 0xaf07f044 0x73db5f4f 0xa7679a23 0x73db5ecf 0xb767da21 1
 *   /tmp/singular_defect_rank nearexact61point 8 0xaf07f044 0x73db5ecf 0xb767da21 7
 *   /tmp/singular_defect_rank ridge61walk 8 0xaf07f044 0x569a93da 0x1f813291 1048576 8 128 24 8
 *   /tmp/singular_defect_rank capped61walk 8 0xaf07f044 0xddf3a9d3 0x76046f0d 1048576 8 128 24 3
 *   /tmp/singular_defect_rank pair61residualpoint 8 0xaf07f044 0xddf3a9d3 0x76046f0d 3
 *   /tmp/singular_defect_rank carrycmp61point 8 0xaf07f044 0xdd73a9d7 0x57046fad 0xaf07f044 0xdd55ab86 0x1d9ca68f
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
    {"msb_m189b13c7_80",           0x189b13c7U, 0x80000000U, 31},
    {"bit13_m4e560940_aa",         0x4e560940U, 0xaaaaaaaaU, 13},
    {"bit17_m427c281d_80",         0x427c281dU, 0x80000000U, 17},
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

static uint64_t next_combination64(uint64_t x);

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

#define MSG_FREE_WORDS 14
#define MSG_DEFECT_ROUNDS 5
#define MSG_CONSTRAINT_WORDS (MSG_DEFECT_ROUNDS + 1)

static const int MSG_FREE_INDEX[MSG_FREE_WORDS] = {
    1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15
};

typedef struct {
    uint32_t a57_xor;
    uint32_t defects[MSG_DEFECT_ROUNDS];
    uint32_t dW[MSG_DEFECT_ROUNDS];
    uint32_t req[MSG_DEFECT_ROUNDS];
    int a57_hw;
    int defect_hw[MSG_DEFECT_ROUNDS];
    int total_hw;
    int constraint_hw;
    int prefix_zero;
    int state_hw;
} msg61_eval_t;

static void expand_schedule64(const uint32_t M[16], uint32_t W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 64; i++) {
        W[i] = sha256_sigma1(W[i - 2]) + W[i - 7] +
               sha256_sigma0(W[i - 15]) + W[i - 16];
    }
}

static void build_candidate_messages(const candidate_t *cand,
                                     const uint32_t free_words[MSG_FREE_WORDS],
                                     uint32_t M1[16], uint32_t M2[16]) {
    uint32_t diff = 1U << cand->bit;
    for (int i = 0; i < 16; i++) {
        M1[i] = cand->fill;
        M2[i] = cand->fill;
    }
    M1[0] = cand->m0;
    M2[0] = cand->m0 ^ diff;
    M2[9] = cand->fill ^ diff;
    for (int i = 0; i < MSG_FREE_WORDS; i++) {
        int word = MSG_FREE_INDEX[i];
        M1[word] = free_words[i];
        M2[word] = free_words[i];
    }
}

static void msg61_eval_candidate(const candidate_t *cand,
                                 const uint32_t free_words[MSG_FREE_WORDS],
                                 msg61_eval_t *out) {
    uint32_t M1[16], M2[16], W1[64], W2[64];
    build_candidate_messages(cand, free_words, M1, M2);
    expand_schedule64(M1, W1);
    expand_schedule64(M2, W2);

    uint32_t s1[8], s2[8];
    memcpy(s1, sha256_IV, sizeof(s1));
    memcpy(s2, sha256_IV, sizeof(s2));

    memset(out, 0, sizeof(*out));

    for (int r = 0; r < 64; r++) {
        if (r >= 57 && r <= 61) {
            int j = r - 57;
            if (j == 0) {
                out->a57_xor = s1[0] ^ s2[0];
                out->a57_hw = hw32(out->a57_xor);
            }
            out->req[j] = cascade1_offset(s1, s2);
            out->dW[j] = W2[r] - W1[r];
            out->defects[j] = out->dW[j] - out->req[j];
            out->defect_hw[j] = hw32(out->defects[j]);
            out->total_hw += out->defect_hw[j];
        }
        apply_round(s1, W1[r], r);
        apply_round(s2, W2[r], r);
    }

    out->constraint_hw = out->a57_hw + out->total_hw;
    out->prefix_zero = 0;
    if (out->a57_xor == 0) {
        for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) {
            if (out->defects[j] != 0) break;
            out->prefix_zero++;
        }
    }

    out->state_hw = 0;
    for (int i = 0; i < 8; i++) out->state_hw += hw32(s1[i] ^ s2[i]);
}

static int msg61_better(const msg61_eval_t *a, const msg61_eval_t *b) {
    if (a->prefix_zero != b->prefix_zero) return a->prefix_zero > b->prefix_zero;
    if (a->constraint_hw != b->constraint_hw) return a->constraint_hw < b->constraint_hw;
    if (a->total_hw != b->total_hw) return a->total_hw < b->total_hw;
    return a->state_hw < b->state_hw;
}

static int msg61_prefix_hw(const msg61_eval_t *ev, int prefix) {
    int hw = ev->a57_hw;
    if (prefix < 1) prefix = 1;
    if (prefix > MSG_DEFECT_ROUNDS) prefix = MSG_DEFECT_ROUNDS;
    for (int i = 0; i < prefix; i++) hw += ev->defect_hw[i];
    return hw;
}

static int msg61_better_prefix(const msg61_eval_t *a, const msg61_eval_t *b,
                               int prefix) {
    int ap = a->prefix_zero < prefix ? a->prefix_zero : prefix;
    int bp = b->prefix_zero < prefix ? b->prefix_zero : prefix;
    if (ap != bp) return ap > bp;
    int ahw = msg61_prefix_hw(a, prefix);
    int bhw = msg61_prefix_hw(b, prefix);
    if (ahw != bhw) return ahw < bhw;
    if (a->total_hw != b->total_hw) return a->total_hw < b->total_hw;
    return a->state_hw < b->state_hw;
}

static void msg61_fill_words(const candidate_t *cand,
                             uint32_t free_words[MSG_FREE_WORDS]) {
    for (int i = 0; i < MSG_FREE_WORDS; i++) free_words[i] = cand->fill;
}

static void msg61_print_words(const uint32_t free_words[MSG_FREE_WORDS]) {
    printf("[");
    for (int i = 0; i < MSG_FREE_WORDS; i++) {
        printf("%s\"0x%08x\"", i ? "," : "", free_words[i]);
    }
    printf("]");
}

static int msg61_words_equal(const uint32_t a[MSG_FREE_WORDS],
                             const uint32_t b[MSG_FREE_WORDS]) {
    for (int i = 0; i < MSG_FREE_WORDS; i++) {
        if (a[i] != b[i]) return 0;
    }
    return 1;
}

static void msg61_print_eval_fields(const msg61_eval_t *ev) {
    printf("\"a57_xor\":\"0x%08x\",\"a57_hw\":%d,\"defects\":[",
           ev->a57_xor, ev->a57_hw);
    for (int i = 0; i < MSG_DEFECT_ROUNDS; i++) {
        printf("%s\"0x%08x\"", i ? "," : "", ev->defects[i]);
    }
    printf("],\"defect_hw\":[");
    for (int i = 0; i < MSG_DEFECT_ROUNDS; i++) {
        printf("%s%d", i ? "," : "", ev->defect_hw[i]);
    }
    printf("],\"dW\":[");
    for (int i = 0; i < MSG_DEFECT_ROUNDS; i++) {
        printf("%s\"0x%08x\"", i ? "," : "", ev->dW[i]);
    }
    printf("],\"req\":[");
    for (int i = 0; i < MSG_DEFECT_ROUNDS; i++) {
        printf("%s\"0x%08x\"", i ? "," : "", ev->req[i]);
    }
    printf("],\"total_hw\":%d,\"constraint_hw\":%d,"
           "\"prefix_zero\":%d,\"state_hw\":%d",
           ev->total_hw, ev->constraint_hw, ev->prefix_zero, ev->state_hw);
}

static void msg61_point_candidate(int idx, const uint32_t *maybe_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t words[MSG_FREE_WORDS];
    if (maybe_words) {
        memcpy(words, maybe_words, sizeof(words));
    } else {
        msg61_fill_words(cand, words);
    }
    msg61_eval_t ev;
    msg61_eval_candidate(cand, words, &ev);
    printf("{\"mode\":\"msg61point\",\"candidate\":\"%s\",\"idx\":%d,\"free_word_index\":[",
           cand->id, idx);
    for (int i = 0; i < MSG_FREE_WORDS; i++) {
        printf("%s%d", i ? "," : "", MSG_FREE_INDEX[i]);
    }
    printf("],\"free_words\":");
    msg61_print_words(words);
    printf(",");
    msg61_print_eval_fields(&ev);
    printf("}\n");
}

static int rank160_vectors(const uint32_t vecs[][MSG_DEFECT_ROUNDS], int n) {
    uint32_t basis[160][MSG_DEFECT_ROUNDS];
    memset(basis, 0, sizeof(basis));
    int rank = 0;
    for (int i = 0; i < n; i++) {
        uint32_t v[MSG_DEFECT_ROUNDS];
        memcpy(v, vecs[i], sizeof(v));
        for (int bit = 159; bit >= 0; bit--) {
            int word = bit / 32;
            int shift = bit % 32;
            if (((v[word] >> shift) & 1U) == 0) continue;
            if (basis[bit][word]) {
                for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) v[j] ^= basis[bit][j];
            } else {
                memcpy(basis[bit], v, sizeof(v));
                rank++;
                break;
            }
        }
    }
    return rank;
}

static int rank192_vectors(const uint32_t vecs[][MSG_CONSTRAINT_WORDS], int n) {
    uint32_t basis[192][MSG_CONSTRAINT_WORDS];
    memset(basis, 0, sizeof(basis));
    int rank = 0;
    for (int i = 0; i < n; i++) {
        uint32_t v[MSG_CONSTRAINT_WORDS];
        memcpy(v, vecs[i], sizeof(v));
        for (int bit = 191; bit >= 0; bit--) {
            int word = bit / 32;
            int shift = bit % 32;
            if (((v[word] >> shift) & 1U) == 0) continue;
            if (basis[bit][word]) {
                for (int j = 0; j < MSG_CONSTRAINT_WORDS; j++) v[j] ^= basis[bit][j];
            } else {
                memcpy(basis[bit], v, sizeof(v));
                rank++;
                break;
            }
        }
    }
    return rank;
}

static void msg61_rank_candidate(int idx) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t base_words[MSG_FREE_WORDS];
    msg61_fill_words(cand, base_words);

    msg61_eval_t base_ev;
    msg61_eval_candidate(cand, base_words, &base_ev);

    uint32_t cols[MSG_FREE_WORDS * 32][MSG_DEFECT_ROUNDS];
    uint32_t guarded_cols[MSG_FREE_WORDS * 32][MSG_CONSTRAINT_WORDS];
    int word_rank[MSG_FREE_WORDS];
    int guarded_word_rank[MSG_FREE_WORDS];
    int c = 0;
    for (int wi = 0; wi < MSG_FREE_WORDS; wi++) {
        uint32_t word_cols[32][MSG_DEFECT_ROUNDS];
        uint32_t guarded_word_cols[32][MSG_CONSTRAINT_WORDS];
        for (int b = 0; b < 32; b++) {
            uint32_t words[MSG_FREE_WORDS];
            memcpy(words, base_words, sizeof(words));
            words[wi] ^= 1U << b;
            msg61_eval_t ev;
            msg61_eval_candidate(cand, words, &ev);
            guarded_cols[c][0] = ev.a57_xor ^ base_ev.a57_xor;
            guarded_word_cols[b][0] = guarded_cols[c][0];
            for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) {
                cols[c][j] = ev.defects[j] ^ base_ev.defects[j];
                word_cols[b][j] = cols[c][j];
                guarded_cols[c][j + 1] = cols[c][j];
                guarded_word_cols[b][j + 1] = guarded_cols[c][j + 1];
            }
            c++;
        }
        word_rank[wi] = rank160_vectors(word_cols, 32);
        guarded_word_rank[wi] = rank192_vectors(guarded_word_cols, 32);
    }

    int rank = rank160_vectors(cols, MSG_FREE_WORDS * 32);
    int guarded_rank = rank192_vectors(guarded_cols, MSG_FREE_WORDS * 32);
    printf("{\"mode\":\"msg61rank\",\"candidate\":\"%s\",\"idx\":%d,",
           cand->id, idx);
    printf("\"base_total_hw\":%d,\"base_constraint_hw\":%d,"
           "\"base_prefix_zero\":%d,\"rank_schedule\":%d,"
           "\"kernel_dim_schedule\":%d,\"rank_guarded\":%d,"
           "\"kernel_dim_guarded\":%d,\"word_rank_schedule\":[",
           base_ev.total_hw, base_ev.constraint_hw, base_ev.prefix_zero,
           rank, MSG_FREE_WORDS * 32 - rank, guarded_rank,
           MSG_FREE_WORDS * 32 - guarded_rank);
    for (int i = 0; i < MSG_FREE_WORDS; i++) {
        printf("%s%d", i ? "," : "", word_rank[i]);
    }
    printf("],\"word_rank_guarded\":[");
    for (int i = 0; i < MSG_FREE_WORDS; i++) {
        printf("%s%d", i ? "," : "", guarded_word_rank[i]);
    }
    printf("],\"free_word_index\":[");
    for (int i = 0; i < MSG_FREE_WORDS; i++) {
        printf("%s%d", i ? "," : "", MSG_FREE_INDEX[i]);
    }
    printf("],");
    msg61_print_eval_fields(&base_ev);
    printf("}\n");
}

static void msg61_sample_candidate(int idx, long long samples, int threads,
                                   int random_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (samples < 1) samples = 1;
    if (threads < 1) threads = 1;
    if (threads > 64) threads = 64;
    const candidate_t *cand = &CANDIDATES[idx];

    msg61_eval_t best_ev;
    uint32_t best_words[MSG_FREE_WORDS];
    msg61_fill_words(cand, best_words);
    msg61_eval_candidate(cand, best_words, &best_ev);
    long long exact_all = 0;
    long long prefix_hits[MSG_DEFECT_ROUNDS + 1];
    memset(prefix_hits, 0, sizeof(prefix_hits));

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x8bf91a735dULL ^ (uint64_t)idx * 0x9e3779b97f4a7c15ULL ^
                       (uint64_t)tid * 0xd1b54a32d192ed03ULL;
        msg61_eval_t local_best;
        uint32_t local_words[MSG_FREE_WORDS];
        msg61_fill_words(cand, local_words);
        msg61_eval_candidate(cand, local_words, &local_best);
        long long local_exact = 0;
        long long local_prefix[MSG_DEFECT_ROUNDS + 1];
        memset(local_prefix, 0, sizeof(local_prefix));

        #pragma omp for schedule(static)
        for (long long t = 0; t < samples; t++) {
            uint32_t words[MSG_FREE_WORDS];
            if (random_words) {
                for (int i = 0; i < MSG_FREE_WORDS; i++) words[i] = splitmix32(&rng);
            } else {
                msg61_fill_words(cand, words);
                int flips = 1 + (int)(splitmix32(&rng) % 32U);
                for (int k = 0; k < flips; k++) {
                    int bit = (int)(splitmix32(&rng) % (MSG_FREE_WORDS * 32U));
                    words[bit / 32] ^= 1U << (bit % 32);
                }
            }
            msg61_eval_t ev;
            msg61_eval_candidate(cand, words, &ev);
            local_prefix[ev.prefix_zero]++;
            if (ev.prefix_zero == MSG_DEFECT_ROUNDS) local_exact++;
            if (msg61_better(&ev, &local_best)) {
                local_best = ev;
                memcpy(local_words, words, sizeof(local_words));
            }
        }

        #pragma omp critical
        {
            exact_all += local_exact;
            for (int i = 0; i <= MSG_DEFECT_ROUNDS; i++) prefix_hits[i] += local_prefix[i];
            if (msg61_better(&local_best, &best_ev)) {
                best_ev = local_best;
                memcpy(best_words, local_words, sizeof(best_words));
            }
        }
    }

    printf("{\"mode\":\"msg61sample\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"samples\":%lld,\"threads\":%d,\"random_words\":%d,"
           "\"exact_all\":%lld,\"prefix_hits\":[",
           cand->id, idx, samples, threads, random_words, exact_all);
    for (int i = 0; i <= MSG_DEFECT_ROUNDS; i++) {
        printf("%s%lld", i ? "," : "", prefix_hits[i]);
    }
    printf("],\"best_free_words\":");
    msg61_print_words(best_words);
    printf(",");
    msg61_print_eval_fields(&best_ev);
    printf("}\n");
}

static void msg61_walk_candidate(int idx, long long trials, int threads,
                                 int max_passes, int start_flips,
                                 int random_words, int objective_prefix,
                                 const uint32_t *seed_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (trials < 1) trials = 1;
    if (threads < 1) threads = 1;
    if (threads > 64) threads = 64;
    if (max_passes < 1) max_passes = 1;
    if (start_flips < 0) start_flips = 0;
    if (start_flips > MSG_FREE_WORDS * 32) start_flips = MSG_FREE_WORDS * 32;
    if (objective_prefix < 1) objective_prefix = 1;
    if (objective_prefix > MSG_DEFECT_ROUNDS) objective_prefix = MSG_DEFECT_ROUNDS;

    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t base_words[MSG_FREE_WORDS];
    if (seed_words) {
        memcpy(base_words, seed_words, sizeof(base_words));
    } else {
        msg61_fill_words(cand, base_words);
    }
    msg61_eval_t best_ev;
    uint32_t best_words[MSG_FREE_WORDS];
    memcpy(best_words, base_words, sizeof(best_words));
    msg61_eval_candidate(cand, best_words, &best_ev);
    long long exact_all = 0;
    long long improved_trials = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xf17a5a2d61ULL ^ (uint64_t)idx * 0x9e3779b97f4a7c15ULL ^
                       (uint64_t)tid * 0xd1b54a32d192ed03ULL;
        msg61_eval_t local_best;
        uint32_t local_best_words[MSG_FREE_WORDS];
        memcpy(local_best_words, base_words, sizeof(local_best_words));
        msg61_eval_candidate(cand, local_best_words, &local_best);
        long long local_exact = 0;
        long long local_improved = 0;

        #pragma omp for schedule(dynamic, 256)
        for (long long t = 0; t < trials; t++) {
            uint32_t words[MSG_FREE_WORDS];
            if (random_words) {
                for (int i = 0; i < MSG_FREE_WORDS; i++) words[i] = splitmix32(&rng);
            } else {
                memcpy(words, base_words, sizeof(words));
                int flips = start_flips ? (int)(splitmix32(&rng) % (uint32_t)(start_flips + 1)) : 0;
                for (int k = 0; k < flips; k++) {
                    int bit = (int)(splitmix32(&rng) % (MSG_FREE_WORDS * 32U));
                    words[bit / 32] ^= 1U << (bit % 32);
                }
            }

            msg61_eval_t cur;
            msg61_eval_candidate(cand, words, &cur);
            int start_score = msg61_prefix_hw(&cur, objective_prefix);
            for (int p = 0; p < max_passes; p++) {
                int bit = (int)(splitmix32(&rng) % (MSG_FREE_WORDS * 32U));
                words[bit / 32] ^= 1U << (bit % 32);
                msg61_eval_t next;
                msg61_eval_candidate(cand, words, &next);
                if (msg61_better(&next, &cur)) {
                    cur = next;
                } else {
                    words[bit / 32] ^= 1U << (bit % 32);
                }
            }
            if (cur.prefix_zero >= objective_prefix) local_exact++;
            if (msg61_prefix_hw(&cur, objective_prefix) < start_score) local_improved++;
            if (msg61_better_prefix(&cur, &local_best, objective_prefix)) {
                local_best = cur;
                memcpy(local_best_words, words, sizeof(local_best_words));
            }
        }

        #pragma omp critical
        {
            exact_all += local_exact;
            improved_trials += local_improved;
            if (msg61_better_prefix(&local_best, &best_ev, objective_prefix)) {
                best_ev = local_best;
                memcpy(best_words, local_best_words, sizeof(best_words));
            }
        }
    }

    printf("{\"mode\":\"msg61walk\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"trials\":%lld,\"threads\":%d,\"max_passes\":%d,"
           "\"start_flips\":%d,\"random_words\":%d,\"objective_prefix\":%d,"
           "\"exact_prefix\":%lld,\"improved_trials\":%lld,"
           "\"best_prefix_hw\":%d,\"seeded\":%d,\"best_free_words\":",
           cand->id, idx, trials, threads, max_passes, start_flips,
           random_words, objective_prefix, exact_all, improved_trials,
           msg61_prefix_hw(&best_ev, objective_prefix), seed_words ? 1 : 0);
    msg61_print_words(best_words);
    printf(",");
    msg61_print_eval_fields(&best_ev);
    printf("}\n");
}

#define MSG_BITS (MSG_FREE_WORDS * 32)
#define MSG_COMBO_WORDS ((MSG_BITS + 63) / 64)

static int solve160_columns(const uint32_t cols[MSG_BITS][MSG_DEFECT_ROUNDS],
                            const uint32_t target[MSG_DEFECT_ROUNDS],
                            uint64_t solution[MSG_COMBO_WORDS],
                            int *rank_out) {
    uint32_t basis[160][MSG_DEFECT_ROUNDS];
    uint64_t combo[160][MSG_COMBO_WORDS];
    memset(basis, 0, sizeof(basis));
    memset(combo, 0, sizeof(combo));
    int rank = 0;

    for (int i = 0; i < MSG_BITS; i++) {
        uint32_t v[MSG_DEFECT_ROUNDS];
        uint64_t c[MSG_COMBO_WORDS];
        memcpy(v, cols[i], sizeof(v));
        memset(c, 0, sizeof(c));
        c[i / 64] = 1ULL << (i % 64);

        for (int bit = 159; bit >= 0; bit--) {
            int word = bit / 32;
            int shift = bit % 32;
            if (((v[word] >> shift) & 1U) == 0) continue;
            if (basis[bit][word]) {
                for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) v[j] ^= basis[bit][j];
                for (int j = 0; j < MSG_COMBO_WORDS; j++) c[j] ^= combo[bit][j];
            } else {
                memcpy(basis[bit], v, sizeof(v));
                memcpy(combo[bit], c, sizeof(c));
                rank++;
                break;
            }
        }
    }

    memset(solution, 0, MSG_COMBO_WORDS * sizeof(uint64_t));
    uint32_t t[MSG_DEFECT_ROUNDS];
    memcpy(t, target, sizeof(t));
    for (int bit = 159; bit >= 0; bit--) {
        int word = bit / 32;
        int shift = bit % 32;
        if (((t[word] >> shift) & 1U) == 0) continue;
        if (!basis[bit][word]) {
            if (rank_out) *rank_out = rank;
            return 0;
        }
        for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) t[j] ^= basis[bit][j];
        for (int j = 0; j < MSG_COMBO_WORDS; j++) solution[j] ^= combo[bit][j];
    }

    if (rank_out) *rank_out = rank;
    return 1;
}

static int solve192_columns(const uint32_t cols[MSG_BITS][MSG_CONSTRAINT_WORDS],
                            const uint32_t target[MSG_CONSTRAINT_WORDS],
                            uint64_t solution[MSG_COMBO_WORDS],
                            int *rank_out) {
    uint32_t basis[192][MSG_CONSTRAINT_WORDS];
    uint64_t combo[192][MSG_COMBO_WORDS];
    memset(basis, 0, sizeof(basis));
    memset(combo, 0, sizeof(combo));
    int rank = 0;

    for (int i = 0; i < MSG_BITS; i++) {
        uint32_t v[MSG_CONSTRAINT_WORDS];
        uint64_t c[MSG_COMBO_WORDS];
        memcpy(v, cols[i], sizeof(v));
        memset(c, 0, sizeof(c));
        c[i / 64] = 1ULL << (i % 64);

        for (int bit = 191; bit >= 0; bit--) {
            int word = bit / 32;
            int shift = bit % 32;
            if (((v[word] >> shift) & 1U) == 0) continue;
            if (basis[bit][word]) {
                for (int j = 0; j < MSG_CONSTRAINT_WORDS; j++) v[j] ^= basis[bit][j];
                for (int j = 0; j < MSG_COMBO_WORDS; j++) c[j] ^= combo[bit][j];
            } else {
                memcpy(basis[bit], v, sizeof(v));
                memcpy(combo[bit], c, sizeof(c));
                rank++;
                break;
            }
        }
    }

    memset(solution, 0, MSG_COMBO_WORDS * sizeof(uint64_t));
    uint32_t t[MSG_CONSTRAINT_WORDS];
    memcpy(t, target, sizeof(t));
    for (int bit = 191; bit >= 0; bit--) {
        int word = bit / 32;
        int shift = bit % 32;
        if (((t[word] >> shift) & 1U) == 0) continue;
        if (!basis[bit][word]) {
            if (rank_out) *rank_out = rank;
            return 0;
        }
        for (int j = 0; j < MSG_CONSTRAINT_WORDS; j++) t[j] ^= basis[bit][j];
        for (int j = 0; j < MSG_COMBO_WORDS; j++) solution[j] ^= combo[bit][j];
    }

    if (rank_out) *rank_out = rank;
    return 1;
}

static int combo_hw(const uint64_t combo[MSG_COMBO_WORDS]) {
    int hw = 0;
    for (int i = 0; i < MSG_COMBO_WORDS; i++) hw += __builtin_popcountll(combo[i]);
    return hw;
}

static void msg_apply_combo(uint32_t words[MSG_FREE_WORDS],
                            const uint64_t combo[MSG_COMBO_WORDS]) {
    for (int bit = 0; bit < MSG_BITS; bit++) {
        if ((combo[bit / 64] >> (bit % 64)) & 1ULL) {
            words[bit / 32] ^= 1U << (bit % 32);
        }
    }
}

static void msg61_build_columns(const candidate_t *cand,
                                const uint32_t words[MSG_FREE_WORDS],
                                const msg61_eval_t *base_ev,
                                uint32_t cols[MSG_BITS][MSG_DEFECT_ROUNDS]) {
    for (int bit = 0; bit < MSG_BITS; bit++) {
        uint32_t next_words[MSG_FREE_WORDS];
        memcpy(next_words, words, sizeof(next_words));
        next_words[bit / 32] ^= 1U << (bit % 32);
        msg61_eval_t ev;
        msg61_eval_candidate(cand, next_words, &ev);
        for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) {
            cols[bit][j] = ev.defects[j] ^ base_ev->defects[j];
        }
    }
}

static void msg61_build_guarded_columns(const candidate_t *cand,
                                        const uint32_t words[MSG_FREE_WORDS],
                                        const msg61_eval_t *base_ev,
                                        uint32_t cols[MSG_BITS][MSG_CONSTRAINT_WORDS]) {
    for (int bit = 0; bit < MSG_BITS; bit++) {
        uint32_t next_words[MSG_FREE_WORDS];
        memcpy(next_words, words, sizeof(next_words));
        next_words[bit / 32] ^= 1U << (bit % 32);
        msg61_eval_t ev;
        msg61_eval_candidate(cand, next_words, &ev);
        cols[bit][0] = ev.a57_xor ^ base_ev->a57_xor;
        for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) {
            cols[bit][j + 1] = ev.defects[j] ^ base_ev->defects[j];
        }
    }
}

static void msg61_newton_candidate(int idx, int restarts, int max_iters,
                                   int jitter_flips, int threads,
                                   int solve_prefix) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (restarts < 1) restarts = 1;
    if (max_iters < 1) max_iters = 1;
    if (jitter_flips < 0) jitter_flips = 0;
    if (jitter_flips > MSG_BITS) jitter_flips = MSG_BITS;
    if (threads < 1) threads = 1;
    if (threads > 64) threads = 64;
    if (solve_prefix < 1) solve_prefix = 1;
    if (solve_prefix > MSG_DEFECT_ROUNDS) solve_prefix = MSG_DEFECT_ROUNDS;

    const candidate_t *cand = &CANDIDATES[idx];
    msg61_eval_t best_ev;
    uint32_t best_words[MSG_FREE_WORDS];
    msg61_fill_words(cand, best_words);
    msg61_eval_candidate(cand, best_words, &best_ev);
    int best_iter = 0;
    int best_restart = 0;
    int best_delta_hw = 0;
    int rank_failures = 0;
    int exact_hits = 0;
    int min_rank = 999;
    long long total_delta_hw = 0;
    long long delta_count = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x61e7a9c3ULL ^ (uint64_t)idx * 0x9e3779b97f4a7c15ULL ^
                       (uint64_t)tid * 0xd1b54a32d192ed03ULL;
        msg61_eval_t local_best;
        uint32_t local_best_words[MSG_FREE_WORDS];
        msg61_fill_words(cand, local_best_words);
        msg61_eval_candidate(cand, local_best_words, &local_best);
        int local_best_iter = 0;
        int local_best_restart = 0;
        int local_best_delta_hw = 0;
        int local_rank_failures = 0;
        int local_exact_hits = 0;
        int local_min_rank = 999;
        long long local_delta_hw = 0;
        long long local_delta_count = 0;

        #pragma omp for schedule(dynamic, 1)
        for (int r = 0; r < restarts; r++) {
            uint32_t words[MSG_FREE_WORDS];
            msg61_fill_words(cand, words);
            int flips = jitter_flips ? (int)(splitmix32(&rng) % (uint32_t)(jitter_flips + 1)) : 0;
            for (int k = 0; k < flips; k++) {
                int bit = (int)(splitmix32(&rng) % (uint32_t)MSG_BITS);
                words[bit / 32] ^= 1U << (bit % 32);
            }

            for (int iter = 0; iter < max_iters; iter++) {
                msg61_eval_t ev;
                msg61_eval_candidate(cand, words, &ev);
                if (ev.prefix_zero >= solve_prefix) local_exact_hits++;
                if (msg61_better_prefix(&ev, &local_best, solve_prefix)) {
                    local_best = ev;
                    memcpy(local_best_words, words, sizeof(local_best_words));
                    local_best_iter = iter;
                    local_best_restart = r;
                }
                if (msg61_prefix_hw(&ev, solve_prefix) == 0) break;

                uint32_t cols[MSG_BITS][MSG_CONSTRAINT_WORDS];
                uint64_t solution[MSG_COMBO_WORDS];
                uint32_t target[MSG_CONSTRAINT_WORDS];
                int rank = 0;
                msg61_build_guarded_columns(cand, words, &ev, cols);
                target[0] = ev.a57_xor;
                for (int j = 0; j < MSG_DEFECT_ROUNDS; j++) {
                    target[j + 1] = ev.defects[j];
                }
                for (int b = 0; b < MSG_BITS; b++) {
                    for (int j = solve_prefix + 1; j < MSG_CONSTRAINT_WORDS; j++) cols[b][j] = 0;
                }
                for (int j = solve_prefix + 1; j < MSG_CONSTRAINT_WORDS; j++) target[j] = 0;
                int solvable = solve192_columns(cols, target, solution, &rank);
                if (rank < local_min_rank) local_min_rank = rank;
                if (!solvable) {
                    local_rank_failures++;
                    break;
                }
                int dhw = combo_hw(solution);
                local_delta_hw += dhw;
                local_delta_count++;
                msg_apply_combo(words, solution);
                if (dhw < local_best_delta_hw || local_best_delta_hw == 0) {
                    local_best_delta_hw = dhw;
                }
            }
        }

        #pragma omp critical
        {
            rank_failures += local_rank_failures;
            exact_hits += local_exact_hits;
            total_delta_hw += local_delta_hw;
            delta_count += local_delta_count;
            if (local_min_rank < min_rank) min_rank = local_min_rank;
            if (msg61_better_prefix(&local_best, &best_ev, solve_prefix)) {
                best_ev = local_best;
                memcpy(best_words, local_best_words, sizeof(best_words));
                best_iter = local_best_iter;
                best_restart = local_best_restart;
                best_delta_hw = local_best_delta_hw;
            }
        }
    }

    printf("{\"mode\":\"msg61newton\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"restarts\":%d,\"max_iters\":%d,\"jitter_flips\":%d,"
           "\"threads\":%d,\"solve_prefix\":%d,\"exact_prefix_hits\":%d,"
           "\"rank_failures\":%d,"
           "\"min_rank\":%d,\"avg_delta_hw\":%.3f,\"best_restart\":%d,"
           "\"best_iter\":%d,\"best_min_delta_hw\":%d,\"best_prefix_hw\":%d,"
           "\"best_free_words\":",
           cand->id, idx, restarts, max_iters, jitter_flips, threads,
           solve_prefix, exact_hits, rank_failures, min_rank,
           delta_count ? (double)total_delta_hw / (double)delta_count : 0.0,
           best_restart, best_iter, best_delta_hw,
           msg61_prefix_hw(&best_ev, solve_prefix));
    msg61_print_words(best_words);
    printf(",");
    msg61_print_eval_fields(&best_ev);
    printf("}\n");
}

static void msg_flip_bit(uint32_t words[MSG_FREE_WORDS], int bit) {
    words[bit / 32] ^= 1U << (bit % 32);
}

static void msg61_guard_neigh_candidate(int idx, int max_k,
                                        const uint32_t *seed_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (max_k < 1) max_k = 1;
    if (max_k > 3) max_k = 3;

    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t base_words[MSG_FREE_WORDS];
    if (seed_words) {
        memcpy(base_words, seed_words, sizeof(base_words));
    } else {
        msg61_fill_words(cand, base_words);
    }

    msg61_eval_t base_ev, best_guard_ev, best_any_ev;
    uint32_t best_guard_words[MSG_FREE_WORDS], best_any_words[MSG_FREE_WORDS];
    msg61_eval_t best_changed_guard_ev;
    uint32_t best_changed_guard_words[MSG_FREE_WORDS];
    msg61_eval_candidate(cand, base_words, &base_ev);
    best_guard_ev = base_ev;
    best_any_ev = base_ev;
    best_changed_guard_ev = base_ev;
    memcpy(best_guard_words, base_words, sizeof(best_guard_words));
    memcpy(best_any_words, base_words, sizeof(best_any_words));
    memcpy(best_changed_guard_words, base_words, sizeof(best_changed_guard_words));
    int best_guard_valid = base_ev.a57_xor == 0;
    int best_changed_guard_valid = 0;

    unsigned long long checked = 0;
    unsigned long long guard_hits = base_ev.a57_xor == 0;
    unsigned long long slot57_hits = base_ev.prefix_zero >= 1;

    for (int i = 0; i < MSG_BITS; i++) {
        uint32_t words[MSG_FREE_WORDS];
        memcpy(words, base_words, sizeof(words));
        msg_flip_bit(words, i);
        msg61_eval_t ev;
        msg61_eval_candidate(cand, words, &ev);
        checked++;
        if (ev.a57_xor == 0) guard_hits++;
        if (ev.prefix_zero >= 1) slot57_hits++;
        if (msg61_better_prefix(&ev, &best_any_ev, 1)) {
            best_any_ev = ev;
            memcpy(best_any_words, words, sizeof(words));
        }
        if (ev.a57_xor == 0 &&
            (!best_guard_valid || msg61_better_prefix(&ev, &best_guard_ev, 1))) {
            best_guard_ev = ev;
            memcpy(best_guard_words, words, sizeof(words));
            best_guard_valid = 1;
        }
    }

    if (max_k >= 2) {
        for (int i = 0; i < MSG_BITS; i++) {
            for (int j = i + 1; j < MSG_BITS; j++) {
                uint32_t words[MSG_FREE_WORDS];
                memcpy(words, base_words, sizeof(words));
                msg_flip_bit(words, i);
                msg_flip_bit(words, j);
                msg61_eval_t ev;
                msg61_eval_candidate(cand, words, &ev);
                checked++;
                if (ev.a57_xor == 0) guard_hits++;
                if (ev.prefix_zero >= 1) slot57_hits++;
                if (msg61_better_prefix(&ev, &best_any_ev, 1)) {
                    best_any_ev = ev;
                    memcpy(best_any_words, words, sizeof(words));
                }
                if (ev.a57_xor == 0 &&
                    (!best_guard_valid || msg61_better_prefix(&ev, &best_guard_ev, 1))) {
                    best_guard_ev = ev;
                    memcpy(best_guard_words, words, sizeof(words));
                    best_guard_valid = 1;
                }
            }
        }
    }

    if (max_k >= 3) {
        for (int i = 0; i < MSG_BITS; i++) {
            for (int j = i + 1; j < MSG_BITS; j++) {
                for (int k = j + 1; k < MSG_BITS; k++) {
                    uint32_t words[MSG_FREE_WORDS];
                    memcpy(words, base_words, sizeof(words));
                    msg_flip_bit(words, i);
                    msg_flip_bit(words, j);
                    msg_flip_bit(words, k);
                    msg61_eval_t ev;
                    msg61_eval_candidate(cand, words, &ev);
                    checked++;
                    if (ev.a57_xor == 0) guard_hits++;
                    if (ev.prefix_zero >= 1) slot57_hits++;
                    if (msg61_better_prefix(&ev, &best_any_ev, 1)) {
                        best_any_ev = ev;
                        memcpy(best_any_words, words, sizeof(words));
                    }
                    if (ev.a57_xor == 0 &&
                        (!best_guard_valid || msg61_better_prefix(&ev, &best_guard_ev, 1))) {
                        best_guard_ev = ev;
                        memcpy(best_guard_words, words, sizeof(words));
                        best_guard_valid = 1;
                    }
                }
            }
        }
    }

    printf("{\"mode\":\"msg61guardneigh\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"max_k\":%d,\"seeded\":%d,\"checked\":%llu,"
           "\"guard_hits\":%llu,\"slot57_hits\":%llu,"
           "\"base_prefix_hw\":%d,\"best_any_prefix_hw\":%d,"
           "\"best_guard_valid\":%d,\"best_guard_prefix_hw\":%d,"
           "\"best_any_words\":",
           cand->id, idx, max_k, seed_words ? 1 : 0, checked,
           guard_hits, slot57_hits, msg61_prefix_hw(&base_ev, 1),
           msg61_prefix_hw(&best_any_ev, 1),
           best_guard_valid,
           msg61_prefix_hw(&best_guard_ev, 1));
    msg61_print_words(best_any_words);
    printf(",\"best_any\":{");
    msg61_print_eval_fields(&best_any_ev);
    printf("},\"best_guard_words\":");
    msg61_print_words(best_guard_words);
    printf(",\"best_guard\":{");
    msg61_print_eval_fields(&best_guard_ev);
    printf("}}\n");
}

static int solve32_msg_columns(const uint32_t cols[MSG_BITS], uint32_t target,
                               uint64_t solution[MSG_COMBO_WORDS],
                               int *rank_out) {
    uint32_t basis[32];
    uint64_t combo[32][MSG_COMBO_WORDS];
    memset(basis, 0, sizeof(basis));
    memset(combo, 0, sizeof(combo));
    int rank = 0;

    for (int i = 0; i < MSG_BITS; i++) {
        uint32_t v = cols[i];
        uint64_t c[MSG_COMBO_WORDS];
        memset(c, 0, sizeof(c));
        c[i / 64] = 1ULL << (i % 64);

        for (int b = 31; b >= 0 && v; b--) {
            if (((v >> b) & 1U) == 0) continue;
            if (basis[b]) {
                v ^= basis[b];
                for (int j = 0; j < MSG_COMBO_WORDS; j++) c[j] ^= combo[b][j];
            } else {
                basis[b] = v;
                memcpy(combo[b], c, sizeof(c));
                rank++;
                break;
            }
        }
    }

    memset(solution, 0, MSG_COMBO_WORDS * sizeof(uint64_t));
    uint32_t t = target;
    for (int b = 31; b >= 0 && t; b--) {
        if (((t >> b) & 1U) == 0) continue;
        if (!basis[b]) {
            if (rank_out) *rank_out = rank;
            return 0;
        }
        t ^= basis[b];
        for (int j = 0; j < MSG_COMBO_WORDS; j++) solution[j] ^= combo[b][j];
    }

    if (rank_out) *rank_out = rank;
    return 1;
}

static void msg61_build_a57_columns(const candidate_t *cand,
                                    const uint32_t words[MSG_FREE_WORDS],
                                    const msg61_eval_t *base_ev,
                                    uint32_t cols[MSG_BITS]) {
    for (int bit = 0; bit < MSG_BITS; bit++) {
        uint32_t next_words[MSG_FREE_WORDS];
        memcpy(next_words, words, sizeof(next_words));
        msg_flip_bit(next_words, bit);
        msg61_eval_t ev;
        msg61_eval_candidate(cand, next_words, &ev);
        cols[bit] = ev.a57_xor ^ base_ev->a57_xor;
    }
}

static void combo_xor_bit(uint64_t combo[MSG_COMBO_WORDS], int bit);
static uint32_t combo_column_effect32(const uint32_t cols[MSG_BITS],
                                      const uint64_t combo[MSG_COMBO_WORDS]);
static int solve_linear_columns(uint32_t target, const uint32_t *cols, int ncols,
                                uint64_t *solution, int *rank_out);

static void msg61_guard_repair_candidate(int idx, long long trials, int threads,
                                         int max_iters, int jitter_flips,
                                         int gauge_flips,
                                         const uint32_t *seed_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (trials < 1) trials = 1;
    if (threads < 1) threads = 1;
    if (threads > 64) threads = 64;
    if (max_iters < 1) max_iters = 1;
    if (jitter_flips < 0) jitter_flips = 0;
    if (jitter_flips > MSG_BITS) jitter_flips = MSG_BITS;
    if (gauge_flips < 0) gauge_flips = 0;
    if (gauge_flips > MSG_BITS) gauge_flips = MSG_BITS;

    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t base_words[MSG_FREE_WORDS];
    if (seed_words) {
        memcpy(base_words, seed_words, sizeof(base_words));
    } else {
        msg61_fill_words(cand, base_words);
    }

    msg61_eval_t best_guard_ev, best_any_ev;
    uint32_t best_guard_words[MSG_FREE_WORDS], best_any_words[MSG_FREE_WORDS];
    msg61_eval_t best_changed_guard_ev;
    uint32_t best_changed_guard_words[MSG_FREE_WORDS];
    msg61_eval_candidate(cand, base_words, &best_guard_ev);
    best_any_ev = best_guard_ev;
    best_changed_guard_ev = best_guard_ev;
    memcpy(best_guard_words, base_words, sizeof(best_guard_words));
    memcpy(best_any_words, base_words, sizeof(best_any_words));
    memcpy(best_changed_guard_words, base_words, sizeof(best_changed_guard_words));
    int best_guard_valid = best_guard_ev.a57_xor == 0;
    int best_changed_guard_valid = 0;

    long long guard_hits = 0;
    long long exact_slot57 = 0;
    long long rank_failures = 0;
    long long changed_guard_hits = 0;
    long long total_delta_hw = 0;
    long long delta_count = 0;
    int min_rank = 999;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x579a57a57ULL ^ (uint64_t)idx * 0x9e3779b97f4a7c15ULL ^
                       (uint64_t)tid * 0xd1b54a32d192ed03ULL;
        msg61_eval_t local_best_guard, local_best_any;
        msg61_eval_t local_best_changed_guard;
        uint32_t local_guard_words[MSG_FREE_WORDS], local_any_words[MSG_FREE_WORDS];
        uint32_t local_changed_guard_words[MSG_FREE_WORDS];
        msg61_eval_candidate(cand, base_words, &local_best_guard);
        local_best_any = local_best_guard;
        local_best_changed_guard = local_best_guard;
        memcpy(local_guard_words, base_words, sizeof(local_guard_words));
        memcpy(local_any_words, base_words, sizeof(local_any_words));
        memcpy(local_changed_guard_words, base_words, sizeof(local_changed_guard_words));
        int local_guard_valid = local_best_guard.a57_xor == 0;
        int local_changed_guard_valid = 0;
        long long local_guard_hits = 0;
        long long local_exact_slot57 = 0;
        long long local_rank_failures = 0;
        long long local_changed_guard_hits = 0;
        long long local_delta_hw = 0;
        long long local_delta_count = 0;
        int local_min_rank = 999;

        #pragma omp for schedule(dynamic, 128)
        for (long long t = 0; t < trials; t++) {
            uint32_t words[MSG_FREE_WORDS];
            memcpy(words, base_words, sizeof(words));
            int flips = jitter_flips ? 1 + (int)(splitmix32(&rng) % (uint32_t)jitter_flips) : 0;
            for (int k = 0; k < flips; k++) {
                int bit = (int)(splitmix32(&rng) % (uint32_t)MSG_BITS);
                msg_flip_bit(words, bit);
            }

            msg61_eval_t start_ev;
            msg61_eval_candidate(cand, words, &start_ev);
            msg61_eval_t cur = start_ev;
            for (int iter = 0; iter < max_iters && cur.a57_xor != 0; iter++) {
                uint32_t cols[MSG_BITS];
                uint64_t gauge[MSG_COMBO_WORDS], repair[MSG_COMBO_WORDS];
                uint64_t combo[MSG_COMBO_WORDS];
                int rank = 0;
                msg61_build_a57_columns(cand, words, &cur, cols);
                memset(gauge, 0, sizeof(gauge));
                if (gauge_flips > 0) {
                    int gflips = 1 + (int)(splitmix32(&rng) % (uint32_t)gauge_flips);
                    for (int k = 0; k < gflips; k++) {
                        int bit = (int)(splitmix32(&rng) % (uint32_t)MSG_BITS);
                        combo_xor_bit(gauge, bit);
                    }
                }
                uint32_t target = cur.a57_xor ^ combo_column_effect32(cols, gauge);
                int ok = solve32_msg_columns(cols, target, repair, &rank);
                if (rank < local_min_rank) local_min_rank = rank;
                if (!ok) {
                    local_rank_failures++;
                    break;
                }
                for (int j = 0; j < MSG_COMBO_WORDS; j++) combo[j] = gauge[j] ^ repair[j];
                int dhw = combo_hw(combo);
                local_delta_hw += dhw;
                local_delta_count++;
                msg_apply_combo(words, combo);
                msg61_eval_candidate(cand, words, &cur);
            }

            if (msg61_better_prefix(&cur, &local_best_any, 1)) {
                local_best_any = cur;
                memcpy(local_any_words, words, sizeof(local_any_words));
            }
            if (cur.a57_xor == 0) {
                local_guard_hits++;
                int changed = !msg61_words_equal(words, base_words);
                if (changed) local_changed_guard_hits++;
                if (cur.prefix_zero >= 1) local_exact_slot57++;
                if (!local_guard_valid ||
                    msg61_better_prefix(&cur, &local_best_guard, 1)) {
                    local_best_guard = cur;
                    memcpy(local_guard_words, words, sizeof(local_guard_words));
                    local_guard_valid = 1;
                }
                if (changed && (!local_changed_guard_valid ||
                    msg61_better_prefix(&cur, &local_best_changed_guard, 1))) {
                    local_best_changed_guard = cur;
                    memcpy(local_changed_guard_words, words, sizeof(local_changed_guard_words));
                    local_changed_guard_valid = 1;
                }
            }
        }

        #pragma omp critical
        {
            guard_hits += local_guard_hits;
            exact_slot57 += local_exact_slot57;
            rank_failures += local_rank_failures;
            changed_guard_hits += local_changed_guard_hits;
            total_delta_hw += local_delta_hw;
            delta_count += local_delta_count;
            if (local_min_rank < min_rank) min_rank = local_min_rank;
            if (msg61_better_prefix(&local_best_any, &best_any_ev, 1)) {
                best_any_ev = local_best_any;
                memcpy(best_any_words, local_any_words, sizeof(best_any_words));
            }
            if (local_guard_valid &&
                (!best_guard_valid ||
                 msg61_better_prefix(&local_best_guard, &best_guard_ev, 1))) {
                best_guard_ev = local_best_guard;
                memcpy(best_guard_words, local_guard_words, sizeof(best_guard_words));
                best_guard_valid = 1;
            }
            if (local_changed_guard_valid &&
                (!best_changed_guard_valid ||
                 msg61_better_prefix(&local_best_changed_guard,
                                     &best_changed_guard_ev, 1))) {
                best_changed_guard_ev = local_best_changed_guard;
                memcpy(best_changed_guard_words, local_changed_guard_words,
                       sizeof(best_changed_guard_words));
                best_changed_guard_valid = 1;
            }
        }
    }

    printf("{\"mode\":\"msg61guardrepair\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"trials\":%lld,\"threads\":%d,\"max_iters\":%d,"
           "\"jitter_flips\":%d,\"gauge_flips\":%d,"
           "\"seeded\":%d,\"guard_hits\":%lld,"
           "\"changed_guard_hits\":%lld,\"exact_slot57\":%lld,"
           "\"rank_failures\":%lld,\"min_rank\":%d,"
           "\"avg_delta_hw\":%.3f,\"best_any_prefix_hw\":%d,"
           "\"best_guard_valid\":%d,\"best_guard_prefix_hw\":%d,"
           "\"best_changed_guard_valid\":%d,"
           "\"best_changed_guard_prefix_hw\":%d,\"best_any_words\":",
           cand->id, idx, trials, threads, max_iters, jitter_flips, gauge_flips,
           seed_words ? 1 : 0, guard_hits, changed_guard_hits, exact_slot57,
           rank_failures, min_rank,
           delta_count ? (double)total_delta_hw / (double)delta_count : 0.0,
           msg61_prefix_hw(&best_any_ev, 1), best_guard_valid,
           msg61_prefix_hw(&best_guard_ev, 1), best_changed_guard_valid,
           msg61_prefix_hw(&best_changed_guard_ev, 1));
    msg61_print_words(best_any_words);
    printf(",\"best_any\":{");
    msg61_print_eval_fields(&best_any_ev);
    printf("},\"best_guard_words\":");
    msg61_print_words(best_guard_words);
    printf(",\"best_guard\":{");
    msg61_print_eval_fields(&best_guard_ev);
    printf("},\"best_changed_guard_words\":");
    msg61_print_words(best_changed_guard_words);
    printf(",\"best_changed_guard\":{");
    msg61_print_eval_fields(&best_changed_guard_ev);
    printf("}}\n");
}

static void combo_xor_bit(uint64_t combo[MSG_COMBO_WORDS], int bit) {
    combo[bit / 64] ^= 1ULL << (bit % 64);
}

static uint32_t combo_column_effect32(const uint32_t cols[MSG_BITS],
                                      const uint64_t combo[MSG_COMBO_WORDS]) {
    uint32_t out = 0;
    for (int bit = 0; bit < MSG_BITS; bit++) {
        if ((combo[bit / 64] >> (bit % 64)) & 1ULL) out ^= cols[bit];
    }
    return out;
}

static void msg61_guard_kernel_candidate(int idx, long long trials, int threads,
                                         int drive_flips,
                                         const uint32_t *seed_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (trials < 1) trials = 1;
    if (threads < 1) threads = 1;
    if (threads > 64) threads = 64;
    if (drive_flips < 1) drive_flips = 1;
    if (drive_flips > MSG_BITS) drive_flips = MSG_BITS;

    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t base_words[MSG_FREE_WORDS];
    if (seed_words) {
        memcpy(base_words, seed_words, sizeof(base_words));
    } else {
        msg61_fill_words(cand, base_words);
    }

    msg61_eval_t base_ev, best_guard_ev, best_any_ev;
    msg61_eval_t best_changed_guard_ev;
    uint32_t best_guard_words[MSG_FREE_WORDS], best_any_words[MSG_FREE_WORDS];
    uint32_t best_changed_guard_words[MSG_FREE_WORDS];
    msg61_eval_candidate(cand, base_words, &base_ev);
    best_guard_ev = base_ev;
    best_any_ev = base_ev;
    best_changed_guard_ev = base_ev;
    memcpy(best_guard_words, base_words, sizeof(best_guard_words));
    memcpy(best_any_words, base_words, sizeof(best_any_words));
    memcpy(best_changed_guard_words, base_words, sizeof(best_changed_guard_words));
    int best_guard_valid = base_ev.a57_xor == 0;
    int best_changed_guard_valid = 0;

    uint32_t cols[MSG_BITS];
    msg61_build_a57_columns(cand, base_words, &base_ev, cols);
    uint64_t zero_sol[MSG_COMBO_WORDS];
    int base_rank = 0;
    solve32_msg_columns(cols, 0, zero_sol, &base_rank);

    long long exact_guard = 0;
    long long exact_slot57 = 0;
    long long changed_guard_hits = 0;
    long long zero_combo = 0;
    long long total_combo_hw = 0;
    long long combo_count = 0;
    int best_combo_hw = 0;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xa57c0deULL ^ (uint64_t)idx * 0x9e3779b97f4a7c15ULL ^
                       (uint64_t)tid * 0xd1b54a32d192ed03ULL;
        msg61_eval_t local_best_guard = base_ev;
        msg61_eval_t local_best_any = base_ev;
        msg61_eval_t local_best_changed_guard = base_ev;
        uint32_t local_guard_words[MSG_FREE_WORDS], local_any_words[MSG_FREE_WORDS];
        uint32_t local_changed_guard_words[MSG_FREE_WORDS];
        memcpy(local_guard_words, base_words, sizeof(local_guard_words));
        memcpy(local_any_words, base_words, sizeof(local_any_words));
        memcpy(local_changed_guard_words, base_words, sizeof(local_changed_guard_words));
        int local_guard_valid = best_guard_valid;
        int local_changed_guard_valid = 0;
        long long local_exact_guard = 0;
        long long local_exact_slot57 = 0;
        long long local_changed_guard_hits = 0;
        long long local_zero_combo = 0;
        long long local_total_combo_hw = 0;
        long long local_combo_count = 0;
        int local_best_combo_hw = 0;

        #pragma omp for schedule(dynamic, 256)
        for (long long t = 0; t < trials; t++) {
            uint64_t drive[MSG_COMBO_WORDS];
            memset(drive, 0, sizeof(drive));
            int flips = 1 + (int)(splitmix32(&rng) % (uint32_t)drive_flips);
            for (int k = 0; k < flips; k++) {
                int bit = (int)(splitmix32(&rng) % (uint32_t)MSG_BITS);
                combo_xor_bit(drive, bit);
            }

            uint32_t effect = combo_column_effect32(cols, drive);
            uint64_t repair[MSG_COMBO_WORDS], combo[MSG_COMBO_WORDS];
            int rank = 0;
            if (!solve32_msg_columns(cols, effect, repair, &rank)) continue;
            for (int i = 0; i < MSG_COMBO_WORDS; i++) combo[i] = drive[i] ^ repair[i];

            int chw = combo_hw(combo);
            if (chw == 0) {
                local_zero_combo++;
                continue;
            }
            local_total_combo_hw += chw;
            local_combo_count++;
            if (local_best_combo_hw == 0 || chw < local_best_combo_hw) {
                local_best_combo_hw = chw;
            }

            uint32_t words[MSG_FREE_WORDS];
            memcpy(words, base_words, sizeof(words));
            msg_apply_combo(words, combo);
            msg61_eval_t ev;
            msg61_eval_candidate(cand, words, &ev);

            if (msg61_better_prefix(&ev, &local_best_any, 1)) {
                local_best_any = ev;
                memcpy(local_any_words, words, sizeof(local_any_words));
            }
            if (ev.a57_xor == 0) {
                local_exact_guard++;
                if (ev.prefix_zero >= 1) local_exact_slot57++;
                int changed = !msg61_words_equal(words, base_words);
                if (changed) local_changed_guard_hits++;
                if (!local_guard_valid ||
                    msg61_better_prefix(&ev, &local_best_guard, 1)) {
                    local_best_guard = ev;
                    memcpy(local_guard_words, words, sizeof(local_guard_words));
                    local_guard_valid = 1;
                }
                if (changed && (!local_changed_guard_valid ||
                    msg61_better_prefix(&ev, &local_best_changed_guard, 1))) {
                    local_best_changed_guard = ev;
                    memcpy(local_changed_guard_words, words, sizeof(local_changed_guard_words));
                    local_changed_guard_valid = 1;
                }
            }
        }

        #pragma omp critical
        {
            exact_guard += local_exact_guard;
            exact_slot57 += local_exact_slot57;
            changed_guard_hits += local_changed_guard_hits;
            zero_combo += local_zero_combo;
            total_combo_hw += local_total_combo_hw;
            combo_count += local_combo_count;
            if (local_best_combo_hw &&
                (best_combo_hw == 0 || local_best_combo_hw < best_combo_hw)) {
                best_combo_hw = local_best_combo_hw;
            }
            if (msg61_better_prefix(&local_best_any, &best_any_ev, 1)) {
                best_any_ev = local_best_any;
                memcpy(best_any_words, local_any_words, sizeof(best_any_words));
            }
            if (local_guard_valid &&
                (!best_guard_valid ||
                 msg61_better_prefix(&local_best_guard, &best_guard_ev, 1))) {
                best_guard_ev = local_best_guard;
                memcpy(best_guard_words, local_guard_words, sizeof(best_guard_words));
                best_guard_valid = 1;
            }
            if (local_changed_guard_valid &&
                (!best_changed_guard_valid ||
                 msg61_better_prefix(&local_best_changed_guard,
                                     &best_changed_guard_ev, 1))) {
                best_changed_guard_ev = local_best_changed_guard;
                memcpy(best_changed_guard_words, local_changed_guard_words,
                       sizeof(best_changed_guard_words));
                best_changed_guard_valid = 1;
            }
        }
    }

    printf("{\"mode\":\"msg61guardkernel\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"trials\":%lld,\"threads\":%d,\"drive_flips\":%d,"
           "\"seeded\":%d,\"base_rank\":%d,\"exact_guard\":%lld,"
           "\"changed_guard_hits\":%lld,\"exact_slot57\":%lld,"
           "\"zero_combo\":%lld,\"avg_combo_hw\":%.3f,"
           "\"best_combo_hw\":%d,\"best_any_prefix_hw\":%d,"
           "\"best_guard_valid\":%d,\"best_guard_prefix_hw\":%d,"
           "\"best_changed_guard_valid\":%d,"
           "\"best_changed_guard_prefix_hw\":%d,\"best_any_words\":",
           cand->id, idx, trials, threads, drive_flips, seed_words ? 1 : 0,
           base_rank, exact_guard, changed_guard_hits, exact_slot57, zero_combo,
           combo_count ? (double)total_combo_hw / (double)combo_count : 0.0,
           best_combo_hw, msg61_prefix_hw(&best_any_ev, 1),
           best_guard_valid, msg61_prefix_hw(&best_guard_ev, 1),
           best_changed_guard_valid,
           msg61_prefix_hw(&best_changed_guard_ev, 1));
    msg61_print_words(best_any_words);
    printf(",\"best_any\":{");
    msg61_print_eval_fields(&best_any_ev);
    printf("},\"best_guard_words\":");
    msg61_print_words(best_guard_words);
    printf(",\"best_guard\":{");
    msg61_print_eval_fields(&best_guard_ev);
    printf("},\"best_changed_guard_words\":");
    msg61_print_words(best_changed_guard_words);
    printf(",\"best_changed_guard\":{");
    msg61_print_eval_fields(&best_changed_guard_ev);
    printf("}}\n");
}

static void msg61_build_a57_word_columns(const candidate_t *cand,
                                         const uint32_t words[MSG_FREE_WORDS],
                                         const msg61_eval_t *base_ev,
                                         int repair_word,
                                         uint32_t cols[32]) {
    for (int bit = 0; bit < 32; bit++) {
        uint32_t next_words[MSG_FREE_WORDS];
        memcpy(next_words, words, sizeof(next_words));
        next_words[repair_word] ^= 1U << bit;
        msg61_eval_t ev;
        msg61_eval_candidate(cand, next_words, &ev);
        cols[bit] = ev.a57_xor ^ base_ev->a57_xor;
    }
}

static void msg61_guard_word_repair_candidate(int idx, long long trials,
                                              int threads, int repair_word,
                                              int max_iters, int random_words,
                                              int jitter_flips,
                                              const uint32_t *seed_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (trials < 1) trials = 1;
    if (threads < 1) threads = 1;
    if (threads > 64) threads = 64;
    if (repair_word < 0) repair_word = 0;
    if (repair_word >= MSG_FREE_WORDS) repair_word = MSG_FREE_WORDS - 1;
    if (max_iters < 1) max_iters = 1;
    if (random_words < 0) random_words = 0;
    if (random_words > 1) random_words = 1;
    if (jitter_flips < 0) jitter_flips = 0;
    if (jitter_flips > MSG_BITS) jitter_flips = MSG_BITS;

    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t base_words[MSG_FREE_WORDS];
    if (seed_words) {
        memcpy(base_words, seed_words, sizeof(base_words));
    } else {
        msg61_fill_words(cand, base_words);
    }

    msg61_eval_t base_ev, best_any_ev, best_guard_ev, best_changed_guard_ev;
    uint32_t best_any_words[MSG_FREE_WORDS], best_guard_words[MSG_FREE_WORDS];
    uint32_t best_changed_guard_words[MSG_FREE_WORDS];
    msg61_eval_candidate(cand, base_words, &base_ev);
    best_any_ev = base_ev;
    best_guard_ev = base_ev;
    best_changed_guard_ev = base_ev;
    memcpy(best_any_words, base_words, sizeof(best_any_words));
    memcpy(best_guard_words, base_words, sizeof(best_guard_words));
    memcpy(best_changed_guard_words, base_words, sizeof(best_changed_guard_words));
    int best_guard_valid = base_ev.a57_xor == 0;
    int best_changed_guard_valid = 0;

    long long guard_hits = 0;
    long long changed_guard_hits = 0;
    long long exact_slot57 = 0;
    long long rank_failures = 0;
    long long zero_delta = 0;
    long long total_delta_hw = 0;
    long long delta_count = 0;
    int min_rank = 999;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x57a17eULL ^ (uint64_t)idx * 0x9e3779b97f4a7c15ULL ^
                       (uint64_t)repair_word * 0xbf58476d1ce4e5b9ULL ^
                       (uint64_t)tid * 0xd1b54a32d192ed03ULL;
        msg61_eval_t local_best_any = base_ev;
        msg61_eval_t local_best_guard = base_ev;
        msg61_eval_t local_best_changed_guard = base_ev;
        uint32_t local_any_words[MSG_FREE_WORDS], local_guard_words[MSG_FREE_WORDS];
        uint32_t local_changed_guard_words[MSG_FREE_WORDS];
        memcpy(local_any_words, base_words, sizeof(local_any_words));
        memcpy(local_guard_words, base_words, sizeof(local_guard_words));
        memcpy(local_changed_guard_words, base_words, sizeof(local_changed_guard_words));
        int local_guard_valid = best_guard_valid;
        int local_changed_guard_valid = 0;
        long long local_guard_hits = 0;
        long long local_changed_guard_hits = 0;
        long long local_exact_slot57 = 0;
        long long local_rank_failures = 0;
        long long local_zero_delta = 0;
        long long local_delta_hw = 0;
        long long local_delta_count = 0;
        int local_min_rank = 999;

        #pragma omp for schedule(dynamic, 64)
        for (long long t = 0; t < trials; t++) {
            uint32_t words[MSG_FREE_WORDS];
            memcpy(words, base_words, sizeof(words));
            if (random_words) {
                for (int i = 0; i < MSG_FREE_WORDS; i++) {
                    if (i != repair_word) words[i] = splitmix32(&rng);
                }
            } else {
                int flips = jitter_flips ? 1 + (int)(splitmix32(&rng) % (uint32_t)jitter_flips) : 0;
                for (int k = 0; k < flips; k++) {
                    int word = (int)(splitmix32(&rng) % (uint32_t)(MSG_FREE_WORDS - 1));
                    if (word >= repair_word) word++;
                    int bit = (int)(splitmix32(&rng) % 32U);
                    words[word] ^= 1U << bit;
                }
            }

            msg61_eval_t cur;
            msg61_eval_candidate(cand, words, &cur);
            for (int iter = 0; iter < max_iters && cur.a57_xor != 0; iter++) {
                uint32_t cols[32];
                uint64_t delta = 0;
                int rank = 0;
                msg61_build_a57_word_columns(cand, words, &cur, repair_word, cols);
                int ok = solve_linear_columns(cur.a57_xor, cols, 32, &delta, &rank);
                if (rank < local_min_rank) local_min_rank = rank;
                if (!ok) {
                    local_rank_failures++;
                    break;
                }
                if (((uint32_t)delta) == 0) {
                    local_zero_delta++;
                    break;
                }
                int dhw = hw32((uint32_t)delta);
                local_delta_hw += dhw;
                local_delta_count++;
                words[repair_word] ^= (uint32_t)delta;
                msg61_eval_candidate(cand, words, &cur);
            }

            if (msg61_better_prefix(&cur, &local_best_any, 1)) {
                local_best_any = cur;
                memcpy(local_any_words, words, sizeof(local_any_words));
            }
            if (cur.a57_xor == 0) {
                local_guard_hits++;
                int changed = !msg61_words_equal(words, base_words);
                if (changed) local_changed_guard_hits++;
                if (cur.prefix_zero >= 1) local_exact_slot57++;
                if (!local_guard_valid ||
                    msg61_better_prefix(&cur, &local_best_guard, 1)) {
                    local_best_guard = cur;
                    memcpy(local_guard_words, words, sizeof(local_guard_words));
                    local_guard_valid = 1;
                }
                if (changed && (!local_changed_guard_valid ||
                    msg61_better_prefix(&cur, &local_best_changed_guard, 1))) {
                    local_best_changed_guard = cur;
                    memcpy(local_changed_guard_words, words,
                           sizeof(local_changed_guard_words));
                    local_changed_guard_valid = 1;
                }
            }
        }

        #pragma omp critical
        {
            guard_hits += local_guard_hits;
            changed_guard_hits += local_changed_guard_hits;
            exact_slot57 += local_exact_slot57;
            rank_failures += local_rank_failures;
            zero_delta += local_zero_delta;
            total_delta_hw += local_delta_hw;
            delta_count += local_delta_count;
            if (local_min_rank < min_rank) min_rank = local_min_rank;
            if (msg61_better_prefix(&local_best_any, &best_any_ev, 1)) {
                best_any_ev = local_best_any;
                memcpy(best_any_words, local_any_words, sizeof(best_any_words));
            }
            if (local_guard_valid &&
                (!best_guard_valid ||
                 msg61_better_prefix(&local_best_guard, &best_guard_ev, 1))) {
                best_guard_ev = local_best_guard;
                memcpy(best_guard_words, local_guard_words, sizeof(best_guard_words));
                best_guard_valid = 1;
            }
            if (local_changed_guard_valid &&
                (!best_changed_guard_valid ||
                 msg61_better_prefix(&local_best_changed_guard,
                                     &best_changed_guard_ev, 1))) {
                best_changed_guard_ev = local_best_changed_guard;
                memcpy(best_changed_guard_words, local_changed_guard_words,
                       sizeof(best_changed_guard_words));
                best_changed_guard_valid = 1;
            }
        }
    }

    printf("{\"mode\":\"msg61guardwordrepair\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"trials\":%lld,\"threads\":%d,\"repair_word\":%d,"
           "\"message_word\":%d,\"max_iters\":%d,\"random_words\":%d,"
           "\"jitter_flips\":%d,\"seeded\":%d,\"guard_hits\":%lld,"
           "\"changed_guard_hits\":%lld,\"exact_slot57\":%lld,"
           "\"rank_failures\":%lld,\"zero_delta\":%lld,\"min_rank\":%d,"
           "\"avg_delta_hw\":%.3f,\"best_any_prefix_hw\":%d,"
           "\"best_guard_valid\":%d,\"best_guard_prefix_hw\":%d,"
           "\"best_changed_guard_valid\":%d,"
           "\"best_changed_guard_prefix_hw\":%d,\"best_any_words\":",
           cand->id, idx, trials, threads, repair_word, MSG_FREE_INDEX[repair_word],
           max_iters, random_words, jitter_flips, seed_words ? 1 : 0,
           guard_hits, changed_guard_hits, exact_slot57, rank_failures,
           zero_delta, min_rank,
           delta_count ? (double)total_delta_hw / (double)delta_count : 0.0,
           msg61_prefix_hw(&best_any_ev, 1), best_guard_valid,
           msg61_prefix_hw(&best_guard_ev, 1), best_changed_guard_valid,
           msg61_prefix_hw(&best_changed_guard_ev, 1));
    msg61_print_words(best_any_words);
    printf(",\"best_any\":{");
    msg61_print_eval_fields(&best_any_ev);
    printf("},\"best_guard_words\":");
    msg61_print_words(best_guard_words);
    printf(",\"best_guard\":{");
    msg61_print_eval_fields(&best_guard_ev);
    printf("},\"best_changed_guard_words\":");
    msg61_print_words(best_changed_guard_words);
    printf(",\"best_changed_guard\":{");
    msg61_print_eval_fields(&best_changed_guard_ev);
    printf("}}\n");
}

static int msg61_better_a57_step(const msg61_eval_t *a, const msg61_eval_t *b) {
    if (a->a57_hw != b->a57_hw) return a->a57_hw < b->a57_hw;
    return msg61_better_prefix(a, b, 1);
}

static void msg61_guard_chart_repair_candidate(int idx, long long trials,
                                               int threads, int max_iters,
                                               int random_words,
                                               int jitter_flips,
                                               const uint32_t *seed_words) {
    if (idx < 0 || idx >= (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]))) idx = 0;
    if (trials < 1) trials = 1;
    if (threads < 1) threads = 1;
    if (threads > 64) threads = 64;
    if (max_iters < 1) max_iters = 1;
    if (random_words < 0) random_words = 0;
    if (random_words > 1) random_words = 1;
    if (jitter_flips < 0) jitter_flips = 0;
    if (jitter_flips > MSG_BITS) jitter_flips = MSG_BITS;

    const candidate_t *cand = &CANDIDATES[idx];
    uint32_t base_words[MSG_FREE_WORDS];
    if (seed_words) {
        memcpy(base_words, seed_words, sizeof(base_words));
    } else {
        msg61_fill_words(cand, base_words);
    }

    msg61_eval_t base_ev, best_any_ev, best_guard_ev, best_changed_guard_ev;
    uint32_t best_any_words[MSG_FREE_WORDS], best_guard_words[MSG_FREE_WORDS];
    uint32_t best_changed_guard_words[MSG_FREE_WORDS];
    msg61_eval_candidate(cand, base_words, &base_ev);
    best_any_ev = base_ev;
    best_guard_ev = base_ev;
    best_changed_guard_ev = base_ev;
    memcpy(best_any_words, base_words, sizeof(best_any_words));
    memcpy(best_guard_words, base_words, sizeof(best_guard_words));
    memcpy(best_changed_guard_words, base_words, sizeof(best_changed_guard_words));
    int best_guard_valid = base_ev.a57_xor == 0;
    int best_changed_guard_valid = 0;

    long long guard_hits = 0;
    long long changed_guard_hits = 0;
    long long exact_slot57 = 0;
    long long no_chart = 0;
    long long tried_charts = 0;
    long long full_rank_charts = 0;
    long long total_delta_hw = 0;
    long long delta_count = 0;
    int min_rank = 999;

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0xc4a2757ULL ^ (uint64_t)idx * 0x9e3779b97f4a7c15ULL ^
                       (uint64_t)tid * 0xd1b54a32d192ed03ULL;
        msg61_eval_t local_best_any = base_ev;
        msg61_eval_t local_best_guard = base_ev;
        msg61_eval_t local_best_changed_guard = base_ev;
        uint32_t local_any_words[MSG_FREE_WORDS], local_guard_words[MSG_FREE_WORDS];
        uint32_t local_changed_guard_words[MSG_FREE_WORDS];
        memcpy(local_any_words, base_words, sizeof(local_any_words));
        memcpy(local_guard_words, base_words, sizeof(local_guard_words));
        memcpy(local_changed_guard_words, base_words, sizeof(local_changed_guard_words));
        int local_guard_valid = best_guard_valid;
        int local_changed_guard_valid = 0;
        long long local_guard_hits = 0;
        long long local_changed_guard_hits = 0;
        long long local_exact_slot57 = 0;
        long long local_no_chart = 0;
        long long local_tried_charts = 0;
        long long local_full_rank_charts = 0;
        long long local_delta_hw = 0;
        long long local_delta_count = 0;
        int local_min_rank = 999;

        #pragma omp for schedule(dynamic, 16)
        for (long long t = 0; t < trials; t++) {
            uint32_t words[MSG_FREE_WORDS];
            memcpy(words, base_words, sizeof(words));
            if (random_words) {
                for (int i = 0; i < MSG_FREE_WORDS; i++) words[i] = splitmix32(&rng);
            } else {
                int flips = jitter_flips ? 1 + (int)(splitmix32(&rng) % (uint32_t)jitter_flips) : 0;
                for (int k = 0; k < flips; k++) {
                    int bit = (int)(splitmix32(&rng) % (uint32_t)MSG_BITS);
                    msg_flip_bit(words, bit);
                }
            }

            msg61_eval_t cur;
            msg61_eval_candidate(cand, words, &cur);
            for (int iter = 0; iter < max_iters && cur.a57_xor != 0; iter++) {
                int found = 0;
                uint32_t best_delta = 0;
                msg61_eval_t step_best = cur;
                uint32_t step_words[MSG_FREE_WORDS];
                memcpy(step_words, words, sizeof(step_words));

                for (int wi = 0; wi < MSG_FREE_WORDS; wi++) {
                    uint32_t cols[32];
                    uint64_t delta = 0;
                    int rank = 0;
                    msg61_build_a57_word_columns(cand, words, &cur, wi, cols);
                    local_tried_charts++;
                    int ok = solve_linear_columns(cur.a57_xor, cols, 32, &delta, &rank);
                    if (rank < local_min_rank) local_min_rank = rank;
                    if (rank == 32) local_full_rank_charts++;
                    if (!ok || ((uint32_t)delta) == 0) continue;

                    uint32_t cand_words[MSG_FREE_WORDS];
                    memcpy(cand_words, words, sizeof(cand_words));
                    cand_words[wi] ^= (uint32_t)delta;
                    msg61_eval_t ev;
                    msg61_eval_candidate(cand, cand_words, &ev);
                    if (!found || msg61_better_a57_step(&ev, &step_best)) {
                        found = 1;
                        best_delta = (uint32_t)delta;
                        step_best = ev;
                        memcpy(step_words, cand_words, sizeof(step_words));
                    }
                }

                if (!found) {
                    local_no_chart++;
                    break;
                }
                local_delta_hw += hw32(best_delta);
                local_delta_count++;
                memcpy(words, step_words, sizeof(words));
                cur = step_best;
            }

            if (msg61_better_prefix(&cur, &local_best_any, 1)) {
                local_best_any = cur;
                memcpy(local_any_words, words, sizeof(local_any_words));
            }
            if (cur.a57_xor == 0) {
                local_guard_hits++;
                int changed = !msg61_words_equal(words, base_words);
                if (changed) local_changed_guard_hits++;
                if (cur.prefix_zero >= 1) local_exact_slot57++;
                if (!local_guard_valid ||
                    msg61_better_prefix(&cur, &local_best_guard, 1)) {
                    local_best_guard = cur;
                    memcpy(local_guard_words, words, sizeof(local_guard_words));
                    local_guard_valid = 1;
                }
                if (changed && (!local_changed_guard_valid ||
                    msg61_better_prefix(&cur, &local_best_changed_guard, 1))) {
                    local_best_changed_guard = cur;
                    memcpy(local_changed_guard_words, words,
                           sizeof(local_changed_guard_words));
                    local_changed_guard_valid = 1;
                }
            }
        }

        #pragma omp critical
        {
            guard_hits += local_guard_hits;
            changed_guard_hits += local_changed_guard_hits;
            exact_slot57 += local_exact_slot57;
            no_chart += local_no_chart;
            tried_charts += local_tried_charts;
            full_rank_charts += local_full_rank_charts;
            total_delta_hw += local_delta_hw;
            delta_count += local_delta_count;
            if (local_min_rank < min_rank) min_rank = local_min_rank;
            if (msg61_better_prefix(&local_best_any, &best_any_ev, 1)) {
                best_any_ev = local_best_any;
                memcpy(best_any_words, local_any_words, sizeof(best_any_words));
            }
            if (local_guard_valid &&
                (!best_guard_valid ||
                 msg61_better_prefix(&local_best_guard, &best_guard_ev, 1))) {
                best_guard_ev = local_best_guard;
                memcpy(best_guard_words, local_guard_words, sizeof(best_guard_words));
                best_guard_valid = 1;
            }
            if (local_changed_guard_valid &&
                (!best_changed_guard_valid ||
                 msg61_better_prefix(&local_best_changed_guard,
                                     &best_changed_guard_ev, 1))) {
                best_changed_guard_ev = local_best_changed_guard;
                memcpy(best_changed_guard_words, local_changed_guard_words,
                       sizeof(best_changed_guard_words));
                best_changed_guard_valid = 1;
            }
        }
    }

    printf("{\"mode\":\"msg61guardchartrepair\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"trials\":%lld,\"threads\":%d,\"max_iters\":%d,"
           "\"random_words\":%d,\"jitter_flips\":%d,\"seeded\":%d,"
           "\"guard_hits\":%lld,\"changed_guard_hits\":%lld,"
           "\"exact_slot57\":%lld,\"no_chart\":%lld,"
           "\"tried_charts\":%lld,\"full_rank_charts\":%lld,"
           "\"full_rank_rate\":%.6f,\"min_rank\":%d,"
           "\"avg_delta_hw\":%.3f,\"best_any_prefix_hw\":%d,"
           "\"best_guard_valid\":%d,\"best_guard_prefix_hw\":%d,"
           "\"best_changed_guard_valid\":%d,"
           "\"best_changed_guard_prefix_hw\":%d,\"best_any_words\":",
           cand->id, idx, trials, threads, max_iters, random_words,
           jitter_flips, seed_words ? 1 : 0, guard_hits, changed_guard_hits,
           exact_slot57, no_chart, tried_charts, full_rank_charts,
           tried_charts ? (double)full_rank_charts / (double)tried_charts : 0.0,
           min_rank,
           delta_count ? (double)total_delta_hw / (double)delta_count : 0.0,
           msg61_prefix_hw(&best_any_ev, 1), best_guard_valid,
           msg61_prefix_hw(&best_guard_ev, 1), best_changed_guard_valid,
           msg61_prefix_hw(&best_changed_guard_ev, 1));
    msg61_print_words(best_any_words);
    printf(",\"best_any\":{");
    msg61_print_eval_fields(&best_any_ev);
    printf("},\"best_guard_words\":");
    msg61_print_words(best_guard_words);
    printf(",\"best_guard\":{");
    msg61_print_eval_fields(&best_guard_ev);
    printf("},\"best_changed_guard_words\":");
    msg61_print_words(best_changed_guard_words);
    printf(",\"best_changed_guard\":{");
    msg61_print_eval_fields(&best_changed_guard_ev);
    printf("}}\n");
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

static int kernel_basis_columns64(const uint64_t *cols, int ncols,
                                  uint64_t *kernel, int *rank_out) {
    uint64_t basis[64];
    uint64_t combo[64];
    memset(basis, 0, sizeof(basis));
    memset(combo, 0, sizeof(combo));
    int rank = 0;
    int kernel_dim = 0;

    for (int i = 0; i < ncols; i++) {
        uint64_t v = cols[i];
        uint64_t c = 1ULL << i;
        int inserted = 0;
        for (int b = 63; b >= 0 && v; b--) {
            if (((v >> b) & 1ULL) == 0) continue;
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

typedef struct {
    uint64_t lo;
    uint32_t hi;
} delta96_t;

static inline delta96_t delta96_zero(void) {
    delta96_t z = {0, 0};
    return z;
}

static inline delta96_t delta96_bit(int bit) {
    delta96_t z = {0, 0};
    if (bit < 64) z.lo = 1ULL << bit;
    else z.hi = 1U << (bit - 64);
    return z;
}

static inline delta96_t delta96_xor(delta96_t a, delta96_t b) {
    delta96_t z = {a.lo ^ b.lo, a.hi ^ b.hi};
    return z;
}

static inline int delta96_hw(delta96_t d) {
    return __builtin_popcountll(d.lo) + hw32(d.hi);
}

static delta96_t combine_kernel_selection96(uint64_t selection,
                                            const delta96_t *kernel_basis) {
    delta96_t out = delta96_zero();
    while (selection) {
        int bit = __builtin_ctzll(selection);
        out = delta96_xor(out, kernel_basis[bit]);
        selection &= selection - 1;
    }
    return out;
}

static int solve_linear_columns96(uint32_t target, const uint32_t *cols,
                                  int ncols, delta96_t *solution,
                                  int *rank_out) {
    uint32_t basis[32];
    delta96_t combo[32];
    memset(basis, 0, sizeof(basis));
    for (int i = 0; i < 32; i++) combo[i] = delta96_zero();
    int rank = 0;

    for (int i = 0; i < ncols; i++) {
        uint32_t v = cols[i];
        delta96_t c = delta96_bit(i);
        for (int b = 31; b >= 0 && v; b--) {
            if (((v >> b) & 1U) == 0) continue;
            if (basis[b]) {
                v ^= basis[b];
                c = delta96_xor(c, combo[b]);
            } else {
                basis[b] = v;
                combo[b] = c;
                rank++;
                break;
            }
        }
    }

    uint32_t t = target;
    delta96_t sol = delta96_zero();
    for (int b = 31; b >= 0 && t; b--) {
        if (((t >> b) & 1U) == 0) continue;
        if (!basis[b]) {
            if (rank_out) *rank_out = rank;
            return 0;
        }
        t ^= basis[b];
        sol = delta96_xor(sol, combo[b]);
    }

    if (rank_out) *rank_out = rank;
    *solution = sol;
    return 1;
}

static int kernel_basis_columns32_96(const uint32_t *cols, int ncols,
                                     delta96_t *kernel, int *rank_out) {
    uint32_t basis[32];
    delta96_t combo[32];
    memset(basis, 0, sizeof(basis));
    for (int i = 0; i < 32; i++) combo[i] = delta96_zero();
    int rank = 0;
    int kernel_dim = 0;

    for (int i = 0; i < ncols; i++) {
        uint32_t v = cols[i];
        delta96_t c = delta96_bit(i);
        int inserted = 0;
        for (int b = 31; b >= 0 && v; b--) {
            if (((v >> b) & 1U) == 0) continue;
            if (basis[b]) {
                v ^= basis[b];
                c = delta96_xor(c, combo[b]);
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

static void apply_delta57_59(const uint32_t in[3], delta96_t delta,
                             uint32_t out[3]) {
    out[0] = in[0] ^ (uint32_t)(delta.lo & 0xffffffffULL);
    out[1] = in[1] ^ (uint32_t)(delta.lo >> 32);
    out[2] = in[2] ^ delta.hi;
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
        for (long long i = 0; i < samples; i++) {
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

static void off58_neighborhood_candidate(int idx, uint32_t base_w57, int max_k) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_k < 0) max_k = 0;
    if (max_k > 8) max_k = 8;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"off58neighbors\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint64_t checked = 0;
    int hist[33];
    uint32_t best_w57_by_hw[33];
    uint32_t best_off58_by_hw[33];
    uint32_t best_w57 = base_w57;
    uint32_t best_off58 = compute_off58_for_w57(&p1, &p2, base_w57);
    int best_hw = hw32(best_off58);
    memset(hist, 0, sizeof(hist));
    memset(best_w57_by_hw, 0, sizeof(best_w57_by_hw));
    memset(best_off58_by_hw, 0, sizeof(best_off58_by_hw));
    for (int h = 0; h <= 32; h++) best_off58_by_hw[h] = 0xffffffffU;

    for (int k = 0; k <= max_k; k++) {
        uint64_t combo = (k == 0) ? 0ULL : ((1ULL << k) - 1ULL);
        while (1) {
            uint32_t w57 = base_w57 ^ (uint32_t)combo;
            uint32_t off58 = compute_off58_for_w57(&p1, &p2, w57);
            int h = hw32(off58);
            checked++;
            hist[h]++;
            if (h < best_hw || (h == best_hw && off58 < best_off58)) {
                best_hw = h;
                best_off58 = off58;
                best_w57 = w57;
            }
            if (off58 < best_off58_by_hw[h]) {
                best_off58_by_hw[h] = off58;
                best_w57_by_hw[h] = w57;
            }

            if (k == 0) break;
            uint64_t next = next_combination64(combo);
            if (!next || next < combo || next >= (1ULL << 32)) break;
            combo = next;
        }
    }

    printf("{\"mode\":\"off58neighbors\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_w57\":\"0x%08x\",\"base_off58\":\"0x%08x\","
           "\"base_off58_hw\":%d,\"max_k\":%d,\"checked\":%llu,"
           "\"best_w57\":\"0x%08x\",\"best_off58\":\"0x%08x\","
           "\"best_hw\":%d,\"hist\":[",
           cand->id, idx, base_w57,
           compute_off58_for_w57(&p1, &p2, base_w57),
           hw32(compute_off58_for_w57(&p1, &p2, base_w57)),
           max_k, (unsigned long long)checked,
           best_w57, best_off58, best_hw);
    for (int h = 0; h <= 32; h++) {
        if (h) printf(",");
        printf("%d", hist[h]);
    }
    printf("],\"best_by_hw\":[");
    int printed = 0;
    for (int h = 0; h <= 8; h++) {
        if (best_off58_by_hw[h] == 0xffffffffU) continue;
        if (printed++) printf(",");
        printf("{\"hw\":%d,\"w57\":\"0x%08x\",\"off58\":\"0x%08x\"}",
               h, best_w57_by_hw[h], best_off58_by_hw[h]);
    }
    printf("]}\n");
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

static void defect60_61_columns96(const sha256_precomp_t *p1,
                                  const sha256_precomp_t *p2,
                                  const uint32_t x[3], uint32_t *d60_out,
                                  uint32_t *d61_out, uint32_t cols60[96],
                                  uint32_t cols61[96], uint64_t cols_pair[96]) {
    uint64_t base = defect60_61_vec(p1, p2, x);
    if (d60_out) *d60_out = (uint32_t)base;
    if (d61_out) *d61_out = (uint32_t)(base >> 32);

    for (int bit = 0; bit < 96; bit++) {
        uint32_t xf[3] = {x[0], x[1], x[2]};
        if (bit < 32) xf[0] ^= 1U << bit;
        else if (bit < 64) xf[1] ^= 1U << (bit - 32);
        else xf[2] ^= 1U << (bit - 64);
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
    if (max_k > 7) max_k = 7;

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
    if (max_k > 7) max_k = 7;

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
                                            int max_passes, int max_flips,
                                            int free_w57) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 64) max_flips = 64;
    int move_bits = free_w57 ? 96 : 64;

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
                int bit = (int)(splitmix32(&rng) % (uint32_t)move_bits);
                if (free_w57 && bit < 32) x[0] ^= 1U << bit;
                else if (free_w57 && bit < 64) x[1] ^= 1U << (bit - 32);
                else if (free_w57) x[2] ^= 1U << (bit - 64);
                else if (bit < 32) x[1] ^= 1U << bit;
                else x[2] ^= 1U << (bit - 32);
            }

            eval_t cur = eval_defect(&p1, &p2, x);
            int passes_used = 0;
            for (int pass = 0; pass < max_passes && cur.defect != 0; pass++) {
                uint32_t best_step_x[3] = {x[0], x[1], x[2]};
                eval_t best_step = cur;

                for (int bit = 0; bit < move_bits; bit++) {
                    uint32_t xf[3] = {x[0], x[1], x[2]};
                    if (free_w57 && bit < 32) xf[0] ^= 1U << bit;
                    else if (free_w57 && bit < 64) xf[1] ^= 1U << (bit - 32);
                    else if (free_w57) xf[2] ^= 1U << (bit - 64);
                    else if (bit < 32) xf[1] ^= 1U << bit;
                    else xf[2] ^= 1U << (bit - 32);
                    eval_t y = eval_defect(&p1, &p2, xf);
                    if (y.defect_hw < best_step.defect_hw ||
                        (y.defect_hw == best_step.defect_hw &&
                         y.defect < best_step.defect)) {
                        best_step = y;
                        best_step_x[0] = xf[0];
                        best_step_x[1] = xf[1];
                        best_step_x[2] = xf[2];
                    }
                }

                if (best_step.defect_hw >= cur.defect_hw) break;
                x[0] = best_step_x[0];
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
            int exact_distance = hw32(x[0] ^ base_x[0]) +
                                 hw32(x[1] ^ base_x[1]) +
                                 hw32(x[2] ^ base_x[2]);
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
           "\"free_w57\":%d,"
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
           trials, max_passes, max_flips, free_w57,
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

typedef struct {
    uint32_t defects[7];
    int d60_hw;
    int d61_hw;
    int d62_hw;
    int d63_hw;
    int tail_defect_hw;
    int tail_hw;
} frontier61_eval_t;

typedef struct {
    int used;
    uint32_t x[3];
    uint32_t defects[7];
    int d61_hw;
    int tail_defect_hw;
    int tail_hw;
    int distance;
    int passes;
    int source_seed;
    int policy;
} frontier61_entry_t;

static void frontier61_eval_point(const sha256_precomp_t *p1,
                                  const sha256_precomp_t *p2,
                                  const uint32_t x[3],
                                  int want_tail_hw,
                                  frontier61_eval_t *out) {
    tail_defects_for_x(p1, p2, x, out->defects);
    out->d60_hw = hw32(out->defects[3]);
    out->d61_hw = hw32(out->defects[4]);
    out->d62_hw = hw32(out->defects[5]);
    out->d63_hw = hw32(out->defects[6]);
    out->tail_defect_hw = out->d61_hw + out->d62_hw + out->d63_hw;
    out->tail_hw = 999;
    if (want_tail_hw && out->defects[3] == 0) {
        tail_trace_t trace;
        tail_trace_for_x(p1, p2, x, &trace);
        out->tail_hw = sha256_eval_tail(p1, p2, trace.w1, trace.w2);
    }
}

static int frontier61_side_score(const frontier61_eval_t *e, int policy) {
    switch (policy & 3) {
        case 0:
            return e->defects[3] ? (e->defects[3] & 0x7fffffff) : 0;
        case 1:
            return e->d61_hw * 128 + e->d62_hw * 4 + e->d63_hw;
        case 2:
            return e->tail_defect_hw * 8 + e->d61_hw;
        default:
            return e->d61_hw * 64 + e->tail_defect_hw * 3;
    }
}

static int frontier61_eval_better(const frontier61_eval_t *a,
                                  const frontier61_eval_t *b,
                                  int policy) {
    if (a->d60_hw != b->d60_hw) return a->d60_hw < b->d60_hw;
    int as = frontier61_side_score(a, policy);
    int bs = frontier61_side_score(b, policy);
    if (as != bs) return as < bs;
    if (a->d61_hw != b->d61_hw) return a->d61_hw < b->d61_hw;
    if (a->tail_defect_hw != b->tail_defect_hw) {
        return a->tail_defect_hw < b->tail_defect_hw;
    }
    if (a->defects[3] != b->defects[3]) return a->defects[3] < b->defects[3];
    if (a->defects[4] != b->defects[4]) return a->defects[4] < b->defects[4];
    return 0;
}

static int frontier61_min_seed_distance(const uint32_t *seeds, int seed_count,
                                        const uint32_t x[3], int *source_out) {
    int best = 999;
    int best_idx = -1;
    for (int i = 0; i < seed_count; i++) {
        const uint32_t *s = seeds + 3 * i;
        int d = hw32(x[0] ^ s[0]) + hw32(x[1] ^ s[1]) + hw32(x[2] ^ s[2]);
        if (d < best) {
            best = d;
            best_idx = i;
        }
    }
    if (source_out) *source_out = best_idx;
    return best;
}

static void frontier61_make_entry(const uint32_t x[3],
                                  const frontier61_eval_t *e,
                                  int distance, int passes,
                                  int source_seed, int policy,
                                  frontier61_entry_t *out) {
    out->used = 1;
    memcpy(out->x, x, 3 * sizeof(uint32_t));
    memcpy(out->defects, e->defects, sizeof(out->defects));
    out->d61_hw = e->d61_hw;
    out->tail_defect_hw = e->tail_defect_hw;
    out->tail_hw = e->tail_hw;
    out->distance = distance;
    out->passes = passes;
    out->source_seed = source_seed;
    out->policy = policy;
}

static int frontier61_better_d61(const frontier61_entry_t *a,
                                 const frontier61_entry_t *b) {
    if (!a->used) return 0;
    if (!b->used) return 1;
    if (a->d61_hw != b->d61_hw) return a->d61_hw < b->d61_hw;
    if (a->tail_hw != b->tail_hw) return a->tail_hw < b->tail_hw;
    if (a->tail_defect_hw != b->tail_defect_hw) {
        return a->tail_defect_hw < b->tail_defect_hw;
    }
    return a->defects[4] < b->defects[4];
}

static int frontier61_better_tail(const frontier61_entry_t *a,
                                  const frontier61_entry_t *b) {
    if (!a->used) return 0;
    if (!b->used) return 1;
    if (a->tail_hw != b->tail_hw) return a->tail_hw < b->tail_hw;
    if (a->d61_hw != b->d61_hw) return a->d61_hw < b->d61_hw;
    if (a->tail_defect_hw != b->tail_defect_hw) {
        return a->tail_defect_hw < b->tail_defect_hw;
    }
    return a->defects[4] < b->defects[4];
}

static int frontier61_better_blend(const frontier61_entry_t *a,
                                   const frontier61_entry_t *b) {
    if (!a->used) return 0;
    if (!b->used) return 1;
    int as = a->d61_hw * 8 + a->tail_hw;
    int bs = b->d61_hw * 8 + b->tail_hw;
    if (as != bs) return as < bs;
    if (a->tail_defect_hw != b->tail_defect_hw) {
        return a->tail_defect_hw < b->tail_defect_hw;
    }
    return a->defects[4] < b->defects[4];
}

static int frontier61_dominates(const frontier61_entry_t *a,
                                const frontier61_entry_t *b) {
    return a->used && b->used &&
           a->d61_hw <= b->d61_hw &&
           a->tail_hw <= b->tail_hw &&
           (a->d61_hw < b->d61_hw || a->tail_hw < b->tail_hw);
}

static int frontier61_same_point(const frontier61_entry_t *a,
                                 const frontier61_entry_t *b) {
    return a->used && b->used &&
           a->x[0] == b->x[0] && a->x[1] == b->x[1] && a->x[2] == b->x[2];
}

static void frontier61_add_entry(frontier61_entry_t entries[16],
                                 const frontier61_entry_t *entry) {
    if (!entry->used) return;
    for (int i = 0; i < 16; i++) {
        if (entries[i].used &&
            (frontier61_same_point(&entries[i], entry) ||
             frontier61_dominates(&entries[i], entry))) {
            return;
        }
    }

    for (int i = 0; i < 16; i++) {
        if (entries[i].used && frontier61_dominates(entry, &entries[i])) {
            entries[i].used = 0;
        }
    }

    for (int i = 0; i < 16; i++) {
        if (!entries[i].used) {
            entries[i] = *entry;
            return;
        }
    }

    int worst = 0;
    int worst_score = entries[0].d61_hw * 8 + entries[0].tail_hw;
    for (int i = 1; i < 16; i++) {
        int score = entries[i].d61_hw * 8 + entries[i].tail_hw;
        if (score > worst_score) {
            worst = i;
            worst_score = score;
        }
    }
    int entry_score = entry->d61_hw * 8 + entry->tail_hw;
    if (entry_score < worst_score) entries[worst] = *entry;
}

static void frontier61_print_entry(const frontier61_entry_t *e) {
    printf("{\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"d61\":\"0x%08x\",\"d61_hw\":%d,"
           "\"tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"tail_defect_hw\":%d,\"tail_hw\":%d,"
           "\"distance\":%d,\"passes\":%d,\"source_seed\":%d,\"policy\":%d}",
           e->x[0], e->x[1], e->x[2],
           e->defects[4], e->d61_hw,
           e->defects[0], e->defects[1], e->defects[2], e->defects[3],
           e->defects[4], e->defects[5], e->defects[6],
           e->tail_defect_hw, e->tail_hw,
           e->distance, e->passes, e->source_seed, e->policy);
}

static void frontier61_print_entries(const frontier61_entry_t entries[16]) {
    printf("[");
    int printed = 0;
    for (int i = 0; i < 16; i++) {
        if (!entries[i].used) continue;
        if (printed++) printf(",");
        frontier61_print_entry(&entries[i]);
    }
    printf("]");
}

static int frontier61_repair(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                             uint32_t x[3], int max_passes, int policy,
                             int *passes_out, frontier61_eval_t *eval_out) {
    frontier61_eval_t cur;
    frontier61_eval_point(p1, p2, x, 0, &cur);
    int passes_used = 0;

    for (int pass = 0; pass < max_passes && cur.defects[3] != 0; pass++) {
        uint32_t best_x[3] = {x[0], x[1], x[2]};
        frontier61_eval_t best = cur;

        for (int bit = 0; bit < 64; bit++) {
            uint32_t xf[3] = {x[0], x[1], x[2]};
            if (bit < 32) xf[1] ^= 1U << bit;
            else xf[2] ^= 1U << (bit - 32);

            frontier61_eval_t y;
            frontier61_eval_point(p1, p2, xf, 0, &y);
            if (frontier61_eval_better(&y, &best, policy)) {
                best = y;
                best_x[1] = xf[1];
                best_x[2] = xf[2];
            }
        }

        if (!frontier61_eval_better(&best, &cur, policy)) break;
        x[1] = best_x[1];
        x[2] = best_x[2];
        cur = best;
        passes_used = pass + 1;
    }

    if (cur.defects[3] == 0) {
        frontier61_eval_point(p1, p2, x, 1, &cur);
    }
    if (passes_out) *passes_out = passes_used;
    if (eval_out) *eval_out = cur;
    return cur.defects[3] == 0;
}

static void frontier61_pool_candidate(int idx, const uint32_t *seeds, int seed_count,
                                      int trials, int threads,
                                      int max_passes, int max_flips) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (seed_count < 1) {
        fprintf(stderr, "frontier61pool needs at least one W57,W58,W59 seed.\n");
        exit(2);
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 64) max_flips = 64;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"frontier61pool\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    frontier61_entry_t global_best_d61 = {0};
    frontier61_entry_t global_best_tail = {0};
    frontier61_entry_t global_best_blend = {0};
    frontier61_entry_t global_best_changed_d61 = {0};
    frontier61_entry_t global_best_changed_tail = {0};
    frontier61_entry_t global_best_changed_blend = {0};
    frontier61_entry_t global_frontier[16];
    memset(global_frontier, 0, sizeof(global_frontier));

    int seed_exact60 = 0;
    for (int i = 0; i < seed_count; i++) {
        const uint32_t *x = seeds + 3 * i;
        frontier61_eval_t e;
        frontier61_eval_point(&p1, &p2, x, 1, &e);
        if (e.defects[3] != 0) continue;
        seed_exact60++;
        frontier61_entry_t entry;
        frontier61_make_entry(x, &e, 0, 0, i, -1, &entry);
        if (frontier61_better_d61(&entry, &global_best_d61)) global_best_d61 = entry;
        if (frontier61_better_tail(&entry, &global_best_tail)) global_best_tail = entry;
        if (frontier61_better_blend(&entry, &global_best_blend)) global_best_blend = entry;
        frontier61_add_entry(global_frontier, &entry);
    }

    long long exact60_hits = seed_exact60;
    long long exact61_hits = 0;
    long long changed_exact60_hits = 0;
    long long projection_failures = 0;
    long long total_passes = 0;
    int max_exact_distance = 0;
    int d61_hw_hist[33];
    int policy_hits[4];
    int policy_changed_hits[4];
    memset(d61_hw_hist, 0, sizeof(d61_hw_hist));
    memset(policy_hits, 0, sizeof(policy_hits));
    memset(policy_changed_hits, 0, sizeof(policy_changed_hits));
    for (int i = 0; i < seed_count; i++) {
        frontier61_eval_t e;
        frontier61_eval_point(&p1, &p2, seeds + 3 * i, 0, &e);
        if (e.defects[3] == 0) {
            int h = e.d61_hw;
            if (h >= 0 && h <= 32) d61_hw_hist[h]++;
            if (e.defects[4] == 0) exact61_hits++;
        }
    }

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x66726f6e74363170ULL ^
                       ((uint64_t)cand->m0 << 7) ^
                       ((uint64_t)seed_count << 41) ^
                       (uint64_t)tid;
        frontier61_entry_t local_best_d61 = global_best_d61;
        frontier61_entry_t local_best_tail = global_best_tail;
        frontier61_entry_t local_best_blend = global_best_blend;
        frontier61_entry_t local_best_changed_d61 = {0};
        frontier61_entry_t local_best_changed_tail = {0};
        frontier61_entry_t local_best_changed_blend = {0};
        frontier61_entry_t local_frontier[16];
        memset(local_frontier, 0, sizeof(local_frontier));
        for (int i = 0; i < 16; i++) {
            if (global_frontier[i].used) local_frontier[i] = global_frontier[i];
        }

        long long local_exact60_hits = 0;
        long long local_exact61_hits = 0;
        long long local_changed_exact60_hits = 0;
        long long local_projection_failures = 0;
        long long local_total_passes = 0;
        int local_max_exact_distance = 0;
        int local_d61_hw_hist[33];
        int local_policy_hits[4];
        int local_policy_changed_hits[4];
        memset(local_d61_hw_hist, 0, sizeof(local_d61_hw_hist));
        memset(local_policy_hits, 0, sizeof(local_policy_hits));
        memset(local_policy_changed_hits, 0, sizeof(local_policy_changed_hits));

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3];
            uint32_t choice = splitmix32(&rng);
            if (local_best_d61.used && (choice & 15U) == 0U) {
                memcpy(x, local_best_d61.x, sizeof(x));
            } else if (local_best_tail.used && (choice & 15U) == 1U) {
                memcpy(x, local_best_tail.x, sizeof(x));
            } else if (local_best_blend.used && (choice & 15U) == 2U) {
                memcpy(x, local_best_blend.x, sizeof(x));
            } else {
                int seed_idx = (int)(splitmix32(&rng) % (uint32_t)seed_count);
                memcpy(x, seeds + 3 * seed_idx, 3 * sizeof(uint32_t));
            }

            int flips = 1 + (int)(splitmix32(&rng) % (uint32_t)max_flips);
            for (int f = 0; f < flips; f++) {
                int bit = (int)(splitmix32(&rng) & 63U);
                if (bit < 32) x[1] ^= 1U << bit;
                else x[2] ^= 1U << (bit - 32);
            }

            int policy = (int)(splitmix32(&rng) & 3U);
            int passes_used = 0;
            frontier61_eval_t e;
            int ok = frontier61_repair(&p1, &p2, x, max_passes,
                                       policy, &passes_used, &e);
            if (!ok) {
                local_projection_failures++;
                continue;
            }

            int source_seed = -1;
            int distance = frontier61_min_seed_distance(seeds, seed_count,
                                                        x, &source_seed);
            frontier61_entry_t entry;
            frontier61_make_entry(x, &e, distance, passes_used,
                                  source_seed, policy, &entry);

            local_exact60_hits++;
            local_total_passes += passes_used;
            if (e.defects[4] == 0) local_exact61_hits++;
            if (e.d61_hw >= 0 && e.d61_hw <= 32) local_d61_hw_hist[e.d61_hw]++;
            local_policy_hits[policy]++;
            if (distance > 0) {
                local_changed_exact60_hits++;
                local_policy_changed_hits[policy]++;
                if (frontier61_better_d61(&entry, &local_best_changed_d61)) {
                    local_best_changed_d61 = entry;
                }
                if (frontier61_better_tail(&entry, &local_best_changed_tail)) {
                    local_best_changed_tail = entry;
                }
                if (frontier61_better_blend(&entry, &local_best_changed_blend)) {
                    local_best_changed_blend = entry;
                }
            }
            if (distance > local_max_exact_distance) {
                local_max_exact_distance = distance;
            }

            if (frontier61_better_d61(&entry, &local_best_d61)) {
                local_best_d61 = entry;
            }
            if (frontier61_better_tail(&entry, &local_best_tail)) {
                local_best_tail = entry;
            }
            if (frontier61_better_blend(&entry, &local_best_blend)) {
                local_best_blend = entry;
            }
            frontier61_add_entry(local_frontier, &entry);
        }

        #pragma omp critical
        {
            exact60_hits += local_exact60_hits;
            exact61_hits += local_exact61_hits;
            changed_exact60_hits += local_changed_exact60_hits;
            projection_failures += local_projection_failures;
            total_passes += local_total_passes;
            if (local_max_exact_distance > max_exact_distance) {
                max_exact_distance = local_max_exact_distance;
            }
            for (int h = 0; h <= 32; h++) {
                d61_hw_hist[h] += local_d61_hw_hist[h];
            }
            for (int p = 0; p < 4; p++) {
                policy_hits[p] += local_policy_hits[p];
                policy_changed_hits[p] += local_policy_changed_hits[p];
            }
            if (frontier61_better_d61(&local_best_d61, &global_best_d61)) {
                global_best_d61 = local_best_d61;
            }
            if (frontier61_better_tail(&local_best_tail, &global_best_tail)) {
                global_best_tail = local_best_tail;
            }
            if (frontier61_better_blend(&local_best_blend, &global_best_blend)) {
                global_best_blend = local_best_blend;
            }
            if (frontier61_better_d61(&local_best_changed_d61,
                                      &global_best_changed_d61)) {
                global_best_changed_d61 = local_best_changed_d61;
            }
            if (frontier61_better_tail(&local_best_changed_tail,
                                       &global_best_changed_tail)) {
                global_best_changed_tail = local_best_changed_tail;
            }
            if (frontier61_better_blend(&local_best_changed_blend,
                                        &global_best_changed_blend)) {
                global_best_changed_blend = local_best_changed_blend;
            }
            for (int i = 0; i < 16; i++) {
                if (local_frontier[i].used) {
                    frontier61_add_entry(global_frontier, &local_frontier[i]);
                }
            }
        }
    }

    printf("{\"mode\":\"frontier61pool\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"seed_count\":%d,\"seed_exact60\":%d,"
           "\"trials\":%d,\"threads\":%d,\"max_passes\":%d,\"max_flips\":%d,"
           "\"exact60_hits\":%lld,\"exact61_hits\":%lld,"
           "\"changed_exact60_hits\":%lld,\"projection_failures\":%lld,"
           "\"avg_success_passes\":%.3f,\"max_exact_distance\":%d,"
           "\"policy_hits\":[%d,%d,%d,%d],"
           "\"policy_changed_hits\":[%d,%d,%d,%d],"
           "\"d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_d61\":",
           cand->id, idx, seed_count, seed_exact60,
           trials, threads, max_passes, max_flips,
           exact60_hits, exact61_hits, changed_exact60_hits,
           projection_failures,
           exact60_hits ? (double)total_passes / (double)exact60_hits : 0.0,
           max_exact_distance,
           policy_hits[0], policy_hits[1], policy_hits[2], policy_hits[3],
           policy_changed_hits[0], policy_changed_hits[1],
           policy_changed_hits[2], policy_changed_hits[3],
           d61_hw_hist[0], d61_hw_hist[1], d61_hw_hist[2], d61_hw_hist[3],
           d61_hw_hist[4], d61_hw_hist[5], d61_hw_hist[6], d61_hw_hist[7],
           d61_hw_hist[8], d61_hw_hist[9], d61_hw_hist[10], d61_hw_hist[11],
           d61_hw_hist[12], d61_hw_hist[13], d61_hw_hist[14], d61_hw_hist[15],
           d61_hw_hist[16], d61_hw_hist[17], d61_hw_hist[18], d61_hw_hist[19],
           d61_hw_hist[20], d61_hw_hist[21], d61_hw_hist[22], d61_hw_hist[23],
           d61_hw_hist[24], d61_hw_hist[25], d61_hw_hist[26], d61_hw_hist[27],
           d61_hw_hist[28], d61_hw_hist[29], d61_hw_hist[30], d61_hw_hist[31],
           d61_hw_hist[32]);
    if (global_best_d61.used) frontier61_print_entry(&global_best_d61);
    else printf("null");
    printf(",\"best_tail\":");
    if (global_best_tail.used) frontier61_print_entry(&global_best_tail);
    else printf("null");
    printf(",\"best_blend\":");
    if (global_best_blend.used) frontier61_print_entry(&global_best_blend);
    else printf("null");
    printf(",\"best_changed_d61\":");
    if (global_best_changed_d61.used) frontier61_print_entry(&global_best_changed_d61);
    else printf("null");
    printf(",\"best_changed_tail\":");
    if (global_best_changed_tail.used) frontier61_print_entry(&global_best_changed_tail);
    else printf("null");
    printf(",\"best_changed_blend\":");
    if (global_best_changed_blend.used) frontier61_print_entry(&global_best_changed_blend);
    else printf("null");
    printf(",\"pareto\":");
    frontier61_print_entries(global_frontier);
    printf("}\n");
}

static void bridge61_consider_point(const sha256_precomp_t *p1,
                                    const sha256_precomp_t *p2,
                                    const uint32_t x[3],
                                    int distance, int source_seed, int policy,
                                    long long *exact60,
                                    long long *exact61,
                                    int d61_hw_hist[33],
                                    frontier61_entry_t *best_d61,
                                    frontier61_entry_t *best_tail,
                                    frontier61_entry_t *best_blend,
                                    frontier61_entry_t pareto[16],
                                    int *best_any_score,
                                    uint32_t best_any_x[3],
                                    frontier61_eval_t *best_any_eval,
                                    int *best_nonexact_score,
                                    uint32_t best_nonexact_x[3],
                                    frontier61_eval_t *best_nonexact_eval) {
    frontier61_eval_t e;
    frontier61_eval_point(p1, p2, x, 1, &e);
    int score = score60_61(e.defects[3], e.defects[4]);
    if (score < *best_any_score ||
        (score == *best_any_score && e.defects[4] < best_any_eval->defects[4])) {
        *best_any_score = score;
        memcpy(best_any_x, x, 3 * sizeof(uint32_t));
        *best_any_eval = e;
    }
    if (e.defects[3] != 0 &&
        (score < *best_nonexact_score ||
         (score == *best_nonexact_score &&
          e.defects[4] < best_nonexact_eval->defects[4]))) {
        *best_nonexact_score = score;
        memcpy(best_nonexact_x, x, 3 * sizeof(uint32_t));
        *best_nonexact_eval = e;
    }
    if (e.defects[3] != 0) return;

    frontier61_entry_t entry;
    frontier61_make_entry(x, &e, distance, 0, source_seed, policy, &entry);
    (*exact60)++;
    if (e.defects[4] == 0) (*exact61)++;
    if (e.d61_hw >= 0 && e.d61_hw <= 32) d61_hw_hist[e.d61_hw]++;

    if (frontier61_better_d61(&entry, best_d61)) *best_d61 = entry;
    if (frontier61_better_tail(&entry, best_tail)) *best_tail = entry;
    if (frontier61_better_blend(&entry, best_blend)) *best_blend = entry;
    frontier61_add_entry(pareto, &entry);
}

static void bridge61_point(int idx, uint32_t fixed_w57,
                           uint32_t w58_a, uint32_t w59_a,
                           uint32_t w58_b, uint32_t w59_b,
                           int max_extra) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_extra < 0) max_extra = 0;
    if (max_extra > 2) max_extra = 2;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"bridge61point\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint64_t diff = ((uint64_t)(w59_a ^ w59_b) << 32) | (uint64_t)(w58_a ^ w58_b);
    int bridge_bits[64];
    int outside_bits[64];
    int bridge_k = 0;
    int outside_k = 0;
    for (int bit = 0; bit < 64; bit++) {
        if ((diff >> bit) & 1ULL) bridge_bits[bridge_k++] = bit;
        else outside_bits[outside_k++] = bit;
    }
    if (bridge_k > 20) {
        printf("{\"mode\":\"bridge61point\",\"candidate\":\"%s\",\"error\":\"bridge_too_wide\",\"bridge_hw\":%d}\n",
               cand->id, bridge_k);
        return;
    }

    long long checked = 0;
    long long exact60 = 0;
    long long exact61 = 0;
    long long exact_by_extra[3] = {0, 0, 0};
    int d61_hw_hist[33];
    memset(d61_hw_hist, 0, sizeof(d61_hw_hist));
    frontier61_entry_t best_d61 = {0};
    frontier61_entry_t best_tail = {0};
    frontier61_entry_t best_blend = {0};
    frontier61_entry_t pareto[16];
    memset(pareto, 0, sizeof(pareto));
    int best_any_score = 9999;
    uint32_t best_any_x[3] = {fixed_w57, w58_a, w59_a};
    frontier61_eval_t best_any_eval;
    memset(&best_any_eval, 0, sizeof(best_any_eval));
    int best_nonexact_score = 9999;
    uint32_t best_nonexact_x[3] = {fixed_w57, w58_a, w59_a};
    frontier61_eval_t best_nonexact_eval;
    memset(&best_nonexact_eval, 0, sizeof(best_nonexact_eval));

    uint64_t bridge_subsets = 1ULL << bridge_k;
    for (uint64_t subset = 0; subset < bridge_subsets; subset++) {
        uint64_t bridge_delta = 0;
        for (int j = 0; j < bridge_k; j++) {
            if ((subset >> j) & 1ULL) bridge_delta |= 1ULL << bridge_bits[j];
        }

        for (int extra_n = 0; extra_n <= max_extra; extra_n++) {
            if (extra_n == 0) {
                uint64_t delta = bridge_delta;
                uint32_t x[3] = {
                    fixed_w57,
                    w58_a ^ (uint32_t)(delta & 0xffffffffULL),
                    w59_a ^ (uint32_t)(delta >> 32)
                };
                long long before = exact60;
                bridge61_consider_point(&p1, &p2, x,
                                        hw32((uint32_t)(delta & 0xffffffffULL)) +
                                        hw32((uint32_t)(delta >> 32)),
                                        0, extra_n, &exact60, &exact61,
                                        d61_hw_hist, &best_d61, &best_tail,
                                        &best_blend, pareto,
                                        &best_any_score, best_any_x,
                                        &best_any_eval,
                                        &best_nonexact_score, best_nonexact_x,
                                        &best_nonexact_eval);
                if (exact60 > before) exact_by_extra[extra_n]++;
                checked++;
            } else if (extra_n == 1) {
                for (int a = 0; a < outside_k; a++) {
                    uint64_t delta = bridge_delta | (1ULL << outside_bits[a]);
                    uint32_t x[3] = {
                        fixed_w57,
                        w58_a ^ (uint32_t)(delta & 0xffffffffULL),
                        w59_a ^ (uint32_t)(delta >> 32)
                    };
                    long long before = exact60;
                    bridge61_consider_point(&p1, &p2, x,
                                            hw32((uint32_t)(delta & 0xffffffffULL)) +
                                            hw32((uint32_t)(delta >> 32)),
                                            0, extra_n, &exact60, &exact61,
                                            d61_hw_hist, &best_d61, &best_tail,
                                            &best_blend, pareto,
                                            &best_any_score, best_any_x,
                                            &best_any_eval,
                                            &best_nonexact_score, best_nonexact_x,
                                            &best_nonexact_eval);
                    if (exact60 > before) exact_by_extra[extra_n]++;
                    checked++;
                }
            } else {
                for (int a = 0; a < outside_k; a++) {
                    for (int b = a + 1; b < outside_k; b++) {
                        uint64_t delta = bridge_delta |
                                         (1ULL << outside_bits[a]) |
                                         (1ULL << outside_bits[b]);
                        uint32_t x[3] = {
                            fixed_w57,
                            w58_a ^ (uint32_t)(delta & 0xffffffffULL),
                            w59_a ^ (uint32_t)(delta >> 32)
                        };
                        long long before = exact60;
                        bridge61_consider_point(&p1, &p2, x,
                                                hw32((uint32_t)(delta & 0xffffffffULL)) +
                                                hw32((uint32_t)(delta >> 32)),
                                                0, extra_n, &exact60, &exact61,
                                                d61_hw_hist, &best_d61, &best_tail,
                                                &best_blend, pareto,
                                                &best_any_score, best_any_x,
                                                &best_any_eval,
                                                &best_nonexact_score, best_nonexact_x,
                                                &best_nonexact_eval);
                        if (exact60 > before) exact_by_extra[extra_n]++;
                        checked++;
                    }
                }
            }
        }
    }

    printf("{\"mode\":\"bridge61point\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"fixed_w57\":\"0x%08x\","
           "\"a\":[\"0x%08x\",\"0x%08x\"],"
           "\"b\":[\"0x%08x\",\"0x%08x\"],"
           "\"bridge_delta\":\"0x%016llx\",\"bridge_hw\":%d,"
           "\"max_extra\":%d,\"checked\":%lld,\"exact60\":%lld,"
           "\"exact61\":%lld,\"exact_by_extra\":[%lld,%lld,%lld],"
           "\"d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_any_score\":%d,"
           "\"best_any_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_any_hw60_61\":[%d,%d],"
           "\"best_any_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_nonexact_score\":%d,"
           "\"best_nonexact_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_nonexact_hw60_61\":[%d,%d],"
           "\"best_nonexact_tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"best_d61\":",
           cand->id, idx, fixed_w57,
           w58_a, w59_a, w58_b, w59_b,
           (unsigned long long)diff, bridge_k,
           max_extra, checked, exact60, exact61,
           exact_by_extra[0], exact_by_extra[1], exact_by_extra[2],
           d61_hw_hist[0], d61_hw_hist[1], d61_hw_hist[2], d61_hw_hist[3],
           d61_hw_hist[4], d61_hw_hist[5], d61_hw_hist[6], d61_hw_hist[7],
           d61_hw_hist[8], d61_hw_hist[9], d61_hw_hist[10], d61_hw_hist[11],
           d61_hw_hist[12], d61_hw_hist[13], d61_hw_hist[14], d61_hw_hist[15],
           d61_hw_hist[16], d61_hw_hist[17], d61_hw_hist[18], d61_hw_hist[19],
           d61_hw_hist[20], d61_hw_hist[21], d61_hw_hist[22], d61_hw_hist[23],
           d61_hw_hist[24], d61_hw_hist[25], d61_hw_hist[26], d61_hw_hist[27],
           d61_hw_hist[28], d61_hw_hist[29], d61_hw_hist[30], d61_hw_hist[31],
           d61_hw_hist[32],
           best_any_score,
           best_any_x[0], best_any_x[1], best_any_x[2],
           best_any_eval.d60_hw, best_any_eval.d61_hw,
           best_any_eval.defects[0], best_any_eval.defects[1],
           best_any_eval.defects[2], best_any_eval.defects[3],
           best_any_eval.defects[4], best_any_eval.defects[5],
           best_any_eval.defects[6],
           best_nonexact_score,
           best_nonexact_x[0], best_nonexact_x[1], best_nonexact_x[2],
           best_nonexact_eval.d60_hw, best_nonexact_eval.d61_hw,
           best_nonexact_eval.defects[0], best_nonexact_eval.defects[1],
           best_nonexact_eval.defects[2], best_nonexact_eval.defects[3],
           best_nonexact_eval.defects[4], best_nonexact_eval.defects[5],
           best_nonexact_eval.defects[6]);
    if (best_d61.used) frontier61_print_entry(&best_d61);
    else printf("null");
    printf(",\"best_tail\":");
    if (best_tail.used) frontier61_print_entry(&best_tail);
    else printf("null");
    printf(",\"best_blend\":");
    if (best_blend.used) frontier61_print_entry(&best_blend);
    else printf("null");
    printf(",\"pareto\":");
    frontier61_print_entries(pareto);
    printf("}\n");
}

static void nearexact61_point(int idx, const uint32_t base_x[3], int max_k) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_k < 0) max_k = 0;
    if (max_k > 7) max_k = 7;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"nearexact61point\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    long long checked = 0;
    long long exact60 = 0;
    long long exact61 = 0;
    long long exact_by_k[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    int d61_hw_hist[33];
    memset(d61_hw_hist, 0, sizeof(d61_hw_hist));
    frontier61_entry_t best_d61 = {0};
    frontier61_entry_t best_tail = {0};
    frontier61_entry_t best_blend = {0};
    frontier61_entry_t pareto[16];
    frontier61_entry_t exact_list[64];
    uint32_t best_nonexact_x[8][3];
    uint32_t best_nonexact_defects[8][7];
    int best_nonexact_k[8];
    int best_nonexact_d61_hw[8];
    int best_nonexact_tail_defect_hw[8];
    memset(pareto, 0, sizeof(pareto));
    memset(exact_list, 0, sizeof(exact_list));
    memset(best_nonexact_x, 0, sizeof(best_nonexact_x));
    memset(best_nonexact_defects, 0, sizeof(best_nonexact_defects));
    for (int i = 0; i < 8; i++) {
        best_nonexact_k[i] = -1;
        best_nonexact_d61_hw[i] = 99;
        best_nonexact_tail_defect_hw[i] = 999;
    }
    int exact_list_count = 0;

    for (int k = 0; k <= max_k; k++) {
        uint64_t combo = (k == 0) ? 0ULL : ((1ULL << k) - 1ULL);
        while (1) {
            uint32_t x[3];
            if (k == 0) memcpy(x, base_x, 3 * sizeof(uint32_t));
            else apply_combo_to_x(base_x, combo, x);

            frontier61_eval_t e;
            frontier61_eval_point(&p1, &p2, x, 1, &e);
            checked++;
            if (e.defects[3] == 0) {
                frontier61_entry_t entry;
                frontier61_make_entry(x, &e, k, 0, 0, k, &entry);
                exact60++;
                exact_by_k[k]++;
                if (e.defects[4] == 0) exact61++;
                if (e.d61_hw >= 0 && e.d61_hw <= 32) d61_hw_hist[e.d61_hw]++;
                if (frontier61_better_d61(&entry, &best_d61)) best_d61 = entry;
                if (frontier61_better_tail(&entry, &best_tail)) best_tail = entry;
                if (frontier61_better_blend(&entry, &best_blend)) best_blend = entry;
                frontier61_add_entry(pareto, &entry);
                if (exact_list_count < 64) exact_list[exact_list_count++] = entry;
            } else if (e.d60_hw >= 1 && e.d60_hw <= 7) {
                if (e.d61_hw < best_nonexact_d61_hw[e.d60_hw] ||
                    (e.d61_hw == best_nonexact_d61_hw[e.d60_hw] &&
                     e.tail_defect_hw < best_nonexact_tail_defect_hw[e.d60_hw])) {
                    best_nonexact_d61_hw[e.d60_hw] = e.d61_hw;
                    best_nonexact_tail_defect_hw[e.d60_hw] = e.tail_defect_hw;
                    best_nonexact_k[e.d60_hw] = k;
                    memcpy(best_nonexact_x[e.d60_hw], x, 3 * sizeof(uint32_t));
                    memcpy(best_nonexact_defects[e.d60_hw], e.defects,
                           sizeof(e.defects));
                }
            }

            if (k == 0) break;
            uint64_t next = next_combination64(combo);
            if (!next || next < combo) break;
            combo = next;
        }
    }

    printf("{\"mode\":\"nearexact61point\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"max_k\":%d,\"checked\":%lld,\"exact60\":%lld,"
           "\"exact61\":%lld,\"exact_by_k\":[%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld],"
           "\"d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_d61\":",
           cand->id, idx, base_x[0], base_x[1], base_x[2],
           max_k, checked, exact60, exact61,
           exact_by_k[0], exact_by_k[1], exact_by_k[2],
           exact_by_k[3], exact_by_k[4], exact_by_k[5], exact_by_k[6],
           exact_by_k[7],
           d61_hw_hist[0], d61_hw_hist[1], d61_hw_hist[2], d61_hw_hist[3],
           d61_hw_hist[4], d61_hw_hist[5], d61_hw_hist[6], d61_hw_hist[7],
           d61_hw_hist[8], d61_hw_hist[9], d61_hw_hist[10], d61_hw_hist[11],
           d61_hw_hist[12], d61_hw_hist[13], d61_hw_hist[14], d61_hw_hist[15],
           d61_hw_hist[16], d61_hw_hist[17], d61_hw_hist[18], d61_hw_hist[19],
           d61_hw_hist[20], d61_hw_hist[21], d61_hw_hist[22], d61_hw_hist[23],
           d61_hw_hist[24], d61_hw_hist[25], d61_hw_hist[26], d61_hw_hist[27],
           d61_hw_hist[28], d61_hw_hist[29], d61_hw_hist[30], d61_hw_hist[31],
           d61_hw_hist[32]);
    if (best_d61.used) frontier61_print_entry(&best_d61);
    else printf("null");
    printf(",\"best_tail\":");
    if (best_tail.used) frontier61_print_entry(&best_tail);
    else printf("null");
    printf(",\"best_blend\":");
    if (best_blend.used) frontier61_print_entry(&best_blend);
    else printf("null");
    printf(",\"pareto\":");
    frontier61_print_entries(pareto);
    printf(",\"exact_list\":[");
    for (int i = 0; i < exact_list_count; i++) {
        if (i) printf(",");
        frontier61_print_entry(&exact_list[i]);
    }
    printf("],\"best_nonexact_by_d60_hw\":[null");
    for (int h = 1; h <= 7; h++) {
        printf(",");
        if (best_nonexact_k[h] < 0) {
            printf("null");
            continue;
        }
        printf("{\"d60_hw\":%d,\"d61_hw\":%d,\"tail_defect_hw\":%d,"
               "\"k\":%d,\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
               "\"0x%08x\",\"0x%08x\",\"0x%08x\"]}",
               h, best_nonexact_d61_hw[h], best_nonexact_tail_defect_hw[h],
               best_nonexact_k[h],
               best_nonexact_x[h][0], best_nonexact_x[h][1],
               best_nonexact_x[h][2],
               best_nonexact_defects[h][0], best_nonexact_defects[h][1],
               best_nonexact_defects[h][2], best_nonexact_defects[h][3],
               best_nonexact_defects[h][4], best_nonexact_defects[h][5],
               best_nonexact_defects[h][6]);
    }
    printf("]}\n");
}

static int ridge61_score(const frontier61_eval_t *e, int weight) {
    return e->d60_hw * weight + e->d61_hw;
}

static int ridge61_eval_better(const frontier61_eval_t *a,
                               const frontier61_eval_t *b,
                               int weight) {
    int as = ridge61_score(a, weight);
    int bs = ridge61_score(b, weight);
    if (as != bs) return as < bs;
    if (a->d61_hw != b->d61_hw) return a->d61_hw < b->d61_hw;
    if (a->d60_hw != b->d60_hw) return a->d60_hw < b->d60_hw;
    if (a->tail_defect_hw != b->tail_defect_hw) {
        return a->tail_defect_hw < b->tail_defect_hw;
    }
    if (a->defects[3] != b->defects[3]) return a->defects[3] < b->defects[3];
    return a->defects[4] < b->defects[4];
}

static void ridge61_print_point(const uint32_t x[3],
                                const frontier61_eval_t *e,
                                int score, int distance,
                                int passes, int tail_hw) {
    printf("{\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"score\":%d,\"d60\":\"0x%08x\",\"d60_hw\":%d,"
           "\"d61\":\"0x%08x\",\"d61_hw\":%d,"
           "\"tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"tail_defect_hw\":%d,\"tail_hw\":%d,"
           "\"distance\":%d,\"passes\":%d}",
           x[0], x[1], x[2],
           score, e->defects[3], e->d60_hw, e->defects[4], e->d61_hw,
           e->defects[0], e->defects[1], e->defects[2], e->defects[3],
           e->defects[4], e->defects[5], e->defects[6],
           e->tail_defect_hw, tail_hw, distance, passes);
}

static void ridge61_walk_candidate(int idx, const uint32_t base_x[3],
                                   int trials, int threads,
                                   int max_passes, int max_flips,
                                   int weight) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 64) max_flips = 64;
    if (weight < 1) weight = 1;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"ridge61walk\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    frontier61_eval_t base_eval;
    frontier61_eval_point(&p1, &p2, base_x, base_x[0] == 0 ? 0 : 1, &base_eval);

    int best_any_score = ridge61_score(&base_eval, weight);
    uint32_t best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
    frontier61_eval_t best_any_eval = base_eval;
    int best_any_distance = 0;
    int best_any_passes = 0;

    int best_exact_d61_hw = (base_eval.defects[3] == 0) ? base_eval.d61_hw : 99;
    uint32_t best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
    frontier61_eval_t best_exact_eval = base_eval;
    int best_exact_distance = 0;
    int best_exact_passes = 0;
    int best_exact_tail_hw = (base_eval.defects[3] == 0) ? base_eval.tail_hw : 999;

    int exact60_hits = (base_eval.defects[3] == 0) ? 1 : 0;
    int exact61_hits = (base_eval.defects[3] == 0 && base_eval.defects[4] == 0) ? 1 : 0;
    int changed_exact60_hits = 0;
    int d60_hw_hist[33];
    int d61_hw_hist[33];
    memset(d60_hw_hist, 0, sizeof(d60_hw_hist));
    memset(d61_hw_hist, 0, sizeof(d61_hw_hist));
    if (base_eval.d60_hw >= 0 && base_eval.d60_hw <= 32) {
        d60_hw_hist[base_eval.d60_hw]++;
    }
    if (base_eval.defects[3] == 0 && base_eval.d61_hw >= 0 &&
        base_eval.d61_hw <= 32) {
        d61_hw_hist[base_eval.d61_hw]++;
    }

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x7269646765363177ULL ^
                       ((uint64_t)cand->m0 << 13) ^
                       ((uint64_t)base_x[1] << 29) ^
                       ((uint64_t)base_x[2] << 3) ^
                       (uint64_t)tid;

        int local_best_any_score = best_any_score;
        uint32_t local_best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
        frontier61_eval_t local_best_any_eval = base_eval;
        int local_best_any_distance = 0;
        int local_best_any_passes = 0;

        int local_best_exact_d61_hw = best_exact_d61_hw;
        uint32_t local_best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
        frontier61_eval_t local_best_exact_eval = base_eval;
        int local_best_exact_distance = 0;
        int local_best_exact_passes = 0;
        int local_best_exact_tail_hw = best_exact_tail_hw;

        int local_exact60_hits = 0;
        int local_exact61_hits = 0;
        int local_changed_exact60_hits = 0;
        int local_d60_hw_hist[33];
        int local_d61_hw_hist[33];
        memset(local_d60_hw_hist, 0, sizeof(local_d60_hw_hist));
        memset(local_d61_hw_hist, 0, sizeof(local_d61_hw_hist));

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3];
            if ((splitmix32(&rng) & 3U) == 0U &&
                local_best_any_score < best_any_score) {
                memcpy(x, local_best_any_x, sizeof(x));
            } else {
                memcpy(x, base_x, 3 * sizeof(uint32_t));
            }

            int flips = 1 + (int)(splitmix32(&rng) % (uint32_t)max_flips);
            for (int f = 0; f < flips; f++) {
                int bit = (int)(splitmix32(&rng) & 63U);
                if (bit < 32) x[1] ^= 1U << bit;
                else x[2] ^= 1U << (bit - 32);
            }

            frontier61_eval_t cur;
            frontier61_eval_point(&p1, &p2, x, 0, &cur);
            int passes_used = 0;

            for (int pass = 0; pass < max_passes; pass++) {
                uint32_t best_step_x[3] = {x[0], x[1], x[2]};
                frontier61_eval_t best_step = cur;

                for (int bit = 0; bit < 64; bit++) {
                    uint32_t xf[3] = {x[0], x[1], x[2]};
                    if (bit < 32) xf[1] ^= 1U << bit;
                    else xf[2] ^= 1U << (bit - 32);

                    frontier61_eval_t y;
                    frontier61_eval_point(&p1, &p2, xf, 0, &y);
                    if (ridge61_eval_better(&y, &best_step, weight)) {
                        best_step = y;
                        best_step_x[1] = xf[1];
                        best_step_x[2] = xf[2];
                    }
                }

                if (!ridge61_eval_better(&best_step, &cur, weight)) break;
                x[1] = best_step_x[1];
                x[2] = best_step_x[2];
                cur = best_step;
                passes_used = pass + 1;
            }

            int distance = hw32(x[1] ^ base_x[1]) + hw32(x[2] ^ base_x[2]);
            int score = ridge61_score(&cur, weight);
            if (cur.d60_hw >= 0 && cur.d60_hw <= 32) {
                local_d60_hw_hist[cur.d60_hw]++;
            }
            if (score < local_best_any_score ||
                (score == local_best_any_score &&
                 ridge61_eval_better(&cur, &local_best_any_eval, weight))) {
                local_best_any_score = score;
                memcpy(local_best_any_x, x, sizeof(local_best_any_x));
                local_best_any_eval = cur;
                local_best_any_distance = distance;
                local_best_any_passes = passes_used;
            }

            if (cur.defects[3] == 0) {
                frontier61_eval_point(&p1, &p2, x, 1, &cur);
                local_exact60_hits++;
                if (cur.defects[4] == 0) local_exact61_hits++;
                if (distance > 0) local_changed_exact60_hits++;
                if (cur.d61_hw >= 0 && cur.d61_hw <= 32) {
                    local_d61_hw_hist[cur.d61_hw]++;
                }
                if (cur.d61_hw < local_best_exact_d61_hw ||
                    (cur.d61_hw == local_best_exact_d61_hw &&
                     cur.tail_hw < local_best_exact_tail_hw)) {
                    local_best_exact_d61_hw = cur.d61_hw;
                    memcpy(local_best_exact_x, x, sizeof(local_best_exact_x));
                    local_best_exact_eval = cur;
                    local_best_exact_tail_hw = cur.tail_hw;
                    local_best_exact_distance = distance;
                    local_best_exact_passes = passes_used;
                }
            }
        }

        #pragma omp critical
        {
            exact60_hits += local_exact60_hits;
            exact61_hits += local_exact61_hits;
            changed_exact60_hits += local_changed_exact60_hits;
            for (int h = 0; h <= 32; h++) {
                d60_hw_hist[h] += local_d60_hw_hist[h];
                d61_hw_hist[h] += local_d61_hw_hist[h];
            }
            if (local_best_any_score < best_any_score ||
                (local_best_any_score == best_any_score &&
                 ridge61_eval_better(&local_best_any_eval, &best_any_eval, weight))) {
                best_any_score = local_best_any_score;
                memcpy(best_any_x, local_best_any_x, sizeof(best_any_x));
                best_any_eval = local_best_any_eval;
                best_any_distance = local_best_any_distance;
                best_any_passes = local_best_any_passes;
            }
            if (local_best_exact_d61_hw < best_exact_d61_hw ||
                (local_best_exact_d61_hw == best_exact_d61_hw &&
                 local_best_exact_tail_hw < best_exact_tail_hw)) {
                best_exact_d61_hw = local_best_exact_d61_hw;
                memcpy(best_exact_x, local_best_exact_x, sizeof(best_exact_x));
                best_exact_eval = local_best_exact_eval;
                best_exact_tail_hw = local_best_exact_tail_hw;
                best_exact_distance = local_best_exact_distance;
                best_exact_passes = local_best_exact_passes;
            }
        }
    }

    printf("{\"mode\":\"ridge61walk\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"base_score\":%d,\"weight\":%d,"
           "\"trials\":%d,\"threads\":%d,\"max_passes\":%d,\"max_flips\":%d,"
           "\"exact60_hits\":%d,\"exact61_hits\":%d,"
           "\"changed_exact60_hits\":%d,"
           "\"d60_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"exact_d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_any\":",
           cand->id, idx,
           base_x[0], base_x[1], base_x[2],
           ridge61_score(&base_eval, weight), weight,
           trials, threads, max_passes, max_flips,
           exact60_hits, exact61_hits, changed_exact60_hits,
           d60_hw_hist[0], d60_hw_hist[1], d60_hw_hist[2], d60_hw_hist[3],
           d60_hw_hist[4], d60_hw_hist[5], d60_hw_hist[6], d60_hw_hist[7],
           d60_hw_hist[8], d60_hw_hist[9], d60_hw_hist[10], d60_hw_hist[11],
           d60_hw_hist[12], d60_hw_hist[13], d60_hw_hist[14], d60_hw_hist[15],
           d60_hw_hist[16], d60_hw_hist[17], d60_hw_hist[18], d60_hw_hist[19],
           d60_hw_hist[20], d60_hw_hist[21], d60_hw_hist[22], d60_hw_hist[23],
           d60_hw_hist[24], d60_hw_hist[25], d60_hw_hist[26], d60_hw_hist[27],
           d60_hw_hist[28], d60_hw_hist[29], d60_hw_hist[30], d60_hw_hist[31],
           d60_hw_hist[32],
           d61_hw_hist[0], d61_hw_hist[1], d61_hw_hist[2], d61_hw_hist[3],
           d61_hw_hist[4], d61_hw_hist[5], d61_hw_hist[6], d61_hw_hist[7],
           d61_hw_hist[8], d61_hw_hist[9], d61_hw_hist[10], d61_hw_hist[11],
           d61_hw_hist[12], d61_hw_hist[13], d61_hw_hist[14], d61_hw_hist[15],
           d61_hw_hist[16], d61_hw_hist[17], d61_hw_hist[18], d61_hw_hist[19],
           d61_hw_hist[20], d61_hw_hist[21], d61_hw_hist[22], d61_hw_hist[23],
           d61_hw_hist[24], d61_hw_hist[25], d61_hw_hist[26], d61_hw_hist[27],
           d61_hw_hist[28], d61_hw_hist[29], d61_hw_hist[30], d61_hw_hist[31],
           d61_hw_hist[32]);
    ridge61_print_point(best_any_x, &best_any_eval, best_any_score,
                        best_any_distance, best_any_passes, best_any_eval.tail_hw);
    printf(",\"best_exact\":");
    if (best_exact_d61_hw < 99) {
        ridge61_print_point(best_exact_x, &best_exact_eval,
                            ridge61_score(&best_exact_eval, weight),
                            best_exact_distance, best_exact_passes,
                            best_exact_tail_hw);
    } else {
        printf("null");
    }
    printf("}\n");
}

static int capped61_over(const frontier61_eval_t *e, int cap) {
    return (e->d61_hw > cap) ? (e->d61_hw - cap) : 0;
}

static int capped61_eval_better(const frontier61_eval_t *a,
                                const frontier61_eval_t *b,
                                int cap) {
    int ao = capped61_over(a, cap);
    int bo = capped61_over(b, cap);
    if (ao != bo) return ao < bo;
    if (a->d60_hw != b->d60_hw) return a->d60_hw < b->d60_hw;
    if (a->d61_hw != b->d61_hw) return a->d61_hw < b->d61_hw;
    if (a->tail_defect_hw != b->tail_defect_hw) {
        return a->tail_defect_hw < b->tail_defect_hw;
    }
    if (a->defects[3] != b->defects[3]) return a->defects[3] < b->defects[3];
    return a->defects[4] < b->defects[4];
}

static void capped61_walk_candidate(int idx, const uint32_t base_x[3],
                                    int trials, int threads,
                                    int max_passes, int max_flips,
                                    int cap) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 64) max_flips = 64;
    if (cap < 0) cap = 0;
    if (cap > 32) cap = 32;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"capped61walk\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    frontier61_eval_t base_eval;
    frontier61_eval_point(&p1, &p2, base_x, base_x[0] == 0 ? 0 : 1, &base_eval);

    uint32_t best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
    frontier61_eval_t best_any_eval = base_eval;
    int best_any_distance = 0;
    int best_any_passes = 0;

    uint32_t best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    frontier61_eval_t best_cap_eval = base_eval;
    int best_cap_distance = 0;
    int best_cap_passes = 0;
    int have_cap = base_eval.d61_hw <= cap;

    uint32_t best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
    frontier61_eval_t best_exact_eval = base_eval;
    int best_exact_distance = 0;
    int best_exact_passes = 0;
    int best_exact_tail_hw = 999;
    int have_exact = 0;
    if (base_eval.defects[3] == 0) {
        have_exact = 1;
        best_exact_tail_hw = base_eval.tail_hw;
    }

    int cap_hits = have_cap ? 1 : 0;
    int exact60_hits = (base_eval.defects[3] == 0) ? 1 : 0;
    int exact_cap_hits = (base_eval.defects[3] == 0 && base_eval.d61_hw <= cap) ? 1 : 0;
    int changed_exact_cap_hits = 0;
    int cap_d60_hist[33];
    int exact_d61_hist[33];
    memset(cap_d60_hist, 0, sizeof(cap_d60_hist));
    memset(exact_d61_hist, 0, sizeof(exact_d61_hist));
    if (have_cap && base_eval.d60_hw >= 0 && base_eval.d60_hw <= 32) {
        cap_d60_hist[base_eval.d60_hw]++;
    }
    if (base_eval.defects[3] == 0 && base_eval.d61_hw >= 0 &&
        base_eval.d61_hw <= 32) {
        exact_d61_hist[base_eval.d61_hw]++;
    }

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x636170363177616cULL ^
                       ((uint64_t)cand->m0 << 11) ^
                       ((uint64_t)base_x[1] << 23) ^
                       ((uint64_t)base_x[2] << 5) ^
                       (uint64_t)tid;

        uint32_t local_best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
        frontier61_eval_t local_best_any_eval = base_eval;
        int local_best_any_distance = 0;
        int local_best_any_passes = 0;

        uint32_t local_best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
        frontier61_eval_t local_best_cap_eval = base_eval;
        int local_best_cap_distance = 0;
        int local_best_cap_passes = 0;
        int local_have_cap = have_cap;

        uint32_t local_best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
        frontier61_eval_t local_best_exact_eval = base_eval;
        int local_best_exact_distance = 0;
        int local_best_exact_passes = 0;
        int local_best_exact_tail_hw = best_exact_tail_hw;
        int local_have_exact = have_exact;

        int local_cap_hits = 0;
        int local_exact60_hits = 0;
        int local_exact_cap_hits = 0;
        int local_changed_exact_cap_hits = 0;
        int local_cap_d60_hist[33];
        int local_exact_d61_hist[33];
        memset(local_cap_d60_hist, 0, sizeof(local_cap_d60_hist));
        memset(local_exact_d61_hist, 0, sizeof(local_exact_d61_hist));

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3];
            if ((splitmix32(&rng) & 3U) == 0U && local_have_cap) {
                memcpy(x, local_best_cap_x, sizeof(x));
            } else {
                memcpy(x, base_x, 3 * sizeof(uint32_t));
            }

            int flips = 1 + (int)(splitmix32(&rng) % (uint32_t)max_flips);
            for (int f = 0; f < flips; f++) {
                int bit = (int)(splitmix32(&rng) & 63U);
                if (bit < 32) x[1] ^= 1U << bit;
                else x[2] ^= 1U << (bit - 32);
            }

            frontier61_eval_t cur;
            frontier61_eval_point(&p1, &p2, x, 0, &cur);
            int passes_used = 0;

            for (int pass = 0; pass < max_passes; pass++) {
                uint32_t best_step_x[3] = {x[0], x[1], x[2]};
                frontier61_eval_t best_step = cur;

                for (int bit = 0; bit < 64; bit++) {
                    uint32_t xf[3] = {x[0], x[1], x[2]};
                    if (bit < 32) xf[1] ^= 1U << bit;
                    else xf[2] ^= 1U << (bit - 32);

                    frontier61_eval_t y;
                    frontier61_eval_point(&p1, &p2, xf, 0, &y);
                    if (capped61_eval_better(&y, &best_step, cap)) {
                        best_step = y;
                        best_step_x[1] = xf[1];
                        best_step_x[2] = xf[2];
                    }
                }

                if (!capped61_eval_better(&best_step, &cur, cap)) break;
                x[1] = best_step_x[1];
                x[2] = best_step_x[2];
                cur = best_step;
                passes_used = pass + 1;
            }

            int distance = hw32(x[1] ^ base_x[1]) + hw32(x[2] ^ base_x[2]);
            if (capped61_eval_better(&cur, &local_best_any_eval, cap)) {
                local_best_any_eval = cur;
                memcpy(local_best_any_x, x, sizeof(local_best_any_x));
                local_best_any_distance = distance;
                local_best_any_passes = passes_used;
            }

            if (cur.d61_hw <= cap) {
                local_cap_hits++;
                if (cur.d60_hw >= 0 && cur.d60_hw <= 32) {
                    local_cap_d60_hist[cur.d60_hw]++;
                }
                if (!local_have_cap ||
                    capped61_eval_better(&cur, &local_best_cap_eval, cap)) {
                    local_have_cap = 1;
                    local_best_cap_eval = cur;
                    memcpy(local_best_cap_x, x, sizeof(local_best_cap_x));
                    local_best_cap_distance = distance;
                    local_best_cap_passes = passes_used;
                }
            }

            if (cur.defects[3] == 0) {
                frontier61_eval_point(&p1, &p2, x, 1, &cur);
                local_exact60_hits++;
                if (cur.d61_hw >= 0 && cur.d61_hw <= 32) {
                    local_exact_d61_hist[cur.d61_hw]++;
                }
                if (cur.d61_hw <= cap) {
                    local_exact_cap_hits++;
                    if (distance > 0) local_changed_exact_cap_hits++;
                }
                if (!local_have_exact ||
                    cur.d61_hw < local_best_exact_eval.d61_hw ||
                    (cur.d61_hw == local_best_exact_eval.d61_hw &&
                     cur.tail_hw < local_best_exact_tail_hw)) {
                    local_have_exact = 1;
                    local_best_exact_eval = cur;
                    memcpy(local_best_exact_x, x, sizeof(local_best_exact_x));
                    local_best_exact_distance = distance;
                    local_best_exact_passes = passes_used;
                    local_best_exact_tail_hw = cur.tail_hw;
                }
            }
        }

        #pragma omp critical
        {
            cap_hits += local_cap_hits;
            exact60_hits += local_exact60_hits;
            exact_cap_hits += local_exact_cap_hits;
            changed_exact_cap_hits += local_changed_exact_cap_hits;
            for (int h = 0; h <= 32; h++) {
                cap_d60_hist[h] += local_cap_d60_hist[h];
                exact_d61_hist[h] += local_exact_d61_hist[h];
            }
            if (capped61_eval_better(&local_best_any_eval, &best_any_eval, cap)) {
                best_any_eval = local_best_any_eval;
                memcpy(best_any_x, local_best_any_x, sizeof(best_any_x));
                best_any_distance = local_best_any_distance;
                best_any_passes = local_best_any_passes;
            }
            if (local_have_cap &&
                (!have_cap ||
                 capped61_eval_better(&local_best_cap_eval, &best_cap_eval, cap))) {
                have_cap = 1;
                best_cap_eval = local_best_cap_eval;
                memcpy(best_cap_x, local_best_cap_x, sizeof(best_cap_x));
                best_cap_distance = local_best_cap_distance;
                best_cap_passes = local_best_cap_passes;
            }
            if (local_have_exact &&
                (!have_exact ||
                 local_best_exact_eval.d61_hw < best_exact_eval.d61_hw ||
                 (local_best_exact_eval.d61_hw == best_exact_eval.d61_hw &&
                  local_best_exact_tail_hw < best_exact_tail_hw))) {
                have_exact = 1;
                best_exact_eval = local_best_exact_eval;
                memcpy(best_exact_x, local_best_exact_x, sizeof(best_exact_x));
                best_exact_distance = local_best_exact_distance;
                best_exact_passes = local_best_exact_passes;
                best_exact_tail_hw = local_best_exact_tail_hw;
            }
        }
    }

    printf("{\"mode\":\"capped61walk\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"cap\":%d,\"trials\":%d,\"threads\":%d,"
           "\"max_passes\":%d,\"max_flips\":%d,"
           "\"cap_hits\":%d,\"exact60_hits\":%d,\"exact_cap_hits\":%d,"
           "\"changed_exact_cap_hits\":%d,"
           "\"cap_d60_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"exact_d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_any\":",
           cand->id, idx,
           base_x[0], base_x[1], base_x[2],
           cap, trials, threads, max_passes, max_flips,
           cap_hits, exact60_hits, exact_cap_hits, changed_exact_cap_hits,
           cap_d60_hist[0], cap_d60_hist[1], cap_d60_hist[2], cap_d60_hist[3],
           cap_d60_hist[4], cap_d60_hist[5], cap_d60_hist[6], cap_d60_hist[7],
           cap_d60_hist[8], cap_d60_hist[9], cap_d60_hist[10], cap_d60_hist[11],
           cap_d60_hist[12], cap_d60_hist[13], cap_d60_hist[14], cap_d60_hist[15],
           cap_d60_hist[16], cap_d60_hist[17], cap_d60_hist[18], cap_d60_hist[19],
           cap_d60_hist[20], cap_d60_hist[21], cap_d60_hist[22], cap_d60_hist[23],
           cap_d60_hist[24], cap_d60_hist[25], cap_d60_hist[26], cap_d60_hist[27],
           cap_d60_hist[28], cap_d60_hist[29], cap_d60_hist[30], cap_d60_hist[31],
           cap_d60_hist[32],
           exact_d61_hist[0], exact_d61_hist[1], exact_d61_hist[2],
           exact_d61_hist[3], exact_d61_hist[4], exact_d61_hist[5],
           exact_d61_hist[6], exact_d61_hist[7], exact_d61_hist[8],
           exact_d61_hist[9], exact_d61_hist[10], exact_d61_hist[11],
           exact_d61_hist[12], exact_d61_hist[13], exact_d61_hist[14],
           exact_d61_hist[15], exact_d61_hist[16], exact_d61_hist[17],
           exact_d61_hist[18], exact_d61_hist[19], exact_d61_hist[20],
           exact_d61_hist[21], exact_d61_hist[22], exact_d61_hist[23],
           exact_d61_hist[24], exact_d61_hist[25], exact_d61_hist[26],
           exact_d61_hist[27], exact_d61_hist[28], exact_d61_hist[29],
           exact_d61_hist[30], exact_d61_hist[31], exact_d61_hist[32]);
    ridge61_print_point(best_any_x, &best_any_eval,
                        best_any_eval.d60_hw * 64 + best_any_eval.d61_hw,
                        best_any_distance, best_any_passes,
                        best_any_eval.tail_hw);
    printf(",\"best_cap\":");
    if (have_cap) {
        ridge61_print_point(best_cap_x, &best_cap_eval,
                            best_cap_eval.d60_hw * 64 + best_cap_eval.d61_hw,
                            best_cap_distance, best_cap_passes,
                            best_cap_eval.tail_hw);
    } else {
        printf("null");
    }
    printf(",\"best_exact\":");
    if (have_exact) {
        ridge61_print_point(best_exact_x, &best_exact_eval,
                            best_exact_eval.d60_hw * 64 + best_exact_eval.d61_hw,
                            best_exact_distance, best_exact_passes,
                            best_exact_tail_hw);
    } else {
        printf("null");
    }
    printf("}\n");
}

typedef struct {
    frontier61_eval_t f;
    int part_dist;
    int carry_dist;
    int chart_dist;
} chart61_eval_t;

static void chart61_eval_point(const sha256_precomp_t *p1,
                               const sha256_precomp_t *p2,
                               const uint32_t x[3],
                               const tail_trace_t *target,
                               int want_tail_hw,
                               chart61_eval_t *out) {
    tail_trace_t trace;
    tail_trace_for_x(p1, p2, x, &trace);

    memcpy(out->f.defects, trace.defects, sizeof(out->f.defects));
    out->f.d60_hw = hw32(trace.defects[3]);
    out->f.d61_hw = hw32(trace.defects[4]);
    out->f.d62_hw = hw32(trace.defects[5]);
    out->f.d63_hw = hw32(trace.defects[6]);
    out->f.tail_defect_hw = out->f.d61_hw + out->f.d62_hw + out->f.d63_hw;
    out->f.tail_hw = 999;
    if (want_tail_hw && trace.defects[3] == 0) {
        out->f.tail_hw = sha256_eval_tail(p1, p2, trace.w1, trace.w2);
    }

    int r61 = 4;
    out->part_dist =
        hw32(trace.parts[r61][1] ^ target->parts[r61][1]) +
        hw32(trace.parts[r61][2] ^ target->parts[r61][2]) +
        hw32(trace.parts[r61][3] ^ target->parts[r61][3]);
    out->carry_dist =
        hw32(trace.carries[r61][0] ^ target->carries[r61][0]) +
        hw32(trace.carries[r61][1] ^ target->carries[r61][1]) +
        hw32(trace.carries[r61][2] ^ target->carries[r61][2]);
    out->chart_dist = out->part_dist + out->carry_dist;
}

static int chart61_over(const chart61_eval_t *e, int cap) {
    return (e->f.d61_hw > cap) ? (e->f.d61_hw - cap) : 0;
}

static int chart61_score(const chart61_eval_t *e, int cap, int policy,
                         int part_weight, int carry_weight) {
    int over = chart61_over(e, cap);
    int chart = e->part_dist * part_weight + e->carry_dist * carry_weight;
    switch (policy & 3) {
        case 0:
            return over * 1000000 + e->f.d60_hw * 10000 +
                   chart * 16 + e->f.d61_hw;
        case 1:
            return over * 1000000 + chart * 10000 +
                   e->f.d60_hw * 64 + e->f.d61_hw;
        case 2:
            return e->f.d60_hw * 1000000 + over * 10000 +
                   chart * 16 + e->f.d61_hw;
        default:
            return (e->f.d60_hw + over) * 100000 +
                   e->f.d61_hw * 1000 + chart;
    }
}

static int chart61_eval_better(const chart61_eval_t *a,
                               const chart61_eval_t *b,
                               int cap, int policy,
                               int part_weight, int carry_weight) {
    int as = chart61_score(a, cap, policy, part_weight, carry_weight);
    int bs = chart61_score(b, cap, policy, part_weight, carry_weight);
    if (as != bs) return as < bs;
    if (a->f.d60_hw != b->f.d60_hw) return a->f.d60_hw < b->f.d60_hw;
    if (a->f.d61_hw != b->f.d61_hw) return a->f.d61_hw < b->f.d61_hw;
    if (a->chart_dist != b->chart_dist) return a->chart_dist < b->chart_dist;
    if (a->f.tail_defect_hw != b->f.tail_defect_hw) {
        return a->f.tail_defect_hw < b->f.tail_defect_hw;
    }
    if (a->f.defects[3] != b->f.defects[3]) {
        return a->f.defects[3] < b->f.defects[3];
    }
    return a->f.defects[4] < b->f.defects[4];
}

static int chart61_cap_better(const chart61_eval_t *a,
                              const chart61_eval_t *b) {
    if (a->f.d60_hw != b->f.d60_hw) return a->f.d60_hw < b->f.d60_hw;
    if (a->f.d61_hw != b->f.d61_hw) return a->f.d61_hw < b->f.d61_hw;
    if (a->chart_dist != b->chart_dist) return a->chart_dist < b->chart_dist;
    if (a->f.tail_defect_hw != b->f.tail_defect_hw) {
        return a->f.tail_defect_hw < b->f.tail_defect_hw;
    }
    return a->f.defects[3] < b->f.defects[3];
}

static void chart61_print_point(const uint32_t x[3], const chart61_eval_t *e,
                                int score, int distance, int passes) {
    printf("{\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"score\":%d,\"d60\":\"0x%08x\",\"d60_hw\":%d,"
           "\"d61\":\"0x%08x\",\"d61_hw\":%d,"
           "\"tail_defects\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"tail_defect_hw\":%d,\"tail_hw\":%d,"
           "\"part_dist\":%d,\"carry_dist\":%d,\"chart_dist\":%d,"
           "\"distance\":%d,\"passes\":%d}",
           x[0], x[1], x[2], score,
           e->f.defects[3], e->f.d60_hw, e->f.defects[4], e->f.d61_hw,
           e->f.defects[0], e->f.defects[1], e->f.defects[2],
           e->f.defects[3], e->f.defects[4], e->f.defects[5],
           e->f.defects[6],
           e->f.tail_defect_hw, e->f.tail_hw,
           e->part_dist, e->carry_dist, e->chart_dist,
           distance, passes);
}

static void chart61_walk_candidate(int idx, const uint32_t base_x[3],
                                   int trials, int threads,
                                   int max_passes, int max_flips,
                                   int cap, int policy,
                                   int part_weight, int carry_weight,
                                   int free_w57) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 64) max_flips = 64;
    if (cap < 0) cap = 0;
    if (cap > 32) cap = 32;
    if (part_weight < 0) part_weight = 0;
    if (carry_weight < 0) carry_weight = 0;
    int move_bits = free_w57 ? 96 : 64;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"chart61walk\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    tail_trace_t target;
    tail_trace_for_x(&p1, &p2, base_x, &target);

    chart61_eval_t base_eval;
    chart61_eval_point(&p1, &p2, base_x, &target, 1, &base_eval);

    uint32_t best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_any_eval = base_eval;
    int best_any_distance = 0;
    int best_any_passes = 0;

    uint32_t best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_cap_eval = base_eval;
    int best_cap_distance = 0;
    int best_cap_passes = 0;
    int have_cap = base_eval.f.d61_hw <= cap;

    uint32_t best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_eval = base_eval;
    int best_exact_distance = 0;
    int best_exact_passes = 0;
    int have_exact = base_eval.f.defects[3] == 0;

    uint32_t best_exact_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_cap_eval = base_eval;
    int best_exact_cap_distance = 0;
    int best_exact_cap_passes = 0;
    int have_exact_cap = have_exact && base_eval.f.d61_hw <= cap;

    int cap_hits = have_cap ? 1 : 0;
    int exact60_hits = have_exact ? 1 : 0;
    int exact_cap_hits = have_exact_cap ? 1 : 0;
    int changed_exact_cap_hits = 0;
    int cap_d60_hist[33];
    int exact_d61_hist[33];
    memset(cap_d60_hist, 0, sizeof(cap_d60_hist));
    memset(exact_d61_hist, 0, sizeof(exact_d61_hist));
    if (have_cap && base_eval.f.d60_hw >= 0 && base_eval.f.d60_hw <= 32) {
        cap_d60_hist[base_eval.f.d60_hw]++;
    }
    if (have_exact && base_eval.f.d61_hw >= 0 && base_eval.f.d61_hw <= 32) {
        exact_d61_hist[base_eval.f.d61_hw]++;
    }

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x6368617274363177ULL ^
                       ((uint64_t)cand->m0 << 11) ^
                       ((uint64_t)base_x[1] << 19) ^
                       ((uint64_t)base_x[2] << 3) ^
                       (uint64_t)tid;

        uint32_t local_best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_any_eval = base_eval;
        int local_best_any_distance = 0;
        int local_best_any_passes = 0;

        uint32_t local_best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_cap_eval = base_eval;
        int local_best_cap_distance = 0;
        int local_best_cap_passes = 0;
        int local_have_cap = have_cap;

        uint32_t local_best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_exact_eval = base_eval;
        int local_best_exact_distance = 0;
        int local_best_exact_passes = 0;
        int local_have_exact = have_exact;

        uint32_t local_best_exact_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_exact_cap_eval = base_eval;
        int local_best_exact_cap_distance = 0;
        int local_best_exact_cap_passes = 0;
        int local_have_exact_cap = have_exact_cap;

        int local_cap_hits = 0;
        int local_exact60_hits = 0;
        int local_exact_cap_hits = 0;
        int local_changed_exact_cap_hits = 0;
        int local_cap_d60_hist[33];
        int local_exact_d61_hist[33];
        memset(local_cap_d60_hist, 0, sizeof(local_cap_d60_hist));
        memset(local_exact_d61_hist, 0, sizeof(local_exact_d61_hist));

        #pragma omp for schedule(dynamic, 8)
        for (int i = 0; i < trials; i++) {
            uint32_t x[3];
            if ((splitmix32(&rng) & 3U) == 0U && local_have_cap) {
                memcpy(x, local_best_cap_x, sizeof(x));
            } else {
                memcpy(x, base_x, 3 * sizeof(uint32_t));
            }

            int flips = 1 + (int)(splitmix32(&rng) % (uint32_t)max_flips);
            for (int f = 0; f < flips; f++) {
                int bit = (int)(splitmix32(&rng) % (uint32_t)move_bits);
                if (free_w57 && bit < 32) x[0] ^= 1U << bit;
                else if (free_w57 && bit < 64) x[1] ^= 1U << (bit - 32);
                else if (free_w57) x[2] ^= 1U << (bit - 64);
                else if (bit < 32) x[1] ^= 1U << bit;
                else x[2] ^= 1U << (bit - 32);
            }

            chart61_eval_t cur;
            chart61_eval_point(&p1, &p2, x, &target, 0, &cur);
            int passes_used = 0;

            for (int pass = 0; pass < max_passes; pass++) {
                uint32_t best_step_x[3] = {x[0], x[1], x[2]};
                chart61_eval_t best_step = cur;

                for (int bit = 0; bit < move_bits; bit++) {
                    uint32_t xf[3] = {x[0], x[1], x[2]};
                    if (free_w57 && bit < 32) xf[0] ^= 1U << bit;
                    else if (free_w57 && bit < 64) xf[1] ^= 1U << (bit - 32);
                    else if (free_w57) xf[2] ^= 1U << (bit - 64);
                    else if (bit < 32) xf[1] ^= 1U << bit;
                    else xf[2] ^= 1U << (bit - 32);

                    chart61_eval_t y;
                    chart61_eval_point(&p1, &p2, xf, &target, 0, &y);
                    if (chart61_eval_better(&y, &best_step, cap, policy,
                                            part_weight, carry_weight)) {
                        best_step = y;
                        memcpy(best_step_x, xf, sizeof(best_step_x));
                    }
                }

                if (!chart61_eval_better(&best_step, &cur, cap, policy,
                                         part_weight, carry_weight)) {
                    break;
                }
                memcpy(x, best_step_x, sizeof(x));
                cur = best_step;
                passes_used = pass + 1;
            }

            int distance = hw32(x[0] ^ base_x[0]) +
                           hw32(x[1] ^ base_x[1]) +
                           hw32(x[2] ^ base_x[2]);
            if (chart61_eval_better(&cur, &local_best_any_eval, cap, policy,
                                    part_weight, carry_weight)) {
                local_best_any_eval = cur;
                memcpy(local_best_any_x, x, sizeof(local_best_any_x));
                local_best_any_distance = distance;
                local_best_any_passes = passes_used;
            }

            if (cur.f.d61_hw <= cap) {
                local_cap_hits++;
                if (cur.f.d60_hw >= 0 && cur.f.d60_hw <= 32) {
                    local_cap_d60_hist[cur.f.d60_hw]++;
                }
                if (!local_have_cap ||
                    chart61_cap_better(&cur, &local_best_cap_eval)) {
                    local_have_cap = 1;
                    local_best_cap_eval = cur;
                    memcpy(local_best_cap_x, x, sizeof(local_best_cap_x));
                    local_best_cap_distance = distance;
                    local_best_cap_passes = passes_used;
                }
            }

            if (cur.f.defects[3] == 0) {
                chart61_eval_point(&p1, &p2, x, &target, 1, &cur);
                local_exact60_hits++;
                if (cur.f.d61_hw >= 0 && cur.f.d61_hw <= 32) {
                    local_exact_d61_hist[cur.f.d61_hw]++;
                }
                if (!local_have_exact ||
                    cur.f.d61_hw < local_best_exact_eval.f.d61_hw ||
                    (cur.f.d61_hw == local_best_exact_eval.f.d61_hw &&
                     cur.f.tail_hw < local_best_exact_eval.f.tail_hw)) {
                    local_have_exact = 1;
                    local_best_exact_eval = cur;
                    memcpy(local_best_exact_x, x, sizeof(local_best_exact_x));
                    local_best_exact_distance = distance;
                    local_best_exact_passes = passes_used;
                }
                if (cur.f.d61_hw <= cap) {
                    local_exact_cap_hits++;
                    if (distance > 0) local_changed_exact_cap_hits++;
                    if (!local_have_exact_cap ||
                        cur.f.d61_hw < local_best_exact_cap_eval.f.d61_hw ||
                        (cur.f.d61_hw == local_best_exact_cap_eval.f.d61_hw &&
                         cur.f.tail_hw < local_best_exact_cap_eval.f.tail_hw)) {
                        local_have_exact_cap = 1;
                        local_best_exact_cap_eval = cur;
                        memcpy(local_best_exact_cap_x, x, sizeof(local_best_exact_cap_x));
                        local_best_exact_cap_distance = distance;
                        local_best_exact_cap_passes = passes_used;
                    }
                }
            }
        }

        #pragma omp critical
        {
            cap_hits += local_cap_hits;
            exact60_hits += local_exact60_hits;
            exact_cap_hits += local_exact_cap_hits;
            changed_exact_cap_hits += local_changed_exact_cap_hits;
            for (int h = 0; h <= 32; h++) {
                cap_d60_hist[h] += local_cap_d60_hist[h];
                exact_d61_hist[h] += local_exact_d61_hist[h];
            }
            if (chart61_eval_better(&local_best_any_eval, &best_any_eval, cap,
                                    policy, part_weight, carry_weight)) {
                best_any_eval = local_best_any_eval;
                memcpy(best_any_x, local_best_any_x, sizeof(best_any_x));
                best_any_distance = local_best_any_distance;
                best_any_passes = local_best_any_passes;
            }
            if (local_have_cap &&
                (!have_cap || chart61_cap_better(&local_best_cap_eval,
                                                 &best_cap_eval))) {
                have_cap = 1;
                best_cap_eval = local_best_cap_eval;
                memcpy(best_cap_x, local_best_cap_x, sizeof(best_cap_x));
                best_cap_distance = local_best_cap_distance;
                best_cap_passes = local_best_cap_passes;
            }
            if (local_have_exact &&
                (!have_exact ||
                 local_best_exact_eval.f.d61_hw < best_exact_eval.f.d61_hw ||
                 (local_best_exact_eval.f.d61_hw == best_exact_eval.f.d61_hw &&
                  local_best_exact_eval.f.tail_hw < best_exact_eval.f.tail_hw))) {
                have_exact = 1;
                best_exact_eval = local_best_exact_eval;
                memcpy(best_exact_x, local_best_exact_x, sizeof(best_exact_x));
                best_exact_distance = local_best_exact_distance;
                best_exact_passes = local_best_exact_passes;
            }
            if (local_have_exact_cap &&
                (!have_exact_cap ||
                 local_best_exact_cap_eval.f.d61_hw < best_exact_cap_eval.f.d61_hw ||
                 (local_best_exact_cap_eval.f.d61_hw ==
                  best_exact_cap_eval.f.d61_hw &&
                  local_best_exact_cap_eval.f.tail_hw <
                  best_exact_cap_eval.f.tail_hw))) {
                have_exact_cap = 1;
                best_exact_cap_eval = local_best_exact_cap_eval;
                memcpy(best_exact_cap_x, local_best_exact_cap_x,
                       sizeof(best_exact_cap_x));
                best_exact_cap_distance = local_best_exact_cap_distance;
                best_exact_cap_passes = local_best_exact_cap_passes;
            }
        }
    }

    printf("{\"mode\":\"chart61walk\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"cap\":%d,\"policy\":%d,\"part_weight\":%d,\"carry_weight\":%d,"
           "\"free_w57\":%d,"
           "\"trials\":%d,\"threads\":%d,\"max_passes\":%d,\"max_flips\":%d,"
           "\"base_part_dist\":%d,\"base_carry_dist\":%d,"
           "\"cap_hits\":%d,\"exact60_hits\":%d,\"exact_cap_hits\":%d,"
           "\"changed_exact_cap_hits\":%d,"
           "\"cap_d60_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"exact_d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_any\":",
           cand->id, idx, base_x[0], base_x[1], base_x[2],
           cap, policy, part_weight, carry_weight,
           free_w57, trials, threads, max_passes, max_flips,
           base_eval.part_dist, base_eval.carry_dist,
           cap_hits, exact60_hits, exact_cap_hits, changed_exact_cap_hits,
           cap_d60_hist[0], cap_d60_hist[1], cap_d60_hist[2], cap_d60_hist[3],
           cap_d60_hist[4], cap_d60_hist[5], cap_d60_hist[6], cap_d60_hist[7],
           cap_d60_hist[8], cap_d60_hist[9], cap_d60_hist[10], cap_d60_hist[11],
           cap_d60_hist[12], cap_d60_hist[13], cap_d60_hist[14], cap_d60_hist[15],
           cap_d60_hist[16], cap_d60_hist[17], cap_d60_hist[18], cap_d60_hist[19],
           cap_d60_hist[20], cap_d60_hist[21], cap_d60_hist[22], cap_d60_hist[23],
           cap_d60_hist[24], cap_d60_hist[25], cap_d60_hist[26], cap_d60_hist[27],
           cap_d60_hist[28], cap_d60_hist[29], cap_d60_hist[30], cap_d60_hist[31],
           cap_d60_hist[32],
           exact_d61_hist[0], exact_d61_hist[1], exact_d61_hist[2],
           exact_d61_hist[3], exact_d61_hist[4], exact_d61_hist[5],
           exact_d61_hist[6], exact_d61_hist[7], exact_d61_hist[8],
           exact_d61_hist[9], exact_d61_hist[10], exact_d61_hist[11],
           exact_d61_hist[12], exact_d61_hist[13], exact_d61_hist[14],
           exact_d61_hist[15], exact_d61_hist[16], exact_d61_hist[17],
           exact_d61_hist[18], exact_d61_hist[19], exact_d61_hist[20],
           exact_d61_hist[21], exact_d61_hist[22], exact_d61_hist[23],
           exact_d61_hist[24], exact_d61_hist[25], exact_d61_hist[26],
           exact_d61_hist[27], exact_d61_hist[28], exact_d61_hist[29],
           exact_d61_hist[30], exact_d61_hist[31], exact_d61_hist[32]);
    chart61_print_point(best_any_x, &best_any_eval,
                        chart61_score(&best_any_eval, cap, policy,
                                      part_weight, carry_weight),
                        best_any_distance, best_any_passes);
    printf(",\"best_cap\":");
    if (have_cap) {
        chart61_print_point(best_cap_x, &best_cap_eval,
                            chart61_score(&best_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_cap_distance, best_cap_passes);
    } else {
        printf("null");
    }
    printf(",\"best_exact\":");
    if (have_exact) {
        chart61_print_point(best_exact_x, &best_exact_eval,
                            chart61_score(&best_exact_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_distance, best_exact_passes);
    } else {
        printf("null");
    }
    printf(",\"best_exact_cap\":");
    if (have_exact_cap) {
        chart61_print_point(best_exact_cap_x, &best_exact_cap_eval,
                            chart61_score(&best_exact_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_cap_distance, best_exact_cap_passes);
    } else {
        printf("null");
    }
    printf("}\n");
}

static void d60_repair_fiber_candidate(int idx, const uint32_t base_x[3],
                                       long long samples, int threads, int cap,
                                       int policy, int part_weight,
                                       int carry_weight, int sequential,
                                       uint64_t seq_start) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (samples < 1) samples = 1;
    if (cap < 0) cap = 0;
    if (cap > 32) cap = 32;
    if (part_weight < 0) part_weight = 0;
    if (carry_weight < 0) carry_weight = 0;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"d60repairfiber\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[64], cols61[64];
    uint64_t cols_pair[64];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns(&p1, &p2, base_x, &d60, &d61,
                        cols60, cols61, cols_pair);

    uint64_t particular = 0;
    int rank60 = 0;
    int solvable = solve_linear_columns(d60, cols60, 64,
                                        &particular, &rank60);
    uint64_t kernel[64];
    int kernel_rank = 0;
    int kernel_dim = kernel_basis_columns32(cols60, 64, kernel, &kernel_rank);

    tail_trace_t target;
    tail_trace_for_x(&p1, &p2, base_x, &target);
    chart61_eval_t base_eval;
    chart61_eval_point(&p1, &p2, base_x, &target, 1, &base_eval);

    if (!solvable) {
        printf("{\"mode\":\"d60repairfiber\",\"candidate\":\"%s\",\"idx\":%d,"
               "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"error\":\"d60_linear_unsolvable\",\"rank60\":%d,"
               "\"kernel_dim\":%d,\"base_d60\":\"0x%08x\","
               "\"base_d61\":\"0x%08x\"}\n",
               cand->id, idx, base_x[0], base_x[1], base_x[2],
               rank60, kernel_dim, d60, d61);
        return;
    }

    uint32_t best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_any_eval = base_eval;
    int best_any_delta_hw = 0;

    uint32_t best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_cap_eval = base_eval;
    int best_cap_delta_hw = 0;
    int have_cap = base_eval.f.d61_hw <= cap;

    uint32_t best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_eval = base_eval;
    int best_exact_delta_hw = 0;
    int have_exact = base_eval.f.defects[3] == 0;

    uint32_t best_exact_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_cap_eval = base_eval;
    int best_exact_cap_delta_hw = 0;
    int have_exact_cap = have_exact && base_eval.f.d61_hw <= cap;

    long long cap_hits = have_cap ? 1 : 0;
    long long exact60_hits = have_exact ? 1 : 0;
    long long exact_cap_hits = have_exact_cap ? 1 : 0;
    int actual_d60_hist[33], cap_d60_hist[33], exact_d61_hist[33];
    memset(actual_d60_hist, 0, sizeof(actual_d60_hist));
    memset(cap_d60_hist, 0, sizeof(cap_d60_hist));
    memset(exact_d61_hist, 0, sizeof(exact_d61_hist));
    if (base_eval.f.d60_hw >= 0 && base_eval.f.d60_hw <= 32) {
        actual_d60_hist[base_eval.f.d60_hw]++;
    }
    if (have_cap && base_eval.f.d60_hw >= 0 && base_eval.f.d60_hw <= 32) {
        cap_d60_hist[base_eval.f.d60_hw]++;
    }
    if (have_exact && base_eval.f.d61_hw >= 0 && base_eval.f.d61_hw <= 32) {
        exact_d61_hist[base_eval.f.d61_hw]++;
    }

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x6436306669626572ULL ^
                       ((uint64_t)cand->m0 << 17) ^
                       ((uint64_t)base_x[1] << 7) ^
                       ((uint64_t)base_x[2] << 29) ^
                       (uint64_t)tid;

        uint32_t local_best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_any_eval = base_eval;
        int local_best_any_delta_hw = 0;

        uint32_t local_best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_cap_eval = base_eval;
        int local_best_cap_delta_hw = 0;
        int local_have_cap = have_cap;

        uint32_t local_best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_exact_eval = base_eval;
        int local_best_exact_delta_hw = 0;
        int local_have_exact = have_exact;

        uint32_t local_best_exact_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_exact_cap_eval = base_eval;
        int local_best_exact_cap_delta_hw = 0;
        int local_have_exact_cap = have_exact_cap;

        long long local_cap_hits = 0;
        long long local_exact60_hits = 0;
        long long local_exact_cap_hits = 0;
        int local_actual_d60_hist[33], local_cap_d60_hist[33], local_exact_d61_hist[33];
        memset(local_actual_d60_hist, 0, sizeof(local_actual_d60_hist));
        memset(local_cap_d60_hist, 0, sizeof(local_cap_d60_hist));
        memset(local_exact_d61_hist, 0, sizeof(local_exact_d61_hist));

        #pragma omp for schedule(dynamic, 256)
        for (int i = 0; i < samples; i++) {
            uint64_t selection = 0;
            if (sequential) {
                if (kernel_dim < 64) {
                    uint64_t mask = (1ULL << kernel_dim) - 1ULL;
                    selection = (seq_start + (uint64_t)i) & mask;
                } else {
                    selection = seq_start + (uint64_t)i;
                }
            } else if (i != 0) {
                uint64_t r = ((uint64_t)splitmix32(&rng) << 32) |
                             (uint64_t)splitmix32(&rng);
                if (kernel_dim < 64) {
                    uint64_t mask = (1ULL << kernel_dim) - 1ULL;
                    selection = r & mask;
                } else {
                    selection = r;
                }
            }
            uint64_t delta = particular ^ combine_kernel_selection(selection, kernel);

            uint32_t x[3];
            apply_delta58_59(base_x, delta, x);
            chart61_eval_t e;
            chart61_eval_point(&p1, &p2, x, &target, 1, &e);
            int dhw = hw32((uint32_t)delta) + hw32((uint32_t)(delta >> 32));

            if (e.f.d60_hw >= 0 && e.f.d60_hw <= 32) {
                local_actual_d60_hist[e.f.d60_hw]++;
            }
            if (chart61_eval_better(&e, &local_best_any_eval, cap, policy,
                                    part_weight, carry_weight)) {
                local_best_any_eval = e;
                memcpy(local_best_any_x, x, sizeof(local_best_any_x));
                local_best_any_delta_hw = dhw;
            }
            if (e.f.d61_hw <= cap) {
                local_cap_hits++;
                if (e.f.d60_hw >= 0 && e.f.d60_hw <= 32) {
                    local_cap_d60_hist[e.f.d60_hw]++;
                }
                if (!local_have_cap || chart61_cap_better(&e, &local_best_cap_eval)) {
                    local_have_cap = 1;
                    local_best_cap_eval = e;
                    memcpy(local_best_cap_x, x, sizeof(local_best_cap_x));
                    local_best_cap_delta_hw = dhw;
                }
            }
            if (e.f.defects[3] == 0) {
                local_exact60_hits++;
                if (e.f.d61_hw >= 0 && e.f.d61_hw <= 32) {
                    local_exact_d61_hist[e.f.d61_hw]++;
                }
                if (!local_have_exact ||
                    e.f.d61_hw < local_best_exact_eval.f.d61_hw ||
                    (e.f.d61_hw == local_best_exact_eval.f.d61_hw &&
                     e.f.tail_hw < local_best_exact_eval.f.tail_hw)) {
                    local_have_exact = 1;
                    local_best_exact_eval = e;
                    memcpy(local_best_exact_x, x, sizeof(local_best_exact_x));
                    local_best_exact_delta_hw = dhw;
                }
                if (e.f.d61_hw <= cap) {
                    local_exact_cap_hits++;
                    if (!local_have_exact_cap ||
                        e.f.d61_hw < local_best_exact_cap_eval.f.d61_hw ||
                        (e.f.d61_hw == local_best_exact_cap_eval.f.d61_hw &&
                         e.f.tail_hw < local_best_exact_cap_eval.f.tail_hw)) {
                        local_have_exact_cap = 1;
                        local_best_exact_cap_eval = e;
                        memcpy(local_best_exact_cap_x, x,
                               sizeof(local_best_exact_cap_x));
                        local_best_exact_cap_delta_hw = dhw;
                    }
                }
            }
        }

        #pragma omp critical
        {
            cap_hits += local_cap_hits;
            exact60_hits += local_exact60_hits;
            exact_cap_hits += local_exact_cap_hits;
            for (int h = 0; h <= 32; h++) {
                actual_d60_hist[h] += local_actual_d60_hist[h];
                cap_d60_hist[h] += local_cap_d60_hist[h];
                exact_d61_hist[h] += local_exact_d61_hist[h];
            }
            if (chart61_eval_better(&local_best_any_eval, &best_any_eval, cap,
                                    policy, part_weight, carry_weight)) {
                best_any_eval = local_best_any_eval;
                memcpy(best_any_x, local_best_any_x, sizeof(best_any_x));
                best_any_delta_hw = local_best_any_delta_hw;
            }
            if (local_have_cap &&
                (!have_cap || chart61_cap_better(&local_best_cap_eval,
                                                 &best_cap_eval))) {
                have_cap = 1;
                best_cap_eval = local_best_cap_eval;
                memcpy(best_cap_x, local_best_cap_x, sizeof(best_cap_x));
                best_cap_delta_hw = local_best_cap_delta_hw;
            }
            if (local_have_exact &&
                (!have_exact ||
                 local_best_exact_eval.f.d61_hw < best_exact_eval.f.d61_hw ||
                 (local_best_exact_eval.f.d61_hw == best_exact_eval.f.d61_hw &&
                  local_best_exact_eval.f.tail_hw < best_exact_eval.f.tail_hw))) {
                have_exact = 1;
                best_exact_eval = local_best_exact_eval;
                memcpy(best_exact_x, local_best_exact_x, sizeof(best_exact_x));
                best_exact_delta_hw = local_best_exact_delta_hw;
            }
            if (local_have_exact_cap &&
                (!have_exact_cap ||
                 local_best_exact_cap_eval.f.d61_hw <
                 best_exact_cap_eval.f.d61_hw ||
                 (local_best_exact_cap_eval.f.d61_hw ==
                  best_exact_cap_eval.f.d61_hw &&
                  local_best_exact_cap_eval.f.tail_hw <
                  best_exact_cap_eval.f.tail_hw))) {
                have_exact_cap = 1;
                best_exact_cap_eval = local_best_exact_cap_eval;
                memcpy(best_exact_cap_x, local_best_exact_cap_x,
                       sizeof(best_exact_cap_x));
                best_exact_cap_delta_hw = local_best_exact_cap_delta_hw;
            }
        }
    }

    printf("{\"mode\":\"d60repairfiber\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"cap\":%d,\"policy\":%d,\"part_weight\":%d,\"carry_weight\":%d,"
           "\"samples\":%lld,\"threads\":%d,\"rank60\":%d,\"kernel_dim\":%d,"
           "\"sequential\":%d,\"seq_start\":\"0x%016llx\","
           "\"particular_delta\":\"0x%016llx\",\"particular_delta_hw\":%d,"
           "\"base_d60\":\"0x%08x\",\"base_d60_hw\":%d,"
           "\"base_d61\":\"0x%08x\",\"base_d61_hw\":%d,"
           "\"cap_hits\":%lld,\"exact60_hits\":%lld,\"exact_cap_hits\":%lld,"
           "\"actual_d60_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"cap_d60_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"exact_d61_hw_hist\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
           "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"best_any\":",
           cand->id, idx, base_x[0], base_x[1], base_x[2],
           cap, policy, part_weight, carry_weight,
           samples, threads, rank60, kernel_dim,
           sequential, (unsigned long long)seq_start,
           (unsigned long long)particular,
           hw32((uint32_t)particular) + hw32((uint32_t)(particular >> 32)),
           d60, hw32(d60), d61, hw32(d61),
           cap_hits, exact60_hits, exact_cap_hits,
           actual_d60_hist[0], actual_d60_hist[1], actual_d60_hist[2],
           actual_d60_hist[3], actual_d60_hist[4], actual_d60_hist[5],
           actual_d60_hist[6], actual_d60_hist[7], actual_d60_hist[8],
           actual_d60_hist[9], actual_d60_hist[10], actual_d60_hist[11],
           actual_d60_hist[12], actual_d60_hist[13], actual_d60_hist[14],
           actual_d60_hist[15], actual_d60_hist[16], actual_d60_hist[17],
           actual_d60_hist[18], actual_d60_hist[19], actual_d60_hist[20],
           actual_d60_hist[21], actual_d60_hist[22], actual_d60_hist[23],
           actual_d60_hist[24], actual_d60_hist[25], actual_d60_hist[26],
           actual_d60_hist[27], actual_d60_hist[28], actual_d60_hist[29],
           actual_d60_hist[30], actual_d60_hist[31], actual_d60_hist[32],
           cap_d60_hist[0], cap_d60_hist[1], cap_d60_hist[2],
           cap_d60_hist[3], cap_d60_hist[4], cap_d60_hist[5],
           cap_d60_hist[6], cap_d60_hist[7], cap_d60_hist[8],
           cap_d60_hist[9], cap_d60_hist[10], cap_d60_hist[11],
           cap_d60_hist[12], cap_d60_hist[13], cap_d60_hist[14],
           cap_d60_hist[15], cap_d60_hist[16], cap_d60_hist[17],
           cap_d60_hist[18], cap_d60_hist[19], cap_d60_hist[20],
           cap_d60_hist[21], cap_d60_hist[22], cap_d60_hist[23],
           cap_d60_hist[24], cap_d60_hist[25], cap_d60_hist[26],
           cap_d60_hist[27], cap_d60_hist[28], cap_d60_hist[29],
           cap_d60_hist[30], cap_d60_hist[31], cap_d60_hist[32],
           exact_d61_hist[0], exact_d61_hist[1], exact_d61_hist[2],
           exact_d61_hist[3], exact_d61_hist[4], exact_d61_hist[5],
           exact_d61_hist[6], exact_d61_hist[7], exact_d61_hist[8],
           exact_d61_hist[9], exact_d61_hist[10], exact_d61_hist[11],
           exact_d61_hist[12], exact_d61_hist[13], exact_d61_hist[14],
           exact_d61_hist[15], exact_d61_hist[16], exact_d61_hist[17],
           exact_d61_hist[18], exact_d61_hist[19], exact_d61_hist[20],
           exact_d61_hist[21], exact_d61_hist[22], exact_d61_hist[23],
           exact_d61_hist[24], exact_d61_hist[25], exact_d61_hist[26],
           exact_d61_hist[27], exact_d61_hist[28], exact_d61_hist[29],
           exact_d61_hist[30], exact_d61_hist[31], exact_d61_hist[32]);
    chart61_print_point(best_any_x, &best_any_eval,
                        chart61_score(&best_any_eval, cap, policy,
                                      part_weight, carry_weight),
                        best_any_delta_hw, 0);
    printf(",\"best_cap\":");
    if (have_cap) {
        chart61_print_point(best_cap_x, &best_cap_eval,
                            chart61_score(&best_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_cap_delta_hw, 0);
    } else {
        printf("null");
    }
    printf(",\"best_exact\":");
    if (have_exact) {
        chart61_print_point(best_exact_x, &best_exact_eval,
                            chart61_score(&best_exact_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_delta_hw, 0);
    } else {
        printf("null");
    }
    printf(",\"best_exact_cap\":");
    if (have_exact_cap) {
        chart61_print_point(best_exact_cap_x, &best_exact_cap_eval,
                            chart61_score(&best_exact_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_cap_delta_hw, 0);
    } else {
        printf("null");
    }
    printf("}\n");
}

static void d60_repair_fiber96_candidate(int idx, const uint32_t base_x[3],
                                         long long samples, int threads, int cap,
                                         int policy, int part_weight,
                                         int carry_weight) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (samples < 1) samples = 1;
    if (cap < 0) cap = 0;
    if (cap > 32) cap = 32;
    if (part_weight < 0) part_weight = 0;
    if (carry_weight < 0) carry_weight = 0;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"d60repairfiber96\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[96], cols61[96];
    uint64_t cols_pair[96];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns96(&p1, &p2, base_x, &d60, &d61,
                          cols60, cols61, cols_pair);

    delta96_t particular = delta96_zero();
    int rank60 = 0;
    int solvable = solve_linear_columns96(d60, cols60, 96,
                                          &particular, &rank60);
    delta96_t kernel[96];
    int kernel_rank = 0;
    int kernel_dim = kernel_basis_columns32_96(cols60, 96, kernel, &kernel_rank);
    int sampled_kernel_dim = kernel_dim > 64 ? 64 : kernel_dim;

    tail_trace_t target;
    tail_trace_for_x(&p1, &p2, base_x, &target);
    chart61_eval_t base_eval;
    chart61_eval_point(&p1, &p2, base_x, &target, 1, &base_eval);

    if (!solvable) {
        printf("{\"mode\":\"d60repairfiber96\",\"candidate\":\"%s\",\"idx\":%d,"
               "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"error\":\"d60_linear_unsolvable\",\"rank60\":%d,"
               "\"kernel_dim\":%d,\"base_d60\":\"0x%08x\","
               "\"base_d61\":\"0x%08x\"}\n",
               cand->id, idx, base_x[0], base_x[1], base_x[2],
               rank60, kernel_dim, d60, d61);
        return;
    }

    uint32_t best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_any_eval = base_eval;
    int best_any_delta_hw = 0;

    uint32_t best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_cap_eval = base_eval;
    int best_cap_delta_hw = 0;
    int have_cap = base_eval.f.d61_hw <= cap;

    uint32_t best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_eval = base_eval;
    int best_exact_delta_hw = 0;
    int have_exact = base_eval.f.defects[3] == 0;

    uint32_t best_exact_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_cap_eval = base_eval;
    int best_exact_cap_delta_hw = 0;
    int have_exact_cap = have_exact && base_eval.f.d61_hw <= cap;

    long long cap_hits = have_cap ? 1 : 0;
    long long exact60_hits = have_exact ? 1 : 0;
    long long exact_cap_hits = have_exact_cap ? 1 : 0;
    long long actual_d60_hist[33], cap_d60_hist[33], exact_d61_hist[33];
    memset(actual_d60_hist, 0, sizeof(actual_d60_hist));
    memset(cap_d60_hist, 0, sizeof(cap_d60_hist));
    memset(exact_d61_hist, 0, sizeof(exact_d61_hist));
    if (base_eval.f.d60_hw >= 0 && base_eval.f.d60_hw <= 32) {
        actual_d60_hist[base_eval.f.d60_hw]++;
    }
    if (have_cap && base_eval.f.d60_hw >= 0 && base_eval.f.d60_hw <= 32) {
        cap_d60_hist[base_eval.f.d60_hw]++;
    }
    if (have_exact && base_eval.f.d61_hw >= 0 && base_eval.f.d61_hw <= 32) {
        exact_d61_hist[base_eval.f.d61_hw]++;
    }

    #pragma omp parallel num_threads(threads)
    {
        int tid = omp_get_thread_num();
        uint64_t rng = 0x6639367265706169ULL ^
                       ((uint64_t)cand->m0 << 9) ^
                       ((uint64_t)base_x[0] << 21) ^
                       ((uint64_t)base_x[1] << 5) ^
                       ((uint64_t)base_x[2] << 37) ^
                       (uint64_t)tid;

        uint32_t local_best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_any_eval = base_eval;
        int local_best_any_delta_hw = 0;

        uint32_t local_best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_cap_eval = base_eval;
        int local_best_cap_delta_hw = 0;
        int local_have_cap = have_cap;

        uint32_t local_best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_exact_eval = base_eval;
        int local_best_exact_delta_hw = 0;
        int local_have_exact = have_exact;

        uint32_t local_best_exact_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
        chart61_eval_t local_best_exact_cap_eval = base_eval;
        int local_best_exact_cap_delta_hw = 0;
        int local_have_exact_cap = have_exact_cap;

        long long local_cap_hits = 0;
        long long local_exact60_hits = 0;
        long long local_exact_cap_hits = 0;
        long long local_actual_d60_hist[33], local_cap_d60_hist[33], local_exact_d61_hist[33];
        memset(local_actual_d60_hist, 0, sizeof(local_actual_d60_hist));
        memset(local_cap_d60_hist, 0, sizeof(local_cap_d60_hist));
        memset(local_exact_d61_hist, 0, sizeof(local_exact_d61_hist));

        #pragma omp for schedule(dynamic, 256)
        for (long long i = 0; i < samples; i++) {
            uint64_t selection = 0;
            if (i != 0) {
                selection = ((uint64_t)splitmix32(&rng) << 32) |
                            (uint64_t)splitmix32(&rng);
                if (sampled_kernel_dim < 64) {
                    selection &= (1ULL << sampled_kernel_dim) - 1ULL;
                }
            }
            delta96_t delta = delta96_xor(particular,
                                          combine_kernel_selection96(selection, kernel));

            uint32_t x[3];
            apply_delta57_59(base_x, delta, x);
            chart61_eval_t e;
            chart61_eval_point(&p1, &p2, x, &target, 1, &e);
            int dhw = delta96_hw(delta);

            if (e.f.d60_hw >= 0 && e.f.d60_hw <= 32) {
                local_actual_d60_hist[e.f.d60_hw]++;
            }
            if (chart61_eval_better(&e, &local_best_any_eval, cap, policy,
                                    part_weight, carry_weight)) {
                local_best_any_eval = e;
                memcpy(local_best_any_x, x, sizeof(local_best_any_x));
                local_best_any_delta_hw = dhw;
            }
            if (e.f.d61_hw <= cap) {
                local_cap_hits++;
                if (e.f.d60_hw >= 0 && e.f.d60_hw <= 32) {
                    local_cap_d60_hist[e.f.d60_hw]++;
                }
                if (!local_have_cap || chart61_cap_better(&e, &local_best_cap_eval)) {
                    local_have_cap = 1;
                    local_best_cap_eval = e;
                    memcpy(local_best_cap_x, x, sizeof(local_best_cap_x));
                    local_best_cap_delta_hw = dhw;
                }
            }
            if (e.f.defects[3] == 0) {
                local_exact60_hits++;
                if (e.f.d61_hw >= 0 && e.f.d61_hw <= 32) {
                    local_exact_d61_hist[e.f.d61_hw]++;
                }
                if (!local_have_exact ||
                    e.f.d61_hw < local_best_exact_eval.f.d61_hw ||
                    (e.f.d61_hw == local_best_exact_eval.f.d61_hw &&
                     e.f.tail_hw < local_best_exact_eval.f.tail_hw)) {
                    local_have_exact = 1;
                    local_best_exact_eval = e;
                    memcpy(local_best_exact_x, x, sizeof(local_best_exact_x));
                    local_best_exact_delta_hw = dhw;
                }
                if (e.f.d61_hw <= cap) {
                    local_exact_cap_hits++;
                    if (!local_have_exact_cap ||
                        e.f.d61_hw < local_best_exact_cap_eval.f.d61_hw ||
                        (e.f.d61_hw == local_best_exact_cap_eval.f.d61_hw &&
                         e.f.tail_hw < local_best_exact_cap_eval.f.tail_hw)) {
                        local_have_exact_cap = 1;
                        local_best_exact_cap_eval = e;
                        memcpy(local_best_exact_cap_x, x,
                               sizeof(local_best_exact_cap_x));
                        local_best_exact_cap_delta_hw = dhw;
                    }
                }
            }
        }

        #pragma omp critical
        {
            cap_hits += local_cap_hits;
            exact60_hits += local_exact60_hits;
            exact_cap_hits += local_exact_cap_hits;
            for (int h = 0; h <= 32; h++) {
                actual_d60_hist[h] += local_actual_d60_hist[h];
                cap_d60_hist[h] += local_cap_d60_hist[h];
                exact_d61_hist[h] += local_exact_d61_hist[h];
            }
            if (chart61_eval_better(&local_best_any_eval, &best_any_eval, cap,
                                    policy, part_weight, carry_weight)) {
                best_any_eval = local_best_any_eval;
                memcpy(best_any_x, local_best_any_x, sizeof(best_any_x));
                best_any_delta_hw = local_best_any_delta_hw;
            }
            if (local_have_cap &&
                (!have_cap || chart61_cap_better(&local_best_cap_eval,
                                                 &best_cap_eval))) {
                have_cap = 1;
                best_cap_eval = local_best_cap_eval;
                memcpy(best_cap_x, local_best_cap_x, sizeof(best_cap_x));
                best_cap_delta_hw = local_best_cap_delta_hw;
            }
            if (local_have_exact &&
                (!have_exact ||
                 local_best_exact_eval.f.d61_hw < best_exact_eval.f.d61_hw ||
                 (local_best_exact_eval.f.d61_hw == best_exact_eval.f.d61_hw &&
                  local_best_exact_eval.f.tail_hw < best_exact_eval.f.tail_hw))) {
                have_exact = 1;
                best_exact_eval = local_best_exact_eval;
                memcpy(best_exact_x, local_best_exact_x, sizeof(best_exact_x));
                best_exact_delta_hw = local_best_exact_delta_hw;
            }
            if (local_have_exact_cap &&
                (!have_exact_cap ||
                 local_best_exact_cap_eval.f.d61_hw <
                 best_exact_cap_eval.f.d61_hw ||
                 (local_best_exact_cap_eval.f.d61_hw ==
                  best_exact_cap_eval.f.d61_hw &&
                  local_best_exact_cap_eval.f.tail_hw <
                  best_exact_cap_eval.f.tail_hw))) {
                have_exact_cap = 1;
                best_exact_cap_eval = local_best_exact_cap_eval;
                memcpy(best_exact_cap_x, local_best_exact_cap_x,
                       sizeof(best_exact_cap_x));
                best_exact_cap_delta_hw = local_best_exact_cap_delta_hw;
            }
        }
    }

    printf("{\"mode\":\"d60repairfiber96\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"cap\":%d,\"policy\":%d,\"part_weight\":%d,\"carry_weight\":%d,"
           "\"samples\":%lld,\"threads\":%d,\"rank60\":%d,"
           "\"kernel_dim\":%d,\"sampled_kernel_dim\":%d,"
           "\"particular_delta_lo\":\"0x%016llx\","
           "\"particular_delta_hi\":\"0x%08x\",\"particular_delta_hw\":%d,"
           "\"base_d60\":\"0x%08x\",\"base_d60_hw\":%d,"
           "\"base_d61\":\"0x%08x\",\"base_d61_hw\":%d,"
           "\"cap_hits\":%lld,\"exact60_hits\":%lld,\"exact_cap_hits\":%lld,"
           "\"actual_d60_hw_hist\":[",
           cand->id, idx, base_x[0], base_x[1], base_x[2],
           cap, policy, part_weight, carry_weight, samples, threads,
           rank60, kernel_dim, sampled_kernel_dim,
           (unsigned long long)particular.lo, particular.hi,
           delta96_hw(particular), d60, hw32(d60), d61, hw32(d61),
           cap_hits, exact60_hits, exact_cap_hits);
    for (int h = 0; h <= 32; h++) {
        if (h) printf(",");
        printf("%lld", actual_d60_hist[h]);
    }
    printf("],\"cap_d60_hw_hist\":[");
    for (int h = 0; h <= 32; h++) {
        if (h) printf(",");
        printf("%lld", cap_d60_hist[h]);
    }
    printf("],\"exact_d61_hw_hist\":[");
    for (int h = 0; h <= 32; h++) {
        if (h) printf(",");
        printf("%lld", exact_d61_hist[h]);
    }
    printf("],\"best_any\":");
    chart61_print_point(best_any_x, &best_any_eval,
                        chart61_score(&best_any_eval, cap, policy,
                                      part_weight, carry_weight),
                        best_any_delta_hw, 0);
    printf(",\"best_cap\":");
    if (have_cap) {
        chart61_print_point(best_cap_x, &best_cap_eval,
                            chart61_score(&best_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_cap_delta_hw, 0);
    } else {
        printf("null");
    }
    printf(",\"best_exact\":");
    if (have_exact) {
        chart61_print_point(best_exact_x, &best_exact_eval,
                            chart61_score(&best_exact_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_delta_hw, 0);
    } else {
        printf("null");
    }
    printf(",\"best_exact_cap\":");
    if (have_exact_cap) {
        chart61_print_point(best_exact_cap_x, &best_exact_cap_eval,
                            chart61_score(&best_exact_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_cap_delta_hw, 0);
    } else {
        printf("null");
    }
    printf("}\n");
}

static void d60_repair_fiber96_low_candidate(int idx, const uint32_t base_x[3],
                                             int max_k, int cap, int policy,
                                             int part_weight, int carry_weight) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_k < 0) max_k = 0;
    if (max_k > 8) max_k = 8;
    if (cap < 0) cap = 0;
    if (cap > 32) cap = 32;
    if (part_weight < 0) part_weight = 0;
    if (carry_weight < 0) carry_weight = 0;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"d60repairfiber96low\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[96], cols61[96];
    uint64_t cols_pair[96];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns96(&p1, &p2, base_x, &d60, &d61,
                          cols60, cols61, cols_pair);

    delta96_t particular = delta96_zero();
    int rank60 = 0;
    int solvable = solve_linear_columns96(d60, cols60, 96,
                                          &particular, &rank60);
    delta96_t kernel[96];
    int kernel_rank = 0;
    int kernel_dim = kernel_basis_columns32_96(cols60, 96, kernel, &kernel_rank);
    int enum_dim = kernel_dim > 64 ? 64 : kernel_dim;

    tail_trace_t target;
    tail_trace_for_x(&p1, &p2, base_x, &target);
    chart61_eval_t base_eval;
    chart61_eval_point(&p1, &p2, base_x, &target, 1, &base_eval);

    if (!solvable) {
        printf("{\"mode\":\"d60repairfiber96low\",\"candidate\":\"%s\",\"idx\":%d,"
               "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
               "\"error\":\"d60_linear_unsolvable\",\"rank60\":%d,"
               "\"kernel_dim\":%d,\"base_d60\":\"0x%08x\","
               "\"base_d61\":\"0x%08x\"}\n",
               cand->id, idx, base_x[0], base_x[1], base_x[2],
               rank60, kernel_dim, d60, d61);
        return;
    }

    uint32_t best_any_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_any_eval = base_eval;
    int best_any_delta_hw = 0;
    int best_any_k = 0;

    uint32_t best_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_cap_eval = base_eval;
    int best_cap_delta_hw = 0;
    int best_cap_k = 0;
    int have_cap = base_eval.f.d61_hw <= cap;

    uint32_t best_exact_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_eval = base_eval;
    int best_exact_delta_hw = 0;
    int best_exact_k = 0;
    int have_exact = base_eval.f.defects[3] == 0;

    uint32_t best_exact_cap_x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t best_exact_cap_eval = base_eval;
    int best_exact_cap_delta_hw = 0;
    int best_exact_cap_k = 0;
    int have_exact_cap = have_exact && base_eval.f.d61_hw <= cap;

    unsigned long long checked = 0;
    unsigned long long cap_hits = have_cap ? 1ULL : 0ULL;
    unsigned long long exact60_hits = have_exact ? 1ULL : 0ULL;
    unsigned long long exact_cap_hits = have_exact_cap ? 1ULL : 0ULL;

    for (int k = 0; k <= max_k; k++) {
        uint64_t combo = (k == 0) ? 0ULL : ((1ULL << k) - 1ULL);
        while (1) {
            delta96_t delta = delta96_xor(particular,
                                          combine_kernel_selection96(combo, kernel));
            uint32_t x[3];
            apply_delta57_59(base_x, delta, x);
            chart61_eval_t e;
            chart61_eval_point(&p1, &p2, x, &target, 1, &e);
            int dhw = delta96_hw(delta);
            checked++;

            if (chart61_eval_better(&e, &best_any_eval, cap, policy,
                                    part_weight, carry_weight)) {
                best_any_eval = e;
                memcpy(best_any_x, x, sizeof(best_any_x));
                best_any_delta_hw = dhw;
                best_any_k = k;
            }
            if (e.f.d61_hw <= cap) {
                cap_hits++;
                if (!have_cap || chart61_cap_better(&e, &best_cap_eval)) {
                    have_cap = 1;
                    best_cap_eval = e;
                    memcpy(best_cap_x, x, sizeof(best_cap_x));
                    best_cap_delta_hw = dhw;
                    best_cap_k = k;
                }
            }
            if (e.f.defects[3] == 0) {
                exact60_hits++;
                if (!have_exact ||
                    e.f.d61_hw < best_exact_eval.f.d61_hw ||
                    (e.f.d61_hw == best_exact_eval.f.d61_hw &&
                     e.f.tail_hw < best_exact_eval.f.tail_hw)) {
                    have_exact = 1;
                    best_exact_eval = e;
                    memcpy(best_exact_x, x, sizeof(best_exact_x));
                    best_exact_delta_hw = dhw;
                    best_exact_k = k;
                }
                if (e.f.d61_hw <= cap) {
                    exact_cap_hits++;
                    if (!have_exact_cap ||
                        e.f.d61_hw < best_exact_cap_eval.f.d61_hw ||
                        (e.f.d61_hw == best_exact_cap_eval.f.d61_hw &&
                         e.f.tail_hw < best_exact_cap_eval.f.tail_hw)) {
                        have_exact_cap = 1;
                        best_exact_cap_eval = e;
                        memcpy(best_exact_cap_x, x,
                               sizeof(best_exact_cap_x));
                        best_exact_cap_delta_hw = dhw;
                        best_exact_cap_k = k;
                    }
                }
            }

            if (k == 0) break;
            uint64_t next = next_combination64(combo);
            if (!next || next < combo || (enum_dim < 64 && (next >> enum_dim))) break;
            combo = next;
        }
    }

    printf("{\"mode\":\"d60repairfiber96low\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"max_k\":%d,\"cap\":%d,\"policy\":%d,"
           "\"part_weight\":%d,\"carry_weight\":%d,"
           "\"checked\":%llu,\"rank60\":%d,\"kernel_dim\":%d,"
           "\"enum_dim\":%d,\"particular_delta_lo\":\"0x%016llx\","
           "\"particular_delta_hi\":\"0x%08x\",\"particular_delta_hw\":%d,"
           "\"base_d60\":\"0x%08x\",\"base_d60_hw\":%d,"
           "\"base_d61\":\"0x%08x\",\"base_d61_hw\":%d,"
           "\"cap_hits\":%llu,\"exact60_hits\":%llu,\"exact_cap_hits\":%llu,"
           "\"best_any_k\":%d,\"best_any\":",
           cand->id, idx, base_x[0], base_x[1], base_x[2],
           max_k, cap, policy, part_weight, carry_weight,
           checked, rank60, kernel_dim, enum_dim,
           (unsigned long long)particular.lo, particular.hi,
           delta96_hw(particular), d60, hw32(d60), d61, hw32(d61),
           cap_hits, exact60_hits, exact_cap_hits, best_any_k);
    chart61_print_point(best_any_x, &best_any_eval,
                        chart61_score(&best_any_eval, cap, policy,
                                      part_weight, carry_weight),
                        best_any_delta_hw, 0);
    printf(",\"best_cap_k\":%d,\"best_cap\":", best_cap_k);
    if (have_cap) {
        chart61_print_point(best_cap_x, &best_cap_eval,
                            chart61_score(&best_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_cap_delta_hw, 0);
    } else {
        printf("null");
    }
    printf(",\"best_exact_k\":%d,\"best_exact\":", best_exact_k);
    if (have_exact) {
        chart61_print_point(best_exact_x, &best_exact_eval,
                            chart61_score(&best_exact_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_delta_hw, 0);
    } else {
        printf("null");
    }
    printf(",\"best_exact_cap_k\":%d,\"best_exact_cap\":", best_exact_cap_k);
    if (have_exact_cap) {
        chart61_print_point(best_exact_cap_x, &best_exact_cap_eval,
                            chart61_score(&best_exact_cap_eval, cap, policy,
                                          part_weight, carry_weight),
                            best_exact_cap_delta_hw, 0);
    } else {
        printf("null");
    }
    printf("}\n");
}

static void chart61_pair_descent_candidate(int idx, const uint32_t base_x[3],
                                           int max_passes, int max_k,
                                           int cap, int policy,
                                           int part_weight, int carry_weight) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (max_passes < 1) max_passes = 1;
    if (max_passes > 256) max_passes = 256;
    if (max_k < 1) max_k = 1;
    if (max_k > 4) max_k = 4;
    if (cap < 0) cap = 0;
    if (cap > 32) cap = 32;
    if (part_weight < 0) part_weight = 0;
    if (carry_weight < 0) carry_weight = 0;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"chart61pairdescent\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    tail_trace_t target;
    tail_trace_for_x(&p1, &p2, base_x, &target);

    uint32_t x[3] = {base_x[0], base_x[1], base_x[2]};
    chart61_eval_t cur;
    chart61_eval_point(&p1, &p2, x, &target, 0, &cur);

    int passes_used = 0;
    uint64_t accepted_combo[256];
    int accepted_k[256];
    memset(accepted_combo, 0, sizeof(accepted_combo));
    memset(accepted_k, 0, sizeof(accepted_k));

    for (int pass = 0; pass < max_passes; pass++) {
        uint32_t best_x[3] = {x[0], x[1], x[2]};
        chart61_eval_t best = cur;
        uint64_t best_combo = 0;
        int best_k = 0;

        for (int k = 1; k <= max_k; k++) {
            uint64_t combo = (k == 0) ? 0ULL : ((1ULL << k) - 1ULL);
            while (1) {
                uint32_t yx[3];
                apply_combo_to_x(x, combo, yx);
                chart61_eval_t y;
                chart61_eval_point(&p1, &p2, yx, &target, 0, &y);
                if (chart61_eval_better(&y, &best, cap, policy,
                                        part_weight, carry_weight)) {
                    best = y;
                    memcpy(best_x, yx, sizeof(best_x));
                    best_combo = combo;
                    best_k = k;
                }

                uint64_t next = next_combination64(combo);
                if (!next || next < combo) break;
                combo = next;
            }
        }

        if (!chart61_eval_better(&best, &cur, cap, policy,
                                 part_weight, carry_weight)) {
            break;
        }
        x[1] = best_x[1];
        x[2] = best_x[2];
        cur = best;
        accepted_combo[passes_used] = best_combo;
        accepted_k[passes_used] = best_k;
        passes_used++;
        if (cur.f.defects[3] == 0 && cur.f.d61_hw <= cap) break;
    }

    chart61_eval_t final_eval;
    chart61_eval_point(&p1, &p2, x, &target, 1, &final_eval);

    printf("{\"mode\":\"chart61pairdescent\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"cap\":%d,\"policy\":%d,\"part_weight\":%d,\"carry_weight\":%d,"
           "\"max_passes\":%d,\"max_k\":%d,\"passes_used\":%d,"
           "\"accepted\":[",
           cand->id, idx, base_x[0], base_x[1], base_x[2],
           cap, policy, part_weight, carry_weight,
           max_passes, max_k, passes_used);
    for (int i = 0; i < passes_used; i++) {
        if (i) printf(",");
        printf("{\"k\":%d,\"combo\":\"0x%016llx\"}",
               accepted_k[i], (unsigned long long)accepted_combo[i]);
    }
    printf("],\"final\":");
    chart61_print_point(x, &final_eval,
                        chart61_score(&final_eval, cap, policy,
                                      part_weight, carry_weight),
                        hw32(x[1] ^ base_x[1]) + hw32(x[2] ^ base_x[2]),
                        passes_used);
    printf("}\n");
}

typedef struct {
    uint32_t x[3];
    chart61_eval_t e;
    int score;
    int distance;
    int depth;
} chart61_beam_state_t;

static int chart61_beam_cmp(const void *va, const void *vb) {
    const chart61_beam_state_t *a = (const chart61_beam_state_t *)va;
    const chart61_beam_state_t *b = (const chart61_beam_state_t *)vb;
    if (a->score != b->score) return (a->score < b->score) ? -1 : 1;
    if (a->e.f.d60_hw != b->e.f.d60_hw) return a->e.f.d60_hw - b->e.f.d60_hw;
    if (a->e.f.d61_hw != b->e.f.d61_hw) return a->e.f.d61_hw - b->e.f.d61_hw;
    if (a->e.chart_dist != b->e.chart_dist) return a->e.chart_dist - b->e.chart_dist;
    if (a->distance != b->distance) return a->distance - b->distance;
    if (a->x[0] != b->x[0]) return (a->x[0] < b->x[0]) ? -1 : 1;
    if (a->x[1] != b->x[1]) return (a->x[1] < b->x[1]) ? -1 : 1;
    if (a->x[2] != b->x[2]) return (a->x[2] < b->x[2]) ? -1 : 1;
    return 0;
}

static int chart61_exact_better(const chart61_eval_t *a,
                                const chart61_eval_t *b) {
    if (a->f.d61_hw != b->f.d61_hw) return a->f.d61_hw < b->f.d61_hw;
    if (a->chart_dist != b->chart_dist) return a->chart_dist < b->chart_dist;
    if (a->f.tail_defect_hw != b->f.tail_defect_hw) {
        return a->f.tail_defect_hw < b->f.tail_defect_hw;
    }
    return a->f.defects[4] < b->f.defects[4];
}

static void chart61_beam_candidate(int idx, const uint32_t base_x[3],
                                   int depth, int beam_size,
                                   int cap, int policy,
                                   int part_weight, int carry_weight,
                                   int free_w57) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (depth < 1) depth = 1;
    if (depth > 64) depth = 64;
    if (beam_size < 1) beam_size = 1;
    if (beam_size > 16384) beam_size = 16384;
    if (cap < 0) cap = 0;
    if (cap > 32) cap = 32;
    if (part_weight < 0) part_weight = 0;
    if (carry_weight < 0) carry_weight = 0;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"chart61beam\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    tail_trace_t target;
    tail_trace_for_x(&p1, &p2, base_x, &target);

    int move_bits = free_w57 ? 96 : 64;
    size_t max_next = (size_t)beam_size * (size_t)move_bits;
    chart61_beam_state_t *beam =
        (chart61_beam_state_t *)calloc((size_t)beam_size, sizeof(*beam));
    chart61_beam_state_t *next =
        (chart61_beam_state_t *)calloc(max_next, sizeof(*next));
    if (!beam || !next) {
        fprintf(stderr, "chart61beam allocation failed\n");
        free(beam);
        free(next);
        exit(1);
    }

    memcpy(beam[0].x, base_x, sizeof(beam[0].x));
    chart61_eval_point(&p1, &p2, beam[0].x, &target, 1, &beam[0].e);
    beam[0].score = chart61_score(&beam[0].e, cap, policy,
                                  part_weight, carry_weight);
    beam[0].distance = 0;
    beam[0].depth = 0;
    int beam_count = 1;

    chart61_beam_state_t best_any = beam[0];
    chart61_beam_state_t best_cap = beam[0];
    chart61_beam_state_t best_exact = beam[0];
    chart61_beam_state_t best_exact_cap = beam[0];
    int have_cap = (beam[0].e.f.d61_hw <= cap);
    int have_exact = (beam[0].e.f.defects[3] == 0);
    int have_exact_cap = have_exact && have_cap;
    uint64_t evals = 1;

    for (int d = 1; d <= depth; d++) {
        size_t next_count = 0;
        for (int i = 0; i < beam_count; i++) {
            for (int bit = 0; bit < move_bits; bit++) {
                chart61_beam_state_t *s = &next[next_count++];
                s->x[0] = beam[i].x[0];
                s->x[1] = beam[i].x[1];
                s->x[2] = beam[i].x[2];
                if (free_w57 && bit < 32) {
                    s->x[0] ^= 1U << bit;
                } else if (free_w57 && bit < 64) {
                    s->x[1] ^= 1U << (bit - 32);
                } else if (free_w57) {
                    s->x[2] ^= 1U << (bit - 64);
                } else if (bit < 32) {
                    s->x[1] ^= 1U << bit;
                } else {
                    s->x[2] ^= 1U << (bit - 32);
                }
                chart61_eval_point(&p1, &p2, s->x, &target, 0, &s->e);
                s->score = chart61_score(&s->e, cap, policy,
                                         part_weight, carry_weight);
                s->distance = hw32(s->x[0] ^ base_x[0]) +
                              hw32(s->x[1] ^ base_x[1]) +
                              hw32(s->x[2] ^ base_x[2]);
                s->depth = d;
                evals++;
            }
        }

        qsort(next, next_count, sizeof(*next), chart61_beam_cmp);
        beam_count = 0;
        for (size_t i = 0; i < next_count && beam_count < beam_size; i++) {
            if (beam_count > 0 &&
                next[i].x[0] == beam[beam_count - 1].x[0] &&
                next[i].x[1] == beam[beam_count - 1].x[1] &&
                next[i].x[2] == beam[beam_count - 1].x[2]) {
                continue;
            }
            beam[beam_count++] = next[i];
        }

        for (int i = 0; i < beam_count; i++) {
            if (chart61_eval_better(&beam[i].e, &best_any.e, cap, policy,
                                    part_weight, carry_weight)) {
                best_any = beam[i];
            }
            if (beam[i].e.f.d61_hw <= cap &&
                (!have_cap || chart61_cap_better(&beam[i].e, &best_cap.e))) {
                best_cap = beam[i];
                have_cap = 1;
            }
            if (beam[i].e.f.defects[3] == 0 &&
                (!have_exact || chart61_exact_better(&beam[i].e, &best_exact.e))) {
                best_exact = beam[i];
                have_exact = 1;
            }
            if (beam[i].e.f.defects[3] == 0 && beam[i].e.f.d61_hw <= cap &&
                (!have_exact_cap ||
                 chart61_exact_better(&beam[i].e, &best_exact_cap.e))) {
                best_exact_cap = beam[i];
                have_exact_cap = 1;
            }
        }
    }

    chart61_eval_point(&p1, &p2, best_any.x, &target, 1, &best_any.e);
    if (have_cap) chart61_eval_point(&p1, &p2, best_cap.x, &target, 1, &best_cap.e);
    if (have_exact) chart61_eval_point(&p1, &p2, best_exact.x, &target, 1, &best_exact.e);
    if (have_exact_cap) chart61_eval_point(&p1, &p2, best_exact_cap.x, &target, 1, &best_exact_cap.e);

    printf("{\"mode\":\"chart61beam\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"base_x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"depth\":%d,\"beam_size\":%d,\"cap\":%d,\"policy\":%d,"
           "\"free_w57\":%d,"
           "\"part_weight\":%d,\"carry_weight\":%d,\"evals\":%llu,"
           "\"final_beam_count\":%d,\"best_any\":",
           cand->id, idx, base_x[0], base_x[1], base_x[2],
           depth, beam_size, cap, policy, free_w57, part_weight, carry_weight,
           (unsigned long long)evals, beam_count);
    chart61_print_point(best_any.x, &best_any.e, best_any.score,
                        best_any.distance, best_any.depth);
    printf(",\"best_cap\":");
    if (have_cap) {
        chart61_print_point(best_cap.x, &best_cap.e, best_cap.score,
                            best_cap.distance, best_cap.depth);
    } else {
        printf("null");
    }
    printf(",\"best_exact\":");
    if (have_exact) {
        chart61_print_point(best_exact.x, &best_exact.e, best_exact.score,
                            best_exact.distance, best_exact.depth);
    } else {
        printf("null");
    }
    printf(",\"best_exact_cap\":");
    if (have_exact_cap) {
        chart61_print_point(best_exact_cap.x, &best_exact_cap.e,
                            best_exact_cap.score, best_exact_cap.distance,
                            best_exact_cap.depth);
    } else {
        printf("null");
    }
    printf("}\n");

    free(beam);
    free(next);
}

static void pair61_residual_point(int idx, const uint32_t x[3], int cap) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (cap < 0) cap = 0;
    if (cap > 8) cap = 8;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"pair61residualpoint\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[64], cols61[64];
    uint64_t cols_pair[64];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns(&p1, &p2, x, &d60, &d61, cols60, cols61, cols_pair);
    int rank_pair = rank64_vectors(cols_pair, 64);

    int residual_count_by_hw[17];
    int solvable_by_hw[17];
    memset(residual_count_by_hw, 0, sizeof(residual_count_by_hw));
    memset(solvable_by_hw, 0, sizeof(solvable_by_hw));

    int solvable = 0;
    int min_delta_hw = 99;
    uint32_t min_delta_residual = 0;
    uint64_t min_delta = 0;
    uint32_t min_delta_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t min_delta_eval;
    memset(&min_delta_eval, 0, sizeof(min_delta_eval));

    int have_best_actual = 0;
    uint32_t best_actual_residual = 0;
    uint64_t best_actual_delta = 0;
    uint32_t best_actual_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t best_actual_eval;
    memset(&best_actual_eval, 0, sizeof(best_actual_eval));

    int have_best_cap = 0;
    uint32_t best_cap_residual = 0;
    uint64_t best_cap_delta = 0;
    uint32_t best_cap_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t best_cap_eval;
    memset(&best_cap_eval, 0, sizeof(best_cap_eval));

    int have_best_exact_cap = 0;
    uint32_t best_exact_cap_residual = 0;
    uint64_t best_exact_cap_delta = 0;
    uint32_t best_exact_cap_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t best_exact_cap_eval;
    memset(&best_exact_cap_eval, 0, sizeof(best_exact_cap_eval));

    for (int k = 0; k <= cap; k++) {
        uint64_t combo = (k == 0) ? 0ULL : ((1ULL << k) - 1ULL);
        while (1) {
            uint32_t residual = (uint32_t)combo;
            uint64_t target = ((uint64_t)(d61 ^ residual) << 32) | d60;
            uint64_t delta = 0;
            int rank = 0;
            residual_count_by_hw[k]++;
            int ok = solve_linear_columns64(target, cols_pair, 64, &delta, &rank);
            if (ok) {
                uint32_t y[3];
                frontier61_eval_t e;
                int dhw = hw32((uint32_t)delta) + hw32((uint32_t)(delta >> 32));
                apply_delta58_59(x, delta, y);
                frontier61_eval_point(&p1, &p2, y, 1, &e);
                solvable++;
                solvable_by_hw[k]++;

                if (dhw < min_delta_hw ||
                    (dhw == min_delta_hw && residual < min_delta_residual)) {
                    min_delta_hw = dhw;
                    min_delta_residual = residual;
                    min_delta = delta;
                    memcpy(min_delta_x, y, sizeof(min_delta_x));
                    min_delta_eval = e;
                }
                if (!have_best_actual ||
                    capped61_eval_better(&e, &best_actual_eval, cap)) {
                    have_best_actual = 1;
                    best_actual_residual = residual;
                    best_actual_delta = delta;
                    memcpy(best_actual_x, y, sizeof(best_actual_x));
                    best_actual_eval = e;
                }
                if (e.d61_hw <= cap &&
                    (!have_best_cap ||
                     capped61_eval_better(&e, &best_cap_eval, cap))) {
                    have_best_cap = 1;
                    best_cap_residual = residual;
                    best_cap_delta = delta;
                    memcpy(best_cap_x, y, sizeof(best_cap_x));
                    best_cap_eval = e;
                }
                if (e.defects[3] == 0 && e.d61_hw <= cap &&
                    (!have_best_exact_cap ||
                     e.d61_hw < best_exact_cap_eval.d61_hw ||
                     (e.d61_hw == best_exact_cap_eval.d61_hw &&
                      e.tail_hw < best_exact_cap_eval.tail_hw))) {
                    have_best_exact_cap = 1;
                    best_exact_cap_residual = residual;
                    best_exact_cap_delta = delta;
                    memcpy(best_exact_cap_x, y, sizeof(best_exact_cap_x));
                    best_exact_cap_eval = e;
                }
            }

            if (k == 0) break;
            uint64_t next = next_combination64(combo);
            if (!next || next < combo || next >= (1ULL << 32)) break;
            combo = next;
        }
    }

    frontier61_eval_t base_eval;
    frontier61_eval_point(&p1, &p2, x, 1, &base_eval);

    printf("{\"mode\":\"pair61residualpoint\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"cap\":%d,\"rank_pair\":%d,"
           "\"base_d60\":\"0x%08x\",\"base_d60_hw\":%d,"
           "\"base_d61\":\"0x%08x\",\"base_d61_hw\":%d,"
           "\"solvable\":%d,"
           "\"residual_count_by_hw\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"solvable_by_hw\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"min_delta_hw\":%d,\"min_delta_residual\":\"0x%08x\","
           "\"min_delta\":\"0x%016llx\",\"min_delta_point\":",
           cand->id, idx, x[0], x[1], x[2], cap, rank_pair,
           d60, hw32(d60), d61, hw32(d61), solvable,
           residual_count_by_hw[0], residual_count_by_hw[1],
           residual_count_by_hw[2], residual_count_by_hw[3],
           residual_count_by_hw[4], residual_count_by_hw[5],
           residual_count_by_hw[6], residual_count_by_hw[7],
           residual_count_by_hw[8], residual_count_by_hw[9],
           residual_count_by_hw[10], residual_count_by_hw[11],
           residual_count_by_hw[12], residual_count_by_hw[13],
           residual_count_by_hw[14], residual_count_by_hw[15],
           residual_count_by_hw[16],
           solvable_by_hw[0], solvable_by_hw[1], solvable_by_hw[2],
           solvable_by_hw[3], solvable_by_hw[4], solvable_by_hw[5],
           solvable_by_hw[6], solvable_by_hw[7], solvable_by_hw[8],
           solvable_by_hw[9], solvable_by_hw[10], solvable_by_hw[11],
           solvable_by_hw[12], solvable_by_hw[13], solvable_by_hw[14],
           solvable_by_hw[15], solvable_by_hw[16],
           min_delta_hw, min_delta_residual, (unsigned long long)min_delta);
    if (solvable) {
        ridge61_print_point(min_delta_x, &min_delta_eval,
                            min_delta_eval.d60_hw * 64 + min_delta_eval.d61_hw,
                            min_delta_hw, 0, min_delta_eval.tail_hw);
    } else {
        printf("null");
    }
    printf(",\"best_actual\":");
    if (have_best_actual) {
        printf("{\"linear_residual\":\"0x%08x\",\"delta\":\"0x%016llx\",\"delta_hw\":%d,\"point\":",
               best_actual_residual, (unsigned long long)best_actual_delta,
               hw32((uint32_t)best_actual_delta) +
               hw32((uint32_t)(best_actual_delta >> 32)));
        ridge61_print_point(best_actual_x, &best_actual_eval,
                            best_actual_eval.d60_hw * 64 + best_actual_eval.d61_hw,
                            hw32((uint32_t)best_actual_delta) +
                            hw32((uint32_t)(best_actual_delta >> 32)),
                            0, best_actual_eval.tail_hw);
        printf("}");
    } else {
        printf("null");
    }
    printf(",\"best_cap\":");
    if (have_best_cap) {
        printf("{\"linear_residual\":\"0x%08x\",\"delta\":\"0x%016llx\",\"delta_hw\":%d,\"point\":",
               best_cap_residual, (unsigned long long)best_cap_delta,
               hw32((uint32_t)best_cap_delta) +
               hw32((uint32_t)(best_cap_delta >> 32)));
        ridge61_print_point(best_cap_x, &best_cap_eval,
                            best_cap_eval.d60_hw * 64 + best_cap_eval.d61_hw,
                            hw32((uint32_t)best_cap_delta) +
                            hw32((uint32_t)(best_cap_delta >> 32)),
                            0, best_cap_eval.tail_hw);
        printf("}");
    } else {
        printf("null");
    }
    printf(",\"best_exact_cap\":");
    if (have_best_exact_cap) {
        printf("{\"linear_residual\":\"0x%08x\",\"delta\":\"0x%016llx\",\"delta_hw\":%d,\"point\":",
               best_exact_cap_residual, (unsigned long long)best_exact_cap_delta,
               hw32((uint32_t)best_exact_cap_delta) +
               hw32((uint32_t)(best_exact_cap_delta >> 32)));
        ridge61_print_point(best_exact_cap_x, &best_exact_cap_eval,
                            best_exact_cap_eval.d60_hw * 64 + best_exact_cap_eval.d61_hw,
                            hw32((uint32_t)best_exact_cap_delta) +
                            hw32((uint32_t)(best_exact_cap_delta >> 32)),
                            0, best_exact_cap_eval.tail_hw);
        printf("}");
    } else {
        printf("null");
    }
    printf("}\n");
}

static void pair61_residual_fiber_point(int idx, const uint32_t x[3],
                                        int cap, int max_kernel_dim) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }
    if (cap < 0) cap = 0;
    if (cap > 8) cap = 8;
    if (max_kernel_dim < 0) max_kernel_dim = 0;
    if (max_kernel_dim > 24) max_kernel_dim = 24;

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"pair61residualfiber\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    uint32_t cols60[64], cols61[64];
    uint64_t cols_pair[64];
    uint32_t d60 = 0, d61 = 0;
    defect60_61_columns(&p1, &p2, x, &d60, &d61, cols60, cols61, cols_pair);

    uint64_t kernel[64];
    int rank_pair = 0;
    int kernel_dim = kernel_basis_columns64(cols_pair, 64, kernel, &rank_pair);
    int enum_dim = kernel_dim;
    if (enum_dim > max_kernel_dim) enum_dim = max_kernel_dim;
    uint64_t enum_count = (enum_dim >= 64) ? 0 : (1ULL << enum_dim);

    int residual_count_by_hw[17];
    int solvable_by_hw[17];
    memset(residual_count_by_hw, 0, sizeof(residual_count_by_hw));
    memset(solvable_by_hw, 0, sizeof(solvable_by_hw));

    uint64_t linear_targets = 0;
    uint64_t solvable_targets = 0;
    uint64_t representatives = 0;
    uint64_t exact60_representatives = 0;
    uint64_t cap_representatives = 0;
    uint64_t exact_cap_representatives = 0;

    int have_best_actual = 0;
    uint32_t best_actual_residual = 0;
    uint64_t best_actual_delta = 0;
    uint32_t best_actual_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t best_actual_eval;
    memset(&best_actual_eval, 0, sizeof(best_actual_eval));

    int have_best_cap = 0;
    uint32_t best_cap_residual = 0;
    uint64_t best_cap_delta = 0;
    uint32_t best_cap_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t best_cap_eval;
    memset(&best_cap_eval, 0, sizeof(best_cap_eval));

    int have_best_exact = 0;
    uint32_t best_exact_residual = 0;
    uint64_t best_exact_delta = 0;
    uint32_t best_exact_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t best_exact_eval;
    memset(&best_exact_eval, 0, sizeof(best_exact_eval));

    int have_best_exact_cap = 0;
    uint32_t best_exact_cap_residual = 0;
    uint64_t best_exact_cap_delta = 0;
    uint32_t best_exact_cap_x[3] = {x[0], x[1], x[2]};
    frontier61_eval_t best_exact_cap_eval;
    memset(&best_exact_cap_eval, 0, sizeof(best_exact_cap_eval));

    for (int k = 0; k <= cap; k++) {
        uint64_t combo = (k == 0) ? 0ULL : ((1ULL << k) - 1ULL);
        while (1) {
            uint32_t residual = (uint32_t)combo;
            uint64_t target = ((uint64_t)(d61 ^ residual) << 32) | d60;
            uint64_t particular = 0;
            int rank = 0;
            linear_targets++;
            residual_count_by_hw[k]++;
            int ok = solve_linear_columns64(target, cols_pair, 64,
                                            &particular, &rank);
            if (ok) {
                solvable_targets++;
                solvable_by_hw[k]++;
                for (uint64_t sel = 0; sel < enum_count; sel++) {
                    uint64_t delta = particular ^ combine_kernel_selection(sel, kernel);
                    uint32_t y[3];
                    frontier61_eval_t e;
                    apply_delta58_59(x, delta, y);
                    frontier61_eval_point(&p1, &p2, y, 1, &e);
                    representatives++;

                    if (e.d61_hw <= cap) cap_representatives++;
                    if (e.defects[3] == 0) exact60_representatives++;
                    if (e.defects[3] == 0 && e.d61_hw <= cap) {
                        exact_cap_representatives++;
                    }

                    if (!have_best_actual ||
                        capped61_eval_better(&e, &best_actual_eval, cap)) {
                        have_best_actual = 1;
                        best_actual_residual = residual;
                        best_actual_delta = delta;
                        memcpy(best_actual_x, y, sizeof(best_actual_x));
                        best_actual_eval = e;
                    }
                    if (e.d61_hw <= cap &&
                        (!have_best_cap ||
                         capped61_eval_better(&e, &best_cap_eval, cap))) {
                        have_best_cap = 1;
                        best_cap_residual = residual;
                        best_cap_delta = delta;
                        memcpy(best_cap_x, y, sizeof(best_cap_x));
                        best_cap_eval = e;
                    }
                    if (e.defects[3] == 0 &&
                        (!have_best_exact ||
                         e.d61_hw < best_exact_eval.d61_hw ||
                         (e.d61_hw == best_exact_eval.d61_hw &&
                          e.tail_hw < best_exact_eval.tail_hw))) {
                        have_best_exact = 1;
                        best_exact_residual = residual;
                        best_exact_delta = delta;
                        memcpy(best_exact_x, y, sizeof(best_exact_x));
                        best_exact_eval = e;
                    }
                    if (e.defects[3] == 0 && e.d61_hw <= cap &&
                        (!have_best_exact_cap ||
                         e.d61_hw < best_exact_cap_eval.d61_hw ||
                         (e.d61_hw == best_exact_cap_eval.d61_hw &&
                          e.tail_hw < best_exact_cap_eval.tail_hw))) {
                        have_best_exact_cap = 1;
                        best_exact_cap_residual = residual;
                        best_exact_cap_delta = delta;
                        memcpy(best_exact_cap_x, y, sizeof(best_exact_cap_x));
                        best_exact_cap_eval = e;
                    }
                }
            }

            if (k == 0) break;
            uint64_t next = next_combination64(combo);
            if (!next || next < combo || next >= (1ULL << 32)) break;
            combo = next;
        }
    }

    frontier61_eval_t base_eval;
    frontier61_eval_point(&p1, &p2, x, 1, &base_eval);

    printf("{\"mode\":\"pair61residualfiber\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"x\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"cap\":%d,\"rank_pair\":%d,\"kernel_dim\":%d,"
           "\"enum_dim\":%d,\"enum_count\":%llu,"
           "\"base_d60\":\"0x%08x\",\"base_d60_hw\":%d,"
           "\"base_d61\":\"0x%08x\",\"base_d61_hw\":%d,"
           "\"linear_targets\":%llu,\"solvable_targets\":%llu,"
           "\"representatives\":%llu,\"exact60_representatives\":%llu,"
           "\"cap_representatives\":%llu,\"exact_cap_representatives\":%llu,"
           "\"residual_count_by_hw\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"solvable_by_hw\":[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d],"
           "\"base_point\":",
           cand->id, idx, x[0], x[1], x[2],
           cap, rank_pair, kernel_dim, enum_dim,
           (unsigned long long)enum_count,
           d60, hw32(d60), d61, hw32(d61),
           (unsigned long long)linear_targets,
           (unsigned long long)solvable_targets,
           (unsigned long long)representatives,
           (unsigned long long)exact60_representatives,
           (unsigned long long)cap_representatives,
           (unsigned long long)exact_cap_representatives,
           residual_count_by_hw[0], residual_count_by_hw[1],
           residual_count_by_hw[2], residual_count_by_hw[3],
           residual_count_by_hw[4], residual_count_by_hw[5],
           residual_count_by_hw[6], residual_count_by_hw[7],
           residual_count_by_hw[8], residual_count_by_hw[9],
           residual_count_by_hw[10], residual_count_by_hw[11],
           residual_count_by_hw[12], residual_count_by_hw[13],
           residual_count_by_hw[14], residual_count_by_hw[15],
           residual_count_by_hw[16],
           solvable_by_hw[0], solvable_by_hw[1],
           solvable_by_hw[2], solvable_by_hw[3],
           solvable_by_hw[4], solvable_by_hw[5],
           solvable_by_hw[6], solvable_by_hw[7],
           solvable_by_hw[8], solvable_by_hw[9],
           solvable_by_hw[10], solvable_by_hw[11],
           solvable_by_hw[12], solvable_by_hw[13],
           solvable_by_hw[14], solvable_by_hw[15],
           solvable_by_hw[16]);
    ridge61_print_point(x, &base_eval,
                        base_eval.d60_hw * 64 + base_eval.d61_hw,
                        0, 0, base_eval.tail_hw);
    printf(",\"best_actual\":");
    if (have_best_actual) {
        printf("{\"linear_residual\":\"0x%08x\",\"delta\":\"0x%016llx\",\"delta_hw\":%d,\"point\":",
               best_actual_residual, (unsigned long long)best_actual_delta,
               hw32((uint32_t)best_actual_delta) +
               hw32((uint32_t)(best_actual_delta >> 32)));
        ridge61_print_point(best_actual_x, &best_actual_eval,
                            best_actual_eval.d60_hw * 64 + best_actual_eval.d61_hw,
                            hw32((uint32_t)best_actual_delta) +
                            hw32((uint32_t)(best_actual_delta >> 32)),
                            0, best_actual_eval.tail_hw);
        printf("}");
    } else {
        printf("null");
    }
    printf(",\"best_cap\":");
    if (have_best_cap) {
        printf("{\"linear_residual\":\"0x%08x\",\"delta\":\"0x%016llx\",\"delta_hw\":%d,\"point\":",
               best_cap_residual, (unsigned long long)best_cap_delta,
               hw32((uint32_t)best_cap_delta) +
               hw32((uint32_t)(best_cap_delta >> 32)));
        ridge61_print_point(best_cap_x, &best_cap_eval,
                            best_cap_eval.d60_hw * 64 + best_cap_eval.d61_hw,
                            hw32((uint32_t)best_cap_delta) +
                            hw32((uint32_t)(best_cap_delta >> 32)),
                            0, best_cap_eval.tail_hw);
        printf("}");
    } else {
        printf("null");
    }
    printf(",\"best_exact\":");
    if (have_best_exact) {
        printf("{\"linear_residual\":\"0x%08x\",\"delta\":\"0x%016llx\",\"delta_hw\":%d,\"point\":",
               best_exact_residual, (unsigned long long)best_exact_delta,
               hw32((uint32_t)best_exact_delta) +
               hw32((uint32_t)(best_exact_delta >> 32)));
        ridge61_print_point(best_exact_x, &best_exact_eval,
                            best_exact_eval.d60_hw * 64 + best_exact_eval.d61_hw,
                            hw32((uint32_t)best_exact_delta) +
                            hw32((uint32_t)(best_exact_delta >> 32)),
                            0, best_exact_eval.tail_hw);
        printf("}");
    } else {
        printf("null");
    }
    printf(",\"best_exact_cap\":");
    if (have_best_exact_cap) {
        printf("{\"linear_residual\":\"0x%08x\",\"delta\":\"0x%016llx\",\"delta_hw\":%d,\"point\":",
               best_exact_cap_residual, (unsigned long long)best_exact_cap_delta,
               hw32((uint32_t)best_exact_cap_delta) +
               hw32((uint32_t)(best_exact_cap_delta >> 32)));
        ridge61_print_point(best_exact_cap_x, &best_exact_cap_eval,
                            best_exact_cap_eval.d60_hw * 64 + best_exact_cap_eval.d61_hw,
                            hw32((uint32_t)best_exact_cap_delta) +
                            hw32((uint32_t)(best_exact_cap_delta >> 32)),
                            0, best_exact_cap_eval.tail_hw);
        printf("}");
    } else {
        printf("null");
    }
    printf("}\n");
}

static void carrycmp61_print_round(const tail_trace_t *a,
                                   const tail_trace_t *b,
                                   int r_index) {
    printf("{\"sched_a\":\"0x%08x\",\"req_a\":\"0x%08x\","
           "\"defect_a\":\"0x%08x\","
           "\"sched_b\":\"0x%08x\",\"req_b\":\"0x%08x\","
           "\"defect_b\":\"0x%08x\","
           "\"sched_xor_hw\":%d,\"req_xor_hw\":%d,\"defect_xor_hw\":%d,"
           "\"parts_a\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"parts_b\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"parts_xor_hw\":[%d,%d,%d,%d],"
           "\"carries_a\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"carries_b\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"carry_xor_hw\":[%d,%d,%d],"
           "\"pairdiff_xor_hw\":[%d,%d,%d,%d,%d,%d,%d,%d]}",
           a->w2[r_index] - a->w1[r_index], a->offsets[r_index],
           a->defects[r_index],
           b->w2[r_index] - b->w1[r_index], b->offsets[r_index],
           b->defects[r_index],
           hw32((a->w2[r_index] - a->w1[r_index]) ^
                (b->w2[r_index] - b->w1[r_index])),
           hw32(a->offsets[r_index] ^ b->offsets[r_index]),
           hw32(a->defects[r_index] ^ b->defects[r_index]),
           a->parts[r_index][0], a->parts[r_index][1],
           a->parts[r_index][2], a->parts[r_index][3],
           b->parts[r_index][0], b->parts[r_index][1],
           b->parts[r_index][2], b->parts[r_index][3],
           hw32(a->parts[r_index][0] ^ b->parts[r_index][0]),
           hw32(a->parts[r_index][1] ^ b->parts[r_index][1]),
           hw32(a->parts[r_index][2] ^ b->parts[r_index][2]),
           hw32(a->parts[r_index][3] ^ b->parts[r_index][3]),
           a->carries[r_index][0], a->carries[r_index][1],
           a->carries[r_index][2],
           b->carries[r_index][0], b->carries[r_index][1],
           b->carries[r_index][2],
           hw32(a->carries[r_index][0] ^ b->carries[r_index][0]),
           hw32(a->carries[r_index][1] ^ b->carries[r_index][1]),
           hw32(a->carries[r_index][2] ^ b->carries[r_index][2]),
           hw32(a->pairdiff[r_index][0] ^ b->pairdiff[r_index][0]),
           hw32(a->pairdiff[r_index][1] ^ b->pairdiff[r_index][1]),
           hw32(a->pairdiff[r_index][2] ^ b->pairdiff[r_index][2]),
           hw32(a->pairdiff[r_index][3] ^ b->pairdiff[r_index][3]),
           hw32(a->pairdiff[r_index][4] ^ b->pairdiff[r_index][4]),
           hw32(a->pairdiff[r_index][5] ^ b->pairdiff[r_index][5]),
           hw32(a->pairdiff[r_index][6] ^ b->pairdiff[r_index][6]),
           hw32(a->pairdiff[r_index][7] ^ b->pairdiff[r_index][7]));
}

static void carrycmp61_point(int idx, const uint32_t xa[3],
                             const uint32_t xb[3]) {
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        exit(2);
    }

    const candidate_t *cand = &CANDIDATES[idx];
    sha256_precomp_t p1, p2;
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"carrycmp61point\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return;
    }

    tail_trace_t a, b;
    tail_trace_for_x(&p1, &p2, xa, &a);
    tail_trace_for_x(&p1, &p2, xb, &b);

    uint32_t off58_a = 0, off58_b = 0;
    uint32_t off59_a = compute_off59_for_w57_w58(&p1, &p2, xa[0], xa[1],
                                                 &off58_a);
    uint32_t off59_b = compute_off59_for_w57_w58(&p1, &p2, xb[0], xb[1],
                                                 &off58_b);
    int dist = hw32(xa[1] ^ xb[1]) + hw32(xa[2] ^ xb[2]);

    printf("{\"mode\":\"carrycmp61point\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"x_a\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"x_b\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"distance58_59\":%d,"
           "\"off58_a\":\"0x%08x\",\"off58_b\":\"0x%08x\","
           "\"off58_xor_hw\":%d,"
           "\"off59_a\":\"0x%08x\",\"off59_b\":\"0x%08x\","
           "\"off59_xor_hw\":%d,"
           "\"defects_a\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"defects_b\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"tail_defect_hw_a\":%d,\"tail_defect_hw_b\":%d,"
           "\"round60\":",
           cand->id, idx,
           xa[0], xa[1], xa[2],
           xb[0], xb[1], xb[2],
           dist,
           off58_a, off58_b, hw32(off58_a ^ off58_b),
           off59_a, off59_b, hw32(off59_a ^ off59_b),
           a.defects[0], a.defects[1], a.defects[2], a.defects[3],
           a.defects[4], a.defects[5], a.defects[6],
           b.defects[0], b.defects[1], b.defects[2], b.defects[3],
           b.defects[4], b.defects[5], b.defects[6],
           hw32(a.defects[4]) + hw32(a.defects[5]) + hw32(a.defects[6]),
           hw32(b.defects[4]) + hw32(b.defects[5]) + hw32(b.defects[6]));
    carrycmp61_print_round(&a, &b, 3);
    printf(",\"round61\":");
    carrycmp61_print_round(&a, &b, 4);
    printf("}\n");
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
    if (argc >= 2 && strcmp(argv[1], "msg61point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t words[MSG_FREE_WORDS];
        uint32_t *maybe_words = NULL;
        if (argc >= 3 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                words[i] = (uint32_t)strtoul(argv[3 + i], NULL, 0);
            }
            maybe_words = words;
        }
        sha256_init(32);
        msg61_point_candidate(idx, maybe_words);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61rank") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        sha256_init(32);
        msg61_rank_candidate(idx);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61sample") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        long long samples = (argc >= 4) ? strtoll(argv[3], NULL, 0) : 1048576LL;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int random_words = (argc >= 6) ? atoi(argv[5]) : 1;
        sha256_init(32);
        msg61_sample_candidate(idx, samples, threads, random_words);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61walk") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        long long trials = (argc >= 4) ? strtoll(argv[3], NULL, 0) : 1048576LL;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int max_passes = (argc >= 6) ? atoi(argv[5]) : 128;
        int start_flips = (argc >= 7) ? atoi(argv[6]) : 32;
        int random_words = (argc >= 8) ? atoi(argv[7]) : 0;
        int objective_prefix = (argc >= 9) ? atoi(argv[8]) : MSG_DEFECT_ROUNDS;
        uint32_t seed_words[MSG_FREE_WORDS];
        uint32_t *maybe_seed = NULL;
        if (argc >= 9 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                seed_words[i] = (uint32_t)strtoul(argv[9 + i], NULL, 0);
            }
            maybe_seed = seed_words;
        }
        sha256_init(32);
        msg61_walk_candidate(idx, trials, threads, max_passes,
                             start_flips, random_words, objective_prefix,
                             maybe_seed);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61newton") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        int restarts = (argc >= 4) ? atoi(argv[3]) : 128;
        int max_iters = (argc >= 5) ? atoi(argv[4]) : 12;
        int jitter_flips = (argc >= 6) ? atoi(argv[5]) : 64;
        int threads = (argc >= 7) ? atoi(argv[6]) : 8;
        int solve_prefix = (argc >= 8) ? atoi(argv[7]) : MSG_DEFECT_ROUNDS;
        sha256_init(32);
        msg61_newton_candidate(idx, restarts, max_iters, jitter_flips,
                               threads, solve_prefix);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61guardneigh") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        int max_k = (argc >= 4) ? atoi(argv[3]) : 2;
        uint32_t seed_words[MSG_FREE_WORDS];
        uint32_t *maybe_seed = NULL;
        if (argc >= 4 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                seed_words[i] = (uint32_t)strtoul(argv[4 + i], NULL, 0);
            }
            maybe_seed = seed_words;
        }
        sha256_init(32);
        msg61_guard_neigh_candidate(idx, max_k, maybe_seed);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61guardrepair") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        long long trials = (argc >= 4) ? strtoll(argv[3], NULL, 0) : 65536LL;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int max_iters = (argc >= 6) ? atoi(argv[5]) : 8;
        int jitter_flips = (argc >= 7) ? atoi(argv[6]) : 64;
        uint32_t seed_words[MSG_FREE_WORDS];
        uint32_t *maybe_seed = NULL;
        if (argc >= 7 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                seed_words[i] = (uint32_t)strtoul(argv[7 + i], NULL, 0);
            }
            maybe_seed = seed_words;
        }
        sha256_init(32);
        msg61_guard_repair_candidate(idx, trials, threads, max_iters,
                                     jitter_flips, 0, maybe_seed);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61guardrepairgauge") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        long long trials = (argc >= 4) ? strtoll(argv[3], NULL, 0) : 65536LL;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int max_iters = (argc >= 6) ? atoi(argv[5]) : 8;
        int jitter_flips = (argc >= 7) ? atoi(argv[6]) : 64;
        int gauge_flips = (argc >= 8) ? atoi(argv[7]) : 16;
        uint32_t seed_words[MSG_FREE_WORDS];
        uint32_t *maybe_seed = NULL;
        if (argc >= 8 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                seed_words[i] = (uint32_t)strtoul(argv[8 + i], NULL, 0);
            }
            maybe_seed = seed_words;
        }
        sha256_init(32);
        msg61_guard_repair_candidate(idx, trials, threads, max_iters,
                                     jitter_flips, gauge_flips, maybe_seed);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61guardkernel") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        long long trials = (argc >= 4) ? strtoll(argv[3], NULL, 0) : 65536LL;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int drive_flips = (argc >= 6) ? atoi(argv[5]) : 64;
        uint32_t seed_words[MSG_FREE_WORDS];
        uint32_t *maybe_seed = NULL;
        if (argc >= 6 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                seed_words[i] = (uint32_t)strtoul(argv[6 + i], NULL, 0);
            }
            maybe_seed = seed_words;
        }
        sha256_init(32);
        msg61_guard_kernel_candidate(idx, trials, threads, drive_flips,
                                     maybe_seed);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61guardwordrepair") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        long long trials = (argc >= 4) ? strtoll(argv[3], NULL, 0) : 65536LL;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int repair_word = (argc >= 6) ? atoi(argv[5]) : 13;
        int max_iters = (argc >= 7) ? atoi(argv[6]) : 8;
        int random_words = (argc >= 8) ? atoi(argv[7]) : 1;
        int jitter_flips = (argc >= 9) ? atoi(argv[8]) : 64;
        uint32_t seed_words[MSG_FREE_WORDS];
        uint32_t *maybe_seed = NULL;
        if (argc >= 9 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                seed_words[i] = (uint32_t)strtoul(argv[9 + i], NULL, 0);
            }
            maybe_seed = seed_words;
        }
        sha256_init(32);
        msg61_guard_word_repair_candidate(idx, trials, threads, repair_word,
                                          max_iters, random_words, jitter_flips,
                                          maybe_seed);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "msg61guardchartrepair") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        long long trials = (argc >= 4) ? strtoll(argv[3], NULL, 0) : 65536LL;
        int threads = (argc >= 5) ? atoi(argv[4]) : 8;
        int max_iters = (argc >= 6) ? atoi(argv[5]) : 8;
        int random_words = (argc >= 7) ? atoi(argv[6]) : 0;
        int jitter_flips = (argc >= 8) ? atoi(argv[7]) : 64;
        uint32_t seed_words[MSG_FREE_WORDS];
        uint32_t *maybe_seed = NULL;
        if (argc >= 8 + MSG_FREE_WORDS) {
            for (int i = 0; i < MSG_FREE_WORDS; i++) {
                seed_words[i] = (uint32_t)strtoul(argv[8 + i], NULL, 0);
            }
            maybe_seed = seed_words;
        }
        sha256_init(32);
        msg61_guard_chart_repair_candidate(idx, trials, threads, max_iters,
                                           random_words, jitter_flips,
                                           maybe_seed);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "carrycmp61point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t xa[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        uint32_t xb[3] = {
            (argc >= 7) ? (uint32_t)strtoul(argv[6], NULL, 0) : 0,
            (argc >= 8) ? (uint32_t)strtoul(argv[7], NULL, 0) : 0,
            (argc >= 9) ? (uint32_t)strtoul(argv[8], NULL, 0) : 0,
        };
        sha256_init(32);
        carrycmp61_point(idx, xa, xb);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "pair61residualpoint") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int cap = (argc >= 7) ? atoi(argv[6]) : 3;
        sha256_init(32);
        pair61_residual_point(idx, x, cap);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "pair61residualfiber") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int cap = (argc >= 7) ? atoi(argv[6]) : 4;
        int max_kernel_dim = (argc >= 8) ? atoi(argv[7]) : 20;
        sha256_init(32);
        pair61_residual_fiber_point(idx, x, cap, max_kernel_dim);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "off58neighbors") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t base_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        int max_k = (argc >= 5) ? atoi(argv[4]) : 5;
        sha256_init(32);
        off58_neighborhood_candidate(idx, base_w57, max_k);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "capped61walk") == 0) {
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
        int cap = (argc >= 11) ? atoi(argv[10]) : 3;
        sha256_init(32);
        capped61_walk_candidate(idx, x, trials, threads,
                                max_passes, max_flips, cap);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "chart61walk") == 0) {
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
        int cap = (argc >= 11) ? atoi(argv[10]) : 3;
        int policy = (argc >= 12) ? atoi(argv[11]) : 0;
        int part_weight = (argc >= 13) ? atoi(argv[12]) : 1;
        int carry_weight = (argc >= 14) ? atoi(argv[13]) : 1;
        int free_w57 = (argc >= 15) ? atoi(argv[14]) : 0;
        sha256_init(32);
        chart61_walk_candidate(idx, x, trials, threads,
                               max_passes, max_flips, cap,
                               policy, part_weight, carry_weight,
                               free_w57);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "d60repairfiber") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        long long samples = (argc >= 7) ? strtoll(argv[6], NULL, 0) : 1048576LL;
        int threads = (argc >= 8) ? atoi(argv[7]) : 8;
        int cap = (argc >= 9) ? atoi(argv[8]) : 4;
        int policy = (argc >= 10) ? atoi(argv[9]) : 0;
        int part_weight = (argc >= 11) ? atoi(argv[10]) : 1;
        int carry_weight = (argc >= 12) ? atoi(argv[11]) : 1;
        sha256_init(32);
        d60_repair_fiber_candidate(idx, x, samples, threads, cap,
                                   policy, part_weight, carry_weight,
                                   0, 0);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "d60repairfiberseq") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        uint64_t start = (argc >= 7) ? strtoull(argv[6], NULL, 0) : 0ULL;
        long long samples = (argc >= 8) ? strtoll(argv[7], NULL, 0) : 1048576LL;
        int threads = (argc >= 9) ? atoi(argv[8]) : 8;
        int cap = (argc >= 10) ? atoi(argv[9]) : 4;
        int policy = (argc >= 11) ? atoi(argv[10]) : 0;
        int part_weight = (argc >= 12) ? atoi(argv[11]) : 1;
        int carry_weight = (argc >= 13) ? atoi(argv[12]) : 1;
        sha256_init(32);
        d60_repair_fiber_candidate(idx, x, samples, threads, cap,
                                   policy, part_weight, carry_weight,
                                   1, start);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "d60repairfiber96") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        long long samples = (argc >= 7) ? strtoll(argv[6], NULL, 0) : 1048576LL;
        int threads = (argc >= 8) ? atoi(argv[7]) : 8;
        int cap = (argc >= 9) ? atoi(argv[8]) : 4;
        int policy = (argc >= 10) ? atoi(argv[9]) : 2;
        int part_weight = (argc >= 11) ? atoi(argv[10]) : 1;
        int carry_weight = (argc >= 12) ? atoi(argv[11]) : 1;
        sha256_init(32);
        d60_repair_fiber96_candidate(idx, x, samples, threads, cap,
                                     policy, part_weight, carry_weight);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "d60repairfiber96low") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_k = (argc >= 7) ? atoi(argv[6]) : 4;
        int cap = (argc >= 8) ? atoi(argv[7]) : 4;
        int policy = (argc >= 9) ? atoi(argv[8]) : 2;
        int part_weight = (argc >= 10) ? atoi(argv[9]) : 1;
        int carry_weight = (argc >= 11) ? atoi(argv[10]) : 1;
        sha256_init(32);
        d60_repair_fiber96_low_candidate(idx, x, max_k, cap, policy,
                                         part_weight, carry_weight);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "chart61pairdescent") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_passes = (argc >= 7) ? atoi(argv[6]) : 32;
        int max_k = (argc >= 8) ? atoi(argv[7]) : 2;
        int cap = (argc >= 9) ? atoi(argv[8]) : 4;
        int policy = (argc >= 10) ? atoi(argv[9]) : 0;
        int part_weight = (argc >= 11) ? atoi(argv[10]) : 1;
        int carry_weight = (argc >= 12) ? atoi(argv[11]) : 1;
        sha256_init(32);
        chart61_pair_descent_candidate(idx, x, max_passes, max_k, cap,
                                       policy, part_weight, carry_weight);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "chart61beam") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int depth = (argc >= 7) ? atoi(argv[6]) : 16;
        int beam_size = (argc >= 8) ? atoi(argv[7]) : 2048;
        int cap = (argc >= 9) ? atoi(argv[8]) : 4;
        int policy = (argc >= 10) ? atoi(argv[9]) : 0;
        int part_weight = (argc >= 11) ? atoi(argv[10]) : 1;
        int carry_weight = (argc >= 12) ? atoi(argv[11]) : 1;
        int free_w57 = (argc >= 13) ? atoi(argv[12]) : 0;
        sha256_init(32);
        chart61_beam_candidate(idx, x, depth, beam_size, cap, policy,
                               part_weight, carry_weight, free_w57);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "ridge61walk") == 0) {
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
        int weight = (argc >= 11) ? atoi(argv[10]) : 8;
        sha256_init(32);
        ridge61_walk_candidate(idx, x, trials, threads,
                               max_passes, max_flips, weight);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "nearexact61point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t x[3] = {
            (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0,
            (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0,
            (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0,
        };
        int max_k = (argc >= 7) ? atoi(argv[6]) : 5;
        sha256_init(32);
        nearexact61_point(idx, x, max_k);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "bridge61point") == 0) {
        int idx = (argc >= 3) ? atoi(argv[2]) : 0;
        uint32_t fixed_w57 = (argc >= 4) ? (uint32_t)strtoul(argv[3], NULL, 0) : 0;
        uint32_t w58_a = (argc >= 5) ? (uint32_t)strtoul(argv[4], NULL, 0) : 0;
        uint32_t w59_a = (argc >= 6) ? (uint32_t)strtoul(argv[5], NULL, 0) : 0;
        uint32_t w58_b = (argc >= 7) ? (uint32_t)strtoul(argv[6], NULL, 0) : 0;
        uint32_t w59_b = (argc >= 8) ? (uint32_t)strtoul(argv[7], NULL, 0) : 0;
        int max_extra = (argc >= 9) ? atoi(argv[8]) : 0;
        sha256_init(32);
        bridge61_point(idx, fixed_w57, w58_a, w59_a,
                       w58_b, w59_b, max_extra);
        return 0;
    }

    if (argc >= 2 && strcmp(argv[1], "frontier61pool") == 0) {
        if (argc < 10 || ((argc - 7) % 3) != 0) {
            fprintf(stderr,
                    "usage: %s frontier61pool IDX TRIALS THREADS PASSES FLIPS "
                    "W57 W58 W59 [W57 W58 W59 ...]\n",
                    argv[0]);
            return 2;
        }
        int idx = atoi(argv[2]);
        int trials = atoi(argv[3]);
        int threads = atoi(argv[4]);
        int max_passes = atoi(argv[5]);
        int max_flips = atoi(argv[6]);
        int seed_count = (argc - 7) / 3;
        uint32_t *seeds = (uint32_t *)calloc((size_t)seed_count * 3, sizeof(uint32_t));
        if (!seeds) {
            fprintf(stderr, "seed allocation failed.\n");
            return 2;
        }
        for (int i = 0; i < seed_count; i++) {
            seeds[3 * i + 0] = (uint32_t)strtoul(argv[7 + 3 * i + 0], NULL, 0);
            seeds[3 * i + 1] = (uint32_t)strtoul(argv[7 + 3 * i + 1], NULL, 0);
            seeds[3 * i + 2] = (uint32_t)strtoul(argv[7 + 3 * i + 2], NULL, 0);
        }
        sha256_init(32);
        frontier61_pool_candidate(idx, seeds, seed_count,
                                  trials, threads, max_passes, max_flips);
        free(seeds);
        return 0;
    }

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
        int free_w57 = (argc >= 11) ? atoi(argv[10]) : 0;
        sha256_init(32);
        surface61_greedy_walk_candidate(idx, x, trials, threads,
                                        max_passes, max_flips, free_w57);
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
