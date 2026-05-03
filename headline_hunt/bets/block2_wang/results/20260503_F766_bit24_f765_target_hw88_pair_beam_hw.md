---
date: 2026-05-03
bet: block2_wang
status: BIT24_F765_TARGET_HW88_PAIR_BEAM_HW_NEGATIVE
parent: F765 repair/cg sample best-target detour
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F766: bit24 F765 target-HW88 pure-HW pair-beam repair

## Setup

F766 takes the best target detour from F765 and asks whether ordinary M2
pair-beam can repair the extra HW.

```text
candidate: bit24_mdc27e18c
init HW: 88
init lane HW: [12, 11, 11, 12, 9, 10, 11, 12]
target L1: 10
source: F765 best target sample
objective: pure HW
pair_rank: HW
pair_pool: 1024
beam_width: 1024
max_pairs: 6
max_radius: 12
```

## Result

```text
best seen HW: 88
best source: init
new records: 0
wall seconds: 670.66
```

Depth trace from stdout:

```text
depth 1 best HW 91
depth 2 best HW 91
depth 3 best HW 92
depth 4 best HW 88
depth 5 best HW 91
depth 6 best HW 91
```

## Interpretation

The best F765 target detour is not repaired by the standard pure-HW pair-beam.
Even though it is much closer to the bit13 HW82 lane signature than the F763
seed, the local pair pool cannot turn that lane coordinate into an HW82 or
sub-HW82 state.

This weakens the simple two-stage plan:

```text
target detour -> ordinary HW repair beam
```

The remaining useful version of the detour idea would need a different repair
operator, probably one that keeps the target lane fixed while repairing damage,
instead of allowing the beam objective to collapse back into ordinary local HW
ranking.
