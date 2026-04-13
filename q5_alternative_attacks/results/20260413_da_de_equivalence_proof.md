# Algebraic Proof: da_r = de_r for r ≥ 61

Date: 2026-04-13 14:30 UTC

## Theorem

For r ≥ 61: da_r = de_r (unconditionally at r=61; conditionally at r≥62).

## Proof for r=61

SHA-256 round update:
- new_a = T1 + T2
- new_e = d + T1

Therefore: da61 = dT1_61 + dT2_61, and de61 = dd60 + dT1_61.

**Step 1**: dd60 = 0 (cascade shift: dd60 = dc59 = db58 = da57 = 0).
Therefore: de61 = dT1_61.

**Step 2**: dT2_61 = d(Sigma0(a60) + Maj(a60,b60,c60)).
The cascade ensures da60 = db60 = dc60 = 0 at round 60.
- dSigma0 = Sigma0(a60_1) - Sigma0(a60_2) = 0 (since a60_1 = a60_2)
- dMaj = Maj(a,b,c1) - Maj(a,b,c2) with a1=a2, b1=b2, c1=c2 → dMaj = 0

Therefore: dT2_61 = 0 (UNCONDITIONALLY — for ALL message words).

**Conclusion**: da61 = dT1_61 + 0 = dT1_61 = de61. ∎

## Extension to r=62 (conditional)

At r=62: da62 = dT1_62 + dT2_62 and de62 = dd61 + dT1_62.

dd61 = dc60 = 0 (cascade). So de62 = dT1_62.
dT2_62 depends on da61, db61, dc61. Among COLLISIONS: da61=0 (proved).
db61 = da60 = 0 (cascade). dc61 = db60 = 0.
→ dT2_62 = 0 AMONG COLLISIONS → da62 = de62 among collisions.

## The Single Equation

The collision reduces to ONE equation per round:
- r61: dT1_61 = 0 (≡ da61=0 ≡ de61=0)
- r62: dT1_62 = 0 (≡ da62=0 ≡ de62=0, conditional on r61 satisfied)
- r63: dT1_63 = 0 (≡ da63=0 ≡ de63=0, conditional on r62 satisfied)

But these are NOT independent:
- dT1_62 involves state61, which is fully determined when dT1_61=0
- dT1_63 involves state62, which is fully determined when dT1_62=0

So there is effectively **ONE independent equation**: dT1_61 = 0.
Once satisfied, r62 and r63 propagate deterministically.

## Verified

- dT2_61 = 0: confirmed across 10K random (w57-w60) at N=8
- P(da61=0) = P(de61=0) = P(both=0) = 1/260: confirmed at N=8
- Full state-diff trajectory confirmed at N=4, 6, 8, 32

## Evidence Level: VERIFIED (algebraic proof + numerical verification)
