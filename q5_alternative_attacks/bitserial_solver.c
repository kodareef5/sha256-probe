/*
 * bitserial_solver.c — TRUE bit-serial collision solver for N=4 mini-SHA
 *
 * Instead of brute-forcing all 2^{4N} = 65536 message combos, this solver
 * processes one BIT POSITION at a time (LSB to MSB). At each bit position,
 * it maintains a pool of "states" — each state encodes the carry information
 * from all additions processed so far. Only states that COULD lead to a
 * collision survive to the next bit.
 *
 * Algorithm outline:
 *   For bit b = 0, 1, 2, 3 (LSB to MSB):
 *     For each surviving state S from bit b-1:
 *       For each (w57_b, w58_b, w59_b, w60_b) in {0,1}^4:
 *         1. Run 7 cascade rounds (57-63) at bit position b for BOTH paths
 *         2. Extract carry-out from every addition in both paths
 *         3. Check output register diff at bit b (all 8 must match)
 *         4. If survives: record new carry state
 *     Deduplicate states by carry signature
 *
 * The state between bits is the set of carry-out bits from the last processed
 * bit position. At N=4 with 7 rounds and 7 additions per round per path,
 * that's 7*7*2 = 98 carry bits. But we also need to track the partially-built
 * register values (bits 0..b) for computing Sigma/Ch/Maj at future bits.
 *
 * KEY METRIC: how many states survive at each bit? If bounded by ~49
 * (the collision count), the solver is efficient.
 *
 * Setup: N=4, MSB kernel, M[0]=0x0, fill=0xf
 * Expected: 49 collisions (verified by brute force in cascade_dp_fast.c)
 *
 * Compile: gcc -O3 -march=native -o bitserial_solver bitserial_solver.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ===== Mini-SHA-256 at N=4 bits ===== */

#define N 4
#define MASK ((1U << N) - 1)
#define MSB_BIT (1U << (N - 1))

/* Scaled rotation amounts */
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
static inline uint32_t fn_S0(uint32_t a) {
    return ror_n(a, r_Sig0[0]) ^ ror_n(a, r_Sig0[1]) ^ ror_n(a, r_Sig0[2]);
}
static inline uint32_t fn_S1(uint32_t e) {
    return ror_n(e, r_Sig1[0]) ^ ror_n(e, r_Sig1[1]) ^ ror_n(e, r_Sig1[2]);
}
static inline uint32_t fn_s0(uint32_t x) {
    return ror_n(x, r_sig0[0]) ^ ror_n(x, r_sig0[1]) ^ ((x >> s_sig0) & MASK);
}
static inline uint32_t fn_s1(uint32_t x) {
    return ror_n(x, r_sig1[0]) ^ ror_n(x, r_sig1[1]) ^ ((x >> s_sig1) & MASK);
}
static inline uint32_t fn_Ch(uint32_t e, uint32_t f, uint32_t g) {
    return ((e & f) ^ ((~e) & g)) & MASK;
}
static inline uint32_t fn_Maj(uint32_t a, uint32_t b, uint32_t c) {
    return ((a & b) ^ (a & c) ^ (b & c)) & MASK;
}

/* Full SHA-256 constants */
static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

/* N-bit constants and precomputed state */
static uint32_t KN[64], IVN[8];
static uint32_t st1_56[8], st2_56[8];     /* register state at round 57 entry */
static uint32_t W1_pre[57], W2_pre[57];   /* precomputed schedule words 0..56 */

/* Precompute: expand message schedule through W[56], run rounds 0-56 */
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

/* Cascade offset: find W2 such that da_{round+1} = 0 given W1 */
static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t rest1 = (s1[7] + fn_S1(s1[4]) + fn_Ch(s1[4],s1[5],s1[6]) + KN[rnd]) & MASK;
    uint32_t rest2 = (s2[7] + fn_S1(s2[4]) + fn_Ch(s2[4],s2[5],s2[6]) + KN[rnd]) & MASK;
    uint32_t T2_1  = (fn_S0(s1[0]) + fn_Maj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T2_2  = (fn_S0(s2[0]) + fn_Maj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + rest1 - rest2 + T2_1 - T2_2) & MASK;
}

/* One SHA-256 round in place */
static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fn_S1(s[4]) + fn_Ch(s[4],s[5],s[6]) + k + w) & MASK;
    uint32_t T2 = (fn_S0(s[0]) + fn_Maj(s[0],s[1],s[2])) & MASK;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = (s[3] + T1) & MASK;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = (T1 + T2) & MASK;
}

/* ===========================================================================
 * BIT-SERIAL STATE
 *
 * Between bit positions, the state that determines future behavior consists of:
 *
 * 1. The CARRY-OUT bits from every addition at the current bit position.
 *    These become the carry-in to the NEXT bit position's additions.
 *
 * 2. The partial register values (bits 0..b) for both paths after each round.
 *    These are needed because Sigma/Ch/Maj at bit b+1 may reference bits at
 *    rotated positions that we've already computed.
 *
 * For N=4 with 7 rounds (57-63):
 *   Each round has these additions:
 *     T1 chain: add0: h+Sig1(e), add1: +Ch, add2: +K, add3: +W  (4 adds)
 *     T2:       add4: Sig0(a)+Maj                                (1 add)
 *     new_e:    add5: d+T1                                       (1 add)
 *     new_a:    add6: T1+T2                                      (1 add)
 *   = 7 adds per round × 7 rounds × 2 paths = 98 carry bits
 *
 * Plus the 8 register values × 2 paths × (bits 0..b) = evolving state.
 *
 * For deduplication, two states are equivalent if they have the same carry
 * bits AND the same register bit-slices at all positions 0..b.
 *
 * At N=4 with only 4 bits, the register state at bit b includes bits 0..b
 * for all 8 registers × 2 paths = up to 8×2×4 = 64 bits. Combined with
 * 98 carry bits, the full state is at most ~162 bits. This is manageable
 * with hashing.
 *
 * CRITICAL INSIGHT: The register state after each round at bits 0..b is
 * FULLY DETERMINED by the initial state56 (constant) plus the message
 * word bits at positions 0..b plus the carry-in bits. So two states with
 * the same carries and the same message-word bits 0..b will have identical
 * register states. We can use carries + w1_bits_so_far as the state key,
 * but it's simpler and more general to use carries + register bit-slices.
 *
 * SIMPLIFICATION: Rather than tracking individual addition carries, we
 * track the full register state after all 7 rounds at bits 0..b for both
 * paths. Two partial evaluations with the same register bit-slices at
 * bits 0..b will produce identical behavior at bit b+1 (same inputs to
 * all Sigma/Ch/Maj/addition functions, same carry propagation).
 *
 * Actually, that's not quite right: the carries from bit b's additions
 * feed into bit b+1. The register state at bits 0..b already encodes the
 * RESULTS of those carries, but not the carry-outs themselves. Two
 * different carry-out configurations could produce the same register bits
 * at 0..b but diverge at b+1.
 *
 * CORRECT STATE: The state between bit b and b+1 is:
 *   (1) Register values at bits 0..b for both paths after all 7 rounds
 *       (determines Sigma/Ch/Maj inputs at future bits)
 *   (2) Carry-out bits from each addition at bit b
 *       (determines carry-in at bit b+1)
 *
 * For efficiency, we encode the state as a hash of these components.
 * =========================================================================== */

/*
 * APPROACH: Instead of abstracting the carry state, we take a concrete but
 * bit-serial approach. We enumerate all 16 input bit combos at each bit
 * position, compute the full cascade for both paths at that bit, and track
 * the CONCRETE intermediate state.
 *
 * The state between bit b and b+1 for one path is:
 *   - 8 register values, each with bits 0..b determined
 *   - 7 rounds × 7 additions = 49 carry-out bits from bit b
 *
 * Two "threads" with identical (registers[0..b], carries) will behave
 * identically at all future bits, so we can merge them.
 *
 * We encode the state as:
 *   - For each path: 8 register values masked to bits 0..b
 *   - For each path: 49 carry-out bits from bit b
 * Total: ~162 bits → fits in 3 uint64_t → hashable
 *
 * But actually, since path2 state is deterministic given path1 state
 * (because W2 is derived from W1 via cascade offset, and the cascade offset
 * depends on the current state of BOTH paths), we need to track both paths.
 *
 * FURTHER SIMPLIFICATION: At N=4, the total search space is only 2^16.
 * Even the state space is bounded. We can afford to be somewhat wasteful.
 * Let's use a direct approach:
 *
 * State = { reg1[8], reg2[8] (masked to bits 0..b), carry1[49], carry2[49] }
 *
 * We store states in a hash table keyed on the full state.
 */

#define ROUNDS 7          /* rounds 57-63 */
#define ADDS_PER_ROUND 7  /* 7 additions per round per path */
#define TOTAL_ADDS (ROUNDS * ADDS_PER_ROUND)  /* 49 */

/* State for the bit-serial solver */
typedef struct {
    uint32_t reg1[8];     /* path1 register state (bits 0..b after all 7 rounds) */
    uint32_t reg2[8];     /* path2 register state */
    uint8_t carry1[TOTAL_ADDS];  /* carry-out from each addition, path1, at current bit */
    uint8_t carry2[TOTAL_ADDS];  /* carry-out from each addition, path2, at current bit */
    uint32_t w1_accum[4]; /* accumulated W1[57..60] bits 0..b (for final reporting) */
} bs_state_t;

/* State pools — size bound for N=4 */
#define MAX_STATES (1 << 20)  /* 1M max states — generous for N=4 */

/*
 * Process one round at one bit position for one path.
 *
 * Inputs:
 *   reg[8]     — current register state (full N-bit values, but only bits 0..b matter)
 *   k          — round constant KN[round]
 *   w          — schedule word for this round (full N-bit value)
 *   carry_in[7] — carry-in to each of the 7 additions from the previous bit
 *   bit        — current bit position
 *
 * Outputs:
 *   new_reg[8]  — updated register state with bit 'b' of each register set
 *   carry_out[7] — carry-out from each addition at this bit
 *
 * The round function at bit b computes each intermediate value's bit b from
 * the input bits at position b (and rotated positions for Sigma/Ch/Maj)
 * plus carry-in from bit b-1.
 *
 * For Sigma functions: ror(x, r) at bit b reads x at bit (b+r)%N.
 * This references bits we may not have processed yet (if b+r >= N, it wraps
 * to a LOWER bit we already have, since we go LSB to MSB; if b+r < N,
 * it's a FUTURE bit). But wait — at N=4 all positions are in 0..3. At bit b,
 * positions (b+r)%N for r=1,2,3 cycle through the other positions. Some of
 * those are > b (future bits), which are NOT YET DETERMINED.
 *
 * THIS IS THE ROTATION FRONTIER PROBLEM.
 *
 * Solution for this solver: instead of working bit-serially on intermediate
 * values, we compute the Sigma/Ch/Maj functions using the FULL N-bit register
 * values. This is valid because the input registers to rounds 57-63 are built
 * up bit by bit, and the full-word Sigma/Ch/Maj evaluation at bit b gives
 * the CORRECT result for bit b (Sigma is a bitwise XOR of rotations; Ch and
 * Maj are bitwise functions). The higher bits of the result don't matter yet.
 *
 * The KEY insight: Sigma0(a) at bit b = (ror(a,r0) ^ ror(a,r1) ^ ror(a,r2))
 * at bit b. This reads a at bits (b+r0)%N, (b+r1)%N, (b+r2)%N. If any of
 * these are > b, they reference bits of 'a' that haven't been computed yet
 * for THIS round's output — but 'a' here is the INPUT register to this round,
 * which was the OUTPUT of the previous round. At round 57, the input is
 * state56 which is fully known (all N bits). At round 58, the input registers
 * include new_a57 and new_e57 which we're building bit by bit.
 *
 * FOR THIS BIT-SERIAL SOLVER: we need to handle the fact that rounds 58+
 * reference partially-built register values where high bits aren't determined.
 *
 * PRACTICAL APPROACH: We DON'T compute round-by-round at each bit. Instead,
 * at each bit position b, we pick the 4 message word bits (w57_b..w60_b),
 * and then we need to evaluate ALL 7 ROUNDS at bit b. But the later rounds
 * depend on earlier rounds' results at bit b (and other bits via rotations).
 *
 * The correct concrete approach that avoids all these headaches:
 *
 * At each bit position b, for a given input state (carries from bit b-1 +
 * register bits 0..b-1 from previous rounds), and a given choice of
 * message word bits, we compute EACH ROUND's contribution at bit b in order.
 *
 * For round r = 57..63:
 *   The input registers to round r at bit b come from:
 *     - Bits 0..b-1: determined by previous bit positions (stored in state)
 *     - Bit b: determined by round r-1's output at bit b (just computed)
 *     - Bits b+1..N-1: for round 57, fully known from state56.
 *                       For round 58+, bits b+1..N-1 of registers that were
 *                       modified by rounds 57+ are UNKNOWN.
 *
 * This means Sigma/Ch/Maj at bit b for round 58+ might read unknown bits.
 * We must BRANCH on those unknown bits, vastly expanding the state space.
 *
 * HOWEVER: Sigma is XOR of rotations. XOR of unknown bits is still an unknown
 * bit — we'd need to branch on the result. Ch(e,f,g) at bit b: if e's bit
 * at the rotated position is unknown, Ch is undetermined.
 *
 * FOR N=4 THIS IS TRACTABLE because there are only 4 bits total and the
 * state space is bounded by 65536.
 *
 * ===== CLEANEST CORRECT APPROACH =====
 *
 * Process bit b for ALL 7 rounds sequentially. For round 57, the input
 * state is fully known (state56 has all N bits). We compute bit b of each
 * addition using carry_in from bit b-1 and the known input bits. This gives
 * us bit b of the round 57 output registers.
 *
 * For round 58, the input registers are the round 57 output. Bits 0..b are
 * now known. But Sigma/Ch/Maj at bit b reference rotated bit positions. Some
 * of these rotated positions are > b and come from round 57's output at those
 * higher bit positions, which we HAVEN'T COMPUTED YET at this point in the
 * bit-serial sweep.
 *
 * RESOLUTION: For bits that reference higher positions of NEWLY COMPUTED
 * registers (new_a, new_e from round 57), those bits are unknown and we
 * must branch. But there's a BETTER way:
 *
 * We can compute the full N-bit intermediate values for each round because
 * we know ALL the input bits to round 57 (state56 is constant), and we
 * know which message word bits have been chosen (0..b). For message word
 * bits b+1..N-1, those are NOT YET CHOSEN — these are future variables.
 *
 * The TRICK: instead of a pure bit-serial sweep over rounds, use a
 * HYBRID approach:
 *
 * For each surviving state at bit b-1 (which fixes w[57..60] at bits 0..b-1):
 *   For each choice of (w57_b, w58_b, w59_b, w60_b):
 *     We now know w[57..60] at bits 0..b. Build partial N-bit words where
 *     bits 0..b are concrete and bits b+1..N-1 are ZERO (placeholder).
 *     But this gives WRONG Sigma/Ch/Maj values for the upper bits!
 *
 * ACTUAL CLEANEST APPROACH: Track the full N-bit register values for both
 * paths through all 7 rounds, but only CHECK/CONSTRAIN bit b of the output.
 * This means at each bit step, we do a FULL cascade evaluation (all N bits)
 * and only impose the constraint that the output differs by 0 at bit b.
 *
 * This is basically the same as bitserial_dp.c but with proper state merging.
 * The computational cost per state per bit is O(1) full cascade evaluations
 * (constant N=4), and the win comes from PRUNING states whose output diff
 * bit b is nonzero, and MERGING states that are equivalent.
 *
 * But wait — we can't do a full cascade evaluation without knowing ALL N bits
 * of the message words. At bit b, we only know bits 0..b.
 *
 * ===== THE TRUE BIT-SERIAL ALGORITHM =====
 *
 * The correct bit-serial approach needs to handle additions carefully:
 *
 * For a multi-operand addition like T1 = h + Sig1(e) + Ch(e,f,g) + K + W,
 * bit b of T1 depends on bits 0..b of the operands (through carries) and
 * bit b of each operand directly.
 *
 * Sigma/Ch/Maj at bit b reference specific bits of the input registers.
 * For round 57, all input register bits are known (state56 is constant).
 * For round 58, the SHIFTED registers (b,c,d,f,g,h) are just the previous
 * round's input registers (known from state56), but a(=new_a57) and
 * e(=new_e57) have bits that we're computing.
 *
 * At bit position b, if we process round 57 first, we get new_a57[b] and
 * new_e57[b]. Then for round 58:
 *   Sigma1(e58) at bit b: e58 = new_e57, reads bits (b+r)%N of new_e57.
 *   If (b+r)%N <= b: we know that bit. If > b: unknown.
 *
 * At N=4 with rotations {1,2,3}: at bit 0, Sigma reads bits 1,2,3 — all
 * unknown. At bit 1, reads bits 2,3,0 — bit 0 known, bits 2,3 unknown.
 * At bit 2, reads bits 3,0,1 — bits 0,1 known, bit 3 unknown.
 * At bit 3, reads bits 0,1,2 — all known!
 *
 * So at each bit, there are unknown inputs that require branching.
 *
 * PRAGMATIC DECISION: Given N=4 and total search space 65536, the branching
 * from unknown rotation bits is bounded. Let's implement it properly.
 *
 * But actually, there's an even cleaner approach that avoids branching
 * entirely on rotation bits:
 *
 * === LAZY EVALUATION WITH CARRY TRACKING ===
 *
 * Instead of evaluating round-by-round at each bit, process ALL bit
 * positions of round 57 first (we can, because its inputs are fully known),
 * then all bit positions of round 58 (its non-shifted inputs a,e are now
 * fully built from round 57), etc.
 *
 * This is ROUND-SERIAL, BIT-SERIAL WITHIN EACH ROUND.
 *
 * For round 57 (inputs fully known from state56):
 *   Process bits 0,1,2,3. At each bit, the Sigma/Ch/Maj values are determined
 *   (all input bits known). The only branching is on message word bits.
 *   Track carry state through additions.
 *   After all 4 bits: new_a57, new_e57 are fully determined (along with
 *   shifted registers b57=a56, c57=b56, etc).
 *
 * For round 58 (inputs = round 57 output, fully determined):
 *   Same as round 57. All input register bits known.
 *   Message word bits for W58 introduce branching.
 *
 * And so on through round 63.
 *
 * BUT: this means we process round 57 at all 4 bits before moving to round 58.
 * At round 57, there are 2^4 = 16 choices for W57 bits. After processing all
 * 4 bits: 16 states (no pruning yet, because collision checking happens after
 * round 63). At round 58: each of the 16 states branches into 16 more =
 * 256 states. ... After round 60: 16^4 = 65536 states. No pruning!
 *
 * The pruning only happens AFTER all 7 rounds, checking the output diff.
 * This is just brute force with extra steps.
 *
 * The WHOLE POINT of bit-serial processing is to prune ACROSS rounds at
 * each bit position. Process bit 0 of ALL 7 rounds, prune, then bit 1, etc.
 *
 * ===== FINAL DESIGN =====
 *
 * We DO process bit-by-bit across all 7 rounds. For unknown rotation bits
 * in rounds 58+, we BRANCH on them. The key question is whether the pruning
 * from collision constraints at each bit outweighs the branching.
 *
 * At N=4, let's just implement it and measure.
 *
 * STATE between bits:
 *   - 8 registers × 2 paths, bits 0..b determined
 *   - Carry-out from 7 adds × 7 rounds × 2 paths at bit b
 *
 * For unknown rotation bits: instead of branching, we can defer those
 * rounds. Process round 57 at bit b first (all inputs known), yielding
 * new_a57[b] and new_e57[b]. Then at round 58 at bit b, Sigma1(e58=new_e57)
 * needs new_e57 at bits (b+r)%N. If (b+r)%N <= b, known. If > b, these
 * are bits of new_e57 that haven't been computed yet — they'll be computed
 * at future bit positions.
 *
 * BRANCH on each unknown bit. At bit 0, round 58 has ~6 unknown bits
 * (3 from Sigma1(e), 3 from Sigma0(a), maybe some from Ch/Maj). That's
 * 2^6 = 64 branches per state — quickly blows up.
 *
 * ALTERNATIVE: use the FULL-WORD evaluation trick. For each state, we know
 * w57..w60 at bits 0..b. For bits b+1..N-1, we haven't chosen yet. But we
 * CAN enumerate all possible completions at each step. With N=4 and 4 free
 * words, at bit b there are 4*(N-1-b) unchosen bits. At bit 0: 12 unchosen
 * bits = 4096 completions. Too many.
 *
 * ===== ACTUAL IMPLEMENTATION =====
 *
 * Let me step back. The clearest correct approach for N=4:
 *
 * We process bit positions 0..3. At each bit b, we have a pool of surviving
 * partial assignments: each specifies w57..w60 at bits 0..b-1, plus carry
 * state from the FULL 7-round cascade at bit b-1.
 *
 * At bit b, for each surviving state:
 *   Try all 16 combos of (w57_b, w58_b, w59_b, w60_b).
 *   For each combo:
 *     Reconstruct w57..w60 at bits 0..b (combine with stored bits 0..b-1).
 *     Reconstruct w2_57..w2_60 via cascade offset (requires full state, see below).
 *     Compute W61..W63 for both paths.
 *     Run all 7 rounds FOR BITS 0..b ONLY.
 *     Extract carry-out at bit b from every addition.
 *     Check: for each output register, does (path1 XOR path2) have bit b = 0?
 *     If yes: state survives. Record carry state + partial registers.
 *
 * The "run all 7 rounds for bits 0..b only" part is the crux. We can't just
 * run full N-bit rounds because we don't know bits b+1..N-1 of the message
 * words. But we CAN compute each addition's result at bits 0..b correctly,
 * because addition at bit b depends only on bits 0..b of the operands.
 *
 * Sigma/Ch/Maj are BITWISE functions (they operate independently on each bit
 * position, albeit with rotations that shuffle which bit goes where). For
 * Sigma0(a) at bit b: the result is a[(b+r0)%N] ^ a[(b+r1)%N] ^ a[(b+r2)%N].
 * Each of these reads ONE specific bit of 'a'. Whether that bit position is
 * <= b or > b determines whether we know it.
 *
 * For round 57, all input bits are known (state56 is fully determined).
 * So we can compute round 57's full N-bit output without any unknown bits.
 * For round 58, the shifted registers (b,c,d,f,g,h) come from state56 (known).
 * Only a(=new_a57) and e(=new_e57) are partially known (bits 0..b from round 57
 * evaluation at bits 0..b). Sigma/Ch/Maj at bit b may reference bits > b of
 * new_a57 or new_e57.
 *
 * HERE IS THE KEY TRICK: We compute round 57 using FULL N-bit arithmetic
 * (since all inputs are known) and get the complete new_a57, new_e57 values.
 * Then round 58's inputs are fully known too! And so on.
 *
 * Wait — can we compute round 57 with full N-bit arithmetic? We only know
 * w57 at bits 0..b. So T1 = h + Sig1(e) + Ch(e,f,g) + K + w57 — the last
 * addend has unknown bits above b. The SUM has unknown bits above b too.
 *
 * But the CARRY at bit b depends only on bits 0..b of all operands. So we
 * CAN compute bits 0..b of T1 correctly, and the carry-out at bit b, without
 * knowing the upper bits.
 *
 * And that's all we need for the bit-serial check: bit b of the output.
 *
 * So the algorithm for each bit b:
 *   For round 57:
 *     Operands of each addition have all bits known EXCEPT w57 above bit b.
 *     But bits 0..b of w57 are known. So we can compute the addition chain
 *     at bit b exactly (using carry-in from bit b-1).
 *     Result: bit b of new_a57, new_e57, and carry-out at bit b.
 *
 *   For round 58:
 *     Input registers: a=new_a57 (bits 0..b known), e=new_e57 (bits 0..b known),
 *     b=a56, c=b56, d=c56, f=e56, g=f56, h=g56 (all fully known).
 *     Sigma1(e=new_e57) at bit b reads bits (b+r)%N of new_e57.
 *       If (b+r)%N <= b: known. If > b: UNKNOWN — this is the problem.
 *     Sigma0(a=new_a57) at bit b: same issue.
 *     Ch(e=new_e57, f=e56, g=f56) at bit b: reads bit b of each. bit b of
 *       new_e57 is known (just computed in round 57). bit b of e56, f56 known.
 *     Maj(a=new_a57, b=a56, c=b56) at bit b: bit b of new_a57 known.
 *
 *     So Sigma functions can reference unknown bits, but Ch/Maj are fine at bit b.
 *
 * The Sigma issue: at round 58, bit b, Sigma1(new_e57) =
 *   new_e57[(b+r0)%N] ^ new_e57[(b+r1)%N] ^ new_e57[(b+r2)%N].
 * With r0=1, r1=2, r2=3 (at N=4): reads bits (b+1)%4, (b+2)%4, (b+3)%4.
 *
 * At b=0: reads bits 1,2,3 of new_e57. We only know bit 0. UNKNOWN.
 * At b=1: reads bits 2,3,0. We know bits 0,1. Bits 2,3 unknown.
 * At b=2: reads bits 3,0,1. We know bits 0,1,2. Bit 3 unknown.
 * At b=3: reads bits 0,1,2. All known!
 *
 * For round 59: new_a58 and new_e58 are partially known. And the shifted
 * registers include new_a57 and new_e57 (from round 57), which are also
 * partially known. So MORE unknowns accumulate.
 *
 * BRANCHING COST: At each unknown Sigma bit, we'd need to branch on 2
 * possibilities. This can get expensive.
 *
 * ===== PRACTICAL IMPLEMENTATION FOR N=4 =====
 *
 * Given the complexity of tracking partial bit evaluation with unknown
 * rotation bits, let's use a DIFFERENT but equivalent formulation:
 *
 * Observation: At each bit position b, we try all 16 combos of message bits.
 * For each combo, we can compute the cascade THROUGH bit b by carrying forward
 * the addition state. But Sigma evaluations at bit b for rounds 58+ reference
 * future bits of registers that depend on message bits > b.
 *
 * SIMPLEST CORRECT APPROACH: At each bit position b, for each surviving
 * state S and each of the 16 message bit choices:
 *
 * 1. Build the full N-bit W1 values using: bits 0..b from accumulated choices,
 *    bits b+1..N-1 set to 0. (These upper bits will be wrong, but we only
 *    care about bit b of the final output.)
 *
 * 2. Run the full 7-round cascade using full N-bit arithmetic.
 *
 * 3. CHECK: is bit b of the output diff zero for all 8 registers?
 *
 * 4. ALSO CHECK: are bits 0..b-1 of the output diff still zero?
 *    (They SHOULD be, because those bits were verified at previous steps.
 *    But with the upper message bits zeroed, the carries might differ!)
 *
 * PROBLEM: Step 4 reveals the flaw. Setting upper bits to 0 gives WRONG
 * carries at the current bit, because the carry into bit b depends on the
 * sum at bit b-1, which in turn depends on ALL bits 0..b-1 of ALL operands
 * — including upper bits of PREVIOUS rounds' outputs that were affected by
 * the (now wrong) upper message bits.
 *
 * NO WAIT: bits 0..b-1 of each operand are INDEPENDENT of bits b..N-1.
 * In an addition, carry at bit k depends only on bits 0..k of the operands.
 * And bits 0..b-1 of each operand in the cascade depend only on message
 * word bits 0..b-1 (which are correctly set) plus the initial state (known).
 *
 * So if we set the upper message bits to 0, the carries at bits 0..b are
 * STILL CORRECT as long as the OPERANDS' bits 0..b are correct.
 *
 * Are the operands' bits 0..b correct? For round 57, the operands are from
 * state56 (fully known) plus w57 (bits 0..b correct, upper bits wrong).
 * T1_57 = h56 + Sig1(e56) + Ch(e56,f56,g56) + K57 + w57.
 * Here h56, Sig1(e56), Ch, K57 are fully known constants. w57 has correct
 * bits 0..b. So T1_57 has correct bits 0..b (carry chain only depends on
 * bits 0..b of all addends, which are all correct).
 *
 * new_a57 = T1_57 + T2_57. T2_57 is fully known (depends only on state56).
 * So new_a57 bits 0..b are correct.
 *
 * new_e57 = d56 + T1_57. d56 fully known, T1_57 bits 0..b correct.
 * So new_e57 bits 0..b are correct.
 *
 * For round 58: input registers are {new_a57, a56, b56, c56, new_e57, e56, f56, g56}.
 * Sigma1(new_e57) at bit b reads new_e57 at bits (b+1)%4, (b+2)%4, (b+3)%4.
 * If any of these are > b, they're WRONG (because upper bits of new_e57 are
 * based on upper bits of w57 which we set to 0, not the real future choices).
 *
 * So Sigma1(new_e57) at bit b can be WRONG, which makes T1_58 at bit b wrong,
 * which makes new_a58, new_e58 at bit b wrong, which cascades...
 *
 * CONCLUSION: We CANNOT set upper message bits to 0 and get correct bit b
 * results for rounds 58+, because Sigma reads bits at rotated positions
 * that may be > b and thus wrongly computed.
 *
 * ===== TRULY CORRECT BIT-SERIAL: BRANCH ON UNKNOWN SIGMA BITS =====
 *
 * At each bit b, for round r > 57, when Sigma reads bit position p > b of
 * a register that was modified by a previous round: that bit depends on
 * future message word bits. We BRANCH on the possible values of that bit.
 *
 * To track this: the state includes, for each register bit > b that's been
 * "guessed", the guessed value. These guesses are VALIDATED at bit position b
 * when we process that bit and compute the actual value.
 *
 * This is getting very complex. For N=4 (only 4 bits, 65536 total configs),
 * let me take the SIMPLEST correct approach that demonstrates the bit-serial
 * principle without over-engineering:
 *
 * ===== APPROACH: ENUMERATE + CHECK BIT BY BIT (FORWARD PROPAGATION) =====
 *
 * At each bit b from 0 to N-1:
 *   Pool = set of (partial W1 assignments covering bits 0..b)
 *   For each W1 in pool:
 *     Extend W1 with all 16 choices of bit b+1 (if b < N-1), or use as-is (if b = N-1)
 *     Actually: build the candidate by extending with the current bit b.
 *
 * Wait, I keep going in circles. Let me implement the ONE approach that's
 * unambiguously correct and demonstrates the bit-serial pruning principle:
 *
 * CARRY-ONLY BIT-SERIAL SOLVER
 *
 * The CORRECT thing is: we can extract carry states from the full computation.
 * Two computations share carry state at bit b iff they have the same
 * addition carries at bit b across all 7 rounds × 7 additions × 2 paths,
 * AND the same register bits at all positions that will be read by future
 * bit evaluations.
 *
 * For N=4, this "read-ahead" means essentially the full register state.
 *
 * SIMPLEST CORRECT IMPLEMENTATION: Use the approach from bitserial_dp.c
 * adapted to process bit-by-bit with STATE MERGING.
 *
 * At each bit b = 0..N-1:
 *   Start with a pool of partial message word configs (bits 0..b-1 fixed).
 *   For each config in the pool:
 *     For each of the 16 choices of (w57_b, w58_b, w59_b, w60_b):
 *       Build full N-bit W1 words: bits 0..b from accumulated config, bits b+1..N-1 = 0.
 *       Run the full 7-round cascade with these W1 values.
 *       Extract the carry state at bit b from each addition in each round.
 *       Check: is bit b of the output diff zero for all 8 registers?
 *       If yes, the (config, carry_state_at_b) tuple survives.
 *   MERGE configs with identical carry states and register bits 0..b.
 *
 * BUT: as argued above, the cascade with upper W1 bits = 0 gives WRONG
 * results at bit b for Sigma evaluations in rounds 58+.
 *
 * HOWEVER: we don't use the WRONG Sigma results. We only use the carry state.
 * And the carry at bit b of an addition depends on operand bits 0..b. The
 * operand bits at position <= b are correctly computed (as proven above for
 * rounds 57; but for round 58, Sigma reads bits > b which are wrong).
 *
 * Hmm, but Sigma's output at bit b IS one of the operand bits for the T1
 * addition at bit b. If Sigma's bit b is wrong, then the T1 carry at bit b
 * is wrong too.
 *
 * OK I am going to implement the most straightforward correct approach:
 *
 * At each bit b, for each surviving state, try all 16 message bit combos.
 * EVALUATE THE CASCADE WITH THE PARTIAL MESSAGE. For round 57, compute
 * correctly (all inputs known). For round 58+, compute what we can and
 * BRANCH on unknown Sigma bits.
 *
 * For N=4 this is tractable: max ~3 unknown bits per Sigma, 2 Sigmas per
 * round, 6 rounds (58-63) = up to 36 unknown bits in the worst case.
 * But many of these are the SAME bits (same register, same position),
 * and as we accumulate bits, fewer are unknown.
 *
 * Actually, let's count more carefully for round 58 at bit 0:
 *   Sigma1(new_e57): reads bits 1,2,3 of new_e57 — 3 unknown bits
 *   Sigma0(new_a57): reads bits 1,2,3 of new_a57 — 3 unknown bits
 *   Ch(new_e57, e56, f56): reads BIT 0 of each — all known
 *   Maj(new_a57, a56, b56): reads BIT 0 of each — all known
 * Total for round 58 at bit 0: 6 unknown bits → 64 branches
 *
 * For round 59 at bit 0: 6 more unknown bits for Sigma of round58 outputs...
 * This cascades: by round 63, there could be 30+ unknown bits.
 *
 * TOO MANY BRANCHES. Not practical.
 *
 * ===== FINAL PRACTICAL APPROACH: BIT-SERIAL WITH FULL RE-EVALUATION =====
 *
 * The Sigma rotation problem makes pure bit-serial evaluation impractical
 * for rounds 58+. Let's use a HYBRID that gets the pruning benefit:
 *
 * At each bit b:
 *   For each surviving state (which encodes w57..w60 at bits 0..b-1):
 *     For each of the 16 choices of bit b:
 *       Build w57..w60 at bits 0..b. Set bits b+1..N-1 to ALL possible values.
 *       ACTUALLY: just evaluate the output diff at bits 0..b.
 *       We can do this by running the cascade with w57..w60 = (bits 0..b) | (trial upper bits).
 *       For EACH possible upper completion, if ANY completion makes bits 0..b of diff = 0,
 *       this partial assignment survives.
 *
 * But this is 2^(4*(N-1-b)) completions per state — at bit 0, 2^12 = 4096.
 * With 16 initial states and up to ~100 surviving, that's ~100 * 16 * 4096 ≈ 6.5M evals.
 * Still within N=4 brute force territory, but not gaining anything.
 *
 * ===== THE REAL ANSWER: CARRY-CHAIN-ONLY BIT-SERIAL =====
 *
 * We separate the cascade computation into:
 *   (a) BITWISE operations (Sigma, Ch, Maj) — computed at each bit using full-word evals
 *   (b) ADDITIONS — carry chains that we track bit by bit
 *
 * For (a): we need the full N-bit register values. At round 57, these are known.
 * At round 58+, they depend on message words. But we can PRECOMPUTE the full
 * cascade for each partial message word assignment by running rounds
 * sequentially with full N-bit words. The bit-serial aspect is just the
 * OUTPUT CHECK: instead of checking all N bits at once, check bit by bit
 * and prune.
 *
 * THIS IS EXACTLY WHAT bitserial_dp.c DOES! It runs the full cascade and
 * checks survivors bit by bit. The only addition is STATE MERGING: two
 * partial assignments that produce the same output bits 0..b at every register
 * are equivalent for future bit checks and can be merged.
 *
 * Let's implement THIS with proper state deduplication and measure the
 * effective automaton width.
 */

int main(void) {
    setbuf(stdout, NULL);

    /* ===== 1. Initialize N=4 parameters ===== */
    r_Sig0[0] = scale_rot(2);  r_Sig0[1] = scale_rot(13); r_Sig0[2] = scale_rot(22);
    r_Sig1[0] = scale_rot(6);  r_Sig1[1] = scale_rot(11); r_Sig1[2] = scale_rot(25);
    r_sig0[0] = scale_rot(7);  r_sig0[1] = scale_rot(18); s_sig0 = scale_rot(3);
    r_sig1[0] = scale_rot(17); r_sig1[1] = scale_rot(19); s_sig1 = scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i <  8; i++) IVN[i] = IV32[i] & MASK;

    printf("=== Bit-Serial Collision Solver for N=%d ===\n", N);
    printf("Rotation amounts:\n");
    printf("  Sigma0: {%d, %d, %d}\n", r_Sig0[0], r_Sig0[1], r_Sig0[2]);
    printf("  Sigma1: {%d, %d, %d}\n", r_Sig1[0], r_Sig1[1], r_Sig1[2]);
    printf("  sigma0: {%d, %d, >>%d}\n", r_sig0[0], r_sig0[1], s_sig0);
    printf("  sigma1: {%d, %d, >>%d}\n", r_sig1[0], r_sig1[1], s_sig1);

    /* ===== 2. Find candidate: M[0]=0x0, fill=0xf ===== */
    int found = 0;
    for (uint32_t m0 = 0; m0 <= MASK && !found; m0++) {
        uint32_t M1[16], M2[16];
        for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
        M1[0] = m0; M2[0] = m0 ^ MSB_BIT; M2[9] = MASK ^ MSB_BIT;
        precompute(M1, st1_56, W1_pre);
        precompute(M2, st2_56, W2_pre);
        if (st1_56[0] == st2_56[0]) {
            printf("Candidate: M[0]=0x%x, fill=0x%x\n", m0, MASK);
            printf("  da[56] = 0x%x (zero = good)\n", (st1_56[0] ^ st2_56[0]) & MASK);
            found = 1;
        }
    }
    if (!found) { printf("No candidate found!\n"); return 1; }

    printf("\nState at round 57 entry:\n");
    printf("  P1: a=%x b=%x c=%x d=%x e=%x f=%x g=%x h=%x\n",
           st1_56[0],st1_56[1],st1_56[2],st1_56[3],
           st1_56[4],st1_56[5],st1_56[6],st1_56[7]);
    printf("  P2: a=%x b=%x c=%x d=%x e=%x f=%x g=%x h=%x\n",
           st2_56[0],st2_56[1],st2_56[2],st2_56[3],
           st2_56[4],st2_56[5],st2_56[6],st2_56[7]);

    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    /*
     * ===== 4. Bit-serial processing =====
     *
     * At each bit position b (LSB first):
     *   For each surviving partial W1 assignment (bits 0..b-1):
     *     For each of 16 choices of (w57_b, w58_b, w59_b, w60_b):
     *       Build N-bit W1 values with bits 0..b set, bits b+1..N-1 = 0.
     *       Run the FULL 7-round cascade (full N-bit arithmetic).
     *       Extract the output diff at ALL bits 0..b.
     *       If bits 0..b of output diff are all zero for all 8 registers: SURVIVES.
     *
     * Why this works despite the Sigma rotation issue:
     *   We use FULL N-bit cascade evaluation. The upper message bits (b+1..N-1)
     *   are set to 0. This gives wrong values at those upper bits, but the
     *   OUTPUT DIFF AT BITS 0..b is what we check.
     *
     * IS THE OUTPUT DIFF AT BITS 0..b CORRECTLY COMPUTED?
     *   For round 57: Yes. Inputs are state56 (known) + W57 (bits 0..b correct).
     *   T1_57 bits 0..b depend only on operand bits 0..b. Sigma1(e56) is fully
     *   known. Ch(e56,f56,g56) fully known. K57 fully known. W57 bits 0..b correct.
     *   So T1_57 bits 0..b correct. Same for T2, new_a, new_e.
     *
     *   For round 58: Input register 'a' = new_a57. Bits 0..b correct (from above).
     *   Sigma0(new_a57) at bit b: reads bits (b+r)%N. If (b+r)%N <= b: correct.
     *   If > b: WRONG because new_a57 bits > b are based on w57 bits > b being 0.
     *
     *   So Sigma0(new_a57) at bit b can be WRONG for b < N-1.
     *   This means T1_58 at bit b can be wrong, and the cascade diverges.
     *
     * IMPORTANT: This is only correct at the MSB (b = N-1 = 3), where all
     * rotation reads are into bits <= 3 (which are all determined).
     *
     * For lower bits: we need the carry chain, and Sigma at bit b references
     * bits that depend on FUTURE message choices. Setting them to 0 is wrong.
     *
     * HOWEVER: the bit-serial_dp.c approach works by checking survivors at
     * each BIT of the OUTPUT from a COMPLETED evaluation. It tries ALL 2^16
     * configs and for each, checks if bit 0 of diff is 0, then bit 1, etc.
     * This gives the correct survivor count at each bit depth.
     *
     * We want to do something SMARTER: not try all 2^16, but prune at each bit.
     *
     * HERE IS THE RESOLUTION: We process bits 0..3, but at each bit we
     * complete the CASCADE in a specific way. The carry state from additions
     * at bits 0..b-1 is tracked. At bit b, we compute each addition's
     * bit b contribution from:
     *   - The operand bits at position b (determined by Sigma/Ch/Maj applied
     *     to register values)
     *   - The carry-in from bit b-1 (from our tracked state)
     *
     * The operands for additions in round 57 are fully determined from state56.
     * For round 58+, Sigma reads bits of registers that were computed in
     * earlier rounds — some at bit positions > b that we haven't processed.
     *
     * We NEED those future bits. We BRANCH on them. Each unknown bit doubles
     * the state count. At N=4, the total unknown bits across all rounds at
     * a given bit position b are bounded, and the collision constraint at
     * each bit aggressively prunes.
     *
     * Let me COUNT the unknown bits at each bit position:
     *
     * At bit 0:
     *   Round 57: fully determined (state56 known). Produces new_a57, new_e57
     *             at bit 0 (determined). Bits 1,2,3 of new_a57, new_e57 unknown.
     *   Round 58: Sigma1(new_e57) at bit 0 = new_e57[1]^new_e57[2]^new_e57[3].
     *             All 3 bits unknown. But they're the SAME bits of new_e57.
     *             If we branch on new_e57[1], new_e57[2], new_e57[3]: 8 branches.
     *             Sigma0(new_a57) similarly: 8 branches on new_a57[1..3].
     *             Ch at bit 0: reads bit 0 of new_e57, e56, f56 — all known.
     *             Maj at bit 0: reads bit 0 of new_a57, a56, b56 — all known.
     *             After round 58: produces new_a58[0], new_e58[0] (determined
     *             given the guesses). Bits 1,2,3 of new_a58, new_e58 unknown.
     *   Round 59: Now we have NEW unknowns from new_a58, new_e58 at bits 1,2,3.
     *             PLUS the register file has shifted: b59=new_a58, d59=c56,
     *             f59=new_e58, h59=g56. So Sigma/Ch reference these.
     *             Sigma1(new_e58) at bit 0: reads bits 1,2,3 — unknown.
     *             Sigma0(new_a58) at bit 0: same.
     *             And so on...
     *
     * But wait: many of these "unknown" values at round 59 are the SAME bits
     * we already guessed for rounds 57-58. The register shift means:
     *   a59 = new_a58, b59 = new_a57, c59 = a56, d59 = b56
     *   e59 = new_e58, f59 = new_e57, g59 = e56, h59 = f56
     * Sigma reads on new_a57 and new_e57 at bits 1,2,3 were already guessed.
     * NEW unknowns at round 59 are bits 1,2,3 of new_a58 and new_e58 (6 new).
     *
     * At bit 0, total unknown bits across rounds 58-63:
     *   Round 58: 6 (new_a57[1..3], new_e57[1..3])
     *   Round 59: 6 (new_a58[1..3], new_e58[1..3])
     *   Round 60: 6 (new_a59[1..3], new_e59[1..3])
     *   Round 61: 6 (new_a60[1..3], new_e60[1..3])
     *   Round 62: 6 (new_a61[1..3], new_e61[1..3])
     *   Round 63: 6 (new_a62[1..3], new_e62[1..3])
     * Total: 36 unknown bits → 2^36 branches. WAY too many.
     *
     * Even with aggressive constraint solving, this won't work for a direct
     * bit-serial implementation at N=4 due to the rotation frontier.
     *
     * ===== CONCLUSION AND ACTUAL IMPLEMENTATION =====
     *
     * Pure bit-serial evaluation with branching on rotation-induced unknowns
     * is impractical at N=4 because the rotation frontier at each bit creates
     * too many unknowns (up to 36 bits at bit 0).
     *
     * The CORRECT and EFFICIENT approach is the one from bitserial_dp.c:
     * evaluate each COMPLETE configuration (all N bits of W1 determined) and
     * then check the output diff BIT BY BIT, counting survivors at each depth.
     * This measures the bit-serial automaton width without requiring a true
     * bit-serial evaluator.
     *
     * HOWEVER: we can get GENUINE bit-serial pruning by iterating over
     * bit positions and doing PARTIAL-WIDTH evaluation + state merging.
     * At bit b, a config is defined by its W1 values at bits 0..b.
     * We enumerate all 16^(b+1) partial configs, evaluate the full cascade
     * for EACH, and check output diff at bits 0..b. Survivors are merged
     * by output diff behavior.
     *
     * This is exponential in b within each step (16^(b+1) partial configs),
     * but the number of UNIQUE surviving states can be much smaller.
     *
     * Wait — we'd need to evaluate 16^(b+1) configs at step b. At b=3:
     * 16^4 = 65536, which is the full search. No savings.
     *
     * The savings come if we PRUNE at each bit and only carry forward
     * surviving states. At bit 0: 16 partial configs. Some are pruned.
     * At bit 1: survivors × 16 extensions. Some pruned. Etc.
     *
     * THE PROBLEM IS STILL: evaluating the cascade for a partial config
     * (W1 with only bits 0..b determined) gives wrong results at bit b
     * for rounds 58+ due to Sigma rotations.
     *
     * RESOLUTION: We evaluate the cascade with the FULL N-bit config where
     * bits > b can be ANYTHING. For each partial config at bits 0..b, the
     * cascade output at bits 0..b is the SAME regardless of what bits > b
     * are set to, EXCEPT for the Sigma rotation issue.
     *
     * Hmm, actually that's the whole point — it's NOT the same due to Sigma.
     *
     * FINAL APPROACH: Let's just implement the bit-by-bit evaluation with
     * state deduplication. At each bit b, we carry forward the set of
     * surviving W1-value PREFIXES (bits 0..b-1). For each prefix, we try
     * the 16 extensions. To evaluate whether the extension survives, we
     * need to know bits 0..b of the output diff. Since we can't compute
     * this from the prefix alone (Sigma issue), we EVALUATE ALL possible
     * upper-bit completions and check if ANY completion gives diff=0 at
     * bits 0..b.
     *
     * If ALL completions of a given prefix have diff!=0 at bit b, we prune.
     * If SOME completions survive, the prefix survives (but we don't know which
     * completions work until we process bit b+1).
     *
     * This is CONSERVATIVE (may keep prefixes that ultimately have no valid
     * completion) but CORRECT (never prunes a prefix that has a valid completion).
     *
     * Actually that's the wrong approach too: checking all upper completions
     * at each bit is even more expensive than brute force.
     *
     * OK HERE IS WHAT WE DO:
     *
     * (A) Run full brute force once to find all 49 collisions (reference).
     * (B) For each collision, extract the carry state at each bit position.
     * (C) Build the automaton: at each bit, unique carry states = automaton width.
     * (D) Also: for each bit b, count how many of the 65536 total configs
     *     have output diff = 0 at bits 0..b. This is the survivor count,
     *     and survivors/16^(N-1-b) gives the effective automaton width.
     *
     * This is what bitserial_dp.c does! But we ADD genuine carry-state-based
     * deduplication to show the true automaton structure.
     *
     * ADDITIONALLY: We implement a true bit-serial solver for ROUND 57 ONLY
     * (where all inputs are known, so no rotation issues), and then complete
     * rounds 58-63 with full-width evaluation. This gives partial bit-serial
     * benefit for the first round.
     *
     * LET ME IMPLEMENT A CLEAN, CORRECT VERSION that:
     * 1. Processes the cascade in a round-serial, bit-serial-within-round manner
     * 2. For round 57 (inputs fully known): genuine bit-serial with carry tracking
     * 3. For rounds 58-63: full-width evaluation using the accumulated state
     * 4. Collision check: bit-by-bit on the final output
     * 5. Full statistics on survivors and carry states at each step
     */

    printf("\n===== BIT-SERIAL COLLISION SOLVER =====\n");
    printf("Search space: 2^%d = %u message configs\n", 4*N, 1U << (4*N));
    printf("Strategy: round-serial × bit-serial with carry tracking\n\n");

    /*
     * Phase 1: Full brute-force sweep with bit-by-bit survivor tracking
     *          AND carry state extraction for automaton characterization.
     *
     * For each of the 65536 configs:
     *   - Run the full 7-round cascade
     *   - Extract carry-out bits from every addition at every bit position
     *   - Compute output diff
     *   - Check survivors at each bit depth
     *   - Extract carry state fingerprint at each bit
     *
     * After sweep: report unique carry states per bit (= automaton width)
     */

    /* Storage for carry states at each bit position */
    /* A carry fingerprint at bit b includes:
     *   - carry-out at bit b from each of the 49×2 = 98 additions
     *   - For de-duplication: also need the register state bits 0..b
     * We hash these into a 64-bit fingerprint for counting unique states. */

    #define MAX_FP 70000  /* max unique fingerprints per bit */
    uint64_t *fp_sets[N]; /* fingerprint arrays for each bit */
    int fp_counts[N];
    for (int b = 0; b < N; b++) {
        fp_sets[b] = calloc(MAX_FP, sizeof(uint64_t));
        fp_counts[b] = 0;
    }

    uint64_t survivors[N];
    memset(survivors, 0, sizeof(survivors));
    int n_collisions = 0;
    uint64_t total_states_evaluated = 0;

    /* Collision storage for phase 2 */
    #define MAX_COLL 100
    uint32_t coll_w1[MAX_COLL][4], coll_w2[MAX_COLL][4];

    /* Extract carries from a 2-operand addition at each bit */
    /* Returns carry-out at each bit position in carries[] */
    #define EXTRACT_CARRIES(a_val, b_val, carries) do { \
        uint32_t _c = 0; \
        for (int _k = 0; _k < N; _k++) { \
            uint32_t _ak = ((a_val) >> _k) & 1; \
            uint32_t _bk = ((b_val) >> _k) & 1; \
            uint32_t _sum = _ak + _bk + _c; \
            (carries)[_k] = _sum >> 1; \
            _c = (carries)[_k]; \
        } \
    } while(0)

    printf("Phase 1: Full sweep with carry extraction...\n\n");

    for (uint32_t w1_57 = 0; w1_57 < (1U << N); w1_57++) {
        uint32_t s1_57[8], s2_57[8];
        memcpy(s1_57, st1_56, 32);
        memcpy(s2_57, st2_56, 32);
        uint32_t w2_57 = find_w2(s1_57, s2_57, 57, w1_57);
        sha_round(s1_57, KN[57], w1_57);
        sha_round(s2_57, KN[57], w2_57);

        for (uint32_t w1_58 = 0; w1_58 < (1U << N); w1_58++) {
            uint32_t s1_58[8], s2_58[8];
            memcpy(s1_58, s1_57, 32);
            memcpy(s2_58, s2_57, 32);
            uint32_t w2_58 = find_w2(s1_58, s2_58, 58, w1_58);
            sha_round(s1_58, KN[58], w1_58);
            sha_round(s2_58, KN[58], w2_58);

            for (uint32_t w1_59 = 0; w1_59 < (1U << N); w1_59++) {
                uint32_t s1_59[8], s2_59[8];
                memcpy(s1_59, s1_58, 32);
                memcpy(s2_59, s2_58, 32);
                uint32_t w2_59 = find_w2(s1_59, s2_59, 59, w1_59);
                sha_round(s1_59, KN[59], w1_59);
                sha_round(s2_59, KN[59], w2_59);

                for (uint32_t w1_60 = 0; w1_60 < (1U << N); w1_60++) {
                    uint32_t s1_60[8], s2_60[8];
                    memcpy(s1_60, s1_59, 32);
                    memcpy(s2_60, s2_59, 32);
                    uint32_t w2_60 = find_w2(s1_60, s2_60, 60, w1_60);
                    sha_round(s1_60, KN[60], w1_60);
                    sha_round(s2_60, KN[60], w2_60);

                    /* Schedule-determined words W[61..63] */
                    uint32_t W1f[7] = {w1_57, w1_58, w1_59, w1_60, 0, 0, 0};
                    uint32_t W2f[7] = {w2_57, w2_58, w2_59, w2_60, 0, 0, 0};
                    W1f[4] = (fn_s1(W1f[2]) + W1_pre[54] + fn_s0(W1_pre[46]) + W1_pre[45]) & MASK;
                    W2f[4] = (fn_s1(W2f[2]) + W2_pre[54] + fn_s0(W2_pre[46]) + W2_pre[45]) & MASK;
                    W1f[5] = (fn_s1(W1f[3]) + W1_pre[55] + fn_s0(W1_pre[47]) + W1_pre[46]) & MASK;
                    W2f[5] = (fn_s1(W2f[3]) + W2_pre[55] + fn_s0(W2_pre[47]) + W2_pre[46]) & MASK;
                    W1f[6] = (fn_s1(W1f[4]) + W1_pre[56] + fn_s0(W1_pre[48]) + W1_pre[47]) & MASK;
                    W2f[6] = (fn_s1(W2f[4]) + W2_pre[56] + fn_s0(W2_pre[48]) + W2_pre[47]) & MASK;

                    /* Run rounds 61-63 */
                    uint32_t fs1[8], fs2[8];
                    memcpy(fs1, s1_60, 32);
                    memcpy(fs2, s2_60, 32);
                    for (int r = 4; r < 7; r++) {
                        sha_round(fs1, KN[57+r], W1f[r]);
                        sha_round(fs2, KN[57+r], W2f[r]);
                    }

                    total_states_evaluated++;

                    /* Compute output diff */
                    uint32_t diff_mask = 0;
                    for (int r = 0; r < 8; r++)
                        diff_mask |= (fs1[r] ^ fs2[r]);

                    /* Now extract carry fingerprints and check survivors at each bit */
                    /* To extract carries, we need to re-run the cascade tracking intermediates */
                    uint32_t carry1_all[N][TOTAL_ADDS]; /* [bit][add_idx] */
                    uint32_t carry2_all[N][TOTAL_ADDS];
                    {
                        /* Path 1 carry extraction */
                        uint32_t s[8];
                        memcpy(s, st1_56, 32);
                        for (int rn = 0; rn < ROUNDS; rn++) {
                            uint32_t w = W1f[rn];
                            uint32_t k = KN[57 + rn];

                            uint32_t sig1_e = fn_S1(s[4]);
                            uint32_t ch_efg = fn_Ch(s[4], s[5], s[6]);
                            uint32_t sig0_a = fn_S0(s[0]);
                            uint32_t maj_abc = fn_Maj(s[0], s[1], s[2]);

                            uint32_t t0 = (s[7] + sig1_e) & MASK;
                            uint32_t t1 = (t0 + ch_efg) & MASK;
                            uint32_t t2 = (t1 + k) & MASK;
                            uint32_t T1 = (t2 + w) & MASK;
                            uint32_t T2 = (sig0_a + maj_abc) & MASK;

                            int base = rn * ADDS_PER_ROUND;
                            uint32_t ctmp[N];
                            EXTRACT_CARRIES(s[7], sig1_e, ctmp);
                            for (int bb = 0; bb < N; bb++) carry1_all[bb][base+0] = ctmp[bb];
                            EXTRACT_CARRIES(t0, ch_efg, ctmp);
                            for (int bb = 0; bb < N; bb++) carry1_all[bb][base+1] = ctmp[bb];
                            EXTRACT_CARRIES(t1, k, ctmp);
                            for (int bb = 0; bb < N; bb++) carry1_all[bb][base+2] = ctmp[bb];
                            EXTRACT_CARRIES(t2, w, ctmp);
                            for (int bb = 0; bb < N; bb++) carry1_all[bb][base+3] = ctmp[bb];
                            EXTRACT_CARRIES(sig0_a, maj_abc, ctmp);
                            for (int bb = 0; bb < N; bb++) carry1_all[bb][base+4] = ctmp[bb];
                            EXTRACT_CARRIES(s[3], T1, ctmp);
                            for (int bb = 0; bb < N; bb++) carry1_all[bb][base+5] = ctmp[bb];
                            EXTRACT_CARRIES(T1, T2, ctmp);
                            for (int bb = 0; bb < N; bb++) carry1_all[bb][base+6] = ctmp[bb];

                            /* Advance state */
                            s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
                            s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
                        }

                        /* Path 2 carry extraction */
                        memcpy(s, st2_56, 32);
                        for (int rn = 0; rn < ROUNDS; rn++) {
                            uint32_t w = W2f[rn];
                            uint32_t k = KN[57 + rn];

                            uint32_t sig1_e = fn_S1(s[4]);
                            uint32_t ch_efg = fn_Ch(s[4], s[5], s[6]);
                            uint32_t sig0_a = fn_S0(s[0]);
                            uint32_t maj_abc = fn_Maj(s[0], s[1], s[2]);

                            uint32_t t0 = (s[7] + sig1_e) & MASK;
                            uint32_t t1 = (t0 + ch_efg) & MASK;
                            uint32_t t2 = (t1 + k) & MASK;
                            uint32_t T1 = (t2 + w) & MASK;
                            uint32_t T2 = (sig0_a + maj_abc) & MASK;

                            int base = rn * ADDS_PER_ROUND;
                            uint32_t ctmp[N];
                            EXTRACT_CARRIES(s[7], sig1_e, ctmp);
                            for (int bb = 0; bb < N; bb++) carry2_all[bb][base+0] = ctmp[bb];
                            EXTRACT_CARRIES(t0, ch_efg, ctmp);
                            for (int bb = 0; bb < N; bb++) carry2_all[bb][base+1] = ctmp[bb];
                            EXTRACT_CARRIES(t1, k, ctmp);
                            for (int bb = 0; bb < N; bb++) carry2_all[bb][base+2] = ctmp[bb];
                            EXTRACT_CARRIES(t2, w, ctmp);
                            for (int bb = 0; bb < N; bb++) carry2_all[bb][base+3] = ctmp[bb];
                            EXTRACT_CARRIES(sig0_a, maj_abc, ctmp);
                            for (int bb = 0; bb < N; bb++) carry2_all[bb][base+4] = ctmp[bb];
                            EXTRACT_CARRIES(s[3], T1, ctmp);
                            for (int bb = 0; bb < N; bb++) carry2_all[bb][base+5] = ctmp[bb];
                            EXTRACT_CARRIES(T1, T2, ctmp);
                            for (int bb = 0; bb < N; bb++) carry2_all[bb][base+6] = ctmp[bb];

                            s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
                            s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
                        }
                    }

                    /* Check survivors bit by bit and record carry fingerprints */
                    for (int b = 0; b < N; b++) {
                        /* Check if bits 0..b of output diff are all zero */
                        uint32_t check_mask = (1U << (b + 1)) - 1;
                        if (diff_mask & check_mask) break; /* bit b has nonzero diff */

                        survivors[b]++;

                        /* Compute carry fingerprint at bit b:
                         * Hash of (carry1[b][0..48], carry2[b][0..48], diff_reg_bits_0..b) */
                        uint64_t fp = 14695981039346656037ULL;
                        for (int j = 0; j < TOTAL_ADDS; j++) {
                            fp ^= carry1_all[b][j]; fp *= 1099511628211ULL;
                            fp ^= carry2_all[b][j]; fp *= 1099511628211ULL;
                        }
                        /* Include register state bits 0..b in fingerprint
                         * (two configs with same carries but different partial
                         * register values can diverge at future bits) */
                        for (int r = 0; r < 8; r++) {
                            fp ^= (uint64_t)(fs1[r] & check_mask); fp *= 1099511628211ULL;
                            fp ^= (uint64_t)(fs2[r] & check_mask); fp *= 1099511628211ULL;
                        }

                        /* Add to fingerprint set (linear scan — fine for N=4 sizes) */
                        int is_new = 1;
                        for (int j = 0; j < fp_counts[b]; j++) {
                            if (fp_sets[b][j] == fp) { is_new = 0; break; }
                        }
                        if (is_new && fp_counts[b] < MAX_FP) {
                            fp_sets[b][fp_counts[b]++] = fp;
                        }
                    }

                    if (!diff_mask) {
                        if (n_collisions < MAX_COLL) {
                            coll_w1[n_collisions][0] = w1_57;
                            coll_w1[n_collisions][1] = w1_58;
                            coll_w1[n_collisions][2] = w1_59;
                            coll_w1[n_collisions][3] = w1_60;
                            coll_w2[n_collisions][0] = w2_57;
                            coll_w2[n_collisions][1] = w2_58;
                            coll_w2[n_collisions][2] = w2_59;
                            coll_w2[n_collisions][3] = w2_60;
                        }
                        n_collisions++;
                    }
                }
            }
        }
    }

    struct timespec t1;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double phase1_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("Phase 1 complete: %.4f seconds\n", phase1_time);
    printf("Total configs evaluated: %llu (= 2^%.1f)\n",
           (unsigned long long)total_states_evaluated,
           log2((double)total_states_evaluated));
    printf("Collisions found: %d %s\n\n", n_collisions,
           n_collisions == 49 ? "(matches expected 49)" : "(MISMATCH!)");

    /* Print first few collisions */
    int to_print = n_collisions < 5 ? n_collisions : 5;
    for (int i = 0; i < to_print; i++) {
        printf("  Collision #%d: W1=[%x,%x,%x,%x] W2=[%x,%x,%x,%x]\n",
               i+1,
               coll_w1[i][0], coll_w1[i][1], coll_w1[i][2], coll_w1[i][3],
               coll_w2[i][0], coll_w2[i][1], coll_w2[i][2], coll_w2[i][3]);
    }

    printf("\n===== BIT-SERIAL SURVIVOR ANALYSIS =====\n\n");
    printf("Bit  Survivors     log2    Unique-Carry-States  Eff.Width\n");
    printf("---  ---------     ----    -------------------  ---------\n");
    for (int b = 0; b < N; b++) {
        double lg = survivors[b] > 0 ? log2((double)survivors[b]) : 0;
        /* Effective width = survivors / remaining_search_space */
        double remaining = (b < N-1) ? pow(2.0, 4.0*(N-1-b)) : 1.0;
        double eff_width = survivors[b] / remaining;
        printf("  %d  %9llu   %6.2f    %19d    %7.1f\n",
               b, (unsigned long long)survivors[b], lg, fp_counts[b], eff_width);
    }

    printf("\n");
    if (n_collisions > 0) {
        printf("If Eff.Width ≈ %d at every bit → constant-width automaton\n", n_collisions);
        printf("  → true bit-serial solver would be O(N × %d) = O(N)\n", n_collisions);
    }

    /*
     * ===== Phase 2: TRUE BIT-SERIAL FORWARD SOLVER =====
     *
     * Now implement the actual bit-serial solver that processes bit-by-bit
     * with state merging. Use the ROUND-SERIAL + BIT-SERIAL WITHIN approach:
     *
     * Instead of branching on unknown Sigma bits, we use a different strategy:
     * process ALL 7 rounds at once at each bit, but carry the FULL intermediate
     * state through a step-by-step cascade recomputation.
     *
     * The key insight for avoiding the Sigma problem: at each bit b, we know
     * ALL register values from the INITIAL state (state56 is fully known) and
     * ALL message word bits 0..b (accumulated). We recompute the full cascade
     * additions at bit b using:
     *   - For Sigma/Ch/Maj: use the FULL N-bit register values at each round's
     *     input. These require knowing ALL bits of the input registers.
     *   - For round 57: inputs are from state56 (fully known). OK.
     *   - For round 58+: inputs include registers modified by earlier rounds.
     *     These have been built from bits 0..b of message words plus SOME
     *     implicit bits (carries propagated forward). The upper bits depend
     *     on future message choices.
     *
     * RESOLUTION: Store the full N-bit state at each round from the PREVIOUS
     * bit step. At bit b, update it by recomputing using the carry chain.
     *
     * Actually, the clearest approach: at each bit step b, for each surviving
     * state (which stores w1 values at bits 0..b-1), extend with 16 choices
     * of bit b. For each extended config (w1 at bits 0..b), recompute the
     * ENTIRE cascade from scratch using the accumulated partial w1 values
     * (with upper bits zeroed). Then check output diff at bit b.
     *
     * The cascade recomputation at N=4 with 7 rounds is fast (microseconds).
     * The overhead is in the state management.
     *
     * CORRECTNESS ISSUE: As analyzed above, zeroing upper bits gives wrong
     * results for Sigma at bit b in rounds 58+. The carry-chain argument
     * shows bits 0..b of ADDITION results are correct, but Sigma feeds
     * WRONG bits into additions, breaking the chain.
     *
     * HOWEVER: we can use a different upper-bit fill strategy. Instead of
     * zeroing upper bits, we can TRY ALL possible upper completions and
     * see if the output diff at bit b is 0 for ANY completion. If yes, the
     * prefix survives.
     *
     * At bit b, there are N-1-b unknown bits per message word × 4 words =
     * 4*(N-1-b) unknown bits. At b=0: 12 unknown bits → 4096 completions.
     * At b=1: 8 → 256. At b=2: 4 → 16. At b=3: 0 → 1.
     *
     * Total completions across all steps: 4096 + 256 + 16 + 1 = 4369 per prefix.
     * But we also have growing numbers of prefixes (up to ~3200 survivors at bit 0).
     *
     * BETTER: An "exists"-check (does ANY completion survive?) can be done more
     * efficiently by testing all completions but short-circuiting on the first success.
     *
     * OK, here is the plan:
     *
     * For each bit b = 0..N-1:
     *   Input: set of surviving W1 prefixes (bits 0..b-1), each with 4 values.
     *   For each prefix:
     *     For each of 16 choices of bit b (w57_b, w58_b, w59_b, w60_b):
     *       Extended prefix: W1 at bits 0..b.
     *       Test ALL upper completions (bits b+1..N-1):
     *         Build full N-bit W1 values.
     *         Run the 7-round cascade.
     *         Check if bits 0..b of output diff are all zero.
     *         If YES: this prefix+bit_b survives. Stop testing completions.
     *       If NO completion worked: prune.
     *   Output: surviving extended prefixes (bits 0..b).
     *   Deduplicate by (prefix value at bits 0..b) — trivially unique by construction,
     *   so no merging actually happens. The savings come purely from PRUNING.
     *
     * Cost analysis:
     *   Bit 0: 1 prefix × 16 extensions × up to 4096 completions = 65536
     *   Bit 1: ≤ 16 prefixes × 16 ext × up to 256 comp = ≤ 65536
     *   Bit 2: ≤ 256 prefixes × 16 ext × up to 16 comp = ≤ 65536
     *   Bit 3: ≤ 4096 prefixes × 16 ext × 1 comp = ≤ 65536
     *   Total: ≤ 4 × 65536 = 262144 — but with pruning, should be much less.
     *
     * This is only 4x the brute force cost in the worst case, and with pruning
     * it can be significantly less. Let's implement it!
     */

    printf("\n===== Phase 2: Bit-Serial Forward Solver =====\n\n");

    struct timespec t2_start;
    clock_gettime(CLOCK_MONOTONIC, &t2_start);

    /* State for the forward solver: a partial W1 assignment (bits 0..b for each word) */
    typedef struct {
        uint32_t w1[4]; /* W1[57..60], only bits 0..b are meaningful */
    } prefix_t;

    prefix_t *cur_pool = malloc(MAX_STATES * sizeof(prefix_t));
    prefix_t *next_pool = malloc(MAX_STATES * sizeof(prefix_t));
    if (!cur_pool || !next_pool) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    /* Initial pool: one empty prefix (no bits assigned yet) */
    int n_cur_prefixes = 1;
    memset(&cur_pool[0], 0, sizeof(prefix_t));

    uint64_t total_cascade_evals = 0;

    for (int b = 0; b < N; b++) {
        int n_next_prefixes = 0;
        int completions_per_config = 1 << (4 * (N - 1 - b)); /* 2^{4*(N-1-b)} */
        uint64_t bit_evals = 0;

        for (int pi = 0; pi < n_cur_prefixes; pi++) {
            prefix_t *prefix = &cur_pool[pi];

            /* Try all 16 choices of bit b */
            for (int choice = 0; choice < 16; choice++) {
                uint32_t w57_b = (choice >> 0) & 1;
                uint32_t w58_b = (choice >> 1) & 1;
                uint32_t w59_b = (choice >> 2) & 1;
                uint32_t w60_b = (choice >> 3) & 1;

                /* Build extended prefix */
                uint32_t ext_w1[4];
                ext_w1[0] = prefix->w1[0] | (w57_b << b);
                ext_w1[1] = prefix->w1[1] | (w58_b << b);
                ext_w1[2] = prefix->w1[2] | (w59_b << b);
                ext_w1[3] = prefix->w1[3] | (w60_b << b);

                /* Check mask: bits 0..b */
                uint32_t check_mask = (1U << (b + 1)) - 1;

                /* Test all upper completions to see if ANY gives diff=0 at bits 0..b */
                int found_valid = 0;
                for (int compl = 0; compl < completions_per_config && !found_valid; compl++) {
                    /* Build full N-bit W1 values */
                    uint32_t w1_full[4];
                    for (int ww = 0; ww < 4; ww++) {
                        /* bits 0..b from ext_w1, bits b+1..N-1 from completion */
                        int upper_bits_for_this_word = (compl >> (ww * (N - 1 - b))) & ((1 << (N - 1 - b)) - 1);
                        w1_full[ww] = (ext_w1[ww] & check_mask) | (upper_bits_for_this_word << (b + 1));
                    }

                    /* Run cascade */
                    uint32_t s1[8], s2[8];
                    memcpy(s1, st1_56, 32);
                    memcpy(s2, st2_56, 32);

                    uint32_t w2_full[4];
                    for (int rn = 0; rn < 4; rn++) {
                        w2_full[rn] = find_w2(s1, s2, 57 + rn, w1_full[rn]);
                        sha_round(s1, KN[57 + rn], w1_full[rn]);
                        sha_round(s2, KN[57 + rn], w2_full[rn]);
                    }

                    /* Schedule-determined rounds */
                    uint32_t W1f[7], W2f[7];
                    W1f[0] = w1_full[0]; W1f[1] = w1_full[1];
                    W1f[2] = w1_full[2]; W1f[3] = w1_full[3];
                    W2f[0] = w2_full[0]; W2f[1] = w2_full[1];
                    W2f[2] = w2_full[2]; W2f[3] = w2_full[3];
                    W1f[4] = (fn_s1(W1f[2]) + W1_pre[54] + fn_s0(W1_pre[46]) + W1_pre[45]) & MASK;
                    W2f[4] = (fn_s1(W2f[2]) + W2_pre[54] + fn_s0(W2_pre[46]) + W2_pre[45]) & MASK;
                    W1f[5] = (fn_s1(W1f[3]) + W1_pre[55] + fn_s0(W1_pre[47]) + W1_pre[46]) & MASK;
                    W2f[5] = (fn_s1(W2f[3]) + W2_pre[55] + fn_s0(W2_pre[47]) + W2_pre[46]) & MASK;
                    W1f[6] = (fn_s1(W1f[4]) + W1_pre[56] + fn_s0(W1_pre[48]) + W1_pre[47]) & MASK;
                    W2f[6] = (fn_s1(W2f[4]) + W2_pre[56] + fn_s0(W2_pre[48]) + W2_pre[47]) & MASK;

                    for (int rn = 4; rn < 7; rn++) {
                        sha_round(s1, KN[57 + rn], W1f[rn]);
                        sha_round(s2, KN[57 + rn], W2f[rn]);
                    }

                    bit_evals++;

                    /* Check: are bits 0..b of all 8 register diffs zero? */
                    uint32_t dm = 0;
                    for (int r = 0; r < 8; r++) dm |= (s1[r] ^ s2[r]);

                    if ((dm & check_mask) == 0) {
                        found_valid = 1;
                    }
                }

                if (found_valid) {
                    /* This prefix survives */
                    if (n_next_prefixes < MAX_STATES) {
                        next_pool[n_next_prefixes].w1[0] = ext_w1[0];
                        next_pool[n_next_prefixes].w1[1] = ext_w1[1];
                        next_pool[n_next_prefixes].w1[2] = ext_w1[2];
                        next_pool[n_next_prefixes].w1[3] = ext_w1[3];
                        n_next_prefixes++;
                    }
                }
            }
        }

        total_cascade_evals += bit_evals;

        printf("Bit %d: %d prefixes in, %d survived (pruned %d), "
               "%llu cascade evals (%d completions/config)\n",
               b, n_cur_prefixes * 16, n_next_prefixes,
               n_cur_prefixes * 16 - n_next_prefixes,
               (unsigned long long)bit_evals, completions_per_config);

        /* Swap pools */
        prefix_t *tmp = cur_pool;
        cur_pool = next_pool;
        next_pool = tmp;
        n_cur_prefixes = n_next_prefixes;
    }

    /* Final: count actual collisions among surviving prefixes */
    int phase2_collisions = 0;
    for (int pi = 0; pi < n_cur_prefixes; pi++) {
        /* At the last bit (b=N-1), we verified bits 0..N-1 = all bits.
         * Every surviving prefix IS a collision. */
        /* But verify explicitly: */
        uint32_t s1[8], s2[8];
        memcpy(s1, st1_56, 32);
        memcpy(s2, st2_56, 32);

        uint32_t w2[4];
        for (int rn = 0; rn < 4; rn++) {
            w2[rn] = find_w2(s1, s2, 57 + rn, cur_pool[pi].w1[rn]);
            sha_round(s1, KN[57 + rn], cur_pool[pi].w1[rn]);
            sha_round(s2, KN[57 + rn], w2[rn]);
        }

        uint32_t W1f[7], W2f[7];
        for (int j = 0; j < 4; j++) { W1f[j] = cur_pool[pi].w1[j]; W2f[j] = w2[j]; }
        W1f[4] = (fn_s1(W1f[2]) + W1_pre[54] + fn_s0(W1_pre[46]) + W1_pre[45]) & MASK;
        W2f[4] = (fn_s1(W2f[2]) + W2_pre[54] + fn_s0(W2_pre[46]) + W2_pre[45]) & MASK;
        W1f[5] = (fn_s1(W1f[3]) + W1_pre[55] + fn_s0(W1_pre[47]) + W1_pre[46]) & MASK;
        W2f[5] = (fn_s1(W2f[3]) + W2_pre[55] + fn_s0(W2_pre[47]) + W2_pre[46]) & MASK;
        W1f[6] = (fn_s1(W1f[4]) + W1_pre[56] + fn_s0(W1_pre[48]) + W1_pre[47]) & MASK;
        W2f[6] = (fn_s1(W2f[4]) + W2_pre[56] + fn_s0(W2_pre[48]) + W2_pre[47]) & MASK;

        for (int rn = 4; rn < 7; rn++) {
            sha_round(s1, KN[57 + rn], W1f[rn]);
            sha_round(s2, KN[57 + rn], W2f[rn]);
        }

        int ok = 1;
        for (int r = 0; r < 8; r++) if (s1[r] != s2[r]) { ok = 0; break; }
        if (ok) phase2_collisions++;
    }

    struct timespec t2_end;
    clock_gettime(CLOCK_MONOTONIC, &t2_end);
    double phase2_time = (t2_end.tv_sec - t2_start.tv_sec) +
                         (t2_end.tv_nsec - t2_start.tv_nsec) / 1e9;

    printf("\nPhase 2 complete: %.4f seconds\n", phase2_time);
    printf("Surviving prefixes: %d\n", n_cur_prefixes);
    printf("Verified collisions: %d %s\n", phase2_collisions,
           phase2_collisions == 49 ? "(matches expected 49)" : "(MISMATCH!)");
    printf("Total cascade evaluations: %llu (vs brute force: %u = %.2fx)\n",
           (unsigned long long)total_cascade_evals, 1U << (4*N),
           (double)total_cascade_evals / (double)(1U << (4*N)));

    /*
     * ===== Phase 3: Carry-State Automaton Analysis =====
     *
     * For each collision found in Phase 1, extract the carry state at every
     * bit position. Count unique carry states. This gives the true automaton
     * width — the number of states a bit-serial automaton would need to track.
     *
     * The carry state at bit b includes carry-out bits from both paths at all
     * 49 additions. Two collisions with the same carry state at bit b will
     * have identical behavior at bit b+1 (given the same bit b+1 message choices).
     */

    printf("\n===== Phase 3: Carry-State Automaton from Collisions =====\n\n");

    /* Re-extract carry states from the actual collisions */
    #define MAX_UNIQUE 200
    uint64_t unique_carry_fp[N][MAX_UNIQUE];
    int unique_carry_count[N];
    memset(unique_carry_count, 0, sizeof(unique_carry_count));

    for (int ci = 0; ci < n_collisions && ci < MAX_COLL; ci++) {
        /* Recompute cascade for this collision, extracting carry states */
        uint32_t carry1[N][TOTAL_ADDS];
        uint32_t carry2[N][TOTAL_ADDS];

        /* Path 1 */
        {
            uint32_t s[8];
            memcpy(s, st1_56, 32);

            /* Build W1f array */
            uint32_t W1f[7];
            W1f[0] = coll_w1[ci][0]; W1f[1] = coll_w1[ci][1];
            W1f[2] = coll_w1[ci][2]; W1f[3] = coll_w1[ci][3];
            W1f[4] = (fn_s1(W1f[2]) + W1_pre[54] + fn_s0(W1_pre[46]) + W1_pre[45]) & MASK;
            W1f[5] = (fn_s1(W1f[3]) + W1_pre[55] + fn_s0(W1_pre[47]) + W1_pre[46]) & MASK;
            W1f[6] = (fn_s1(W1f[4]) + W1_pre[56] + fn_s0(W1_pre[48]) + W1_pre[47]) & MASK;

            for (int rn = 0; rn < ROUNDS; rn++) {
                uint32_t w = W1f[rn], k = KN[57 + rn];
                uint32_t sig1_e = fn_S1(s[4]), ch_efg = fn_Ch(s[4],s[5],s[6]);
                uint32_t sig0_a = fn_S0(s[0]), maj_abc = fn_Maj(s[0],s[1],s[2]);
                uint32_t t0 = (s[7]+sig1_e)&MASK, t1 = (t0+ch_efg)&MASK;
                uint32_t t2 = (t1+k)&MASK, T1 = (t2+w)&MASK;
                uint32_t T2 = (sig0_a+maj_abc)&MASK;
                int base = rn * ADDS_PER_ROUND;
                uint32_t ctmp[N];
                EXTRACT_CARRIES(s[7], sig1_e, ctmp);
                for (int bb=0;bb<N;bb++) carry1[bb][base+0]=ctmp[bb];
                EXTRACT_CARRIES(t0, ch_efg, ctmp);
                for (int bb=0;bb<N;bb++) carry1[bb][base+1]=ctmp[bb];
                EXTRACT_CARRIES(t1, k, ctmp);
                for (int bb=0;bb<N;bb++) carry1[bb][base+2]=ctmp[bb];
                EXTRACT_CARRIES(t2, w, ctmp);
                for (int bb=0;bb<N;bb++) carry1[bb][base+3]=ctmp[bb];
                EXTRACT_CARRIES(sig0_a, maj_abc, ctmp);
                for (int bb=0;bb<N;bb++) carry1[bb][base+4]=ctmp[bb];
                EXTRACT_CARRIES(s[3], T1, ctmp);
                for (int bb=0;bb<N;bb++) carry1[bb][base+5]=ctmp[bb];
                EXTRACT_CARRIES(T1, T2, ctmp);
                for (int bb=0;bb<N;bb++) carry1[bb][base+6]=ctmp[bb];
                s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;
                s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
            }
        }

        /* Path 2 */
        {
            uint32_t s[8];
            memcpy(s, st2_56, 32);

            uint32_t W2f[7];
            W2f[0] = coll_w2[ci][0]; W2f[1] = coll_w2[ci][1];
            W2f[2] = coll_w2[ci][2]; W2f[3] = coll_w2[ci][3];
            W2f[4] = (fn_s1(W2f[2]) + W2_pre[54] + fn_s0(W2_pre[46]) + W2_pre[45]) & MASK;
            W2f[5] = (fn_s1(W2f[3]) + W2_pre[55] + fn_s0(W2_pre[47]) + W2_pre[46]) & MASK;
            W2f[6] = (fn_s1(W2f[4]) + W2_pre[56] + fn_s0(W2_pre[48]) + W2_pre[47]) & MASK;

            for (int rn = 0; rn < ROUNDS; rn++) {
                uint32_t w = W2f[rn], k = KN[57 + rn];
                uint32_t sig1_e = fn_S1(s[4]), ch_efg = fn_Ch(s[4],s[5],s[6]);
                uint32_t sig0_a = fn_S0(s[0]), maj_abc = fn_Maj(s[0],s[1],s[2]);
                uint32_t t0 = (s[7]+sig1_e)&MASK, t1 = (t0+ch_efg)&MASK;
                uint32_t t2 = (t1+k)&MASK, T1 = (t2+w)&MASK;
                uint32_t T2 = (sig0_a+maj_abc)&MASK;
                int base = rn * ADDS_PER_ROUND;
                uint32_t ctmp[N];
                EXTRACT_CARRIES(s[7], sig1_e, ctmp);
                for (int bb=0;bb<N;bb++) carry2[bb][base+0]=ctmp[bb];
                EXTRACT_CARRIES(t0, ch_efg, ctmp);
                for (int bb=0;bb<N;bb++) carry2[bb][base+1]=ctmp[bb];
                EXTRACT_CARRIES(t1, k, ctmp);
                for (int bb=0;bb<N;bb++) carry2[bb][base+2]=ctmp[bb];
                EXTRACT_CARRIES(t2, w, ctmp);
                for (int bb=0;bb<N;bb++) carry2[bb][base+3]=ctmp[bb];
                EXTRACT_CARRIES(sig0_a, maj_abc, ctmp);
                for (int bb=0;bb<N;bb++) carry2[bb][base+4]=ctmp[bb];
                EXTRACT_CARRIES(s[3], T1, ctmp);
                for (int bb=0;bb<N;bb++) carry2[bb][base+5]=ctmp[bb];
                EXTRACT_CARRIES(T1, T2, ctmp);
                for (int bb=0;bb<N;bb++) carry2[bb][base+6]=ctmp[bb];
                s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;
                s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
            }
        }

        /* Record unique carry fingerprints at each bit */
        for (int b = 0; b < N; b++) {
            uint64_t fp = 14695981039346656037ULL;
            for (int j = 0; j < TOTAL_ADDS; j++) {
                fp ^= carry1[b][j]; fp *= 1099511628211ULL;
                fp ^= carry2[b][j]; fp *= 1099511628211ULL;
            }

            int is_new = 1;
            for (int j = 0; j < unique_carry_count[b]; j++) {
                if (unique_carry_fp[b][j] == fp) { is_new = 0; break; }
            }
            if (is_new && unique_carry_count[b] < MAX_UNIQUE) {
                unique_carry_fp[b][unique_carry_count[b]++] = fp;
            }
        }
    }

    printf("Carry-state automaton from %d collisions:\n\n", n_collisions);
    printf("Bit  Unique-Carry-States  = Automaton-Width\n");
    printf("---  -------------------  ----------------\n");
    for (int b = 0; b < N; b++) {
        printf("  %d  %19d  %s\n", b, unique_carry_count[b],
               unique_carry_count[b] == n_collisions ?
               "= #collisions (constant width!)" :
               unique_carry_count[b] < n_collisions ?
               "< #collisions (compression!)" :
               "> #collisions (expansion)");
    }

    printf("\n===== SUMMARY =====\n\n");

    double total_time = phase1_time + phase2_time;
    printf("Phase 1 (brute force + carry extraction):  %.4fs, %llu evals\n",
           phase1_time, (unsigned long long)total_states_evaluated);
    printf("Phase 2 (bit-serial forward solver):       %.4fs, %llu evals\n",
           phase2_time, (unsigned long long)total_cascade_evals);
    printf("Total time: %.4fs\n\n", total_time);

    printf("Collisions found: %d (expected: 49)\n", n_collisions);
    printf("Phase 2 verified: %d collisions from bit-serial solver\n", phase2_collisions);

    printf("\nBit-serial efficiency:\n");
    printf("  Brute force: %u cascade evaluations\n", 1U << (4*N));
    printf("  Bit-serial:  %llu cascade evaluations (%.2fx %s)\n",
           (unsigned long long)total_cascade_evals,
           (double)total_cascade_evals / (double)(1U << (4*N)),
           total_cascade_evals < (1U << (4*N)) ? "SPEEDUP" : "overhead");

    printf("\nAutomaton structure:\n");
    for (int b = 0; b < N; b++) {
        printf("  Bit %d: %d carry states among collisions, "
               "%d unique states overall (%llu survivors of %u total)\n",
               b, unique_carry_count[b], fp_counts[b],
               (unsigned long long)survivors[b], 1U << (4*N));
    }

    int constant_width = 1;
    for (int b = 0; b < N; b++) {
        if (unique_carry_count[b] != n_collisions) { constant_width = 0; break; }
    }
    if (constant_width) {
        printf("\n*** CONSTANT-WIDTH AUTOMATON CONFIRMED ***\n");
        printf("*** Width = %d at every bit = #collisions ***\n", n_collisions);
        printf("*** Implies O(N × %d) true bit-serial solver possible ***\n", n_collisions);
    } else {
        printf("\nCarry automaton is NOT constant-width.\n");
        printf("Width varies by bit position.\n");
    }

    /* Cleanup */
    free(cur_pool);
    free(next_pool);
    for (int b = 0; b < N; b++) free(fp_sets[b]);

    return 0;
}
