---
date: 2026-05-03
bet: block2_wang
status: BIT24_HW82_PAIR_POTENTIAL_CLOSED
parent: F760 bit24 target/repair HW82
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F761: bit24 HW82 pair-potential atlas

## Setup

F761 reruns the full two-bit M2 pair-potential atlas around the new F760
bit24 HW82 witness:

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [9, 10, 11, 10, 10, 13, 13, 6]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
target L1: 24
init c/g objective: 130
```

The run enumerated all 130,816 two-bit M2 flips.

## Result

```text
HW < 82 pairs: 0
HW <= 82 pairs: 0
c/g-improving pairs: 0
target-L1-improving pairs: 54
wall seconds: 19.42
```

Best raw-HW pair:

```text
bits [231, 447]
HW 93
lane [12, 10, 12, 8, 10, 17, 13, 11]
target L1 27
```

Best target-L1 pair:

```text
bits [200, 505]
HW 97
lane [13, 12, 11, 11, 10, 11, 12, 17]
target L1 17
```

## Interpretation

F760's bit24 HW82 witness is locally closed under the one-pair atlas for both
total HW and c/g objective. This mirrors the earlier bit13 HW82 closure and
supports treating HW82 as the current mapped floor rather than an obvious
one-pair waypoint.

The endpoint is not geometrically dead, though. There are still 54 one-pair
moves that reduce distance to the bit13 HW82 lane signature. They are expensive
single moves, with the best target-L1 move paying HW82 -> HW97, so they are not
usable directly. The practical lesson is the same as F760: any next descent
must be composed as a multi-pair target/repair move, not as a greedy pair-beam
or single-pair local move.

## Next

Use F761 as the atlas parent for a smaller target/repair combo from the HW82
state. Keep the first pass constrained: selected pairs from target repair and
per-register repair only, then test whether any 4-pair or 5-pair final-state
composition can reach HW81 or produce a materially better c/g coordinate.
