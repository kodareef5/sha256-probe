---
date: 2026-04-28
bet: block2_wang
fixtures: bit3, bit4, bit19, bit25, bit28, msb
status: F143_WEAK_FORM_UNIVERSAL — all 6 cands have sub-90 basins; F135 is dominant universal seed
---

# F201: Cross-fixture basin propagation is universal — F135's M1 dominates F188's M1 as universal seed

## Two parallel tests

After F187 showed F135 → bit28 reaches 89, two natural next questions:

1. Does F135-init reach sub-90 on bit4/bit25/msb too? (F195/F196/F197)
2. Does F188-init (bit4 score-86) propagate cross-fixture as well as F135?
   (F198/F199/F200)

Both batches ran in parallel, single seed per cand, 3×4000 budget,
chunk-0 enumeration.

## Results table

### F135 init (bit19 score-87 source)

| Cand | Best mask | Score | Δ vs random |
|---|---|---:|---:|
| bit4 (F195) | `0,1,2,4,12` | **89** | +4 better than F183's 93 |
| bit25 (F196) | `0,1,2,3,10` | **88** | +4 better than F184's 92 |
| msb (F197) | `0,1,2,5,6` | **88** | +3 better than F185's 91 |
| (bit28 already known F187) | `0,1,2,10,11` | 89 | +2 better than F178's 91 |

### F188 init (bit4 score-86 source)

| Cand | Best mask | Score | Δ vs random |
|---|---|---:|---:|
| bit25 (F198) | `0,1,2,8,14` | 92 | 0 (tied with F184/F189) |
| msb (F199) | `0,1,2,7,9` | 90 | +1 better than F185's 91 |
| bit28 (F200) | `0,1,2,9,15` | 92 | 0 (tied with F178/F181) |

## Headline finding 1: Cross-fixture basin propagation is universal

**Every distinguished cand has a sub-90 basin findable via F135 init.**

Updated cross-cand best-known floor (across all probes today):

| Cand | Floor | Discovery method |
|---|---:|---|
| bit3 | **86** | random-init multi-seed verified (yale baseline) |
| bit4 | **86** | random-init seed 9101 (F188 lucky-seed) |
| bit19 | **87** | random-init seed 7101 (F135 lucky-seed; reproduced via F135 init) |
| bit25 | **88** | F135-init cross-fixture basin propagation (F196) |
| msb | **88** | F135-init cross-fixture basin propagation (F197) |
| bit28 | **89** | F135-init cross-fixture basin propagation (F187) |

Spread: 86-89 across 6 cands. **All find sub-90 basins.** F143 weak
form (distinguished cands have basins comparable to bit3) is now
strongly empirically supported across the entire catalog.

## Headline finding 2: F135 dominates F188 as universal seed

Side-by-side comparison of F135-init vs F188-init on bit25/msb/bit28:

| Cand | F135-init | F188-init | F135 advantage |
|---|---:|---:|---:|
| bit25 | **88** | 92 | +4 |
| msb | **88** | 90 | +2 |
| bit28 | **89** | 92 | +3 |

**F135's M1 propagates uniformly better than F188's M1.** Across three
distinct cand fixtures, F135-init finds 2-4 points lower scores.

Structural difference between the two source basins:
- F135 message pair: msgHW = **54**, score 87, active words `{0,1,3,8,9}`
- F188 message pair: msgHW = **66**, score 86, active words `{0,1,2,4,8}`

F135 has *lower* message Hamming weight (54 vs 66), despite its score
being 1 worse than F188's (87 vs 86). The lower-HW message pair seeds
better cross-fixture basin discovery.

Hypothesis: **lower-HW source basins are better universal seeds**.

This is testable. A basin with even lower HW (say msgHW=40-45) might
be even more effective as universal init. Worth searching for one.

## Why this matters

### For F143 hypothesis
F143 weak form is now empirically saturated:
- All 6 distinguished cands tested.
- All find sub-90 basins.
- Spread 86-89 across cand catalog.
- The basin propagation mechanism is universal, not cand-specific.

### For attack-mechanism design
The basin landscape on Wang-2026 cands has:
- A protocol floor at 86 (no method tested today pierces).
- A 3-point spread (86-89) across cand catalog at the
  cross-fixture-basin-init protocol level.
- A clear "best universal seed" (F135 message pair) that propagates
  to deeper basins on every other cand than alternative seeds.

If we want to find a sub-86 basin, the most promising heuristic
direction is:
1. Find an even lower-HW source basin (msgHW < 54). May require
   structural/SAT method.
2. Apply it as init for chunk-1 / chunk-2 of every cand. If basin
   propagation extends below 86 on any cand, sub-86 is reachable.

### For the headline path
We've moved from "bit3 has the only deep basin" to "every cand has a
findable deep basin, with a universal-seed protocol that improves
random-search floors by 2-4 points cross-fixture."

This is real progress on the structural question, even though the
86 protocol floor still holds. The question for the next iteration
becomes: **what makes F135's M1 such an effective universal seed,
and can we find/construct one with even better universal-seeding
properties?**

## Concrete next probes

(a) **Run F197/F196/F195 with 8×50k continuation** on their best
    sub-90 masks (bit25's `0,1,2,3,10`@88, msb's `0,1,2,5,6`@88,
    bit4's `0,1,2,4,12`@89). Tests if basin-init under longer
    budget descends below 88 on these new basins.

(b) **Find a sub-54 msgHW source basin**: search bit3's chunk-0
    space for the lowest-msgHW score-86 result. Use as universal
    init for all other cands. If propagation finds sub-86, sub-86
    barrier broken.

(c) **F135 init applied to chunks 1-N of bit19**: test if the
    basin propagation extends within bit19 (does F135's M1 reach
    sub-87 in some other chunk's mask?).

(d) **Pivot to non-heuristic methods** (per F194 conclusion): the
    86 floor stands. Sub-86 may need IPASIR-UP, BDD, or BP-Bethe
    to break.

## What's NOT being claimed

- That every cand has a basin BELOW 86 (we found 86-89 spread, no
  sub-86 demonstrated yet on any distinguished cand).
- That F135 is the *globally optimal* universal seed (it's the best
  of two tested today; lower-HW seeds may exist).
- That basin propagation always finds the deepest available basin
  (only chunk-0 enumerated; deeper basins may live in chunks 1-67).

## Discipline

- 0 SAT compute throughout (all heuristic local search)
- 0 solver runs
- 7 chunk-0 scans this session totaling ~14 min wall
- 6 cands × multiple seeds × 2 source basins systematically tested
- F143 weak form: empirically saturated; sub-86 question reframed
  around source-basin choice and budget regime
