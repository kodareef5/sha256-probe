---
date: 2026-05-04
bet: block2_wang
status: BIT13_HW82_OVERLAP_PAIR6_SAMPLE5M_NEGATIVE_TRANSFER
parent: F732 bit13 HW82 / F751 pair atlas
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F795: bit13 HW82 six-pair overlap-transfer sample

## Setup

F795 applies the F788 overlap-detour selector to a different HW82 parent:
bit13/F732, using the F751 bit13 pair-potential atlas.

```text
candidate: bit13
init HW: 82
init lane: [10, 11, 9, 12, 9, 7, 10, 14]
pair atlas: F751 bit13 HW82 self-lane atlas
selected pairs: 137
pair_count = 6
radius = 10..12
sampled combos = 5,000,000
rng seed = 795

overlap filter:
  pair removed-bit union >= 80
  pair added-bit union <= 170
  pair added-bit repeat excess >= 250
```

## Result

```text
candidate combos: 5,000,000
skipped radius/duplicate: 1,831
skipped by overlap signature: 904,026
evaluated: 4,094,143
HW < 82: 0
HW <= 82: 0
c/g-improving: 0
target-L1-improving: 0
wall seconds: 780.3
```

Best raw-HW sample:

```text
HW 90
target L1 14
c/g objective 140
lane [9, 14, 15, 12, 9, 9, 10, 12]
standalone net-delta sum 201
nonlinear HW gain 193
word pairs: (2,4), (5,10), (12,14), (1,8), (1,7), (9,11)
sources: cg + repair_c + repair_d + repair_f + repair_h + repair_c
```

Best target-L1 sample:

```text
HW 92
target L1 12
c/g objective 134
lane [12, 10, 10, 12, 12, 11, 11, 14]
standalone net-delta sum 163
nonlinear HW gain 153
word pairs: (12,13), (3,12), (1,6), (3,11), (9,15), (2,9)
sources: target/hw + repair_f + repair_g + repair_b + repair_g + repair
```

Best-HW M2:

```text
0x20500008,0x42400000,0x00000101,0x00100008,
0x40021000,0x50000200,0x08040000,0x00500000,
0x08480000,0x00080008,0x24000000,0x40020800,
0x040100c1,0x00004200,0x80010000,0x00000008
```

## Interpretation

This is a negative transfer test. The same overlap signature that created the
F788 bit24 HW86 side basin did not preserve or improve the bit13 HW82 floor in
5M sampled six-pair compositions.

The best bit13 detours still show large nonlinear cancellation, but the
starting parent is too brittle: no sampled combo improved HW, c/g, or target
distance. That is materially weaker than F788, which produced thousands of
target-lane improvements and a repairable HW86 detour.

The immediate conclusion is to spend the next overlap-detour budget on another
bit24 HW82 tie rather than widening bit13. If the second bit24 tie also
transfers, the operator is probably family-specific; if it fails, F788/F789
may be an isolated lucky branch.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F795_bit13_hw82_overlap_pair6_sample5m_combo6.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F795_bit13_hw82_overlap_pair6_sample5m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F795_m2_combo_cancellation.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F795_m2_combo_bit_overlap.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F795_m2_combo_graph_motifs.json
```

## Next

Run the same overlap-detour pattern on the other mapped bit24 HW82 tie
(F763/F764), then only launch a repair beam if that sample finds a plausible
HW86-HW90 detour with target-lane structure.
