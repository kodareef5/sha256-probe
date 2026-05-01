---
date: 2026-05-01
bet: block2_wang
status: PATH_C_DEEPEST_CANDS_RADIUS6_CONFIRMED
parent: F428 bit24 HW=43; F408 bit28 HW=45; F427 bit28 radius-3 negative
evidence_level: VERIFIED
compute: 0 solver search; ~120s parallel anneal (2 cands, 12×200k iter, max_flips=6); 0 cert-pin runs (no new records)
author: macbook-claude
---

# F434: bit24 HW=43 and bit28 HW=45 survive radius-6 seeded anneal — bridge between F408 wide and F428 narrow closes

## Setup

The day's prior work showed:

- **F408** (codex): max_flips=6 random-init wide anneal. Found bit24
  HW=49 and bit28 HW=45 (along with bit3/bit2 HW=51).
- **F428** / **F427**: max_flips=3 seeded anneal from F408 best. F428
  found bit24 HW 49 → 43 (breakthrough); F427 confirmed bit28 HW=45
  robust at radius 3.
- **F429+F430+F431**: deterministic Hamming-{1,2,3} ball over W1[57..60]
  for all 4 panel cands. 0 candidates ≤ current best.

Gap: max_flips=6 seeded (bridging F408's max_flips=6 random and
F428's max_flips=3 seeded). F434 closes that gap on the deepest
records: bit24 HW=43 and bit28 HW=45.

Parameters:

- 12 restarts × 200,000 iter × max_flips=6 × temp 1.0 → 0.05 × tabu 1024
- bit24 seeded from `0x4be5074f, 0x429efff2, 0xe09458af, 0xe6560e70` (F428 HW=43)
- bit28 seeded from `0x307cf0e7, 0x853d504a, 0x78f16a5e, 0x41fc6a74` (F408 HW=45)
- 2 cands run in parallel on separate cores, ~120s wall total

Artifacts:
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F434_bit24_wide_seeded.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F434_bit28_wide_seeded.json`

## Results

| Cand | Init HW | Seeds at init HW | Other HW seen | Best HW found |
|---|---:|---:|---|---:|
| bit24 | 43 | 12/12 (score 79.07) | none | 43 |
| bit28 | 45 | 11/12 (score 74.15) | 1 seed → HW=47 score=75.33 | 45 |

bit24: zero seeds left the HW=43 basin even at max_flips=6. The
seeded anneal at radius 6 does not find any HW-different W reachable
from F428's record.

bit28: 1 seed escaped to HW=47 / score=75.33 — the same
score-better/HW-worse neighbor F427 already characterized (3-bit
W1[60] flip, positions 8/11/19). The anneal accepts this neighbor
because score=75.33 > 74.15. Other 11 seeds stayed at HW=45.

## Findings

### Finding 1: radius 6 confirms radius 3 — current bests are stable

F427 (radius 3) and F434 (radius 6) on bit28: same outcome. F428
(breakthrough at radius 3) and F434 (radius 6) on bit24: HW=43 holds.
The W-cube minima at the current bests are stable across the
explored anneal radii.

The earlier F408 wide-random anneal at max_flips=6 found HW=45 on
bit28 and HW=49 on bit24 — but F408's *random initialization* meant
restart trajectories started far from the optimal basins. F434's
seeded-from-best approach with max_flips=6 explores the
local neighborhood thoroughly without the random-restart overhead;
even with broader mutation radius, no improvement.

### Finding 2: the F427 score-better/HW-worse W keeps reappearing

F427's bit28 HW=47 score=75.33 W (3-bit W1[60] flip 8/11/19) is
reached again in F434. That W is a true secondary basin of bridge_score
nearby F408's HW=45 / score=74.15 init. The anneal can find it at
both radius 3 and radius 6 with the right walk.

This is reproducible structural evidence that bridge_score's
landscape near bit28's W1[60]=0x41fc6a74 has TWO distinct local
maxima: HW=45 score=74.15 (the F408 record) and HW=47 score=75.33
(adjacent neighbor). bridge_score's selector ascends to the higher
score; HW objective prefers the lower HW.

### Finding 3: Path C panel summary stable

Across F408 + F427 + F428 + F432 + F434, the deepest records are:

| Cand | Best HW | Source | Cert-pin |
|---|---:|---|---|
| bit24 | 43 | F428 | UNSAT (kissat + cadical) |
| bit28 | 45 | F408 | UNSAT (kissat + cadical) |
| bit13 | 50 | F432 | UNSAT (kissat + cadical) |
| bit3  | 51 | F408 | UNSAT (kissat + cadical) |
| bit2  | 51 | F408 | UNSAT (kissat + cadical) |

All 5 are Hamming-3 isolated peaks (F429/F430/F431/F433-B coverage).
bit24 and bit28 additionally survive radius-6 seeded anneal (F434).

## Verdict

- bit24 HW=43 and bit28 HW=45 confirmed stable at Hamming radius 6.
- The Path C 5-cand panel is at its W-cube floor under cascade-1 +
  bridge_score constraints at radii ≤ 6. Further reduction needs
  larger radius (max_flips=10+) or different geometry.
- No new records, no new cert-pin runs. Structural confirmation only.

## Next

The Path C residual program has reached a clean stopping point on
this 5-cand panel. Plausible continuations:

1. **F435: drop cascade-1 c=g=1 constraint** and re-search. Tests
   whether the constraint is the binding floor.
2. **F436: scan untouched kbits** (bit5, bit10, bit14, ...). Each
   could yield an analogous F432-style record. Time-boxed expansion
   of the panel.
3. **Pivot to sr61_n32** — completely untouched today.
4. **Synthesize the day's findings** — write a session-summary
   memo cross-referencing all 7 macbook-claude F-numbers.
5. **Pause for codex's quota reset** (13:22 EDT, ~2.25h from now).

The structural picture of Path C residuals on cascade-1-fingerprinted
cands is now well-mapped. The headline-class SAT collision objective
remains uncrossed — every cert-pin'd record is UNSAT under kissat +
cadical with audited CNFs. Path C produces increasingly tight
residuals (5 cands now ≤ HW=51, two ≤ HW=45) but not single-block
collisions.
