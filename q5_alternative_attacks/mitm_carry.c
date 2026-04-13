/*
 * mitm_carry.c — Meet-in-the-middle on carry states
 *
 * Split the 7-round cascade at round 60:
 * - Forward: rounds 57-60 (4 free message words → state60)
 * - Backward: rounds 63-61 (3 determined message words → state60)
 *
 * Forward has 2^{4N} configurations → ~C collisions' worth of state60 values.
 * Backward has 2^{3N} configurations.
 * Match at state60: forward state60 == backward state60.
 *
 * At N=4: forward has 2^16 = 65536 states, backward has 2^12 = 4096.
 * Both can be stored in hash tables and matched.
 *
 * Key insight from carry automaton: the carry states at round 60 are
 * highly constrained. The a-path is fully invariant from round 59+,
 * meaning da60=db60=dc60=dd60=0. Only de60 differs between collisions.
 *
 * Compile: gcc -O3 -march=native -o mitm_carry mitm_carry.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define MAX_N 8
#define MAX_STATES (1 << 24)  /* up to 2^{3*8} = 16M for backward at N=8 */

static int gN;
static uint32_t gMASK;
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static uint32_t KN[64], IVN[8];

static inline uint32_t ror_n(uint32_t x, int k) { k %= gN; return ((x >> k) | (x << (gN - k))) & gMASK; }
static inline uint32_t fnS0(uint32_t a) { return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & gMASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & gMASK); }
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e & f) ^ ((~e) & g)) & gMASK; }
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & gMASK; }
static const uint32_t K32[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static int scale_rot(int k32) { int r = (int)rint((double)k32 * gN / 32.0); return r < 1 ? 1 : r; }

static uint32_t W1pre[57], W2pre[57], state1[8], state2[8];

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & gMASK;
    for (int i = 16; i < 57; i++) W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i]) & gMASK;
        uint32_t T2 = (fnS0(a)+fnMj(a,b,c)) & gMASK;
        h=g; g=f; f=e; e=(d+T1)&gMASK; d=c; c=b; b=a; a=(T1+T2)&gMASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w) & gMASK;
    uint32_t T2 = (fnS0(s[0])+fnMj(s[0],s[1],s[2])) & gMASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&gMASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&gMASK;
}

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd]) & gMASK;
    uint32_t r2 = (s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd]) & gMASK;
    uint32_t T21 = (fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2])) & gMASK;
    uint32_t T22 = (fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2])) & gMASK;
    return (w1 + r1 - r2 + T21 - T22) & gMASK;
}

/* Inverse round: given output state and round constant/message word,
 * recover input state. Uses the shift register structure.
 *
 * Forward:  (a,b,c,d,e,f,g,h) + K + W → (a_new, a, b, c, e_new, e, f, g)
 * So: b_out=a_in, c_out=b_in, d_out=c_in, f_out=e_in, g_out=f_in, h_out=g_in
 * Inverse: a_in=b_out, b_in=c_out, c_in=d_out, e_in=f_out, f_in=g_out, g_in=h_out
 * And: a_out = T1+T2, e_out = d_out + T1 → T1 = e_out - d_out = e_out - c_in
 * T2 = a_out - T1
 *
 * But we also need W for the inverse, and for the backward pass, the schedule
 * words W[61], W[62], W[63] are DETERMINED by W[57..60].
 *
 * The MITM split: we guess W[57..60] for the forward pass, giving state60.
 * For the backward pass, we need W[61..63], but these depend on W[57..60]!
 * Specifically:
 *   W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
 *   W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
 *   W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
 *
 * W[61] depends on W[59] only (plus constants).
 * W[62] depends on W[60] only (plus constants).
 * W[63] depends on W[61] → W[59] only.
 *
 * So W[61..63] depend on W[59..60] but NOT on W[57..58]!
 *
 * This means we can split differently:
 * Forward: fix W[59], W[60] → compute W[61], W[62], W[63]
 *          → run rounds 59-63 backward from collision → get state59 constraint
 * Inner: for each (W[57], W[58]): run forward from state56 to state59
 *        → check if state59 matches the backward constraint
 *
 * This is a 2-layer MITM:
 * Outer: W[59], W[60] (2^{2N} choices)
 * Inner: W[57], W[58] (2^{2N} choices)
 * Match at state59 (8*N bits)
 *
 * Total: 2^{2N} * (2^{2N} + backward_cost) vs brute-force 2^{4N}
 * If backward is O(1) per outer iteration, total is O(2^{2N} * 2^{2N}) = O(2^{4N})
 * — no speedup!
 *
 * But with CACHING: precompute all 2^{2N} forward states (from W57,W58),
 * then for each backward state (from W59,W60,W61..63), look up matching
 * forward states in a hash table.
 *
 * Forward table: 2^{2N} entries, each an 8*N-bit state59 value
 * Backward: for each of 2^{2N} (W59,W60) combos, compute state59 backward
 *           and look up in the forward table.
 * Total: O(2^{2N}) time + O(2^{2N}) space!
 *
 * This is a REAL MITM speedup: 2^{2N} vs 2^{4N}.
 * At N=4: 2^8 = 256 vs 2^16 = 65536 (256x speedup!)
 * At N=8: 2^16 = 65536 vs 2^32 = 4.3B (65536x speedup!)
 *
 * The catch: the backward computation requires INVERTING the SHA-256 rounds.
 * This is possible because the shift register makes the round invertible
 * when both T1 and T2 are known (which they are when we have the output state).
 */

/* Inverse SHA-256 round: given output state (a',b',c',d',e',f',g',h')
 * and the round constant K and message word W, recover the input state.
 *
 * From the shift register:
 *   a_in = b_out
 *   b_in = c_out
 *   c_in = d_out
 *   e_in = f_out
 *   f_in = g_out
 *   g_in = h_out
 *
 * From the round function:
 *   a_out = T1 + T2
 *   e_out = d_in + T1
 *   where T1 = h_in + Sigma1(e_in) + Ch(e_in, f_in, g_in) + K + W
 *         T2 = Sigma0(a_in) + Maj(a_in, b_in, c_in)
 *
 * We know a_in, b_in, c_in, e_in, f_in, g_in from the output.
 * T2 = Sigma0(a_in) + Maj(a_in, b_in, c_in) — fully known
 * T1 = a_out - T2 (mod 2^N)
 * d_in = e_out - T1 (mod 2^N)
 * h_in = T1 - Sigma1(e_in) - Ch(e_in, f_in, g_in) - K - W (mod 2^N)
 */
static void sha_round_inv(const uint32_t out[8], uint32_t in[8],
                           uint32_t k, uint32_t w) {
    /* Recover a_in..g_in from shift register */
    uint32_t a_in = out[1];
    uint32_t b_in = out[2];
    uint32_t c_in = out[3];
    uint32_t e_in = out[5];
    uint32_t f_in = out[6];
    uint32_t g_in = out[7];

    /* T2 from a-path */
    uint32_t T2 = (fnS0(a_in) + fnMj(a_in, b_in, c_in)) & gMASK;
    /* T1 = a_out - T2 */
    uint32_t T1 = (out[0] - T2) & gMASK;
    /* d_in = e_out - T1 */
    uint32_t d_in = (out[4] - T1) & gMASK;
    /* h_in = T1 - Sigma1(e_in) - Ch(e_in,f_in,g_in) - K - W */
    uint32_t h_in = (T1 - fnS1(e_in) - fnCh(e_in, f_in, g_in) - k - w) & gMASK;

    in[0] = a_in; in[1] = b_in; in[2] = c_in; in[3] = d_in;
    in[4] = e_in; in[5] = f_in; in[6] = g_in; in[7] = h_in;
}

/* Hash a state to 64-bit for hash table lookup */
static uint64_t hash_state(const uint32_t s[8]) {
    uint64_t h = 14695981039346656037ULL;
    for (int i = 0; i < 8; i++) {
        h ^= s[i];
        h *= 1099511628211ULL;
    }
    return h;
}

/* Simple hash table for MITM */
#define HT_SIZE (1 << 20)  /* 1M buckets */
#define HT_CHAIN 16        /* max chain length */
typedef struct {
    uint64_t hash;
    uint32_t w57, w58;
    uint32_t state[8];
} ht_entry_t;

static ht_entry_t ht_entries[MAX_STATES];
static int ht_heads[HT_SIZE];
static int ht_next[MAX_STATES];
static int ht_count;

static void ht_init(void) {
    memset(ht_heads, -1, sizeof(ht_heads));
    ht_count = 0;
}

static void ht_insert(uint64_t hash, uint32_t w57, uint32_t w58, const uint32_t state[8]) {
    int idx = ht_count++;
    ht_entries[idx].hash = hash;
    ht_entries[idx].w57 = w57;
    ht_entries[idx].w58 = w58;
    memcpy(ht_entries[idx].state, state, 32);
    int bucket = hash % HT_SIZE;
    ht_next[idx] = ht_heads[bucket];
    ht_heads[bucket] = idx;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    gN = argc > 1 ? atoi(argv[1]) : 4;
    if (gN > MAX_N) { printf("N must be <= %d\n", MAX_N); return 1; }
    gMASK = (1U << gN) - 1;

    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & gMASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & gMASK;

    /* Find candidate */
    uint32_t MSB = 1U << (gN - 1);
    uint32_t fills[] = {gMASK, 0};
    int found = 0;
    for (int fi = 0; fi < 2 && !found; fi++) {
        for (uint32_t m0 = 0; m0 <= gMASK && !found; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fills[fi]; M2[i] = fills[fi]; }
            M1[0] = m0; M2[0] = m0 ^ MSB; M2[9] = fills[fi] ^ MSB;
            precompute(M1, state1, W1pre);
            precompute(M2, state2, W2pre);
            if (state1[0] == state2[0]) {
                printf("Candidate: M[0]=0x%x fill=0x%x\n", m0, fills[fi]);
                found = 1;
            }
        }
    }
    if (!found) { printf("No candidate\n"); return 1; }

    printf("\nMITM Carry Solver at N=%d\n", gN);
    printf("Forward: W[57],W[58] → state59  (2^%d entries)\n", 2*gN);
    printf("Backward: W[59],W[60] → state59  (2^%d lookups)\n", 2*gN);
    printf("Total: O(2^%d) vs brute-force O(2^%d)\n\n", 2*gN, 4*gN);

    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    /* ===== PHASE 1: Forward pass — build hash table of state59 values ===== */
    printf("Phase 1: Forward pass (W57, W58 → state59)...\n");
    ht_init();

    for (uint32_t w57 = 0; w57 < (1U << gN); w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

        for (uint32_t w58 = 0; w58 < (1U << gN); w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

            /* Store (state59_path1, state59_path2) as combined hash */
            /* We need BOTH paths to match, so hash both together */
            uint64_t h = hash_state(s58a) ^ (hash_state(s58b) * 0x9E3779B97F4A7C15ULL);
            ht_insert(h, w57, w58, s58a);
            /* Also store path2 state — we'll need it for matching */
            /* Pack w57,w58 into the entry, retrieve later */
        }
    }
    printf("  Forward table: %d entries\n", ht_count);

    /* ===== PHASE 2: Backward pass — for each (W59,W60), compute state59 ===== */
    printf("Phase 2: Backward pass (W59, W60 → state59)...\n");

    int n_coll = 0;
    for (uint32_t w59 = 0; w59 < (1U << gN); w59++) {
        for (uint32_t w60 = 0; w60 < (1U << gN); w60++) {
            /* Compute W[61], W[62], W[63] from W[59], W[60] */
            uint32_t W1_61 = (fns1(w59) + W1pre[54] + fns0(W1pre[46]) + W1pre[45]) & gMASK;
            uint32_t W2_61_b; /* need w59b, but we don't know it yet! */

            /* Problem: W2[59] = find_w2(state58_path2, 59, w59)
             * which depends on state58_path2, which depends on W57, W58.
             * We don't know W57, W58 in the backward pass!
             *
             * This means we can't compute W2[61..63] without knowing the forward state.
             * The MITM doesn't fully separate because W2 values depend on both halves.
             *
             * HOWEVER: W1[61] = sigma1(W1[59]) + const depends ONLY on W1[59].
             * And W1[62] = sigma1(W1[60]) + const depends ONLY on W1[60].
             * And W1[63] = sigma1(W1[61]) + const depends ONLY on W1[59].
             *
             * So we CAN do the backward pass for PATH 1 only!
             * For path 2, we'd need to re-derive W2 values at match time.
             *
             * Alternative approach: backward from collision state = (0,0,...,0) diff
             * Since the collision means final state1 == final state2, we can run
             * path 1 backward from the SAME final state.
             *
             * Actually, the collision means: after round 63, all register diffs = 0.
             * So the final state of path 1 equals path 2.
             * We can run backward on PATH 1 ONLY and get state59 for path 1.
             * Then check if any forward state59 (from W57, W58) matches.
             */

            /* Compute schedule for path 1 */
            uint32_t W1_62 = (fns1(w60) + W1pre[55] + fns0(W1pre[47]) + W1pre[46]) & gMASK;
            uint32_t W1_63 = (fns1(W1_61) + W1pre[56] + fns0(W1pre[48]) + W1pre[47]) & gMASK;

            /* Forward path 1 from state58_fwd (unknown) through rounds 59-63 */
            /* We need to work BACKWARD from the collision constraint.
             *
             * But we don't know the final state! The collision says the two paths
             * have the same final state, but we don't know what that state IS.
             *
             * Hmm. The standard MITM doesn't work directly because:
             * 1. The backward computation requires knowing the TARGET state (unknown)
             * 2. The W2 schedule depends on the forward state through find_w2
             *
             * The collision constraint is: state_final_1 == state_final_2
             * This is 8*N equations, but we don't know the target.
             *
             * What we CAN do: forward from state56 with W57,W58,W59 (3*N bits),
             * then check round 60 with W60 (N bits) and rounds 61-63.
             * This is a 3-to-1 split: O(2^{3N}) forward, O(2^N) backward.
             * Not as good as 2-to-2.
             *
             * OR: use the CASCADE CONSTRAINT more cleverly.
             * The cascade says: at round 59+, da=0. This means
             * for collision checking, we can match on DIFFERENCES rather than values.
             *
             * Forward: compute (state59_1, state59_2) from (W57, W58, W59)
             * Backward: from the collision (diff=0 at round 63), compute what
             *           the diff should be at round 59.
             *
             * The diff at round 59 is determined by the cascade: da59=0 from
             * cascade, and de59 = dd58 + dT1_58 (from round 58).
             * The e-path diffs at round 59 are determined by rounds 57-58.
             *
             * This is getting complicated. Let me just implement the BRUTE FORCE
             * approach and then see how much the hash table helps.
             */

            /* Actually, let's do a simpler version:
             * Forward: (W57, W58) → state58 hash table (both paths)
             * For each (W59, W60):
             *   Forward from ALL state58 entries + W59 → state59
             *   Then do round 60-63 and check collision
             *
             * This doesn't save anything vs brute force!
             *
             * The REAL MITM needs to exploit the cascade structure.
             * Let me try a different approach: use the carry automaton width.
             */
            (void)W1_62; (void)W1_63; (void)W2_61_b;
            break;
        }
        break;
    }

    /* ===== APPROACH 2: Width-bounded forward search ===== */
    /* Since the carry automaton has width = #collisions at every bit,
     * we can enumerate state59 values that are COMPATIBLE with collisions.
     *
     * At round 59, da=0 from cascade. The compatible state59 values form
     * a set of size ~C (the collision count).
     *
     * For each compatible state59:
     *   - Check rounds 60-63 (with W60 as the only free variable)
     *   - This is O(2^N) per compatible state59
     * Total: O(C * 2^N)
     *
     * But we don't KNOW the compatible state59 values without computing
     * from W57, W58, W59. The width bound tells us they exist but not how
     * to find them without the forward pass.
     */

    /* ===== APPROACH 3: Simple brute force with MITM accounting ===== */
    printf("\nRunning brute force (for correctness verification)...\n");
    n_coll = 0;
    for (uint32_t w57 = 0; w57 < (1U << gN); w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);
        for (uint32_t w58 = 0; w58 < (1U << gN); w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);
            for (uint32_t w59 = 0; w59 < (1U << gN); w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);
                for (uint32_t w60 = 0; w60 < (1U << gN); w60++) {
                    uint32_t fa[8], fb[8];
                    memcpy(fa, s59a, 32); memcpy(fb, s59b, 32);
                    uint32_t w60b = find_w2(fa, fb, 60, w60);
                    sha_round(fa, KN[60], w60); sha_round(fb, KN[60], w60b);
                    uint32_t W1[7]={w57,w58,w59,w60,0,0,0}, W2[7]={w57b,w58b,w59b,w60b,0,0,0};
                    W1[4]=(fns1(W1[2])+W1pre[54]+fns0(W1pre[46])+W1pre[45])&gMASK;
                    W2[4]=(fns1(W2[2])+W2pre[54]+fns0(W2pre[46])+W2pre[45])&gMASK;
                    W1[5]=(fns1(W1[3])+W1pre[55]+fns0(W1pre[47])+W1pre[46])&gMASK;
                    W2[5]=(fns1(W2[3])+W2pre[55]+fns0(W2pre[47])+W2pre[46])&gMASK;
                    W1[6]=(fns1(W1[4])+W1pre[56]+fns0(W1pre[48])+W1pre[47])&gMASK;
                    W2[6]=(fns1(W2[4])+W2pre[56]+fns0(W2pre[48])+W2pre[47])&gMASK;
                    for (int r = 4; r < 7; r++) {
                        sha_round(fa, KN[57+r], W1[r]);
                        sha_round(fb, KN[57+r], W2[r]);
                    }
                    int ok = 1;
                    for (int r = 0; r < 8; r++) if (fa[r] != fb[r]) { ok = 0; break; }
                    if (ok) n_coll++;
                }
            }
        }
    }

    struct timespec t1;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double el = (t1.tv_sec-t0.tv_sec) + (t1.tv_nsec-t0.tv_nsec)/1e9;

    printf("\n=== Results ===\n");
    printf("N=%d, Collisions: %d\n", gN, n_coll);
    printf("Brute force time: %.3fs\n", el);
    printf("Forward table size: %d entries (2^%d = %d expected)\n",
           ht_count, 2*gN, 1 << (2*gN));

    /* Test inverse round */
    printf("\n=== Inverse Round Verification ===\n");
    {
        uint32_t fwd[8], inv[8], orig[8];
        memcpy(orig, state1, 32);
        memcpy(fwd, state1, 32);
        sha_round(fwd, KN[57], 0x05);
        sha_round_inv(fwd, inv, KN[57], 0x05);
        int match = 1;
        for (int i = 0; i < 8; i++) if (orig[i] != inv[i]) match = 0;
        printf("Forward then inverse: %s\n", match ? "MATCH" : "MISMATCH");
        if (!match) {
            for (int i = 0; i < 8; i++)
                printf("  reg[%d]: orig=%x inv=%x\n", i, orig[i], inv[i]);
        }
    }

    printf("\n=== MITM Analysis ===\n");
    printf("Standard: O(2^%d) = %llu operations\n", 4*gN, 1ULL << (4*gN));
    printf("MITM could be: O(2^%d) = %d operations (with inverse rounds)\n",
           2*gN, 1 << (2*gN));
    printf("Speedup potential: %dx\n", 1 << (2*gN));
    printf("\nNote: the W2 schedule depends on forward state, preventing\n");
    printf("clean separation. The cascade constraint (da=0) helps but\n");
    printf("doesn't fully decouple the two halves.\n");
    printf("\nPath forward: exploit carry automaton width bound (C=%d)\n", n_coll);
    printf("to enumerate only compatible carry states at the midpoint.\n");

    return 0;
}
