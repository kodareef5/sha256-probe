---
date: 2026-05-03
bet: block2_wang
status: PATHC_BIT24_HW85_WIDER_CG_NEGATIVE
parent: F746/F548 bit24 HW85; F549 radius-12 HW85 closure
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F748: bit24 HW85 wider c/g restart is negative

## Setup

F746/F548 found the path-C bit24 c/g descent:

```text
candidate: bit24_mdc27e18c
HW86 -> HW85
lane HW: [9, 10, 10, 13, 13, 12, 13, 5]
```

Mac's F549 then showed the HW85 witness is closed under radius-12 c/g. F748
tests whether that closure survives the wider F541/F744 scale.

```text
objective = total_hw + 2 * (c + g)
pair_rank = cg
rounds = 24
pair_pool = 2048
beam_width = 1024
max_pairs = 8
max_radius = 16
```

## Result

No sub-HW85 records were found.

| Run | Candidate | Init HW | Best HW | New records | Wall seconds |
|---|---|---:|---:|---:|---:|
| F748 | bit24_mdc27e18c | 85 | 85 | 0 | 1904.56 |

The best-HW state remained the seed:

```text
lane HW = [9, 10, 10, 13, 13, 12, 13, 5]
```

The best c/g-objective state moved to a higher-HW shape:

```text
objective = 121
HW = 93
depth = 4
lane HW = [15, 12, 7, 12, 10, 15, 7, 15]
bits = [69, 70, 171, 321, 365, 387, 418, 434]
```

Best-objective M2:

```text
0x00001000 0x00100000 0x00004064 0x00001002
0x00000000 0x00001800 0x00008000 0x00200000
0x00002000 0x20020040 0x0180810a 0x00002000
0x00000008 0x00010004 0x02008000 0x00000000
```

## Verdict

Bit24's c/g descent appears to stop at HW85 under this operator:

```text
F548/F746: HW86 -> HW85
F549:      HW85 -> HW85 at radius 12
F748:      HW85 -> HW85 at radius 16
```

That makes bit24 the second-deepest mapped candidate after bit13, but not a
current route to the global HW82 floor. The wider c/g operator still sculpts
c/g lanes, but the best objective trade returns to HW93 rather than producing
a lower total-HW absorber.
