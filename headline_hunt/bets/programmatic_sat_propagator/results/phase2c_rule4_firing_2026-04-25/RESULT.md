# Phase 2C-Rule4 firing LIVE — modular Theorem 4 propagator runs end-to-end

## What this completes

The full implementation chain for Rule 4 at r=62 (modular Theorem 4 with partial-bit reasoning, value-bearing rule that CNF cannot express directly):

| Component | Status |
|---|---|
| varmap v3 with `aux_modular_diff` | ✓ shipped (commit `17c3efe`) |
| Substrate (bit-tracking + backtrack) | ✓ shipped |
| Sigma0/Maj/dT2 helpers | ✓ shipped, 14+12+14 unit tests pass |
| Modular subtraction primitive | ✓ shipped, 14/14 tests pass |
| Partial-bit dSigma0/dMaj evaluators | ✓ shipped, 12/12 tests pass |
| 1:many SAT-var lookup fix | ✓ shipped |
| `try_fire_rule4_r62()` firing logic | ✓ shipped (this commit) |
| Reason-clause construction | ✓ shipped (this commit) |

## Test (sr=60 expose, MSB candidate, 50k conflicts)

```
Rule 4 firing targets: 128 modular-diff aux SAT vars across 4 (reg,round) entries

Propagator stats:
  notify_assignment events:        519,231
  cb_propagate fires:              669
    of which Rule 5:               32
    of which Rule 4@r=61:          32
    of which Rule 4@r=62 forcings: 157  ← NEW: value-bearing fires
  actual-reg bit assigns:          892,511
  decisions:                       431,452
  backtracks:                      58,886
```

**157 Rule 4@r=62 forcings**: each is a forcing of one bit of `(e1[62] - e2[62]) mod 2^32` to a value determined by partial-bit reasoning over actual register values. CNF cannot derive these without long resolution chains involving the modular adder/subtractor structure.

Sound: reason clauses include all decided input lits (a_61, a_60, a_59, a_62 in both pairs). Backtrack-safe: per-level undo of `rule4_forced` set.

## Side-by-side timing (real time, /usr/bin/time -p)

| CNF | propagator | wall | Rule4 fires |
|---|---|---:|---:|
| sr=60 force MSB | ON (full Phase 2C) | 2.04s | 157 |
| sr=60 force MSB | OFF (vanilla) | 0.91s | — |
| sr=61 force bit-10 | ON | 2.26s | 170 |
| sr=61 force bit-10 | OFF | 1.09s | — |

**Per-conflict wall time is ~2× SLOWER with the full propagator.** The Rule 4 partial-bit reasoning runs on every 64 actual-register bit assignments, consuming CPU cycles for each evaluation.

**At 50k conflicts, both ON and OFF hit UNKNOWN.** The conflict-count-to-SAT comparison (the bet's actual decision gate) requires longer-budget runs to settle. We cannot yet tell whether Rule 4's partial-bit firings reduce the conflicts-to-SAT count enough to compensate for the per-conflict overhead.

## Honest assessment

**What's proven**:
- The full Phase 2 propagator architecture is sound — 157 modular-arithmetic propagations fire per 50k conflicts without crashes, with valid reason clauses and clean backtracking.
- Rule 4@r=62 is a real value-bearing constraint (CNF cannot derive it directly without aux ripple-carry adders).
- The implementation matches the design doc (`MODULAR_VS_XOR_FORCING_ISSUE.md` Option C).

**What's NOT yet proven**:
- That Rule 4 firing reduces conflicts-to-SAT count by ≥10× (the bet's decision gate).
- That the net wall-time is faster than vanilla cadical on hard instances.
- Both require multi-hour runs that can't fit in a 30-min pulse.

**What this commit ships**: the working propagator — the engineering substrate that lets a future worker (or compute-heavy session) measure the actual conflict-count benefit.

## Decision-gate experiment design

To evaluate the bet's value-add, a future session should:
1. Pick 3 sr=61 candidates (varied kernels — bit-10, bit-19, bit-31).
2. Run each at conflict budget = 10M (~30-60 min each on cadical) with propagator ON vs OFF.
3. Measure: conflicts-to-SAT, wall-to-SAT, peak memory.
4. Decision: ≥10× conflict-count reduction → continue/scale; 2-10× → triage; <2× → kill the bet.

That experiment is ~3-6 CPU-hours total. **Not initiating without explicit user direction** (per CLAUDE.md guidelines on multi-hour compute).

## Commits in this Phase 2C arc

- `8138fd3` — propagator SPEC.md (8 rules)
- `4b649e5` — IPASIR-UP API survey + Phase 2A smoke test
- `2bcfffe` — Phase 1 Python prototype
- `56b4c6f` — varmap v1 sidecar
- `d736ef6` — Phase 2B C++ Rules 1+2 (4× speedup on Mode A)
- `d3f6816` — Rule 5 (R63.1)
- `99f09ef` — Rule 4 specialization at r=61
- `cc1dc84` — varmap v2 (actual register vars)
- `396cf5a` — Rule 3 (three-filter)
- `3424a29` — Rule 4 r=62/63 substrate
- `4df69b8` — full-input helpers
- `7394d98` — helper unit tests
- `a63fee5` — modular subtraction primitive
- `5656896` — partial-bit Sigma0/Maj evaluators
- `e814b3d` — 1:many SAT-var lookup fix (breakthrough)
- `a6076d3` — modular-vs-XOR design doc
- `17c3efe` — varmap v3 + encoder Option C
- `???????` — Rule 4 firing logic (this commit)

## Build artifact

Single-file C++ source, ~750 LOC. Builds cleanly:
```
g++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
    cascade_propagator.cc -lcadical -o cascade_propagator
```

Companion test files: `test_helpers.cc`, `test_modular_sub.cc`, `test_partial_sigma0.cc` — together ~560 LOC of unit tests.

## What this means for the bet

The propagator is **engineering-complete for Phase 2C**. The bet's hypothesis ("≥10× conflict-count reduction via cascade-aware propagation") is now testable end-to-end on real CNFs. The remaining unknown is the empirical answer.

Without a multi-hour compute commitment, we cannot tell if the bet pays off. The infrastructure to find out is in place.
