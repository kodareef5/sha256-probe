/* cascade_max_slot_search.c
 *
 * Random-message search for cascade-1 alignment at extended slot range.
 *
 * For a given (m0, fill, bit) kernel, dW[57..63] are kernel-determined
 * (fixed values computable once). For each random M (with M[0]=m0 and
 * M[9]= m0^kernel_diff[9-position] kept fixed for kernel), we compute
 * cw1[57..63] and check at how many slots cw1[k] matches dW[k].
 *
 * Verified sr=60: 4-slot match (slots 57, 58, 59, 60). We hunt for 5+.
 *
 * NOTE: random search at random M finds k-slot match with prob 2^(-32k).
 * 4-slot match: 1 in 2^128. Won't find by brute force in our lifetime.
 * BUT if any cand has cascade-1 alignment STRUCTURE that biases the
 * probability, we'll see it as elevated hit-rate at slot 57.
 *
 * Compile: gcc -O3 -march=native -o cascade_max_slot_search cascade_max_slot_search.c
 * Usage:   ./cascade_max_slot_search 0x17149975 0xffffffff 31 1000000000 [seed]
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
    u32 dh = s1[7] - s2[7];
    u32 dSig1 = Sigma1(s1[4]) - Sigma1(s2[4]);
    u32 dCh = Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6]);
    u32 T2_1 = Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]);
    u32 T2_2 = Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]);
    return dh + dSig1 + dCh + T2_1 - T2_2;
}

static inline void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

/* Compute schedule W[0..63] from M[0..15]. */
static void compute_schedule(const u32 M[16], u32 W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 64; i++) {
        W[i] = sigma1_(W[i-2]) + W[i-7] + sigma0_(W[i-15]) + W[i-16];
    }
}

/* Compute SHA-256 state at slot k (i.e., after rounds 0..k-1). */
static void compute_state_at_slot(const u32 W[64], int slot, u32 out[8]) {
    for (int i = 0; i < 8; i++) out[i] = IV[i];
    for (int r = 0; r < slot; r++) sha_round(out, K[r], W[r]);
}

/* Check at how many of slots {57,58,...,57+max_slots} the cascade-1
 * condition holds for messages M1, M2.
 * Returns (count of matches, dW values, cw1 values). */
static int check_cascade_alignment(const u32 M1[16], const u32 M2[16],
                                    int max_slots,
                                    u32 dW_out[8], u32 cw_out[8]) {
    u32 W1[64], W2[64];
    compute_schedule(M1, W1);
    compute_schedule(M2, W2);
    /* Compute slot-57 input states. */
    u32 s1[8], s2[8];
    compute_state_at_slot(W1, 57, s1);
    compute_state_at_slot(W2, 57, s2);
    /* Sanity: cascade-eligibility requires da[57]=0 i.e. s1[0]==s2[0]. */
    if (s1[0] != s2[0]) return -1;  /* Not cascade-eligible. */

    int matches = 0;
    int last_match_slot = 56;
    for (int slot = 57; slot <= 56 + max_slots && slot < 64; slot++) {
        u32 expected_cw = cw1(s1, s2);
        u32 actual_dW = W2[slot] - W1[slot];
        dW_out[slot - 57] = actual_dW;
        cw_out[slot - 57] = expected_cw;
        if (expected_cw == actual_dW) {
            matches++;
            last_match_slot = slot;
            /* Apply round (we continue in case match restarts) */
            sha_round(s1, K[slot], W1[slot]);
            sha_round(s2, K[slot], W2[slot]);
        } else {
            /* Cascade broke. Stop counting consecutive matches from slot 57. */
            break;
        }
    }
    return matches;
}

static inline u32 xorshift32(u32 *state) {
    u32 x = *state; x ^= x << 13; x ^= x >> 17; x ^= x << 5; *state = x; return x;
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

    u32 max_matches = 0;
    u32 best_M1[16] = {0};
    uint64_t hit_at_slot[8] = {0};  /* hit_at_slot[k] = count of M with >= k matches */

    u32 rng = seed;
    clock_t t0 = clock();
    for (uint64_t i = 0; i < n; i++) {
        u32 M1[16];
        M1[0] = m0;
        /* Vary M[1..8, 10..15] randomly. M[9] uses fill since kernel touches M[9]. */
        for (int j = 1; j < 16; j++) M1[j] = xorshift32(&rng);
        /* But the registry "default" structure has M[9]=fill — check if that
         * matters for cascade eligibility. For now, set M[9] = fill too. */
        M1[9] = fill;
        /* Actually let M[1..15] all be random EXCEPT M[9] keeps kernel structure */
        for (int j = 1; j < 16; j++) M1[j] = xorshift32(&rng);

        u32 M2[16];
        memcpy(M2, M1, sizeof M2);
        M2[0] ^= kernel_mask;
        M2[9] ^= kernel_mask;

        u32 dW[8] = {0}, cw[8] = {0};
        int m = check_cascade_alignment(M1, M2, 7, dW, cw);
        if (m < 0) continue;  /* Not cascade-eligible */

        for (int k = 1; k <= m; k++) hit_at_slot[k]++;

        if ((u32)m > max_matches) {
            max_matches = m;
            memcpy(best_M1, M1, sizeof best_M1);
            printf("[i=%llu] new max: %d slot matches\n", (unsigned long long)i, m);
            printf("  M1[0..15] = ");
            for (int j = 0; j < 16; j++) printf("0x%08x ", M1[j]);
            printf("\n  matches at slots 57..%d (cw1==dW)\n", 56 + m);
        }
    }
    double dt = (double)(clock() - t0) / CLOCKS_PER_SEC;

    printf("\n=== Summary ===\n");
    printf("Samples: %llu  Elapsed: %.2fs (%.2fM/s)\n", (unsigned long long)n, dt, n/dt/1e6);
    printf("Max slot matches: %u\n", max_matches);
    for (int k = 1; k <= 7; k++) {
        printf("  >= %d-slot matches: %llu\n", k, (unsigned long long)hit_at_slot[k]);
    }
    return 0;
}
