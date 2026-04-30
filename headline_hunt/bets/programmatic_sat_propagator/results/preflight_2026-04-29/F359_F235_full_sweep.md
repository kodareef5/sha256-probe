---
date: 2026-04-30
bet: programmatic_sat_propagator × sr61_n32
status: F235_FULL_ROW_MINED — 3 unit + 31 pair clauses on F357 cand
---

# F359: F344-style full-row sweep on F235 reopen-target cand

## Setup

F357 found 2 mined clauses (1 unit + 1 pair) on aux_force_sr61
m09990bd2/bit25 (the F235 reopen-target cand). F358 translated these to
F235 vars and got -2.1% speedup. F359 extends to F344-style FULL-row
sweep (32 single-bits + 31 adjacent pairs) for richer clause library.

## Result

```
=== F359 full-row sweep on aux_force_sr61 m09990bd2/bit25 ===
wall: 750.26s (~12.5 min)
Single-bit forced: 3 / 32 ← MORE than bit31's single-bit count of 1
  dW57[0] forced=0
  dW57[1] forced=0
  dW57[2] forced=1
Adjacent-pair forbidden: 31 / 31 (every consecutive pair constrained)
```

Sample pair forbidden polarities:
| Pair | Forbidden |
|---|---|
| (0, 1) | (0, 1) |
| (1, 2) | (0, 0) |
| (2, 3) | (0, 0) |
| (3, 4) | (0, 0) |
| (4, 5) | (0, 1) |
| ... | (full table in JSON) |

## Findings

### Finding 1 — m09990bd2/bit25 has more single-bit constraints than bit31

bit31 (F341) had 1 single-bit forced (dW57[0]=1).
m09990bd2/bit25 (F359) has 3: dW57[0]=0, dW57[1]=0, dW57[2]=1.

Different cands have different richness in single-bit class.
This is consistent with F340/F357 finding that polarity / which bits
get forced varies per cand metadata.

### Finding 2 — All 31 adjacent pairs forbidden (matches F344 bit31)

The "every adjacent pair has exactly one forbidden polarity"
structural property holds for this cand too. Universal at the
adjacent-pair level on dW57 row.

### Finding 3 — Total clauses available for F235 injection: 34

3 unit clauses + 31 pair clauses = 34 mined clauses (vs F357 minimal's 2).

## Cost-benefit projection for F235 injection

F358 with 6 translated clauses (2 unit + 4 OR-of-XOR for pair) gave -2.1%
on F235.

Scaling by clause count:
- F347 bit31 aux_force, 32 clauses: -13.7% (small overlap with this cand)
- F348 5 cands aux_force, 2 clauses: -8.8% mean (full F343 minimal)
- F352 bit29 aux_expose, 2 clauses: -1.06% (mode penalty)
- F358 F235 basic-cascade, 6 clauses: -2.1% (basic-cascade penalty + small)

Projecting F359 → F235 with 34 clauses translated:
- Single-bit: 3 × 2 clauses = 6 clauses
- Pair: 31 × 4 clauses (OR-of-XOR without aux) = 124 clauses
- Total: 130 clauses to inject (vs F358's 6)
- Expected speedup: 5-10% (between F358's 2.1% and F347's 13.7%)

If realized, ~50-85s saved on F235's 848s baseline. Modest but might
help marginally on the hardest sr=61 instances.

## What's shipped

- F359 full sweep JSON (34 mined clauses on aux_force).
- This memo.

## Concrete next moves

(a) **Translate F359's 34 clauses to F235 vars + test injection** (F360):
    ~30 min translation work, ~10 min cadical comparison. Project
    5-10% speedup.

(b) **Phase 2D propagator C++ implementation**: native 2-literal
    clause injection via cb_add_external_clause. Expected: F347-class
    13.7% on F235 (no var translation overhead, no 4-literal expansion).

(c) **Multi-cand F344 sweep + injection benchmark**: extend F359 to
    other 5 cands at sr=61 force-mode. Compare full-row vs minimal
    speedup across cands.

## Compute

- 750s wall (32 single + 31 pair × 4 polarity × ~5s avg cadical).
- 0 long compute beyond per-probe budget.
