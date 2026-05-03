---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_CROSS_ROUND_PIPE_NEGATIVE
parent: F736-F741 remaining seed sweep; F738 rank18 HW83
evidence_level: VERIFIED_JSON_ARTIFACTS
author: yale-codex
---

# F742: rank18 cross-round pipe is negative

## Setup

F738 made rank18 the best remaining-panel seed at HW83 under a direct
24-round M2 pair beam. F742 tests the F519/F535 cross-round idea:

```text
rank18 seed
rounds: 16 -> 20 -> 24
pair_pool = 1024
beam_width = 1024
max_pairs = 6
max_radius = 12
objective = hw
```

Each stage restarts from the previous stage's true best M2 using
`m2_cross_round_pipe.py`.

## Results

| Stage | Rounds | Init HW | Best HW | Delta | Depth | Lane HW |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 16 | 127 | 88 | -39 | 6 | `11,11,9,12,11,10,13,11` |
| 2 | 20 | 130 | 88 | -42 | 2 | `11,8,11,9,13,10,11,15` |
| 3 | 24 | 132 | 90 | -42 | 6 | `10,7,13,12,10,16,9,13` |

Artifacts:

- `20260503_F742_rank18_cross_round_pipe_stage1_r16.json`
- `20260503_F742_rank18_cross_round_pipe_stage2_r20.json`
- `20260503_F742_rank18_cross_round_pipe_stage3_r24.json`
- `20260503_F742_rank18_cross_round_pipe_summary.json`

## Verdict

The staged pipe does not beat the direct 24-round rank18 result:

```text
direct rank18 F738: 128 -> 83
F742 pipe final:    132 -> 90
```

For rank18, lower-round optimization does not transfer into a better
24-round basin. It appears to overfit the intermediate rounds and enter a
worse final-round basin.

## Next

Continue with direct local work around the actual floor:

1. Revisit rank18 HW83 with c/g objective; it is close to HW82 and has a
   different lane shape.
2. Revisit the HW82/HW83 basin with wider pair pools if the one-at-a-time
   queue has spare compute.
