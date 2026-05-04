---
date: 2026-05-04
bet: block2_wang
status: BIT24_TARGET_OBJECTIVE_BEAM_HW84
parent: F769/F771 detour branch; target-lane objective tool
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F772: bit24 F768 HW85 target-objective pair beam

## Setup

F772 is the first full run of the new target-lane M2 pair-beam objective. It
starts from the same F768 HW85 detour used by F769, but ranks and beams by:

```text
objective = HW + 2 * L1(lane, bit13 HW82 lane)
target lane = [10, 11, 9, 12, 9, 7, 10, 14]
```

Run parameters:

```text
candidate: bit24_mdc27e18c
init HW: 85
init lane HW: [14, 11, 10, 13, 7, 6, 12, 12]
init target L1: 13
init target objective: 111
pair_rank: target
pair_pool: 1024
beam_width: 1024
max_pairs: 6
max_radius: 12
```

## Result

```text
best seen HW: 84
best source: final beam
best depth: 6
new HW records: 1
wall seconds: 677.07
```

Best HW record:

```text
HW 84
lane [13, 9, 9, 8, 9, 15, 12, 9]
target L1 24
target objective 132
bits [59, 86, 133, 166, 308, 319, 345, 348, 409, 434, 440, 454]
```

M2:

```text
0x00001000 0x0c100000 0x20404004 0x40105002
0x01000020 0x10041040 0x00000000 0x00201000
0x0a002000 0xa0120040 0x13808108 0x00100000
0x02001000 0x01010010 0x12018042 0x02000040
```

## Interpretation

The target-lane objective works as a tool and found a distinct HW84 record from
the F768 HW85 detour. However, it did not solve the drift problem on this first
setting:

```text
init: HW85, target L1 13, objective 111
best HW: HW84, target L1 24, objective 132
```

The beam found an HW repair, but only by moving away from the target lane. In
other words, target pressure with weight 2 is not enough to keep the repair path
target-aligned, and the best target-objective state remained the seed.

This is still a useful operator extension because it gives us a knob for
constrained repair. The next settings should use either a higher target weight
or a hard target-L1 cap rather than a soft penalty alone.
