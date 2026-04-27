/* block2_pareto_sampler.c - online HW/LM Pareto sampler for block2_wang.
 *
 * For a candidate (m0, fill, kernel bit), random-sample W1[57..60],
 * apply cascade-1 at rounds 57..60, schedule-extend through 63, then
 * measure:
 *   - final residual HW,
 *   - Lipmaa-Moriai cost across active adders in rounds 57..63,
 *   - exact a61=e61 symmetry, observed as final c63 == g63.
 *
 * The tool keeps a small Pareto frontier over (HW, LM) online instead of
 * saving only min-HW records. This is meant to hunt the F43 surface:
 * low-HW records, low-LM records, and exact-symmetry records can be
 * different objects.
 *
 * Compile:
 *   gcc -O3 -march=native -fopenmp -o /tmp/block2_pareto_sampler \
 *     headline_hunt/bets/block2_wang/trails/block2_pareto_sampler.c
 *
 * Run:
 *   /tmp/block2_pareto_sampler 0x39a03c2d 0xffffffff 4 100000000 24 0x1234
 *
 * Point check:
 *   /tmp/block2_pareto_sampler 0x39a03c2d 0xffffffff 4 0 1 0 \
 *     0x34cbddf6 0xa1d273cc 0x1adb0739 0x3dbf5ec7
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _OPENMP
#include <omp.h>
#endif

typedef uint32_t u32;

static inline u32 ROR(u32 x, int n) { return (x >> n) | (x << (32 - n)); }
static inline u32 Ch(u32 e, u32 f, u32 g) { return (e & f) ^ ((~e) & g); }
static inline u32 Maj(u32 a, u32 b, u32 c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline u32 Sigma0(u32 a) { return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22); }
static inline u32 Sigma1(u32 e) { return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25); }
static inline u32 sigma0_(u32 x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline u32 sigma1_(u32 x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }
static inline int popcnt(u32 x) { return __builtin_popcount(x); }

static const u32 K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

static const u32 IV[8] = {
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
};

typedef struct {
    u32 W1_pre[64], W2_pre[64];
    u32 s1_pre[8], s2_pre[8];
} ctx_t;

typedef struct {
    int active;
    u32 alpha, beta, gamma;
    int lm_cost;
} adder_info_t;

typedef struct {
    int valid;
    int hw, lm, active, incompat, sym;
    u32 W[4];
    u32 diff[8];
} rec_t;

#define FRONT_CAP 128

typedef struct {
    rec_t front[FRONT_CAP];
    int nfront;
    rec_t best_hw;
    rec_t best_lm;
    rec_t best_sym_lm;
    uint64_t sym_count;
    uint64_t incompat_count;
} stats_t;

static inline u32 cw1(const u32 s1[8], const u32 s2[8]) {
    return (s1[7] - s2[7]) + (Sigma1(s1[4]) - Sigma1(s2[4]))
         + (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6]))
         + (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]))
         - (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]));
}

static inline void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

static inline u32 xorshift32(u32 *state) {
    u32 x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

static int lm_cost(u32 alpha, u32 beta, u32 gamma) {
    u32 eq = (~(alpha ^ beta)) & (~(alpha ^ gamma));
    u32 eq_lo = eq & 0x7fffffffU;
    u32 viol = (alpha ^ beta ^ gamma ^ (beta << 1)) & (eq << 1);
    if (viol) return -1;
    return popcnt((~eq_lo) & 0x7ffffffeU);
}

static void compute_round_adders(const u32 s1[8], const u32 s2[8],
                                 u32 w1, u32 w2, u32 k,
                                 adder_info_t adders[7]) {
    u32 a1 = s1[7] ^ s2[7];
    u32 b1 = Sigma1(s1[4]) ^ Sigma1(s2[4]);
    u32 acc1_1 = s1[7] + Sigma1(s1[4]);
    u32 acc1_2 = s2[7] + Sigma1(s2[4]);
    u32 g1 = acc1_1 ^ acc1_2;
    adders[0] = (adder_info_t){(a1 | b1) != 0, a1, b1, g1, 0};

    u32 a2 = g1;
    u32 b2 = Ch(s1[4], s1[5], s1[6]) ^ Ch(s2[4], s2[5], s2[6]);
    u32 acc2_1 = acc1_1 + Ch(s1[4], s1[5], s1[6]);
    u32 acc2_2 = acc1_2 + Ch(s2[4], s2[5], s2[6]);
    u32 g2 = acc2_1 ^ acc2_2;
    adders[1] = (adder_info_t){(a2 | b2) != 0, a2, b2, g2, 0};

    u32 a3 = g2;
    u32 acc3_1 = acc2_1 + k;
    u32 acc3_2 = acc2_2 + k;
    u32 g3 = acc3_1 ^ acc3_2;
    adders[2] = (adder_info_t){a3 != 0, a3, 0, g3, 0};

    u32 a4 = g3;
    u32 b4 = w1 ^ w2;
    u32 T1_1 = acc3_1 + w1;
    u32 T1_2 = acc3_2 + w2;
    u32 g4 = T1_1 ^ T1_2;
    adders[3] = (adder_info_t){(a4 | b4) != 0, a4, b4, g4, 0};

    u32 a5 = Sigma0(s1[0]) ^ Sigma0(s2[0]);
    u32 b5 = Maj(s1[0], s1[1], s1[2]) ^ Maj(s2[0], s2[1], s2[2]);
    u32 T2_1 = Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]);
    u32 T2_2 = Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]);
    u32 g5 = T2_1 ^ T2_2;
    adders[4] = (adder_info_t){(a5 | b5) != 0, a5, b5, g5, 0};

    u32 a6 = g4;
    u32 b6 = g5;
    u32 a_new_1 = T1_1 + T2_1;
    u32 a_new_2 = T1_2 + T2_2;
    u32 g6 = a_new_1 ^ a_new_2;
    adders[5] = (adder_info_t){(a6 | b6) != 0, a6, b6, g6, 0};

    u32 a7 = s1[3] ^ s2[3];
    u32 b7 = g4;
    u32 e_new_1 = s1[3] + T1_1;
    u32 e_new_2 = s2[3] + T1_2;
    u32 g7 = e_new_1 ^ e_new_2;
    adders[6] = (adder_info_t){(a7 | b7) != 0, a7, b7, g7, 0};

    for (int i = 0; i < 7; i++) {
        adders[i].lm_cost = adders[i].active
            ? lm_cost(adders[i].alpha, adders[i].beta, adders[i].gamma)
            : 0;
    }
}

static int init_ctx(ctx_t *ctx, u32 m0, u32 fill, int bit) {
    u32 M1[16], M2[16];
    u32 mask = (u32)1 << bit;
    M1[0] = m0;
    for (int i = 1; i < 16; i++) M1[i] = fill;
    memcpy(M2, M1, sizeof(M1));
    M2[0] ^= mask;
    M2[9] ^= mask;

    for (int i = 0; i < 16; i++) {
        ctx->W1_pre[i] = M1[i];
        ctx->W2_pre[i] = M2[i];
    }
    for (int i = 16; i < 64; i++) {
        ctx->W1_pre[i] = sigma1_(ctx->W1_pre[i - 2]) + ctx->W1_pre[i - 7]
                       + sigma0_(ctx->W1_pre[i - 15]) + ctx->W1_pre[i - 16];
        ctx->W2_pre[i] = sigma1_(ctx->W2_pre[i - 2]) + ctx->W2_pre[i - 7]
                       + sigma0_(ctx->W2_pre[i - 15]) + ctx->W2_pre[i - 16];
    }

    for (int i = 0; i < 8; i++) {
        ctx->s1_pre[i] = IV[i];
        ctx->s2_pre[i] = IV[i];
    }
    for (int r = 0; r < 57; r++) {
        sha_round(ctx->s1_pre, K[r], ctx->W1_pre[r]);
        sha_round(ctx->s2_pre, K[r], ctx->W2_pre[r]);
    }

    return ctx->s1_pre[0] == ctx->s2_pre[0];
}

static rec_t evaluate_point(const ctx_t *ctx, const u32 W[4]) {
    u32 s1[8], s2[8];
    memcpy(s1, ctx->s1_pre, sizeof(s1));
    memcpy(s2, ctx->s2_pre, sizeof(s2));

    u32 W1_57 = W[0], W1_58 = W[1], W1_59 = W[2], W1_60 = W[3];
    u32 W2_57, W2_58, W2_59, W2_60;
    int total_lm = 0, total_active = 0, incompat = 0;

    for (int r = 57; r <= 60; r++) {
        u32 w1 = W[r - 57];
        u32 w2 = w1 + cw1(s1, s2);
        if (r == 57) W2_57 = w2;
        if (r == 58) W2_58 = w2;
        if (r == 59) W2_59 = w2;
        if (r == 60) W2_60 = w2;

        adder_info_t adders[7];
        compute_round_adders(s1, s2, w1, w2, K[r], adders);
        for (int i = 0; i < 7; i++) {
            if (adders[i].active) {
                total_active++;
                if (adders[i].lm_cost < 0) incompat++;
                else total_lm += adders[i].lm_cost;
            }
        }
        sha_round(s1, K[r], w1);
        sha_round(s2, K[r], w2);
    }

    u32 W1_61 = sigma1_(W1_59) + ctx->W1_pre[54]
              + sigma0_(ctx->W1_pre[46]) + ctx->W1_pre[45];
    u32 W1_62 = sigma1_(W1_60) + ctx->W1_pre[55]
              + sigma0_(ctx->W1_pre[47]) + ctx->W1_pre[46];
    u32 W1_63 = sigma1_(W1_61) + ctx->W1_pre[56]
              + sigma0_(ctx->W1_pre[48]) + ctx->W1_pre[47];
    u32 W2_61 = sigma1_(W2_59) + ctx->W2_pre[54]
              + sigma0_(ctx->W2_pre[46]) + ctx->W2_pre[45];
    u32 W2_62 = sigma1_(W2_60) + ctx->W2_pre[55]
              + sigma0_(ctx->W2_pre[47]) + ctx->W2_pre[46];
    u32 W2_63 = sigma1_(W2_61) + ctx->W2_pre[56]
              + sigma0_(ctx->W2_pre[48]) + ctx->W2_pre[47];

    const u32 W1_tail[3] = {W1_61, W1_62, W1_63};
    const u32 W2_tail[3] = {W2_61, W2_62, W2_63};
    for (int i = 0; i < 3; i++) {
        int r = 61 + i;
        adder_info_t adders[7];
        compute_round_adders(s1, s2, W1_tail[i], W2_tail[i], K[r], adders);
        for (int j = 0; j < 7; j++) {
            if (adders[j].active) {
                total_active++;
                if (adders[j].lm_cost < 0) incompat++;
                else total_lm += adders[j].lm_cost;
            }
        }
        sha_round(s1, K[r], W1_tail[i]);
        sha_round(s2, K[r], W2_tail[i]);
    }

    rec_t rec;
    memset(&rec, 0, sizeof(rec));
    rec.valid = 1;
    rec.lm = total_lm;
    rec.active = total_active;
    rec.incompat = incompat;
    memcpy(rec.W, W, sizeof(rec.W));

    int hw = 0;
    for (int i = 0; i < 8; i++) {
        rec.diff[i] = s1[i] ^ s2[i];
        hw += popcnt(rec.diff[i]);
    }
    rec.hw = hw;
    rec.sym = rec.diff[2] == rec.diff[6];
    return rec;
}

static int dominates(const rec_t *a, const rec_t *b) {
    if (!a->valid || !b->valid) return 0;
    return a->hw <= b->hw && a->lm <= b->lm && (a->hw < b->hw || a->lm < b->lm);
}

static int better_hw(const rec_t *a, const rec_t *b) {
    return !b->valid || a->hw < b->hw || (a->hw == b->hw && a->lm < b->lm);
}

static int better_lm(const rec_t *a, const rec_t *b) {
    return !b->valid || a->lm < b->lm || (a->lm == b->lm && a->hw < b->hw);
}

static void front_add(stats_t *st, const rec_t *rec) {
    for (int i = 0; i < st->nfront; i++) {
        if (st->front[i].hw == rec->hw && st->front[i].lm == rec->lm) {
            if (rec->sym && !st->front[i].sym) st->front[i] = *rec;
            return;
        }
        if (dominates(&st->front[i], rec)) return;
    }

    int out = 0;
    for (int i = 0; i < st->nfront; i++) {
        if (!dominates(rec, &st->front[i])) st->front[out++] = st->front[i];
    }
    st->nfront = out;
    if (st->nfront < FRONT_CAP) {
        st->front[st->nfront++] = *rec;
    }
}

static void stats_offer(stats_t *st, const rec_t *rec) {
    if (better_hw(rec, &st->best_hw)) st->best_hw = *rec;
    if (better_lm(rec, &st->best_lm)) st->best_lm = *rec;
    if (rec->sym && better_lm(rec, &st->best_sym_lm)) st->best_sym_lm = *rec;
    front_add(st, rec);
}

static void stats_add(stats_t *st, const rec_t *rec) {
    stats_offer(st, rec);
    if (rec->sym) st->sym_count++;
    if (rec->incompat) st->incompat_count++;
}

static void stats_merge(stats_t *dst, const stats_t *src) {
    if (src->best_hw.valid) stats_offer(dst, &src->best_hw);
    if (src->best_lm.valid) stats_offer(dst, &src->best_lm);
    if (src->best_sym_lm.valid) stats_offer(dst, &src->best_sym_lm);
    for (int i = 0; i < src->nfront; i++) stats_offer(dst, &src->front[i]);
    dst->sym_count += src->sym_count;
    dst->incompat_count += src->incompat_count;
}

static int cmp_rec(const void *pa, const void *pb) {
    const rec_t *a = (const rec_t *)pa, *b = (const rec_t *)pb;
    if (a->hw != b->hw) return a->hw - b->hw;
    return a->lm - b->lm;
}

static void print_rec_json(const char *name, const rec_t *r) {
    if (!r->valid) {
        printf("\"%s\":null", name);
        return;
    }
    printf("\"%s\":{\"hw\":%d,\"lm\":%d,\"active\":%d,\"incompat\":%d,"
           "\"sym\":%d,\"W\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"diff\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\","
           "\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]}",
           name, r->hw, r->lm, r->active, r->incompat, r->sym,
           r->W[0], r->W[1], r->W[2], r->W[3],
           r->diff[0], r->diff[1], r->diff[2], r->diff[3],
           r->diff[4], r->diff[5], r->diff[6], r->diff[7]);
}

static int run_walk(int argc, char **argv) {
    int point_mode = strcmp(argv[1], "pointwalk") == 0;
    u32 baseW[4] = {0, 0, 0, 0};
    u32 m0, fill, seed;
    int bit, threads, max_flips, slack;
    uint64_t restarts, steps;

    if (point_mode) {
        if (argc < 14) {
            fprintf(stderr,
                    "Usage: %s pointwalk m0 fill bit W57 W58 W59 W60 restarts steps threads seed max_flips [slack]\n",
                    argv[0]);
            return 1;
        }
        m0 = strtoul(argv[2], NULL, 0);
        fill = strtoul(argv[3], NULL, 0);
        bit = atoi(argv[4]);
        baseW[0] = strtoul(argv[5], NULL, 0);
        baseW[1] = strtoul(argv[6], NULL, 0);
        baseW[2] = strtoul(argv[7], NULL, 0);
        baseW[3] = strtoul(argv[8], NULL, 0);
        restarts = strtoull(argv[9], NULL, 0);
        steps = strtoull(argv[10], NULL, 0);
        threads = atoi(argv[11]);
        seed = strtoul(argv[12], NULL, 0);
        max_flips = atoi(argv[13]);
        slack = (argc >= 15) ? atoi(argv[14]) : 4;
    } else {
        if (argc < 10) {
            fprintf(stderr,
                    "Usage: %s walk m0 fill bit restarts steps threads seed max_flips [slack]\n",
                    argv[0]);
            return 1;
        }
        m0 = strtoul(argv[2], NULL, 0);
        fill = strtoul(argv[3], NULL, 0);
        bit = atoi(argv[4]);
        restarts = strtoull(argv[5], NULL, 0);
        steps = strtoull(argv[6], NULL, 0);
        threads = atoi(argv[7]);
        seed = strtoul(argv[8], NULL, 0);
        max_flips = atoi(argv[9]);
        slack = (argc >= 11) ? atoi(argv[10]) : 4;
    }
    if (max_flips < 1) max_flips = 1;
    if (max_flips > 64) max_flips = 64;
    if (slack < 0) slack = 0;

    ctx_t ctx;
    if (!init_ctx(&ctx, m0, fill, bit)) {
        fprintf(stderr, "ERROR: candidate is not cascade-eligible at round 57\n");
        return 2;
    }

    if (threads < 1) threads = 1;
#ifdef _OPENMP
    omp_set_num_threads(threads);
#else
    threads = 1;
#endif

    stats_t global;
    memset(&global, 0, sizeof(global));

    double t0;
#ifdef _OPENMP
    t0 = omp_get_wtime();
#else
    t0 = (double)clock() / CLOCKS_PER_SEC;
#endif

#pragma omp parallel
    {
        stats_t local;
        memset(&local, 0, sizeof(local));
        int tid = 0;
#ifdef _OPENMP
        tid = omp_get_thread_num();
#endif
        u32 rng = seed ^ (0x85ebca6bU * (u32)(tid + 1));

#pragma omp for schedule(static)
        for (uint64_t r = 0; r < restarts; r++) {
            u32 curW[4];
            if (point_mode) {
                memcpy(curW, baseW, sizeof(curW));
                if (r != 0) {
                    int warm = 1 + (int)(xorshift32(&rng) % (u32)max_flips);
                    for (int f = 0; f < warm; f++) {
                        u32 pick = xorshift32(&rng);
                        curW[pick & 3U] ^= (u32)1 << ((pick >> 2) & 31U);
                    }
                }
            } else {
                curW[0] = xorshift32(&rng);
                curW[1] = xorshift32(&rng);
                curW[2] = xorshift32(&rng);
                curW[3] = xorshift32(&rng);
            }
            rec_t cur = evaluate_point(&ctx, curW);
            stats_add(&local, &cur);

            for (uint64_t step = 0; step < steps; step++) {
                u32 propW[4] = {curW[0], curW[1], curW[2], curW[3]};
                int flips = 1 + (int)(xorshift32(&rng) % (u32)max_flips);
                for (int f = 0; f < flips; f++) {
                    u32 pick = xorshift32(&rng);
                    propW[pick & 3U] ^= (u32)1 << ((pick >> 2) & 31U);
                }
                rec_t prop = evaluate_point(&ctx, propW);
                stats_add(&local, &prop);

                int accept = 0;
                if (prop.lm < cur.lm) accept = 1;
                else if (prop.lm == cur.lm && prop.hw <= cur.hw) accept = 1;
                else if (prop.lm <= cur.lm + slack &&
                         (xorshift32(&rng) & 15U) == 0) accept = 1;
                if (accept) {
                    cur = prop;
                    memcpy(curW, propW, sizeof(curW));
                }
            }
        }

#pragma omp critical
        stats_merge(&global, &local);
    }

    double t1;
#ifdef _OPENMP
    t1 = omp_get_wtime();
#else
    t1 = (double)clock() / CLOCKS_PER_SEC;
#endif

    qsort(global.front, global.nfront, sizeof(rec_t), cmp_rec);
    uint64_t evals = restarts * (steps + 1);

    printf("{\"mode\":\"%s\",\"m0\":\"0x%08x\","
           "\"fill\":\"0x%08x\",\"bit\":%d,\"restarts\":%llu,"
           "\"steps\":%llu,\"evals\":%llu,\"threads\":%d,"
           "\"max_flips\":%d,\"slack\":%d,\"seconds\":%.3f,"
           "\"rate_mps\":%.3f,\"sym_count\":%llu,\"incompat_count\":%llu,",
           point_mode ? "block2_pareto_pointwalk" : "block2_pareto_walk",
           m0, fill, bit, (unsigned long long)restarts,
           (unsigned long long)steps, (unsigned long long)evals,
           threads, max_flips, slack, t1 - t0,
           (t1 > t0) ? ((double)evals / (t1 - t0) / 1e6) : 0.0,
           (unsigned long long)global.sym_count,
           (unsigned long long)global.incompat_count);
    print_rec_json("best_hw", &global.best_hw);
    printf(",");
    print_rec_json("best_lm", &global.best_lm);
    printf(",");
    print_rec_json("best_sym_lm", &global.best_sym_lm);
    printf(",\"frontier\":[");
    for (int i = 0; i < global.nfront; i++) {
        if (i) printf(",");
        printf("{\"hw\":%d,\"lm\":%d,\"sym\":%d,"
               "\"W\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]}",
               global.front[i].hw, global.front[i].lm, global.front[i].sym,
               global.front[i].W[0], global.front[i].W[1],
               global.front[i].W[2], global.front[i].W[3]);
    }
    printf("]}\n");
    return 0;
}

static int run_sweep60(int argc, char **argv) {
    if (argc < 9) {
        fprintf(stderr,
                "Usage: %s sweep60 m0 fill bit W57 W58 W59 threads [start] [count]\n",
                argv[0]);
        return 1;
    }

    u32 m0 = strtoul(argv[2], NULL, 0);
    u32 fill = strtoul(argv[3], NULL, 0);
    int bit = atoi(argv[4]);
    u32 fixedW[4] = {
        strtoul(argv[5], NULL, 0),
        strtoul(argv[6], NULL, 0),
        strtoul(argv[7], NULL, 0),
        0
    };
    int threads = atoi(argv[8]);
    uint64_t start = (argc >= 10) ? strtoull(argv[9], NULL, 0) : 0;
    uint64_t count = (argc >= 11) ? strtoull(argv[10], NULL, 0) : (1ULL << 32);
    if (count > (1ULL << 32)) count = (1ULL << 32);

    ctx_t ctx;
    if (!init_ctx(&ctx, m0, fill, bit)) {
        fprintf(stderr, "ERROR: candidate is not cascade-eligible at round 57\n");
        return 2;
    }

    if (threads < 1) threads = 1;
#ifdef _OPENMP
    omp_set_num_threads(threads);
#else
    threads = 1;
#endif

    stats_t global;
    memset(&global, 0, sizeof(global));

    double t0;
#ifdef _OPENMP
    t0 = omp_get_wtime();
#else
    t0 = (double)clock() / CLOCKS_PER_SEC;
#endif

#pragma omp parallel
    {
        stats_t local;
        memset(&local, 0, sizeof(local));

#pragma omp for schedule(static)
        for (uint64_t i = 0; i < count; i++) {
            u32 W[4] = {fixedW[0], fixedW[1], fixedW[2], (u32)(start + i)};
            rec_t rec = evaluate_point(&ctx, W);
            stats_add(&local, &rec);
        }

#pragma omp critical
        stats_merge(&global, &local);
    }

    double t1;
#ifdef _OPENMP
    t1 = omp_get_wtime();
#else
    t1 = (double)clock() / CLOCKS_PER_SEC;
#endif

    qsort(global.front, global.nfront, sizeof(rec_t), cmp_rec);

    printf("{\"mode\":\"block2_pareto_sweep60\",\"m0\":\"0x%08x\","
           "\"fill\":\"0x%08x\",\"bit\":%d,"
           "\"fixed_W\":[\"0x%08x\",\"0x%08x\",\"0x%08x\"],"
           "\"start\":\"0x%08x\",\"count\":%llu,\"threads\":%d,"
           "\"seconds\":%.3f,\"rate_mps\":%.3f,"
           "\"sym_count\":%llu,\"incompat_count\":%llu,",
           m0, fill, bit, fixedW[0], fixedW[1], fixedW[2],
           (u32)start, (unsigned long long)count, threads, t1 - t0,
           (t1 > t0) ? ((double)count / (t1 - t0) / 1e6) : 0.0,
           (unsigned long long)global.sym_count,
           (unsigned long long)global.incompat_count);
    print_rec_json("best_hw", &global.best_hw);
    printf(",");
    print_rec_json("best_lm", &global.best_lm);
    printf(",");
    print_rec_json("best_sym_lm", &global.best_sym_lm);
    printf(",\"frontier\":[");
    for (int i = 0; i < global.nfront; i++) {
        if (i) printf(",");
        printf("{\"hw\":%d,\"lm\":%d,\"sym\":%d,"
               "\"W\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]}",
               global.front[i].hw, global.front[i].lm, global.front[i].sym,
               global.front[i].W[0], global.front[i].W[1],
               global.front[i].W[2], global.front[i].W[3]);
    }
    printf("]}\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && (strcmp(argv[1], "walk") == 0 ||
                     strcmp(argv[1], "pointwalk") == 0)) {
        return run_walk(argc, argv);
    }
    if (argc > 1 && strcmp(argv[1], "sweep60") == 0) {
        return run_sweep60(argc, argv);
    }

    if (argc < 7) {
        fprintf(stderr, "Usage: %s m0 fill bit nsamples threads seed [W57 W58 W59 W60]\n", argv[0]);
        return 1;
    }

    u32 m0 = strtoul(argv[1], NULL, 0);
    u32 fill = strtoul(argv[2], NULL, 0);
    int bit = atoi(argv[3]);
    uint64_t n = strtoull(argv[4], NULL, 0);
    int threads = atoi(argv[5]);
    u32 seed = strtoul(argv[6], NULL, 0);

    ctx_t ctx;
    if (!init_ctx(&ctx, m0, fill, bit)) {
        fprintf(stderr, "ERROR: candidate is not cascade-eligible at round 57\n");
        return 2;
    }

    if (argc >= 11) {
        u32 W[4] = {
            strtoul(argv[7], NULL, 0), strtoul(argv[8], NULL, 0),
            strtoul(argv[9], NULL, 0), strtoul(argv[10], NULL, 0)
        };
        rec_t rec = evaluate_point(&ctx, W);
        printf("{\"mode\":\"point\",\"m0\":\"0x%08x\",\"fill\":\"0x%08x\","
               "\"bit\":%d,", m0, fill, bit);
        print_rec_json("point", &rec);
        printf("}\n");
        return 0;
    }

    if (threads < 1) threads = 1;
#ifdef _OPENMP
    omp_set_num_threads(threads);
#else
    threads = 1;
#endif

    stats_t global;
    memset(&global, 0, sizeof(global));

    double t0;
#ifdef _OPENMP
    t0 = omp_get_wtime();
#else
    t0 = (double)clock() / CLOCKS_PER_SEC;
#endif

#pragma omp parallel
    {
        stats_t local;
        memset(&local, 0, sizeof(local));
        int tid = 0;
#ifdef _OPENMP
        tid = omp_get_thread_num();
#endif
        u32 rng = seed ^ (0x9e3779b9U * (u32)(tid + 1));

#pragma omp for schedule(static)
        for (uint64_t i = 0; i < n; i++) {
            u32 W[4] = {
                xorshift32(&rng), xorshift32(&rng),
                xorshift32(&rng), xorshift32(&rng)
            };
            rec_t rec = evaluate_point(&ctx, W);
            stats_add(&local, &rec);
        }

#pragma omp critical
        stats_merge(&global, &local);
    }

    double t1;
#ifdef _OPENMP
    t1 = omp_get_wtime();
#else
    t1 = (double)clock() / CLOCKS_PER_SEC;
#endif

    qsort(global.front, global.nfront, sizeof(rec_t), cmp_rec);

    printf("{\"mode\":\"block2_pareto_sampler\",\"m0\":\"0x%08x\","
           "\"fill\":\"0x%08x\",\"bit\":%d,\"samples\":%llu,"
           "\"threads\":%d,\"seconds\":%.3f,\"rate_mps\":%.3f,"
           "\"sym_count\":%llu,\"incompat_count\":%llu,",
           m0, fill, bit, (unsigned long long)n, threads, t1 - t0,
           (t1 > t0) ? ((double)n / (t1 - t0) / 1e6) : 0.0,
           (unsigned long long)global.sym_count,
           (unsigned long long)global.incompat_count);
    print_rec_json("best_hw", &global.best_hw);
    printf(",");
    print_rec_json("best_lm", &global.best_lm);
    printf(",");
    print_rec_json("best_sym_lm", &global.best_sym_lm);
    printf(",\"frontier\":[");
    for (int i = 0; i < global.nfront; i++) {
        if (i) printf(",");
        printf("{\"hw\":%d,\"lm\":%d,\"sym\":%d,"
               "\"W\":[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]}",
               global.front[i].hw, global.front[i].lm, global.front[i].sym,
               global.front[i].W[0], global.front[i].W[1],
               global.front[i].W[2], global.front[i].W[3]);
    }
    printf("]}\n");
    return 0;
}
