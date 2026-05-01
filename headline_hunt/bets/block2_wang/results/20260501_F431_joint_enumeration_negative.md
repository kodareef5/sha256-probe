---
date: 2026-05-01
bet: block2_wang
status: PATH_C_HAMMING3_BALL_FULLY_NEGATIVE
parent: F429 W[60] enum, F430 W[57..59] enum
evidence_level: VERIFIED
compute: 0 solver search; 35.9s exhaustive joint enumeration (786,432 forward evaluations); 0 cert-pin runs
author: macbook-claude
---

# F431: joint Hamming-{2,3} enumeration confirms the full W1[57..60] Hamming-3 ball is empty of equal-or-better HW

## Setup

F429 covered W1[60]-only at Hamming-{1,2,3} (5,488 evals/cand).
F430 covered W1[57..59]-only at Hamming-{1,2,3} (147,536 evals/cand).
The remaining gap was joint perturbations: flips spanning W1[57..59]
AND W1[60].

F431 enumerates all joint Hamming-{2,3} cases:

- H-2 joint: 1 bit in W1[57..59] (96) × 1 bit in W1[60] (32) = 3,072 / cand
- H-3 1+2: 1 bit in W1[57..59] × 2 bits in W1[60] = 96 × 496 = 47,616 / cand
- H-3 2+1: 2 bits in W1[57..59] × 1 bit in W1[60] = 4,560 × 32 = 145,920 / cand
- **Total: 196,608 / cand × 4 cands = 786,432 evaluations**

Combined with F429 + F430, this completes the full Hamming-{1,2,3}
ball over the 128-bit W1[57..60] for each cand:

| Coverage | Per cand | × 4 cands |
|---|---:|---:|
| F429: W[60]-only | 5,488 | 21,952 |
| F430: W[57..59]-only | 147,536 | 590,144 |
| F431: joint | 196,608 | 786,432 |
| **Total Hamming-{1,2,3}** | **349,632** | **1,398,528** |

35.9s wall. 0 SAT solver runs.

Runner: `headline_hunt/bets/block2_wang/encoders/F431_joint_enumerate.py`.
Artifact: `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F431_joint_enumeration.json`.

## Results

| Cand | Current best HW | F431 candidates ≤ best | New records |
|---|---:|---:|---:|
| bit3  | 51 | 0 | 0 |
| bit2  | 51 | 0 | 0 |
| bit24 | 43 | 0 | 0 |
| bit28 | 45 | 0 | 0 |

**Zero candidates at HW ≤ best in all joint classes** for all 4 cands.

## Filter pass-rates

cascade-1 invariants pass for **all 786,432 candidates** across all 4
cands. (Joint flips across W1[57..59] and W1[60] still preserve
cascade-1 because the differential propagation accommodates each
W-flip via cascade1/cascade2 offsets.)

bridge_score pass-rates:

| Cand | H-2 joint | H-3 1+2 | H-3 2+1 |
|---|---|---|---|
| bit3  | 3008 / 3072 (97.9%) | 46624 / 47616 (97.9%) | 139872 / 145920 (95.9%) |
| bit2  | 100% | 100% | 100% |
| bit24 | 100% | 100% | 100% |
| bit28 | 100% | 100% | 100% |

bit3 (kbit=3) is the only cand with bridge rejections in F431. Its
kbit-table constraints are tighter than kbit=2/24/28. Even excluding
bridge-rejected candidates and using only cascade-1 + HW, bit3 still
has 0 candidates at HW ≤ 51 in F431 — bridge_score is not the floor.

## Combined Hamming-{1,2,3} verdict

Across F429 + F430 + F431 = **1,398,528 forward evaluations** covering
the full Hamming-{1,2,3} ball around current bests for all 4 panel
cands:

- **bit24 HW=43**: 0 H-{1,2,3} neighbors at HW ≤ 43.
- **bit28 HW=45**: 0 H-{1,2,3} neighbors at HW ≤ 45.
- **bit3, bit2 HW=51 each**: 0 H-{1,2,3} neighbors at HW ≤ 51.

The discovered records are sharp, isolated W-cube points. Not local
minima in a connected basin — they are *singletons* surrounded by
strictly-higher-HW neighbors at radius ≤ 3.

## Findings

### Finding 1: Path C residual records are W-cube isolated singletons

This is a strong structural fact about block-2 absorption:

- HW landscape has discrete "spikes" at specific W-cube points, with
  no nearby HW plateaus.
- The Hamming-3 ball covers ~10⁶ neighbors per cand. None achieves
  the record HW. The records are not in shallow basins — they are
  in deep, narrow wells.

This explains why F408's wide-radius (max_flips=6) anneal *missed*
bit24 HW=43 and why F428's tighter (max_flips=3) anneal seeded from
F408's HW=49 *found* it: the HW=43 well is small and deep, requires
hitting the specific 2-bit W1[60] flip pattern. Probabilistic anneal
finds it only with seeded-and-narrow exploration; wide anneal with
many random flips drifts past it.

### Finding 2: bridge_score and cascade-1 are not the binding floor

Both filters pass nearly all candidates (cascade-1 100% across all
1.4M evaluations; bridge_score 100% for bit2/bit24/bit28 and ~96-98%
for bit3 in F431). Yet 0 candidates achieve HW ≤ current best.
Therefore the HW objective itself produces this isolation — it is a
property of the combinatorial structure of (round 57-63 forward
simulation, kbit-fixed cand, cascade-1 invariants), not an artifact of
the bridge_score reward.

### Finding 3: deeper Path C records require radius > 3 or different geometry

To find HW < current best, future Path C work must pursue one of:

- **Wider Hamming radius**: try anneal with max_flips=6, 8, or 10.
  But: the F408 wide anneal (max_flips=6) already explored this and
  did not find HW < 49 on bit24, HW < 45 on bit28, etc. Wider anneal
  may not help further.
- **Joint with cascade-1 relaxation**: lift the `c=g=1` constraint
  or allow `da_eq_de`. New geometries may have lower-HW records.
- **Different kbit cands**: bit13 (untouched), bit5, bit10, ...
  Each kbit gives a different W-cube; some may have lower minima.
- **Non-W-cube approach**: search over `m0` / `fill` instead of
  fixing them. Larger search space but potentially lower HW.

### Finding 4: cumulative day's evidence on Path C

| F-number | Type | Best HW found |
|---|---|---|
| F408 (codex) | Wide anneal | bit3 51, bit2 51, bit24 49, bit28 45 |
| F427 | Seeded refine bit28 | bit28 still 45 (3-bit isolation) |
| F428 | Seeded refine bit3/bit2/bit24 | **bit24 43** ← single breakthrough |
| F429 | W[60] enum | 0 ≤ best across 4 cands |
| F430 | W[57..59] enum | 0 ≤ best across 4 cands |
| F431 | Joint enum | 0 ≤ best across 4 cands |

Net: one new HW record (bit24 49 → 43), and a complete characterization
that all current bests are Hamming-3 isolated peaks.

## Verdict

- **Path C residual records are at sharp isolated W-cube points.**
  Confirmed by 1.4M deterministic evaluations covering the full
  Hamming-{1,2,3} ball.
- **No new records in F431.**
- The Hamming-3 attack vector is now closed. Future Path C work needs
  a different attack: wider radius, geometry relaxation, new cands,
  or different bet entirely.

## Next

Plausible day-end pivots:

1. **F432: bit13 seeded refinement**. F378 surprise top-1, untouched
   in this cycle. Quick (~3 min). Could find a new record analogous
   to bit24 HW 49 → 43.
2. **F433: drop cascade-1 c=g=1 constraint and see what HW reductions
   exist** under a relaxed geometry. Risky (changes the residual
   problem) but informative.
3. **Pivot to sr61_n32**: this session has not touched the schedule-
   compliance bet at all. Bigger headline target.
4. **Pause for codex's quota reset (13:22 EDT)**, sync up with Yale's
   F416-F426 chain, and replan together.

The combined F429+F430+F431 result is a clean structural conclusion
that suggests Path C may be near its W-cube floor on these 4 cands.
The single F428 breakthrough was the exception, not the rule.
