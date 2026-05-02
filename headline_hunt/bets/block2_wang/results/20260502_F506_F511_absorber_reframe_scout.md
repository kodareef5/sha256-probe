---
date: 2026-05-02
bet: block2_wang
status: ABSORBER_REFRAME_SCOUT
parent: F491 post-HW35 basin manifest
evidence_level: SCOUT
author: yale-codex
---

# F506/F511: second-block absorber reframe scout

## Question

After F487/F491, Path C's best block-1 residual is bit13 HW35. This scout
tests a different objective: are the lowest-HW block-1 residuals also the
easiest for a crude free second block to absorb?

Answer from this scout: no. The HW35 champion is not the best launch point
under this absorber proxy.

## Tooling

Added:

- `headline_hunt/bets/block2_wang/encoders/export_manifest_residuals.py`
- `headline_hunt/bets/block2_wang/encoders/run_absorber_matrix.py`

This exports pair-beam seed manifests into the JSONL shape consumed by the
existing absorber prototype:

- `headline_hunt/bets/block2_wang/prototypes/block2_absorber_probe.c`

Artifacts:

- F506: `search_artifacts/20260502_F506_f491_residuals_for_absorber.jsonl`
- F507: `search_artifacts/20260502_F507_f491_absorber_r12_100k.csv`
- F508: `search_artifacts/20260502_F508_f491_absorber_r16_100k.csv`
- F509: `search_artifacts/20260502_F509_f491_absorber_selected_ranks.jsonl`
- F510: `search_artifacts/20260502_F510_f491_selected_absorber_r16_5M.csv`
- F511: `search_artifacts/20260502_F511_f491_selected_absorber_r20_5M.csv`
- F512: `search_artifacts/20260502_absorber_matrix_overnight/F512_f491_absorber_matrix_summary.md`

## All-rank scout

F507/F508 ran 100k hill-climb iterations over all 43 F491 seeds.

At 12 rounds, the best absorber rows were not the HW35 row:

| Rank | Block-1 HW | Start HW | Best HW | Improvement |
|---:|---:|---:|---:|---:|
| 36 | 42 | 113 | 76 | 37 |
| 28 | 42 | 130 | 78 | 52 |
| 3 | 38 | 129 | 79 | 50 |
| 43 | 44 | 122 | 80 | 42 |
| 1 | 35 | 134 | 87 | 47 |

At 16 rounds, the ordering changed but the same conclusion held:

| Rank | Block-1 HW | Start HW | Best HW | Improvement |
|---:|---:|---:|---:|---:|
| 18 | 41 | 122 | 76 | 46 |
| 19 | 41 | 121 | 79 | 42 |
| 2 | 36 | 123 | 80 | 43 |
| 32 | 42 | 113 | 80 | 33 |
| 1 | 35 | 142 | 87 | 55 |

## Selected-rank deep scout

F510/F511 deepened selected ranks `{1,2,3,4,18,19,28,36}` to 5M
iterations each.

16-round absorber:

| Rank | Block-1 HW | Start HW | Best HW | Improvement |
|---:|---:|---:|---:|---:|
| 3 | 38 | 130 | 73 | 57 |
| 18 | 41 | 122 | 79 | 43 |
| 28 | 42 | 130 | 80 | 50 |
| 36 | 42 | 119 | 82 | 37 |
| 1 | 35 | 142 | 88 | 54 |

20-round absorber:

| Rank | Block-1 HW | Start HW | Best HW | Improvement |
|---:|---:|---:|---:|---:|
| 19 | 41 | 119 | 99 | 20 |
| 36 | 42 | 130 | 100 | 30 |
| 4 | 38 | 123 | 100 | 23 |
| 2 | 36 | 130 | 101 | 29 |
| 1 | 35 | 131 | 104 | 27 |

## F512 full F491 matrix

F512 ran all 43 F491 residuals across rounds 12/16/20/24 and four RNG
seeds, 5M iterations per cell.

Top aggregate rows by minimum absorber HW:

| Rank | Block-1 HW | Bridge Score | Min Best HW | Mean Best HW | Runs |
|---:|---:|---:|---:|---:|---:|
| 34 | 42 | 76.684 | 69 | 91.938 | 16 |
| 15 | 41 | 80.923 | 69 | 93.438 | 16 |
| 21 | 41 | 80.923 | 71 | 91.938 | 16 |
| 11 | 40 | 81.842 | 72 | 89.938 | 16 |
| 7 | 40 | 81.842 | 72 | 92.562 | 16 |
| 20 | 41 | 80.923 | 73 | 92.500 | 16 |
| 18 | 41 | 80.923 | 73 | 92.750 | 16 |
| 4 | 38 | 83.667 | 74 | 91.062 | 16 |
| 36 | 42 | 76.684 | 75 | 93.938 | 16 |
| 1 | 35 | 86.364 | 79 | 92.688 | 16 |

Round-specific winners:

| Rounds | Best rank(s) | Best HW |
|---:|---|---:|
| 12 | rank 20 | 73 |
| 16 | ranks 15 and 34 | 69 |
| 20 | rank 21 | 93 |
| 24 | rank 36 | 91 |

The HW35 seed is not a failure under the absorber proxy, but it is not the
leader. Several HW40-HW42 residuals appear more absorbable, and rank 11 has
the best aggregate mean among the top minima.

## Interpretation

This is not a certificate and not a real two-block Wang engine. It is only a
cheap proxy: treat the block-1 `diff63` as an XOR IV difference and ask a free
second block to reduce state-difference HW after R rounds.

Even with that caveat, the signal is useful:

- The block-1 HW objective and the absorber objective are not aligned.
- The HW35 residual is locally excellent for Path C, but it is not the best
absorber seed in this scout.
- Manifest ranks 3, 18, 19, 28, and 36 deserve more attention than their
block-1 HW ranking alone suggests.
- Today's compute should treat residuals as a Pareto set:
  `(block1_hw, bridge_score, absorber_r16, absorber_r20, basin_novelty)`.

## Recommended next compute

1. Feed the best absorber-ranked residuals back into pair-beam/carry-chart
   search, even if their block-1 HW is worse than 35.
2. Build a proper two-block meet table next: block 1 supplies residual
   signatures; block 2 supplies absorbable signatures; match by lane profile
   rather than scalar HW.
3. Run a longer focused absorber burn on ranks 11/15/21/34/36 plus HW35 as
   control, especially at rounds 20/24 where seed stability matters more.

## Verdict

Spend today's exploratory compute on the two-objective frontier, not on
linear F491 manifest continuation. HW35 remains the block-1 SOTA, but the
best side-effort path may run through a slightly worse, more absorbable
residual.

F512 command:

```bash
python3 headline_hunt/bets/block2_wang/encoders/run_absorber_matrix.py \
  --manifest headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F491_bit13_basin_seed_manifest_post_hw35.json \
  --out-dir headline_hunt/bets/block2_wang/results/search_artifacts/20260502_absorber_matrix_overnight \
  --label F512_f491_absorber_matrix \
  --rounds 12,16,20,24 \
  --seeds 0x20260502,0x20260512,0x20260522,0x20260532 \
  --iterations 5000000 \
  --compile
```
