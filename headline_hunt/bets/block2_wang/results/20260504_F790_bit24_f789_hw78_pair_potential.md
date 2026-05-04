---
date: 2026-05-04
bet: block2_wang
status: BIT24_HW78_PAIR_POTENTIAL_CLOSED
parent: F789 HW78 breakthrough
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F790: bit24 F789 HW78 pair-potential atlas

## Setup

F790 maps all two-bit M2 flips around the new F789 HW78 witness.

```text
candidate: bit24_mdc27e18c
init HW: 78
init lane: [13, 11, 8, 9, 7, 9, 8, 13]
target lane: [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 14
total two-bit pairs: 130,816
top retained per bucket: 80
```

## Result

```text
HW < 78 pairs: 0
HW <= 78 pairs: 0
c/g-improving pairs: 0
target-L1-improving pairs: 0
wall seconds: 17.71
```

Best raw-HW pair:

```text
HW 95
target L1 25
c/g objective 145
delta lane [-3, 0, 9, 4, 8, 2, 0, -3]
bits [15, 304]
```

Best c/g pair:

```text
HW 96
c/g objective 128
target L1 28
delta lane [1, 3, 0, 6, 4, 7, 0, -3]
bits [200, 270]
```

Best target-L1 pair:

```text
target L1 18
HW 100
delta lane [1, 1, 1, 3, 5, 4, 5, 2]
bits [22, 456]
```

## Interpretation

The HW78 witness is one-pair closed for every tracked objective. The best
single two-bit move is destructive, jumping to HW95, and no move improves the
target lane distance.

Because F789 itself was a multi-pair repair, one more pure-HW beam from HW78 is
still warranted. But if that closes, the current HW78 witness should be treated
as the mapped endpoint of the overlap-detour branch.

## Artifact

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F790_bit24_f789_hw78_pair_potential_top80.json
```

## Next

Run pure-HW M2 pair-beam from HW78. If it cannot beat HW78, close the local
descent branch and update the portfolio around the new global floor.
