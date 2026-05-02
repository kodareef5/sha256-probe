---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT20_BIT18_SCOUT_DEEPENED
parent: F525 panel expansion; F563/F584 manifest-rank workflow
evidence_level: VERIFIED
author: yale-codex
---

# F585/F587: bit20 and bit18 pair-beam scout

## Setup

After F563/F584 pushed F525's top new cands (`bit1`, `bit4`) to HW35, this
run applied the same F521-style pair-beam settings to the next F525 new cands:

- `bit20_m294e1ea8`, seeded from F525 HW46
- `bit18_m99bf552b`, seeded from the F525 artifact's `best_hw` record HW45

Settings:

- pair pool 1024
- beam 1024
- max pairs 6
- max radius 12
- c/g penalty weight 2

## Results

| Run | Cand | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F585 | bit20 | 46 | 43 | 74.105 | `0x27336ee8 0x0117f64f 0x4ef5c884 0x320afc6c` |
| F586 | bit18 | 45 | 42 | 78.385 | `0xc67e23c3 0x61dac42f 0x48c35ae2 0xb8edf0de` |

F585 improves bit20 by 3 bits. F586 improves bit18 by 3 bits relative to the
artifact's true best-HW seed and by 7 bits relative to the F525 summary table.

## Cert-pin validation

`--solver all` remains unavailable on this host because `cryptominisat5` is not
installed. Each new record was validated with `kissat` and `cadical` separately.

| Witness | kissat | cadical |
|---|---|---|
| F585 bit20 HW43 | UNSAT, 0.010s | UNSAT, 0.018s |
| F586 bit18 HW42 | UNSAT, 0.009s | UNSAT, 0.019s |

Both are confirmed near-residuals, not full collisions.

## Basin manifests

F587 extracted reusable rank seeds from both pair-beam artifacts:

- `search_artifacts/20260502_F587_bit20_post_hw43_basin_manifest.json`
  with 21 seeds.
- `search_artifacts/20260502_F587_bit18_post_hw42_basin_manifest.json`
  with 23 seeds.

Top bit20 seeds:

| Rank | HW | Score | W57..W60 |
|---:|---:|---:|---|
| 1 | 43 | 74.105 | `0x27336ee8 0x0117f64f 0x4ef5c884 0x320afc6c` |
| 2 | 44 | 76.610 | `0x27336ee8 0x0117f64f 0x4ef5c884 0x7102f4f0` |
| 3 | 44 | 75.000 | `0x27336ee8 0x0117f64f 0x4ef5c884 0xf204f4c0` |
| 4 | 45 | 77.209 | `0x27336ee8 0x0117f64f 0x4ef5c884 0x1603e460` |

Top bit18 seeds:

| Rank | HW | Score | W57..W60 |
|---:|---:|---:|---|
| 1 | 42 | 78.385 | `0xc67e23c3 0x61dac42f 0x48c35ae2 0xb8edf0de` |
| 2 | 42 | 76.684 | `0xc67e23c3 0x61dac42f 0x48c35ae2 0x18e3cdde` |
| 3 | 42 | 76.684 | `0xc67e23c3 0x61dac42f 0x48c35ae2 0x44ecf0e6` |
| 4 | 43 | 79.073 | `0xc67e23c3 0x61dac42f 0x48c35ae2 0x08fbadde` |

## Note on F525 bit18

The F525 summary table lists `bit18_m99bf552b` as HW49. The artifact contains
two notions of "best": `best_per_cand` by objective/score at HW49 and
`best_hw_per_cand` at HW45. F586 intentionally seeds from `best_hw_per_cand`:

`0xc67e23c3 0x61dac42f 0x48c35ae2 0x88eab1de`.

Future floor tables should use the artifact's `best_hw_per_cand` when ranking
by residual HW.

## Updated panel slice

| Cand | Prior floor | New floor | Status |
|---|---:|---:|---|
| bit13 | 35 | 35 | unchanged co-best |
| bit1 | 35 | 35 | unchanged co-best |
| bit4 | 35 | 35 | unchanged co-best |
| bit3 | 36 | 36 | unchanged |
| bit2 | 39 | 39 | unchanged |
| bit24 | 40 | 40 | unchanged |
| bit18 | 45 | 42 | new scout floor |
| bit28 | 42 | 42 | unchanged |
| bit20 | 46 | 43 | new scout floor |

## Next

1. Run bit18 F587 ranks 2..6; it already has three HW42 seeds and one HW43 seed.
2. Run bit20 F587 ranks 2..5; the rank-2 score is stronger than rank 1 despite
   one extra HW bit.
3. If either reaches HW40 or lower, add small bridge-relaxed closure around the
   new floor before widening to the remaining F525 cands.
