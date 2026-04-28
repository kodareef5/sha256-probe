---
date: 2026-04-28
bet: block2_wang
fixtures: bit3_HW55, bit19_HW56_51ca0b34, bit28_HW59, bit4_HW63, bit25_HW62, msb_HW62_9cfea9ce
status: F143_FURTHER_FALSIFIED + STRUCTURAL_PATTERNS_OBSERVED
---

# F186: cross-cand chunk-0 floor map — distinguished cands all sit 5-8 points above bit3

## Setup

Yale's chunked-scan campaign produced bit19's chunk-0 floor (F134).
This memo extends to all 5 remaining distinguished cands. Each got a
chunk-0 scan (start_index=0, 64 size-5 masks, 3×4000 random restart).
Single seed per cand (multi-seed reproducibility deferred).

## Result table

| Fixture | Cand | Best mask (chunk-0, 3×4000) | Score | msgHW |
|---|---|---|---:|---:|
| bit3 | cand_n32_bit3_m17149975 (yale, multi-seed verified) | `0,1,2,8,9` | **86** | — |
| bit19 | cand_n32_bit19_m51ca0b34 (yale F134 seed 7034) | `0,1,2,7,15` | **90** | 56 |
| msb | cand_n32_msb_m9cfea9ce (F185 seed 8301) | `0,1,2,3,4` | **91** | 71 |
| bit28 | cand_n32_bit28_md1acca79 (F178 seed 8001) | `0,1,2,3,14` | **91** | 86 |
| bit4 | cand_n32_bit4_m39a03c2d (F183 seed 8101) | `0,1,2,8,12` | **93** | 64 |
| bit25 | cand_n32_bit25_m09990bd2 (F184 seed 8201) | `0,1,2,6,14` | **94** | 63 |

## Patterns

### 1. Universal `{0,1,2,*,*}` prefix
Every cand's chunk-0 winner has active words `{0, 1, 2}`. Two more
words vary by fixture. This is the lex-first portion of the size-5
enumeration (start_index=0..63), so this might partially be a search
artifact, but the SCORES still favor `{0,1,2,*,*}` — these masks
genuinely solve well across all cands.

### 2. Bit3 dominates all distinguished cands
At 3×4000 random-init budget:
- bit3: 86
- next-best: bit19 (90) — 4 points worse
- worst: bit25 (94) — 8 points worse

F143 hypothesis (distinguished cands have **better** fixture-local
optima) is **further falsified** at this budget. Five cands tested,
all sit above bit3 by ≥4 points. Pattern is consistent.

### 3. Distinguished-cand floor band: 90-94
The five distinguished cands span a 4-point band. This itself is
structure: a 4-point spread across 5 different fixtures suggests
the chunked-scan budget *does* discriminate cand-level differences
(it's not a flat noise floor across all cands).

But the discrimination places ALL distinguished cands ABOVE the
default bit3 cand. Whatever structural property bit3 has that
permits the 86 robust floor is *not* the same as
de58_size-below-median or hardlock_bits.

### 4. Terminal-pair fixture-specificity
Each cand's "last two words" of the best mask are different:
- bit3: (8, 9)
- bit19: (7, 15)
- msb: (3, 4) — adjacent indices, unique
- bit28: (3, 14)
- bit4: (8, 12)
- bit25: (6, 14)

Six cands, six different terminal pairs. Only `{0, 1, 2}` is
universal. The "right tail" of the active-word mask is genuinely
fixture-local.

### 5. msb's adjacent-word cluster
msb's chunk-0 top-2:
- rank 1: `{0,1,2,3,4}` — 5 consecutive indices
- rank 2: `{0,1,2,4,5}` — near-consecutive

No other cand has consecutive indices in its top-2. This may be a
structural signal of msb's distinct fixture geometry, but the score
is still 91 (worse than bit3's 86). One observation, weak signal.

## Implications for F143 hypothesis

F143: "distinguished cands (de58_size below median, hardlock_bits)
should have better fixture-local optima than bit3 due to structural
distinction."

Empirical status as of F186:

| Test | Result |
|---|---|
| bit19 chunk-0 random-init 3×4000 | 90 vs bit3's 86 → falsified by 4 |
| bit19 chunk-1 random-init 3×4000 | 91 (robust, F180) → falsified by 5 |
| bit19 F135-init 8×50k | 87 → falsified by 1 |
| bit28 chunk-0 random-init 3×4000 | 91 (robust, F182) → falsified by 5 |
| bit4 chunk-0 random-init 3×4000 | 93 → falsified by 7 |
| bit25 chunk-0 random-init 3×4000 | 94 → falsified by 8 |
| msb chunk-0 random-init 3×4000 | 91 → falsified by 5 |

**Five cands × multiple budgets, all falsify F143.** The hypothesis
that distinguished cands have better fixture-local optima is dead at
the chunked-scan random-init level.

What remains open:
- Could distinguished cands have *deeper* basins findable only with
  basin-init or a global method? (yale's F173 found 87 on bit19 via
  F135-init.) The "deepest known" basins on each cand:
  - bit3: 86 (random-init reproducible)
  - bit19: 87 (F135-init only)
  - bit28: 91 (random-init reproducible across seeds; deeper basin
    not yet found)
  - bit4/bit25/msb: 91-94 (single-seed; deeper basins not searched)
- The F143 hypothesis at the *basin-init* level is undertested.
  The structurally honest framing: "distinguished cands may have
  comparable or deeper basins than bit3, but they require basin-
  finding methods more powerful than random-init local search."

## What's NOT being claimed

- That distinguished cands lack deeper basins (might exist; not
  found at this budget).
- That bit3's 86 is the universal best (it might be beaten by
  basin-init or SAT on some distinguished cand).
- That F143 is dead globally (it's dead at random-init chunked-scan
  level only).

## Discipline

- 0 SAT compute (heuristic local search only)
- 0 solver runs
- Six fixtures × 64 masks × 3 restarts × 4000 iterations =
  ~5.5 million local search iterations total. ~6 min wall.

## Next-step priorities

1. **Multi-seed verification** on bit4/bit25/msb (currently single-
   seed). ~6 min wall total; would extend F182's robustness check
   to all distinguished cands.

2. **Basin-init cross-fixture test**: take bit3's score-86 message
   pair and use as init for chunk-0 on bit19/bit28/etc. Tests
   whether bit3's basin generalizes via basin propagation. If yes
   → cand-distinction may live elsewhere. If no → bit3's basin is
   genuinely cand-specific.

3. **Chunks 1-N on bit4/bit25/msb**: extend horizontal coverage to
   match bit19's depth. ~30-60 min wall per cand for chunks 1-3.

4. **Pause cross-cand chunked-scan campaign**: the F143 falsification
   at random-init budget is now strong (6 cands consistent). More
   chunked-scan probably won't reveal new structure; we need either
   basin-init protocol OR a non-local method (SAT, BDD).

## Headline-relevance check

We are hunting a "headline-worthy SHA-256 collision result". Today's
finding chain:
- F176/F179: random-init can't reach the F135 score-87 basin.
- F180: chunked-scan floors carry seed-uncertainty; bit19 robust
  floor is 91, not 87.
- F182/F186: distinguished cands are *worse* than bit3 at random-init.

This is **not** progress toward a headline. It is *honest negative
calibration*: the chunked-scan campaign's qualitative landscape is
flatter and noisier than the early F134/F135 results suggested. The
real attack-mechanism question is now sharper: how do we find a
sub-86 basin (or a deeper bit3-class basin on a structurally
distinguished cand) without already knowing where to seed?

The answer probably involves either:
- A novel basin-discovery protocol (basin-hopping, simulated tempering,
  or seeded global moves).
- A non-local method (SAT with structural constraints, BDD enumeration,
  IPASIR-UP propagator with active-word side-channel).

This is a productive recalibration, not a setback. Better to know
the chunked-scan ceiling at random-init is ~91 than to keep running
chunks expecting another 87.
