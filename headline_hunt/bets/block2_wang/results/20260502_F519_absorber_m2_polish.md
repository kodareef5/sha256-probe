---
date: 2026-05-02
bet: block2_wang
status: ABSORBER_M2_POLISH
parent: F518 late-round M2 seed bundle
evidence_level: VERIFIED
author: yale-codex
---

# F519: seeded absorber M2 polish

## Setup

F518 made absorber `M2` masks first-class seeds. F519 upgrades
`block2_absorber_probe.c` so rows containing `block1_diff63` and
`absorber_m2` start from that M2 mask instead of zero.

Run:

```bash
/tmp/block2_absorber_probe \
  headline_hunt/bets/block2_wang/results/search_artifacts/20260502_absorber_matrix_overnight/F518_absorber_m2_late_round_seeds.jsonl \
  24 5000000 0x20260542 22 \
  > headline_hunt/bets/block2_wang/results/search_artifacts/20260502_F519_absorber_m2_polish_r24_5M.csv
```

## Result

The 24-round seeds were already local under this 5M one-bit M2 hill-climb:

| Record | Rank | Seed Rounds | Start HW | Best HW | Improvement |
|---:|---:|---:|---:|---:|---:|
| 1 | 36 | 24 | 91 | 91 | 0 |
| 2 | 14 | 24 | 93 | 93 | 0 |
| 3 | 22 | 24 | 94 | 94 | 0 |
| 4 | 32 | 24 | 95 | 95 | 0 |
| 5 | 20 | 24 | 96 | 96 | 0 |
| 6 | 39 | 24 | 96 | 96 | 0 |
| 7 | 33 | 24 | 96 | 96 | 0 |

Some 20-round M2 masks polish at 24 rounds:

| Record | Rank | Seed Rounds | Start HW | Best HW | Improvement |
|---:|---:|---:|---:|---:|---:|
| 19 | 32 | 20 | 128 | 98 | 30 |
| 13 | 38 | 20 | 147 | 99 | 48 |
| 20 | 14 | 20 | 123 | 100 | 23 |

But none beat the best existing 24-round seed, rank 36 at HW91.

## Interpretation

This is the first operator that directly consumes absorber M2/profile seeds.
It says:

- F518's 24-round M2 rows are already local under simple one-bit M2 polish.
- Cross-round transfer works: a 20-round M2 seed can often be improved when
  evaluated at 24 rounds.
- The current one-bit hill-climb is too local to create a new 24-round floor.

## Next Operator

The next M2-aware operator should not be another single-bit hill-climb. It
should use one of:

1. multi-bit M2 pair beam, analogous to W57..W60 pair beam;
2. lane-targeted M2 flips, rewarding reductions in high final lanes and
   penalizing c/g growth;
3. cross-round continuation: polish at 16, lift to 20, then lift to 24 with
   retained beam state.

## Verdict

M2/profile-aware work is now executable and validated, but the first local
polish is boxed in. Continue with a composed M2 operator, not more scalar
single-bit hill-climb.
