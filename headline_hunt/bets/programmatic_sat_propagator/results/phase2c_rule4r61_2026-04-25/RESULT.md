# Phase 2C Rule 4 @ r=61 — `dA[61] = dE[61]` (Theorem 4 specialization)

## What this adds

Rule 4 of SPEC.md, specialized at r=61: `da_61 ≡ de_61 (mod 2^32)`.

Under the cascade-DP construction, `dT2_61 = dSigma0(a_60) + dMaj(a_60, b_60, c_60) = 0` because all three of (a_60, b_60, c_60) have zero diff (cascade through r=60). So the unified Theorem 4 reduces to bit-equality between dA[61] and dE[61] — same propagation structure as Rule 5.

## Implementation

Refactored the equality machinery to support multiple register-pair groups. Two groups now active:

| Group | Pair | Constraint | Reason |
|---|---|---|---|
| 0 | dC[63] ↔ dG[63] | Rule 5 (R63.1) | shift register: c_63 = a_61, g_63 = e_61, da_61=de_61 |
| 1 | dA[61] ↔ dE[61] | Rule 4 specialization | dT2_61 = 0 under cascade |

Both groups use identical bit-by-bit watch logic. The flat `r63_eq_pairs[64]` array holds 32 bits × 2 groups, with reverse lookup keyed off SAT-var ID.

## Test (sr=61 expose, bit-10 m=0x3304caa0, 50k conflicts)

| Mode | wall | cb_propagate fires |
|---|---:|---|
| Propagator OFF | 7s | 0 |
| Propagator ON  | **2s** | 416 = 352 (Rules 1+2) + 32 (Rule 5) + 32 (Rule 4@r=61) |

3.5× speedup persists. Both equality rules fire the expected 32× each (one per bit position). No backtrack failures, no extra overhead vs Phase 2C Rule 5 alone.

## Cumulative Phase 2 status

| Phase | Rules | LOC | Mode A speedup |
|---|---|---:|---:|
| 2A | API smoke | n/a | — |
| 2B | 1+2 | 280 | 4× |
| 2C-Rule5 | 1+2+5 | 370 | 4× |
| **2C-Rule4@r61** | **1+2+5+4(r=61)** | **400** | **3.5×** |
| 2C-future | + 3 | TBD | + Mode FORCE three-filter |
| 2C-future | + 4@r=62, r=63 + 6 | TBD | **modular Theorem 4 — value-bearing** |

## Why r=62 and r=63 are harder

At r=61, dT2_61 = 0 by cascade structure — pure bit-equality.

At r=62: `dT2_62 = dSigma0(a_61) + dMaj(a_61, a_60, a_59)`. This involves ACTUAL register values (a_61's value, a_60's value, a_59's value), not just diffs. To enforce `da_62 − de_62 = dT2_62 mod 2^32` as a propagator, we need:
1. SAT vars for actual a_60, a_61 (not just dA[61] aux). The encoder allocates these but the varmap currently exposes only diff-aux vars.
2. dSigma0 and dMaj computation on partially-decided register values.
3. Modular subtraction reasoning: `dA[62] − dE[62] = dT2_62`.

That's a real implementation extension, not a refactor. ~400-500 LOC. Will need to extend the encoder to also dump actual-register varmap entries (alongside the diff-aux varmap currently shipped).

For now: Rule 4@r=61 ships clean as the structurally simplest case. The propagator's CDCL-equivalent enforcement of cascade-DP modular invariants at r=61 is now complete.

## Build artifacts

`cascade_propagator.cc`: ~400 LOC. Same build command:
```bash
g++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
    cascade_propagator.cc -lcadical -o cascade_propagator
```

Run logs in this directory.
