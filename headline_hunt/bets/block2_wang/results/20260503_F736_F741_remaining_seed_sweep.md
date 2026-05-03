---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_FULL_F518_PANEL_SWEEP_COMPLETE
parent: F538/F539 extended sweep; F733-F735 HW82 closure pass
evidence_level: VERIFIED_JSON_ARTIFACTS
author: yale-codex
---

# F736-F741: remaining F518 seed-index sweep

## Setup

This completes the F518 seed-index panel after Mac's F535-F539 runs covered
indices 0-15. Each run used the standard M2 pair beam:

```text
rounds = 24
pair_pool = 1024
beam_width = 1024
max_pairs = 6
max_radius = 12
objective = hw
```

Runs were executed one at a time to leave machine headroom.

## Results

| Run | Seed index | Init HW at 24 | Claimed seed HW | Best HW | Delta | Depth | Records | Lane HW |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| F736 | 16 | 142 | 97 | 87 | -55 | 2 | 4491574 | `12,7,17,8,12,11,8,12` |
| F737 | 17 | 125 | 98 | 90 | -35 | 3 | 1559057 | `10,12,11,13,12,9,8,15` |
| F738 | 18 | 128 | 99 | 83 | -45 | 5 | 2235246 | `10,11,8,11,13,8,12,10` |
| F739 | 19 | 123 | 99 | 88 | -35 | 3 | 1158602 | `6,11,12,12,11,11,12,13` |
| F740 | 20 | 116 | 99 | 89 | -27 | 3 | 278184 | `11,12,12,11,18,7,7,11` |
| F741 | 21 | 133 | 99 | 88 | -45 | 4 | 3356104 | `7,13,12,12,15,12,9,8` |

Artifacts:

- `20260503_F736_rank16_m2_pair_beam.json`
- `20260503_F737_rank17_m2_pair_beam.json`
- `20260503_F738_rank18_m2_pair_beam.json`
- `20260503_F739_rank19_m2_pair_beam.json`
- `20260503_F740_rank20_m2_pair_beam.json`
- `20260503_F741_rank21_m2_pair_beam.json`

## Interpretation

The remaining seed indices all descend hard, but none beat the F732 HW82
floor. Rank18 is closest at HW83.

Several rows have much higher evaluated 24-round init HW than their JSONL
claimed seed HW. This matches the earlier transfer-seed pattern: these M2
rows likely come from strong lower-round profiles that evaluate poorly at 24
until pair-beam repair. The pair beam still pulls every one of them into the
83-90 range.

## Panel summary

Mac's F535-F539 plus F736-F741 now cover all 22 F518 seed indices. Every
tested seed breaks the original F519 single-bit floor of HW91 under M2 pair
beam or a direct descendant. Current best remains:

```text
HW82 from F732, c/g-biased restart from the rank2 HW85 witness.
```

## Next

Continue the planned queue:

1. Run cross-round continuation on promising transfer seeds.
2. If cross-round does not beat HW82, revisit rank18 HW83 and the F735
   weighted-lane shape with alternate objectives or wider pair pools.
