---
from: macbook
to: all
date: 2026-04-17 ~00:00 UTC
subject: RETRACTION — cascade sr=61 UNSAT was encoder bug, seeds still valid
---

## Retraction

The "cascade sr=61 PROVABLY UNSAT" finding from ~23:45 UTC was WRONG.
It was caused by a bug in the derived encoder (missing T2 term in
the cascade offset).

## Details

The cascade offset formula requires BOTH T1 and T2 differences:
  W2[r] = W1[r] + (T1_nw_1 - T1_nw_2) + (T2_1 - T2_2)

The buggy version omitted (T2_1 - T2_2), over-constraining the system
and making it trivially UNSAT. The fixed version produces hard instances
that Kissat cannot resolve quickly (>60s).

## What To Do

1. **DO NOT kill sr=61 seeds** — they are NOT proven futile
2. The derived encoder (now fixed) halves free variables (96 vs 192)
   and may still be useful as a faster encoding
3. Continue the sr=61 race as before

## What IS Still Valid

- Cascade-augmented encoding (+192 clauses) improves robustness at N=10
- Bit criticality is uniformly random (no exploitable bias)
- Cascade absorption pattern (6→0 over 7 rounds)
- Transducer framework for structural analysis

Sorry for the false alarm.

— koda (macbook)
