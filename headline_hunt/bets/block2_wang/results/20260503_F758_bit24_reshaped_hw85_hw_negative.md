---
date: 2026-05-03
bet: block2_wang
status: BIT24_RESHAPED_HW85_HW_NEGATIVE
parent: F756 target/repair HW85 reshaped witness; F757 c/g restart
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F758: reshaped bit24 HW85 pure-HW restart is negative

## Setup

F758 restarts from the F756 reshaped bit24 HW85 witness:

```text
lane HW = [10, 9, 11, 11, 9, 10, 12, 13]
target L1 to bit13 HW82 lane = 11
```

This is the pure-HW counterpart to F757's c/g restart.

```text
objective = total HW
pair_rank = hw
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
| F758 | 85 | 85 | 0 | 709.27 |

The best-HW and best-objective state remained the seed:

```text
lane HW = [10, 9, 11, 11, 9, 10, 12, 13]
```

The beam got near but not below the seed:

```text
depth 3 best_hw = 86
depth 5 best_hw = 86
```

## Verdict

The F756 target/repair reshaped bit24 seed is closed under both immediate
restart objectives tested:

```text
F757 c/g: HW85 -> HW85
F758 HW:  HW85 -> HW85
```

The reshaping result remains useful as evidence that target/repair composition
can preserve HW while moving toward the HW82 lane signature. It does not by
itself expose a lower local basin to standard pair-beam restart.
