# F_2-Linear Jacobian Analysis — Issue #15 Results

## Setup

128×256 Jacobian matrix: each row = one free input bit (4 words × 32 bits),
each column = one output difference bit (8 registers × 32 bits).
Entry = 1 if flipping input bit changes output bit in XOR-linear model.

Candidate: M[0]=0x17149975, fill=0xffffffff (verified sr=60 SAT).

## Results

### Full rank: 128 of 128
Every free input bit has a unique linear fingerprint. No redundancy
in the XOR-linear approximation. This means there's no "free" direction
that doesn't affect any output — every input bit matters.

### Weakest output bits: dh[63] register
| Output region | Min column weight | Meaning |
|---|---|---|
| dh[63] bits 22-31 | 19 of 128 | Only 15% of input bits affect these |
| dg[63] | ~35 | Moderately sensitive |
| da[63], de[63] | ~60-70 | Highly mixed |

**dh[63] is the weakest link.** The h-register is last in the shift chain,
so it receives the least mixing. Its high bits depend on only 19 input bits
— meaning if we could zero those 19 bits' contributions, dh would be zero
regardless of the other 109 bits.

### SVD: moderate low-rank structure
- Top singular value: 65.3 (dominates — 4.4x the second)
- Rank for 90% energy: 73 of 128
- Rank for 99% energy: ~120 of 128

The linear structure concentrates into 73 dimensions. 55 dimensions
carry only 10% of the signal. This is MODERATE low-rank — not as
exploitable as rank 20 would be, but not random (which would be ~128).

### Input bit influence distribution
- Mean: each input bit affects 85.8 of 256 output bits (33.5%)
- Range: 58 to 100
- No extreme outliers — all input bits are moderately influential

## Interpretation

1. **dh[63] as attack target**: Focus a constrained SAT instance on
   zeroing dh first (fewest dependencies), then propagate backward.
   This is a principled way to decompose the collision constraint.

2. **The dominant singular direction**: The top SVD vector represents
   the single most correlated pattern between inputs and outputs.
   Projecting the free words onto this direction gives the "most
   informative" 1D slice of the 128-dimensional search space.

3. **Moderate rank = moderate exploitability**: 73 effective dimensions
   means the XOR-linear problem is ~57% of full dimensionality. Carries
   fill in the rest. A lattice attack would need to handle the carry
   structure to exploit this further.

## Caveats

- **XOR-linear model is LOOSE**: Ch ≈ XOR and Maj ≈ XOR are bad
  approximations. Real Ch is a multiplexer (nonlinear), real Maj is
  a majority gate. The actual Jacobian over Z/2^32 would be different.
- **Carries ignored**: The gap between XOR-linear and modular arithmetic
  is exactly the carry propagation that makes SAT hard.
- **Single message pair only**: dW analysis, not independent M1/M2 analysis.

## Next steps

1. Compute the ACTUAL (carry-aware) Jacobian via sampling (like Issue #14's
   correlation matrix). Compare rank to the XOR-linear baseline.
2. Build a SAT instance that constrains dh[63] first (target the weakest
   output register specifically).
3. Project free words onto the top SVD direction and search that 1D slice.

## Validation Against Nonlinear Model — NEGATIVE

Sampled 100K random (W[57..60]) pairs through the ACTUAL 7-round tail
(with carries, real Ch/Maj). Result:

- **ALL 8 registers: mean diff HW = 16.00 ± 0.01** (perfectly uniform)
- **ALL 256 output bits: zero frequency = 50.0% ± 0.4%** (no outliers)
- Top vs bottom bit: 50.40% vs 49.58% — within sampling noise

**The XOR-linear dh[63] weakness is completely masked by carry propagation.**
In the real function, no register or bit is easier to zero than any other.
The carries randomize the output so thoroughly that the linear Jacobian
structure does NOT transfer.

This means:
1. Targeting dh[63] first won't help — it's no easier than any other register
2. The moderate SVD low-rank (73/128) is an artifact of the linearization
3. Carry propagation is the dominant source of difficulty, not linear mixing

**The lattice approach (Issue #15) is unlikely to help at N=32** unless
we find a way to handle carries within the lattice framework.

## Evidence level

**EVIDENCE**: XOR-linear Jacobian is exact for the linearized model.
Carry-aware validation (100K samples) shows the linear structure does
NOT transfer to the actual function. The lattice approach is deprioritized.
