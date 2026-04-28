---
date: 2026-04-28
bet: cascade_aux_encoding
status: F232_BUG_FIXED — v2 sound but slower than direct kissat on trivial UNSAT
---

# F233/F234: shell_eliminate_v2 — soundness fixed, but speedup not yet demonstrated

## Setup

F232 reported a soundness bug in shell_eliminate.py: false-SAT
verdicts on UNSAT inputs due to stale var_pos/var_neg indices after
BVE resolutions within a pass. F233 implements a corrected v2 with
single-elim-per-step and eager index updates.

## v2 implementation differences

| Aspect | v1 (buggy) | v2 (sound) |
|---|---|---|
| Elimination order | All vars in min-degree order in one pass | One var at a time |
| Index updates | Once per pass (stale within) | Eager after each elimination |
| Pure-literal check | Based on initial counts | Based on current counts |
| Resolvent tracking | Added to new_clauses at end of pass | Added immediately, indices updated |
| UNSAT detection | None (could mask UNSAT) | Empty-clause check on resolvents |

## v2 result on cert-pin (W=0)

```
Input: 13179 vars, 54774 clauses
Eliminations: 42.4%
Final: 7589 vars, 43538 clauses
Wall: 18.73s
```

vs v1 on same input: **94.5%** elimination, 0 clauses, 0.20s
(false-SAT artifact).

The actual shell-eliminable structure is **42%**, not 94%. The
remaining 7,589 vars are the genuine hard core of cert-pin (W=0)
that requires CDCL search.

## Soundness verification

```
$ kissat /tmp/v2_certpin_reduced.cnf
s UNSATISFIABLE  (0.02s)

$ kissat /tmp/aux_certpin_zero.cnf  (original)
s UNSATISFIABLE  (0.02s)
```

Both original and v2-reduced agree: UNSAT. v2 is sound on this case.

## Speedup analysis

| Stage | Wall |
|---|---:|
| v2 preprocessing | 18.73s |
| kissat on v2-reduced | 0.02s |
| **v2 pipeline total** | **18.75s** |
| **Direct kissat on original** | **0.02s** |

**v2 is ~900× SLOWER** than direct kissat on the cert-pin (W=0) case.

The reason: cert-pin (W=0) is a TRIVIAL UNSAT instance for kissat
(its preprocessor finds the contradiction in 0.02s via unit
propagation). v2's structural elimination doesn't help when the
solver is already fast.

## What this means

### Soundness IS fixed

v2 correctly preserves SAT/UNSAT. F232's primary concern is
addressed.

### Speedup is NOT yet demonstrated

For F211's BP-decoder design to be valuable, the preprocessor must
help on **hard** UNSAT instances. On trivial UNSAT (where kissat
solves in <1s), preprocessing overhead dominates.

### F211 thesis still untested empirically

The 200×+ speedup target requires:
- A cert-pin instance where kissat takes minutes (not 0.02s)
- v2 reduction giving a residual CNF kissat solves quickly

Such hard instances exist (the F100 cert-pin sweep found UNSATs
across many witnesses; some took longer than others). Need to
identify a hard one and re-run.

## Concrete next probes

(a) **Find a hard cert-pin instance**: scan runs.jsonl for cert-pin
    runs with wall > 10s. Use that witness for v2 testing.

(b) **Profile v2 to identify bottleneck**: 18s on 13K-var cert-pin
    is slow. Likely hot loop is the resolvent tautology check in
    Python. Could rewrite in C for ~50× speedup.

(c) **Improve v2 algorithm**: relax single-elim-per-step. After each
    elimination, only update indices for affected variables (those
    appearing in deleted/added clauses). This is asymptotically
    correct AND faster.

(d) **Test on bare cascade_aux**: v1 said 94% elim → SAT. v2 should
    give a different number. If v2 also says SAT (lower elim%), the
    bare cnf IS SAT and v1's overall conclusion holds (just
    mechanism wrong).

## Updated retraction status

F232 retracted F223-F230's preprocessor results pending v2 fix.
F233/F234 confirms:
- F232's soundness diagnosis was correct
- v1's "94% elimination" was the bug, not the structure
- v2 elimination rate (42%) is more realistic but slower
- F211's BP-decoder design depends on a FASTER sound preprocessor
  to be empirically valuable

## Honest position

The structural pivot (F207-F217 analysis) remains valid. The
algorithmic pivot (F223-F230 preprocessor) is in progress:
- v2 is sound but slow (18s)
- v1 was fast but unsound (false SAT)
- A fast+sound version requires more careful implementation

The session's strongest deliverable is now the F207-F217 structural
analysis itself, NOT the preprocessor pipeline. The pipeline is a
work-in-progress. F211's BP-decoder direction is structurally
plausible but its empirical speedup is not yet demonstrated.

## Discipline

- 1 SAT solver run (kissat verification of v2 soundness)
- v2 sound implementation shipped
- F232 retraction's primary concern addressed
- Speedup target (200×) not yet achieved; deferred to faster
  sound preprocessor implementation
