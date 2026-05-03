---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_HW82_CG_OBJECTIVE_BREAKTHROUGH
parent: F536/F731 HW85 witness; F539 pure-HW HW85 closure check
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F732: c/g-biased M2 pair beam moves HW85 to HW82

## Setup

Mac's F539 checked the rank2 HW85 witness under the standard HW-ranked
pair beam and found it locally closed at radius 12.

F732 changes only the ranking objective:

```text
objective = total_hw + 2.0 * (lane_c_hw + lane_g_hw)
pair_rank = cg
rounds = 24
pair_pool = 1024
beam_width = 1024
max_pairs = 6
max_radius = 12
```

Starting M2 is the F536/F731 rank2 HW85 witness:

```text
M2 = 0x20100008 0x40000000 0x00000100 0x00100000
     0x40020000 0x10000000 0x08040000 0x00100000
     0x08400000 0x00000008 0x20000000 0x40000800
     0x04010041 0x00000200 0x00010000 0x00000008
```

Initial lane HW:

```text
[11, 9, 10, 9, 8, 11, 13, 14] = 85
objective = 85 + 2 * (10 + 13) = 131
```

Artifact:

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F732_hw85_cg_objective_m2_pair_beam.json
```

## Result

F732 found HW82 at depth 2, only 4 M2 bits from the HW85 parent:

```text
M2 = 0x20500008 0x40000000 0x00000100 0x00100008
     0x40020000 0x50000000 0x08040000 0x00100000
     0x08400000 0x00000008 0x20000000 0x40000800
     0x04010041 0x00004200 0x00010000 0x00000008
```

Flip bits:

```text
22, 99, 190, 430
```

Lane HW:

```text
[10, 11, 9, 12, 9, 7, 10, 14] = 82
objective = 82 + 2 * (9 + 10) = 120
```

The run also found an HW83 record at depth 6. Total sub-init records: 2.

## Objective-best note

The best objective state was not the best HW state:

```text
best objective = 119
best-objective HW = 89
best-objective lane HW = [11, 12, 7, 10, 19, 9, 8, 13]
```

This is useful: c/g ranking did not merely rediscover the pure-HW beam. It
walked into a different lane geometry, and one of the nearby states also
improved total HW by 3.

## Interpretation

F539's "HW85 locally closed" result is true for the standard HW-ranked beam.
F732 shows that closure is objective-dependent. The c/g pressure opens a
short branch from HW85 to HW82.

This validates the old F446/F519 recommendation: the next operator should
coordinate lane pressure, especially c/g, instead of treating total HW as the
only ranking signal.

## Next

1. Iterate from HW82 with standard HW ranking.
2. Iterate from HW82 with c/g ranking again.
3. Try a weighted-lane objective that also penalizes the now-heavy h lane.
4. Run `m2_pair_beam_atlas.py` across F536-F539/F731/F732 to compare basin
   distances and lane signatures.
