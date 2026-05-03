---
date: 2026-05-03
bet: block2_wang
status: BIT24_TARGET_REPAIR_COMBO_HW85_RESHAPE
parent: F750 bit24 pair-potential atlas
evidence_level: VERIFIED_JSON_ARTIFACTS
author: yale-codex
---

# F755-F756: bit24 target/repair pair-combo pilot

## Tool

Added:

```text
headline_hunt/bets/block2_wang/encoders/m2_target_pair_combo.py
```

The script consumes an `m2_pair_potential_atlas.py` artifact, selects pairs
from target-lane, repair, HW, c/g, and per-register lists, then evaluates
fixed-size pair combinations by final state only. This is deliberately not a
greedy beam: bad prefix moves are allowed if the final composition repairs
them.

## Setup

Seed:

```text
candidate: bit24_mdc27e18c
init: F746/F548/F549/F748 HW85 witness
lane HW: [9, 10, 10, 13, 13, 12, 13, 5]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
target L1 distance: 25
```

Pair atlas:

```text
F750 bit24 HW85 pair-potential atlas
```

## Results

| Run | Pair count | Evaluated | HW < 85 | HW <= 85 | Target-improving | Best HW | Best target |
|---|---:|---:|---:|---:|---:|---:|---|
| F755 | 3 | 192,917 | 0 | 0 | 190 | 88 | HW88, L1 16 |
| F756 | 4 | 3,464,651 | 0 | 1 | 3,062 | 85 | HW85, L1 11 |

F756 found an equal-HW reshaped bit24 absorber:

```text
HW = 85
target L1 = 11  (was 25)
lane HW = [10, 9, 11, 11, 9, 10, 12, 13]
bits = [12, 23, 216, 356, 426, 440, 471, 507]
pair sources = cg + repair_e + repair_c + repair_a
```

M2:

```text
0x00800000 0x00100000 0x00004004 0x00001002
0x00000000 0x00001000 0x01008000 0x00200000
0x00002000 0x20020040 0x01808108 0x00000010
0x00000000 0x01050400 0x02808000 0x08000000
```

## Interpretation

The new operator did not beat HW85, but it achieved something the greedy
pair-beam variants did not: it moved bit24 much closer to the HW82 lane
signature while preserving total HW.

This validates the pair-potential diagnosis:

```text
single target move:  HW85 -> HW96, L1 25 -> 16
3-pair combo:        HW85 -> HW88, L1 25 -> 16
4-pair combo:        HW85 -> HW85, L1 25 -> 11
```

The next immediate test is to restart the normal M2 pair beam from this
reshaped HW85 witness. If the reshaped basin has different local geometry, it
may expose a descent that the original bit24 HW85 witness did not.
