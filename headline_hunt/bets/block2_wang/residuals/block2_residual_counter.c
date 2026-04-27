/* block2_residual_counter.c — fast residual HW counter for block2_wang.
 *
 * For a cand (m0, fill, bit), generate N random (W1_57, W1_58, W1_59, W1_60)
 * tuples. Apply cascade-1 at slots 57-59 (forces da[57..59]=0). Apply
 * cascade-2 at slot 60 (forces de[60]=0). Forward through rounds 61-63
 * using the schedule recursion W[k] = sigma1(W[k-2]) + W[k-7] +
 * sigma0(W[k-15]) + W[k-16].
 *
 * Need W1[0..56] (the "prefix") computed from the default message
 * [m0, fill, fill, ..., fill] for the schedule recursion to work at
 * slots 61-63.
 *
 * Output: HW distribution of round-63 residuals (sum across 8 registers).
 * Identify W1_60 values producing min-HW residuals.
 *
 * Compile: gcc -O3 -march=native -o block2_residual_counter block2_residual_counter.c
 * Usage:   ./block2_residual_counter 0x189b13c7 0x80000000 31 1000000 [seed]
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef uint32_t u32;

static inline u32 ROR(u32 x, int n) { return (x >> n) | (x << (32 - n)); }
static inline u32 Ch(u32 e, u32 f, u32 g) { return (e & f) ^ ((~e) & g); }
static inline u32 Maj(u32 a, u32 b, u32 c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline u32 Sigma0(u32 a) { return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22); }
static inline u32 Sigma1(u32 e) { return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25); }
static inline u32 sigma0_(u32 x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline u32 sigma1_(u32 x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }

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
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
};

static inline u32 cw1(const u32 s1[8], const u32 s2[8]) {
    return (s1[7] - s2[7]) + (Sigma1(s1[4]) - Sigma1(s2[4]))
         + (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6]))
         + (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]))
         - (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]));
}

/* cascade-2 offset at slot 60: dW[60] needed for de[60]=0.
 * de[60] = dd[59] + dT1_60 = de[58] + dT1_60 (since dd_59 = de_58 by shift)
 * Wait — under cascade-1, de[58] != 0 generally. Let me use the formula
 * straightforwardly: pick W2_60 such that e_60_1 == e_60_2.
 * e_60 = d_59 + T1_60. Setting e_60_1 == e_60_2:
 *   d_59_1 + T1_60_1 == d_59_2 + T1_60_2
 *   T1_60_1 - T1_60_2 == d_59_2 - d_59_1
 * dT1_60 = -(d_59_1 - d_59_2) = d_59_2 - d_59_1.
 * dT1_60 = dh_60 + dSig1_60 + dCh_60 + dW_60
 * So dW_60 = -(dh_60 + dSig1_60 + dCh_60) + (d_59_2 - d_59_1)
 *
 * In our state vec convention, d_59 = state[3] before round 60 = c_58
 * = a_57. Under cascade-1 da[57]=0, so a_57_1 = a_57_2, so d_59_1 = d_59_2.
 * Hence dW_60 = -(dh_60 + dSig1_60 + dCh_60).
 *
 * But wait — under our F14 finding, cascade-1 at slot 60 ALREADY gives
 * de[60]=0 as a side effect. So cw1[60] (the cascade-1 offset) = the
 * cascade-2-required value. They're the same thing.
 *
 * So we can use cw1[60] for cascade-2 in the corpus.
 */

static inline void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

static inline u32 xorshift32(u32 *state) {
    u32 x = *state; x ^= x << 13; x ^= x >> 17; x ^= x << 5; *state = x; return x;
}

static inline int popcnt8(const u32 v[8]) {
    return __builtin_popcount(v[0]) + __builtin_popcount(v[1]) +
           __builtin_popcount(v[2]) + __builtin_popcount(v[3]) +
           __builtin_popcount(v[4]) + __builtin_popcount(v[5]) +
           __builtin_popcount(v[6]) + __builtin_popcount(v[7]);
}

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s m0 fill bit nsamples [seed]\n", argv[0]);
        return 1;
    }
    u32 m0 = strtoul(argv[1], NULL, 0);
    u32 fill = strtoul(argv[2], NULL, 0);
    int bit = atoi(argv[3]);
    uint64_t n = strtoull(argv[4], NULL, 0);
    u32 seed = (argc >= 6) ? strtoul(argv[5], NULL, 0) : 0xdeadbeef;

    u32 kernel_mask = (u32)1 << bit;

    /* Build default message + schedule. */
    u32 M1[16], M2[16];
    M1[0] = m0;
    for (int i = 1; i < 16; i++) M1[i] = fill;
    memcpy(M2, M1, sizeof M2);
    M2[0] ^= kernel_mask;
    M2[9] ^= kernel_mask;

    u32 W1_pre[64], W2_pre[64];
    for (int i = 0; i < 16; i++) { W1_pre[i] = M1[i]; W2_pre[i] = M2[i]; }
    for (int i = 16; i < 64; i++) {
        W1_pre[i] = sigma1_(W1_pre[i-2]) + W1_pre[i-7] + sigma0_(W1_pre[i-15]) + W1_pre[i-16];
        W2_pre[i] = sigma1_(W2_pre[i-2]) + W2_pre[i-7] + sigma0_(W2_pre[i-15]) + W2_pre[i-16];
    }

    /* Precompute slot-57 input states. */
    u32 s1_pre[8], s2_pre[8];
    for (int i = 0; i < 8; i++) { s1_pre[i] = IV[i]; s2_pre[i] = IV[i]; }
    for (int r = 0; r < 57; r++) {
        sha_round(s1_pre, K[r], W1_pre[r]);
        sha_round(s2_pre, K[r], W2_pre[r]);
    }

    /* Verify cascade-eligibility. */
    if (s1_pre[0] != s2_pre[0]) {
        fprintf(stderr, "WARN: cascade-1 not held at slot 57 input (da[57]!=0)\n");
        return 1;
    }

    /* Random sample (W1_57, W1_58, W1_59, W1_60). Apply cascade-1 at each
     * slot. Forward through 61-63 using schedule. Track HW. */
    u32 rng = seed;
    u32 hw_dist[33] = {0};  /* total HW across all 8 registers at slot 64 */
    uint64_t low_hw_count = 0;
    u32 min_hw = 256;
    u32 best_W57 = 0, best_W58 = 0, best_W59 = 0, best_W60 = 0;

    /* Track best 5 low-HW examples */
    struct {
        u32 W1_57, W1_58, W1_59, W1_60;
        u32 hw;
        u32 d_state[8];
    } best5[5];
    int n_best = 0;

    clock_t t0 = clock();
    for (uint64_t i = 0; i < n; i++) {
        u32 W1_57 = xorshift32(&rng);
        u32 W1_58 = xorshift32(&rng);
        u32 W1_59 = xorshift32(&rng);
        u32 W1_60 = xorshift32(&rng);

        u32 s1[8], s2[8];
        memcpy(s1, s1_pre, sizeof s1);
        memcpy(s2, s2_pre, sizeof s2);

        /* slot 57 cascade-1 */
        u32 cw57 = cw1(s1, s2);
        sha_round(s1, K[57], W1_57);
        sha_round(s2, K[57], W1_57 + cw57);

        /* slot 58 cascade-1 */
        u32 cw58 = cw1(s1, s2);
        sha_round(s1, K[58], W1_58);
        sha_round(s2, K[58], W1_58 + cw58);

        /* slot 59 cascade-1 */
        u32 cw59 = cw1(s1, s2);
        sha_round(s1, K[59], W1_59);
        sha_round(s2, K[59], W1_59 + cw59);

        /* slot 60 cascade-1 (also gives de[60]=0 by F14) */
        u32 cw60 = cw1(s1, s2);
        u32 W2_57 = W1_57 + cw57;
        u32 W2_58 = W1_58 + cw58;
        u32 W2_59 = W1_59 + cw59;
        u32 W2_60 = W1_60 + cw60;
        sha_round(s1, K[60], W1_60);
        sha_round(s2, K[60], W2_60);

        /* slots 61-63 use schedule-extended W. */
        /* Build pseudo-W from W1_pre[0..56] + actual W1[57..60] then extend. */
        u32 W1[64], W2[64];
        memcpy(W1, W1_pre, 57 * sizeof(u32));
        memcpy(W2, W2_pre, 57 * sizeof(u32));
        W1[57] = W1_57; W1[58] = W1_58; W1[59] = W1_59; W1[60] = W1_60;
        W2[57] = W2_57; W2[58] = W2_58; W2[59] = W2_59; W2[60] = W2_60;
        for (int r = 61; r < 64; r++) {
            W1[r] = sigma1_(W1[r-2]) + W1[r-7] + sigma0_(W1[r-15]) + W1[r-16];
            W2[r] = sigma1_(W2[r-2]) + W2[r-7] + sigma0_(W2[r-15]) + W2[r-16];
        }
        sha_round(s1, K[61], W1[61]);
        sha_round(s2, K[61], W2[61]);
        sha_round(s1, K[62], W1[62]);
        sha_round(s2, K[62], W2[62]);
        sha_round(s1, K[63], W1[63]);
        sha_round(s2, K[63], W2[63]);

        /* Compute residual: state diff at slot 64 (final). */
        u32 d_state[8];
        for (int j = 0; j < 8; j++) d_state[j] = s1[j] ^ s2[j];
        u32 hw_total = popcnt8(d_state);
        if (hw_total > 256) hw_total = 256;
        if (hw_total < 33) hw_dist[hw_total]++;
        if (hw_total <= 16) low_hw_count++;

        if (hw_total < min_hw) {
            min_hw = hw_total;
            best_W57 = W1_57; best_W58 = W1_58; best_W59 = W1_59; best_W60 = W1_60;
            /* Update best5 */
            if (n_best < 5) {
                best5[n_best].W1_57 = W1_57; best5[n_best].W1_58 = W1_58;
                best5[n_best].W1_59 = W1_59; best5[n_best].W1_60 = W1_60;
                best5[n_best].hw = hw_total;
                memcpy(best5[n_best].d_state, d_state, sizeof d_state);
                n_best++;
            }
        }
    }
    double dt = (double)(clock() - t0) / CLOCKS_PER_SEC;

    printf("=== block2 residual scan: m0=0x%08x fill=0x%08x bit=%d ===\n", m0, fill, bit);
    printf("samples: %llu  elapsed: %.2fs (%.2fM/s)\n",
           (unsigned long long)n, dt, n/dt/1e6);
    printf("min residual HW: %u\n", min_hw);
    printf("HW <= 16 count: %llu\n", (unsigned long long)low_hw_count);
    printf("HW distribution (0..32):\n");
    for (int hw = 0; hw <= 32; hw++) {
        if (hw_dist[hw] > 0) {
            printf("  HW=%2d: %u\n", hw, hw_dist[hw]);
        }
    }
    printf("Best (min-HW) sample:\n");
    printf("  W1[57]=0x%08x W1[58]=0x%08x W1[59]=0x%08x W1[60]=0x%08x  HW=%u\n",
           best_W57, best_W58, best_W59, best_W60, min_hw);
    return 0;
}
