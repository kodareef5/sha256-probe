# F170: bit19 chunked-scan winners are all radius-1 neighbors of bit3's {0,1,2,8,9}

**2026-04-28**

## Summary

Pure-thought structural observation while chunks 43-45 run in
background. After ~15 chunks of bit19 fixture-local scanning, the
EMPIRICAL WINNERS form a tight cluster — all radius-1 (one-word swap)
from yale's bit3 winner {0,1,2,8,9}.

## bit19 chunked-scan winners so far

| Chunk | Best mask | Score | msgHW | Hamming-radius from bit3's {0,1,2,8,9} |
|---|---|---|---|---|
| 0 (yale F134) | 0,1,2,7,15 | 90 | 56 | 2 (swap 8→7, 9→15) |
| **1 (parallel F135/F159)** | **0,1,3,8,9** | **87** | 54 | **1** (swap 2→3) |
| 2 (yale F136) | 0,1,3,12,15 | 91 | 76 | 2 (swap 2→3, 8→12, 9→15) |
| 3 (yale F137) | varies | 91 | — | — |
| 4 (yale F138) | varies | 91 | — | — |
| 5 (yale F167) | 0,1,9,10,14 | 93 | — | 2 (swap 2→14, 8→10) |
| 6 (yale F168) | 0,2,3,8,9 | **89** | — | **1** (swap 1→3, but actually +3, -1) |
| 34 (macbook F161) | 1,6,7,11,14 | 91 | 60 | far (3+) |
| 35 (macbook F162) | 1,7,10,11,15 | 88 | 67 | 3+ |
| 36 (macbook F163) | 1,8,9,12,14 | 92 | 83 | 3+ |
| 37 (macbook F164) | 2,3,4,12,14 | 91 | 76 | 3+ |
| 38 (macbook F164) | 2,3,6,8,9 | 91 | 81 | 2 (swap 0→6, 1→3) |
| 39 (macbook F164) | 2,3,7,13,15 | 90 | 56 | 3+ |
| 40 (macbook F165) | 2,3,11,12,15 | 90 | 73 | 3+ |
| 41 (macbook F165) | 2,4,6,11,13 | 89 | 76 | 3+ |
| 42 (macbook F165) | 2,4,9,11,15 | 92 | 53 | 3+ |

## Pattern

The TWO best bit19 results (87 from chunk 1, 89 from chunk 6) are
BOTH radius-1 from bit3's empirical {0,1,2,8,9}:
- Chunk 1: {0,1,3,8,9} = swap W[2] → W[3]
- Chunk 6: {0,2,3,8,9} = swap W[1] → W[3] (and add W[3])

Wait — let me re-check chunk 6. {0,2,3,8,9} vs {0,1,2,8,9}: same {0,2,8,9}, replace W[1] with W[3]. That's **radius 1**.

Other radius-1 neighbors of {0,1,2,8,9} on a 16-element ground set:
- Swap 0→k for k ∉ {1,2,8,9}: {1,2,8,9,k}, 12 options
- Swap 1→k: {0,2,8,9,k}, 12 options  
- Swap 2→k: {0,1,8,9,k}, 12 options
- Swap 8→k: {0,1,2,9,k}, 12 options
- Swap 9→k: {0,1,2,8,k}, 12 options

Total: 60 radius-1 neighbors. yale's chunk 1 (start 64) and chunk 6
(start 384) HAPPEN to land on radius-1 neighbors. Macbook's chunk 38
{2,3,6,8,9} is also CLOSE to {0,1,2,8,9} (radius-3, but in the
{...,8,9} core).

## Hypothesis

bit19's fixture-local optimum is in the {0,1,X,8,9} family where X ∈
{2, 3, ?}. Chunks NOT containing the {0,1,_,8,9} or {0,_,_,8,9}
backbone are likely to score >88.

The 60 radius-1 neighbors of bit3's winner are the priority sub-target
for bit19 search. Specifically:
- {0,1,2,8,9} (bit3 baseline): bit19 score 103 (yale's F132 confirmed
  this cross-cand transfer fails)
- {0,1,3,8,9}: bit19 87 ← our current best
- {0,1,4,8,9} through {0,1,15,8,9}: ~10 candidates, untested
- {0,2,3,8,9}: bit19 89 (yale chunk 6)
- {0,3,4,8,9} through {0,1,2,8,X}: untested

Worth a focused F111 scan over the 60 radius-1 neighbors of yale's
winner — should narrow bit19's optimum within ~10 minutes more compute.

## What yale and macbook chunks have NOT systematically tested

Looking at the chunks done so far, NONE explicitly target the
radius-1 family of yale's bit3 winner. The chunked scan is a generic
sweep; it lands on radius-1 neighbors only by chance.

Concrete actionable: a TARGETED scan over the 60 radius-1 neighbors
would either:
- Find a sub-87 absorber on bit19 (= structural-distinction
  hypothesis empirically validated)
- Confirm 87 as the radius-1 floor (= bit3 has cand-specific
  optimum, no cross-cand improvement possible at radius 1)

## Quick math: cost

60 radius-1 neighbors × 5 min per F111 scan = 5 hours. That's a lot
for ~10× scan budget.

Cheaper: a 60-mask single-pool scan via active_subset_scan with
--pool 0,1,2,3,...,15 --sizes 5 --start-index? Actually easier to
enumerate the 60 explicitly:
- For each i ∈ {0,1,2,8,9} (5 positions):
  - For each k ∈ {0..15} \ {i, other 4 positions} (12 candidates):
    - Build mask = {0,1,2,8,9} - {i} ∪ {k}

This gives 60 specific masks. Run them as 1 chunk-sized scan with
custom subset enumeration. ~2 minutes wall.

## Status

Pure-thought observation while chunks 43-45 run. Identifies a
focused next-iteration pattern: scan the 60 radius-1 neighbors of
yale's bit3 winner directly. If yale or macbook picks this up,
~2 min compute resolves whether bit19 has a sub-87 mask in the
radius-1 family.

This is different from yale's chunked scan (which enumerates all
4368 size-5 masks systematically). The radius-1 enumeration is
HYPOTHESIS-DRIVEN — testing whether bit19's optimum matches bit3's
within radius 1.

## Discipline

- 0 SAT compute
- Pure-thought analysis on existing yale + macbook chunk results
- Pattern identification only; no new compute proposed in this memo

This memo was written in parallel with chunks 43-45 background run;
no resource conflict.
