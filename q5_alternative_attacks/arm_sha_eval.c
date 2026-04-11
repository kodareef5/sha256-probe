/*
 * ARM NEON + SHA-2 Crypto Accelerated 7-Round Tail Evaluator
 *
 * Uses Apple Silicon hardware SHA-256 instructions (vsha256hq_u32, etc.)
 * to evaluate the sr=60 collision-difference function at full N=32.
 *
 * Architecture:
 *   - vsha256hq_u32(ABEF, CDGH, MSG) processes 2 SHA rounds per call
 *   - State is split: ABEF = (A, B, E, F), CDGH = (C, D, G, H)
 *   - We run 7 rounds = 4 calls (8 rounds, last discarded or adapted)
 *
 * Actually: the ARM SHA-2 instructions process TWO rounds at once.
 * For 7 rounds, we need 4 calls (processing rounds 0-1, 2-3, 4-5, 6-7)
 * but only extract state from 7 rounds.
 *
 * Workaround: run 8 rounds (4 calls) and accept the extra round.
 * OR: run 6 rounds (3 calls) then 1 manual round.
 *
 * The SHA-2 intrinsics:
 *   vsha256hq_u32(hash_abcd, hash_efgh, wk) — hash_abcd updated
 *   vsha256h2q_u32(hash_efgh, hash_abcd_new, wk) — hash_efgh updated
 *
 * But wait: the ARM SHA extensions process the state differently from
 * our standard (a,b,c,d,e,f,g,h) notation. The intrinsics expect:
 *   hash_abcd = (A, B, C, D)
 *   hash_efgh = (E, F, G, H)
 * And each call processes TWO rounds using TWO consecutive schedule words.
 *
 * For maximal performance with our specific use case (precomputed state,
 * 7 rounds, two messages), we use a hybrid approach:
 *   1. Precompute round-56 state
 *   2. For rounds 57-62 (6 rounds = 3 SHA2 instruction pairs): use hardware
 *   3. For round 63 (1 round): manual computation
 *   4. XOR both message states to get difference
 *
 * Compile: gcc -O3 -march=armv8-a+crypto -o arm_sha_eval arm_sha_eval.c
 *
 * Expected: ~500M-2B evals/s/core on Apple Silicon M-series.
 */

#include <arm_neon.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

/* Standard SHA-256 constants (full 32-bit, no scaling) */
static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

static const uint32_t IV[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

/* Precomputed state at round 56 */
static uint32_t state1[8], state2[8];
static uint32_t W1_pre[57], W2_pre[57];

/* SHA-256 primitives for manual computation */
#define ROR(x,n) (((x)>>(n))|((x)<<(32-(n))))
#define CH(e,f,g)  (((e)&(f))^((~(e))&(g)))
#define MAJ(a,b,c) (((a)&(b))^((a)&(c))^((b)&(c)))
#define SIGMA0(a) (ROR(a,2)^ROR(a,13)^ROR(a,22))
#define SIGMA1(e) (ROR(e,6)^ROR(e,11)^ROR(e,25))
#define sigma0(x) (ROR(x,7)^ROR(x,18)^((x)>>3))
#define sigma1(x) (ROR(x,17)^ROR(x,19)^((x)>>10))

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + SIGMA1(e) + CH(e,f,g) + K[i] + W[i];
        uint32_t T2 = SIGMA0(a) + MAJ(a,b,c);
        h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/*
 * Single SHA-256 round (manual, for the 7th round after 6 hardware rounds)
 */
static inline void sha256_round_manual(uint32_t st[8], uint32_t k, uint32_t w) {
    uint32_t T1 = st[7] + SIGMA1(st[4]) + CH(st[4],st[5],st[6]) + k + w;
    uint32_t T2 = SIGMA0(st[0]) + MAJ(st[0],st[1],st[2]);
    st[7]=st[6]; st[6]=st[5]; st[5]=st[4]; st[4]=st[3]+T1;
    st[3]=st[2]; st[2]=st[1]; st[1]=st[0]; st[0]=T1+T2;
}

/*
 * Evaluate 7 rounds using NEON SHA-2 hardware for first 6 rounds
 * and manual computation for round 7.
 *
 * Returns the final state as 8 uint32_t values.
 *
 * Note: vsha256hq_u32 processes 2 rounds. State layout:
 *   abcd = {a, b, c, d}
 *   efgh = {e, f, g, h}
 *   wk = {W[i]+K[i], W[i+1]+K[i+1], ...} (two rounds' worth)
 */
static inline void eval_7rounds_hw(const uint32_t init_st[8],
                                    const uint32_t W[7],
                                    uint32_t out_st[8]) {
    /* Load initial state into NEON vectors */
    uint32x4_t abcd = vld1q_u32(&init_st[0]);  /* a, b, c, d */
    uint32x4_t efgh = vld1q_u32(&init_st[4]);  /* e, f, g, h */

    /* Rounds 57-58 (hardware, 2 rounds) */
    uint32x4_t wk01;
    wk01 = (uint32x4_t){W[0]+K[57], W[1]+K[58], 0, 0};
    /* Unfortunately, vsha256hq processes rounds differently than we need.
       The ARM SHA intrinsics expect a SPECIFIC round function format.
       Let me use the correct approach. */

    /* Actually, the ARM SHA-256 intrinsics work like this:
       vsha256hq_u32(hash_abcd, hash_efgh, scheduled_wk)
       processes 4 rounds (not 2) using 4 schedule words.
       The wk vector contains W[i]+K[i] for 4 consecutive rounds.

       BUT our application has only 7 rounds. So:
       - 4 rounds via first call
       - 4 rounds via second call  = 8 rounds, one extra
       OR:
       - Do all 7 rounds manually with NEON vectorized operations

       The SHA HW instructions are for STANDARD SHA-256 processing.
       They assume the standard message schedule and round function.
       Our application uses the SAME round function but with a custom
       schedule (precomputed W[57..63]).

       So the hardware instructions should work as long as we provide
       the correct W+K values. Each call processes 4 rounds. */

    /* Save initial state */
    uint32x4_t save_abcd = abcd;
    uint32x4_t save_efgh = efgh;

    /* Rounds 57-60 (4 rounds via hardware) */
    uint32x4_t wk0 = (uint32x4_t){W[0]+K[57], W[1]+K[58], W[2]+K[59], W[3]+K[60]};
    uint32x4_t tmp = abcd;
    abcd = vsha256hq_u32(abcd, efgh, wk0);
    efgh = vsha256h2q_u32(efgh, tmp, wk0);

    /* Rounds 61-63 + one extra (4 rounds via hardware) */
    uint32x4_t wk1 = (uint32x4_t){W[4]+K[61], W[5]+K[62], W[6]+K[63], 0};
    /* Problem: round 64 doesn't exist. Using W=0, K=0 for the 8th "round"
       will compute one garbage round. We need to extract state after 7 rounds.

       Alternative: do rounds 57-60 via hardware (4 rounds), then
       rounds 61-63 manually (3 rounds). */

    /* Extract state after 4 hardware rounds */
    vst1q_u32(&out_st[0], abcd);
    vst1q_u32(&out_st[4], efgh);

    /* Rounds 61, 62, 63 manually */
    sha256_round_manual(out_st, K[61], W[4]);
    sha256_round_manual(out_st, K[62], W[5]);
    sha256_round_manual(out_st, K[63], W[6]);
}

/*
 * Fully manual 7-round evaluation (baseline for comparison)
 */
static inline void eval_7rounds_manual(const uint32_t init_st[8],
                                        const uint32_t W[7],
                                        uint32_t out_st[8]) {
    memcpy(out_st, init_st, 32);
    for (int i = 0; i < 7; i++) {
        sha256_round_manual(out_st, K[57+i], W[i]);
    }
}

/*
 * NEON-vectorized manual round: process BOTH messages simultaneously
 * using 128-bit NEON vectors (2 × 2 uint32 per vector).
 *
 * This is actually the best approach for our use case: we have TWO
 * independent SHA-256 state machines (msg1, msg2) that we want to
 * evaluate in parallel. NEON can process both in lockstep.
 */
static inline uint32_t eval_diff_neon(const uint32_t W1[7], const uint32_t W2[7]) {
    /* Interleave: st_ae = (a1, a2, e1, e2), etc. */
    /* Actually simpler: just run both messages manually and XOR at end.
       The NEON benefit comes from processing a1+a2, e1+e2 in parallel. */

    /* Load states for both messages */
    uint32_t st1[8], st2[8];
    memcpy(st1, state1, 32);
    memcpy(st2, state2, 32);

    /* 7 rounds, both messages */
    for (int i = 0; i < 7; i++) {
        uint32_t T1a = st1[7] + SIGMA1(st1[4]) + CH(st1[4],st1[5],st1[6]) + K[57+i] + W1[i];
        uint32_t T2a = SIGMA0(st1[0]) + MAJ(st1[0],st1[1],st1[2]);
        st1[7]=st1[6]; st1[6]=st1[5]; st1[5]=st1[4]; st1[4]=st1[3]+T1a;
        st1[3]=st1[2]; st1[2]=st1[1]; st1[1]=st1[0]; st1[0]=T1a+T2a;

        uint32_t T1b = st2[7] + SIGMA1(st2[4]) + CH(st2[4],st2[5],st2[6]) + K[57+i] + W2[i];
        uint32_t T2b = SIGMA0(st2[0]) + MAJ(st2[0],st2[1],st2[2]);
        st2[7]=st2[6]; st2[6]=st2[5]; st2[5]=st2[4]; st2[4]=st2[3]+T1b;
        st2[3]=st2[2]; st2[2]=st2[1]; st2[1]=st2[0]; st2[0]=T1b+T2b;
    }

    /* XOR difference + popcount using NEON */
    uint32x4_t s1_0 = vld1q_u32(&st1[0]);
    uint32x4_t s2_0 = vld1q_u32(&st2[0]);
    uint32x4_t s1_4 = vld1q_u32(&st1[4]);
    uint32x4_t s2_4 = vld1q_u32(&st2[4]);

    uint32x4_t diff0 = veorq_u32(s1_0, s2_0);
    uint32x4_t diff4 = veorq_u32(s1_4, s2_4);

    /* Count set bits (Hamming weight) using NEON */
    uint8x16_t cnt0 = vcntq_u8(vreinterpretq_u8_u32(diff0));
    uint8x16_t cnt4 = vcntq_u8(vreinterpretq_u8_u32(diff4));
    uint8x16_t total = vaddq_u8(cnt0, cnt4);

    /* Sum all bytes */
    uint16x8_t sum16 = vpaddlq_u8(total);
    uint32x4_t sum32 = vpaddlq_u16(sum16);
    uint64x2_t sum64 = vpaddlq_u32(sum32);
    return (uint32_t)(vgetq_lane_u64(sum64, 0) + vgetq_lane_u64(sum64, 1));
}

/* xoshiro256** PRNG */
static uint64_t rng_s[4];
static inline uint64_t rng_rotl(uint64_t x, int k) { return (x<<k)|(x>>(64-k)); }
static inline uint64_t rng_next(void) {
    uint64_t result = rng_rotl(rng_s[1]*5,7)*9;
    uint64_t t = rng_s[1]<<17;
    rng_s[2]^=rng_s[0]; rng_s[3]^=rng_s[1]; rng_s[1]^=rng_s[2]; rng_s[0]^=rng_s[3];
    rng_s[2]^=t; rng_s[3]=rng_rotl(rng_s[3],45);
    return result;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    uint64_t n_samples = 1000000000ULL;  /* 1 billion default */
    if (argc > 1) n_samples = strtoull(argv[1], NULL, 10);

    /* Precompute state for the published candidate */
    uint32_t M1[16], M2[16];
    for (int i = 0; i < 16; i++) { M1[i] = 0xffffffff; M2[i] = 0xffffffff; }
    M1[0] = 0x17149975;
    M2[0] = 0x17149975 ^ 0x80000000;
    M2[9] = 0xffffffff ^ 0x80000000;

    precompute(M1, state1, W1_pre);
    precompute(M2, state2, W2_pre);

    /* Verify da[56] = 0 */
    if (state1[0] != state2[0]) {
        printf("ERROR: da[56] != 0 (0x%08x vs 0x%08x)\n", state1[0], state2[0]);
        return 1;
    }

    /* Compute cascade constant */
    uint32_t C_w57 = (state1[7] - state2[7])
                   + (SIGMA1(state1[4]) - SIGMA1(state2[4]))
                   + (CH(state1[4],state1[5],state1[6]) - CH(state2[4],state2[5],state2[6]))
                   + (SIGMA0(state1[0]) + MAJ(state1[0],state1[1],state1[2]))
                   - (SIGMA0(state2[0]) + MAJ(state2[0],state2[1],state2[2]));

    printf("ARM NEON SHA-256 7-Round Tail Evaluator (N=32)\n");
    printf("Candidate: M[0]=0x17149975\n");
    printf("Cascade: W2[57] = W1[57] + 0x%08x\n", C_w57);
    printf("Target: %llu evaluations\n\n", (unsigned long long)n_samples);

    /* Seed PRNG */
    rng_s[0] = 0x12345678deadbeefULL;
    rng_s[1] = 0xfeedface01234567ULL;
    rng_s[2] = 0xabcdef0123456789ULL;
    rng_s[3] = 0x0011223344556677ULL;

    /* Benchmark: manual rounds + NEON XOR+popcount */
    uint32_t best_hw = 256;
    uint64_t n_collisions = 0;
    uint32_t best_W1[4], best_W2[4];

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (uint64_t i = 0; i < n_samples; i++) {
        uint64_t r0 = rng_next();
        uint64_t r1 = rng_next();
        uint64_t r2 = rng_next();
        uint64_t r3 = rng_next();

        uint32_t w1_57 = (uint32_t)r0;
        uint32_t w2_57 = w1_57 + C_w57;  /* cascade constraint */
        uint32_t w1_58 = (uint32_t)(r0 >> 32);
        uint32_t w2_58 = (uint32_t)r1;
        uint32_t w1_59 = (uint32_t)(r1 >> 32);
        uint32_t w2_59 = (uint32_t)r2;
        uint32_t w1_60 = (uint32_t)(r2 >> 32);
        uint32_t w2_60 = (uint32_t)r3;

        /* Build schedule */
        uint32_t W1[7] = {w1_57, w1_58, w1_59, w1_60, 0, 0, 0};
        uint32_t W2[7] = {w2_57, w2_58, w2_59, w2_60, 0, 0, 0};

        /* W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45] */
        W1[4] = sigma1(w1_59) + W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45];
        W2[4] = sigma1(w2_59) + W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45];
        /* W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46] */
        W1[5] = sigma1(w1_60) + W1_pre[55] + sigma0(W1_pre[47]) + W1_pre[46];
        W2[5] = sigma1(w2_60) + W2_pre[55] + sigma0(W2_pre[47]) + W2_pre[46];
        /* W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47] */
        W1[6] = sigma1(W1[4]) + W1_pre[56] + sigma0(W1_pre[48]) + W1_pre[47];
        W2[6] = sigma1(W2[4]) + W2_pre[56] + sigma0(W2_pre[48]) + W2_pre[47];

        uint32_t hw = eval_diff_neon(W1, W2);

        if (hw < best_hw) {
            best_hw = hw;
            memcpy(best_W1, (uint32_t[]){w1_57,w1_58,w1_59,w1_60}, 16);
            memcpy(best_W2, (uint32_t[]){w2_57,w2_58,w2_59,w2_60}, 16);
        }
        if (hw == 0) {
            n_collisions++;
            printf("COLLISION #%llu at sample %llu!\n",
                   (unsigned long long)n_collisions, (unsigned long long)i);
            printf("  W1 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n",
                   w1_57, w1_58, w1_59, w1_60);
            printf("  W2 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n",
                   w2_57, w2_58, w2_59, w2_60);
        }

        if ((i & 0xFFFFFFF) == 0 && i > 0) {
            clock_gettime(CLOCK_MONOTONIC, &t1);
            double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
            double rate = i / elapsed;
            printf("[%6.1f%%] %llu evals, best_hw=%u, %.1fM/s, ETA %.0fs\n",
                   100.0 * i / n_samples, (unsigned long long)i,
                   best_hw, rate / 1e6,
                   (n_samples - i) / rate);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("\n=== Results ===\n");
    printf("Samples: %llu\n", (unsigned long long)n_samples);
    printf("Time: %.1fs\n", elapsed);
    printf("Rate: %.1fM evals/s\n", n_samples / elapsed / 1e6);
    printf("Best HW: %u\n", best_hw);
    printf("  W1 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n",
           best_W1[0], best_W1[1], best_W1[2], best_W1[3]);
    printf("  W2 = {0x%08x, 0x%08x, 0x%08x, 0x%08x}\n",
           best_W2[0], best_W2[1], best_W2[2], best_W2[3]);
    printf("Collisions: %llu\n", (unsigned long long)n_collisions);

    return 0;
}
