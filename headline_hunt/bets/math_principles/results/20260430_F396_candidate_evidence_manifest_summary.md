---
date: 2026-04-30
bet: math_principles
status: CANDIDATE_EVIDENCE_MANIFEST
---

# F396: candidate evidence manifest

## Summary

Manifest: `headline_hunt/bets/math_principles/data/20260430_F396_candidate_evidence_manifest.jsonl`.
Rows: 119; candidates with evidence: 67.
Registry candidates: 67.
F387 class histogram: `{'A': 51, 'B': 16}`.
Preflight clause sets: 21.
Block2 cert-pin witnesses: 11.
Best block2 bridge-beam HW in manifest: 56.

## Rows By Kind

| Kind | Rows |
|---|---:|
| `block2_bridge_beam_best` | 4 |
| `block2_certpin_witness` | 11 |
| `cascade_w57_pair_probe` | 6 |
| `math_bridge_cube` | 9 |
| `math_w57_pair_core` | 1 |
| `preflight_clause_set` | 21 |
| `registry_candidate` | 67 |

## Candidate Evidence Density

| Candidate | Rows | Kinds |
|---|---:|---|
| `bit31_m17149975_fillffffffff` | 15 | `{"cascade_w57_pair_probe": 1, "math_bridge_cube": 9, "math_w57_pair_core": 1, "preflight_clause_set": 3, "registry_candidate": 1}` |
| `bit2_ma896ee41_fillffffffff` | 8 | `{"block2_bridge_beam_best": 1, "block2_certpin_witness": 6, "registry_candidate": 1}` |
| `bit28_md1acca79_fillffffffff` | 6 | `{"block2_bridge_beam_best": 1, "block2_certpin_witness": 4, "registry_candidate": 1}` |
| `bit0_m8299b36f_fill80000000` | 5 | `{"cascade_w57_pair_probe": 1, "preflight_clause_set": 3, "registry_candidate": 1}` |
| `bit10_m3304caa0_fill80000000` | 5 | `{"cascade_w57_pair_probe": 1, "preflight_clause_set": 3, "registry_candidate": 1}` |
| `bit11_m45b0a5f6_fill00000000` | 5 | `{"cascade_w57_pair_probe": 1, "preflight_clause_set": 3, "registry_candidate": 1}` |
| `bit13_m4d9f691c_fill55555555` | 5 | `{"cascade_w57_pair_probe": 1, "preflight_clause_set": 3, "registry_candidate": 1}` |
| `bit17_m427c281d_fill80000000` | 5 | `{"cascade_w57_pair_probe": 1, "preflight_clause_set": 3, "registry_candidate": 1}` |
| `bit13_m916a56aa_fillffffffff` | 3 | `{"block2_bridge_beam_best": 1, "block2_certpin_witness": 1, "registry_candidate": 1}` |
| `bit29_m17454e4b_fillffffffff` | 3 | `{"preflight_clause_set": 2, "registry_candidate": 1}` |

## Immediate Use

- Use this table as the join point for REM/tail, influence, preflight, and bridge-score follow-ups.
- Keep cert-pin and aux-force evidence separated; cert-pin is UP-trivial while aux-force carries the CDCL learning signal.
- Treat F343/F344 clause count as mostly exhausted per F395; the next useful operator axis is decision priority / VSIDS trajectory.
