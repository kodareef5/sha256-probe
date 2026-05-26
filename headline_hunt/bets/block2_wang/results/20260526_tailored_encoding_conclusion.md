---
date: 2026-05-26
bet: block2_wang
status: CONCLUSION — tailored encoding attempted; >18 solver-limited (not refuted); kill #1 NOT fired
author: macbook-claude
evidence_level: EVIDENCE (R=18 absorber VERIFIED; >18 solver-limited across naive + 2 tailored levers)
---

# Tailored encoding does not beat 18 (yet); >18 stays solver-limited, not infeasible

Per the user's direction ("chase >18 via tailored encoding"), two tailored levers were built
and tested on top of the validated CNF encoder. Neither breaks the R=18 → R=19 wall. The
honest conclusion: the >18-round block-2 absorber gate is **solver-limited, not
proven-infeasible**, and the oracle-confirmed **R=18 absorber** stands as the deliverable.

## Levers tried

**1. Naive CNF (baseline).** kissat: R=15/16 SAT instantly, R=18 SAT in 5.2s (oracle-confirmed,
zero output diff, msg-HW 240), R=19 UNKNOWN at 866s, cadical R=19 also TIMEOUT at 300s. The
naive 2-message CNF tops out at 18 — matching the project's prior naive-SAT frontier.

**2. Difference-window (restrict which message words may differ).** Non-monotonic:
```
  R=18 W0..3  (4w):  TIMEOUT (150s)      # too few correction DOF -> hard/UNSAT
  R=18 W0..7  (8w):  TIMEOUT (150s)
  R=18 W0..11 (12w): SAT 2.3s, oracle-confirmed, msg-HW 188   # SWEET SPOT (sparser + faster!)
  R=19 W0..11 (12w): TIMEOUT (300s)      # sweet spot does NOT extend past 18
```
A mid-size (12-word) window is a genuine *sweet spot at R=18* — it finds a **sparser**
absorber (HW 188 vs the full-window HW 240) **faster** (2.3s vs 5.2s). But at R=19 even the
sweet-spot window times out. The window lever does not crack >18.

**3. Path-pinning (pin engine-forced bit-conditions into the CNF).** DEAD on arrival: running
the engine's arc-consistency `propagate()` on the R=19 absorber (input = residual, output = 0)
forces **0 message bits and 0 state0 bits** — the over-approximation determines no free
variable, so there are no forced conditions to add as clauses. No CNF reduction possible.

## Why (the structural reason)

The block-1 residuals are **dense** (HW ≥ 35). A dense input difference admits no low-weight
differential characteristic, so there is no sparse structure for either tailoring lever to
exploit: arc-consistency forces nothing (path-pin dead), and constraining the message
difference to a window doesn't match the broad correction a dense residual needs (window
counterproductive, except the R=18 sweet spot). This is exactly the bet's long-standing,
never-met dependency — *"get block-1 residuals down to HW ≤ 16 (Wang differential
threshold)"* (`mechanisms.yaml`). Residual-min floored at ~HW 35
([[project_cascade_tail_suboptimal]]). The tailored advantage requires the sparse residual
that does not exist; absent it, only the hard naive SAT instance remains, and it tops out at 18.

## Decision — kill #1 NOT fired

R=19 is **never shown UNSAT** — every probe is a timeout (kissat 866s, cadical 300s, window
300s), and propagation finds no contradiction at R=18/20/24. So a >18 absorber is **not
refuted**; it is **search-limited**. Firing kill #1 requires the gate to be decisively
unreached after a real search effort with a *reason*; "solver timeout" across naive + 2
tailored levers is strong evidence but not a proof of infeasibility, and the kill trigger's
1-week timeline is not met (~1 day). **Kill #1 stays unfired.**

Caveat unchanged: the CNF leaves the chaining value CV free, so even the R=18 result is a
≥18-round absorber **trail for the residual difference**, not a full 2-block collision pinned
to block 1's actual CV.

## Standing deliverable (all committed locally)

- Wang trail engine (`wang_trail_engine.py` + `wang_search.py`), control-validated on the
  SHA-256 9-step local collision.
- CNF encoder (`absorber_cnf.py`) validated against the engine, with the difference-window
  lever.
- **Oracle-confirmed 18-round block-2 absorber** for the bit13 HW35 residual (sparsest:
  12-word window, msg-HW 188).
- Full record: `trail_search_summary.md`, `20260526_block2_absorber_VERDICT.md`, this memo.

## Open routes (for the direction decision)

1. **Pause** block2_wang here — strong, honest deliverable.
2. **Different angle**: a hand-crafted low-weight characteristic; a SAT portfolio / much
   longer compute on R=19; or pursue a **HW ≤ 16 residual class** (the unmet dependency —
   itself a hard, separately-floored problem).
3. **Redirect** the autonomous lane to a fresh unowned mechanism.
