# F154: Dual-wave injection hypothesis — what yale's empirical {0,1,2,8,9} has that rankers miss

**2026-04-28**

## Summary

After two iterations of structural rankers (F150 raw density + F152
refined composite + yale's F129 concentration ranker), yale's empirical
score-86 winner {0,1,2,8,9} is consistently ranked LOW (134, 107, 192
in different rankers).

The pure expansion-structural rankers MISS what makes {0,1,2,8,9}
special. F154 proposes a hypothesis: **dual-wave temporal injection**.

## The pattern

{0,1,2,8,9} can be decomposed as:
- **Early cluster**: {0, 1, 2} — three consecutive words feeding
  early expansion rounds (W[16..18] via direct_t16; W[15..17] via σ_0
  but those are below i=16 so they don't apply)
- **Mid cluster**: {8, 9} — two consecutive words feeding mid
  expansion rounds (W[23..25] via direct_t16; W[15..16] via direct_t7)

The gap from 2 to 8 is 6, NOT in the expansion offset set {2, 7, 15, 16}.
This means the two clusters are **DECOUPLED** in expansion-recurrence
terms — they inject into different downstream-round bands.

## Hypothesis

Yale's absorber search at score 86 works because cascade-1's d63=h63=0
forcing has TWO TEMPORAL ATTRACTORS:
1. Early (rounds 16-23): driven by {0,1,2}
2. Mid (rounds 23-30 ish): driven by {8,9}

The absorber's role is to ABSORB the cascade-1 residual. With dual-
wave injection, the absorber has TWO WAVES of message-diff to work
with, providing redundancy and allowing it to find a stable score-86
configuration.

Pure overlap-density rankers measure SINGLE-target concentration,
missing the dual-wave structure. Yale's concentration ranker
measures W[16] fan-in, missing the SECOND wave at W[23].

## Testable predictions

If dual-wave is the right framework:

1. **Other dual-cluster patterns** like {0,1,7,8,15} or {1,2,3,9,10}
   should also yield low scores, comparable to yale's 86.
   - {0,1,7,8,15}: early {0,1}, mid {7,8}, late {15}
   - {1,2,3,9,10}: early {1,2,3}, mid {9,10}
   - {2,3,8,9,15}: early {2,3}, mid {8,9}, late {15}

2. **Single-cluster patterns** like {0,1,2,3,4} (consecutive early
   only) or {8,9,10,11,12} (consecutive mid only) should NOT reach
   score 86 — only one wave.

3. **No-gap patterns** like {0,1,2,3,8} (early+late but with
   3→8 gap of 5) should be intermediate.

## Why pure rankers miss this

Single-target rankers measure how concentrated active words are at
ONE downstream W[i]. Dual-wave measures how concentrated they are at
TWO BANDS of downstream rounds, with appropriate gap.

For {0,1,2,8,9}:
- W[16] gets 3 feeders (W[0] direct, W[1] σ_0, W[9] direct_t7)
- W[24] gets 2 feeders (W[8] direct, W[9] σ_0)

The W[16]-W[24] PAIR is the dual-wave signature. Single-target
rankers see W[16]-only.

A composite ranker should reward subsets with HIGH FAN-IN AT TWO
BANDS, not one.

## Concrete experiment

Yale could test:
- **{0,1,7,8,15}**: predicted low score (dual-wave + late)
- **{2,3,8,9,15}**: predicted low score (dual-wave variant)
- **{0,1,2,3,4}**: predicted high score (single-wave control)
- **{8,9,10,11,12}**: predicted high score (single-wave control)

Estimated yale-side compute: ~25 min for 4 active subset scans.

## Connection to project's principles framework

The dual-wave hypothesis maps onto SYNTHESIS_iwasawa_pipelines.md
(april28_explore/principles/) where SHA-256's a-pipeline and
e-pipeline are Z₂-towers. Each pipeline absorbs cascade-1 forcing
through DIFFERENT temporal regimes:
- a-pipeline (a→b→c→d): rounds 60-63 forcing → backward absorption
  through round-shift  
- e-pipeline (e→f→g→h): rounds 60-63 forcing → similar but offset

The "early" cluster {0,1,2} drives a-pipeline mid-rounds; the "mid"
cluster {8,9} drives e-pipeline. Two independent absorption channels.

This structural reading makes dual-wave a NATURAL PREDICTION of the
Iwasawa-pipeline framework.

## Discipline

- 0 SAT compute
- 0 solver runs
- Pure-thought hypothesis on yale's F129/F130 negative result
- No new probe code; references existing analyses

## Status

Hypothesis proposed for yale's empirical {0,1,2,8,9} score-86 lane.
Testable via 4 controlled experiments (~25 min yale compute).

The macbook ↔ yale loop is now at iteration 3:
- F150 (macbook): raw density prediction
- F128 (yale): falsified simple density
- F152 (macbook): refined composite metric
- F129/F130 (yale): tested refined, also misses winner
- F154 (this memo, macbook): dual-wave hypothesis — what
  pure-structural metrics miss

If F154 holds: dual-cluster patterns should yield score floors
comparable to {0,1,2,8,9}'s 86. If not: yale's winner has yet
another hidden feature (perhaps cand-specific).
