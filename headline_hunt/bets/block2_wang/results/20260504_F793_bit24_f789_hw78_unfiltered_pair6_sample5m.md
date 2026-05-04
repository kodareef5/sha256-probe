---
date: 2026-05-04
bet: block2_wang
status: BIT24_HW78_PAIR6_SAMPLE5M_NEGATIVE_DETOUR
parent: F792 HW78 local restart closure
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F793: bit24 HW78 six-pair basin-transfer sample

## Setup

F793 tests whether the new F789 HW78 endpoint has another F788-style
basin-transfer move. It uses the F790 top-80 pair-potential atlas and samples
six-pair final-state compositions without an overlap filter.

```text
candidate: bit24_mdc27e18c
init HW: 78
pair atlas: F790 top-80
selected pairs: 251
pair_count = 6
radius = 10..12
sampled combos = 5,000,000
rng seed = 793
```

## Result

```text
candidate combos: 5,000,000
evaluated: 4,999,571
HW < 78: 0
HW <= 78: 0
c/g-improving: 0
target-L1-improving: 3
wall seconds: 758.4
```

Best raw-HW sample:

```text
HW 84
target L1 22
c/g objective 128
lane [8, 8, 10, 9, 14, 11, 12, 12]
standalone net-delta sum 169
nonlinear HW gain 163
sources target + target + repair_e + cg + repair/repair_a + repair
```

Best target-L1 sample:

```text
HW 94
target L1 12
c/g objective 132
lane [11, 12, 9, 15, 11, 11, 10, 15]
standalone net-delta sum 200
nonlinear HW gain 184
```

## Interpretation

The HW78 basin is much tighter than the F760/F788 parent. In 5M sampled six-pair
compositions, it produced no floor-preserving states and only three target-lane
improvements.

The best-HW sample is still worth one repair test. F788's HW86 detour repaired
to HW78 under standard pair beam, and F793's HW84 detour has similar large
nonlinear cancellation. If that beam closes, the HW78 basin-transfer branch is
closed at this scale.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F793_bit24_f789_hw78_unfiltered_pair6_sample5m_combo6.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F793_bit24_f789_hw78_unfiltered_pair6_sample5m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F793_m2_combo_cancellation.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F793_m2_combo_bit_overlap.json
```

## Next

Restart pure-HW M2 pair beam from the F793 HW84 detour.
