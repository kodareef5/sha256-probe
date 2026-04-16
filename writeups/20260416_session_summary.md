# 2026-04-16 Session Summary: Structural Findings

## Context

Today's session launched with the `sr=61 at N=32` race (10 macbook + 34 fleet
seeds on 29 CNFs) and opportunistically explored cascade structure while
waiting for kissat. Kissat produced no SAT as of 14:00 (~3 hours CPU each).

## Findings (in order of discovery)

### 1. Rotation-Aligned Kernel Hypothesis (Posted 11:47, Refined 15:15)

Fleet scanned N=32 for sr=61 candidates across 9 kernel bit positions.
Observation: bits that gave candidates — {0, 6, 10, 11, 13, 17, 19, 25} —
are 6/8 aligned with SHA-256 rotation constants (plus LSB).

Hypothesis strong version: productive = {0} ∪ {rotation constants}.

**REFUTED 15:15** when fleet found 3 candidates at bit 20 (not a rotation).

Refined hypothesis: rotation-aligned bits are MORE productive on average
(bit 25 = Sigma1[2] gave 9 candidates — record), but non-rotation bits
can still produce candidates at lower rates.

Writeup: `writeups/rotation_aligned_kernels.md`

### 2. Linear Invariants at N=4 (Retracted at N=8)

At N=4 (49 collisions, MSB kernel): 2 linear invariants across all collisions.
Specifically: W1[59] bits 2 and 3 are fixed (b2=0, b3=1), so W1[59] ∈ {8,9,a,b}.
Affine rank 14/16.

At N=8 (260 collisions): **zero linear invariants**. Affine rank 32/32.

Conclusion: the N=4 invariants are artifacts of small-N scaled rotations,
NOT fundamental cascade properties. No algebraic shortcut generalizes.

Writeup: `q5_alternative_attacks/results/20260416_collision_linear_invariants.md`

### 3. W1[59] Cardinality Reduction (VERIFIED)

Across N=4,6,8,10: W1[59] takes a consistently small fraction of possible
values, dramatically smaller than sibling words W[57], W[58], W[60]:

| N | W1[59] unique / 2^N | Fraction |
|---|---------------------|----------|
| 4 | 4/16 | 25.0% |
| 6 | 17/64 | 26.6% |
| 8 | 42/256 | 16.4% |
| 10 | 68/1024 (partial) | 6.6% |

Trend: **decreasing cardinality fraction with N**. At N=32, may be <1%.

But: the 42-set at N=8 has near-maximal algebraic degree (7/8) AND a BDD
of 48 nodes vs 56 for random — **no exploitable standalone structure**.
The cascade constraint IS in W1[59] but is NOT accessible via marginal
projection.

Writeup: `q5_alternative_attacks/results/20260416_W59_cardinality_reduction.md`

### 4. Cascade Tree Linearity (MAJOR)

At N=8, 260 collisions factor through **250 unique (W57,W58) pairs** and
**251 unique (W57,W58,W59) triples** — fanout ratio 1.04.

Forward branching factors:
- W57 productive: 152/256 (59%)
- W58 given W57: avg 1.64
- W59 given (W57,W58): ~1.0
- W60 given (W57,W58,W59): ~1.04

**Effective collision path count = 2^N** (matches carry entropy theorem).

At N=10 (partial, 151/946): ratio 1.049 — **confirmed**.

Writeup: `q5_alternative_attacks/results/20260416_cascade_tree_linearity.md`

### 5. f(W57)→(W58,W59,W60) Map Diffusion (Negative Result)

Given the near-deterministic cascade tree, is there a simple f(W57) map?
Tested at N=8:
- Delta W58-W57: uniform distribution (no consistent offset)
- XOR W57⊕W58: uniform
- Bit-correlations: max 0.077 from 0.5
- Hamming-weight correlations: ~0

**No algebraic structure** in the W57→W58 map. Polynomial-time path via
"learn f from small N, apply to N=32" does not trivially work.

### 6. BDD Measurement at N=8 (4322 Nodes, Scaling 4.56)

Built collision BDD with interleaved bit ordering: **4322 nodes** for 260
collisions (16.6/collision). Combined with prior N=4 (183 nodes):
scaling exponent ~N^4.56 (consistent with prior memory of O(N^4.8)).

**Projected BDD size at N=32: ~4.4M nodes ≈ 100 MB** (tractable).

Writeup: `q5_alternative_attacks/results/20260416_bdd_size_measurement.md`

### 7. Bit-1 Bias in Productive W57 (Weak)

At N=8, 63% of productive W57 values have bit 1 = 1 vs 31% of non-productive.
Other bits ~50%. Single bit gives weak predictive power but not enough
for efficient prediction. Could be candidate-specific (only M[0]=0x67 tested).

## Unified Picture

All findings are facets of the same underlying structure:
- **Collision set has bounded complexity** (O(N^4.56) BDD, O(2^N) collisions)
- **But NO forward-accessible structure** (cascade tree linearity requires
  navigating a diffused map)
- **Marginal projections lack exploitable structure** (W1[59] indicator BDD
  no better than random)
- **Intermediate BDD construction explodes** (127K nodes at N=4 intermediate
  vs 183 final)

This is consistent with the "finite-state transducer with polynomial output
complexity but near-injective individual paths" model from `unified_theory.md`.

## Race Status (End of Session)

- N=32 sr=61: 10 macbook + 34 fleet seeds, 0 SAT (3+ hours CPU each)
- N=10 cascade DP: 151/946 collisions, ~4h remaining
- Fleet total N=32 candidates: 40 across 9 kernel bits

## Open Questions Raised

1. Does SAT solve time at N=32 correlate with rotation-alignment?
   (Bit-25 vs bit-20 test)
2. Does the W1[59] cardinality fraction continue decreasing toward 0?
   (Test N=12, N=14)
3. Is there a POLYNOMIAL-TIME BDD construction that avoids the
   intermediate explosion?
4. Can we find a PROVABLY compact description of the collision set
   beyond the BDD (e.g., a polynomial variety)?
