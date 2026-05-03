---
date: 2026-05-03
bet: block2_wang
status: BIT24_F763_HW82_PAIR_POTENTIAL_TOP80_CLOSED
parent: F763 HW82 horizontal combo
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F764: bit24 F763 HW82 pair-potential top-80 atlas

## Setup

F764 maps the new F763 HW82 tie with a wider top-80 pair-potential atlas.

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [7, 10, 12, 16, 11, 7, 8, 11]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 18
init c/g objective: 122
top per bucket: 80
```

## Result

```text
total two-bit M2 pairs: 130,816
HW < 82 pairs: 0
HW <= 82 pairs: 0
c/g-improving pairs: 0
target-L1-improving pairs: 5
wall seconds: 17.39
```

Best raw-HW and c/g pair:

```text
bits [38, 43]
HW 89
c/g objective 131
target L1 17
lane [12, 13, 10, 9, 14, 8, 11, 12]
```

Best target-L1 pair:

```text
bits [121, 126]
HW 97
target L1 15
lane [12, 12, 9, 16, 9, 15, 10, 14]
```

## Interpretation

The F763 HW82 tie is one-pair closed for total HW and c/g. It is also much
more target-rigid than the first F760 HW82 point:

```text
F761 around F760 HW82: target-improving pairs = 54
F764 around F763 HW82: target-improving pairs = 5
```

So F763 did not merely slide to another easy lane-copying surface. It moved to
a tighter HW82/cg coordinate, with c/g objective 122 instead of 130, and left
only a handful of direct target-lane one-pair moves.

## Next

Use this top-80 atlas for a repair/cg-heavy sampled combo run. The selection
should deliberately downweight target pairs and keep a wider repair menu,
because both F760 and F763 reached HW82 using ugly repair/per-register repair
pairs rather than target-only moves.
