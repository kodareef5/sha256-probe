---
date: 2026-05-03
bet: block2_wang
status: BIT24_HW82_TARGET_REPAIR_COMBO4_NEGATIVE
parent: F761 bit24 HW82 pair-potential atlas
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F762: bit24 HW82 target/repair 4-pair combo

## Setup

F762 tests whether the new F760 bit24 HW82 endpoint has a shallow
target/repair composition exit.

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
pair_count = 4
radius = 6..8
```

## Result

```text
candidate combos: 1,282,975
evaluated: 1,282,974
HW < 82: 0
HW <= 82: 0
c/g-improving: 6
target-L1-improving: 658
wall seconds: 181.89
```

Best raw-HW combo:

```text
HW 88
target L1 22
lane [13, 11, 15, 10, 13, 8, 10, 8]
bits [210, 215, 270, 274, 291, 454, 469, 505]
```

Best target-L1 combo:

```text
HW 91
target L1 13
lane [14, 12, 9, 10, 13, 9, 10, 14]
bits [76, 79, 124, 136, 158, 274, 307, 505]
c/g objective 129, delta -1
```

Best c/g combo:

```text
HW 94
c/g objective 122, delta -8
lane [15, 17, 5, 18, 7, 12, 9, 11]
bits [120, 162, 200, 203, 362, 403, 425, 505]
```

## Interpretation

The 4-pair target/repair neighborhood from bit24 HW82 is closed below or equal
to the current floor. This is a useful negative result because it checks the
cheap continuation after F761 before committing to a wider sweep.

The geometry signal did not disappear. F762 found 658 target-lane improvements
and 6 c/g improvements, but every useful move pays at least +6 HW. That is the
same pattern that made F760 work from HW85: target moves need enough repair
budget to be evaluated by final state instead of by a greedy prefix.

## Next

Run the corresponding 5-pair final-state composition from the same selected
set with radius 8..10. If that closes too, the F760 bit24 HW82 basin should be
treated as locally mapped under this operator family.
