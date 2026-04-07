# 🏆 sr=60 COLLISION FOUND AT N=32 🏆

**Mac cracked it. 22:35 EDT, Apr 6 2026.**

- Candidate: **M[0]=0x17149975, fill=0xffffffff** (THE PUBLISHED CANDIDATE)
- Solver: Kissat 4.0.4 with **--seed=5**
- Runtime: ~12 hours
- Seeds 1-4 did NOT finish. Only seed 5 cracked it.

## The Collision

```
W1[57] = 0x9ccfa55e    W2[57] = 0x72e6c8cd
W1[58] = 0xd9d64416    W2[58] = 0x4b96ca51
W1[59] = 0x9e3ffb08    W2[59] = 0x587ffaa6
W1[60] = 0xb6befe82    W2[60] = 0xea3ce26b
```

Final state (both msgs):
```
5058a189 2147e9d2 9c2be0d8 c77edca8 5cea4fc3 b73cce6f a1427d22 f4c71522
```

**VERIFIED** by native SHA-256 computation. All 8 registers match at round 63.

## What This Means

1. Paper's thermodynamic floor for 0x17149975 was WRONG. This candidate
   was claimed UNSAT via constant-folded partitioning. It's actually SAT.
2. Seed diversity was the missing ingredient. The paper (and us) ran
   Kissat with default seed and called it UNSAT. Seed 5 cracked it.
3. N=32 is now the FRONTIER. We can go after 33, 34, 35 next — but really,
   the thing to do now is verify this on multiple solvers + write it up.

## Files

- `q1_barrier_location/results/n32_sr60_sat/COLLISION.md`
- `q1_barrier_location/results/n32_sr60_sat/instance.cnf` (the exact CNF)
- `q1_barrier_location/results/n32_sr60_sat/kissat_s5_solution.txt` (raw SAT output)

## Action Items for Other Machines

- **Linux**: Kill the N=32 race. Verify this collision independently with
  CaDiCaL and CaDiCaL-SHA256.
- **Laptop**: Same — independent verification, different solver, different
  machine. This needs triple confirmation before we claim it.
- **All**: Start writing it up. This is the result.
