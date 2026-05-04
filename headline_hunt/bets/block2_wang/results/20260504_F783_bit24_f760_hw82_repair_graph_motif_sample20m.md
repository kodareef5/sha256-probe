---
date: 2026-05-04
bet: block2_wang
status: BIT24_F760_HW82_REPAIR_GRAPH_MOTIF_SAMPLE20M_NEGATIVE
parent: F782 graph motif; F760/F763 repair-only source pattern
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F783: bit24 F760 HW82 repair-only graph-motif 20M sample

## Setup

F783 repeats F782's graph-motif test but disables target-pair selection. This
matches the source pattern of the two known HW82 records:

```text
F760 HW82 sources: repair/cg + repair_c + repair + repair + repair_a
F763 HW82 sources: repair + repair + repair_e + repair_e + repair_h
```

The graph gate is unchanged:

```text
late-late pairs >= 1
early-late bridge pairs >= 2
```

Selection and run parameters:

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [9, 10, 11, 10, 10, 13, 13, 6]
pair atlas: F767 top-80
target pairs = 0
repair pairs = 80
HW pairs = 20
c/g pairs = 40
per-register repair pairs = 10
selected pairs = 173
pair_count = 5
radius = 8..10
sampled combos = 20,000,000
rng seed = 783
```

## Result

```text
candidate combos: 20,000,000
skipped by graph motif: 17,035,587
skipped duplicate: 24,307
skipped radius: 180
evaluated: 2,939,926
HW < 82: 0
HW <= 82: 0
c/g-improving: 10
target-L1-improving: 1,546
wall seconds: 549.4
```

Best raw-HW and target-L1 sample:

```text
HW 90
target L1 14
c/g objective 138, delta +8
lane [9, 10, 13, 13, 10, 11, 11, 13]
bits [150, 154, 219, 266, 279, 299, 405, 411, 422, 481]
word pairs [(8,8), (4,12), (6,9), (12,13), (4,15)]
sources hw/cg + cg + repair_e + repair/repair_f + repair_d
```

Best c/g sample:

```text
HW 94
c/g objective 120, delta -10
target L1 26
lane [12, 11, 5, 15, 12, 18, 8, 13]
```

## Cancellation Check

F783 still shows nonlinear cancellation, but not enough:

```text
F760 HW82: nonlinear HW gain 127, final HW 82
F763 HW82: nonlinear HW gain 163, final HW 82
F782 best: nonlinear HW gain 112, final HW 87
F783 best: nonlinear HW gain 98, final HW 90
```

The best c/g state in F783 has stronger cancellation, 130, but it lands at
HW94 and target L1 26. Large cancellation alone is not the missing selector;
the cancellation has to land in the right lanes.

## Interpretation

This closes the simple word-graph branch. The graph motif is compatible with
the HW82 successes, but filtering on it does not recover floor-preserving
states in either the broad target+repair pool or the repair-only pool.

The useful positive residue is F782's HW87 / target L1 13 detour. It is much
closer to the bit13 lane signature than F760's starting HW82 point, so the next
operator should not be another broad graph sample. It should try a standard
pair-beam restart from that detour and see whether local repair can pull HW
back down.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F783_bit24_f760_hw82_repair_graph_motif_sample20m_combo5.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F783_bit24_f760_hw82_repair_graph_motif_sample20m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F783_m2_combo_graph_motifs.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F783_m2_combo_cancellation.json
```

## Next

Restart `block2_m2_pair_beam.py` from the F782 HW87 / target L1 13 detour. Use
pure HW first, then c/g only if the HW restart finds a new floor or a better
side basin.
