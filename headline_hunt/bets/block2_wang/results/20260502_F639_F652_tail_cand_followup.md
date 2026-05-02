---
date: 2026-05-02
bet: block2_wang
status: PATH_C_TAIL_CAND_FOLLOWUP
parent: F531 all-cands-under-42 milestone
evidence_level: VERIFIED_AND_LOCALLY_CLOSED
author: yale-codex
---

# F639/F652: tail-cand follow-up

## Setup

After F531 put all 16 cands at HW <= 42, the tail cands were:

- `bit12_m8cbb392c`, HW41
- `bit26_m11f9d4c7`, HW41
- `bit6_m6e173e58`, HW42

F639 extracted fresh manifests for those cands. F640/F645 tested ranks 2 and 3
for each using the standard pair-beam settings.

## Results

| Run | Cand | Rank | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---:|---|
| F640 | bit12 | 2 | 41 | 40 | 81.842 | `0x6e835350 0x8322f4cf 0x30dd0ed1 0x927f3e65` |
| F641 | bit12 | 3 | 41 | 40 | 81.842 | `0x6e835350 0x8322f4cf 0x30dd0ed1 0x927f3e65` |
| F642 | bit26 | 2 | 44 | 39 | 81.000 | `0xbfe07c65 0x012df925 0xae91ccb9 0x715d9e89` |
| F643 | bit26 | 3 | 44 | 42 | 80.000 | `0xbfe07c65 0x012df925 0xae91ccb9 0x31da1d8f` |
| F644 | bit6 | 2 | 45 | 42 | 78.385 | `0x58e6e512 0xf2a359c0 0x22420dc5 0x9d542a79` |
| F645 | bit6 | 3 | 45 | 45 | 77.209 | `0x58e6e512 0xf2a359c0 0x28420dc7 0x1d18ba6c` |

F640/F641 move bit12 to HW40. F642 moves bit26 to HW39. Bit6 remains the
panel tail at HW42.

## Cert-pin validation

The first manual cert-pin commands in this work block were rerun after checking
artifact W values. This table records only the corrected artifact witnesses.

| Witness | kissat | cadical |
|---|---|---|
| F640 bit12 HW40 | UNSAT, 0.011s | UNSAT, 0.020s |
| F642 bit26 HW39 | UNSAT, 0.012s | UNSAT, 0.015s |

Both are confirmed near-residuals, not full collisions.

## Refreshed manifests

F650 refreshed the post-follow-up manifests:

- `search_artifacts/20260502_F650_bit12_post_hw40_basin_manifest.json`
  with 74 seeds.
- `search_artifacts/20260502_F650_bit26_post_hw39_basin_manifest.json`
  with 67 seeds.
- `search_artifacts/20260502_F650_bit6_post_hw42_basin_manifest.json`
  with 49 seeds.

Top seeds:

| Cand | Rank | HW | Score | W57..W60 |
|---|---:|---:|---:|---|
| bit12 | 1 | 40 | 81.842 | `0x6e835350 0x8322f4cf 0x30dd0ed1 0x927f3e65` |
| bit12 | 2 | 40 | 81.842 | `0x6e835350 0x8322f4cf 0x30dd0ed5 0x818a358c` |
| bit26 | 1 | 39 | 81.000 | `0xbfe07c65 0x012df925 0xae91ccb9 0x715d9e89` |
| bit26 | 2 | 41 | 80.923 | `0xbfe07c65 0x012df925 0xae91cc39 0x237d9d4d` |
| bit6 | 1 | 42 | 78.385 | `0x58e6e512 0xf2a359c0 0x22420dc5 0x9d542a79` |
| bit6 | 2 | 45 | 77.209 | `0x58e6e512 0xf2a359c0 0x28460dd5 0x9d5aa2cc` |

## Local closure

Exact bridge-relaxed closure around the new bit12 HW40 witness:

| Run | Cand | Floor | Slots | Radius | Total at max radius | Bridge pass | Bridge reject | HW<=floor | HW<floor |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| F646 | bit12 | 40 | W60 | 6 | 906,192 | 905,487 | 705 | 0 | 0 |
| F647 | bit12 | 40 | W59,W60 | 4 | 635,376 | 635,298 | 78 | 0 | 0 |

Exact bridge-relaxed closure around the new bit26 HW39 witness:

| Run | Cand | Floor | Slots | Radius | Total at max radius | Bridge pass | Bridge reject | HW<=floor | HW<floor |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| F648 | bit26 | 39 | W60 | 6 | 906,192 | 906,192 | 0 | 0 | 0 |
| F649 | bit26 | 39 | W59,W60 | 4 | 635,376 | 635,376 | 0 | 0 | 0 |

Exact bridge-relaxed closure around the current bit6 HW42 witness:

| Run | Cand | Floor | Slots | Radius | Total at max radius | Bridge pass | Bridge reject | HW<=floor | HW<floor |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| F651 | bit6 | 42 | W60 | 6 | 906,192 | 906,192 | 0 | 0 | 0 |
| F652 | bit6 | 42 | W59,W60 | 4 | 635,376 | 635,376 | 0 | 0 | 0 |

## Updated panel tail

After this checkpoint, the tail is:

| Cand | Floor HW |
|---|---:|
| bit24 | 40 |
| bit12 | 40 |
| bit28 | 42 |
| bit6 | 42 |

All other active Path C cands are HW39 or lower.
