---
date: 2026-04-28
bet: cascade_aux_encoding
status: SELECTOR_EMITS_MANIFESTS
---

# F313: hard-core selector emits runnable cube manifests

## Purpose

F311 ranked schedule bits from hard-core membership plus observed stats. F312
still required manually copying selected shell bits into `schedule_cube_planner`.
F313 closes that loop: `hard_core_cube_seeds.py` can now emit a runnable
`run_schedule_cubes.py` manifest directly from its ranked rows.

## Tool Change

`hard_core_cube_seeds.py` now supports:

- `--cnf`: base CNF for DIMACS header metadata;
- `--emit-manifest`: output JSONL manifest;
- `--emit-depth`: depth for selected-bit cubes;
- `--emit-top`: number of ranked bits to use;
- `--only-core-class`: restrict selected bits, e.g. `shell` or `both_core`.

The emitted records include a compact `selector` field carrying bit score,
core class, metric, and preferred value.

## Verification Manifests

Shell W2_57 top-4 unit manifest:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/hard_core_cube_seeds.py \
  --hard-core-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F311_auxforce_sr61_bit25_hard_core.json \
  --target w2 --round 57 --top 4 --only-core-class shell \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --emit-manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F313_w2r57_shell_top4_auto_manifest.jsonl
```

Output: 8 cube records over shell bits `31,30,29,27`.

Hard-core/stat-ranked dW59 top-4 depth-2 manifest:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/hard_core_cube_seeds.py \
  --hard-core-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F311_auxforce_sr61_bit25_hard_core.json \
  --target dw --round 59 --metric decisions \
  --stats-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F306_auxforce_sr61_bit25_dw59_depth1_cadical_50k_stats.jsonl \
  --stats-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cadical_100k_stats.jsonl \
  --stats-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F309_auxforce_sr61_bit25_dw59_depth3_outlier_expansion_cadical_100k_stats.jsonl \
  --top 4 --only-core-class both_core \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --emit-depth 2 --emit-top 4 \
  --emit-manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F313_dw59_decision_top4_depth2_auto_manifest.jsonl
```

Output: 24 cube records over bits `29,19,1,3`.

## Interpretation

This is infrastructure, not a new solver claim. It turns the F310-F312 loop into
a repeatable pipeline:

1. decompose a CNF into hard-core/shell JSON;
2. rank schedule bits using hard-core membership and optional solver stats;
3. emit a manifest that the cube runner can execute without hand selection.

The immediate value is error reduction. Future probes can compare shell, core,
and observed-stat selections by changing selector flags instead of editing bit
lists by hand.
