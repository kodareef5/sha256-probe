---
date: 2026-05-03
bet: block2_wang
status: BIT24_HW82_TARGET_REPAIR_COMBO5_HORIZONTAL
parent: F761 pair-potential atlas; F762 4-pair negative
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F763: bit24 HW82 target/repair 5-pair combo

## Setup

F763 is the five-pair counterpart to F762. It starts from the F760 bit24 HW82
witness and composes selected pairs from the F761 pair-potential atlas.

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [9, 10, 11, 10, 10, 13, 13, 6]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 24
pair atlas: F761
```

Selection:

```text
target pairs = 20
repair pairs = 20
HW pairs = 10
c/g pairs = 10
per-register repair pairs = 4
selected pairs = 76
pair_count = 5
radius = 8..10
```

## Result

```text
candidate combos: 18,474,840
evaluated: 18,474,546
HW < 82: 0
HW <= 82: 1
c/g-improving: 38
target-L1-improving: 9,767
wall seconds: 2658.19
```

Best HW record:

```text
HW 82
target L1 18
c/g objective 122, delta -8
lane [7, 10, 12, 16, 11, 7, 8, 11]
bits [6, 71, 96, 177, 186, 398, 408, 427, 456, 465]
pair sources repair + repair + repair_e + repair_e + repair_h
```

M2:

```text
0x00001040 0x00100000 0x00004084 0x40105003
0x00000000 0x14021000 0x00000000 0x00200000
0x08002000 0x20020040 0x01808108 0x00000000
0x01004000 0x00050800 0x12038102 0x00000040
```

Best target-L1 record:

```text
HW 94
target L1 12
lane [12, 11, 10, 12, 13, 9, 13, 14]
```

Best c/g record:

```text
HW 89
c/g objective 119, delta -11
lane [18, 14, 10, 9, 12, 10, 5, 11]
```

## Interpretation

F763 does not break the HW82 floor, but it proves the floor is not a single
isolated point under the target/repair operator. Five selected pairs can move
bit24 horizontally on the HW82 surface while improving both target-lane distance
and c/g objective:

```text
F760 HW82: lane [9, 10, 11, 10, 10, 13, 13, 6], target L1 24, c/g 130
F763 HW82: lane [7, 10, 12, 16, 11, 7, 8, 11], target L1 18, c/g 122
```

The source analysis is the important part. The HW82 tie used no target-only
pairs. It used repair and per-register repair pairs, including standalone moves
that look terrible in isolation:

```text
standalone pair HWs: 110, 107, 110, 126, 120
sources: repair, repair, repair_e, repair_e, repair_h
```

This independently repeats the F760 lesson: productive M2 compositions are made
from ugly local repair moves whose compensation damage cancels only at the
final-state level. Pure target-lane copying is a weaker explanation than
repair-composition geometry.

## Next

1. Run a pair-potential atlas around the F763 HW82 tie.
2. Then run a repair/cg-heavy sampled combo pass with a wider pair atlas. The
   selector should keep more ugly repair pairs and fewer target-only pairs.
