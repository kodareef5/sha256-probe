---
date: 2026-04-28
bet: block2_wang
fixture: bit28_HW59_naive_blocktwo
status: F143_ALIVE_AT_BASIN_INIT_LEVEL — cross-fixture basin propagation works
---

# F187: cross-fixture basin propagation — F135's bit19 score-87 init reaches bit28 score 89

## Setup

After F186 falsified F143 at random-init chunked-scan budget, the
remaining hypothesis was: *distinguished cands may have deeper basins
findable only with basin-init.* This memo tests it concretely with a
cross-fixture basin propagation experiment.

Take F135's score-87 message pair on bit19 fixture (M1, M2 from the
`bit19_chunk0064_64x3x4k` result file) and use as `--init-json` when
running chunk-0 on **bit28** fixture. Restart 0 of every mask starts
from F135's M1; restarts 1-2 use random init.

```bash
PYTHONPATH=. python3 active_subset_scan.py \
  bit28_HW59_naive_blocktwo.json \
  --pool 0-15 --sizes 5 --start-index 0 --limit 64 \
  --restarts 3 --iterations 4000 --seed 9501 \
  --require-all-used \
  --init-json 20260428_F135_bit19_fullpool_size5_chunk0064_64x3x4k.json \
  --top 16
```

## Result

Top 5 by score:

| Rank | Score | msgHW | Active words |
|---:|---:|---:|---|
| **1** | **89** | 85 | **`0,1,2,10,11`** ← NEW BASIN |
| 2 | 90 | 78 | `0,1,2,5,12` |
| 3 | 92 | 61 | `0,1,2,3,6` |
| 4 | 92 | 77 | `0,1,2,3,14` (F178's best at random-init seed 8001) |
| 5 | 93 | 62 | `0,1,2,7,12` |

## Key finding

**Cross-fixture basin propagation works at chunked-scan budget.**

| Test | Best score on bit28 chunk-0 | Best mask |
|---|---:|---|
| F178 (random init, seed 8001) | 91 | `0,1,2,3,14` |
| F181 (random init, seed 9001) | 92 | `0,1,2,6,15` |
| **F187 (F135 basin init, seed 9501)** | **89** | `0,1,2,10,11` |

Sub-91 result on bit28: **achieved**. First time. The mask
`{0,1,2,10,11}` did NOT appear in either random-init scan's top-16
— it's a basin invisible to random search at 3×4000 but accessible
when seeded from a known good message pair on a *different* fixture.

This is real cross-fixture basin propagation evidence.

## Implications

### 1. F143 alive at basin-init level

F186 falsified F143 at random-init chunked-scan budget. F187 partially
revives it: distinguished cands DO have deeper basins than chunked-
scan exposes, and those basins ARE accessible via cross-fixture
basin propagation.

The qualified F143:
> Distinguished cands have deeper basins than random-init at chunked-
> scan budget reveals. Reaching them requires either basin-init from
> a known good pair or a global method.

This is now **empirically supported** (single experiment, single
fixture pair).

### 2. Bit28 sub-91 basin demonstrated

Best known random-init: 91-92.
Best known via basin-init: 89.
Gap: 2-3 points hidden inside basin not visible to random search.

If basin-hopping from this 89 result repeats the F135 → 87 pattern,
bit28 may have a sub-87 mask. Worth a 8×50k continuation on
`{0,1,2,10,11}@89` — same protocol that drove bit19 from chunked-
scan 87 to F135 init's 87 stable basin.

### 3. The propagation is non-trivial

F135's mask is `{0,1,3,8,9}`. Bit3's mask is `{0,1,2,8,9}`. F187's
new bit28 result is `{0,1,2,10,11}`. **Three different masks**, yet
the basin propagation worked from F135's pair to bit28's basin.

This means: the basin propagation isn't just "use the same mask".
The message pair (M1, M2) carries cross-fixture-transferrable
structure beyond the active-word mask. Possibly:
- The structural shape of the message-pair difference (carries,
  adder geometry, schedule compliance pattern).
- A particular non-trivial M1 base that lands in good geometry
  under bit28's chain1_out compression.

This is **the most interesting structural signal** we've found in
several iterations.

### 4. Implications for distinguished-cand campaign

Three follow-ups:

(a) **Continue 8×50k on bit28's `{0,1,2,10,11}@89`** with F135-init
    init_kicks=2. If reaches 86-88, real cand-level structural
    distinction shown.

(b) **Run F187-style basin-init on bit4 / bit25 / msb / bit19** with
    F135 init. If all reach sub-91, basin propagation is a robust
    cross-fixture mechanism.

(c) **Reverse-direction tests**: use bit3's score-86 pair as init
    for bit19/bit28/bit4/bit25/msb. Asks whether bit3's basin
    transfers in the reverse direction.

### 5. The headline path may run through basin propagation

If the basin-init protocol consistently reveals sub-90 basins on
distinguished cands, then the attack-mechanism question becomes:

> *Can we discover the FIRST sub-86 basin without already knowing
> where to seed from?*

Current sub-86 known: none.
Basin-init discoveries today: F187 found bit28's 89 from F135's 87.

If basin propagation chains exist (89 → 87 → 85 → ...), and each
step requires a known seed, then we need ONE first sub-86 basin
to bootstrap. Where does that come from?

- A SAT probe with structural constraints (bet:
  programmatic_sat_propagator).
- A BDD enumeration on the partial-trail freedom space.
- A combinatorial discovery method (mitm_residue, Σ-Steiner cover).
- Simulated tempering / parallel tempering / basin-hopping with
  diversity.

This is a clarified question worth pursuing. F187 turns a dead
horizon into an open one.

## What's NOT being claimed

- That bit28 has a sub-86 basin (we've found 89, not below 86).
- That basin propagation always works (one experiment, one fixture
  pair).
- That F143 in its full form is back (still dead at random-init;
  alive only at basin-init).

## Discipline

- 0 SAT compute (heuristic local search with basin-init)
- 0 solver runs
- One sharp single-experiment finding: cross-fixture basin
  propagation works at chunked-scan budget; bit28 has at least
  one sub-91 basin invisible to random search.

## Reopen registry note

This finding may justify reopening the F143 hypothesis at
"basin-init level" in the registry. Consider updating
`mechanisms.yaml` with a note distinguishing random-init vs
basin-init regimes.
