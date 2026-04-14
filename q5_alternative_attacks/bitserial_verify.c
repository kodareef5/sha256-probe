/*
 * bitserial_verify.c — Verify that sr=60 collisions at N=4 are fully
 *                       characterized by the single equation dT1_61 = 0.
 *
 * Theory: In the cascade framework (MSB kernel, W2 derived from W1 to
 * enforce da=0 at rounds 57-60), the remaining freedom is W1[57..60].
 * The claim is that after these 4 cascade rounds, the ONLY condition
 * needed for a full collision (all 8 register diffs = 0 after round 63)
 * is that dT1 at round 61 equals zero: T1_path1 - T1_path2 = 0 mod 2^N.
 *
 * This tool exhaustively checks all 2^16 = 65536 combos at N=4 and
 * compares the collision set against the dT1_61 = 0 set.
 *
 * Setup: N=4, MSB kernel, M[0]=0x0, fill=0xf
 *
 * Compile: gcc -O3 -march=native -o bitserial_verify bitserial_verify.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ===== Mini-SHA-256 at N bits ===== */

#define N 4
#define MASK ((1U << N) - 1)
#define MSB  (1U << (N - 1))

/* Scaled rotation amounts (banker's rounding, minimum 1) */
static int r_Sig0[3], r_Sig1[3], r_sig0[2], r_sig1[2], s_sig0, s_sig1;
static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

/* N-bit rotate right */
static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N;
    return ((x >> k) | (x << (N - k))) & MASK;
}

/* SHA-256 functions, truncated to N bits */
static inline uint32_t fn_S0(uint32_t a)  { return ror_n(a, r_Sig0[0]) ^ ror_n(a, r_Sig0[1]) ^ ror_n(a, r_Sig0[2]); }
static inline uint32_t fn_S1(uint32_t e)  { return ror_n(e, r_Sig1[0]) ^ ror_n(e, r_Sig1[1]) ^ ror_n(e, r_Sig1[2]); }
static inline uint32_t fn_s0(uint32_t x)  { return ror_n(x, r_sig0[0]) ^ ror_n(x, r_sig0[1]) ^ ((x >> s_sig0) & MASK); }
static inline uint32_t fn_s1(uint32_t x)  { return ror_n(x, r_sig1[0]) ^ ror_n(x, r_sig1[1]) ^ ((x >> s_sig1) & MASK); }
static inline uint32_t fn_Ch(uint32_t e, uint32_t f, uint32_t g)  { return ((e & f) ^ ((~e) & g)) & MASK; }
static inline uint32_t fn_Maj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & MASK; }

/* Full SHA-256 constants */
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

/* N-bit constants and precomputed state */
static uint32_t KN[64], IVN[8];
static uint32_t state1[8], state2[8];     /* register state at round 57 */
static uint32_t W1_pre[57], W2_pre[57];   /* precomputed schedule words 0..56 */

/* Precompute: expand message schedule through W[56], run rounds 0-56,
 * store resulting register state and schedule words. */
static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fn_s1(W[i-2]) + W[i-7] + fn_s0(W[i-15]) + W[i-16]) & MASK;

    uint32_t a = IVN[0], b = IVN[1], c = IVN[2], d = IVN[3];
    uint32_t e = IVN[4], f = IVN[5], g = IVN[6], h = IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fn_S1(e) + fn_Ch(e,f,g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fn_S0(a) + fn_Maj(a,b,c)) & MASK;
        h = g; g = f; f = e; e = (d + T1) & MASK;
        d = c; c = b; b = a; a = (T1 + T2) & MASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

/* One SHA-256 round: mutates state s in place.
 * s[0..7] = a,b,c,d,e,f,g,h */
static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fn_S1(s[4]) + fn_Ch(s[4],s[5],s[6]) + k + w) & MASK;
    uint32_t T2 = (fn_S0(s[0]) + fn_Maj(s[0],s[1],s[2])) & MASK;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = (s[3] + T1) & MASK;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = (T1 + T2) & MASK;
}

/* Compute T1 for a given state and round word (without modifying state).
 * T1 = h + Sigma1(e) + Ch(e,f,g) + K[round] + W[round] */
static inline uint32_t compute_T1(const uint32_t s[8], uint32_t k, uint32_t w) {
    return (s[7] + fn_S1(s[4]) + fn_Ch(s[4],s[5],s[6]) + k + w) & MASK;
}

/* Cascade offset: given state57 for both messages, find W2[k] such that
 * da_{round+1} = 0, i.e., the 'a' register difference is cancelled.
 *
 * a_new = T1 + T2. For da_new = 0:
 *   T1_path1 + T2_path1 = T1_path2 + T2_path2
 *   (rest1 + W1) + T2_1 = (rest2 + W2) + T2_2
 *   W2 = W1 + (rest1 - rest2) + (T2_1 - T2_2)
 * where rest = h + Sigma1(e) + Ch(e,f,g) + K[round]  (everything in T1 except W) */
static uint32_t find_w2_cascade(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t rest1 = (s1[7] + fn_S1(s1[4]) + fn_Ch(s1[4],s1[5],s1[6]) + KN[rnd]) & MASK;
    uint32_t rest2 = (s2[7] + fn_S1(s2[4]) + fn_Ch(s2[4],s2[5],s2[6]) + KN[rnd]) & MASK;
    uint32_t T2_1  = (fn_S0(s1[0]) + fn_Maj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T2_2  = (fn_S0(s2[0]) + fn_Maj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + rest1 - rest2 + T2_1 - T2_2) & MASK;
}

int main(void) {
    setbuf(stdout, NULL);

    /* ===== 1. Initialize N=4 parameters ===== */
    r_Sig0[0] = scale_rot(2);  r_Sig0[1] = scale_rot(13); r_Sig0[2] = scale_rot(22);
    r_Sig1[0] = scale_rot(6);  r_Sig1[1] = scale_rot(11); r_Sig1[2] = scale_rot(25);
    r_sig0[0] = scale_rot(7);  r_sig0[1] = scale_rot(18); s_sig0 = scale_rot(3);
    r_sig1[0] = scale_rot(17); r_sig1[1] = scale_rot(19); s_sig1 = scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & MASK;

    printf("=== Bitserial Collision Characterization Verifier ===\n");
    printf("N=%d, MASK=0x%x, MSB=0x%x\n", N, MASK, MSB);
    printf("Rotation amounts:\n");
    printf("  Sigma0: {%d, %d, %d}\n", r_Sig0[0], r_Sig0[1], r_Sig0[2]);
    printf("  Sigma1: {%d, %d, %d}\n", r_Sig1[0], r_Sig1[1], r_Sig1[2]);
    printf("  sigma0: {%d, %d, >>%d}\n", r_sig0[0], r_sig0[1], s_sig0);
    printf("  sigma1: {%d, %d, >>%d}\n", r_sig1[0], r_sig1[1], s_sig1);

    /* ===== 2. Set up the candidate: M[0]=0x0, fill=0xf ===== */
    uint32_t m0_val  = 0x0;
    uint32_t fill    = MASK;  /* 0xf at N=4 */

    uint32_t M1[16], M2[16];
    for (int i = 0; i < 16; i++) { M1[i] = fill; M2[i] = fill; }
    /* MSB kernel: flip MSB of M[0] and M[9] between paths */
    M1[0] = m0_val;
    M2[0] = m0_val ^ MSB;
    M2[9] = fill ^ MSB;

    printf("\nCandidate setup:\n");
    printf("  M[0] = 0x%x, fill = 0x%x\n", m0_val, fill);
    printf("  MSB kernel: dM[0] = 0x%x, dM[9] = 0x%x\n", MSB, MSB);

    /* Precompute schedule + state through round 56 for both paths */
    precompute(M1, state1, W1_pre);
    precompute(M2, state2, W2_pre);

    /* Verify da[56] = 0 (required for cascade to be valid) */
    uint32_t da56 = (state1[0] ^ state2[0]) & MASK;
    printf("  da[56] = 0x%x %s\n", da56, da56 == 0 ? "(OK)" : "(FAIL - not a valid candidate!)");
    if (da56 != 0) {
        printf("ERROR: da[56] != 0. This M[0]/fill combo is not a valid sr=60 candidate.\n");
        return 1;
    }

    /* Print the full differential state at round 57 entry */
    printf("\nState at round 57 (after 57 rounds of precomputation):\n");
    printf("  Path 1: a=%x b=%x c=%x d=%x e=%x f=%x g=%x h=%x\n",
           state1[0],state1[1],state1[2],state1[3],
           state1[4],state1[5],state1[6],state1[7]);
    printf("  Path 2: a=%x b=%x c=%x d=%x e=%x f=%x g=%x h=%x\n",
           state2[0],state2[1],state2[2],state2[3],
           state2[4],state2[5],state2[6],state2[7]);
    printf("  Diffs:  da=%x db=%x dc=%x dd=%x de=%x df=%x dg=%x dh=%x\n",
           (state1[0]^state2[0])&MASK, (state1[1]^state2[1])&MASK,
           (state1[2]^state2[2])&MASK, (state1[3]^state2[3])&MASK,
           (state1[4]^state2[4])&MASK, (state1[5]^state2[5])&MASK,
           (state1[6]^state2[6])&MASK, (state1[7]^state2[7])&MASK);

    /* ===== 3. Exhaustive enumeration of all 2^(4N) = 2^16 message combos ===== */
    /*
     * The cascade approach:
     *   - Choose W1[57], W1[58], W1[59], W1[60] freely (the 4 free words)
     *   - Derive W2[57..60] via cascade offset to enforce da=0 at each step
     *   - Compute schedule-determined W[61..63] for both paths
     *   - Run remaining rounds 61-63
     *   - Check for collision and independently compute dT1_61
     */
    printf("\n=== Exhaustive Enumeration: 2^%d = %u configs ===\n\n", 4*N, 1U << (4*N));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    uint64_t n_tested     = 0;
    uint64_t n_collisions = 0;
    uint64_t n_dT1_61_zero = 0;
    /* Overlap tracking */
    uint64_t n_both       = 0;  /* collision AND dT1_61=0 */
    uint64_t n_coll_only  = 0;  /* collision but dT1_61!=0 */
    uint64_t n_dT1_only   = 0;  /* dT1_61=0 but not collision */

    /* Also track dT1 values at other rounds for diagnostics */
    uint64_t n_dT1_57_zero = 0;
    uint64_t n_dT1_58_zero = 0;
    uint64_t n_dT1_59_zero = 0;
    uint64_t n_dT1_60_zero = 0;
    uint64_t n_dT1_62_zero = 0;
    uint64_t n_dT1_63_zero = 0;

    /* Store first few examples of each category for diagnostics */
    #define MAX_EXAMPLES 5
    typedef struct {
        uint32_t w1[4], w2[4];
        uint32_t dT1_61;
    } example_t;
    example_t coll_examples[MAX_EXAMPLES];
    example_t dT1_examples[MAX_EXAMPLES];
    example_t coll_only_examples[MAX_EXAMPLES];
    example_t dT1_only_examples[MAX_EXAMPLES];
    int n_coll_ex = 0, n_dT1_ex = 0, n_coll_only_ex = 0, n_dT1_only_ex = 0;

    for (uint32_t w1_57 = 0; w1_57 < (1U << N); w1_57++) {
        /* --- Round 57: apply cascade for da=0 --- */
        uint32_t s57_1[8], s57_2[8];
        memcpy(s57_1, state1, 32);
        memcpy(s57_2, state2, 32);
        uint32_t w2_57 = find_w2_cascade(s57_1, s57_2, 57, w1_57);
        sha_round(s57_1, KN[57], w1_57);
        sha_round(s57_2, KN[57], w2_57);

        for (uint32_t w1_58 = 0; w1_58 < (1U << N); w1_58++) {
            /* --- Round 58: apply cascade for da=0 --- */
            uint32_t s58_1[8], s58_2[8];
            memcpy(s58_1, s57_1, 32);
            memcpy(s58_2, s57_2, 32);
            uint32_t w2_58 = find_w2_cascade(s58_1, s58_2, 58, w1_58);
            sha_round(s58_1, KN[58], w1_58);
            sha_round(s58_2, KN[58], w2_58);

            for (uint32_t w1_59 = 0; w1_59 < (1U << N); w1_59++) {
                /* --- Round 59: apply cascade for da=0 --- */
                uint32_t s59_1[8], s59_2[8];
                memcpy(s59_1, s58_1, 32);
                memcpy(s59_2, s58_2, 32);
                uint32_t w2_59 = find_w2_cascade(s59_1, s59_2, 59, w1_59);
                sha_round(s59_1, KN[59], w1_59);
                sha_round(s59_2, KN[59], w2_59);

                for (uint32_t w1_60 = 0; w1_60 < (1U << N); w1_60++) {
                    /* --- Round 60: apply cascade for da=0 --- */
                    uint32_t s60_1[8], s60_2[8];
                    memcpy(s60_1, s59_1, 32);
                    memcpy(s60_2, s59_2, 32);
                    uint32_t w2_60 = find_w2_cascade(s60_1, s60_2, 60, w1_60);
                    sha_round(s60_1, KN[60], w1_60);
                    sha_round(s60_2, KN[60], w2_60);

                    /* --- Compute schedule-determined words W[61..63] ---
                     * W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]
                     *
                     * For rounds 61-63 (absolute), the free words are at
                     * indices 57-60 in the schedule, so:
                     *   W[61] = s1(W[59]) + W[54] + s0(W[46]) + W[45]
                     *   W[62] = s1(W[60]) + W[55] + s0(W[47]) + W[46]
                     *   W[63] = s1(W[61]) + W[56] + s0(W[48]) + W[47]
                     * where W[45..56] are precomputed constants. */
                    uint32_t W1_61 = (fn_s1(w1_59)  + W1_pre[54] + fn_s0(W1_pre[46]) + W1_pre[45]) & MASK;
                    uint32_t W2_61 = (fn_s1(w2_59)  + W2_pre[54] + fn_s0(W2_pre[46]) + W2_pre[45]) & MASK;
                    uint32_t W1_62 = (fn_s1(w1_60)  + W1_pre[55] + fn_s0(W1_pre[47]) + W1_pre[46]) & MASK;
                    uint32_t W2_62 = (fn_s1(w2_60)  + W2_pre[55] + fn_s0(W2_pre[47]) + W2_pre[46]) & MASK;
                    uint32_t W1_63 = (fn_s1(W1_61)  + W1_pre[56] + fn_s0(W1_pre[48]) + W1_pre[47]) & MASK;
                    uint32_t W2_63 = (fn_s1(W2_61)  + W2_pre[56] + fn_s0(W2_pre[48]) + W2_pre[47]) & MASK;

                    /* === (a) Compute dT1 at round 61 BEFORE running round 61 ===
                     *
                     * T1 = h + Sigma1(e) + Ch(e,f,g) + K[61] + W[61]
                     *
                     * The state entering round 61 is s60_1/s60_2 (after rounds 57-60).
                     * dT1_61 = T1_path1 - T1_path2  (arithmetic difference mod 2^N) */
                    uint32_t T1_61_path1 = compute_T1(s60_1, KN[61], W1_61);
                    uint32_t T1_61_path2 = compute_T1(s60_2, KN[61], W2_61);
                    uint32_t dT1_61 = (T1_61_path1 - T1_61_path2) & MASK;

                    int dT1_61_is_zero = (dT1_61 == 0);
                    if (dT1_61_is_zero) n_dT1_61_zero++;

                    /* === Also compute dT1 at every round for diagnostics === */
                    {
                        /* Round 57: use pre-cascade state */
                        uint32_t t1a = compute_T1(state1, KN[57], w1_57);
                        uint32_t t1b = compute_T1(state2, KN[57], w2_57);
                        if (((t1a - t1b) & MASK) == 0) n_dT1_57_zero++;
                    }
                    {
                        /* Round 58: use post-round-57 state */
                        uint32_t ts1[8], ts2[8];
                        memcpy(ts1, state1, 32); memcpy(ts2, state2, 32);
                        sha_round(ts1, KN[57], w1_57); sha_round(ts2, KN[57], w2_57);
                        uint32_t t1a = compute_T1(ts1, KN[58], w1_58);
                        uint32_t t1b = compute_T1(ts2, KN[58], w2_58);
                        if (((t1a - t1b) & MASK) == 0) n_dT1_58_zero++;
                    }
                    {
                        /* Round 59: use s58 state (already computed above) */
                        uint32_t t1a = compute_T1(s58_1, KN[59], w1_59);
                        uint32_t t1b = compute_T1(s58_2, KN[59], w2_59);
                        if (((t1a - t1b) & MASK) == 0) n_dT1_59_zero++;
                    }
                    {
                        /* Round 60: use s59 state (already computed above) */
                        uint32_t t1a = compute_T1(s59_1, KN[60], w1_60);
                        uint32_t t1b = compute_T1(s59_2, KN[60], w2_60);
                        if (((t1a - t1b) & MASK) == 0) n_dT1_60_zero++;
                    }

                    /* === (b) Run rounds 61-63 to check full collision === */
                    uint32_t final1[8], final2[8];
                    memcpy(final1, s60_1, 32);
                    memcpy(final2, s60_2, 32);
                    sha_round(final1, KN[61], W1_61);
                    sha_round(final2, KN[61], W2_61);

                    /* dT1 at round 62 (state entering round 62 = final state after round 61) */
                    {
                        uint32_t t1a = compute_T1(final1, KN[62], W1_62);
                        uint32_t t1b = compute_T1(final2, KN[62], W2_62);
                        if (((t1a - t1b) & MASK) == 0) n_dT1_62_zero++;
                    }

                    sha_round(final1, KN[62], W1_62);
                    sha_round(final2, KN[62], W2_62);

                    /* dT1 at round 63 (state entering round 63) */
                    {
                        uint32_t t1a = compute_T1(final1, KN[63], W1_63);
                        uint32_t t1b = compute_T1(final2, KN[63], W2_63);
                        if (((t1a - t1b) & MASK) == 0) n_dT1_63_zero++;
                    }

                    sha_round(final1, KN[63], W1_63);
                    sha_round(final2, KN[63], W2_63);

                    /* === (c) Check collision: all 8 register diffs = 0 === */
                    int is_collision = 1;
                    for (int r = 0; r < 8; r++) {
                        if (final1[r] != final2[r]) { is_collision = 0; break; }
                    }
                    if (is_collision) n_collisions++;

                    /* === (d) Classify into overlap categories === */
                    if (is_collision && dT1_61_is_zero) {
                        n_both++;
                        if (n_coll_ex < MAX_EXAMPLES) {
                            coll_examples[n_coll_ex].w1[0] = w1_57;
                            coll_examples[n_coll_ex].w1[1] = w1_58;
                            coll_examples[n_coll_ex].w1[2] = w1_59;
                            coll_examples[n_coll_ex].w1[3] = w1_60;
                            coll_examples[n_coll_ex].w2[0] = w2_57;
                            coll_examples[n_coll_ex].w2[1] = w2_58;
                            coll_examples[n_coll_ex].w2[2] = w2_59;
                            coll_examples[n_coll_ex].w2[3] = w2_60;
                            coll_examples[n_coll_ex].dT1_61 = dT1_61;
                            n_coll_ex++;
                        }
                    } else if (is_collision && !dT1_61_is_zero) {
                        n_coll_only++;
                        if (n_coll_only_ex < MAX_EXAMPLES) {
                            coll_only_examples[n_coll_only_ex].w1[0] = w1_57;
                            coll_only_examples[n_coll_only_ex].w1[1] = w1_58;
                            coll_only_examples[n_coll_only_ex].w1[2] = w1_59;
                            coll_only_examples[n_coll_only_ex].w1[3] = w1_60;
                            coll_only_examples[n_coll_only_ex].w2[0] = w2_57;
                            coll_only_examples[n_coll_only_ex].w2[1] = w2_58;
                            coll_only_examples[n_coll_only_ex].w2[2] = w2_59;
                            coll_only_examples[n_coll_only_ex].w2[3] = w2_60;
                            coll_only_examples[n_coll_only_ex].dT1_61 = dT1_61;
                            n_coll_only_ex++;
                        }
                    } else if (!is_collision && dT1_61_is_zero) {
                        n_dT1_only++;
                        if (n_dT1_only_ex < MAX_EXAMPLES) {
                            dT1_only_examples[n_dT1_only_ex].w1[0] = w1_57;
                            dT1_only_examples[n_dT1_only_ex].w1[1] = w1_58;
                            dT1_only_examples[n_dT1_only_ex].w1[2] = w1_59;
                            dT1_only_examples[n_dT1_only_ex].w1[3] = w1_60;
                            dT1_only_examples[n_dT1_only_ex].w2[0] = w2_57;
                            dT1_only_examples[n_dT1_only_ex].w2[1] = w2_58;
                            dT1_only_examples[n_dT1_only_ex].w2[2] = w2_59;
                            dT1_only_examples[n_dT1_only_ex].w2[3] = w2_60;
                            dT1_only_examples[n_dT1_only_ex].dT1_61 = dT1_61;
                            n_dT1_only_ex++;
                        }
                    }

                    n_tested++;
                }
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    /* ===== 4. Report results ===== */
    printf("\n");
    printf("============================================================\n");
    printf("  RESULTS: Bitserial Collision Characterization at N=%d\n", N);
    printf("  M[0]=0x%x, fill=0x%x, MSB kernel\n", m0_val, fill);
    printf("============================================================\n\n");

    printf("Configs tested:       %llu (2^%d = %u)\n",
           (unsigned long long)n_tested, 4*N, 1U << (4*N));
    printf("Time:                 %.4f seconds\n\n", elapsed);

    printf("--- Set A: Full collisions (all 8 register diffs = 0) ---\n");
    printf("  Count:              %llu\n", (unsigned long long)n_collisions);
    printf("  Density:            1 per %.1f configs\n",
           n_collisions > 0 ? (double)n_tested / n_collisions : 0.0);
    printf("\n");

    printf("--- Set B: dT1_61 = 0 (T1_path1 == T1_path2 at round 61) ---\n");
    printf("  Count:              %llu\n", (unsigned long long)n_dT1_61_zero);
    printf("  Density:            1 per %.1f configs\n",
           n_dT1_61_zero > 0 ? (double)n_tested / n_dT1_61_zero : 0.0);
    printf("\n");

    printf("--- Set comparison ---\n");
    printf("  A intersect B:      %llu  (collision AND dT1_61=0)\n",
           (unsigned long long)n_both);
    printf("  A \\ B:              %llu  (collision but dT1_61 != 0)\n",
           (unsigned long long)n_coll_only);
    printf("  B \\ A:              %llu  (dT1_61=0 but not collision)\n",
           (unsigned long long)n_dT1_only);
    printf("\n");

    /* The key verdict */
    if (n_collisions == n_dT1_61_zero && n_coll_only == 0 && n_dT1_only == 0) {
        printf("*** VERDICT: SETS ARE IDENTICAL ***\n");
        printf("    Every collision has dT1_61=0, and every dT1_61=0 is a collision.\n");
        printf("    The single equation dT1_61=0 FULLY CHARACTERIZES sr=60 collisions.\n");
    } else if (n_coll_only == 0 && n_dT1_only > 0) {
        printf("*** VERDICT: Collisions are a STRICT SUBSET of dT1_61=0 ***\n");
        printf("    Every collision has dT1_61=0 (necessary), but dT1_61=0 is not sufficient.\n");
        printf("    There are %llu configs with dT1_61=0 that are NOT collisions.\n",
               (unsigned long long)n_dT1_only);
    } else if (n_coll_only > 0 && n_dT1_only == 0) {
        printf("*** VERDICT: dT1_61=0 is a STRICT SUBSET of collisions ***\n");
        printf("    Every dT1_61=0 is a collision, but %llu collisions have dT1_61 != 0.\n",
               (unsigned long long)n_coll_only);
    } else if (n_coll_only > 0 && n_dT1_only > 0) {
        printf("*** VERDICT: PARTIAL OVERLAP ***\n");
        printf("    %llu collisions have dT1_61 != 0, and %llu dT1_61=0 are not collisions.\n",
               (unsigned long long)n_coll_only, (unsigned long long)n_dT1_only);
    } else {
        printf("*** VERDICT: DISJOINT (no overlap at all!) ***\n");
    }

    /* Print dT1 statistics at ALL rounds for context */
    printf("\n--- dT1=0 counts at each round (diagnostics) ---\n");
    printf("  Round 57: %llu / %llu  (%.2f%%)\n",
           (unsigned long long)n_dT1_57_zero, (unsigned long long)n_tested,
           100.0 * n_dT1_57_zero / n_tested);
    printf("  Round 58: %llu / %llu  (%.2f%%)\n",
           (unsigned long long)n_dT1_58_zero, (unsigned long long)n_tested,
           100.0 * n_dT1_58_zero / n_tested);
    printf("  Round 59: %llu / %llu  (%.2f%%)\n",
           (unsigned long long)n_dT1_59_zero, (unsigned long long)n_tested,
           100.0 * n_dT1_59_zero / n_tested);
    printf("  Round 60: %llu / %llu  (%.2f%%)\n",
           (unsigned long long)n_dT1_60_zero, (unsigned long long)n_tested,
           100.0 * n_dT1_60_zero / n_tested);
    printf("  Round 61: %llu / %llu  (%.2f%%)  <-- THE KEY EQUATION\n",
           (unsigned long long)n_dT1_61_zero, (unsigned long long)n_tested,
           100.0 * n_dT1_61_zero / n_tested);
    printf("  Round 62: %llu / %llu  (%.2f%%)\n",
           (unsigned long long)n_dT1_62_zero, (unsigned long long)n_tested,
           100.0 * n_dT1_62_zero / n_tested);
    printf("  Round 63: %llu / %llu  (%.2f%%)\n",
           (unsigned long long)n_dT1_63_zero, (unsigned long long)n_tested,
           100.0 * n_dT1_63_zero / n_tested);

    /* Print example collisions */
    if (n_coll_ex > 0) {
        printf("\n--- Example collisions (with dT1_61=0) ---\n");
        for (int i = 0; i < n_coll_ex; i++) {
            printf("  #%d: W1=[%x,%x,%x,%x] W2=[%x,%x,%x,%x] dT1_61=0x%x\n",
                   i+1,
                   coll_examples[i].w1[0], coll_examples[i].w1[1],
                   coll_examples[i].w1[2], coll_examples[i].w1[3],
                   coll_examples[i].w2[0], coll_examples[i].w2[1],
                   coll_examples[i].w2[2], coll_examples[i].w2[3],
                   coll_examples[i].dT1_61);
        }
    }
    if (n_coll_only_ex > 0) {
        printf("\n--- Collisions WITHOUT dT1_61=0 (counterexamples!) ---\n");
        for (int i = 0; i < n_coll_only_ex; i++) {
            printf("  #%d: W1=[%x,%x,%x,%x] W2=[%x,%x,%x,%x] dT1_61=0x%x\n",
                   i+1,
                   coll_only_examples[i].w1[0], coll_only_examples[i].w1[1],
                   coll_only_examples[i].w1[2], coll_only_examples[i].w1[3],
                   coll_only_examples[i].w2[0], coll_only_examples[i].w2[1],
                   coll_only_examples[i].w2[2], coll_only_examples[i].w2[3],
                   coll_only_examples[i].dT1_61);
        }
    }
    if (n_dT1_only_ex > 0) {
        printf("\n--- dT1_61=0 that are NOT collisions ---\n");
        for (int i = 0; i < n_dT1_only_ex; i++) {
            printf("  #%d: W1=[%x,%x,%x,%x] W2=[%x,%x,%x,%x] dT1_61=0x%x\n",
                   i+1,
                   dT1_only_examples[i].w1[0], dT1_only_examples[i].w1[1],
                   dT1_only_examples[i].w1[2], dT1_only_examples[i].w1[3],
                   dT1_only_examples[i].w2[0], dT1_only_examples[i].w2[1],
                   dT1_only_examples[i].w2[2], dT1_only_examples[i].w2[3],
                   dT1_only_examples[i].dT1_61);
        }
    }

    printf("\nDone.\n");
    return 0;
}
