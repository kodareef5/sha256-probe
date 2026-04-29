---
date: 2026-04-29
bet: programmatic_sat_propagator × cascade_aux_encoding
status: SR61_VALIDATED — F343 mining works at sr=61, same constraint structure
---

# F354: F343 preflight on sr=61 aux_force bit31 m17149975

## Setup

F343/F344 mined Class 1a/2 clauses at sr=60 force/expose mode. F354
extends to sr=61 — the open frontier (no SAT cert yet).

## Result

```
=== F343 preflight on aux_force_sr61_n32_bit31_m17149975_fillffffffff.cnf ===
n_vars=13516, clauses=56135  (vs sr=60: 13248/54919)
wall: 20.16s

dW57[0] forced=1 (inject lit +12665)         ← Class 1a-univ ✓
(dW57[22], dW57[23]) forbidden=(0, 1)        ← Class 2 ✓
inject [12687, -12688]
```

## Findings

### Finding 1 — Class 1a-univ holds at sr=61

dW57[0] = 1 forced — same as sr=60 force-mode bit31 (per F341/F342).
The LSB anchor universality extends to sr=61.

### Finding 2 — Class 2 has SAME polarity at sr=61 as sr=60 for bit31

W57[22:23] forbidden=(0, 1) at sr=61, same as sr=60 force-mode bit31
(per F340). The fill bit-31 SET → (0, 1) hypothesis from F340 holds
at sr=61 for this cand.

### Finding 3 — F343 mining is sr-agnostic for force-mode

The 20s preflight produces the same 2 mined clauses at sr=60 and
sr=61 force-mode for the same cand. Phase 2D propagator's preflight
step would generate identical clause libraries for the same cand
at both sr levels.

This is encouraging for the F235 hard instance (sr=61 cascade-encoder,
not aux_force, but related). The mined clauses on aux_force sr=61
SHOULD transfer to the basic-cascade sr=61 encoder by re-mining,
since both encode the same cascade-1 collision constraint.

## What's shipped

- F354 sr=61 preflight result + JSON.
- This memo.
- Confirms F343 mining tool works at sr=61.

## Compute

- 20.16s wall (5 cadical 5s probes).
- 0 long compute.

## Cross-bet implication

For block2_wang absorber search at sr=61: pre-injection of dW57[0]=1
unit clause + W57[22:23] blocking pair would speed up cadical/kissat
on sr=61 instances by similar magnitude as F347/F348 measured on sr=60
(5-14% conflict reduction).

For programmatic_sat_propagator Phase 2D: the IPASIR-UP propagator's
cb_add_external_clause hook gets the SAME clauses for the same cand
across sr levels. Cleaner per-cand integration.
