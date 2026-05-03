---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_HW82_WIDER_WEIGHTED_NEGATIVE
parent: F735 weighted-lane hint; F541/F543/F744 wider HW82 closure
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F745: wider weighted-lane restart from HW82

## Setup

F745 is the wider version of F735. It restarts from the F732 HW82 witness and
uses the same c/g/h-weighted lane objective, but at the wider F541/F744 scale.

```text
init: F732 HW82 M2
objective = weighted lane HW
lane weights = [1, 1, 2, 1, 1, 1, 2, 3]
pair_rank = weighted
rounds = 24
pair_pool = 2048
beam_width = 1024
max_pairs = 8
max_radius = 16
```

Initial lane HW:

```text
[10, 11, 9, 12, 9, 7, 10, 14] = 82
weighted objective = 129
```

## Result

No sub-HW82 records were found.

| Run | Init HW | Best HW | New records | Wall seconds | Best objective | Objective-best HW |
|---|---:|---:|---:|---:|---:|---:|
| F745 | 82 | 82 | 0 | 1922.38 | 124 | 94 |

The best-HW state remained the seed. The best weighted-objective state moved
farther into a lane-shape trade:

```text
objective = 124
HW = 94
depth = 7
lane HW = [14, 14, 13, 14, 12, 14, 9, 4]
bits = [34, 41, 94, 98, 110, 114, 188, 275, 325, 356, 362, 392, 446, 471]
```

Best-objective M2:

```text
0x20500008 0x40000204 0x40000100 0x0014400c
0x40020000 0x40000000 0x08040000 0x00100000
0x08480000 0x00000008 0x20000020 0x40000c10
0x04010141 0x40004200 0x00810000 0x00000008
```

## Comparison to F735

F735, at radius 12/pool 1024, found:

```text
objective = 127
HW = 86
lane HW = [11, 9, 8, 11, 13, 11, 13, 10]
```

F745 improves the weighted objective to 124, but only by pushing much more
mass into a/g/d/f and collapsing h. That is not a plausible direct descent
shape under the current total-HW target.

## Verdict

The HW82 witness is now closed under the simple local pair-beam objective
family:

- pure HW at radius 12 and radius 16,
- c/g at radius 12 and radius 16,
- weighted c/g/h at radius 12 and radius 16.

The weighted objective can sculpt lane shape, but at wider radius it moves
away from low total HW. Further progress likely needs a different operator
class, a restart from a non-HW82 basin, or a selection/atlas step that uses
these lane trades without treating them as direct floor candidates.
