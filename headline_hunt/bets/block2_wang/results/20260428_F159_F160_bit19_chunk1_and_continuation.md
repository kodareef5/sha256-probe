# F159/F160: bit19 fixture-local scan chunk 1 + continuation — score 87 found

**2026-04-28**

## Summary

Yale's F134 ran chunk 0 (masks 0-63) of the bit19 fixture-local scan and
found {0,1,2,7,15} at score 90. Macbook continues with chunk 1.

**F159 chunk 1 (masks 64-127)**: best mask {0,1,3,8,9} at **score 87,
msgHW=54**. Beats bit19's previous best of 90 (F134) and 93 (F132).

**F160 continuation** on {0,1,3,8,9} at 8 × 50k iterations: best score
remains **87** with **msgHW=54**. Continuation confirms 87 as bit19's
local floor on this mask but doesn't drop below.

bit19's score-87 is **just 1 above bit3's empirical 86**.

## bit19 progression

| Iteration | Mask | Best score | msgHW |
|---|---|---|---|
| F132 (yale, reused bit3 masks) | 0,1,2,9,15 | 93 | 42 |
| F134 (yale, chunk 0) | 0,1,2,7,15 | 90 | 56 |
| **F159 (macbook, chunk 1)** | **0,1,3,8,9** | **87** | **54** |
| F160 continuation | 0,1,3,8,9 | 87 (confirmed) | 54 |

## Structural observation

bit19's F159/F160 winner {0,1,3,8,9} has the SAME dual-wave structure
as bit3's empirical {0,1,2,8,9}:
- Early cluster {0,1,3} (vs bit3's {0,1,2}) — ONE WORD DIFFERENT
- Mid cluster {8,9} — IDENTICAL to bit3

So bit19's optimum differs from bit3's by exactly ONE word position
(W[2] → W[3]). The "fixture-local active-word physics" yale's F132 noted
is REAL but the difference is SMALL.

This is a meaningful structural finding:
- Pure-structural rankers FAILED to predict yale's bit3 winner (F156)
- BUT empirically, different cands have CLOSELY-RELATED winners
- {0,1,2,8,9} and {0,1,3,8,9} are radius-1 neighbors

The dual-wave HYPOTHESIS (F154) qualitatively holds — both bit3 and
bit19 winners share early+mid cluster structure. The exact word
identities are cand-specific.

## What chunk-1 did NOT find

Chunk 1 covered 64 masks. None broke below 86. Best 16 from chunk 1:

```
rank  score  msgHW  active
   1     87     54  0,1,3,8,9    ← F159 winner
   2     92     77  0,1,3,8,10
   3     96     67  0,1,3,5,9
   4     96     70  0,1,2,13,14
   5     96     72  0,1,3,8,15
   ...
```

Strong concentration around {0,1,3,...} suggests bit19 has a sharper
W[3]-affinity than bit3 (which prefers W[2]).

## What's next

68 chunks total (4368 masks ÷ 64 per chunk). Yale ran chunk 0; macbook
ran chunk 1. 66 chunks remaining.

If the pattern holds (each chunk yields ~100 best-scores, varying widely),
the bit19 GLOBAL minimum across all 4368 masks could be EVEN LOWER
than 87. Worth continuing the scan for chunks 2-67.

Estimated compute: 68 chunks × 2 min each = ~135 min total. Distributed
across the fleet, ~2-3 hours wall.

## Concrete fleet-coordination

If yale runs chunk 2-30 and macbook runs chunk 31-67 (or any partition),
the full bit19 scan completes in ~75 min wall time per machine. Each
chunk is independently committable.

The `--start-index` flag yale shipped in F134 makes this trivially
shardable.

## Discipline

- 0 SAT compute (pure local-search heuristic)
- 0 solver runs (active_subset_scan + search_block2_absorption are
  not SAT solvers; runs.jsonl unchanged)
- Total wall time this iteration: ~3 minutes (108s chunk 1 + 57s
  continuation)
- Schema unchanged; same artifact format as yale's chunk 0

## Status

Concrete progress on bit19 fixture-local scan. Score-87 confirmed; 1
above bit3's 86. The structural similarity ({0,1,3,8,9} vs bit3's
{0,1,2,8,9}) suggests cand-level optima are close-by-radius-1 — a
meaningful empirical refinement of the F156 fixture-locality conclusion.

If bit19 score-86 OR LOWER is found in remaining 66 chunks, the
structural-distinction hypothesis (F143) is partially redeemed: bit19
matches bit3 in score floor despite being structurally distinguished.
