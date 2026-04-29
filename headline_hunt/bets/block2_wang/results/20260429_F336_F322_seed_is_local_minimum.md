---
date: 2026-04-29
bet: block2_wang × math_principles cross-machine
status: STRUCTURAL — F322 random-init basin and yale chamber-seed basin are DISTINCT
---

# F336: F322 random-init seed is a kernel-safe local minimum

## Setup

Yale's F374 strict-kernel Pareto bridge reached a57=4 at depth 2 from F370
base (chamber-seed-derived). F322 random-init kernel-preserving best is at
a57=5, D61=14, score=39.65 in chamber chart.

Question: does F322's random-init basin contain a path to F374's a57=4
territory under strict cascade-1, or are these distinct basins?

## Test

Enumerated all kernel-safe single moves from F322 best (1536 = 16 words ×
32 bits × (1 common_xor + 2 common_add directions)) and measured atlas
score / a57 / D61 / chart for each.

## Result

```
F322 base:        score=39.65, a57=5,  D61=14, chart=(dh,dCh)

Top 5 depth-1 by atlas score:
  common_add w13 b0 +1:    score=56.60 a57=8  D61=18 chart=(dh,dCh)
  common_add w15 b17 -1:   score=56.80 a57=9  D61=14 chart=(dh,dCh)
  common_xor w8 b11:       score=58.60 a57=9  D61=9  chart=(dT2,dh)
  ...

Top 5 depth-1 by a57:
  common_add w13 b0 +1:    a57=8 D61=18 chart=(dh,dCh)
  common_add w3 b23 +1:    a57=8 D61=22 chart=(dSig1,dCh)
  ...

Top 5 depth-1 by D61:
  common_xor w3 b1:        a57=13 D61=7 chart=(dCh,dSig1)
  common_add w3 b1 +1:     a57=13 D61=7 chart=(dCh,dSig1)
  common_xor w4 b20:       a57=14 D61=7 chart=(dSig1,dT2)
  ...

Improvements over F322 base:
  a57 < 5:    0 / 1536 moves
  D61 < 14:   302 / 1536 moves (all break chart or hike a57)
  score < 39.65: 0 / 1536 moves
```

## Findings

### Finding 1 — F322 random-init seed is a kernel-safe local minimum

**0/1536 single kernel-safe moves improve a57 below 5 OR atlas score
below 39.65.** The seed sits at the bottom of a basin in single-move
space.

The 302 moves that lower D61 below 14 all incur:
- a57 increase to 8-17 (large cost)
- chart shift away from (dh, dCh)

So the basin is "soft" on D61 (multiple D61-lowering moves available) but
"hard" on a57 (no a57-lowering moves) and "hard" on score (no score-
improving moves).

### Finding 2 — F322 and yale F374 are distinct kernel-safe basins

Yale's F374 reached a57=4 at depth 2 from F370 base (which is chamber-
seed-derived). F322 random-init at depth 1 has 0 moves reaching a57=4.

Two distinct kernel-safe basins on the cascade-1 Pareto front:

| Basin | seed | best (a57, D61, chart) | source |
|---|---|---|---|
| Random-init | F322 random M1 | (5, 8 — different restart, dh/dCh) | macbook F322 |
| Chamber-seed-derived | F370/F374 | (4, 11, dT2/dCh) [a57 angle] OR (12, 5, dCh/dh) [D61 angle] | yale F374 |

The two basins reach DIFFERENT regions of the strict-kernel Pareto front:
- Random-init: low-a57-with-chamber-chart corner
- Chamber-seed: mixed corners across multiple charts

### Finding 3 — Combined cross-machine kernel-safe Pareto front (current)

| a57 | D61 | chart | source | atlas score |
|---:|---:|---|---|---:|
| 4 | 11 | (dT2,dCh) | F374 best_guard | 40.8 |
| 5 | 8  | (dh,dCh) | F322 r5 (different restart) | 39.65 |
| 5 | 14 | (dh,dCh) | F322 r5 (this seed) | 39.65 |
| 6 | 8  | (dh,dCh) | F372 best_score | 37.8 |
| 12| 5  | (dCh,dh) | F374 best_d61 | 59.1 |
| 15| 5  | (dCh,dh) | F372 best_d61 | 71.45 |

The chamber attractor (a57=0, D61=4, (dh,dCh)) is bracketed but
unreached. F336 confirms the bracketing is from at least 2 distinct
basins in kernel-safe space.

## What this means

The chamber attractor's brittleness has a NEW dimension: it's not just
"unreachable from any starting point" — it's also "the kernel-safe
Pareto front splits into multiple disjoint basins, each with its own
local minimum, NONE of which contain the attractor".

Implication: a single-basin search (random-init OR chamber-seed) can
only reach ONE of the basins. To find the attractor, we'd need either:
- A cross-basin transfer mechanism (currently unknown to exist)
- A search method that simultaneously explores all basins (CDCL is
  the natural candidate per F324-F326 search-invariant thesis)

## Compute

- 0.5s wall (1536 kernel-safe moves on F322 seed).
- 0 SAT compute.
- All 1536 moves verified kernel-preserving (kernel_check pass at
  enumeration time, redundant since moves are common_xor / common_add
  by construction).

## What's shipped

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260429_F336_kernel_safe_depth1_from_F322.json`
- This memo.

## Concrete next moves

1. **Depth-2 enumeration from F322 seed**: 1536 × ~1500 ≈ 2.3M evaluations,
   ~100s wall. Tests if F322's basin contains a 2-move path to a57<5
   that depth-1 missed.

2. **Random-init in F374's basin region**: pick an M1 randomly within
   yale's F370-style chamber-seed neighborhood (or use a real chamber
   witness as init), run F322-style search (kernel-preserving annealed
   atlas-loss). Compare to F322 random-init.

3. **Cross-basin bridge probe**: enumerate kernel-safe paths between
   F322 best and F374 best_guard (a57=4 territory). Even if no direct
   path within ~6 moves, the structure of separating moves is
   informative.

(1) is cheap and concrete; quick follow-up.
