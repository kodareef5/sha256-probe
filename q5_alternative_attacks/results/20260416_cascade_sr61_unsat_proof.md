# CASCADE sr=61 Derived Encoding — RETRACTED

**Date**: 2026-04-16 ~23:40 UTC (original), RETRACTED 2026-04-17 ~00:00 UTC
**Evidence level**: RETRACTED — the "UNSAT proof" was an encoder bug

## What Happened

1. Built a "derived" encoder that computes W2 from W1 via cascade offset
2. The initial encoder had a BUG: the cascade offset only included
   (T1_nw_1 - T1_nw_2) but MISSED the (T2_1 - T2_2) term
3. The buggy encoder over-constrained the system → trivially UNSAT
4. This was mistakenly reported as "cascade sr=61 PROVABLY UNSAT"

## The Bug

The cascade condition is: T1_1 + T2_1 = T1_2 + T2_2 (for da=0)

The buggy derivation assumed T2_1 = T2_2 (since da56=0 → a56 equal).
But T2 = Sigma0(a) + Maj(a,b,c), and b56 ≠ b56', c56 ≠ c56'.
So T2_1 ≠ T2_2, and the correct formula is:

  W2[r] = W1[r] + (T1_nw_1 - T1_nw_2) + (T2_1 - T2_2)

## Verification

| Test | Buggy encoder | Fixed encoder |
|------|--------------|---------------|
| bit25 candidate | UNSAT 0.14s | >60s (running) |
| Q3 candidates | UNSAT <1s each | >30s each (running) |
| Derivation numerical check | W2 wrong | W2 matches known collision |
| sr=60 derived | Not tested | >120s (as expected) |

The fixed encoder produces valid CNFs that Kissat cannot resolve quickly.
The "UNSAT proof" was entirely due to the missing T2 term.

## What's Still Valid

1. The derived encoding DOES halve free variables (96 vs 192)
2. The cascade offset formula (with T2 term) is numerically verified
3. The encode_sr61_derived.py tool is now CORRECT and may still be useful
4. The cascade-augmented encoding (+192 clauses) is also correct

## What's Invalidated

- ~~"Cascade sr=61 PROVABLY UNSAT for all 7 N=32 candidates"~~ — RETRACTED
- The 11 running kissat seeds are NOT proven futile
- The fleet should NOT kill sr=61 seeds based on this finding

## Lesson

Always verify encoder correctness with a POSITIVE control (known SAT
instance) before claiming UNSAT. The sr=60 derived control would have
caught this bug immediately.
