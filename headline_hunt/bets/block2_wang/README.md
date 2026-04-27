# bet: block2_wang — Wang-style block-2 modification from cascade residuals

**Priority 1** per GPT-5.5 (highest expected information per CPU-hour).

## The bet

The naive multi-block negative result closed only one form of the question:
"can a generic block-2 cancel high-HW residuals?" — answer: no, residual HW=7+ is too large.

What is **NOT** closed: "can we design a Wang-style differential trail for block 2
tailored to the residual family produced by a cascade near-collision?" That is a
different mechanism — the difference is the trail design, not just message freedom.

## Hypothesis

Structured block-1 residuals (cascade has them — da=de pattern is regular) can be
absorbed by a tailored block-2 trail using:
- disturbance correction
- neutral bits
- local collisions
- Wang-style message modification

Trail search must come **before** SAT — naive SAT on block 2 will reproduce the existing
~18-round frontier and stall.

## Headline if it works

> "2-block cascade+Wang construction reaches X full-schedule rounds"

OR

> "Block-2 absorbs cascade residual through Y rounds with full schedule."

Either bridges beyond the single-block cascade boundary that this project's structural
theorems describe — i.e., changes the public-known bound for SHA-256 reduced-round
collision attacks via a multi-block construction tailored to the cascade family.

## What's built / TODO

- [ ] **Residual corpus collection.** Mine q5 runs for ~100-1000 best block-1 near-collisions.
  Output: `residuals/corpus.jsonl` with one row per residual, fields:
  `{m0, fill, kernel, n, da_pattern, de_pattern, db_hw, dc_hw, register_active_set, carry_entry_profile, source_run_id}`.
- [ ] **Cluster the corpus.** Script: `cluster_residuals.py`. Cluster by active registers,
  bit positions, signed/additive vs XOR form, carry-entry profile. Output: `residuals/clusters.yaml`.
- [ ] **Bitcondition / trail-search engine.** This is the core build. Inputs: cluster
  representative; round budget. Output: differential trail with message modification opportunities.
  Search objective: maximize satisfied local conditions through rounds 0-31 (NOT solve full 64).
- [ ] **Reduced-round pilot.** Per cluster, search at 20, 24, 28, 32 rounds with full W[0..15]
  message freedom. Compare against known SHA-256 differential trail frameworks.
- [ ] **Decision gate.** After 1 week of trail search: best cluster's trail must reach >18
  rounds OR kill criterion #1 fires.

## How to join

This is a single-owner bet at the trail-engine build phase (concentrated design work). After
the engine exists, multiple machines can run cluster trail searches in parallel.

1. Edit `headline_hunt/registry/mechanisms.yaml` and set `block2_wang_residual_absorption.owner`
   to your machine name.
2. Update `BET.yaml` `owner` and `machines_assigned`.
3. Read the classical references in `../../literature/papers.bib`:
   - Wang/Yu/Yin message modification
   - Mendel/Nad/Schläffer SHA-256 local collisions
   - de Cannière/Rechberger automated characteristic search
   - Lipmaa/Moriai modular addition differentials
4. Read GPT-5.5's full reasoning: `../../../consultations/20260424_secondwind/20260424_1505_gpt55.md`
   (section 2 — "Highest-EV unexplored mechanism").

## Related

- Closes if: `kill_criteria.md` triggers fire.
- Closed by failure of: nothing — independent of other bets.
- Reopens if: see `mechanisms.yaml` reopen_criteria.
- Adjacent: `mitm_residue` (also bypasses single-block cascade boundary, different mechanism).

## Current Trail Targets

The F42/F43 all-record LM scan makes candidate selection a Pareto problem
over residual HW, Lipmaa-Moriai cost, and exact `a61=e61` symmetry. The
current short list is:

- `bit2_ma896ee41`: HW45, exact symmetry, LM824.
- `bit13_m4e560940`: HW47, exact symmetry, LM780.
- `msb_ma22dc6c7`: HW48, LM773.
- `bit28_md1acca79`: HW49/LM765 in the F43 corpus; F45 online sampling
  and exact W60/W59-neighbor sweeps improve this to HW33/LM679 on the
  HW axis. Later exact sheet atlases push the local chart to HW39/LM720,
  HW45/LM637 on the raw/exact-symmetry LM axis, and pair-aligned
  HW78/LM731 with `pair_hw=8`.
- `bit4_m39a03c2d`: HW53/LM757 in the F43 corpus; F45 online sampling
  improves raw LM to HW71/LM720 and exact-symmetry LM to HW64/LM743,
  but bit28 now dominates both LM axes.

See `trails/20260427_F43_recordwise_lm_pareto.md` and
`trails/20260427_F45_online_pareto_sampler.md`. The latest exact-sheet
map is `trails/20260427_F77_exact_sheet_atlas_pair_metric.md`.
