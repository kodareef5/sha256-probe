/* certificate_64r_sfs_sr60.c
 *
 * Self-contained C verifier for the project's sr=60 SHA-256 SFS collision.
 * Compile and run to independently verify the collision claim.
 *
 *   gcc -O3 -o cert_sr60 certificate_64r_sfs_sr60.c
 *   ./cert_sr60
 *
 * Expected output:
 *   sr = 60, collision verified, H = ba6287f0 dcaf9857 d89ad44a 6cced1e2
 *                                    adf8a242 524236fb c0c656cd 50a7e23b
 *
 * Cert summary
 *   Type:           Semi-free-start (SFS) collision, full 64 rounds
 *   sr (compliance): 60 of 64 schedule equations satisfied (93.75%)
 *   Free schedule:  W[57..60] (4 words, slack=0 at the SAT/UNSAT phase
 *                   transition Viragh 2026 identified as a "structural
 *                   barrier")
 *   Kernel:         MSB, dM[0] = dM[9] = 0x80000000
 *   M[0]:           0x17149975 (one of Viragh's scan_m0 outputs)
 *   M[1..15]:       0xFFFFFFFF (fill)
 *   W1[57..60]:     0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82
 *   W2[57..60]:     0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b
 *   Solver:         Kissat 4.0.4 (pure SAT on cascade_aux Mode A encoding)
 *   Seed:           5
 *   Wall:           ~12 hours on macbook M5 (single-thread)
 *   Verified:       3 machines (macbook, linux server, gpu laptop)
 *
 * Comparison to Viragh 2026 ("We Broke 92% of SHA-256", March 27 2026):
 *   Viragh's frontier: sr=59, free=5, slack=64, ~276s wall.
 *   Viragh's prediction for sr=60 (this configuration):
 *     "TIMEOUT > 7200s, structural barrier, breaking this will require
 *      a few more techniques :)"
 *   This work: SAT in ~12h via deeper kissat seed exploration. +1 round
 *   advance over Viragh's published frontier in the same methodology.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

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
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
};

static void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

/* Build full schedule W[0..63] with W[57..60] CHOSEN (override) and the
 * rest from the standard SHA-256 schedule recurrence. */
static void build_schedule(const u32 M[16], const u32 W_override[4], u32 W[64]) {
    /* W[0..15] = M[0..15] */
    for (int i = 0; i < 16; i++) W[i] = M[i];
    /* W[16..56]: standard schedule */
    for (int i = 16; i <= 56; i++) {
        W[i] = sigma1_(W[i-2]) + W[i-7] + sigma0_(W[i-15]) + W[i-16];
    }
    /* W[57..60]: OVERRIDE (4 free schedule words for sr=60) */
    for (int i = 0; i < 4; i++) W[57 + i] = W_override[i];
    /* W[61..63]: standard schedule (using overridden W[57..60]) */
    for (int i = 61; i <= 63; i++) {
        W[i] = sigma1_(W[i-2]) + W[i-7] + sigma0_(W[i-15]) + W[i-16];
    }
}

/* Run all 64 rounds + Davies-Meyer finalization. */
static void sha256_compress(const u32 W[64], u32 final_state[8]) {
    u32 s[8];
    for (int i = 0; i < 8; i++) s[i] = IV[i];
    for (int r = 0; r < 64; r++) sha_round(s, K[r], W[r]);
    for (int i = 0; i < 8; i++) final_state[i] = (IV[i] + s[i]);
}

int main(void) {
    /* Message inputs: M[0]=0x17149975, M[1..15]=0xFFFFFFFF (the candidate). */
    u32 M1[16];
    M1[0] = 0x17149975;
    for (int i = 1; i < 16; i++) M1[i] = 0xFFFFFFFF;

    /* M2 = M1 with MSB kernel diff applied at positions 0 and 9. */
    u32 M2[16];
    memcpy(M2, M1, sizeof M2);
    M2[0] ^= 0x80000000;
    M2[9] ^= 0x80000000;

    /* Free schedule words (chosen by kissat): W1[57..60] and W2[57..60]. */
    u32 W1_override[4] = {0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82};
    u32 W2_override[4] = {0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b};

    u32 W1[64], W2[64];
    build_schedule(M1, W1_override, W1);
    build_schedule(M2, W2_override, W2);

    u32 H1[8], H2[8];
    sha256_compress(W1, H1);
    sha256_compress(W2, H2);

    /* Verify schedule compliance. */
    int sched_eqs_ok = 0;
    for (int i = 16; i < 64; i++) {
        u32 expected = sigma1_(W1[i-2]) + W1[i-7] + sigma0_(W1[i-15]) + W1[i-16];
        if (W1[i] == expected) sched_eqs_ok++;
    }
    int total_sched_eqs = 48;  /* W[16..63] */

    /* Print schedule words for transparency. */
    printf("Verifying sr=60 SFS collision certificate\n");
    printf("\n");
    printf("Message structure:\n");
    printf("  M[0]    = 0x%08x\n", M1[0]);
    printf("  M[1..15] = 0x%08x (fill)\n", M1[1]);
    printf("  Kernel: dM[0] = dM[9] = 0x80000000 (MSB)\n");
    printf("\n");
    printf("Free schedule words (overridden):\n");
    for (int i = 0; i < 4; i++) {
        printf("  W1[%d] = 0x%08x   W2[%d] = 0x%08x   dW = 0x%08x\n",
               57 + i, W1_override[i], 57 + i, W2_override[i],
               W2_override[i] - W1_override[i]);
    }
    printf("\n");
    printf("Schedule compliance: %d / %d (%.2f%%) → sr = %d\n",
           sched_eqs_ok, total_sched_eqs,
           100.0 * sched_eqs_ok / total_sched_eqs,
           16 + sched_eqs_ok);
    printf("\n");

    int collision = (memcmp(H1, H2, sizeof H1) == 0);
    printf("Final hashes:\n");
    printf("  H(M1) = ");
    for (int i = 0; i < 8; i++) printf("%08x ", H1[i]);
    printf("\n");
    printf("  H(M2) = ");
    for (int i = 0; i < 8; i++) printf("%08x ", H2[i]);
    printf("\n");
    printf("\n");

    /* Expected hash from cert YAML. */
    static const u32 EXPECTED[8] = {
        0xba6287f0, 0xdcaf9857, 0xd89ad44a, 0x6cced1e2,
        0xadf8a242, 0x524236fb, 0xc0c656cd, 0x50a7e23b
    };
    int matches_expected = (memcmp(H1, EXPECTED, sizeof EXPECTED) == 0);

    if (collision && matches_expected) {
        printf("RESULT: sr = %d, collision VERIFIED\n", 16 + sched_eqs_ok);
        printf("        H = ba6287f0 dcaf9857 d89ad44a 6cced1e2 adf8a242 524236fb c0c656cd 50a7e23b\n");
        return 0;
    } else {
        printf("RESULT: VERIFICATION FAILED\n");
        printf("  collision: %s\n", collision ? "YES" : "NO");
        printf("  matches expected hash: %s\n", matches_expected ? "YES" : "NO");
        return 1;
    }
}
