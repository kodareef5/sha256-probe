---
date: 2026-05-04
bet: block2_wang
status: BIT24_F782_HW87_PAIR_POTENTIAL_CLOSED
parent: F784 F782-detour pair-beam negative
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F785: bit24 F782 HW87 pair-potential atlas

## Setup

F785 maps all two-bit M2 flips around the F782 HW87 / target-L1 13 detour.
This checks whether F784's beam failure was caused by a poor beam objective or
by real one-pair local rigidity.

```text
candidate: bit24_mdc27e18c
init HW: 87
init lane HW: [10, 8, 12, 15, 10, 7, 12, 13]
target lane: [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 13
top retained per bucket: 80
total two-bit pairs: 130,816
```

## Result

```text
HW < 87 pairs: 0
HW <= 87 pairs: 0
c/g-improving pairs: 1
target-L1-improving pairs: 0
wall seconds: 19.70
```

Best raw-HW pair:

```text
HW 94
target L1 22
c/g objective 136
delta lane [5, 9, -2, -1, -2, 2, -1, -3]
bits [220, 412]
```

Best c/g pair:

```text
HW 96
c/g objective 128, delta -7
target L1 26
delta lane [7, 5, -1, -4, 1, 4, -7, 4]
bits [128, 243]
```

Best target-L1 pair:

```text
target L1 16, delta +3
HW 96
delta lane [1, 6, 2, -3, 4, 0, -1, 0]
bits [38, 230]
```

## Interpretation

The F782 detour is closed. It has good target-lane geometry, but no one-pair
move improves HW or target distance, and the only c/g-improving move is
expensive. Combined with F784, this says the F782 branch is not a useful side
basin.

The broader lesson is stronger: word-pair graph filters can find aesthetically
closer lane signatures, but those states are not necessarily more repairable.
The next selector should be based on lane-specific nonlinear cancellation,
not on graph shape or target-lane proximity alone.

## Artifact

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F785_bit24_f782_hw87_pair_potential_top80.json
```

## Next

Build a small cancellation-signature selector from known records. The feature
to test is not "large nonlinear cancellation" generally, but whether predicted
damage and observed cancellation land in the same lanes as F760/F763 rather
than F782/F783.
