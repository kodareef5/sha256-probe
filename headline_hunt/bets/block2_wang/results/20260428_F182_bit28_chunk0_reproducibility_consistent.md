---
date: 2026-04-28
bet: block2_wang
fixture: bit28_HW59_naive_blocktwo
status: BIT28_FLOOR_ROBUST + CAND_LEVEL_DISTINCTION_REFINED
---

# F182: bit28 chunk-0 reproducibility — floor is robust across seeds (91-92)

## Setup

Same protocol as F178 (bit28 chunk-0, 64 size-5 masks at 3×4000) but
with seed 9001 instead of 8001. Tests whether F178's floor of 91 is
seed-singular like F135 (per F180) or seed-robust.

## Result comparison

| Seed | Best mask | Best score | bit3 reused mask `{0,1,2,8,9}` |
|---:|---|---:|---:|
| 8001 (F178) | `0,1,2,3,14` | **91** | rank 15 / 98 |
| 9001 (F182) | `0,1,2,6,15` | **92** | not in top-16 |

Across two seeds, bit28 chunk-0 floor is **91-92** (1-point spread).

The *best mask* differs (`0,1,2,3,14` vs `0,1,2,6,15`) — terminal
pair is seed-noisy — but the *floor value* is stable.

## Sharp contrast with bit19's chunk-1

| Fixture+chunk | Seed-7101/8001 floor | Seed-9101/9001 floor | Spread |
|---|---:|---:|---:|
| bit19 chunk-1 (F135 / F180) | 87 | 91 | **4** |
| bit28 chunk-0 (F178 / F182) | 91 | 92 | 1 |

Bit19's chunk-1 has a singular deep basin (the F135 score-87 result)
that requires the right seed to find. Bit28's chunk-0 has a flat,
seed-robust 91-92 plateau — no comparable deep basin findable at
3×4000.

## Cand-level structural-distinction picture (revised)

| Fixture | Cand | Robust chunk floor (3×4000, multi-seed) | Notes |
|---|---|---:|---|
| bit3 | cand_n32_bit3_m17149975 | **86** | Yale's empirical chunk-0 winner, reproducible |
| bit19 | cand_n32_bit19_m51ca0b34 | 91 | One singular sub-91 basin (F135 seed 7101 → 87) |
| bit28 | cand_n32_bit28_md1acca79 | 91-92 | Flat floor; no seed-9001 sub-91 result |

### F143 hypothesis status (partial falsification at this budget)

F143 predicted: distinguished cands (bit19, bit28, bit4, bit25, msb)
should have **better** fixture-local optima than bit3 due to their
structural distinction (de58_size below median, hardlock_bits).

Evidence against F143 at chunk-0/1 budget:
- Bit3 (NOT structurally distinguished): robust floor 86.
- Bit19 (distinguished): robust floor 91, with seed-singular 87.
- Bit28 (distinguished): robust floor 91-92.

At 3×4000 random-init budget, **bit3 has the lowest robust floor**.
Distinguished cands sit 5-6 points worse.

### But F143 may still hold under basin-init

Yale's F173 demonstrated that F135-init basin propagation reaches
87 on bit19. The score-87 basin exists but is invisible to chunked-
scan random search. If distinguished cands have deeper-but-narrower
basins, they may need basin-init or a global method to find.

The current empirical state:
- **At random-init budget**: F143 falsified (distinguished cands
  have worse floors).
- **At basin-init or global-method level**: F143 status unknown.
  Need to either find a sub-86 basin via basin-hopping, or run a
  SAT/BDD probe.

## Implications

### For ongoing fleet work
- **Multi-seed protocol confirmed valuable**: bit28's floor is
  robust across two seeds at low budget. Bit19's was not. This
  asymmetry itself is informative.
- **Distinguished-cand chunked-scan campaign at risk of being
  uninformative at 3×4000**: If bit4/bit25/msb behave like bit28
  (flat 91-92 plateau), the chunked-scan campaign won't reveal
  deep basins. We'd need basin-init or stronger budget per mask.

### For attack-mechanism design
- Random local search at chunked-scan budget can't reach the deep
  basins on distinguished cands.
- Basin propagation via F135-style init works on bit19 (87) but
  required a known good seed pair. We don't have one for bit28
  yet.
- **Discovery problem**: How to find the *first* deep basin on a
  new distinguished cand without knowing where to seed?
  - Option 1: brute-force chunked-scan with 5-10 seeds × 68 chunks
    × 5 cands = 50× current campaign. Maybe finds basin by luck.
  - Option 2: structural-method probe (SAT, BDD on the fixture)
    with known short-trail constraints. Doesn't rely on local
    search.
  - Option 3: cross-fixture transfer from bit19's known sub-87
    basin via the carry-automaton or differential-trail invariant
    (if any exists).

## What's NOT being claimed

- That bit28 lacks a deep basin (it might exist but is invisible
  to 3×4000 random search).
- That F143 is dead (it might hold under basin-init or global
  methods).
- That bit3's robust 86 floor is "easy" — it's seed-robust, but
  the search space is genuinely 5D with millions of masks.

## Discipline

- 0 SAT compute (heuristic local search)
- 0 solver runs
- Reproducibility test result: bit28 chunk-0 floor is seed-robust
  (91-92) — distinct from bit19's seed-noisy chunk-1 (87↔91).
