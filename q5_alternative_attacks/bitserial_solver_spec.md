# Bitserial Carry Solver Specification

## Goal
Find sr=60 collisions in O(N × W) time instead of O(SIZE^4) = O(2^{4N}).

## Key Structural Facts Used
1. **dT2 = 0 at r61** (unconditional): cascade forces a=b=c match
2. **da61 = de61 = dT1_61**: single collision equation
3. **dh61 = dg60 = de58**: single DOF propagates through shift register
4. **dT1_61 depends on dh60 (const) + dCh60(de58) + dW61(sigma1_diff)**

## The Equation
dT1_61 = dh60 + Sigma1_diff(e60) + Ch_diff(e60,f60,g60) + dW[61]

Since de60=0: Sigma1_diff = 0.
dh60 = constant (cascade shift from state56).
Ch_diff depends on df60 (constant) and dg60 (= de58, variable).
dW[61] = sigma1(W1[59]) - sigma1(W2[59]) + (schedule constants).

## Bit-Serial Algorithm

Process bit positions b = 0, 1, ..., N-1:

### State at bit b
- carry_ch: carry from the Ch_diff computation (1 bit)
- carry_sig1: carry from the sigma1_diff computation (1 bit)
- carry_dT1: carry from the dT1_61 addition (1 bit)
- deferred_sigma1: sigma1(w59) bits at positions > b that are
  referenced by bit b via rotations (up to 19 deferred bits at N=32)

Total state width: 2^3 × 2^19 = 2^22 ≈ 4M (upper bound)

### Per-bit operation
For each state S and each (w57_bit_b, w59_bit_b) ∈ {0,1}^2:
1. Compute de58[b] from w57[0..b] (via cascade + Maj difference)
2. Compute Ch_diff[b] from de58[b] and df60 (constant)
3. Compute sigma1_diff[b] from w59 bits (including deferred)
4. Compute dT1_61[b] = dh60[b] + Ch_diff[b] + sigma1_diff[b] + carry
5. If dT1_61[b] != 0 at bit b and no carry can fix it: PRUNE
6. Update carries and deferred state → new state S'

### Pruning condition
At bit b, the partial dT1_61[0..b] must equal 0[0..b].
This eliminates ~50% of states per bit (random-like pruning).

### Complexity
Bits: N = 32
States per bit: W ≤ 2^22 (with pruning: expected 2^10-2^15)
Choices per state per bit: 4 (two message bits)
Total: N × W × 4 ≈ 32 × 2^15 × 4 = 2^22 ≈ 4M operations

At 1B ops/s: **4 milliseconds**

## The Challenge: Cascade Rounds 57-60

The equation dT1_61 depends on state60, which is the result of 4
cascade rounds. Each cascade round involves:
- W2[r] = W1[r] + cascade_offset (determined by state)
- SHA round update (T1 + T2)

The bit-serial approach must track the carries through ALL 4 rounds
plus the 3 schedule-determined rounds. Total additions: ~28.

Each addition contributes 1 carry bit to the state. Total carry state:
~28 bits. Combined with deferred sigma1 bits (~19): state ≈ 2^47.

This is TOO WIDE. Need reduction:

### Reduction 1: T2 path invariance
dT2 = 0 at r58+ → T2 carries are predetermined → remove from state.
Saves ~12 carry bits (4 rounds × 3 T2 additions).
Remaining: ~16 T1-path carries + 19 deferred = 2^35. Still too wide.

### Reduction 2: Cascade offset linearity
The cascade offset W2[r] = W1[r] + constant (per round, per state).
This is an ADD operation with known carries. Can be pre-computed.
Saves ~4 carry bits.

### Reduction 3: Schedule carry pre-computation
W[61] = sigma1(W[59]) + known constants. The addition carries can
be folded into the sigma1 deferred state.

### Effective state width (optimistic estimate)
~10 T1-path carries + 19 deferred sigma1 = 2^29.
With pruning at each bit: expected survivors ≈ 2^14-2^20.

### Complexity (realistic estimate)
N × 2^20 × 4 = 32 × 2^20 × 4 ≈ 2^27 ≈ 134M operations.
At 1B ops/s on GPU: **0.13 seconds at N=32**

## Next Steps
1. Implement the bit-serial state machine for the SINGLE EQUATION dT1_61=0
2. Track carry state through all 7 rounds + schedule
3. Verify at N=8: should find all 260 (w57,w59) roots in milliseconds
4. Scale to N=32: find all dT1_61=0 solutions, then search (w58,w60)

## Evidence Level: HYPOTHESIS (algorithm specified, not implemented)
