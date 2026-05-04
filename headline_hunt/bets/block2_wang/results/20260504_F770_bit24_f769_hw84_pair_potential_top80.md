---
date: 2026-05-04
bet: block2_wang
status: BIT24_F769_HW84_PAIR_POTENTIAL_TOP80_CLOSED
parent: F769 HW84 side basin
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F770: bit24 F769 HW84 pair-potential top-80 atlas

## Setup

F770 maps the HW84 side basin found by F769.

```text
candidate: bit24_mdc27e18c
init HW: 84
init lane HW: [12, 6, 13, 8, 9, 11, 9, 16]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 22
init c/g objective: 128
top per bucket: 80
```

## Result

```text
total two-bit M2 pairs: 130,816
HW < 84 pairs: 0
HW <= 84 pairs: 0
c/g-improving pairs: 0
target-L1-improving pairs: 20
wall seconds: 19.20
```

Best raw-HW pair:

```text
bits [382, 473]
HW 95
target L1 17
lane [9, 12, 11, 11, 13, 11, 14, 14]
```

Best target-L1 pair:

```text
bits [231, 444]
HW 96
target L1 16
lane [12, 13, 13, 12, 9, 9, 15, 13]
```

## Interpretation

The F769 HW84 side basin is one-pair closed for HW and c/g. It still has 20
target-improving one-pair moves, but they are all expensive. This looks like a
real local side basin rather than an immediate waypoint below HW84.

The next reasonable check is a c/g-biased restart from HW84. If that also
closes, stop this detour branch.
