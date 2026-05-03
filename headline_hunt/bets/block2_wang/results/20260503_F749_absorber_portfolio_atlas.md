---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_PORTFOLIO_ATLAS
parent: F732-F748 M2 pair-beam and path-C absorber runs
evidence_level: VERIFIED_JSON_ARTIFACTS
author: yale-codex
---

# F749: current absorber portfolio atlas

## Scope

This consolidates the mapped 24-round M2 absorber geometry after the HW82
bit13 breakthrough, HW82 closure passes, rank18 HW83 follow-up, and path-C
cross-candidate expansion.

The atlas was generated with:

```text
headline_hunt/bets/block2_wang/encoders/m2_pair_beam_atlas.py
```

over the key F732-F748 artifacts.

## Portfolio

| Candidate / basin | Best HW | Closure checks | Lane HW at best |
|---|---:|---|---|
| bit13 / rank2 | 82 | HW r12, c/g r12, weighted r12, HW r16, c/g r16, weighted r16 | `10,11,9,12,9,7,10,14` |
| bit13 / rank18 | 83 | c/g r12 | `10,11,8,11,13,8,12,10` |
| bit24 path-C | 85 | c/g r12, c/g r16 | `9,10,10,13,13,12,13,5` |
| bit3 path-C | 86 | c/g r12 | `10,18,9,6,9,13,11,10` |
| bit4 path-C | 89 | c/g r12 | `14,11,9,10,13,9,9,14` |

## Key rows

| Artifact | Init | Best | Delta | Records | Wall(s) | Lane HW |
|---|---:|---:|---:|---:|---:|---|
| `20260503_F732_hw85_cg_objective_m2_pair_beam.json` | 85 | 82 | -3 | 2 | 676.9 | `10,11,9,12,9,7,10,14` |
| `20260503_F738_rank18_m2_pair_beam.json` | 128 | 83 | -45 | 2235246 | 697.0 | `10,11,8,11,13,8,12,10` |
| `20260503_F547_pathC_rank0_m2_pair_beam.json` | 126 | 86 | -40 | 1775901 | 722.3 | `10,18,9,6,9,13,11,10` |
| `20260503_F547_pathC_rank1_m2_pair_beam.json` | 127 | 86 | -41 | 2004962 | 723.5 | `11,12,12,13,8,10,11,9` |
| `20260503_F746_pathC_rank1_hw86_cg_m2_pair_beam.json` | 86 | 85 | -1 | 1 | 677.5 | `9,10,10,13,13,12,13,5` |
| `20260503_F547_pathC_rank2_m2_pair_beam.json` | 132 | 89 | -43 | 3148211 | 729.9 | `14,11,9,10,13,9,9,14` |

## Interpretation

The M2 pair-beam operator is broadly reusable. It pulls cold path-C absorbers
from HW126-HW132 into HW86-HW89, and c/g ranking can deepen some basins.

But the endpoint is candidate-dependent:

```text
bit13 -> HW82
bit24 -> HW85
bit3  -> HW86
bit4  -> HW89
```

That pattern argues against one universal local pair-beam floor. The block-1
residual geometry still controls how deep the absorber can go.

## Next operator direction

Further progress should stop treating pair-beam variants as the main novelty.
The next useful tool is a selection/atlas step:

1. Score candidate basins by lane-vector similarity to the bit13 HW82 and
   rank18 HW83 endpoints.
2. Build a pair-potential atlas around best witnesses that records not only
   immediate HW, but lane-delta direction and whether moves preserve the
   low-lane signature.
3. Use that atlas to choose non-local compositions rather than relying on a
   fixed HW/c/g/weighted pair ranking.

The immediate concrete target is a small pair-potential atlas around the
bit13 HW82, bit24 HW85, bit3 HW86, bit4 HW89, and rank18 HW83 witnesses.
