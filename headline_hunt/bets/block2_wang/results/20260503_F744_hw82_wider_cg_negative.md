---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_HW82_WIDER_CG_NEGATIVE
parent: F732 HW82; F734 radius-12 c/g restart; F541 wider HW restart
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F744: wider c/g restart from HW82

## Setup

F744 retests the current HW82 floor with the same c/g objective that produced
the F732 descent, but at the wider scale Mac used for F541's pure-HW check.

```text
init: F732 HW82 M2
objective = total_hw + 2 * (c + g)
pair_rank = cg
rounds = 24
pair_pool = 2048
beam_width = 1024
max_pairs = 8
max_radius = 16
```

Initial lane HW:

```text
[10, 11, 9, 12, 9, 7, 10, 14] = 82
```

## Result

No sub-HW82 records were found.

| Run | Init HW | Best HW | New records | Wall seconds | Best objective | Objective-best HW |
|---|---:|---:|---:|---:|---:|---:|
| F744 | 82 | 82 | 0 | 1888.87 | 119 | 85 |

The best-HW state remained the seed. The best c/g-objective state moved away
from the seed but traded total HW for c/g pressure:

```text
objective = 119
HW = 85
depth = 7
lane HW = [13, 10, 7, 11, 9, 11, 10, 14]
bits = [25, 51, 64, 140, 154, 189, 216, 281, 296, 387, 450, 459, 472, 505]
```

Best-objective M2:

```text
0x22500008 0x40080000 0x00000101 0x00100008
0x44021000 0x70000000 0x09040000 0x00100000
0x0a400000 0x00000108 0x20000000 0x40000800
0x04010049 0x00004200 0x01010804 0x02000008
```

## Verdict

The HW82 witness is now closed under both:

- F541 wider pure-HW search at pool=2048, max_pairs=8, max_radius=16.
- F744 wider c/g search at the same scale.

The c/g objective can still move within the basin, but its best wider move
lands at HW85. That makes the immediate HW82 neighborhood look more like a
real local wall than a radius-12 artifact.

## Next

The remaining direct HW82-local test is the wider weighted-lane objective,
because F735 found a lower weighted-lane shape at HW86 without lowering total
HW. If that also fails, future progress likely needs a new operator class or a
restart from a non-HW82 lane-shape seed.
