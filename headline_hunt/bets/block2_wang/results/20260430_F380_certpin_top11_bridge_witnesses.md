---
date: 2026-04-30
bet: block2_wang
status: DELIVERABLE_4_SHIPPED — 22/22 UNSAT including F379 NEW bit2 HW=56; selector finds extremes but not collisions
parent: F378 (selector) + F379 (beam-discovered NEW bit2 HW=56)
direction: per user 2026-04-30 — bridge-guided block2_wang
compute: 22 cert-pin runs × 5s budget; total wall ~5s; all UP-derivable UNSAT in 0.01s each
---

# F380: cert-pin verify F378 top-10 + F379 NEW bit2 HW=56 → 22/22 UNSAT

## Setup

Per user direction (deliverable #4): "Generate a small set of bridge
assumption cubes from top beam states and run identical short
CaDiCaL/Kissat probes."

Tested 11 W-witnesses:
  - F378 top-10 by bridge_score from the 47 corpora (highest-scoring
    records in held-out validation)
  - F379 NEW bit2_ma896ee41 HW=56 (beam-discovered W-witness below
    the corpus empirical floor of HW=57)

Per cand × witness × {kissat 5s, cadical 5s} = 22 cert-pin runs.

Pipeline: cascade_aux_encoder.py (sr=60, expose) → varmap →
build_certpin → solver. Same as F372/F373.

## Result

**22/22 UNSAT.** All resolved in 0.01s (UP-derivable UNSAT). 2-solver
agreement on every record.

```
src                       cand_short                    hw  kissat   cadical
F378_top1                 bit13_m916a56aa               59  UNSAT    UNSAT
F378_top2                 bit2_ma896ee41                57  UNSAT    UNSAT
F378_top3                 bit2_ma896ee41                60  UNSAT    UNSAT
F378_top4                 bit28_md1acca79               67  UNSAT    UNSAT
F378_top5                 bit2_ma896ee41                66  UNSAT    UNSAT
F378_top6                 bit2_ma896ee41                63  UNSAT    UNSAT
F378_top7                 bit28_md1acca79               67  UNSAT    UNSAT
F378_top8                 bit2_ma896ee41                67  UNSAT    UNSAT
F378_top9                 bit28_md1acca79               63  UNSAT    UNSAT
F378_top10                bit28_md1acca79               63  UNSAT    UNSAT
F379_NEW_below_floor      bit2_ma896ee41                56  UNSAT    UNSAT  ← NEW data point
```

## Findings

### Finding 1 — Bridge_score elevates structural extremes; extremes are still UNSAT

The selector worked as designed:
  - Top-scored W-witnesses are concentrated in F374's deep-tail
    dominator cands (bit2 / bit28 / bit13).
  - F379 hillclimb extended to HW=56 below random-sampling floor.
  - All cert-pin verify UNSAT in <0.01s.

The bridge_score gradient finds structurally interesting records
(strong c/g asymmetry, sub-65 HW, bridge polarity OK), but **those
records are still in the UNSAT region of cascade-1 W-space**.

This is a clean validation pattern, not a contradiction:
  - F100 / F371-F373: 67/67 cands cert-pin UNSAT at corpus extremes
  - F380: same conclusion holds for selector-elevated extremes,
    INCLUDING records below the random-sampling empirical floor

### Finding 2 — bit2_ma896ee41 HW=56 (BELOW corpus floor) is also UNSAT

The NEW data point F379 surfaced (bit2 HW=56, score 55.96) verifies
UNSAT in cert-pin. **This pushes the empirical UNSAT envelope from
HW=57 down to HW=56** for this cand, while leaving the F100 conclusion
unchanged (no SAT).

Concretely: anyone who searched the bit2 corpus and stopped at HW=57
hadn't reached the structural floor. Bridge-guided search lowers the
bound. **And that bound remains UNSAT.**

### Finding 3 — Cert-pin instances stay UP-derivable; no learned clauses to extract

All 22 runs resolved in 0.01s. cadical's CDCL machinery never deepened
beyond unit propagation — the W-pin + cascade-1 hardlock + round
recurrence make these instances trivially UNSAT under UP.

This is a problem for **deliverable #5 (learned-clause clustering)**:
the cert-pin instances don't generate learned clauses to cluster.
Any cross-cand learned-clause work needs HARDER instances — likely:
  - aux_force / aux_expose without W-pin (the F347-F369 chain CNFs)
  - or basic_cascade with shorter time budget where CDCL is forced
    to learn

The F347-F369 cadical 60s runs DO produce ~5-15M conflicts each — those
have the learned clauses. Pivoting deliverable #5 to operate on those
instances is the right move.

### Finding 4 — bridge_score is a near-residual selector, not a collision-finder

The F378-F380 chain demonstrates: bridge_score's gradient reliably
finds structurally extreme cascade-1 W-witnesses. **It does not find
collisions.** Collisions, if they exist, are either:

  (a) below HW values reachable by random + greedy hillclimb (the F379
      hillclimb plateaued for 3/4 cands; deeper SA/restart needed)
  (b) point-singular per F98 — collision W-vectors are structurally
      indistinguishable from UNSAT neighbors at gradient-search scale,
      so any selector-based search will miss them

Both possibilities remain open. Cert-pin verification rules out
collisions at the discovered extremes, but doesn't rule them out
elsewhere.

## What's shipped

- `20260430_F380_certpin_top11_bridge_witnesses.{md,json}`
- 22 cert-pin runs in `runs.jsonl` (all UNSAT, all `--allow-audit-failure`
  /tmp paths)
- Cumulative cert-pin coverage now 67/67 cands + 1 NEW-below-floor
  witness for bit2_ma896ee41 (HW=56)

## Compute discipline

- 22 solver runs × 5s budget; actual wall 0.01s each → ~0.5s total
- 11 base CNFs + 11 cert-pin CNFs in /tmp
- All logged via append_run.py with --allow-audit-failure (transient
  /tmp paths). Real audit failure rate stays 0%.
- Total session F379+F380 compute: ~6s

## Deliverable status

  ✅ #1 (F378): bridge_score.py written + validated
  ✅ #2 (F378): hold-out validation, F371 sub-floor in top 30/368k
  ✅ #3 (F379): block2_bridge_beam.py + bit2 HW=56 below corpus floor
  ✅ #4 (THIS): cert-pin probes of top-K → 22/22 UNSAT including HW=56
  ⏳ #5: cross-cand learned-clause clustering — pivoted to aux_force
     60s cadical instances (F347-F369 chain) since cert-pin is too
     trivial to learn from. Next iteration's main move.

## Refined unit-of-progress per user direction

User said: "the unit of progress now is: a new bridge selector, a
falsified selector, or a generalized learned clause."

This session's F378-F380 chain delivered:

  ✅ A new bridge selector (F378 bridge_score.py) — empirically validated
  ✅ A falsified selector (F380): the selector identifies structural
     extremes that are still UNSAT — falsifying any reading of "bridge
     score is a collision proxy." It's a near-residual selector.
  ⏳ A generalized learned clause: deliverable #5 pending; will
     operate on aux_force 60s cadical instances rather than cert-pin
     UP-trivial instances.

## Next-iteration moves

(a) **Deliverable #5 reframed**: extract learned clauses from F347-F369
    cadical 60s runs (which produced ~5-15M conflicts each, with
    real CDCL learning), cluster across cands. Targets: bit2/bit3/bit28/bit13
    aux_force sr=60 + the new aux variants F375 generated. This is
    where cross-cand generalization could surface.

(b) **Beam improvements**: F379's greedy hillclimb plateaued on
    3/4 cands. Add simulated annealing + restarts. Target: discover
    more sub-floor records like the F379 bit2 HW=56.

(c) **Combined path**: feed beam-discovered W-witnesses into yale's
    F378-F384 bridge-cube design (yale's bridge cubes minimize to a
    2-literal core when applied to the right W-pinned instance). If
    the bridge-cube minimization reveals a NEW core (different from
    the F384 W57[22:23]=(0,1)), that's a generalized learned clause.

The unit of progress unblocks at deliverable #5 — operating on
non-trivial CDCL instances with real learning.
