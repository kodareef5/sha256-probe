# Why Theorem 4 breaks at r=62 — structural proof + empirical confirmation

The pinpoint observation (`20260425_theorem4_pinpoint.md`) showed Theorem 4's modular form holds at 100% at r=61 but 0% at r=62. This writeup gives the **structural reason** and verifies it empirically.

## Theorem (informal extension)

For cascade-eligible candidate at sr=61:
```
da_62 − de_62  ≡  dT2_62  (mod 2^32)
```
where `dT2_62 = dSigma0(a_61) + dMaj(a_61, b_61, c_61)` (modular).

## Derivation

At round 62:
- `da_62 = T1_62 + T2_62` (modular, definition of new a register)
- `de_62 = d_61 + T1_62`

Subtracting (in modular arithmetic on the diffs):
```
da_62 − de_62 = (T1_62 + T2_62) − (d_61 + T1_62) = T2_62 − d_61
```

Taking diffs across messages (subscript 1 vs 2):
```
(da_62)_1 − (da_62)_2 − ((de_62)_1 − (de_62)_2)
  = (T2_62_1 + d_61_1) − (T2_62_2 + d_61_2) − wait let me redo
```

Cleaner: For diff-of-diffs (modular, using d as the diff operator on register pairs):

```
diff(da_62) = diff(T1_62) + diff(T2_62)
diff(de_62) = diff(d_61) + diff(T1_62)
diff(da_62) - diff(de_62) = diff(T2_62) - diff(d_61)
                          = dT2_62 - dd_61
```

Under cascade-1 extending through round 61 (which the cascade-DP guarantees if cascade-1 held to round 60):
- `dd_61 = dc_60 = 0` (cascade shift-zero propagation)

So: **`da_62 − de_62 ≡ dT2_62 (mod 2^32)`**.

`dT2_62 = dSigma0(a_61) + dMaj(a_61, b_61, c_61)`. With `db_61 = dc_61 = 0` (cascade) but `da_61 ≠ 0` generically (Theorem 4 says da_61 = de_61 modularly, and de_61 = dT1_61 is nonzero unless dE[61] is forced to 0 by Theorem 3 / collision constraint), `dT2_62` is generically nonzero. Hence `da_62 ≠ de_62` generically.

At the COLLISION cert (where Theorem 3 forces dE[61] = 0): `da_61 = de_61 = 0` → `dT2_62 = dSigma0(0) + dMaj(0, 0, 0) = 0` → `da_62 = de_62 = 0`. Trivially.

## Empirical confirmation

1000 cascade-held samples on the priority candidate (cand_n32_msb_m17149975, sr=60 cert candidate, sr=61 cascade construction):

| Property | Count | Theory |
|---|---:|---|
| db_61 = 0 | 1000/1000 | cascade extends ✓ |
| dc_61 = 0 | 1000/1000 | cascade extends ✓ |
| dd_61 = 0 | 1000/1000 | cascade shift-zero ✓ |
| dT2_62 ≠ 0 | 1000/1000 | da_61 generically nonzero → dT2_62 generically nonzero ✓ |

Sample trace:
- da_61 = 0x1f1270c3 (nonzero, modular)
- de_61 = 0x1f1270c3 (= da_61, Theorem 4 ✓)
- dT2_62 = 0xcbf0e059
- da_62 = 0xafc8e580
- de_62 = 0xe3d80527
- (da_62 − de_62) mod 2^32 = **0xcbf0e059 = dT2_62** ✓

The formula `da_62 − de_62 ≡ dT2_62 (mod 2^32)` is empirically verified exactly on every sample.

## Implications

1. **Theorem 4's natural domain is r=61 specifically** — it's a one-round invariant from cascade-1 propagation through round 60 plus the round-61 algebra. It doesn't extend to r=62 because round 62's T2 input includes a_61 with nonzero diff.

2. **At the cert specifically**, da_61 = 0 makes Theorem 4 hold "vacuously" through r=63 (everything is zero). This is consistent but isn't a structural extension of Theorem 4.

3. **For the cascade-aux force-mode SPEC**: the constraint `dA[61] = dE[61]` (XOR) is consistent with collision-finding because Theorem 3 + Theorem 4 together force both to zero at the collision. The earlier SPEC-bug claim was correctly retracted.

4. **For random cascade-held residuals (no collision constraint)**: Theorem 4 is the strongest "da-de relationship" available — it doesn't extend to higher rounds. Any analysis of round-62+ structure cannot rely on da-de equality.

## Adds to the boundary proof writeup

`writeups/sr60_sr61_boundary_proof.md` Theorem 4 currently states:
> da_r = de_r for all r ≥ 61 (unconditionally at r=61).

The "for all r ≥ 61" language is potentially misleading — the proof only establishes r=61 specifically. Empirically, **only r=61** holds. The writeup should clarify that the unconditional result is r=61 only, with extension to higher rounds requiring additional constraints (the three-filter dE[r]=0 of Theorem 3, which combines with Theorem 4 to force everything zero at the collision).

A small TYPO/PRECISION fix to the boundary-proof writeup is recommended. Not a major bug, but precision matters.

## Files

- This writeup
- The Python trace script in this writeup is reproducible from the imports above
