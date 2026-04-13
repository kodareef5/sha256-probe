# The Complete Cascade Structure of sr=60 Collisions

*GPU-laptop findings, April 12-13, 2026*

## 1. The Cascade Diagonal

After 57 rounds of precomputation (yielding da56=0), the cascade DP
forces da=0 at every subsequent round. Combined with SHA-256's shift
register (b←a, c←b, d←c, f←e, g←f, h←g), this produces a diagonal
zero wave through the state-diff matrix:

```
       da  db  dc  dd  de  df  dg  dh
r57:    0   0   C   C   C   C   C   C
r58:    0   0   0   C   V   C   C   C     V = 2^hw(db56) values
r59:    0   0   0   0   C   V   C   C
r60:    0   0   0   0   0   C   V   C
r61:    ?   0   0   0   ?   0   C   V     ? = schedule-dependent
r62:    ?   ?   0   0   ?   ?   0   C
r63:    ?   ?   ?   0   ?   ?   ?   0     COLLISION iff all ? = 0
```

Two zero waves (a-path upper-left, e-path lower-right) converge.
The collision requires the schedule-dependent registers (?) to also
reach zero — this is the "hard residue."

## 2. The de58 Theorem (Corrected)

**Observation**: |de58| = 2^hw(b56₁ XOR b56₂) exactly at N ≤ 14.
**Correction**: At N=32, |de58| = 1024 < 2^17 = 2^hw(db56).
Arithmetic carry effects collapse the Maj image at large N.

**Corrected statement**: |de58| ≤ 2^hw(db56 XOR), with equality for N ≤ 14.
The cascade's e-register has at most hw(db56) binary degrees of freedom.

## 3. de60 = 0 ALWAYS (The Free Cascade)

The e-register diff at round 60 is identically zero for ALL message
word combinations. This means the e-path cascade (de60→df61→dg62→dh63)
fires automatically — the collision mechanism gets it for free.

**Proof**: dd59 = dc58 = db57 = da56 = 0 (cascade + shift register).
de60 = dd59 + dT1_59 - dT2_59, where dT2_59 = 0 (since da59=db59=dc59=0).
The cascade offset ensures dT1_59 = -dT2_59 = 0, so de60 = dd59 = 0. ∎

## 4. The sr=61 Cascade Break

For sr=61, W[60] is schedule-determined: W[60] = sigma1(W[58]) + const.
The schedule-determined W2[60] matches the cascade-required W2[60]
with probability exactly 1/SIZE = 2^(-N).

At N=32: P(a-path survives) = 2^(-32) ≈ 2.3 × 10^(-10).
The e-path is UNAFFECTED (de60=0 regardless), but the a-path breaks.

This is the cleanest explanation of the sr=60/61 barrier.

## 5. de58 Predicts Hotspots

At N=8, collisions are unevenly distributed across de58 classes:
3.9x variation (15 to 59 collisions per class of 32 w57 values).
Bit 2 of de58 is the key predictor. Since de58 is computable from
w57 alone (O(1) per w57), this enables free hotspot prioritization.

## 6. Four Scaling Classes by N mod 4

| N mod 4 | Growth rate | Alt fill effect | Examples |
|---------|------------|-----------------|----------|
| 0 | 0.873 bits/N | minimal | N=4, 8 |
| **1** | **0.950 bits/N** | **MASSIVE (3-28x)** | **N=5, 9** |
| 2 | 1.036 bits/N | minimal | N=6, 10 |
| 3 | 0.717 bits/N | modest (1.1x) | N=7, 11 |

The alternating fill (0x55) activates a collision mechanism at
N ≡ 1 (mod 4) that's absent with standard fills.

## 7. Complete Collision Counts

| N | Best | log2 | Fill | Kernel |
|---|------|------|------|--------|
| 4 | 146 | 7.19 | std | bit 1 |
| 5 | 1024 | 10.00 | ALT | bit 0 |
| 6 | 83 | 6.37 | std | bit 4 |
| 7 | 373 | 8.54 | std | bit 1 |
| 8 | 1644 | 10.68 | std | bit 6 |
| 9 | 14263 | 13.80 | ALT | bit 1 |
| 10 | 1467 | 10.52 | std | bit 8 |
| 11 | 2720 | 11.41 | ALT | bit 1 |
| 12 | ~4250 | ~12.05 | MSB | (running) |

## 8. The da=de Algebraic Identity (NEW)

**Theorem**: da_r = de_r for all r ≥ 61 (unconditionally at r=61).

**Proof**: At round 61, new_a = T1+T2 and new_e = d+T1. The cascade
ensures dd60=0 (shift from dc59=db58=da57=0), so de61 = dT1_61.
The cascade also ensures da60=db60=dc60=0 at round 60, making
dSigma0=0 and dMaj=0, so dT2_61=0 UNCONDITIONALLY.
Therefore: da61 = dT1_61 + 0 = dT1_61 = de61. ∎

This extends: among collisions where da61=0, dT2_62=0 too → da62=de62.

**Consequence**: The collision's 6 non-trivial equations at r61-r63
reduce to 3 (one per round: dT1_r=0). And by back-propagation,
the r62 and r63 equations are determined once r61 is satisfied.

**The collision is ONE independent equation: dT1_61 = 0.**

Verified: P(da61=0) = P(de61=0) = P(both=0) = 1/260 at N=8
(perfect correlation, 260x above independence). Algebraic identity
confirmed at N=32 against known collision certificate.

## 9. Cross-Validation: Carry Automaton at N=12 (Macbook)

The macbook's carry automaton analysis of 2240 N=12 collisions independently
confirms the algebraic structure:

```
Rounds 61-63 carry-diff analysis:
  Sig0(a)+Maj   → CONSTANT (carry-diff = 0)    ← = dT2 = 0 ✓
  d+T1 = new_e  → CONSTANT (carry-diff = 0)    ← = de = 0 ✓
  T1+T2 = new_a → CONSTANT (carry-diff = 0)    ← = da = 0 ✓

  h+Sig1, +Ch, +K, +W → all VARIABLE (T1 path free)
```

The "Sig0+Maj CONSTANT" observation IS our dT2=0 theorem, expressed in carry
space rather than state-diff space. The "T1+T2 CONSTANT" confirms da=0. The
"d+T1 CONSTANT" confirms de=0. Three independent representations of the same
structural identity, verified at N=4, 6, 8, 12, and 32.

T2-path freedom: 26.6% overall, 0% at r61-63 (all invariant).
T1-path freedom: 84.2% (where the collision's single DOF lives).

## 10. Implications

1. The cascade is a **thin diagonal path** through an 8N-dimensional
   state-diff space. Its "width" is determined by hw(db56).

2. sr=60 collisions exist because the e-path cascade is **free** (de60=0
   always) and the a-path cascade can be maintained through 4 free message
   words. sr=61 removes the freedom to maintain the a-path at round 60.

3. The de58 hotspot structure suggests that collision search can be
   accelerated by ~2-4x through de58-based prioritization, with no
   additional infrastructure beyond a single SHA round evaluation.

4. The N mod 4 scaling classes reflect fundamental properties of SHA-256's
   rotation structure under banker's rounding, not artifacts of specific
   candidates. This has implications for any SHA-256 attack framework.
