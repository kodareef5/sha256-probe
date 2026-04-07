# sr=60 Collision at Full 32-bit SHA-256

**Date:** 2026-04-06 22:35 EDT
**Machine:** mac-m5 (Apple M5, 10 cores)
**Solver:** Kissat 4.0.4 with `--seed=5`
**Runtime:** ~12 hours (launched 10:43, completed 22:35)

## The Candidate

The same candidate from Viragh (2026) — the "dead" one that was claimed
UNSAT via constant-folded partitioning. With random seed 5, Kissat found
a collision for it at full 32-bit width.

```
M[0]  = 0x17149975
M[1..15] = 0xffffffff (all ones)

MSB kernel: M2[0] = M1[0] ^ 0x80000000, M2[9] = M1[9] ^ 0x80000000
```

## The Collision

Free schedule words (W[57..60] for both messages):

```
W1[57] = 0x9ccfa55e    W2[57] = 0x72e6c8cd    dW[57] = 0xee296d93
W1[58] = 0xd9d64416    W2[58] = 0x4b96ca51    dW[58] = 0x92408e47
W1[59] = 0x9e3ffb08    W2[59] = 0x587ffaa6    dW[59] = 0xc64001ae
W1[60] = 0xb6befe82    W2[60] = 0xea3ce26b    dW[60] = 0x5c821ce9
```

Schedule-determined words W[61..63] follow the standard rule and need
no special handling — they just work out with the above free word choice.

## Final State (both messages identical after round 63)

```
a = 0x5058a189
b = 0x2147e9d2
c = 0x9c2be0d8
d = 0xc77edca8
e = 0x5cea4fc3
f = 0xb73cce6f
g = 0xa1427d22
h = 0xf4c71522
```

## Verification

Verified by native SHA-256 computation — all 8 state registers match
between msg1 and msg2 after round 63. This is a true collision of the
compression function state after the schedule-compliant round boundary
at position 60.

## What This Means

1. **The paper's thermodynamic floor claim is wrong.** The exact candidate
   (M[0]=0x17149975) claimed UNSAT at sr=60 via partitioning is actually
   SAT — it just needed random seed 5 and ~12 hours of Kissat.

2. **Seed diversity matters enormously.** The Mac ran 5 seeds (1..5) on
   this candidate. Only seed 5 cracked it. The other 4 were still running
   when seed 5 finished.

3. **The scaling fit was roughly right.** T ≈ 0.87 × 1.47^N predicted
   ~19 hours at N=32. Actual: ~12 hours with seed diversity.

4. **sr=60 is solvable at full 32-bit SHA-256.** Combined with the N=8-31
   homotopy results, the conclusion is unambiguous: sr=60 is NOT a
   topological barrier. It is a computational one, and that barrier is
   now broken for this candidate.

## Artifacts

- `instance.cnf`: The exact CNF that was solved (10988 vars, 45743 clauses)
- `kissat_s5_solution.txt`: The raw SAT solution from Kissat
- `COLLISION.md`: This file
