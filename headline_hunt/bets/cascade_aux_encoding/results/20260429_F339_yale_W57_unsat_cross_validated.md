---
date: 2026-04-29
bet: cascade_aux_encoding × math_principles cross-machine
status: VALIDATED — yale's F384 W57[22:23]=(0,1) UNSAT confirmed via cadical 10s
---

# F339: cross-validation of yale's F384 W57[22:23]=(0,1) UNSAT polarity

## Setup

Yale's F384 (math_principles bet) found, via conflict-guided cube minimization,
a 2-literal UNSAT core on the cascade_aux force-mode CNF for cand
m17149975/bit31:

  dW57[22] = 0  (var 12419 negated)
  dW57[23] = 1  (var 12420 positive)

This polarity is forbidden by the cascade-1 hardlock under cadical CDCL.

F339 cross-validates with two independent codepaths:
1. F324-style UP test (Python, my own propagator)
2. cadical 10s budget (independent solver)

## Results

### Python UP (F324 codepath)

```
=== F339: replicate F384 W57[22:23] polarity test via UP only ===
  (0, 0): UP-OK (483 forced)  (UP wall=0.03s)
  (0, 1): UP-OK (483 forced)  (UP wall=0.04s)
  (1, 0): UP-OK (483 forced)  (UP wall=0.03s)
  (1, 1): UP-OK (483 forced)  (UP wall=0.03s)
```

**ALL 4 polarities are UP-feasible.** UP cannot see the (0, 1) UNSAT.
The 483 forced is baseline 481 + 2 unit assumptions.

### cadical 10s (independent solver)

```
=== F339: cadical 10s on each polarity ===
  (-12419, -12420) [00]: UNKNOWN  (wall=10.01s)
  (-12419, +12420) [01]: UNSATISFIABLE  (wall=0.08s) ← yale UNSAT confirmed
  (+12419, -12420) [10]: UNKNOWN  (wall=10.01s)
  (+12419, +12420) [11]: UNKNOWN  (wall=10.01s)
```

**Cadical confirms yale's verdict.** Polarity (0, 1) is UNSAT in 0.08s
of CDCL conflict analysis. The other 3 polarities run to 10s budget
without resolution (UNKNOWN, consistent with UP being feasible).

## Analysis

The constraint `NOT(dW57[22]=0 AND dW57[23]=1)` for cand m17149975/bit31:

| Property | Verdict |
|---|---|
| In original Tseitin / UP-derivable | NO (F324, F325, F339 UP test) |
| In F286 universal core (10/10 cands) | NO (W*_57[22:23] at 0.40-0.50 fraction) |
| CDCL-derivable in 0.08s | YES (F339 cadical) |
| Cand-specific | YES (cand m17149975/bit31 specifically) |

This is the cleanest example yet of a CDCL-derived structural constraint
that:
- Is NOT in the encoder's Tseitin clauses
- Is NOT a universal-hard-core property (per F286)
- IS quickly derivable by CDCL conflict analysis
- Is precisely the kind of "external clause" F327's `cb_add_external_clause`
  IPASIR-UP hook should pre-load

## Confirmed picture (F324-F326-F339)

The cascade-1 collision search problem has THREE classes of CDCL-derived
structural constraints:

1. **Universal anchors** (10/10 cands): W1_57[0], W2_57[0], W2_58[14],
   W2_58[26]. F286.

2. **Universal round-bits** (10/10 cands, 128 bits): W*_59 + W*_60 (sr60).
   F286.

3. **Cand-specific 2-literal CDCL UNSAT cores**: e.g., W57[22:23]=(0,1)
   forbidden for m17149975/bit31. **F339 (this memo) is the first
   independently-verified instance.** Yale's F378-F384 mining pipeline
   produces these from kernel-safe basin search.

Each class is structurally distinct:
- Class 1 + 2 are encoder-mode-independent (per F329) and cand-agnostic
  for the universal subset.
- Class 3 is cand-specific and emerges from conflict-guided cube mining.

## Implication for F327 IPASIR-UP design

The propagator's `cb_add_external_clause` hook should support BOTH:

- **At init**: pre-load the universal 132-bit hard core as branching
  priorities + as conflict-clause hints.
- **Per-cand at runtime**: pre-load mined cand-specific UNSAT cores
  like F384's `NOT(dW57[22]=0 AND dW57[23]=1)`. These are 2-literal
  clauses, cheap to inject.

For each new cand, mine the F384-style cores via:
1. Run kernel-safe depth-2 beam from random init (yale F378 pattern).
2. Generate bridge cubes for each Pareto branch (yale F380 pattern).
3. Minimize UNSAT cores (yale F382 pattern).
4. Test polarities (yale F384 pattern).
5. Inject the UNSAT polarity as a `cb_add_external_clause` literal.

Estimated mining cost per cand: ~5 minutes (F378-F384 took yale that long).
Speedup at solve time: cadical takes 0.08s to derive each clause; if
the propagator avoids 50+ such derivations during full search, that's
4+ seconds saved per solve.

## What's shipped

- F339 cross-validation results (Python UP + cadical) in this memo.
- Confirms yale's F384 verdict independently.

## Discipline

- ~30s wall (4 UP runs × 0.03s + 4 cadical × 10s).
- 0 long compute.
- Direct cross-machine + cross-tool validation: yale's cadical, my
  Python UP, my cadical run — all consistent.

## Cross-machine status

The yale → macbook flywheel:
1. yale F378 conflict-guided cube
2. yale F380 cube generator
3. yale F382 UNSAT proof minimization
4. yale F384 polarity analysis (2-literal core identified)
5. **macbook F339 (this memo): cross-validates and ties to F324-F326**

The cycle produces the first concrete external-clause target for the
F327 IPASIR-UP propagator design. Phase 2D + 2D' implementation can
now use F339's verified clause as one of its initial test injections.
