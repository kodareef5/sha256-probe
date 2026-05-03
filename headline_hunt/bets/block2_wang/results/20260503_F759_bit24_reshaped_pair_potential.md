---
date: 2026-05-03
bet: block2_wang
status: BIT24_RESHAPED_HW85_PAIR_POTENTIAL
parent: F756 reshaped HW85; F757/F758 restart closures
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F759: pair-potential atlas around reshaped bit24 HW85

## Setup

F759 reruns the two-bit M2 pair-potential atlas around the F756 reshaped bit24
HW85 witness:

```text
lane HW = [10, 9, 11, 11, 9, 10, 12, 13]
target lane = [10, 11, 9, 12, 9, 7, 10, 14]
target L1 = 11
```

All 130,816 two-bit M2 flips were evaluated.

## Result

| Metric | Count |
|---|---:|
| HW < 85 pairs | 0 |
| HW <= 85 pairs | 0 |
| c/g-improving pairs | 1 |
| target-L1-improving pairs | 0 |

Best pair by total HW:

```text
HW = 94
lane HW = [8, 11, 14, 16, 11, 9, 14, 11]
target L1 = 22
bits = [198, 439]
```

Best pair by c/g objective:

```text
HW = 98
objective = 130
lane HW = [11, 17, 10, 12, 14, 13, 6, 15]
target L1 = 24
bits = [23, 241]
```

Best pair by target-L1 still moves away from target:

```text
HW = 99
target L1 = 17
target L1 delta = +6
lane HW = [14, 13, 11, 12, 10, 14, 10, 15]
bits = [0, 16]
```

## Verdict

F756 succeeded as a horizontal move on the HW85 surface, but it landed at a
locally rigid point. Compared to the original bit24 HW85 witness:

```text
original HW85: target L1 25, 107 target-improving pairs
reshaped HW85: target L1 11, 0 target-improving pairs
```

This explains why F757/F758 did not descend: the reshaped seed is closer to
the HW82 lane signature, but its immediate two-bit neighborhood is even more
closed.
