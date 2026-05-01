---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BASIN_SEED_MANIFEST
parent: F467/F471/F472 intermediate-basin work
evidence_level: TOOLING
compute: JSON artifact mining; no search evaluations
author: yale-codex
---

# F473: reusable basin seed manifest

## Setup

F467 showed that the best next seed is not always the current record. To
make that tactic repeatable, F473 adds:

`headline_hunt/bets/block2_wang/encoders/extract_basin_seeds.py`

The tool reads pair-beam artifacts, extracts `best_seen`, `new_records`, and
`top_records`, deduplicates by candidate and W tuple, and emits a compact
manifest of reusable seeds with `pair_beam_init_W_arg` and
`pair_beam_init_hw_arg`.

Generated artifact:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F473_bit13_basin_seed_manifest.json`

Input artifacts:

- F458 bit13 HW41 wider pair beam
- F462 bit13 HW38 wider pair beam
- F467 bit13 HW40 intermediate pair beam
- F471 bit13 HW36 restart
- F472 bit13 HW38 F467-intermediate restart

## Result

The manifest contains 35 deduplicated bit13 seeds. Top entries:

| Rank | HW | Score | W1 |
|---:|---:|---:|---|
| 1 | 36 | 85.471 | `0x5228ed8d 0x61a1a29c 0x6a3a8409 0x2c9e917b` |
| 2 | 38 | 83.667 | `0x5228ed8d 0x61a1a29c 0xea3a8429 0x2d9f1a3b` |
| 3 | 38 | 83.667 | `0x5228ed8d 0x61a1a29c 0xea3a8c29 0x258bfd92` |
| 4 | 39 | 82.757 | `0x5228ed8d 0x61a1a29c 0xea3a8c29 0x2589119a` |
| 5 | 39 | 82.757 | `0x5228ed8d 0x61a1a29c 0xea3a8c29 0x2d8b5d92` |
| 6 | 40 | 81.842 | `0x5228ed8d 0x61a1a29c 0x6a3a8409 0x149f957b` |

## Verdict

F473 turns the intermediate-basin tactic into a reusable workflow. The next
search should sample ranks 4-10 from this manifest before spending more
time on direct record-seed restarts.
