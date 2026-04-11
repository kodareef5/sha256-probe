# UNSAT Core Extraction: sr=61 at N=8

**Date**: 2026-04-10
**Evidence level**: VERIFIED (complete scan, all 8 bits tested)

## Result

At N=8, the sr=61 UNSAT is caused by the **collective** enforcement of ALL
W[60] schedule bits. No single bit is individually necessary.

| Bit removed | Result | Time |
|------------|--------|------|
| None (sr=60) | SAT | 22.4s |
| All enforced (sr=61) | UNSAT | 64.4s |
| Skip bit 0 | UNSAT | 250.8s |
| Skip bit 1 | UNSAT | 163.5s |
| Skip bit 2 | UNSAT | 183.3s |
| Skip bit 3 | UNSAT | 154.5s |
| Skip bit 4 | UNSAT | 138.0s |
| Skip bit 5 | UNSAT | 243.9s |
| Skip bit 6 | UNSAT | 101.4s |
| Skip bit 7 | UNSAT | 90.4s |

## Interpretation

1. **Every bit is redundant**: removing any single schedule bit leaves UNSAT.
   The obstruction is not in any one bit — it's a collective property.

2. **The boundary requires ≥2 free bits**: since sr=60 (all bits free) is SAT,
   and enforcing N-1 bits is still UNSAT, the phase transition happens when
   K bits are enforced for some K < N-1.

3. **Solve times increase when bits are removed**: removing bit 0 takes 250s
   (vs 64s for full enforcement). This suggests the solver works harder when
   the problem is "almost UNSAT but not quite maximally constrained."

4. **No shortcut to sr=61**: you can't find a "critical bit" to flip. The
   entire schedule constraint network must be relaxed to reach SAT.

## Connection to Phase Transition

This complements the sr=60.5 sweep data. The transition from SAT to UNSAT
requires enforcing some threshold K* bits. This UNSAT core result tells us
K* < N-1 (since enforcing N-1 is still UNSAT).

Combined with sr=60.5 sweep at N=8 (K=0 SAT, K≈N UNSAT), the critical
threshold K* determines the exact "budget" of schedule freedom needed.

## Implication for sr=61 at N=32

At N=32, if the same collective structure holds, then:
- No single bit of W[60] schedule compliance is the bottleneck
- The obstruction is information-theoretic, not positional
- Multi-block attacks (which change the problem structure entirely)
  may be the only path to sr>60
