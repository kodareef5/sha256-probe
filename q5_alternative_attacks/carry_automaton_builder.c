/*
 * carry_automaton_builder.c — Build explicit carry automaton from collision data
 *
 * Reads collision tuples, extracts carry states at every bit position,
 * builds the transition table, and characterizes the automaton structure.
 *
 * This is the key tool for understanding the polynomial-time structure
 * of the SHA-256 cascade collision problem.
 *
 * Input: collision file with format "W1[57] W1[58] W1[59] W1[60] | W2[57] ..."
 * Output: automaton description — states, transitions, width, invariant bits
 *
 * Compile: gcc -O3 -march=native -o carry_automaton_builder carry_automaton_builder.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define MAX_COLL 4096
#define MAX_N 16
#define ROUNDS 7        /* rounds 57-63 */
#define ADDS_PER_ROUND 7  /* 4 for T1 chain, 1 for T2, 1 for new_e, 1 for new_a */
#define TOTAL_ADDS (ROUNDS * ADDS_PER_ROUND)  /* 49 carry bits per bit position */

static int gN;
static uint32_t gMASK;
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static uint32_t KN[64], IVN[8];

static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % gN; return ((x >> k) | (x << (gN - k))) & gMASK;
}
static inline uint32_t fnS0(uint32_t a) { return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & gMASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & gMASK); }
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e & f) ^ ((~e) & g)) & gMASK; }
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & gMASK; }

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
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * gN / 32.0); return r < 1 ? 1 : r;
}

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & gMASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],
             e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i]) & gMASK;
        uint32_t T2 = (fnS0(a)+fnMj(a,b,c)) & gMASK;
        h=g; g=f; f=e; e=(d+T1)&gMASK; d=c; c=b; b=a; a=(T1+T2)&gMASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w) & gMASK;
    uint32_t T2 = (fnS0(s[0])+fnMj(s[0],s[1],s[2])) & gMASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&gMASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&gMASK;
}

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd]) & gMASK;
    uint32_t r2 = (s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd]) & gMASK;
    uint32_t T21 = (fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2])) & gMASK;
    uint32_t T22 = (fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2])) & gMASK;
    return (w1 + r1 - r2 + T21 - T22) & gMASK;
}

/*
 * Extract carry bits from a 2-operand addition a+b at each bit position.
 * carry[k] = carry OUT of bit k (carry INTO bit k+1).
 * carry[N-1] is the overflow carry (discarded in mod 2^N arithmetic).
 */
static void extract_add_carries(uint32_t a, uint32_t b, uint32_t carries[MAX_N]) {
    uint32_t c = 0; /* carry into current bit */
    for (int k = 0; k < gN; k++) {
        uint32_t ak = (a >> k) & 1;
        uint32_t bk = (b >> k) & 1;
        uint32_t sum = ak + bk + c;
        carries[k] = sum >> 1; /* carry out */
        c = carries[k];
    }
}

/*
 * Carry state for one collision at one bit position.
 * Vector of TOTAL_ADDS (49) carry bits.
 */
typedef struct {
    uint8_t bits[TOTAL_ADDS]; /* 0 or 1 */
} carry_state_t;

/*
 * Extract all carry states for one path of one collision.
 * Returns carry_states[bit][add_idx] for each bit position.
 */
static void extract_all_carries(
    const uint32_t init_state[8],
    const uint32_t W_values[7], /* W[57]..W[63] */
    uint32_t carry_matrix[MAX_N][TOTAL_ADDS])
{
    uint32_t s[8];
    memcpy(s, init_state, 32);

    for (int r = 0; r < ROUNDS; r++) {
        /* Compute intermediate values for this round */
        uint32_t sig1_e = fnS1(s[4]);
        uint32_t ch_efg = fnCh(s[4], s[5], s[6]);
        uint32_t sig0_a = fnS0(s[0]);
        uint32_t maj_abc = fnMj(s[0], s[1], s[2]);

        /* T1 chain: t0 = h+Sig1(e), t1 = t0+Ch, t2 = t1+K, T1 = t2+W */
        uint32_t t0 = (s[7] + sig1_e) & gMASK;
        uint32_t t1 = (t0 + ch_efg) & gMASK;
        uint32_t t2 = (t1 + KN[57+r]) & gMASK;
        uint32_t T1 = (t2 + W_values[r]) & gMASK;
        /* T2 = Sig0(a) + Maj(a,b,c) */
        uint32_t T2 = (sig0_a + maj_abc) & gMASK;
        /* new_e = d + T1 */
        /* new_a = T1 + T2 */

        /* Extract carries for each addition */
        int base = r * ADDS_PER_ROUND;
        uint32_t c_tmp[MAX_N];

        /* Add 0: h + Sig1(e) */
        extract_add_carries(s[7], sig1_e, c_tmp);
        for (int k = 0; k < gN; k++) carry_matrix[k][base+0] = c_tmp[k];

        /* Add 1: t0 + Ch(e,f,g) */
        extract_add_carries(t0, ch_efg, c_tmp);
        for (int k = 0; k < gN; k++) carry_matrix[k][base+1] = c_tmp[k];

        /* Add 2: t1 + K */
        extract_add_carries(t1, KN[57+r], c_tmp);
        for (int k = 0; k < gN; k++) carry_matrix[k][base+2] = c_tmp[k];

        /* Add 3: t2 + W */
        extract_add_carries(t2, W_values[r], c_tmp);
        for (int k = 0; k < gN; k++) carry_matrix[k][base+3] = c_tmp[k];

        /* Add 4: Sig0(a) + Maj(a,b,c) = T2 */
        extract_add_carries(sig0_a, maj_abc, c_tmp);
        for (int k = 0; k < gN; k++) carry_matrix[k][base+4] = c_tmp[k];

        /* Add 5: d + T1 = new_e */
        extract_add_carries(s[3], T1, c_tmp);
        for (int k = 0; k < gN; k++) carry_matrix[k][base+5] = c_tmp[k];

        /* Add 6: T1 + T2 = new_a */
        extract_add_carries(T1, T2, c_tmp);
        for (int k = 0; k < gN; k++) carry_matrix[k][base+6] = c_tmp[k];

        /* Advance state (shift register) */
        s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&gMASK;
        s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&gMASK;
    }
}

/* Collision data */
static int n_coll;
static uint32_t coll_w1[MAX_COLL][4], coll_w2[MAX_COLL][4];

/* Carry matrices: [collision][bit][add_index] */
static uint32_t carry1[MAX_COLL][MAX_N][TOTAL_ADDS];
static uint32_t carry2[MAX_COLL][MAX_N][TOTAL_ADDS];

/* Carry-DIFF: carry1 XOR carry2 */
static uint32_t carry_diff[MAX_COLL][MAX_N][TOTAL_ADDS];

/* Carry state hash for uniqueness checking */
static uint64_t hash_carry_state(uint32_t state[TOTAL_ADDS]) {
    /* FNV-1a on the carry bit vector */
    uint64_t h = 14695981039346656037ULL;
    for (int i = 0; i < TOTAL_ADDS; i++) {
        h ^= state[i];
        h *= 1099511628211ULL;
    }
    return h;
}

/* Compare two carry states */
static int carry_state_equal(uint32_t a[TOTAL_ADDS], uint32_t b[TOTAL_ADDS]) {
    return memcmp(a, b, TOTAL_ADDS * sizeof(uint32_t)) == 0;
}

/* Addition names for reporting */
static const char *add_names[ADDS_PER_ROUND] = {
    "h+Sig1(e)", "+Ch(e,f,g)", "+K[r]", "+W[r]",
    "Sig0(a)+Maj", "d+T1=new_e", "T1+T2=new_a"
};

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    if (argc < 3) {
        fprintf(stderr, "Usage: %s N collision_file\n", argv[0]);
        fprintf(stderr, "  collision_file format: W1[57] W1[58] W1[59] W1[60] | W2[57] W2[58] W2[59] W2[60]\n");
        return 1;
    }

    gN = atoi(argv[1]);
    if (gN > MAX_N) { fprintf(stderr, "N too large (max %d)\n", MAX_N); return 1; }
    gMASK = (1U << gN) - 1;

    rS0[0]=scale_rot(2); rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6); rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7); rs0[1]=scale_rot(18); ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19); ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & gMASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & gMASK;

    /* Read collision file — supports two formats:
     * Format 1: "W1[57] W1[58] W1[59] W1[60] | W2[57] W2[58] W2[59] W2[60]"
     * Format 2: "COLL w57 w58 w59 w60" (W2 computed after finding candidate)
     */
    FILE *f = fopen(argv[2], "r");
    if (!f) { perror("fopen"); return 1; }
    n_coll = 0;
    int need_w2 = 0; /* set if we read COLL format */
    char line[256];
    while (fgets(line, sizeof(line), f) && n_coll < MAX_COLL) {
        uint32_t a[4], b[4];
        if (sscanf(line, "%x %x %x %x | %x %x %x %x",
                   &a[0], &a[1], &a[2], &a[3],
                   &b[0], &b[1], &b[2], &b[3]) == 8) {
            for (int i = 0; i < 4; i++) { coll_w1[n_coll][i] = a[i]; coll_w2[n_coll][i] = b[i]; }
            n_coll++;
        } else if (sscanf(line, "COLL %x %x %x %x", &a[0], &a[1], &a[2], &a[3]) == 4) {
            for (int i = 0; i < 4; i++) coll_w1[n_coll][i] = a[i];
            need_w2 = 1;
            n_coll++;
        }
    }
    fclose(f);
    printf("Loaded %d collisions at N=%d%s\n\n", n_coll, gN,
           need_w2 ? " (COLL format, will compute W2)" : "");

    /* Find the candidate (M[0], fill, kernel bit) by trying all and verifying
     * against the first collision. For COLL format, verify by running full
     * cascade and checking if the first collision produces a collision. */
    uint32_t fills[] = {gMASK, 0, gMASK>>1, 1U<<(gN-1), 0x55&gMASK, 0xAA&gMASK};
    int nfills = 6;
    uint32_t state56_1[8], state56_2[8], W1pre[57], W2pre[57];
    int found = 0;

    /* Try all kernel bit positions */
    for (int kbit = gN-1; kbit >= 0 && !found; kbit--) {
        uint32_t delta = 1U << kbit;
        for (int fi = 0; fi < nfills && !found; fi++) {
            for (uint32_t m0 = 0; m0 <= gMASK && !found; m0++) {
                uint32_t M1[16], M2[16];
                for (int i = 0; i < 16; i++) { M1[i] = fills[fi]; M2[i] = fills[fi]; }
                M1[0] = m0; M2[0] = m0 ^ delta; M2[9] = fills[fi] ^ delta;
                precompute(M1, state56_1, W1pre);
                precompute(M2, state56_2, W2pre);
                if (state56_1[0] != state56_2[0]) continue;

                /* Verify: run first collision's W1 values through cascade */
                uint32_t s1[8], s2[8];
                memcpy(s1, state56_1, 32); memcpy(s2, state56_2, 32);
                uint32_t W1[7], W2[7];
                for (int r = 0; r < 4; r++) {
                    W1[r] = coll_w1[0][r];
                    W2[r] = find_w2(s1, s2, 57+r, W1[r]);
                    sha_round(s1, KN[57+r], W1[r]);
                    sha_round(s2, KN[57+r], W2[r]);
                }
                /* Schedule words 61-63 */
                W1[4] = (fns1(W1[2]) + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & gMASK;
                W2[4] = (fns1(W2[2]) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & gMASK;
                W1[5] = (fns1(W1[3]) + W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & gMASK;
                W2[5] = (fns1(W2[3]) + W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & gMASK;
                W1[6] = (fns1(W1[4]) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & gMASK;
                W2[6] = (fns1(W2[4]) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & gMASK;
                for (int r = 4; r < 7; r++) {
                    sha_round(s1, KN[57+r], W1[r]);
                    sha_round(s2, KN[57+r], W2[r]);
                }
                int ok = 1;
                for (int r = 0; r < 8; r++) if (s1[r] != s2[r]) { ok = 0; break; }
                if (ok) {
                    printf("Found candidate: M[0]=0x%x fill=0x%x (bit-%d kernel)\n",
                           m0, fills[fi], kbit);
                    found = 1;
                    /* If pipe format was used, store W2 for verification */
                    if (!need_w2) {
                        /* Verify W2[57] matches */
                        uint32_t ts1[8], ts2[8];
                        memcpy(ts1, state56_1, 32); memcpy(ts2, state56_2, 32);
                        uint32_t w2_check = find_w2(ts1, ts2, 57, coll_w1[0][0]);
                        if (w2_check != coll_w2[0][0]) {
                            printf("WARNING: W2 mismatch for pipe format!\n");
                            found = 0;
                        }
                    }
                }
            }
        }
    }

    if (!found) {
        fprintf(stderr, "Cannot identify kernel/candidate. Please provide known state.\n");
        return 1;
    }

    /* If COLL format, compute W2 for each collision */
    if (need_w2) {
        for (int c = 0; c < n_coll; c++) {
            uint32_t s1[8], s2[8];
            memcpy(s1, state56_1, 32); memcpy(s2, state56_2, 32);
            for (int r = 0; r < 4; r++) {
                coll_w2[c][r] = find_w2(s1, s2, 57+r, coll_w1[c][r]);
                sha_round(s1, KN[57+r], coll_w1[c][r]);
                sha_round(s2, KN[57+r], coll_w2[c][r]);
            }
        }
        printf("Computed W2 values for all %d collisions\n", n_coll);
    }

    /* Build complete schedule for each collision */
    printf("\n--- Extracting carry states for %d collisions ---\n\n", n_coll);

    for (int c = 0; c < n_coll; c++) {
        /* Build W[57]..W[63] for path 1 and path 2 */
        uint32_t W1[7], W2[7];
        W1[0] = coll_w1[c][0]; W1[1] = coll_w1[c][1];
        W1[2] = coll_w1[c][2]; W1[3] = coll_w1[c][3];
        W2[0] = coll_w2[c][0]; W2[1] = coll_w2[c][1];
        W2[2] = coll_w2[c][2]; W2[3] = coll_w2[c][3];

        /* Schedule: W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45] */
        W1[4] = (fns1(W1[2]) + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & gMASK;
        W2[4] = (fns1(W2[2]) + W2pre[54] + fns0(W2pre[46]) + W2pre[45]) & gMASK;
        W1[5] = (fns1(W1[3]) + W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & gMASK;
        W2[5] = (fns1(W2[3]) + W2pre[55] + fns0(W2pre[47]) + W2pre[46]) & gMASK;
        W1[6] = (fns1(W1[4]) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & gMASK;
        W2[6] = (fns1(W2[4]) + W2pre[56] + fns0(W2pre[48]) + W2pre[47]) & gMASK;

        extract_all_carries(state56_1, W1, carry1[c]);
        extract_all_carries(state56_2, W2, carry2[c]);

        /* Compute carry diffs */
        for (int k = 0; k < gN; k++)
            for (int a = 0; a < TOTAL_ADDS; a++)
                carry_diff[c][k][a] = carry1[c][k][a] ^ carry2[c][k][a];
    }

    /* ===== ANALYSIS 1: Width at each bit (permutation check) ===== */
    printf("=== Carry State Width at Each Bit ===\n");
    printf("(Path 1 carries, Path 2 carries, Carry-diffs)\n\n");
    printf("Bit   P1-unique  P2-unique  Diff-unique  Permutation?\n");

    int is_permutation = 1;
    for (int k = 0; k < gN; k++) {
        /* Count unique states for path 1 */
        int p1_unique = 0;
        for (int c = 0; c < n_coll; c++) {
            int dup = 0;
            for (int c2 = 0; c2 < c; c2++) {
                if (carry_state_equal(carry1[c][k], carry1[c2][k])) { dup = 1; break; }
            }
            if (!dup) p1_unique++;
        }
        /* Count unique states for path 2 */
        int p2_unique = 0;
        for (int c = 0; c < n_coll; c++) {
            int dup = 0;
            for (int c2 = 0; c2 < c; c2++) {
                if (carry_state_equal(carry2[c][k], carry2[c2][k])) { dup = 1; break; }
            }
            if (!dup) p2_unique++;
        }
        /* Count unique carry-diff states */
        int d_unique = 0;
        for (int c = 0; c < n_coll; c++) {
            int dup = 0;
            for (int c2 = 0; c2 < c; c2++) {
                if (carry_state_equal(carry_diff[c][k], carry_diff[c2][k])) { dup = 1; break; }
            }
            if (!dup) d_unique++;
        }

        const char *perm = (p1_unique == n_coll && p2_unique == n_coll) ? "YES" : "no";
        if (p1_unique != n_coll || p2_unique != n_coll) is_permutation = 0;
        printf("  %d    %4d       %4d       %4d         %s\n",
               k, p1_unique, p2_unique, d_unique, perm);
    }
    printf("\nOverall permutation: %s\n", is_permutation ? "YES (every collision has unique carry state)" : "NO");

    /* ===== ANALYSIS 2: Per-addition invariance ===== */
    printf("\n=== Per-Addition Carry-Diff Invariance ===\n");
    printf("(Fraction of collisions sharing the same carry-diff at each bit)\n\n");

    int total_invariant = 0, total_bits = 0;
    for (int r = 0; r < ROUNDS; r++) {
        printf("Round %d (%s):\n", 57+r, r < ROUNDS ? "active" : "");
        for (int a = 0; a < ADDS_PER_ROUND; a++) {
            int add_idx = r * ADDS_PER_ROUND + a;
            int inv_count = 0;
            for (int k = 0; k < gN; k++) {
                /* Check if all collisions have the same carry-diff at this (bit, add) */
                int all_same = 1;
                for (int c = 1; c < n_coll; c++) {
                    if (carry_diff[c][k][add_idx] != carry_diff[0][k][add_idx]) {
                        all_same = 0; break;
                    }
                }
                if (all_same) inv_count++;
            }
            total_invariant += inv_count;
            total_bits += gN;
            printf("  %14s: %d/%d bits invariant (%5.1f%%)",
                   add_names[a], inv_count, gN, 100.0 * inv_count / gN);
            if (inv_count == gN) printf(" *** 100%%");
            printf("\n");
        }
    }
    printf("\nTotal: %d/%d carry-diff bits invariant (%.1f%%)\n",
           total_invariant, total_bits, 100.0 * total_invariant / total_bits);

    /* ===== ANALYSIS 3: Transition structure ===== */
    printf("\n=== Transition Structure (bit k -> bit k+1) ===\n\n");

    for (int k = 0; k < gN - 1; k++) {
        /* Build transition: carry_state at bit k -> carry_state at bit k+1 */
        /* Since it's a permutation, each state at bit k maps to exactly one at bit k+1 */
        /* Check: is the transition deterministic? (one successor per state) */
        int max_successors = 0;
        for (int c = 0; c < n_coll; c++) {
            int succ_count = 0;
            for (int c2 = 0; c2 < n_coll; c2++) {
                if (carry_state_equal(carry1[c][k], carry1[c2][k])) {
                    succ_count++;
                }
            }
            if (succ_count > max_successors) max_successors = succ_count;
        }
        /* Since carry_state at k is unique (permutation), succ_count should be 1 for all */
        printf("  Bit %d -> %d: max successors = %d %s\n",
               k, k+1, max_successors,
               max_successors == 1 ? "(deterministic)" : "(BRANCHING!)");
    }

    /* ===== ANALYSIS 4: Carry-diff classification ===== */
    printf("\n=== Carry-Diff Pattern Classification ===\n\n");

    /* For each round, which additions have carry-diffs that are constant (same for all collisions)? */
    printf("Round  Addition        Constant?  Value-at-bit0  Value-at-MSB\n");
    for (int r = 0; r < ROUNDS; r++) {
        for (int a = 0; a < ADDS_PER_ROUND; a++) {
            int add_idx = r * ADDS_PER_ROUND + a;
            int constant_all = 1;
            for (int k = 0; k < gN; k++) {
                for (int c = 1; c < n_coll; c++) {
                    if (carry_diff[c][k][add_idx] != carry_diff[0][k][add_idx]) {
                        constant_all = 0; break;
                    }
                }
                if (!constant_all) break;
            }
            if (constant_all) {
                printf("  %2d   %14s   CONSTANT    %d              %d\n",
                       57+r, add_names[a],
                       carry_diff[0][0][add_idx],
                       carry_diff[0][gN-1][add_idx]);
            } else {
                /* Count how many distinct patterns there are */
                int distinct = 0;
                for (int c = 0; c < n_coll; c++) {
                    int dup = 0;
                    for (int c2 = 0; c2 < c; c2++) {
                        int same = 1;
                        for (int k = 0; k < gN; k++) {
                            if (carry_diff[c][k][add_idx] != carry_diff[c2][k][add_idx]) {
                                same = 0; break;
                            }
                        }
                        if (same) { dup = 1; break; }
                    }
                    if (!dup) distinct++;
                }
                printf("  %2d   %14s   variable    (%d distinct patterns)\n",
                       57+r, add_names[a], distinct);
            }
        }
    }

    /* ===== ANALYSIS 5: Hamming distance between carry states ===== */
    printf("\n=== Carry State Hamming Distances (Path 1, bit 0) ===\n");
    int min_dist = TOTAL_ADDS + 1, max_dist = 0;
    long long sum_dist = 0;
    int n_pairs = 0;
    for (int c = 0; c < n_coll && c < 500; c++) {
        for (int c2 = c+1; c2 < n_coll && c2 < 500; c2++) {
            int d = 0;
            for (int a = 0; a < TOTAL_ADDS; a++)
                d += (carry1[c][0][a] != carry1[c2][0][a]);
            if (d < min_dist) min_dist = d;
            if (d > max_dist) max_dist = d;
            sum_dist += d;
            n_pairs++;
        }
    }
    if (n_pairs > 0)
        printf("  Min: %d  Max: %d  Mean: %.1f  (of %d bits)\n",
               min_dist, max_dist, (double)sum_dist / n_pairs, TOTAL_ADDS);

    /* ===== ANALYSIS 6: Active carry-diff bits (T1-path freedom) ===== */
    printf("\n=== T1-path vs T2-path Freedom ===\n");
    int t1_free = 0, t2_free = 0, t1_total = 0, t2_total = 0;
    for (int r = 0; r < ROUNDS; r++) {
        for (int a = 0; a < ADDS_PER_ROUND; a++) {
            int add_idx = r * ADDS_PER_ROUND + a;
            int is_t2_path = (a == 4 || a == 5 || a == 6); /* Sig0+Maj, d+T1, T1+T2 */
            for (int k = 0; k < gN; k++) {
                int variable = 0;
                for (int c = 1; c < n_coll; c++) {
                    if (carry_diff[c][k][add_idx] != carry_diff[0][k][add_idx]) {
                        variable = 1; break;
                    }
                }
                if (is_t2_path) { t2_total++; if (variable) t2_free++; }
                else { t1_total++; if (variable) t1_free++; }
            }
        }
    }
    printf("  T1-path (h+Sig1, +Ch, +K, +W): %d/%d free (%.1f%%)\n",
           t1_free, t1_total, 100.0*t1_free/t1_total);
    printf("  T2-path (Sig0+Maj, d+T1, T1+T2): %d/%d free (%.1f%%)\n",
           t2_free, t2_total, 100.0*t2_free/t2_total);
    printf("  Total free: %d/%d (%.1f%%)\n",
           t1_free+t2_free, t1_total+t2_total,
           100.0*(t1_free+t2_free)/(t1_total+t2_total));

    printf("\n=== Done ===\n");
    return 0;
}
