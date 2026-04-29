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
python3 headline_hunt/bets/math_principles/encoders/chamber_seed_linear_lift.py
python3 headline_hunt/bets/math_principles/encoders/optimize_chamber_seed_freevars.py
python3 headline_hunt/bets/math_principles/encoders/build_chamber_seed_pareto_front.py
python3 headline_hunt/bets/math_principles/encoders/continue_atlas_from_pareto.py
python3 headline_hunt/bets/math_principles/encoders/extend_atlas_continuation.py
python3 headline_hunt/bets/math_principles/encoders/probe_descendant_neighborhood.py
python3 headline_hunt/bets/math_principles/encoders/probe_d61_repair_moves.py
python3 headline_hunt/bets/math_principles/encoders/probe_guard_repair_third_moves.py
python3 headline_hunt/bets/math_principles/encoders/continue_atlas_kernel_safe.py
python3 headline_hunt/bets/math_principles/encoders/extend_kernel_safe_continuation.py
python3 headline_hunt/bets/math_principles/encoders/probe_kernel_safe_neighborhood.py
python3 headline_hunt/bets/math_principles/encoders/beam_kernel_safe_neighborhood.py
python3 headline_hunt/bets/math_principles/encoders/search_kernel_safe_junction.py
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
- `results/20260429_F356_chamber_seed_linear_lift.{json,md}`
- `results/20260429_F357_chamber_seed_freevar_opt.{json,md}`
- `results/20260429_F358_chamber_seed_freevar_opt_long.{json,md}`
- `results/20260429_F359_chamber_seed_freevar_atlas_objective.{json,md}`
- `results/20260429_F360_chamber_seed_pareto_front.{json,md}`
- `results/20260429_F361_pareto_seeded_atlas_continuation.{json,md}`
- `results/20260429_F362_pareto_descendant_continuation.{json,md}`
- `results/20260429_F363_d61_weighted_descendant_continuation.{json,md}`
- `results/20260429_F364_m1_move_descendant_continuation.{json,md}`
- `results/20260429_F365_descendant_neighborhood_r1.{json,md}`
- `results/20260429_F366_d61_repair_pair_probe.{json,md}`
- `results/20260429_F367_guard_repair_third_probe.{json,md}`
- `results/20260429_F368_guard_lowered_fourth_probe.{json,md}`
- `results/20260429_F369_kernel_safe_pareto_continuation.{json,md}`
- `results/20260429_F370_kernel_safe_descendant_continuation.{json,md}`
- `results/20260429_F371_kernel_safe_neighborhood_r1.{json,md}`
- `results/20260429_F372_kernel_safe_beam_probe.{json,md}`
- `results/20260429_F373_kernel_safe_junction_search.{json,md}`

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

F356 starts the chamber-seeded initialization path suggested by the MacBook
F314 memo. The no-carry GF(2) schedule lift exactly matches chamber
`W57..W59` in the linear model and has rank 96 with 416 free variables. True
modular carries break the best sampled seed by 30 bits, so the lift has signal
but needs carry-aware free-variable optimization before it is a chamber seed.

F357 keeps the exact F356 no-carry chamber constraint and hill-climbs the 416
free variables against true modular `W57..W59` mismatch. A short 4x50k run
improves 30 bits to 25 bits, confirming that the free variables carry real
correction signal even before adding a carry-feature objective.

F358 lengthens the free-variable search to 8x100k with up to four free-bit
flips per proposal. It improves the chamber schedule mismatch again, reaching
24 bits (`6,12,6` by round). That crosses the near-chamber gate, but the atlas
rec is still off-attractor (`a57=14`, chart `dSig1,dh`), so schedule proximity
and cascade-state proximity must be optimized together next.

F359 adds atlas terms to the free-variable objective. It can hold the
chamber chart and found an accepted `a57=8` side candidate, but the best scalar
objective settled at 29-bit schedule mismatch with `a57=17`. This exposes a
Pareto problem rather than a simple weighted-sum problem: schedule closeness,
chart membership, and the a57 guard should be tracked as separate fronts.

F360 implements that Pareto-front view over true `W57..W59` mismatch, chart
penalty, `a57_xor_hw`, and `D61_hw`. The 84k-eval run produced a 43-point
front. The best mismatch member is 26 bits but off-chart; the best chart/guard
member is `a57=5` on `dh,dCh` but 50 bits from the chamber schedule. This
confirms the chamber-seed problem is a multi-objective tradeoff, not a
weight-tuning problem.

F361 continues three F360 front representatives under atlas loss in the
drift-allowed move space. The `best_mismatch` seed improves atlas score 74.3
-> 43.8 and enters the chamber chart at `a57=6`; the `best_D61` seed improves
62.9 -> 44.85 and enters `dh,dCh` with D61=10. The Pareto front is actionable
as an atlas-landscape object, but this run is not cascade-kernel strict.

F362 extends the improved F361 descendants in the same drift-allowed move
space. Both branches improve again:
`best_mismatch` reaches score 38.1 with `a57=5`, D61=11, chart `dh,dCh`;
`best_D61` reaches score 35.4 with `a57=5`, D61=9, chart `dh,dCh`. This is
useful landscape evidence but should not be quoted as cascade-1 progress.

F363 reruns the F362 `best_D61` descendant with D61 weighted twice as heavily.
It does not descend: under the beta=2 score, seed and best both remain 44.4
with `a57=5`, D61=9, chart `dh,dCh`. The current raw/common message move set
appears locally stuck at that drift-allowed basin.

F364 changes the move family around the same F362 `best_D61` descendant by
adding raw M1-side flips and allowing 3-flip proposals. It still does not
descend: seed and best remain score 35.4, `a57=5`, D61=9, chart `dh,dCh`.
This makes the basin look genuinely local under message-side bit moves.

F365 deterministically probes radius-1 moves around the F362 `best_D61` basin.
No single raw/common message move improves the atlas score. One raw M2 move
does lower D61 from 9 to 8, but only by breaking the chart and raising `a57` to
11. D61 is locally movable, but not independently of the guard/chart
coordinates.

F366 forces the F365 D61-lowering bit and enumerates one repair move. A
nontrivial pair can preserve D61=8 and repair the chart (`dCh,dh`), but `a57`
stays high at 11 and the score is 58.3. The D61/chart conflict is repairable
with two moves; the remaining blocker is guard repair.

F367 starts from the F366 D61-preserving chart-repaired pair and enumerates a
third move. Guard can move: 51 moves lower `a57`, with the best guard move
reaching `a57=6`. But no third move lowers guard while also preserving chart
and D61<=8. The three constraints remain coupled.

F368 starts from the F367 guard-lowered candidate (`a57=6`, D61=13, wrong
chart) and enumerates one more move. It finds zero moves satisfying the target
combination `a57<=6`, chart match, and D61<=9. The local repair graph cycles
between D61/chart repair and guard repair rather than combining them.

F369 reruns the F361-style Pareto continuation with strict cascade-1 kernel
preservation enforced after every proposed move. The front is still actionable:
`best_D61` improves score 62.9 -> 37.8 while remaining kernel-valid, with
`a57=6`, D61=8, chart `dh,dCh`. This is the current cascade-kernel-safe atlas
benchmark for the Pareto path; it is higher than the drift-allowed F362 score
35.4 but structurally meaningful.

F370 extends the F369 `best_D61` descendant under the same strict kernel guard.
It does not improve at 4x30k: seed and best remain score 37.8, `a57=6`,
D61=8, chart `dh,dCh`. This is the current local floor for common-mode,
kernel-preserving atlas continuation from the Pareto path.

F371 deterministically probes the F370 strict-kernel basin at radius 1 using
only kernel-preserving common moves. Across 1536 valid moves it finds no score
improvement, no `a57` improvement, and no D61 improvement. The score-37.8
strict-kernel basin is a radius-1 local minimum under common-mode moves.

F372 deepens that local test with a strict-kernel common-mode beam to depth 3.
Across 64,718 evaluated descendants it finds no scalar-score improvement over
37.8, but it does split the constraints: one branch lowers guard to `a57=4`
with D61=22, while another reaches D61=5 with `a57=15`. The next useful move
is a targeted junction/repair search between those branches, not more blind
budget around the unchanged scalar floor.

F373 turns the F372 split into a strict-kernel junction search. The literal
union of the low-guard and low-D61 moves stays kernel-valid but lands off-chart
at score 85.25. Bounded repair beams from both branch points reduce target
violations but do not close them: the low-guard branch can restore chart and
reach D61=13 only after giving guard back to `a57=6`, while the low-D61 branch
can repair guard/chart only by losing D61 to 20. The nontrivial depth-2 common
neighborhood still separates guard and D61.

## Next tracks

- add outcome-aware calibration before spending more budget on F343-style selectors
- use F342 stable-core coordinates as hard features for BP/matroid audits
- use common-mode atlas continuation as a post-atlas polish operator
- escalate F373 from branch repair to a small Pareto bridge over nontrivial strict-kernel states
