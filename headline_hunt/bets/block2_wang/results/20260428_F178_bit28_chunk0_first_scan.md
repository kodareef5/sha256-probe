---
date: 2026-04-28
bet: block2_wang
fixture: bit28_HW59_naive_blocktwo (cand_n32_bit28_md1acca79_fillffffffff)
status: BASELINE_ESTABLISHED
---

# F178: bit28 fixture-local chunk-0 scan — first probe of distinguished cand

## Why this scan

Per F156's consolidation, the structural-distinction hypothesis predicts
that yale's distinguished cands (de58_size below median, hardlock_bits)
should have **fixture-specific** absorber physics — not necessarily a
lower floor than bit19, but observably *different* mask families
populating the low-budget winners.

Bit28_md1acca79 is yale's primary structurally-distinguished cand. It
has been included in registry-wide cert-pin sweeps (F100), but **never**
probed for fixture-local active-word search.

This is the first such scan. It establishes a baseline on the
chunk-0 enumeration (size-5 subsets at lex start_index=0..63) using the
yale-standard 3×4000 budget — same protocol as F134 (bit19 chunk-0).

## Setup

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit28_HW59_naive_blocktwo.json \
  --pool 0-15 --sizes 5 --start-index 0 --limit 64 \
  --restarts 3 --iterations 4000 --seed 8001 \
  --require-all-used --top 20 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F177_bit28_HW59_chunk0000_64x3x4k.json
```

## Top-20 results

| Rank | Score | msgHW | Active words |
|---:|---:|---:|---|
| 1 | **91** | 86 | `0,1,2,3,14` |
| 2 | 93 | 52 | `0,1,2,6,9` |
| 3 | 95 | 66 | `0,1,2,8,14` |
| 4 | 95 | 69 | `0,1,2,4,10` |
| 5 | 96 | 46 | `0,1,2,4,11` |
| 6 | 96 | 62 | `0,1,2,4,14` |
| 7 | 96 | 67 | `0,1,2,8,13` |
| 8 | 96 | 80 | `0,1,2,7,15` |
| 9 | 97 | 49 | `0,1,2,9,15` |
| 10 | 97 | 77 | `0,1,2,4,6` |
| 11 | 97 | 81 | `0,1,2,5,12` |
| 12 | 98 | 66 | `0,1,2,4,7` |
| 13 | 98 | 66 | `0,1,2,4,15` |
| 14 | 98 | 69 | `0,1,2,6,11` |
| 15 | 98 | 69 | **`0,1,2,8,9`** ← bit3's empirical winner |
| 16 | 98 | 73 | `0,1,2,5,15` |
| 17 | 98 | 74 | `0,1,2,4,8` |
| 18 | 98 | 83 | `0,1,2,6,12` |
| 19 | 98 | 86 | `0,1,2,7,11` |
| 20 | 99 | 42 | `0,1,2,5,13` |

## Cross-fixture comparison

| Fixture | Cand | chunk-0 floor mask | Score |
|---|---|---|---:|
| bit3 | cand_n32_bit3_m17149975 | (yale's empirical) `0,1,2,8,9` | 86 |
| bit19 | cand_n32_bit19_m51ca0b34 (yale F134) | `0,1,2,7,15` | 90 |
| **bit28** | cand_n32_bit28_md1acca79 (this scan) | `0,1,2,3,14` | **91** |

Bit28 chunk-0 floor (91) sits comparable-to-slightly-above bit19's (90).
Both are well above bit3 baseline (86) and bit19's known global-best
(`0,1,3,8,9`@87 via 8x50k continuation).

## Pattern observations

1. **`{0,1,2,*,*}` prefix dominates**: every one of the top-20 starts
   with `0,1,2`. This is the *same* prefix family that dominated bit3's
   chunk-0 (where the empirical `{0,1,2,8,9}` was best) and bit19's
   chunk-0 (where `{0,1,2,7,15}` was best). All three distinguished
   cands prefer early-message-word activity in their cheapest scan.

2. **Different terminal pair**: bit28's best mask uses `(3,14)` — far
   from bit3's `(8,9)` or bit19's `(7,15)`. The `*,*` tail is genuinely
   fixture-specific.

3. **Bit3 reused mask underperforms by 12 points**: `{0,1,2,8,9}` scores
   98 on bit28 vs 86 on bit3 native. Confirms the F132/F156 finding
   that bit3's empirical winner does not transfer fixture-locally —
   now extended to bit28.

4. **Wider score spread at low budget**: bit28's top-20 spans 91→99
   (8-point spread). bit19's chunk-0 top-20 spread was tighter
   (90→94, F134). Suggests bit28's local optima are sparser at this
   budget OR that 3×4000 sits in a noisier regime for this fixture.

## Hypothesis update

F143's "cand-specific structural distinction" hypothesis predicted
fixture-local optima would differ in *location* (mask), not necessarily
in *floor*. This first-look on bit28 is consistent:

- Floor: bit28 (91, chunk 0) ≈ bit19 (90, chunk 0). No dramatic
  cand-level fixture floor difference at chunk 0 budget.
- Location: bit28's winner `(0,1,2,3,14)` ≠ bit19's `(0,1,2,7,15)` ≠
  bit3's `(0,1,2,8,9)`. Each cand's terminal pair is its own.

## Next-step priorities

1. **Continue bit28 chunks 1-3** (start_index=64, 128, 192) to see if
   any non-`{0,1,2,*,*}` mask families surface, and whether bit28
   has a chunk-1 → 87-class winner like bit19's `{0,1,3,8,9}`.

2. **Continue top-K bit28 chunk-0 with 8×50k** (the F172 budget
   calibration finding: chunk floor at 3×4000 sits well above
   per-mask local minimum at 8×50k). The bit28 `{0,1,2,3,14}@91`
   could drop to 87-89 at full budget; that would close cand-level
   distinction at fixture-floor level.

3. **bit4_HW63 + bit25_HW62 + msb_m9cfea9ce**: each is also
   never-scanned and same-class-distinguished. Three more chunk-0
   probes would complete the F156 cross-cand floor map.

## Discipline

- 0 SAT compute (heuristic local search)
- 0 solver runs
- Validates against F143 hypothesis without falsifying it
- New empirical baseline added to fixture-local cross-cand corpus
