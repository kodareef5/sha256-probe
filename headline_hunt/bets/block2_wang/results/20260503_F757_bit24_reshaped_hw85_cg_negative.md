---
date: 2026-05-03
bet: block2_wang
status: BIT24_RESHAPED_HW85_CG_NEGATIVE
parent: F756 target/repair HW85 reshaped witness
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F757: reshaped bit24 HW85 c/g restart is negative

## Setup

F756 found an equal-HW bit24 absorber much closer to the bit13 HW82 lane
signature:

```text
old bit24 HW85 lane: [9, 10, 10, 13, 13, 12, 13, 5], target L1 25
new bit24 HW85 lane: [10, 9, 11, 11, 9, 10, 12, 13], target L1 11
```

F757 restarts the standard c/g M2 pair beam from the reshaped HW85 witness.

```text
objective = total_hw + 2 * (c + g)
pair_rank = cg
rounds = 24
pair_pool = 1024
beam_width = 1024
max_pairs = 6
max_radius = 12
```

## Result

No sub-HW85 records were found.

| Run | Init HW | Best HW | New records | Wall seconds |
|---|---:|---:|---:|---:|
| F757 | 85 | 85 | 0 | 703.93 |

The best-HW state remained the reshaped seed:

```text
lane HW = [10, 9, 11, 11, 9, 10, 12, 13]
```

The best c/g-objective state moved to a higher-HW shape:

```text
objective = 116
HW = 90
depth = 4
lane HW = [12, 15, 8, 12, 13, 11, 5, 14]
bits = [7, 73, 121, 170, 318, 326, 485, 489]
```

## Verdict

The target/repair operator successfully changed bit24's lane geometry at equal
HW, but a standard c/g beam from that reshaped seed still does not descend
below HW85.

This keeps bit24's mapped floor at HW85. The positive part is that F756
created a new same-HW basin coordinate; the negative part is that c/g alone is
not enough to exploit it.
