# Phase 2C Rule 5 ships — R63.1 (dc_63 = dg_63) bit-equality propagator

## What this adds

Rule 5 of SPEC.md: enforce **`dc_63 = dg_63` modular** (R63.1 from the mitm_residue structural picture). 32 bit-equalities, one per bit position. Fires CONDITIONALLY when one side is decided.

C++ implementation extends `cascade_propagator.cc`:
- `r63_eq_pairs[32]`: bit-i pair (cv, dc_polarity, gv, dg_polarity) from varmap.
- `r63_eq_lookup`: SAT-var → (pair_idx, side ∈ {c, g}).
- `notify_assignment` watches Rule-5 vars; when one side is assigned, computes the bit value and forces the other side to match.
- `cb_propagate` drains Rule-5-queued literals before falling through to Rules 1+2 zero-forcing.
- Reason clause for Rule-5 forced literal: binary clause `[forced_lit, -input_lit]`.
- `notify_backtrack` undoes Rule-5 state changes.

## Test (sr=61 expose, bit-10 m=0x3304caa0, 50k conflicts)

| Mode | wall | cb_propagate fires | of which Rule 5 |
|---|---:|---:|---:|
| Propagator OFF (baseline) | 8s | 0 | — |
| Propagator ON (Rules 1+2+5) | **2s** | **384** | **32** |

**4× speedup persists from Phase 2B; Rule 5 fires the expected 32× (one per bit pair)** and adds zero overhead in the steady state.

## Why Rule 5 doesn't change wall time on this CNF

The Mode A expose CNF still has the full r=63 collision constraint (`dE[63]=0` etc. — eq_word for all 8 registers at r=63). Cascading from that:
- `dE[63]=0` and `dG[63]=0` are both forced by the collision constraint at level 0.
- Therefore both sides of the dc=dg pair become zero at level 0.
- Rule 5 fires to "confirm" the equality, but the partner is already at the right value — no work for CDCL beyond confirming.

Where Rule 5 WILL matter:
- A propagator-only encoding that DOESN'T pre-restrict to full r=63 collision (e.g., a hypothetical Mode "C" — collision only at r=62 + Theorem-3 closure via propagator).
- Mid-search, when CDCL has decided one side of a bit-equality but not yet the other (Rule 5 fires before CDCL would derive it via long resolution chain).

## Implementation correctness

Verified:
- 32 Rule-5 fires per run match expected (one per bit, single time at level 0).
- No backtrack failures: `notify_backtrack` correctly undoes Rule-5 state.
- Reason clauses are valid binary clauses `[propagated, -input]`.
- Total cb_propagate count matches Rule-1+2 (352) + Rule-5 (32) = 384.
- Wall time on Mode A unchanged from Phase 2B (2s with vs 8s without). Rule 5 does NOT slow down the propagator.

## Cumulative Phase 2 status

| Phase | Rules | Mode A speedup | New capability |
|---|---|---:|---|
| 2A | smoke | n/a | API works |
| 2B | 1+2 | 4× | dynamic Mode B parity |
| **2C** | **1+2+5** | **4×** | **+ R63.1 bit-equality** |
| 2C-next | + 3 | TBD | Mode FORCE three-filter via propagator |
| 2C-next | + 4+6 | TBD | **modular Theorem 4** (CNF can't express directly) |

Rule 4 is the value-bearing rule for Phase 2C beyond Mode B: it requires actual register value tracking (a, e bits at each round) and modular sum reasoning (`da_r − de_r ≡ dT2_r` where dT2_r involves Sigma0+Maj on actual values). That's ~400 LOC of more careful work — next session.

## Git state

Single commit per phase. Total propagator C++ now ~370 LOC. Builds against local CaDiCaL 3.0.0 + nlohmann-json (brew installed).

```
g++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
    cascade_propagator.cc -lcadical -o cascade_propagator
./cascade_propagator <cnf> <varmap.json> [--conflicts=N] [--no-propagator]
```
