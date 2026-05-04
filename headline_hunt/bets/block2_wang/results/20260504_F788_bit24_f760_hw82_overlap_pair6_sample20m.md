---
date: 2026-05-04
bet: block2_wang
status: BIT24_F760_HW82_OVERLAP_PAIR6_SAMPLE20M_NEGATIVE_DETOUR
parent: F787 bit-overlap diagnostic
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F788: bit24 F760 HW82 six-pair overlap sample

## Setup

F788 is the first six-pair combo sample from the original F760 bit24 HW82
parent. It uses the F787 pre-evaluation overlap idea instead of word graph or
aggregate lane-HW filters.

The selector keeps pair sets with:

```text
pair removed-bit union >= 80
pair added-bit union <= 170
pair added-bit repeat excess >= 250
```

Run parameters:

```text
candidate: bit24_mdc27e18c
init HW: 82
pair atlas: F767 top-80
selected pairs: 236
pair_count = 6
radius = 10..12
sampled combos = 20,000,000
rng seed = 788
```

## Result

```text
candidate combos: 20,000,000
skipped by overlap signature: 3,349,939
skipped radius: 2,014
skipped duplicate: 715
evaluated: 16,647,332
HW < 82: 0
HW <= 82: 0
c/g-improving: 40
target-L1-improving: 8,860
wall seconds: 3061.1
```

Best raw-HW sample:

```text
HW 86
target L1 16
c/g objective 130
lane [14, 13, 10, 8, 8, 8, 12, 13]
removed bits 56
added bits 60
standalone net-delta sum 175
nonlinear HW gain 171
word pairs [(1,11), (6,13), (12,12), (0,3), (0,8), (1,8)]
sources target + cg + repair + repair/repair_d + repair_h + repair_h
```

Best target-L1 sample:

```text
HW 89
target L1 9
c/g objective 129
lane [12, 10, 10, 12, 12, 9, 10, 14]
removed bits 57
added bits 64
standalone net-delta sum 173
nonlinear HW gain 166
```

## Interpretation

The overlap selector produces a new useful detour but does not preserve the
HW82 floor. It finds huge nonlinear cancellation, but the final state still
adds more bits than it removes:

```text
F788 best HW: removed 56, added 60 -> HW86
F788 best target: removed 57, added 64 -> HW89
```

This is the same failure mode as F782/F786 in a six-pair form. The selector can
shape lane signatures and find large nonlinear cancellation, but it still
cannot preselect combinations whose new added final bits are suppressed enough
to stay on the floor.

The positive residue is the best-HW detour. HW86 is not competitive with the
floor, but it is close enough to test with the standard pure-HW pair beam, the
same way F768's HW85 detour repaired to HW84.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_combo6.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F788_m2_combo_graph_motifs.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F788_m2_combo_cancellation.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F788_m2_combo_bit_overlap.json
```

## Next

Restart pure-HW M2 pair beam from the F788 HW86 detour. If that cannot repair
below HW86, close the overlap selector branch.
