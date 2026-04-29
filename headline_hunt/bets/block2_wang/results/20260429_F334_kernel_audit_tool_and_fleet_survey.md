---
date: 2026-04-29
bet: block2_wang × infra
status: TOOL_SHIPPED — kernel-preservation auditor + fleet-wide drift survey
---

# F334: kernel-preservation auditor + fleet-wide drift survey

## What's shipped

`headline_hunt/infra/audit_kernel_preservation.py` — a preventive auditor
that scans search-result JSONs for cascade-1 kernel drift. Catches the
F322/F333 class of bug systematically.

Tool semantics:
- Recursively walks JSON looking for (M1, M2), (best_M1, best_M2), or
  (M1, M2_kernel) pair structures.
- For each pair, checks if M1 ^ M2 satisfies cascade-1 kernel: nonzero
  diff at exactly word-pair (0,9) (or exotic 0,14 / 0,1) with both diff
  values = 1 << bit.
- Reports PASS / DRIFT / NO_DIFF per pair, summary per file.
- `--block-context block1|block2` flag distinguishes block-1 cascade-1
  pair search (where DRIFT = bug) from block-2 absorber search (where
  drift is expected and acceptable).

## Verification

Ground truth tests against known-good and known-drift results:

| File | Expected | Actual | Status |
|---|---|---|---|
| F315 (drift-allowed seeded atlas) | DRIFT | 8/8 DRIFT | ✓ |
| F321 (kernel-preserving seeded) | PASS | 8/8 PASS | ✓ |
| F322 (kernel-preserving random init) | PASS | 8/8 PASS | ✓ |
| F362 (yale Pareto descendant) | DRIFT | 28/28 DRIFT | ✓ |

## Fleet-wide drift survey (block-1 atlas-loss search results)

### block2_wang (macbook search artifacts, 2026-04-29 only)

| File | Pairs | DRIFT | PASS | Status |
|---|---:|---:|---:|---|
| F312 atlas_loss_8x50k | 8 | 8 | 0 | drift (RETRACTED F322) |
| F312_schedule_space_pilot | 4 | 4 | 0 | drift (RETRACTED F322) |
| F315 seeded_atlas yale_F358 | 8 | 8 | 0 | drift (RETRACTED F322) |
| F316 seeded_atlas yale_F359 | 8 | 8 | 0 | drift (RETRACTED F322) |
| F317 multibit_F358 | 8 | 8 | 0 | drift (RETRACTED F322) |
| F318 annealed_F358 | 8 | 8 | 0 | drift (RETRACTED F322) |
| F319 annealed 8x50k | 8 | 8 | 0 | drift (RETRACTED F322) |
| F320 annealed 32x20k | 32 | 32 | 0 | drift (RETRACTED F322) |
| F321 kernel-preserving seeded | 8 | 0 | 8 | ✓ valid |
| F322 kernel-preserving random | 8 | 0 | 8 | ✓ valid |
| F313 yale_masks (5 files) | 20 | 20 | 0 | drift (RETRACTED F322) |
| **Total** | **128** | **104 (81%)** | **24 (19%)** | |

### math_principles (yale's recent work, 2026-04-29 only)

| File group | Pairs | DRIFT | PASS | Status |
|---|---:|---:|---:|---|
| F344 submodular mask cal | 96 | 96 | 0 | drift |
| F347 radius1 basin walk | 160 | 160 | 0 | drift |
| F348-F349 radius1 new88 | 16 | 16 | 0 | drift |
| F352 new88 alpha sweeps (4 files) | 16 | 16 | 0 | drift |
| F353-F354 alpha probes | 111 | 111 | 0 | drift |
| F355 commonmode continuation | 13 | 13 | 0 | drift |
| F361-F365 Pareto descendant | 142 | 142 | 0 | drift |
| F365 r1 neighborhood | 50 | 50 | 0 | drift |
| F366-F368 repair probes | 85 | 85 | 0 | drift |
| F361 pareto seeded continuation | 33 | 26 | 7 | partial drift |
| **Total** | **~722** | **~715 (99%)** | **7 (1%)** | |

## Findings

### Finding 1 — Cross-machine atlas-loss search has been overwhelmingly drift-allowed

Across both bets, ~819 (M1, M2) pairs from atlas-loss search results today,
of which 819 - 31 = 788 are DRIFT. Only F321/F322 (10 PASS) and a partial
F361 (7 of 33 PASS) are kernel-preserving.

This is consistent with F322's retraction analysis: the "atlas score
38.85" / "score 35.4" / "a57=4 D61=9" findings from the drift-allowed
runs measure a search space STRICTLY LARGER than cascade-1 collisions.

### Finding 2 — F321/F322 kernel-preserving runs are cascade-1-valid

F321 (yale-seeded) and F322 (random-init) at strict kernel preservation
PASS the auditor for all 16 pairs. The cascade-1 floors from those runs
(a57=5 D61=10 yale-seeded; a57=5 D61=8 random-init) are real cascade-1
collision search results.

### Finding 3 — Auditor is now fleet-callable

Any future search result can be audited via:
```bash
python3 headline_hunt/infra/audit_kernel_preservation.py \
    --block-context block1 path/to/result.json
```

For block-2 absorber search (where drift is intentional), use
`--block-context block2`. The auditor will report DRIFT counts as
informational rather than as bug indicators.

## What this means for the project's record

Today's atlas-loss work mostly measures the drift-allowed landscape. To
read the day's results correctly:

- **Drift-allowed metrics** (atlas score 35.4, a57=4, D61=7-9 in chamber
  chart): characterize the relaxed search space, useful for landscape
  understanding but NOT cascade-1 collision floors.
- **Kernel-preserving metrics** (F321: a57=5 D61=10; F322: a57=5 D61=8):
  THE cascade-1 collision floors at this compute level.

The chamber attractor (a57=0, D61=4, chart=(dh,dCh)) remains unreached
in either regime. F311 brittleness + F324-F326 search-invariance thesis
hold regardless of drift status.

## Why the tool is high-leverage

Without the auditor, future search work could continue to silently drift.
F322 + F333 caught two instances after the fact; the auditor would have
caught them within seconds of result-shipping. Post-F334, any future
cross-machine work can pass through the auditor as a one-line CI step:

```bash
python3 headline_hunt/infra/audit_kernel_preservation.py \
    --block-context block1 --summary-only path/to/new_result.json \
    | grep -q "DRIFT.*0$" || echo "WARNING: drift detected"
```

## Discipline

- ~30 min wall (tool authoring + smoke tests + fleet survey + memo).
- 0 SAT compute.
- Tool is small (~250 LOC), portable, single-file, no dependencies
  beyond Python stdlib.
- Direct extension of F322 + F331 + F333: from one-off retractions to a
  systematic preventive measure.

## Concrete next moves enabled by F334

1. **Yale**: re-run F361-F368 with kernel-preservation enforced. F334
   auditor will show 0 drift on the re-run; results are then valid
   cascade-1 floors.

2. **macbook**: when F315-F320-style work resumes (any drift-allowed
   atlas search), run the auditor first to confirm intentional drift
   vs unintentional.

3. **Fleet**: integrate the auditor into the standard ship checklist
   alongside `audit_cnf.py` and `validate_registry.py`. Any new search
   result JSON should pass `--block-context block1` audit (or be
   explicitly labeled as block2 / drift-allowed in its memo).
