---
date: 2026-05-03
bet: block2_wang
status: BIT24_F760_HW82_REPAIR_CG_SAMPLE20M_NEGATIVE
parent: F767 top-80 pair-potential atlas
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F768: bit24 F760 HW82 repair/cg 20M sampled combo

## Setup

F768 repeats the F765 broad repair/cg sampled combo, but from the original
F760 HW82 point. This tests whether F765's negative was specific to the tighter
F763 HW82 tie.

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [9, 10, 11, 10, 10, 13, 13, 6]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 24
init c/g objective: 130
```

Selection:

```text
target pairs = 0
repair pairs = 80
HW pairs = 20
c/g pairs = 40
per-register repair pairs = 10
selected pairs = 173
pair_count = 5
radius = 8..10
sampled combos = 20,000,000
rng seed = 768
```

## Result

```text
candidate combos: 20,000,000
evaluated: 19,836,163
skipped duplicate: 163,338
HW < 82: 0
HW <= 82: 0
c/g-improving: 48
target-L1-improving: 10,634
wall seconds: 2977.48
```

Best raw-HW sample:

```text
HW 85
target L1 13
c/g objective 129, delta -1
lane [14, 11, 10, 13, 7, 6, 12, 12]
bits [58, 93, 152, 178, 236, 281, 372, 396, 420, 505]
```

Best target-L1 sample:

```text
HW 91
target L1 9
c/g objective 135
lane [10, 13, 11, 13, 9, 10, 11, 14]
bits [37, 101, 105, 164, 266, 391, 432, 437, 439, 511]
```

Best c/g sample:

```text
HW 87
c/g objective 117, delta -13
target L1 13
lane [10, 13, 7, 15, 10, 10, 8, 14]
```

## Interpretation

F768 is negative on the floor, but it cleanly distinguishes the two HW82
parents:

```text
F765 from F763 HW82: 250 target improvements, best HW86, best target L1 10/HW88
F768 from F760 HW82: 10,634 target improvements, best HW85, best target L1 9/HW91
```

So the original F760 HW82 point has far more lane-geometry slack than the F763
tie. But the broad repair/cg sampler still could not preserve HW82, much less
break it. The best F768 sample re-enters an HW85 surface with better target L1
and slightly better c/g than the original bit24 HW85 lineage, which may be
worth one repair-beam check.

## Next

Run a standard pair-beam repair check from the F768 best-HW sample:

```text
HW85, target L1 13, c/g 129
lane [14, 11, 10, 13, 7, 6, 12, 12]
```

If that closes too, stop spending cycles on direct five-pair repair/cg samples
around the bit24 HW82 basin and move to a different operator family.
