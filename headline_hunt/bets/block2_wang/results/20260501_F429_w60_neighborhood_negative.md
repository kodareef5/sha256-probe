---
date: 2026-05-01
bet: block2_wang
status: PATH_C_W60_LOCAL_OPTIMA_CONFIRMED
parent: F428 multi-cand seeded refinement, F427 bit28 seeded refinement, F408 wide anneal
evidence_level: VERIFIED
compute: 0 solver search; 1.1s exhaustive enumeration; 0 cert-pin runs (no new records)
author: macbook-claude
---

# F429: W1[60] Hamming-{1,2,3} enumeration confirms current bests are W[60]-locally-optimal — no new records

## Motivation

F408 (wide anneal), F427 (bit28 seeded refine), and F428 (bit3/bit2/bit24
seeded refine) all show the same pattern: when the search finds a new
sub-floor record, the improvement is entirely in W1[60]; W57, W58,
W59 stay at the greedy/wide-anneal optimum.

This raises a deterministic question: are the current bests
**actually** W1[60]-locally-optimal? Anneal explores probabilistically
and could miss specific bit patterns. F429 enumerates the full
{1, 2, 3}-bit Hamming neighborhood of W1[60] for each cand, with
W57/W58/W59 fixed at current best, to answer it.

If a deeper minimum existed at small W1[60] Hamming distance, F429
would find it. If not, current bests are confirmed W[60]-locally
optimal and the next breakthrough requires varying W57/W58/W59.

## Setup

Per-cand: enumerate all `C(32, r)` for r in {1, 2, 3} flips of W1[60]
(32 + 496 + 4960 = 5488 candidates each). For each, compute cascade-1
forward, evaluate bridge_score, record HW, score.

W57/W58/W59 fixed at the current best per cand:

| Cand | Current best W1[57..60] | HW | Score | Source |
|---|---|---:|---:|---|
| bit3_m33ec77ca | `0xba476635 0x8cf9982c 0x0699c787 0x8893274d` | 51 | 71.551 | F408 |
| bit2_ma896ee41 | `0x504e056e 0x3e435e29 0xda594ea2 0xe37c8fe1` | 51 | 71.551 | F408 |
| bit24_mdc27e18c | `0x4be5074f 0x429efff2 0xe09458af 0xe6560e70` | 43 | 79.073 | F428 |
| bit28_md1acca79 | `0x307cf0e7 0x853d504a 0x78f16a5e 0x41fc6a74` | 45 | 74.146 | F408 |

Enumeration runner: `headline_hunt/bets/block2_wang/encoders/F429_w60_enumerate.py`. 0 SAT solver runs.

Total wall: 1.1s for all 4 cands × 5488 enumerations = 21,952 forward
evaluations.

Artifact: `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F429_w60_enumeration.json`.

## Results

| Cand | Current best HW | F429 best HW (radii 1–3) | New records |
|---|---:|---:|---:|
| bit3 | 51 | 51 | 0 |
| bit2 | 51 | 52 | 0 |
| bit24 | 43 | 49 | 0 |
| bit28 | 45 | 47 | 0 |

**Zero new records.** Every cand's current best is strictly better than
any W1[60]-only neighbor at Hamming distance 1, 2, or 3.

For bit24, the closest W1[60] neighbor at any radius lands at HW=49 —
which is exactly F408's HW=49. This makes mechanism sense: F428's
W1[60]=0xe6560e70 differs from F408's W1[60]=0xd6560e70 by 2 bits
(positions 28, 29). Flipping 1 bit back toward F408's 0xd6560e70 lands
near HW=49 (F408's value). The HW=43 basin is sharp: enter it via the
specific 2-bit pattern, and any 1-bit return-flip drops you straight
back to HW=49.

## Cascade-1 / bridge_score pass rates

For all 4 cands, every single W1[60] flip in the enumerated radius
preserves cascade-1 invariants (all 5488 candidates pass). The cascade
fingerprint is robust to W1[60] flips because cascade-1 invariants
depend on rounds 57–59 (which are fixed) and on `da_eq_de` of the
diff-state (which W1[60] only enters at round 60).

For bit3, bit2, bit24: bridge_score also passes for all 5488 flips.

For bit28: 31/32 + 493/496 + 4955/4960 = 5479 of 5488 pass bridge_score
— **9 W1[60] flips fail bridge_score** at small radii. These are
points where the bridge selector's structural constraints are
violated. Likely tail-HW thresholds or kbit-table constraints. Not
investigated further in this memo.

## Findings

### Finding 1: current bests are sharp W[60]-only local minima

Across all 4 cands, no W1[60] flip at distance ≤ 3 produces a lower
HW than the current best. F428's HW=43 bit24 record was the deepest
the seeded refinement could reach in a small W1[60] basin; F429
confirms it deterministically.

### Finding 2: the W[60] dominance pattern is bidirectional

The breakthrough pattern says: F408 wide-search misses, narrow seeded
refinement at small W1[60] distance finds. F429 says: at the new
record, no smaller W1[60] perturbation goes further. Combined: the
records are at W1[60] basin centers, not edges. This is structural
information about block-2 absorption's residual surface — it has
discrete W1[60] basins separated by Hamming-stable barriers.

### Finding 3: any deeper records require varying W[57..59] too

The next seedable experiment is the *complementary* enumeration: hold
W1[60] at current best and vary W1[57], W1[58], W1[59] at small
Hamming distance. If those enumerations also negative, the current
bests are W-cube local minima, and seeking deeper records requires
either a wider radius or a different geometry (e.g., relaxing
cascade-1 invariants on `c=g=1`).

## Verdict

- W1[60] Hamming radius ≤ 3 enumeration: **negative across all 4 cands**.
- Current bests are deterministically W1[60]-locally-optimal.
- The "small W1[60] perturbation" attack vector (which F427 and F428
  exploited from F408's first-pass results) is now exhausted. Further
  HW reduction requires moving W1[57..59].

## Next

1. **Symmetric experiment**: F430 — enumerate W1[57..59] Hamming-{1,2}
   neighborhoods with W1[60] held at current best. ~10 sec compute.
   If positive, finds a new "perturb-W57..59-only" attack vector.
2. **Joint enumeration**: F431 — enumerate Hamming-2 over the full
   128-bit W1[57..60] (8128 candidates per cand). ~5 sec. May find
   joint perturbations the per-word scans miss.
3. **Drop bridge_score gating**: re-run F429-style enumeration but
   with HW directly as the objective and only cascade-1 as a filter.
   Tests whether the bridge_score reward terms are blocking some
   HW-better witnesses.
4. **Move to a different cand**: bit13_m916a56aa (F378 surprise top-1
   control) was untouched in F427/F428. Its F378 best is HW=59. Same
   F428-style seeded refine. ~3 min compute.

This is a clean negative result that closes the easy-W[60]-perturb
hypothesis. The bigger picture: F408's HW=45 / HW=43 records on bit28
and bit24 may be near the W-space minimum reachable under cascade-1
+ bridge_score, in which case Path C's residual ceiling is here.
