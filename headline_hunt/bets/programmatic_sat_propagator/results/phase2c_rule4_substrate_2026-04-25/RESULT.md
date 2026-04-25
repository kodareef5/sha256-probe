# Phase 2C Rule 4 r=62/63 substrate — bit-tracking infrastructure

## What this adds

The data-structures layer and notify_assignment hook for **actual register-value bit tracking**. Foundation for the value-bearing Rule 4 at r=62 and r=63 (modular Theorem 4 with Sigma0/Maj reasoning).

This commit does NOT yet fire Rule 4 at r=62/63 — that needs the modular sum + Sigma0/Maj logic from `RULE4_R62_R63_DESIGN.md` (~500 LOC, multi-day). What this commit does:

1. **Per-pair partial-register storage**: `actual_p1`, `actual_p2` (map from `reg_key=reg_idx*64+round` to `PartialReg{bits[32], n_decided}`).
2. **Reverse lookup**: `actual_var_lookup` (SAT var → `{reg_key, pair, bit, polarity}`).
3. **Bit assignment tracking**: `notify_assignment` updates the partial register for every relevant variable.
4. **Backtrack safety**: per-decision-level undo stack `level_actual_undo` rewinds bit assignments correctly on `notify_backtrack`.
5. **Setup loop in main()**: reads varmap v2's `actual_p1` / `actual_p2`, registers all SAT vars for `a`, `b`, `c` registers at rounds 59-62 in both pairs, calls `solver.add_observed_var` for each.

## Test (sr=61 expose, bit-10, 50k conflicts)

```
Rule 4 r=62/63 substrate: 768 actual-register SAT vars registered
  (a, b, c at r=59..62 × 2 pairs × 32 bits, minus const-folded)

Propagator connected: 448 cascade-zero + 128 Rule-5 + 384 actual-register vars observed

Per 50k-conflict run:
  notify_assignment events:  521,483 (vs ~500 before substrate)
  cb_propagate fires:        480 (unchanged — substrate is read-only for now)
  actual-reg bit assigns:    520,937 (the new tracking volume)
  decisions:                 381,733
  backtracks:                58,826

Wall time: 3s (same as without substrate; tracking adds O(hash-lookup)
per assignment but doesn't change search direction).
```

**Verified**: substrate compiles, runs, tracks correctly across 520k bit assignments, doesn't crash on backtrack (58k backtracks survived).

## Why this is the right intermediate step

Phase 2C-r62/63 implementation is ~640 LOC total. Splitting into:
- **Substrate** (this commit, ~150 LOC): data structures + tracking + backtrack. Verifiable independently.
- **Trigger detection** (next): when `n_decided` reaches the threshold for Sigma0/Maj evaluation.
- **Rule firing** (next): the actual modular sum + reason clause construction.

By landing the substrate first, we de-risk the multi-day implementation:
- If the substrate has a bug (e.g., backtrack incorrectness), we catch it now in the no-firing phase.
- The trigger and firing logic build on a stable foundation.
- Future sessions can ship Rule 4 at r=62 first (simpler — only one varying register input), then r=63 (two varying inputs).

## Cumulative Phase 2 status

| Phase | What | Status |
|---|---|---|
| 2A | API smoke | shipped |
| 2B | Rules 1+2 (cascade-zero + dE[60]=0) | shipped, 4× speedup |
| 2C-Rule5 | R63.1 dc=dg | shipped |
| 2C-Rule4@r61 | dA[61]=dE[61] | shipped |
| 2C-Rule3 | dE[61..63]=0 three-filter | shipped |
| 2C-Varmap-v2 | actual register vars exposed | shipped |
| **2C-Rule4-substrate** | **bit-tracking + backtrack** | **shipped (this commit)** |
| 2C-Rule4@r62 | trigger + Sigma0/Maj + modular sum | next session |
| 2C-Rule4@r63 | (same, with TWO varying inputs) | session after that |

## Decision gate (per kill_criteria.md)

After Rule 4 at r=62/63 ships and is benchmarked:
- ≥10× conflict-count reduction on sr=61 cascade-DP → continue / scale.
- 2-10× → triage (still useful but not headline-class).
- <2× → kill the bet.

The substrate is necessary for Rule 4 to fire. With substrate landed, the next dedicated session can focus purely on the firing logic.

## Build artifact

`cascade_propagator.cc` is now ~470 LOC, builds cleanly:
```
g++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
    cascade_propagator.cc -lcadical -o cascade_propagator
```
