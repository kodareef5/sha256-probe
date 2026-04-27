/* active_adder_count.c — count active modular adders along a cascade-1 trail
 *
 * Uses sha_round() verbatim from block2_lowhw_set.c. Active-adder count
 * is tallied via a parallel "diff trace" computation BEFORE the actual
 * round runs.
 *
 * Compile: gcc -O3 -march=native -o active_adder_count active_adder_count.c
 * Run:     ./active_adder_count m0 fill bit W57 W58 W59 W60
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

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

/* Count active modular adders for ONE round, given pre-round s1, s2 and W1, W2.
   Does NOT modify states. Returns count in [0, 7]. */
static int count_active_adders(const u32 s1[8], const u32 s2[8], u32 w1, u32 w2, u32 k) {
    int n = 0;
    /* Adder 1: h + Σ1(e) */
    u32 a1_in_1 = s1[7], a2_in_1 = s2[7];
    u32 sig1_1 = Sigma1(s1[4]), sig1_2 = Sigma1(s2[4]);
    if ((a1_in_1 ^ a2_in_1) | (sig1_1 ^ sig1_2)) n++;
    u32 acc1_1 = a1_in_1 + sig1_1, acc1_2 = a2_in_1 + sig1_2;

    /* Adder 2: + Ch(e,f,g) */
    u32 ch_1 = Ch(s1[4], s1[5], s1[6]), ch_2 = Ch(s2[4], s2[5], s2[6]);
    if ((acc1_1 ^ acc1_2) | (ch_1 ^ ch_2)) n++;
    u32 acc2_1 = acc1_1 + ch_1, acc2_2 = acc1_2 + ch_2;

    /* Adder 3: + K */
    if (acc2_1 ^ acc2_2) n++;
    u32 acc3_1 = acc2_1 + k, acc3_2 = acc2_2 + k;

    /* Adder 4: + W (= T1) */
    if ((acc3_1 ^ acc3_2) | (w1 ^ w2)) n++;
    u32 T1_1 = acc3_1 + w1, T1_2 = acc3_2 + w2;

    /* Adder 5: T2 = Σ0(a) + Maj(a,b,c) */
    u32 sig0_1 = Sigma0(s1[0]), sig0_2 = Sigma0(s2[0]);
    u32 maj_1 = Maj(s1[0], s1[1], s1[2]), maj_2 = Maj(s2[0], s2[1], s2[2]);
    if ((sig0_1 ^ sig0_2) | (maj_1 ^ maj_2)) n++;
    u32 T2_1 = sig0_1 + maj_1, T2_2 = sig0_2 + maj_2;

    /* Adder 6: a' = T1 + T2 */
    if ((T1_1 ^ T1_2) | (T2_1 ^ T2_2)) n++;

    /* Adder 7: e' = d + T1 */
    if ((s1[3] ^ s2[3]) | (T1_1 ^ T1_2)) n++;

    return n;
}

int main(int argc, char **argv) {
    if (argc < 8) {
        fprintf(stderr, "Usage: %s m0 fill bit W57 W58 W59 W60\n", argv[0]);
        return 1;
    }
    u32 m0 = strtoul(argv[1], NULL, 0);
    u32 fill = strtoul(argv[2], NULL, 0);
    int bit = atoi(argv[3]);
    u32 W1_57 = strtoul(argv[4], NULL, 0);
    u32 W1_58 = strtoul(argv[5], NULL, 0);
    u32 W1_59 = strtoul(argv[6], NULL, 0);
    u32 W1_60 = strtoul(argv[7], NULL, 0);
    u32 kernel_mask = (u32)1 << bit;

    /* Pre-state */
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
    u32 s1_pre[8], s2_pre[8];
    for (int i = 0; i < 8; i++) { s1_pre[i] = IV[i]; s2_pre[i] = IV[i]; }
    for (int r = 0; r < 57; r++) {
        sha_round(s1_pre, K[r], W1_pre[r]);
        sha_round(s2_pre, K[r], W2_pre[r]);
    }

    /* Cascade-1 forward simulation, COUNTING active adders.
       Uses sha_round() verbatim from block2_lowhw_set.c. */
    u32 s1[8], s2[8];
    memcpy(s1, s1_pre, sizeof s1);
    memcpy(s2, s2_pre, sizeof s2);

    int hw_pre = 0;
    for (int j = 0; j < 8; j++) hw_pre += popcnt(s1[j] ^ s2[j]);
    printf("=== active_adder_count: m0=0x%08x fill=0x%08x bit=%d ===\n", m0, fill, bit);
    printf("Pre-round-57 state diff:\n");
    for (int j = 0; j < 8; j++) printf("  d[%d] = 0x%08x\n", j, s1[j] ^ s2[j]);
    printf("HW(pre-57) = %d\n\n", hw_pre);

    int total_active = 0;
    int active_per_round[8] = {0};
    int hw_per_round[8] = {0};

    /* Round 57 */
    u32 cw57 = cw1(s1, s2);
    u32 W2_57 = W1_57 + cw57;
    int n57 = count_active_adders(s1, s2, W1_57, W2_57, K[57]);
    sha_round(s1, K[57], W1_57); sha_round(s2, K[57], W2_57);
    int hw57 = 0; for (int j = 0; j < 8; j++) hw57 += popcnt(s1[j] ^ s2[j]);
    active_per_round[0] = n57; hw_per_round[0] = hw57; total_active += n57;

    /* Round 58 */
    u32 cw58 = cw1(s1, s2);
    u32 W2_58 = W1_58 + cw58;
    int n58 = count_active_adders(s1, s2, W1_58, W2_58, K[58]);
    sha_round(s1, K[58], W1_58); sha_round(s2, K[58], W2_58);
    int hw58 = 0; for (int j = 0; j < 8; j++) hw58 += popcnt(s1[j] ^ s2[j]);
    active_per_round[1] = n58; hw_per_round[1] = hw58; total_active += n58;

    /* Round 59 */
    u32 cw59 = cw1(s1, s2);
    u32 W2_59 = W1_59 + cw59;
    int n59 = count_active_adders(s1, s2, W1_59, W2_59, K[59]);
    sha_round(s1, K[59], W1_59); sha_round(s2, K[59], W2_59);
    int hw59 = 0; for (int j = 0; j < 8; j++) hw59 += popcnt(s1[j] ^ s2[j]);
    active_per_round[2] = n59; hw_per_round[2] = hw59; total_active += n59;

    /* Round 60 */
    u32 cw60 = cw1(s1, s2);
    u32 W2_60 = W1_60 + cw60;
    int n60 = count_active_adders(s1, s2, W1_60, W2_60, K[60]);
    sha_round(s1, K[60], W1_60); sha_round(s2, K[60], W2_60);
    int hw60 = 0; for (int j = 0; j < 8; j++) hw60 += popcnt(s1[j] ^ s2[j]);
    active_per_round[3] = n60; hw_per_round[3] = hw60; total_active += n60;

    /* Rounds 61, 62, 63 — W2 follows from message expansion */
    u32 W1_full[64], W2_full[64];
    memcpy(W1_full, W1_pre, 57 * sizeof(u32));
    memcpy(W2_full, W2_pre, 57 * sizeof(u32));
    W1_full[57] = W1_57; W1_full[58] = W1_58; W1_full[59] = W1_59; W1_full[60] = W1_60;
    W2_full[57] = W2_57; W2_full[58] = W2_58; W2_full[59] = W2_59; W2_full[60] = W2_60;
    for (int r = 61; r < 64; r++) {
        W1_full[r] = sigma1_(W1_full[r-2]) + W1_full[r-7] + sigma0_(W1_full[r-15]) + W1_full[r-16];
        W2_full[r] = sigma1_(W2_full[r-2]) + W2_full[r-7] + sigma0_(W2_full[r-15]) + W2_full[r-16];
    }
    for (int r = 61; r < 64; r++) {
        int n = count_active_adders(s1, s2, W1_full[r], W2_full[r], K[r]);
        sha_round(s1, K[r], W1_full[r]); sha_round(s2, K[r], W2_full[r]);
        int hw = 0; for (int j = 0; j < 8; j++) hw += popcnt(s1[j] ^ s2[j]);
        active_per_round[r - 57] = n; hw_per_round[r - 57] = hw; total_active += n;
    }

    /* Print per-round summary */
    u32 cws[4] = {cw57, cw58, cw59, cw60};
    u32 W1s[7] = {W1_57, W1_58, W1_59, W1_60, W1_full[61], W1_full[62], W1_full[63]};
    u32 W2s[7] = {W2_57, W2_58, W2_59, W2_60, W2_full[61], W2_full[62], W2_full[63]};
    printf("%-3s %-10s %-10s %-10s %-7s %-12s\n",
           "r", "W1", "W2", "cw", "active", "HW(diff_after)");
    for (int i = 0; i < 7; i++) {
        u32 cw_print = (i < 4) ? cws[i] : (W2s[i] - W1s[i]);
        printf("%-3d 0x%08x 0x%08x 0x%08x %-7d %-12d\n",
               57 + i, W1s[i], W2s[i], cw_print, active_per_round[i], hw_per_round[i]);
    }

    int hw_final = hw_per_round[6];
    printf("\n=== Final state diff (round 63) ===\n");
    for (int j = 0; j < 8; j++)
        printf("  d[%d] = 0x%08x  (HW=%d)\n", j, s1[j] ^ s2[j], popcnt(s1[j] ^ s2[j]));
    printf("HW(diff63) = %d\n", hw_final);

    printf("\n=== Active-adder summary ===\n");
    for (int i = 0; i < 7; i++)
        printf("  round %d: %d active adders\n", 57 + i, active_per_round[i]);
    printf("  TOTAL: %d active adders (max 49)\n", total_active);
    printf("\n  Naive trail-prob lower bound: 2^-%d\n", total_active);
    printf("  256-bit second-block freedom → ~2^%d expected solutions if bound is tight\n",
           256 - total_active);
    return 0;
}
