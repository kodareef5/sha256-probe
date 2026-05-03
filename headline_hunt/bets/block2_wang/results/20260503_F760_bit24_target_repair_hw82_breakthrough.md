---
date: 2026-05-03
bet: block2_wang
status: BIT24_TARGET_REPAIR_HW82
parent: F750 pair-potential atlas; F755/F756 target-repair combo pilot
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F760: bit24 target/repair combo reaches HW82

## Setup

F760 extends the target/repair composition line from the original bit24 HW85
witness:

```text
candidate: bit24_mdc27e18c
init HW: 85
init lane HW: [9, 10, 10, 13, 13, 12, 13, 5]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
target L1: 25
```

Pair source:

```text
F750 bit24 HW85 pair-potential atlas
```

Selection:

```text
target pairs = 32
repair pairs = 32
HW pairs = 16
c/g pairs = 16
per-register repair pairs = 4
selected pairs = 83
pair_count = 5
radius = 8..10
```

## Result

F760 evaluated 29,034,276 final states and found two sub-HW85 records.

| Run | Evaluated | HW < 85 | HW <= 85 | Best HW | Wall seconds |
|---|---:|---:|---:|---:|---:|
| F760 | 29,034,276 | 2 | 3 | 82 | 4102.83 |

Best witness:

```text
HW = 82
target L1 = 24
lane HW = [9, 10, 11, 10, 10, 13, 13, 6]
bits = [110, 116, 126, 188, 207, 283, 449, 464, 476, 486]
pair sources = repair/cg + repair_c + repair + repair + repair_a
```

M2:

```text
0x00001000 0x00100000 0x00004004 0x40105002
0x00000000 0x10001000 0x00000000 0x00200000
0x08002000 0x20020040 0x01808108 0x00000000
0x00000000 0x00050000 0x12018002 0x00000040
```

Other retained non-worse records:

```text
HW84, target L1 20, lane [8, 11, 11, 10, 11, 9, 15, 9]
HW85, target L1 17, lane [5, 14, 10, 10, 10, 8, 12, 16]
```

## Interpretation

This ties the global absorber floor:

```text
bit13 F732: HW82
bit24 F760: HW82
```

It also validates the pair-potential/target-repair idea. Greedy pair-beam
variants closed at bit24 HW85, and F756 only moved horizontally on the HW85
surface. F760 found the missing non-local composition by allowing five selected
pairs to combine by final state rather than by prefix objective.

The HW82 bit24 lane is not especially close to the bit13 HW82 lane:

```text
bit13 HW82 lane: [10, 11, 9, 12, 9, 7, 10, 14]
bit24 HW82 lane: [9, 10, 11, 10, 10, 13, 13, 6]
```

So the important lesson is not lane copying. It is that the target/repair
selection creates useful non-greedy repair compositions that the standard beam
does not enter.

## Next

Verify the bit24 HW82 witness with a fresh local atlas/restart:

1. Run pair-potential atlas around F760 HW82.
2. Run a small c/g or HW restart from F760 HW82 if the atlas suggests any
   nontrivial local direction.
