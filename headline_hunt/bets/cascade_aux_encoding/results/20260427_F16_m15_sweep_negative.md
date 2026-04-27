# F16: Single-axis M[15] sweep — 0 cascade-1 hits across 17.2B messages
**2026-04-26 21:09 EDT**

NEGATIVE empirical confirmation: random single-axis perturbation of
the registry default message cannot find cascade-1 alignment at slot 57+.

## Setup

For each of 4 candidate cands, fix M[0]=m0, M[1..14]=fill, vary M[15]
across all 2^32 values. For each M[15]:
1. Compute schedule W[0..63] for both M1 and M2 (with kernel diff)
2. Run SHA-256 forward through round 56
3. Check cascade-eligibility (da[57]=0)
4. If eligible, count consecutive cascade-1 alignments at slots 57..63

C tool: `encoders/cascade_m15_sweep.c` at ~5M iterations/sec on M5.

## Result

| cand | cascade-eligible (of 2^32) | slot-57 cascade-1 hits |
|---|---:|---:|
| msb_m17149975 (verified sr=60 cand) | 3 | 0 |
| bit19_m51ca0b34 | 3 | 0 |
| msb_m189b13c7 (HW=2 chamber champion) | 2 | 0 |
| bit17_m427c281d | 1 | 0 |
| **TOTAL** | **9** | **0** |

Total messages explored: 4 × 2^32 = **17,179,869,184**.

## Expected vs observed

- **Cascade-eligibility** (da[57]=0 prob = 2^-32): expected 1 per cand,
  observed 1-3. Variance consistent with binomial distribution.
- **Slot-57 cascade-1** (conditional prob = 2^-32 given eligibility):
  expected 9 × 2^-32 ≈ 0. Observed 0. Match.

## Why this matters

It empirically confirms that **single-axis message perturbation is
asymptotically equivalent to brute-force random search** for cascade-1
alignment. We need 17.2 billion samples to find ~9 cascade-eligible
messages (1 per 2 billion), then need ANOTHER 2^32 attempts each to
find slot-57 alignment. Total: 2^64 ≈ 1.8e19 message evaluations to
expect 1 slot-57 cascade-1 hit. At our 5M/s rate, ~120,000 years.

## What this rules out

The "smart" idea of "vary one message word systematically and find
the cascade-aligned chamber" is **infeasible at C-tool speed**. The
search needs:

1. **Multi-axis variation**: vary all 14 free message words, not just
   M[15]. But that's 2^448 search space — way larger.
2. **Constraint propagation**: kissat / CDCL solvers do this. They
   propagate cascade-1 constraints back into M's bits, narrowing the
   search to ~2^60 effective via unit propagation.
3. **Algebraic reduction**: solve the schedule's nonlinear constraints
   directly. This is the "impossibility argument" track in writeups/.

## What's confirmed structurally

- The verified sr=60 cert (m17149975) found 1 cascade-aligned M in
  ~12h via kissat. F16 random search can't reproduce this because
  the search space density is 2^-128 for 4-slot alignment.
- For the 67 registry cands, 0 default messages have cascade-1 at
  slot 57+ (F15). Random single-axis sweep adds confirmation that
  we can't find one by simple perturbation.

## What this means for the bet

- **kissat / cadical search is the right tool** for finding cascade-
  aligned messages. Random perturbation is not.
- **F-series tools** (de58_enum, de60_enum, lowhw_set) are useful for
  STRUCTURAL CHARACTERIZATION of cascade-1 chambers, but they cannot
  produce sr=61 SAT.
- **The bet's compute budget** should remain on kissat, not on C
  enumeration tools.

## Tool retrospective

The C enumeration tools (~600M evals/sec for the simpler de58_enum,
~5M evals/sec for the heavier cascade_m15_sweep) characterize what
EXISTS in the cascade-1 chamber image. They don't search for what
the SCHEDULE produces — that's the kissat job.

EVIDENCE-level: VERIFIED. 17.2 billion message evaluations.
