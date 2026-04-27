/* cascade_m15_sweep.c
 * For a registry cand (m0, fill, bit), vary M[15] across all 2^32 values.
 * For each M[15], compute schedule, state, and cascade-1 alignment at slot 57+.
 * Find ANY M[15] that extends cascade-1 beyond slot 56.
 *
 * Compile: gcc -O3 -march=native -o cascade_m15_sweep cascade_m15_sweep.c
 * Usage:   ./cascade_m15_sweep 0x17149975 0xffffffff 31
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

static inline void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s m0 fill bit\n", argv[0]);
        return 1;
    }
    u32 m0 = strtoul(argv[1], NULL, 0);
    u32 fill = strtoul(argv[2], NULL, 0);
    int bit = atoi(argv[3]);
    u32 kernel_mask = (u32)1 << bit;

    /* Compute dW[57..63] for the kernel. dW[k] depends only on dM[0..15]
     * which is fixed by kernel: dM[0] = mask, dM[9] = mask, others = 0.
     * Use the schedule recursion on dW. */
    u32 dM[16] = {0};
    dM[0] = kernel_mask; dM[9] = kernel_mask;
    /* But dW[k] is NOT a linear function of dM via schedule (sigma0/sigma1 are
     * XOR-only AND modular subtraction is involved). We need to compute
     * dW = W2 - W1 (modular) where W1, W2 are full schedules.
     *
     * SO: for each M[15], compute W1 = schedule(M1), W2 = schedule(M2 = M1 XOR dM).
     * dW[k] = W2[k] - W1[k] (modular). This DOES depend on M for k>=16 because
     * sigma0/sigma1 are non-linear over modular arithmetic. */

    /* Build M1 base = [m0, fill, fill, ..., fill]. Vary M1[15] across 2^32. */
    u32 M1[16], M2[16];
    for (int i = 0; i < 16; i++) M1[i] = fill;
    M1[0] = m0;
    memcpy(M2, M1, sizeof M2);
    M2[0] ^= kernel_mask;
    M2[9] ^= kernel_mask;

    /* For each M[15] value, compute everything. */
    uint64_t cascade_eligible_count = 0;
    uint64_t hit_at[8] = {0};  /* hit_at[k] = count with >= k cascade-1 matches at slot 57..56+k */
    u32 max_matches = 0;
    u32 best_m15 = 0;

    clock_t t0 = clock();
    for (uint64_t i = 0; i < (1ULL << 32); i++) {
        M1[15] = (u32)i;
        M2[15] = (u32)i;  /* M[15] not part of kernel, no diff */

        /* Compute schedule W1, W2 for both messages. */
        u32 W1[64], W2[64];
        for (int j = 0; j < 16; j++) { W1[j] = M1[j]; W2[j] = M2[j]; }
        for (int j = 16; j < 64; j++) {
            W1[j] = sigma1_(W1[j-2]) + W1[j-7] + sigma0_(W1[j-15]) + W1[j-16];
            W2[j] = sigma1_(W2[j-2]) + W2[j-7] + sigma0_(W2[j-15]) + W2[j-16];
        }

        /* Compute slot-57 input states. */
        u32 s1[8], s2[8];
        for (int j = 0; j < 8; j++) { s1[j] = IV[j]; s2[j] = IV[j]; }
        for (int r = 0; r < 57; r++) {
            sha_round(s1, K[r], W1[r]);
            sha_round(s2, K[r], W2[r]);
        }

        /* Cascade-eligibility: da[57]=0 i.e. s1[0]==s2[0]. */
        if (s1[0] != s2[0]) continue;
        cascade_eligible_count++;

        /* Check at how many of slots 57..63 cascade-1 holds. */
        int matches = 0;
        for (int slot = 57; slot < 64; slot++) {
            u32 expected_cw = cw1(s1, s2);
            u32 actual_dW = W2[slot] - W1[slot];
            if (expected_cw == actual_dW) {
                matches++;
                sha_round(s1, K[slot], W1[slot]);
                sha_round(s2, K[slot], W2[slot]);
            } else {
                break;
            }
        }

        for (int k = 1; k <= matches; k++) hit_at[k]++;

        if ((u32)matches > max_matches) {
            max_matches = matches;
            best_m15 = (u32)i;
            printf("[m15=0x%08x] new max: %d slot matches (cascade-1 at slots 57..%d)\n",
                   (u32)i, matches, 56 + matches);
            fflush(stdout);
        }

        /* Progress report every 100M */
        if ((i & 0x05ffffff) == 0x05ffffff) {
            double dt = (double)(clock() - t0) / CLOCKS_PER_SEC;
            fprintf(stderr, "  %llu / 4.3B (%.1f%%, %.0fM/s, %.1fs elapsed) "
                    "elig=%llu hit_at[1]=%llu max=%u\n",
                    (unsigned long long)i, 100.0*i/(1ULL<<32),
                    i/dt/1e6, dt,
                    (unsigned long long)cascade_eligible_count,
                    (unsigned long long)hit_at[1], max_matches);
        }
    }
    double dt = (double)(clock() - t0) / CLOCKS_PER_SEC;

    printf("\n=== Summary: m0=0x%08x fill=0x%08x bit=%d ===\n", m0, fill, bit);
    printf("Total samples (M[15] in [0, 2^32)): %llu\n", (1ULL << 32));
    printf("Elapsed: %.1fs (%.0fM/s)\n", dt, (1ULL<<32)/dt/1e6);
    printf("Cascade-eligible (da[57]=0): %llu\n", (unsigned long long)cascade_eligible_count);
    printf("Max cascade-1 slot matches: %u (best M[15]=0x%08x)\n", max_matches, best_m15);
    for (int k = 1; k <= 7; k++) {
        printf("  >= %d-slot: %llu\n", k, (unsigned long long)hit_at[k]);
    }
    return 0;
}
