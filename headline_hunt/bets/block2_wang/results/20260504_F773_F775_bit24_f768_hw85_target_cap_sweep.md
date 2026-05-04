---
date: 2026-05-04
bet: block2_wang
status: BIT24_TARGET_CAP_SWEEP_NEGATIVE
parent: F772 target-objective beam
evidence_level: VERIFIED_JSON_ARTIFACTS
author: yale-codex
---

# F773/F775: bit24 F768 HW85 hard target-cap sweep

## Setup

F773-F775 test the hard target-lane cap added to `block2_m2_pair_beam.py`.
The seed is the same F768 HW85 detour used by F769 and F772.

```text
candidate: bit24_mdc27e18c
init HW: 85
init lane HW: [14, 11, 10, 13, 7, 6, 12, 12]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 13
objective: pure HW
pair_rank: HW
pair_pool: 1024
beam_width: 1024
max_pairs: 6
max_radius: 12
```

## Result

| Run | Target L1 cap | Wall seconds | Beam behavior | Best HW |
|---|---:|---:|---|---:|
| F773 | 16 | 18.02 | depth 1 kept 1, depth 2 empty | 85 |
| F774 | 20 | 19.40 | depth 1 kept 14, depth 2 kept 2, depth 3 empty | 85 |
| F775 | 24 | 72.07 | survives depth 6 with 70 states | 85 |

F775 depth trace:

```text
depth 1: kept=122 best_hw=92
depth 2: kept=100 best_hw=94
depth 3: kept=83  best_hw=93
depth 4: kept=81  best_hw=98
depth 5: kept=70  best_hw=91
depth 6: kept=70  best_hw=92
```

## Interpretation

Hard target caps behave as expected:

```text
cap 16: too tight
cap 20: too tight
cap 24: viable but no HW repair
```

The known HW84 repairs from F769/F772 require drifting to target L1 22 and 24.
F775 allows that range but still does not find any HW<85 record, which means
the simple capped pure-HW beam is not enough to reproduce the uncapped HW84
repair while preserving the target band.

This closes the first constrained-repair attempt. The target-lane objective and
cap are useful tool knobs, but the first settings do not expose an HW82 route.
Further work should not just sweep caps; it should change the state expansion,
for example by selecting pairs from target-improving and repair atlases rather
than the ordinary HW-ranked pair pool.
