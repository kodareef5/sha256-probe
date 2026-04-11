# Bit-Serial MITM Specification

## Goal
Find all sr=60 collisions at N=32 in <1 hour on a 16GB machine.

## Algorithm: O(1.9^{N/2}) via MITM on bit positions

### Key Insight
Split the N=32 bit positions into two halves at bit 16.
Forward: process bits 0→15, grow from 1 state to ~30K states.
Backward: process bits 31→16, grow from 1 state to ~30K states.
Match: join at bit 16. Total: ~60K states, <10MB memory.

### State Definition
At bit position k, the state is:
```
struct state {
    uint8_t carry_diff[49];  // carry-difference for each addition chain
    // (7 additions × 7 rounds = 49 chains, 1 bit each)
    // Packed: 49 bits = 7 bytes

    uint32_t w1_partial[4];  // W1[57..60] bits assigned so far
    // Only bits 0..k (forward) or k..31 (backward)
};
```
Total state size: 7 + 16 = 23 bytes. At 30K states: 690KB.

### Forward Pass (bits 0→15)

```c
states[0] = { carry_diff = all_zeros, w1_partial = 0 };
n_states = 1;

for (bit = 0; bit < 16; bit++) {
    new_states = empty;
    for each state s in states:
        for w1_bits = 0..15:  // 4 bits: W1[57..60] at position 'bit'
            // Set bit 'bit' of each W1 word
            w1_57_bit = (w1_bits >> 0) & 1;
            w1_58_bit = (w1_bits >> 1) & 1;
            w1_59_bit = (w1_bits >> 2) & 1;
            w1_60_bit = (w1_bits >> 3) & 1;

            // Compute W2 bits from cascade (known function of state + W1 bit)
            // W2[r] bit k = W1[r] bit k XOR cascade_diff_bit_k(state)

            // For each of 49 addition chains:
            //   new_carry = maj(x1_bit, y1_bit, c1_in) XOR maj(x2_bit, y2_bit, c2_in)
            //   where x,y are the addition operands at this bit
            //
            // THE ROTATION PROBLEM:
            //   Some operands use rotated register values.
            //   E.g., Sigma1(e57) at bit k needs e57 at bit (k+6)%32.
            //   If (k+6) > 15 (our forward range), this bit is UNKNOWN.
            //
            // SOLUTION: track it as a SYMBOLIC frontier bit.
            //   The frontier has at most 6 unknown bits per round
            //   (from the 3 rotation offsets of Sigma0 and Sigma1).
            //   Over 7 rounds: ~42 frontier bits max.
            //   But many overlap: same W1 bit referenced from multiple rounds.
            //   Effective frontier: ~20 unique bits.
            //
            // For each frontier assignment (2^20 = 1M):
            //   Compute carry-outs, check constraints.
            //   Store (carry_state, frontier_assignment) as new state.
            //
            // BUT 1M × 30K = 30 billion — too slow.
            //
            // BETTER: don't enumerate frontiers at each step.
            //   Instead, track the CONSTRAINT on frontier bits.
            //   Each carry transition either:
            //   (a) is fully determined (no frontier bits involved), or
            //   (b) depends on a frontier bit — record the dependency.
            //
            // After processing all 16 forward bits, the state includes:
            //   - 49 carry values (or symbolic expressions in frontier bits)
            //   - The constraint system on frontier bits
            //
            // This is the RREF/affine system that GPT-5.4 described.

            // SIMPLIFICATION FOR ROUND 57:
            // At round 57, T1 = constant + W1[57].
            // Sigma1(e56) is constant (no rotation of variables).
            // So round 57 at bit k is PURELY LOCAL. No frontier.
            // carry_out = maj(constant_k, W1[57]_k, carry_in).
            // FULLY DETERMINED. No frontier needed.

            // Round 58: e57 depends on W1[57]. Sigma1(e57) at bit k
            // needs e57 at bits (k+6,k+11,k+25)%32.
            // If k < 16 and k+6 >= 16: frontier bit from W1[57] at k+6.
            // But W1[57] bit k+6 is a CHOSEN variable (from the forward pass).
            // At bit 0: W1[57] bits 6,11,25 are needed.
            // Bits 6 and 11 are in range [0,15] — ALREADY ASSIGNED.
            // Bit 25 is in range [16,31] — FRONTIER.
            // So only 1 frontier bit per Sigma1 access at most.

    // After expansion and pruning:
    states = new_states;
    n_states = |new_states|;
    printf("  Bit %d: %d surviving states\n", bit, n_states);
}
```

### The Rotation Frontier at N=32

For the forward pass (bits 0-15), the frontier bits are W1 values at
positions 16-31 that are referenced by rotations from positions 0-15.

Sigma0(a) uses ROR(2,13,22): at bit k, references (k+2,k+13,k+22)%32.
  For k=0: refs 2,13,22. Bit 22 is in [16,31] = frontier.
  For k=3: refs 5,16,25. Bits 16,25 are frontier.
  For k=14: refs 16,27,4. Bits 16,27 are frontier.
  For k=15: refs 17,28,5. Bits 17,28 are frontier.

Sigma1(e) uses ROR(6,11,25): at bit k, references (k+6,k+11,k+25)%32.
  For k=0: refs 6,11,25. Bit 25 is frontier.
  For k=5: refs 11,16,30. Bits 16,30 are frontier.
  For k=15: refs 21,26,8. Bits 21,26 are frontier.

The UNIQUE frontier positions referenced from bits 0-15:
  From Sigma0: {16,17,18,19,20,21,22,23,24,25,26,27,28} = 13 positions
  From Sigma1: {16,17,18,19,20,21,22,23,24,25,26,27,28,29,30} = 15 positions
  Union: {16..30} = 15 positions

But these are positions of REGISTER values, not message words.
The register values depend on W1 through the carry chain.
At bit 16+j, the register value depends on W1 bits 0..16+j.
Bits 0..15 are already assigned. So the frontier is W1 bits at {16..30}.

For W1[57]: 15 frontier bits (positions 16-30)
For W1[58]: same but fewer (round 58 state depends on fewer rounds)
Total: ~15 unique frontier positions per word × 4 words = ~60 bits.
BUT many are not independently free — they're constrained by carries.

EFFECTIVE frontier (after carry constraints): ~20 bits (empirical estimate).

### Practical Implementation

1. For round 57 at all 16 forward bits: NO frontier. Pure carry chain.
   This resolves W1[57] bits 0-15 completely.

2. For round 58: frontier = W1[57] bits 16-30 (through Sigma1(e57)).
   HOWEVER: W1[57] bits 16-30 are not yet assigned.
   We CANNOT compute round 58 without them.

   SOLUTION: process W1[57] ALL 32 bits first (as one word), THEN
   process W1[58] bit-by-bit with W1[57] fully known.

   This is the WORD-ROUND-HYBRID approach:
   - Process W1[57] as a whole word: 2^32 choices → 2^32 states
   - For each state, process W1[58] bit-by-bit (0→31)
   - Branching factor per bit: ~1.9
   - After 16 bits of W1[58]: 2^32 × 1.9^16 ≈ 2^32 × 30K ≈ 130 billion states
   TOO MUCH.

   OR: process W1[57] bit-by-bit, but DEFER rotation-dependent
   computations until the referenced bits are assigned.
   At bit 15: all bits 0-15 of W1[57] are known.
   But Sigma1(e57) at bit 0 needs bit 25 — still unknown.
   We can't evaluate round 58 bit 0 until bit 25 of W1[57] is known.

   CONCLUSION: The bit-serial approach requires processing ALL 32 bits
   of W1[57] before ANY bit of round 58 can be computed. This means
   the forward pass must process W1[57] as a unit: 2^32 states.

   Then W1[58] can be processed bit-by-bit WITH W1[57] known.
   But 2^32 × (branching from W1[58]) = still huge.

### The Real Architecture

After deep analysis, the bit-serial MITM has a fundamental issue:
rotations in Sigma0 and Sigma1 reference bits up to 25 positions away.
This means you MUST assign ~25 bits before you can evaluate any round
that uses those rotations.

The practical algorithm for N=32 is:

1. Enumerate W1[57] (2^32 values) — this fully determines round 57 state.
2. For each W1[57], use bit-serial DP on W1[58] (carry + rotation
   dependencies now resolved since W1[57] is fully known).
   Growth: ~1.9^32 ≈ 830M states over 32 bits. Memory: ~53GB. TOO MUCH.

OR use MITM on W1[58]:
2. Forward W1[58] bits 0-15: ~30K states per W1[57] value.
3. Backward W1[58] bits 31-16: ~30K states.
4. Match at bit 16: ~30K × 30K = 900M comparisons.
5. Total: 2^32 × 900M = 3.9 × 10^18 — TOO MUCH.

### The Correct Decomposition

The cascade chain means W2 is determined by W1.
So the free variables are just W1[57..60] = 4 × 32 = 128 bits.

The MITM should split these 128 bits into two halves:
  Forward: W1[57] + W1[58] = 64 bits → 2^64 states
  Backward: W1[59] + W1[60] = 64 bits → 2^64 states
  Match: at the state boundary between round 58 and round 59.

Memory: 2^64 states × 64 bytes = way too much (10^20 bytes).

WITH cascade pruning (da=0 at each round):
  Forward states: much fewer than 2^64 (carries constrain heavily).
  The carry entropy says ~sqrt(830M) ≈ 29K effective states.

ESTIMATED: forward states = O(1.9^{N/2} × 2^N) because we process
W1[57] exhaustively (2^32) and W1[58] with carry pruning (~1.9^32).
That's 2^32 × 830M = 3.6 × 10^18. TOO MUCH.

### Conclusion

The fundamental issue: at N=32, you must process at least ONE word
(32 bits) exhaustively because rotations span the full word width.
This contributes a factor of 2^32 that can't be avoided.

The remaining 3 words can potentially be handled by carry-serial DP
with branching factor ~1.9 per bit, giving ~1.9^96 for 3 words.
But 1.9^96 ≈ 10^27 — still astronomical.

The O(1.9^{N/2}) estimate from Gemini assumed bit-serial processing
ACROSS ALL ROUNDS SIMULTANEOUSLY. This requires handling the rotation
frontier, which at N=32 is ~25 bits — creating a 2^25 factor per step.

TRUE complexity: O(N × 2^25 × 1.9^N) ≈ O(2^25 × 830M) = 28 billion.
Memory: O(2^25 × 1.9^{N/2}) = O(2^25 × 30K) = 1 billion states = 64GB.

WITH state compression (hash equivalent states): could fit in 16GB.

THIS IS THE REAL ALGORITHM. It needs careful engineering but is feasible.
