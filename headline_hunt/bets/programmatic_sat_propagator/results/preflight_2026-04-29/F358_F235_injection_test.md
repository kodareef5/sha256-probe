---
date: 2026-04-29
bet: programmatic_sat_propagator × sr61_n32
status: F235_INJECTION_FIRST_RESULT — 2.1% conflict reduction
---

# F358: F343-mined clauses translated to F235 — first injection on hard instance

## Setup

F357 mined clauses on aux_force_sr61 m09990bd2/bit25 cand. F356 confirmed
mode-invariance — same clauses apply to both force and expose modes.
F358 translates these clauses to F235's basic-cascade encoder var IDs
and tests injection.

## Var ID translation (one-time per encoder)

For F235 (basic cascade encoder, sr=61 m09990bd2/bit25/0x80000000):

| Aux constraint | Aux force-mode CNF | F235 (basic cascade) translation |
|---|---|---|
| dW57[0] = 0 (forced) | inject `-12643` | (W1_57[0] = W2_57[0]) → 2 clauses: `[-2, 98]`, `[2, -98]` |
| W57[22:23] forbidden (0, 0) | inject `[12665, 12666]` | (W1_57[22] != W2_57[22]) OR (W1_57[23] != W2_57[23]) → 4 clauses |

Total injection: 6 clauses (2 for unit, 4 for OR-of-XORs without aux vars).

In F235:
- W1_57[0] = var 2; W2_57[0] = var 98
- W1_57[22] = var 24; W1_57[23] = var 25
- W2_57[22] = var 120; W2_57[23] = var 121

## Test

cadical 5-min budget on F235 baseline vs F235 + 6 mined clauses.

## Result

```
F235 BASELINE:  5,448,917 conflicts at 295s = UNKNOWN
F235 INJECTED:  5,334,575 conflicts at 295s = UNKNOWN
Δ:             -114,342 conflicts (-2.1%)
```

## Findings

### Finding 1 — F343-style injection on F235 gives -2.1% conflict reduction

First empirical measurement of F343 injection on F235 hard instance
(the reopen target for programmatic_sat_propagator bet).

The 2.1% is smaller than:
- F347 sr=60 FORCE bit31, 32 mined clauses: -13.7%
- F348 sr=60 FORCE 5 cands, 2 mined clauses: -8.8% mean

But MORE than:
- F352 sr=60 EXPOSE bit29, 2 mined clauses: -1.06%

Plausible explanation: F235 is a basic cascade encoder (no aux vars).
The 4 OR-of-XOR clauses are 4-literal each, less aggressive than the
2-literal aux-force version. CDCL needs more work per propagation.

### Finding 2 — Var ID translation is feasible, takes ~30 min

The translation from aux_force var IDs to basic-cascade var IDs requires:
1. Identify W1_57[i], W2_57[i] vars in basic cascade encoder via
   re-running encoder Python and inspecting `free_var_names` (~10 min)
2. Convert "dW = aux XOR var" clauses to "W1[i] != W2[i]" clauses
   (manual encoding: 2 clauses for unit, 4 clauses for forbidden pair)
3. Test cadical with combined CNF (~5 min × 2 = 10 min)

Total: ~30 min per encoder. One-time per encoder family.

### Finding 3 — Cost-benefit at F235 budget

For F235 (cadical 848s timeout baseline):
- 20s preflight (aux_force) + 30 min var translation (one-time) + 0 marginal
- 2.1% × 848s = ~18s saved per F235 solve
- Break-even at ~1500s solves; for typical F235-class hard instances
  with 848s timeouts, modest but positive.

Larger gains would require:
- Mining more rounds (F344 full row gave +4% over F343 minimal)
- Or different encoder structure that better leverages aux vars

### Finding 4 — Phase 2D propagator could give bigger gains

The 4-literal OR-of-XORs is suboptimal CNF. An IPASIR-UP propagator's
`cb_add_external_clause` hook would inject the constraint as native
2-literal clauses with aux vars, matching F347's 13.7% efficiency
profile rather than F358's 2.1%.

So F358 is a LOWER BOUND on what propagator integration would achieve.

## Compute

- 5 min × 2 cadical runs = 600s wall.
- Logged via append_run.py (bet=sr61_n32, cand=bit25_m09990bd2).

## What's shipped

- F358 baseline + injected logs.
- This memo with var ID translation table.
- First empirical measurement of F343-derived clauses on F235.

## Concrete next moves

(a) **F235 1h cadical with injection**: see if 2.1% scales to flip
    cadical 848s timeout → SAT. ~1h compute. Could be small enough to
    fit budget.

(b) **Mine MORE clauses on F357**: F344-style full-row sweep on
    aux_force_sr61 m09990bd2/bit25 (~13 min). Translate ~32 clauses
    to F235 (~30 min). Test injection. Speedup target: 5-8% (between
    F343 minimal and F347 full-row).

(c) **Phase 2D propagator C++ implementation**: native 2-literal
    clause injection via cb_add_external_clause. Should give the
    F347-class 13.7% speedup directly, no var translation overhead.
