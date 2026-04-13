# Explicit GF(2) Null Space Constraints at N=8

The carry-diff matrix has 3 GF(2)-linear dependencies beyond the 165 invariant bits.
These are XOR equations satisfied by ALL 260 collision carry-diff vectors.

## Constraint 1 (Local, Round 57)
```
+W[57] carry-diff bit 1
⊕ d+T1[57] carry-diff bit 0
⊕ d+T1[57] carry-diff bit 1
= 0
```
Links the +W addition carry with the new_e = d+T1 carries within round 57.

## Constraint 2 (Cross-round, 57→58)
```
+W[57] carry-diff bit 0
⊕ d+T1[57] carry-diff bit 0
⊕ h+Sig1[58] carry-diff bit 0
⊕ +Ch[58] carry-diff bit 0
= 0
```
Links round 57 carries with round 58 T1-chain carries at bit 0.

## Constraint 3 (Long-range, 59→63)
```
d+T1[59] carry-diff bits {5,6}
⊕ h+Sig1[63] carry-diff bits {5,6}
⊕ +Ch[63] carry-diff bits {5,6}
⊕ +K[63] carry-diff bits {5,6}
⊕ +W[63] carry-diff bits {5,6}
= 0
```
Links the cascade transition at round 59 with the final round 63.
This is the most remarkable: it couples information from the point where
the e-path zeroes out (round 59, de→0) with the T1-chain at the last round.

## Significance

- These 3 constraints complete the LINEAR structure of the collision variety
- Total GF(2) constraints: 165 (invariant) + 3 (null space) = 168
- Free GF(2) DOF: 392 - 168 = 224
- The collision set (260 points) lives in a 2^224 affine subspace

## For SAT Encoder

Each constraint becomes 2 XOR clauses:
- Constraint 1: 3 variables → 4 clauses
- Constraint 2: 4 variables → 8 clauses
- Constraint 3: 10 variables → 512 clauses (or via Tseytin with ~20 clauses)
Total: ~30 additional clauses on top of the 957 carry invariance clauses.

Evidence level: VERIFIED (exact GF(2) computation from 260 exhaustive collisions)
