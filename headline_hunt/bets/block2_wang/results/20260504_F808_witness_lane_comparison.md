---
date: 2026-05-04
bet: block2_wang
status: WITNESS_LANE_AND_M2_COMPARISON
parent: F788/F789/F796/F800/F802/F805/F807
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F808: witness lane and M2 comparison

## Setup

F808 adds `summarize_m2_witness_lanes.py`, a small utility for comparing M2
witnesses by lane shape, c/g load, M2 popcount, and distance to named target
lanes.

Compared witnesses:

```text
F788 HW86 repairable detour
F789 HW78 floor
F796 HW87 closed detour
F800 HW86 bridgeable detour
F802 HW85 closed bridge witness
F805 HW88 shallow repair
F807 HW89 target-shape objective winner
```

Target lanes:

```text
F788 HW86 lane: [14, 13, 10, 8, 8, 8, 12, 13]
F789 HW78 lane: [13, 11, 8, 9, 7, 9, 8, 13]
bit13 HW82 lane: [10, 11, 9, 12, 9, 7, 10, 14]
```

## Table

```text
label                  HW  lane                         c+g  M2wt  L1 F788  L1 F789  L1 bit13
F788_HW86_repairable   86  [14,13,10,8,8,8,12,13]       22   40    0        12       16
F789_HW78_floor        78  [13,11,8,9,7,9,8,13]         16   44    12       0        14
F796_HW87_closed       87  [10,11,9,14,11,11,12,9]      21   50    23       23       15
F800_HW86_bridgeable   86  [10,7,9,9,17,14,11,9]        20   50    32       30       28
F802_HW85_closed       85  [11,12,7,12,12,12,9,10]      16   56    25       19       17
F805_HW88_shallow      88  [10,6,12,17,13,12,10,8]      22   54    38       36       28
F807_HW89_target_shape 89  [17,13,10,10,9,7,13,10]      23   56    11       21       19
```

## Interpretation

Simple lane distance is not enough. F800 was far from both F788 and F789 by
lane L1, but it bridged to HW85. F796 was closer by lane L1, but did not bridge.

The new coordinate is M2 popcount:

```text
successful F788/F789 path: M2 weight 40 -> 44
closed/weaker branches:   M2 weight 50 -> 56
```

That suggests the weak branches may be over-filled. A sparse-M2 penalty is a
reasonable next objective because it gives the beam a way to prefer low-HW
states that also stay closer to the successful witness sparsity regime.

## Artifacts

```text
headline_hunt/bets/block2_wang/encoders/summarize_m2_witness_lanes.py
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F808_witness_lane_comparison.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F808_witness_lane_comparison.md
```

## Next

Add sparse M2 objectives to `block2_m2_pair_beam.py` and test a sparse
target-lane bridge from F802 HW85 toward the F789 HW78 lane.
