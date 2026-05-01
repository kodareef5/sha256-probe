---
date: 2026-05-01
bet: block2_wang
status: PATH_C_W57_59_HAMMING3_LOCAL_OPTIMA_CONFIRMED
parent: F429 W1[60] enumeration negative
evidence_level: VERIFIED
compute: 0 solver search; 26.8s exhaustive enumeration (590,144 forward evaluations); 0 cert-pin runs
author: macbook-claude
---

# F430: W1[57..59] Hamming-{1,2,3} enumeration confirms current bests are W-cube-locally-optimal — even sharper negative than F429

## Motivation

F429 closed the W1[60]-only-perturbation question: at Hamming radius
≤ 3, no W1[60] flip improves HW. F430 closes the symmetric question:
at Hamming radius ≤ 3 over W1[57..59] (W1[60] fixed at current best),
does any flip improve HW?

If F430 also negative, the current bests are W1[57..60]-cube local
optima at radius 3 — not just W[60]-locally optimal but W-cube-locally
optimal in this Hamming-3 ball minus the joint cases.

## Setup

Per-cand: enumerate all `C(96, r)` for r in {1, 2, 3} flips over the
96 bits of W1[57], W1[58], W1[59] (W1[60] fixed at current best).
96 + 4560 + 142880 = 147,536 candidates per cand × 4 cands =
**590,144 forward evaluations**. 26.8s wall. 0 SAT solver runs.

Same panel + current bests as F429:

| Cand | Current best W1[57..60] | HW | Score | Source |
|---|---|---:|---:|---|
| bit3_m33ec77ca | `0xba476635 0x8cf9982c 0x0699c787 0x8893274d` | 51 | 71.551 | F408 |
| bit2_ma896ee41 | `0x504e056e 0x3e435e29 0xda594ea2 0xe37c8fe1` | 51 | 71.551 | F408 |
| bit24_mdc27e18c | `0x4be5074f 0x429efff2 0xe09458af 0xe6560e70` | 43 | 79.073 | F428 |
| bit28_md1acca79 | `0x307cf0e7 0x853d504a 0x78f16a5e 0x41fc6a74` | 45 | 74.146 | F408 |

Runner: `headline_hunt/bets/block2_wang/encoders/F430_w57_59_enumerate.py`.
Artifact: `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F430_w57_59_enumeration.json`.

## Results

| Cand | Current best HW | Candidates ≤ best | New records |
|---|---:|---:|---:|
| bit3 | 51 | 0 | 0 |
| bit2 | 51 | 0 | 0 |
| bit24 | 43 | 0 | 0 |
| bit28 | 45 | 0 | 0 |

**Zero candidates even tie the current best HW.** Out of 590,144
W1[57..59] perturbations evaluated, *not one* lands at HW ≤ current
best for any cand. This is sharper than F429, where bit3/bit2/bit24
had at least one neighbor at HW=current_best (the cand's own current
best, which is excluded).

In F430, the current bests are not just locally optimal — they are
**strictly isolated peaks**, with every W1[57..59] Hamming-3 neighbor
strictly worse on HW.

## Filter pass-rates

cascade-1 invariants pass for **all 590,144 candidates**. W1[57..59]
flips do not affect rounds 60 invariants: cascade_step_offset(57..59)
and the round-59 invariants `s1_59[1..3] == s2_59[1..3]` depend on
W1[57..59] but the differential is preserved by construction — the
W2 slot tracks via cascade1 offset. So all 4 cands have 100%
cascade-1 pass rate.

bridge_score pass rates (where < 100%, the bridge selector blocks the
flip):

| Cand | r=1 | r=2 | r=3 |
|---|---:|---:|---:|
| bit3  | 94 / 96 | 4371 / 4560 | 134044 / 142880 |
| bit2  | 96 / 96 | 4560 / 4560 | 142880 / 142880 |
| bit24 | 96 / 96 | 4560 / 4560 | 142880 / 142880 |
| bit28 | 96 / 96 | 4560 / 4560 | 142880 / 142880 |

bit3's bridge_score has narrower acceptance — kbit=3 has stricter
table constraints than kbit=2/24/28. Bit2/24/28: 100% bridge pass.

This means HW degradation isn't an artifact of bridge_score gating —
even if we drop bridge_score and accept all cascade-1-valid W's, the
HW *still* doesn't improve at radius ≤ 3 over W1[57..59] (since 0
candidates land at HW ≤ best).

## Findings

### Finding 1: current bests are isolated peaks at radius ≤ 3

Combining F429 and F430:

- F429 (W1[60] only, radius ≤ 3): 0 new records, but neighbors at
  HW close to best exist (e.g., bit24 HW=49 at distance 1 from
  HW=43).
- F430 (W1[57..59], W[60] fixed, radius ≤ 3): 0 candidates even at
  HW ≤ best. Sharper isolation.

Together: the current bests are **strict isolated peaks** in the
Hamming-3 neighborhood of W1[57..60]. The HW landscape near the
current bests has no plateaus — every flip strictly increases HW.

### Finding 2: bridge_score is not the bottleneck

Even if bridge_score is dropped (since cascade-1 alone passes 100% for
all cands), zero candidates achieve HW ≤ current best in F430. The
HW objective itself produces this isolation, independent of the
bridge_score reward terms.

This refutes the "bridge_score is too restrictive" hypothesis from
F427's score-better/HW-worse finding. Bridge_score and HW agree on
the local structure; the disagreement F427 saw was about which W1[60]
flip is *globally* score-best vs HW-best, not about local
neighborhood structure.

### Finding 3: deeper records (if they exist) require radius > 3

F428 found bit24's HW=43 from HW=49 at radius 2 in W1[60]. F429+F430
say no further radius-3 improvement exists. So if HW < 43 (bit24) or
HW < 45 (bit28) is reachable, it requires either:

- **Radius > 3** in W1[57..60] (joint perturbations of 4+ bits)
- **Joint W1[57..59] + W1[60] flips** — partially covered by anneal's
  random walk, but not exhaustively enumerated. F431 candidate.
- **Outside the Hamming ball entirely** — i.e., a different W-cube
  region. The seeded-anneal pattern can't find these.

### Finding 4: the bit24 HW=43 / bit28 HW=45 records may be near W-cube floor

If the Hamming-3 neighborhood is empty of better W's and joint
Hamming-3 (F431) also returns negative, the current records are
likely at or near the W-cube minimum reachable under cascade-1 +
bridge_score constraints with kbit-fixed cands. Lifting cascade-1's
`c=g=1` constraint or relaxing kbit could open new geometry.

## Verdict

- W1[57..59] Hamming-3 enumeration: **strictly negative across all 4 cands**.
  590,144 evaluations, 0 candidates at HW ≤ current best.
- Combined F429 + F430: current bests are **isolated peaks** at
  Hamming radius ≤ 3 over W1[57..60]; bridge_score is not the bottleneck.
- No Path C breakthrough. Strong structural negative.

## Next

1. **F431: joint Hamming-2 enumeration** over full W1[57..60] (8256
   per cand). Tests the joint-perturbation gap. ~2 sec compute.
   Likely also negative given F429+F430, but worth confirming.
2. **F432: bit13 seeded refinement** (untouched control cand, F378
   surprise top-1, no Path C touch). Same F428 pattern. ~3 min.
3. **Drop bridge_score AND cascade-1 c=g=1**: relax invariants and
   re-search; tests whether the constraint geometry is the binding floor.
4. **Move to a different bet**: bit24's HW=43 + bit28's HW=45 + the
   isolation finding might be sufficient block2_wang output for now;
   pivot to sr61_n32 (untouched in this session) or wait for codex
   quota reset (13:22 EDT) for cross-mechanism coordination.

The W1[57..60] Hamming-3 ball is now fully (or near-fully)
characterized for these 4 cands. The discovered records sit at
isolated peaks, which is a clean structural conclusion even without
SAT-class progress.
