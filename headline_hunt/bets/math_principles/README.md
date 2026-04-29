# math_principles

This bet turns the April 2026 math-principles survey into small, checkable
tools. The first implementation slice focuses on measurement and triage rather
than new solver volume:

- shared manifest over existing artifacts
- REM/tail-law fit for block2 scores
- empirical influence priors for active words/pairs
- hard-core/carry-invariant audit from sr60/sr61 stability artifacts

The scripts are intentionally dependency-free and consume repo artifacts that
already exist.

## Current slice

Run these from the repo root:

```bash
python3 headline_hunt/bets/math_principles/encoders/build_principles_manifest.py
python3 headline_hunt/bets/math_principles/encoders/fit_tail_law.py
python3 headline_hunt/bets/math_principles/encoders/rank_influence_priors.py
python3 headline_hunt/bets/math_principles/encoders/audit_carry_invariants.py
python3 headline_hunt/bets/math_principles/encoders/select_submodular_masks.py
python3 headline_hunt/bets/math_principles/encoders/summarize_submodular_scan.py
python3 headline_hunt/bets/math_principles/encoders/build_cluster_atlas.py
python3 headline_hunt/bets/math_principles/encoders/plan_radius1_basin_walk.py
python3 headline_hunt/bets/math_principles/encoders/summarize_radius1_scan.py
python3 headline_hunt/bets/math_principles/encoders/summarize_new88_continuation.py
python3 headline_hunt/bets/math_principles/encoders/summarize_atlas_weight_sweep.py
python3 headline_hunt/bets/math_principles/encoders/probe_atlas_neighborhood.py
python3 headline_hunt/bets/math_principles/encoders/continue_atlas_from_seed.py
```

The original manifest slice intentionally excludes downstream math-principles
calibration scans. To build a v2 manifest that promotes F347/F350 discoveries:

```bash
python3 headline_hunt/bets/math_principles/encoders/build_principles_manifest.py \
  --include-math-results \
  --out-jsonl headline_hunt/bets/math_principles/data/20260429_principles_manifest_v2.jsonl \
  --summary-json headline_hunt/bets/math_principles/results/20260429_F351_manifest_v2_summary.json
```

Default outputs:

- `data/20260429_principles_manifest.jsonl`
- `data/20260429_principles_manifest_v2.jsonl`
- `data/20260429_F343_submodular_masks.txt`
- `data/20260429_F346_radius1_basin_walk_masks.txt`
- `results/20260429_manifest_summary.json`
- `results/20260429_F351_manifest_v2_summary.json`
- `results/20260429_F340_tail_law.{json,md}`
- `results/20260429_F341_influence_priors.{json,md}`
- `results/20260429_F342_carry_invariant_audit.{json,md}`
- `results/20260429_F343_submodular_selectors.{json,md}`
- `results/20260429_F344_submodular_mask_calibration_scan_summary.{json,md}`
- `results/20260429_F345_cluster_atlas.{json,md}`
- `results/20260429_F346_radius1_basin_walk_plan.{json,md}`
- `results/20260429_F347_radius1_basin_walk_scan_summary.{json,md}`
- `results/20260429_F350_radius1_new88_continuation_summary.{json,md}`
- `results/20260429_F352_new88_atlas_weight_sweep_summary.{json,md}`
- `results/20260429_F353_alpha12_best_a57_atlas_probe_r2.{json,md}`
- `results/20260429_F354_alpha4_best_chart_atlas_probe_r2.{json,md}`
- `results/20260429_F355_seeded_atlas_commonmode_continuation_4x20k.{json,md}`

## Readout

F340 says the bit19 active-subset scores are not behaving like a plain REM
tail. Score <= 90 appears far more often than the Gaussian null predicts, so
the next search should treat the low-score masks as structured basins.

F341 gives the first active-word priors from that same corpus. Word 3 ranks
first; pairs `6,11`, `3,8`, `8,9`, and `1,3` are the strongest current pair
signals. The `{1,3}` axis survives as useful but not exclusive.

F342 promotes the late-round carry/core rule: sr60 has all last-two free-round
bits in stable core, and sr61 misses by one bit. First-free-round behavior is
still candidate-specific.

F343 is the first Track 6 bridge. It ranks size-5 active-word masks by a
monotone submodular coverage objective over the low-score evidence plus F341
word priors, then emits a calibration subset list for the existing block2
scanner. The raw objective is not yet a trusted selector; its top observed
masks were poor, so the emitted list preserves known-good controls.

F344 scanned that F343 list with the existing block2 active-subset scanner.
The result is negative at this budget: best score 92, no score <= 90, and the
best unseen selector mask scored 96.

F345 is the first Track 2 cluster atlas. It graphs observed active masks by
one-word swaps and checks whether low scores are isolated or connected through
near-score bridges.

F346 turns the F345 atlas into a bounded queue: known <=95 bridge controls
plus unseen one-swap neighbors around the score <=90 masks.

F347 scanned the F346 queue at 4x10k and found a new unseen score-88 mask:
`2,6,11,12,13`.

F350 continued the new score-88 mask. It is narrow: no-kick seeding preserves
88, kicked continuation loses the basin, and single-bit polish does not descend.

F351 rebuilds the manifest with F344/F347/F350 included. The promoted score-88
mask increases the low-score set to 16 masks; the <=90 graph now has 5 direct
one-swap edges and a largest low component of 4 masks.

F352 cross-feeds the MacBook carry-chart atlas loss back into the new score-88
mask `2,6,11,12,13`. Raising the `a57_xor` penalty alone does not lock the
candidate into the chamber: alpha 12 finds `a57=4`, but on chart
`dCh,dSig1`; the best chart-compatible points stay at `a57=5`.

F353/F354 turn the chart issue into a deterministic local-neighborhood probe.
The alpha-12 low-guard point is locally stiff under radius-2 raw/common message
moves. The alpha-4 chart-compatible point is not: a two-bit common-mode move
improves atlas score from 43.3 to 37.9 while preserving the `dh,dCh` chart and
dropping D61 from 17 to 11.

F355 seeds stochastic continuation from the F354 common-mode improvement. At
4x20k it preserves the 37.9 atlas score but does not extend it, so the move is
currently a deterministic polish operator rather than a robust stochastic
descent path.

## Next tracks

- add outcome-aware calibration before spending more budget on F343-style selectors
- use F342 stable-core coordinates as hard features for BP/matroid audits
- use common-mode atlas continuation as a post-atlas polish operator
