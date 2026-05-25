/*
 * sched_repair_probe.c
 *
 * Schedule-realizable W60 repair probe for the mitm_residue free-word route.
 *
 * Motivation (2026-05-25):
 *   The oracle repair in free_word_mitm_reducedn.c (eval_repaired_tail) reaches
 *   tail HW8 by overwriting W60_2 := req_w2_60 directly. That patch is NOT
 *   schedule-realizable: the message schedule forces
 *       W60_2 = s1(W2_58) + Wpre2[53] + s0(Wpre2[45]) + Wpre2[44].
 *   The only knob feeding W60_2 is W2_58 (through s1). The cascade currently
 *   PINS W2_58 = w2_for_zero_a(58, ...) so the round-58 a-difference is zeroed.
 *
 *   This probe releases that pin: W2_58 = w2_58_base + delta. A nonzero delta is
 *   a genuine schedule perturbation that moves W60_2 honestly toward req, at the
 *   cost of leaving a round-58 difference (the "shaping price"). We sweep delta
 *   and measure whether the resulting *honest* tail beats the no-repair (delta=0)
 *   plateau and how close it gets to the oracle frontier.
 *
 *   Frontiers reported per window:
 *     honest_d0   : best tail over delta=0 triples with D60=0   (matches existing exact scan)
 *     honest_any  : best tail over delta=0 triples, any D60      (no D60 gate)
 *     oracle      : best tail with W60_2 := req                  (the un-realizable HW8 target)
 *     sched_repair: best HONEST tail over delta != 0             (the new schedule-realizable result)
 *
 * Model primitives (setup_width / sigmas / sha_round / w2_for_zero_* / precompute
 * / find_candidate) are copied verbatim from free_word_mitm_reducedn.c so the
 * reduced-N model is identical and results are directly comparable. Do not edit
 * them here without mirroring that file.
 *
 * Compile (OpenMP):
 *   gcc -O3 -march=native -Xclang -fopenmp \
 *     -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *     -o /tmp/sched_repair_probe \
 *     headline_hunt/bets/mitm_residue/prototypes/sched_repair_probe.c -lm
 *
 * Run:
 *   /tmp/sched_repair_probe N [tri_limit] [delta_mode] [delta_radius] [sample_start]
 *     tri_limit    : number of (w57,w58) prefixes to scan (0 = all 2^(2N))
 *     delta_mode   : 0 = baseline only, 1 = full delta in [0,2^N), 2 = HW(delta)<=radius ball
 *     delta_radius : ball radius for delta_mode=2
 *     sample_start : shifts permuted-prefix samples (ignored when tri_limit covers all)
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
static int gKnob = 58;   /* which message-2 word gets the repair delta: 57, 58 (W60 knob), or 59 (control) */
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
static inline uint32_t S0(uint32_t x){return (ror_n(x,rS0[0])^ror_n(x,rS0[1])^ror_n(x,rS0[2]))&gMASK;}
static inline uint32_t S1(uint32_t x){return (ror_n(x,rS1[0])^ror_n(x,rS1[1])^ror_n(x,rS1[2]))&gMASK;}
static inline uint32_t s0(uint32_t x){return (ror_n(x,rs0[0])^ror_n(x,rs0[1])^(x>>ss0))&gMASK;}
static inline uint32_t s1(uint32_t x){return (ror_n(x,rs1[0])^ror_n(x,rs1[1])^(x>>ss1))&gMASK;}
static inline uint32_t ch(uint32_t e,uint32_t f,uint32_t g){return ((e&f)^((~e)&g))&gMASK;}
static inline uint32_t maj(uint32_t a,uint32_t b,uint32_t c){return ((a&b)^(a&c)^(b&c))&gMASK;}
static inline int hw(uint32_t x){return __builtin_popcount(x & gMASK);}

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & gMASK;
    for (int i = 16; i < 57; i++)
        W[i] = (s1(W[i-2]) + W[i-7] + s0(W[i-15]) + W[i-16]) & gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + S1(e) + ch(e,f,g) + KN[i] + W[i]) & gMASK;
        uint32_t T2 = (S0(a) + maj(a,b,c)) & gMASK;
        h=g; g=f; f=e; e=(d+T1)&gMASK; d=c; c=b; b=a; a=(T1+T2)&gMASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d; st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

static inline void sha_round(uint32_t st[8], int round_idx, uint32_t W) {
    uint32_t T1 = (st[7] + S1(st[4]) + ch(st[4],st[5],st[6]) + KN[round_idx] + W) & gMASK;
    uint32_t T2 = (S0(st[0]) + maj(st[0],st[1],st[2])) & gMASK;
    st[7]=st[6]; st[6]=st[5]; st[5]=st[4]; st[4]=(st[3]+T1)&gMASK;
    st[3]=st[2]; st[2]=st[1]; st[1]=st[0]; st[0]=(T1+T2)&gMASK;
}

static inline uint32_t w2_for_zero_a(const uint32_t s1v[8], const uint32_t s2v[8],
                                     int round_idx, uint32_t w1) {
    uint32_t base1 = (s1v[7]+S1(s1v[4])+ch(s1v[4],s1v[5],s1v[6])+KN[round_idx]) & gMASK;
    uint32_t base2 = (s2v[7]+S1(s2v[4])+ch(s2v[4],s2v[5],s2v[6])+KN[round_idx]) & gMASK;
    uint32_t T21 = (S0(s1v[0])+maj(s1v[0],s1v[1],s1v[2])) & gMASK;
    uint32_t T22 = (S0(s2v[0])+maj(s2v[0],s2v[1],s2v[2])) & gMASK;
    return (w1 + base1 - base2 + T21 - T22) & gMASK;
}

static inline uint32_t w2_for_zero_e(const uint32_t s1v[8], const uint32_t s2v[8],
                                     int round_idx, uint32_t w1) {
    uint32_t base1 = (s1v[7]+S1(s1v[4])+ch(s1v[4],s1v[5],s1v[6])+KN[round_idx]) & gMASK;
    uint32_t base2 = (s2v[7]+S1(s2v[4])+ch(s2v[4],s2v[5],s2v[6])+KN[round_idx]) & gMASK;
    return (w1 + s1v[3] - s2v[3] + base1 - base2) & gMASK;
}

static int state_diff_hw(const uint32_t a[8], const uint32_t b[8]) {
    int out = 0;
    for (int i = 0; i < 8; i++) out += hw(a[i] ^ b[i]);
    return out;
}
static void copy_state(uint32_t dst[8], const uint32_t src[8]){memcpy(dst,src,8*sizeof(uint32_t));}

static uint64_t mix64(uint64_t x){
    x^=x>>30; x*=0xbf58476d1ce4e5b9ULL; x^=x>>27; x*=0x94d049bb133111ebULL; x^=x>>31; return x;
}

/* Deterministic base window: first m0 with matching a-register at round 57,
 * else a hashed random message. Mirrors free_word_mitm_reducedn.c. */
static int find_candidate(uint32_t M1[16], uint32_t M2[16],
                          uint32_t st1[8], uint32_t st2[8],
                          uint32_t W1[64], uint32_t W2[64]) {
    uint64_t limit = (uint64_t)gMASK + 1u;
    for (uint64_t m0 = 0; m0 < limit; m0++) {
        for (int i = 0; i < 16; i++) M1[i] = gMASK;
        M1[0] = (uint32_t)m0;
        memcpy(M2, M1, 16*sizeof(uint32_t));
        M2[0] ^= gMSB; M2[9] ^= gMSB;
        precompute(M1, st1, W1);
        precompute(M2, st2, W2);
        if (st1[0] == st2[0]) return 1;
    }
    uint64_t random_limit = 1ull << 24;
    for (uint64_t trial = 0; trial < random_limit; trial++) {
        for (int i = 0; i < 16; i++)
            M1[i] = (uint32_t)mix64(trial ^ (0x9e3779b97f4a7c15ULL*(uint64_t)(i+1))) & gMASK;
        memcpy(M2, M1, 16*sizeof(uint32_t));
        M2[0] ^= gMSB; M2[9] ^= gMSB;
        precompute(M1, st1, W1);
        precompute(M2, st2, W2);
        if (st1[0] == st2[0]) return 1;
    }
    return 0;
}

typedef struct {
    int tail_hw, r61_hw, mid58_hw, d60_hw;
    uint32_t d60, delta, w57, w58, w59;
} res_t;

/* One tail evaluation. delta perturbs the schedule word W2_58. oracle=1 overwrites
 * W60_2 := req (the un-realizable comparison). Returns tail HW (rounds 60..63). */
static int eval_probe(const uint32_t init1[8], const uint32_t init2[8],
                      const uint32_t Wpre1[64], const uint32_t Wpre2[64],
                      uint32_t w57, uint32_t w58, uint32_t w59,
                      uint32_t delta, int oracle, res_t *r) {
    uint32_t s1v[8], s2v[8];
    copy_state(s1v, init1); copy_state(s2v, init2);

    uint32_t w2_57_base = w2_for_zero_a(s1v, s2v, 57, w57);
    uint32_t w2_57 = (gKnob == 57) ? ((w2_57_base + delta) & gMASK) : w2_57_base;
    sha_round(s1v, 57, w57); sha_round(s2v, 57, w2_57);

    uint32_t w2_58_base = w2_for_zero_a(s1v, s2v, 58, w58);
    uint32_t w2_58 = (gKnob == 58) ? ((w2_58_base + delta) & gMASK) : w2_58_base; /* repair variable */
    sha_round(s1v, 58, w58); sha_round(s2v, 58, w2_58);
    int mid58 = state_diff_hw(s1v, s2v);                    /* shaping price */

    uint32_t W60_1 = (s1(w58)   + Wpre1[53] + s0(Wpre1[45]) + Wpre1[44]) & gMASK;
    uint32_t W60_2 = (s1(w2_58) + Wpre2[53] + s0(Wpre2[45]) + Wpre2[44]) & gMASK;

    uint32_t w2_59_base = w2_for_zero_a(s1v, s2v, 59, w59);
    uint32_t w2_59 = (gKnob == 59) ? ((w2_59_base + delta) & gMASK) : w2_59_base;
    sha_round(s1v, 59, w59); sha_round(s2v, 59, w2_59);

    uint32_t req = w2_for_zero_e(s1v, s2v, 60, W60_1);
    uint32_t d60 = (W60_2 - req) & gMASK;
    uint32_t use_W60_2 = oracle ? req : W60_2;

    uint32_t W61_1 = (s1(w59)   + Wpre1[54] + s0(Wpre1[46]) + Wpre1[45]) & gMASK;
    uint32_t W61_2 = (s1(w2_59) + Wpre2[54] + s0(Wpre2[46]) + Wpre2[45]) & gMASK;
    uint32_t W62_1 = (s1(W60_1)     + Wpre1[55] + s0(Wpre1[47]) + Wpre1[46]) & gMASK;
    uint32_t W62_2 = (s1(use_W60_2) + Wpre2[55] + s0(Wpre2[47]) + Wpre2[46]) & gMASK;
    uint32_t W63_1 = (s1(W61_1) + Wpre1[56] + s0(Wpre1[48]) + Wpre1[47]) & gMASK;
    uint32_t W63_2 = (s1(W61_2) + Wpre2[56] + s0(Wpre2[48]) + Wpre2[47]) & gMASK;

    sha_round(s1v, 60, W60_1); sha_round(s2v, 60, use_W60_2);
    sha_round(s1v, 61, W61_1); sha_round(s2v, 61, W61_2);
    int r61 = state_diff_hw(s1v, s2v);
    sha_round(s1v, 62, W62_1); sha_round(s2v, 62, W62_2);
    sha_round(s1v, 63, W63_1); sha_round(s2v, 63, W63_2);
    int tail = state_diff_hw(s1v, s2v);

    if (r) {
        r->tail_hw = tail; r->r61_hw = r61; r->mid58_hw = mid58;
        r->d60 = d60; r->d60_hw = hw(d60); r->delta = delta;
        r->w57 = w57; r->w58 = w58; r->w59 = w59;
    }
    return tail;
}

static void maybe_update(res_t *best, const res_t *cand) {
    if (cand->tail_hw < best->tail_hw ||
        (cand->tail_hw == best->tail_hw && cand->r61_hw < best->r61_hw))
        *best = *cand;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s N [tri_limit] [delta_mode] [delta_radius] [sample_start] [knob]\n", argv[0]);
        fprintf(stderr, "  knob = 57|58|59 : which message-2 word the repair delta perturbs (default 58 = W60 knob; 59 = control)\n");
        return 1;
    }
    int N = atoi(argv[1]);
    setup_width(N);
    uint64_t word_space = (uint64_t)gMASK + 1u;
    uint64_t prefix_space = word_space * word_space;          /* (w57,w58) plane */
    uint64_t tri_limit = (argc >= 3) ? strtoull(argv[2], NULL, 0) : 0;
    if (tri_limit == 0 || tri_limit > prefix_space) tri_limit = prefix_space;
    int delta_mode = (argc >= 4) ? atoi(argv[3]) : 1;
    int delta_radius = (argc >= 5) ? atoi(argv[4]) : 2;
    uint64_t sample_start = (argc >= 6) ? (strtoull(argv[5], NULL, 0) & (prefix_space - 1u)) : 0;
    if (argc >= 7) gKnob = atoi(argv[6]);
    if (gKnob != 57 && gKnob != 58 && gKnob != 59) gKnob = 58;

    uint32_t M1[16], M2[16], init1[8], init2[8], Wpre1[64]={0}, Wpre2[64]={0};
    if (!find_candidate(M1, M2, init1, init2, Wpre1, Wpre2)) {
        fprintf(stderr, "No base window found for N=%d\n", N);
        return 1;
    }

    /* Precompute the delta set for ball mode. */
    uint32_t *delta_set = NULL; uint64_t delta_count = 0;
    if (delta_mode == 1) {
        delta_count = word_space;
    } else if (delta_mode == 2) {
        /* all delta with popcount <= radius */
        uint64_t cap = 1;
        for (uint64_t v = 0; v < word_space; v++) if (hw((uint32_t)v) <= delta_radius) cap++;
        delta_set = malloc(cap * sizeof(uint32_t));
        for (uint64_t v = 0; v < word_space; v++)
            if (hw((uint32_t)v) <= delta_radius) delta_set[delta_count++] = (uint32_t)v;
    }

    const uint64_t perm_step = 11400714819323198485ull;
    int exact = (tri_limit == prefix_space);

    res_t best_d0   = {.tail_hw=999,.r61_hw=999};
    res_t best_any  = {.tail_hw=999,.r61_hw=999};
    res_t best_orac = {.tail_hw=999,.r61_hw=999};
    res_t best_rep  = {.tail_hw=999,.r61_hw=999};
    uint64_t n_d0 = 0;

    clock_t t0 = clock();

    #pragma omp parallel
    {
        res_t l_d0={.tail_hw=999,.r61_hw=999}, l_any={.tail_hw=999,.r61_hw=999};
        res_t l_orac={.tail_hw=999,.r61_hw=999}, l_rep={.tail_hw=999,.r61_hw=999};
        uint64_t l_nd0 = 0;
        #pragma omp for schedule(dynamic, 256)
        for (uint64_t i = 0; i < tri_limit; i++) {
            uint64_t p = exact ? i : (((sample_start + i) * perm_step) & (prefix_space - 1u));
            uint32_t w57 = (uint32_t)(p & gMASK);
            uint32_t w58 = (uint32_t)((p >> N) & gMASK);
            for (uint64_t w = 0; w < word_space; w++) {
                uint32_t w59 = (uint32_t)w;
                res_t r;
                /* baseline: delta = 0, honest schedule */
                eval_probe(init1, init2, Wpre1, Wpre2, w57, w58, w59, 0, 0, &r);
                maybe_update(&l_any, &r);
                if (r.d60 == 0) { l_nd0++; maybe_update(&l_d0, &r); }
                /* oracle: W60_2 := req */
                res_t ro;
                eval_probe(init1, init2, Wpre1, Wpre2, w57, w58, w59, 0, 1, &ro);
                maybe_update(&l_orac, &ro);
                /* schedule-realizable repair: sweep delta != 0 */
                if (delta_mode == 1) {
                    for (uint64_t dd = 1; dd < delta_count; dd++) {
                        res_t rr;
                        eval_probe(init1, init2, Wpre1, Wpre2, w57, w58, w59, (uint32_t)dd, 0, &rr);
                        maybe_update(&l_rep, &rr);
                    }
                } else if (delta_mode == 2) {
                    for (uint64_t k = 0; k < delta_count; k++) {
                        if (delta_set[k] == 0) continue;
                        res_t rr;
                        eval_probe(init1, init2, Wpre1, Wpre2, w57, w58, w59, delta_set[k], 0, &rr);
                        maybe_update(&l_rep, &rr);
                    }
                }
            }
        }
        #pragma omp critical
        {
            maybe_update(&best_d0, &l_d0);
            maybe_update(&best_any, &l_any);
            maybe_update(&best_orac, &l_orac);
            maybe_update(&best_rep, &l_rep);
            n_d0 += l_nd0;
        }
    }

    double secs = (double)(clock() - t0) / CLOCKS_PER_SEC;

    printf("N=%d tri_limit=%" PRIu64 " (exact=%d) word_space=%" PRIu64
           " delta_mode=%d delta_radius=%d sample_start=%" PRIu64 " knob=W2_%d\n",
           N, tri_limit, exact, word_space, delta_mode, delta_radius, sample_start, gKnob);
    printf("D60=0 triples found = %" PRIu64 "\n", n_d0);
    printf("\n  frontier      | tail | r61 | d60_hw | mid58_hw | delta  | W1[57..59]\n");
    printf("  --------------+------+-----+--------+----------+--------+------------------\n");
    #define ROW(label, b) printf("  %-13s | %4d | %3d | %6d | %8d | 0x%04x | 0x%x,0x%x,0x%x\n", \
        label, (b).tail_hw, (b).r61_hw, (b).d60_hw, (b).mid58_hw, (b).delta, (b).w57,(b).w58,(b).w59)
    ROW("honest_d0",   best_d0);
    ROW("honest_any",  best_any);
    ROW("oracle",      best_orac);
    if (delta_mode != 0) ROW("sched_repair", best_rep);
    #undef ROW
    printf("\nelapsed=%.2fs\n", secs);
    if (delta_set) free(delta_set);
    return 0;
}
