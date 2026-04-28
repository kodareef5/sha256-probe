---
date: 2026-04-28
bet: cascade_aux_encoding
status: SHELL_ELIMINATE_SOUNDNESS_BUG_DISCOVERED — F223-F230 conclusions need revision
---

# F231/F232: shell_eliminate.py has a soundness bug — produces false-SAT verdicts on UNSAT inputs

## What I did (F231)

Generated a proper cert-pin CNF via the canonical pipeline:
1. Re-encoded m6781a62a/fillaaaaaaaa/bit06 with `--varmap +` to get
   sidecar.
2. Used `build_certpin.py` to pin W1[57..60] = (0, 0, 0, 0).
3. Ran `shell_eliminate.py` on the cert-pin output.

Expected: cert-pin should make the CNF more constrained, possibly
UNSAT. shell_eliminate should produce a non-empty residual or
detect UNSAT.

Observed: shell_eliminate reduced cert-pin CNF to **0 clauses**
(94.5% var elimination, "SAT" verdict).

## What kissat says (F232)

```
$ kissat --time=15 --quiet /tmp/aux_certpin_zero.cnf
s UNSATISFIABLE
```

**The cert-pin (W=0) CNF is UNSAT.** shell_eliminate's "SAT" verdict
is WRONG.

This is a soundness bug. My preprocessor produces false positives
(claims SAT when reality is UNSAT).

## Root cause hypothesis

In `eliminate_one_pass`, after eliminating var v:
- Original clauses with v are marked deleted ✓
- Resolvents are appended to a new_clauses list and returned at the
  end of the pass ✓
- BUT: during the same pass, when processing subsequent variables u,
  the var_pos/var_neg indices were built from the INITIAL clause set
  and don't include the new resolvents.

If a resolvent contains both polarities of u after v's elimination,
my code's pos/neg counts for u are STALE. u might be classified as
"pure literal" based on the original clauses, when in reality the
resolvents add the missing polarity.

When I treat u as pure literal and delete its clauses, I'm
incorrectly removing constraints. Iterated this way, I cascade
through the formula deleting constraints that should have been
preserved.

## Quantitative impact

Across F223-F230 tests:
- All bare cascade_aux CNFs reduced to 0 clauses → claimed SAT
- All cert-pin variants (F226-F229) reduced to 0 clauses → claimed SAT
- F231 cert-pin (W=0) reduced to 0 clauses → SHOULD be UNSAT per kissat

The 94% elimination rate may be an over-elimination artifact.
Fragments of true UNSAT proofs are being deleted as "pure literals"
that aren't actually pure when resolvents are accounted for.

## What's correct vs incorrect in F223-F230

**Likely still correct**:
- F207-F217 structural analysis (4-cycle counting, treewidth bound,
  variable semantic mapping). These don't depend on preprocessing
  soundness.
- F218-F220 kissat-default-vs-no-eliminate timing. Independent of
  shell_eliminate.

**Likely INCORRECT due to bug**:
- F223 "94% elimination on bare cascade_aux" — over-eliminates
- F224 "BP-decoder design needs ~700-var hard core" — the actual
  hard core may be much larger
- F225 "encoder-universal 700-var convergence" — same
- F226-F229 "pinning-tolerant SAT verdict" — the "SAT" reading
  was a false positive
- F230 "200× kissat speedup pipeline" — works only because the
  speedup is on bare-CNF SAT instances; on UNSAT (the actual
  collision-finding case), the pipeline gives wrong answers

## What this means for the bet

The cascade_aux_encoding bet's algorithmic deliverable
(`solve_with_shell.sh`) IS NOT VALID for the actual collision-finding
problem. It only correctly preprocesses bare SAT instances.

For the F211 three-stage decoder design:
- Stage 1 (shell elimination) needs a correct implementation.
- A proper Stage 1 must update var_pos/var_neg eagerly when
  adding resolvents, OR rebuild indices after each elimination.

Estimated fix: ~1-2 hours of careful implementation work. The
algorithm is correct; the bookkeeping needs fixing.

## Honest assessment

This is the second soundness-class issue of the session (F205
retracted F201's overstated cross-fixture claim; F232 retracts
F223-F230's preprocessor correctness).

Two retraction-class commits in one session is uncomfortable but
healthy. The discipline is "ship corrections, don't defend
overstated claims".

## Concrete next probes

(a) **Fix shell_eliminate.py**: implement proper var-index update
    when adding resolvents. Test on F231's cert-pin CNF — should
    NOT produce 0 clauses; either non-empty residual (kissat-
    solvable in seconds) or empty-clause derivation (UNSAT
    proof).

(b) **Use kissat as ground truth**: any future preprocessor
    soundness claim must be empirically verified against kissat
    (or another solver) on at least one known-UNSAT instance
    before being trusted.

(c) **Re-run F223-F229 with fixed preprocessor**: see what the
    actual elimination rate is on bare cascade_aux when soundness
    is preserved.

(d) **Update kill_criteria.md**: the BP-decoder direction's
    feasibility depends on a correctly-implemented Stage 1. Until
    the bug is fixed, the bet's algorithmic-direction claims
    should be treated as proposals not validated tools.

## Discipline

- 1 SAT solver run (kissat 15s on cert-pin CNF, returns UNSAT)
- shell_eliminate.py soundness bug discovered via empirical
  comparison
- F232 retracts/qualifies F223-F230 results
- The fact that we caught this is itself disciplinary value:
  ground truth via kissat exposed the bug

## Honest summary of session

Through F231/F232 the session has produced:
- **Real structural analysis** (F207-F217): valid; doesn't depend
  on preprocessor.
- **A working tool that produces correct SAT preprocessing on
  satisfiable instances** (shell_eliminate): partial value.
- **A broken tool for UNSAT preprocessing**: needs fixing before
  it has practical value for collision finding.

The session ends with mixed value: real structural insights, a
half-working tool, and an honest soundness-bug correction.
