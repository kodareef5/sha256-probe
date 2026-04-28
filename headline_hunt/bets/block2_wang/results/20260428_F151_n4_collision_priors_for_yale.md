# F151: N=4 collision priors — empirical W[59] diff structure for yale's search

**2026-04-28**

## Summary

Cluster-analyzed q5_alternative_attacks/results/collision_list_n4.log
(49 N=4 cascade-1 collisions exhaustively enumerated). Found a STRONG
EMPIRICAL CONSTRAINT on the W[59]-position differential that yale's
absorber search at N=32 hasn't been exploiting.

## The empirical constraint

At N=4, the 49 verified collisions have W[2] differential bit-frequency:

```
bit 0: 47/49 set (96%)
bit 1: 49/49 set (100%)
bit 2:  0/49 set (0%, FORBIDDEN)
bit 3: 49/49 set (100%)
```

Most common W[2] diff value: **0xb (= 0b1011) in 47/49 collisions (96%)**.

W[2] in N=4 cascade-1 framework corresponds to **W[59] in N=32**
(since W57..W60 are the 4 free words; W[2] = W[57+2] = W[59]).

## What this predicts at N=32

Linear scaling N=4 → N=32 (4× width):
- N=4 W[2] diff bit pattern {0, 1, 3} → N=32 W[59] diff bits {0,1,3, 8,9,11, 16,17,19, 24,25,27} (8-bit chunks)
- N=4 W[2] forbidden bit {2} → N=32 W[59] forbidden bits {2, 10, 18, 26}

But this linear extrapolation is naive. The CORRECT scaling depends on
how the cascade mechanism scales — empirically observed in the project's
de58 growth law: |de58| = 2^(N-22) for N > 22. At N=32, only 10 bits
of de58 vary; 22 bits are structurally constrained.

For W[59], an analogous constraint likely applies. Yale's absorber
search currently treats W[59] as free; restricting it to a specific
bit pattern derived from the cascade mechanism could escape yale's
score-86 local minimum.

## Other empirical priors

- **W[0] (= W[57] at N=32)**: bit 0 set in 49/49 (100%), bit 3 set in
  48/49 (98%), bit 2 set in 1/49 (2%). Pattern: bits {0, 3} required,
  bit {2} forbidden. Top value 0x9 (= 0b1001) in 33/49 (67%).
- **W[3] (= W[60])**: bit 1 NEVER set (0%) — strong constraint.
- **W[1] (= W[58])**: most variable, no strong bit constraint.
- **dW_hw (total)**: range 6-12 at N=4, mean 9.02 (≈56% density).

## Concrete suggestion for yale

Yale's F111 active subset scan currently lets W[57..60] vary freely
within active words. Two structural restrictions could surface lower
scores:

1. **W[59] diff bit-2 forbidden** (and analog bits {2, 10, 18, 26} at
   N=32). Implement as a hard constraint in search_block2_absorption.

2. **W[57] (= W[0]) diff bits {0, 3} required** (and analog bits
   {0, 3, 8, 11, 16, 19, 24, 27} at N=32). Tightens W[0] by 4 bits
   (out of 32).

Combined: ~12 bits of W57+W59 differential are structurally fixed.
Reduces yale's effective search space by ~12 bits = 4096×.

## Active position analysis

N=4 active positions:
- (0,1,2,3) — all 4: 45/49 (92%)
- (0,2,3) — skip W[1]: 4/49 (8%)
- W[1] is sometimes inactive (4/49 collisions)

This contradicts the assumption that all 4 W's must be active. yale's
F111 explicitly tested {0,1,11} and {0,1,8,14} sparse subsets;
{0,2,3} skip-W[1] subset hasn't been tried at N=32. Could be worth
adding to yale's search slate.

## Connection to existing work

This is the "cluster-analysis on existing q5 results that could feed
block2_wang" the hourly pulse mentioned. Q5 has ~50 result files;
this memo extracts ONE high-value insight (W[59] diff structure
constraint) from the N=4 collision list.

Other q5 files worth analyzing:
- q5_alternative_attacks/results/20260411_cascade_dp_n10_946_collisions.log
  (only top-line summary in log; full data may be elsewhere)
- 20260412_collision_scaling_law.md — log2(C) = 1.07*N + α prediction
- 20260411_restricted_anf_n8_complete.md — ANF analysis at N=8

## Predicted outcomes

If yale ADDS the W[59] diff bit-2 forbidden constraint (and its bit-
position analogs at N=32):
- Search space tightens by ~12 bits
- Lower-score absorbers should be reachable in fewer iterations
- Predicted score floor: 80-83 (vs current 86)

If outcomes match: empirical small-N collision structure transfers to
N=32 absorber yield, validating the project's structural framework.

If outcomes don't match: small-N constraints don't transfer linearly,
and yale's local minimum is N=32-specific.

## Discipline

- 0 SAT compute
- 0 solver runs
- Pure-thought analysis on existing q5 N=4 data + yale's structural
  framework
- Probe at `/tmp/q5_collision_analysis.py` (one-shot, can re-derive)

## Status

Concrete structural prior identified. Adds a 3rd axis to yale's
slate (cand axis F148/F149 + word-subset axis F150 + bit-position
axis F151). Estimated combined yale-side compute: 5 cands × 6 word-
subsets × testing the W[59] constraint = ~10 minutes additional vs
without F151's bit constraints.

This is the kind of fleet-discoverable structural prior that an
isolated yale would not surface — comes from cross-bet data integration.
