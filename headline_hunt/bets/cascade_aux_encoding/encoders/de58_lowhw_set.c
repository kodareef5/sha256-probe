/* de58_lowhw_set.c — find ALL distinct de58 values at HW <= threshold.
 *
 * Compile: gcc -O3 -march=native -o de58_lowhw_set de58_lowhw_set.c
 * Run:     ./de58_lowhw_set 0x189b13c7 0x80000000 31 5
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
static inline u32 sigma0(u32 x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline u32 sigma1(u32 x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }

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

static inline void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

static void precompute_state(u32 M[16], int k_target, u32 out[8]) {
    u32 W[64];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 64; i++) W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
    for (int i = 0; i < 8; i++) out[i] = IV[i];
    for (int r = 0; r < k_target; r++) sha_round(out, K[r], W[r]);
}

static inline u32 cw1(const u32 s1[8], const u32 s2[8]) {
    u32 dh = s1[7] - s2[7];
    u32 dSig1 = Sigma1(s1[4]) - Sigma1(s2[4]);
    u32 dCh = Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6]);
    u32 T2_1 = Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]);
    u32 T2_2 = Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]);
    return dh + dSig1 + dCh + T2_1 - T2_2;
}

static inline u32 de58_at_w57(const u32 s1_in[8], const u32 s2_in[8], u32 w57) {
    u32 s1[8], s2[8];
    memcpy(s1, s1_in, sizeof s1); memcpy(s2, s2_in, sizeof s2);
    u32 cw57 = cw1(s1, s2);
    sha_round(s1, K[57], w57); sha_round(s2, K[57], w57 + cw57);
    u32 cw58 = cw1(s1, s2);
    sha_round(s1, K[58], 0); sha_round(s2, K[58], cw58);
    return s1[4] - s2[4];
}

#define MAX_DISTINCT 4096

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s m0 fill bit max_hw\n", argv[0]);
        return 1;
    }
    u32 m0 = strtoul(argv[1], NULL, 0);
    u32 fill = strtoul(argv[2], NULL, 0);
    int bit = atoi(argv[3]);
    int max_hw = atoi(argv[4]);

    u32 M1[16], M2[16];
    M1[0] = m0;
    for (int i = 1; i < 16; i++) M1[i] = fill;
    memcpy(M2, M1, sizeof M2);
    M2[0] ^= ((u32)1 << bit);
    M2[9] ^= ((u32)1 << bit);

    u32 s1[8], s2[8];
    precompute_state(M1, 57, s1);
    precompute_state(M2, 57, s2);

    if (s1[0] != s2[0]) {
        fprintf(stderr, "WARN: cascade-1 not held at slot 57 input\n");
    }

    /* Track distinct de58 values per HW level. Use simple array up to MAX_DISTINCT. */
    u32 distinct_by_hw[33][MAX_DISTINCT];
    u32 count_by_hw[33] = {0};
    u32 total_by_hw[33] = {0};

    /* Full 2^32 enumeration */
    for (uint64_t i = 0; i < (1ULL << 32); i++) {
        u32 w57 = (u32)i;
        u32 d = de58_at_w57(s1, s2, w57);
        u32 hw = __builtin_popcount(d);
        if ((int)hw <= max_hw) {
            total_by_hw[hw]++;
            /* Add to distinct set if new */
            int seen = 0;
            for (u32 j = 0; j < count_by_hw[hw]; j++) {
                if (distinct_by_hw[hw][j] == d) { seen = 1; break; }
            }
            if (!seen && count_by_hw[hw] < MAX_DISTINCT) {
                distinct_by_hw[hw][count_by_hw[hw]++] = d;
            }
        }
    }

    printf("=== m0=0x%08x fill=0x%08x bit=%d max_hw=%d ===\n", m0, fill, bit, max_hw);
    for (int hw = 0; hw <= max_hw; hw++) {
        if (total_by_hw[hw] == 0) continue;
        printf("HW=%2d: %u total chambers, %u distinct de58 values\n",
               hw, total_by_hw[hw], count_by_hw[hw]);
        for (u32 j = 0; j < count_by_hw[hw] && j < 20; j++) {
            printf("    de58=0x%08x\n", distinct_by_hw[hw][j]);
        }
        if (count_by_hw[hw] > 20) printf("    ... and %u more\n", count_by_hw[hw] - 20);
    }
    return 0;
}
