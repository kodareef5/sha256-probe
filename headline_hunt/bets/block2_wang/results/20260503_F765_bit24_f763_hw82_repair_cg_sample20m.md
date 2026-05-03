---
date: 2026-05-03
bet: block2_wang
status: BIT24_F763_HW82_REPAIR_CG_SAMPLE20M_NEGATIVE
parent: F764 top-80 pair-potential atlas
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F765: bit24 F763 HW82 repair/cg 20M sampled combo

## Setup

F765 tests the hypothesis suggested by F760 and F763 source analysis: productive
HW82 compositions are built from ugly repair pairs, not target-only lane-copying
pairs.

It starts from the F763 HW82 tie and uses the F764 top-80 atlas with target
pairs disabled.

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [7, 10, 12, 16, 11, 7, 8, 11]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 18
init c/g objective: 122
```

Selection:

```text
target pairs = 0
repair pairs = 80
HW pairs = 20
c/g pairs = 40
per-register repair pairs = 10
selected pairs = 182
pair_count = 5
radius = 8..10
sampled combos = 20,000,000
rng seed = 765
```

## Result

```text
candidate combos: 20,000,000
evaluated: 19,872,172
skipped duplicate: 127,105
HW < 82: 0
HW <= 82: 0
c/g-improving: 0
target-L1-improving: 250
wall seconds: 2890.51
```

Best raw-HW sample:

```text
HW 86
target L1 18
c/g objective 128
lane [10, 10, 10, 7, 13, 12, 11, 13]
bits [12, 56, 72, 125, 158, 206, 227, 309, 339, 396]
```

Best target-L1 sample:

```text
HW 88
target L1 10
c/g objective 132
lane [12, 11, 11, 12, 9, 10, 11, 12]
bits [8, 15, 68, 140, 179, 213, 239, 289, 341, 437]
```

Best c/g sample:

```text
HW 95
c/g objective 123
target L1 29
lane [11, 15, 6, 13, 12, 19, 8, 11]
```

## Interpretation

This is a meaningful negative for the widened repair/cg branch around the F763
HW82 tie. The sampled selector was much broader than F763's exact 76-pair
target/repair set:

```text
F763 selected pairs: 76 exact, 18.47M combos, found one HW82 tie
F765 selected pairs: 182 sampled, 19.87M evaluated, found zero HW82 ties
```

The result does not falsify repair-composition geometry globally, because the
sample is a tiny slice of the 182-choose-5 space. It does say the F763 tie is a
tight endpoint under this obvious widened repair/cg sampler. The best target
sample reached L1 10, but paid HW82 -> HW88, so the geometry can still move
without preserving the current floor.

## Next

Do not spend the next run on another blind widening of the same F763 repair/cg
sample. Better options:

1. Use the best F765 target detour (HW88, target L1 10) as a deliberate repair
   seed for a standard pair-beam restart.
2. Return to the original F760 HW82 point and run a top-80 repair/cg sampler
   there, because F761 had 54 target-improving pairs versus only 5 around F763.
3. Try a two-stage operator: sample detours by target L1, then repair each
   detour with a short beam rather than requiring the sampled final state to be
   low-HW immediately.
