---
date: 2026-05-04
bet: block2_wang
status: BIT24_F760_HW82_DELTA_SIGNATURE_SAMPLE20M_NEGATIVE
parent: F785 F782 branch closure; F763 cancellation signature
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F786: bit24 F760 HW82 delta-signature 20M sample

## Setup

F786 adds a pre-evaluation lane-delta filter to `m2_target_pair_combo.py`.
Instead of filtering by word graph, it filters by the sum of standalone pair
effects from the pair-potential atlas.

The filter is modeled on the successful F763 HW82 composition:

```text
F763 delta-lane sum: [36, 33, 22, 29, 6, -1, 3, 35]
F763 standalone net-delta sum: 163
```

F786 requirements:

```text
standalone net-delta sum >= 140
delta lane b >= 25
delta lane c >= 18
delta lane g >= 0
delta lane h >= 30
```

Run parameters:

```text
candidate: bit24_mdc27e18c
init HW: 82
pair atlas: F767 top-80
selected pairs: 236
pair_count = 5
radius = 8..10
sampled combos = 20,000,000
rng seed = 786
```

## Result

```text
candidate combos: 20,000,000
skipped by delta signature: 19,729,820
skipped duplicate: 440
skipped radius: 5
evaluated: 269,735
HW < 82: 0
HW <= 82: 0
c/g-improving: 0
target-L1-improving: 128
wall seconds: 122.4
```

Best raw-HW sample:

```text
HW 93
target L1 23
c/g objective 141
lane [13, 14, 12, 9, 10, 12, 12, 11]
standalone net-delta sum 155
delta-lane sum [6, 29, 23, 34, 25, -9, 3, 44]
nonlinear HW gain 144
word pairs [(0,1), (7,8), (7,10), (6,11), (7,10)]
```

Best target-L1 sample:

```text
HW 97
target L1 17
c/g objective 139
lane [12, 14, 11, 13, 14, 10, 10, 13]
standalone net-delta sum 151
delta-lane sum [23, 25, 19, 17, 9, 11, 3, 44]
nonlinear HW gain 136
```

## Interpretation

This closes the simple delta-signature selector. F786 finds records with
F763-like standalone damage and very large nonlinear cancellation, but they
still land far above the HW82 floor.

The failure mode is sharper now:

```text
F763 HW82: nonlinear gain 163, final HW82
F786 best HW: nonlinear gain 144, final HW93
F786 best target: nonlinear gain 136, final HW97
```

Large cancellation and F763-like predicted damage are necessary-looking but not
sufficient. The missing feature is probably signed/carry-local, not visible in
lane-HW deltas alone.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F786_bit24_f760_hw82_delta_signature_sample20m_combo5.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F786_bit24_f760_hw82_delta_signature_sample20m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F786_m2_combo_graph_motifs.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F786_m2_combo_cancellation.json
```

## Next

Stop filtering on aggregate lane HW summaries. The next selector should inspect
signed bit positions or carry-chart overlap for the pair products, because the
aggregate HW-delta features cannot separate F763 from F786.
