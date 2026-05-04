---
date: 2026-05-04
bet: block2_wang
status: BIT24_F760_HW82_GRAPH_MOTIF_SAMPLE20M_NEGATIVE
parent: F781 late-word motif; F760/F763 source and graph analysis
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F782: bit24 F760 HW82 graph-motif 20M sample

## Setup

F782 tests the sharper word-pair graph motif extracted from the two known
bit24 HW82 compositions and the F776/F781 near misses.

The predecessor graph analysis found:

```text
F760 HW82: late-late pairs = 1, early-late pairs = 2
F763 HW82: late-late pairs = 1, early-late pairs = 3
F776 best HW85: late-late pairs = 0, early-late pairs = 2
F781 best HW86: late-late pairs = 1, early-late pairs = 1
```

So F782 reruns the broad F776 target+repair selection from the original F760
HW82 point, but only evaluates sampled five-pair combinations with at least one
late-late pair and at least two early-late bridge pairs.

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [9, 10, 11, 10, 10, 13, 13, 6]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 24
pair atlas: F767 top-80
selected pairs: 236
pair_count = 5
radius = 8..10
sampled combos = 20,000,000
graph motif: late-late >= 1, early-late >= 2
rng seed = 782
```

## Result

```text
candidate combos: 20,000,000
skipped by graph motif: 17,104,701
skipped duplicate: 4,944
skipped radius: 117
evaluated: 2,890,238
HW < 82: 0
HW <= 82: 0
c/g-improving: 8
target-L1-improving: 1,523
wall seconds: 544.0
```

Best raw-HW and target-L1 sample:

```text
HW 87
target L1 13
c/g objective 135, delta +5
lane [10, 8, 12, 15, 10, 7, 12, 13]
bits [8, 9, 178, 210, 215, 318, 389, 390, 464, 475]
word pairs [(0,12), (5,9), (14,14), (0,12), (6,6)]
sources target/repair/repair_f + cg + cg + repair + repair/repair_b
```

Best c/g sample:

```text
HW 94
c/g objective 126, delta -4
target L1 18
lane [14, 14, 7, 12, 11, 11, 9, 16]
```

## Interpretation

The graph motif is a useful discriminator but not a sufficient compatibility
rule. It rejects most of the broad sample and excludes the two best near-miss
templates from F776/F781, yet it still finds no HW82 tie in 2.89M evaluated
final states.

The best F782 record exactly satisfies the F760-style graph motif:

```text
late-touch pairs = 3
late-late pairs = 1
early-late pairs = 2
```

But it is still HW87 and uses a target-labeled pair. The two HW82 records were
repair-only compositions made from ugly standalone moves. That points to a
second compatibility axis: successful five-pair products may need repair-source
damage cancellation, not merely the right early/late word graph.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F782_bit24_f760_hw82_graph_motif_target_repair_sample20m_combo5.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F782_bit24_f760_hw82_graph_motif_target_repair_sample20m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F782_m2_combo_graph_motifs.json
```

## Next

Run the same graph motif with target-pair selection disabled, matching the
repair-only character of F760 and F763. If that is also negative, stop
word-graph filters and pivot to a nonlinear carry/damage-cancellation
signature.
