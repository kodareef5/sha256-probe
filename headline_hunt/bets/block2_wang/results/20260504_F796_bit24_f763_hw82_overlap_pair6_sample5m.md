---
date: 2026-05-04
bet: block2_wang
status: BIT24_F763_HW82_OVERLAP_PAIR6_SAMPLE5M_DETOUR
parent: F763 bit24 HW82 / F764 pair atlas
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F796: bit24 F763 HW82 six-pair overlap-transfer sample

## Setup

F796 applies the F788 overlap-detour selector to the second mapped bit24 HW82
tie, F763/F764. This tests whether the F788 -> F789 HW78 chain was a general
bit24-family operator or specific to the original F760 parent.

```text
candidate: bit24_mdc27e18c
seed JSONL: F547_pathC_absorber_seeds.jsonl
seed rank: 1
init HW: 82
init lane: [7, 10, 12, 16, 11, 7, 8, 11]
pair atlas: F764 top-80
selected pairs: 248
pair_count = 6
radius = 10..12
sampled combos = 5,000,000
rng seed = 796

overlap filter:
  pair removed-bit union >= 80
  pair added-bit union <= 170
  pair added-bit repeat excess >= 250
```

## Result

```text
candidate combos: 5,000,000
skipped radius/duplicate: 440
skipped by overlap signature: 757,132
evaluated: 4,242,428
HW < 82: 0
HW <= 82: 0
c/g-improving: 0
target-L1-improving: 49
wall seconds: 826.7
```

Best raw-HW sample:

```text
HW 87
target L1 15
c/g objective 129
lane [10, 11, 9, 14, 11, 11, 12, 9]
standalone net-delta sum 161
nonlinear HW gain 156
word pairs: (12,14), (1,1), (8,11), (2,6), (9,10), (0,5)
sources: target + target + target + repair_e + repair_g + repair_c
```

Best target-L1 sample:

```text
HW 92
target L1 10
c/g objective 136
lane [11, 11, 11, 14, 11, 9, 11, 14]
standalone net-delta sum 185
nonlinear HW gain 175
sources: repair-heavy
```

Best-HW M2:

```text
0x00001042,0x00120004,0x01004084,0x40105003,
0x00000000,0x14021040,0x00000002,0x00200000,
0x08802000,0x20020240,0x05808108,0x00000020,
0x01404000,0x00050800,0x12038100,0x00000040
```

## Interpretation

F796 is a weaker but nonempty version of the F788 transfer pattern. It did not
preserve the HW82 floor, and its target-improvement density is much lower than
F788:

```text
F788/F760 overlap sample: 8,860 target improvements / 16.65M evals
F796/F763 overlap sample:    49 target improvements /  4.24M evals
F795/bit13 overlap sample:    0 target improvements /  4.09M evals
```

The F763 parent is therefore tighter than F760 under the same overlap
signature, but it is not as inert as bit13. The HW87 detour is close enough to
justify one standard pure-HW repair beam. If that fails, treat the F763 branch
as closed at this scale.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F796_bit24_f763_hw82_overlap_pair6_sample5m_combo6.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F796_bit24_f763_hw82_overlap_pair6_sample5m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F796_m2_combo_cancellation.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F796_m2_combo_bit_overlap.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F796_m2_combo_graph_motifs.json
```

## Next

Run F797: standard pure-HW pair-beam repair from the F796 HW87 detour.
