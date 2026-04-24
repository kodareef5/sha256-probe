# dMaj structure under cascade — partial step toward g60 prediction

Working toward closed-form g60 prediction. Key intermediate result: dMaj_57's
GF(2) (XOR) form has a clean structure, but the cascade needs MODULAR
difference, and the XOR-to-modular conversion is the open carry-chain analysis.

## What's derived

For the cascade-aware Maj at round 57:
- da57 = 0 (cascade), so a1_57 = a2_57 = a (same value)
- db57 = 0 (cascade-shift propagation), so b1_57 = b2_57 = b
- dc57 ≠ 0 (= db56_mod, candidate constant), so c1_57 ≠ c2_57; let dc = c1 ⊕ c2 ≠ 0

Using GF(2) identity **MAJ(a,b,c) = ab ⊕ ac ⊕ bc**:

```
dMaj_57_xor = MAJ(a,b,c1) ⊕ MAJ(a,b,c2)
            = (ab ⊕ ac1 ⊕ bc1) ⊕ (ab ⊕ ac2 ⊕ bc2)
            = a·(c1 ⊕ c2) ⊕ b·(c1 ⊕ c2)
            = (a ⊕ b) · dc                  [bitwise AND with dc as a mask]
```

Therefore:
- Bit i of dMaj_57_xor:
  - `= 0`           if dc[i] = 0
  - `= (a XOR b)[i]` if dc[i] = 1

Since a57 = const + w1_57 (uniform random for random w1_57), and b57 = a56 (candidate constant):
- (a57 XOR b57)[i] is uniform random over random w1_57.

**Conclusion (XOR domain)**: dMaj_57_xor takes 2^(HW(dc57)) distinct values uniformly. For MSB candidate, dc57 = db56 = 0x754fbd5d → HW = 21 → 2^21 ≈ 2M distinct dMaj_xor values.

This matches the empirical observation that 70k distinct Δe58 values from 100k samples — consistent with a 2^21-element underlying support.

## Why this doesn't directly give g60 prediction

The cascade uses **modular** dT2_58 = T2_1 − T2_2 (mod 2^32), not XOR. We have:
- T2_1 − T2_2 = (Sigma0(a) + Maj_1) − (Sigma0(a) + Maj_2) = Maj_1 − Maj_2

Maj_1 and Maj_2 share most bits but differ where dc57[i] = 1. Their modular difference depends on the carry chain through those differing bits.

Going from XOR-difference to modular-difference for an N-bit quantity with sparse known XOR structure is the well-known "ARX cryptanalyst's nightmare" — see Lipmaa/Moriai 2001 for the original treatment. There's no clean closed form, but partial structural results exist.

## What this enables for g60 prediction

The marginal distribution of Δe58 is supported on roughly 2^HW(db56) values, NOT uniform on 2^32. This is a much smaller search space than naive "Δe58 is uniform on 2^32" assumed.

For each candidate's HW(db56):

| Candidate | db56_mod | HW(db56) | Δe58 support size |
|---|---|---:|---:|
| MSB | 0x754fbd5d | 21 | 2^21 |
| bit10_3304caa0 | 0x74616db3 | 16 | 2^16 |
| bit06_6781a62a | 0x9e59935d | 17 | 2^17 |
| bit17_8c752c40 | 0x89995121 | 13 | 2^13 |

Smaller HW(db56) → smaller support → potentially fewer effectively-uniform g60 bits. This is testable empirically. If predicted g60 hard-bit count tracks HW(db56) ratio, we have a half-prediction even without full closed form.

(Empirical g60 from earlier: MSB ~19, bit10 ~16, bit06 ~21, bit17 ~19 hard bits. Doesn't obviously track HW(db56) — needs more careful analysis. Note bit06_6781a62a has HW(db56)=17 but g60=21 hard bits, while bit17 has HW=13 but g60=19 hard bits. Mostly flat.)

## Open

The XOR-to-modular mapping is the bottleneck. Two ways forward:
1. Derive the per-bit modular distribution from the XOR structure analytically (Lipmaa/Moriai-style carry analysis) — multi-day, deeply technical.
2. Empirically characterize the modular distribution and tabulate for each candidate's specific dc57 mask — bypass the closed form, just build a per-candidate predictor table.

(2) is much faster and probably enough for the bet.

## What's actually shipped

- `dMaj_xor = (a XOR b) AND dc` derivation captured here
- Empirical observation that Δe58 support ≈ 2^HW(db56) confirmed via 70k distinct values from 100k samples on MSB
- HW(db56) per candidate computable in O(1) — tabulated for top candidates above

Not yet a full g60 predictor, but a real structural step beyond "g60 needs marginal model — TBD".
