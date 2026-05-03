---
date: 2026-05-03
bet: block2_wang
status: PATHC_BIT4_ABSORBER_CG_NEGATIVE
parent: F547 path-C absorber expansion; F548/F549 cross-candidate c/g map
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F747: bit4 path-C HW89 c/g restart is negative

## Setup

Mac's F547 path-C expansion found a distinct bit4 absorber basin:

```text
candidate: bit4_m39a03c2d
source: F547_pathC_rank2
pure-HW result: 132 -> 89
lane HW: [14, 11, 9, 10, 13, 9, 9, 14]
```

F747 restarts from that HW89 witness under c/g ranking.

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

No sub-HW89 records were found.

| Run | Candidate | Init HW | Best HW | New records | Wall seconds |
|---|---|---:|---:|---:|---:|
| F747 | bit4_m39a03c2d | 89 | 89 | 0 | 689.02 |

The best-HW state remained the seed:

```text
lane HW = [14, 11, 9, 10, 13, 9, 9, 14]
```

The best c/g-objective state traded total HW upward:

```text
objective = 123
HW = 91
depth = 5
lane HW = [14, 10, 4, 16, 13, 10, 12, 12]
bits = [1, 10, 32, 42, 79, 87, 91, 95, 173, 306]
```

Best-objective M2:

```text
0x02200402 0x00000401 0x88808000 0x00000010
0x00000002 0x00402000 0x00002000 0x00008000
0x00000800 0x00040000 0x00000000 0x02000002
0x00000000 0x00000000 0x00000400 0x02000000
```

## Verdict

The first-pass path-C c/g map is now complete:

```text
bit24: HW86 -> HW85, then HW85 closed at radius 12
bit3:  HW86 closed at radius 12
bit4:  HW89 closed at radius 12
```

The candidates do not share one universal c/g descent depth. Bit24 behaves
most like bit13, bit3 stalls at the common HW86 family floor, and bit4 remains
a shallower HW89 basin under this operator.
