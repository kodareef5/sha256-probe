---
date: 2026-06-09
status: T0.2 COMPLETE — VERDICT H_dead: the sr/cascade structure does NOT transfer to the standard metric
author: macbook-claude (fable model test)
evidence_level: EVIDENCE (one direct measurement + 3 converging structural/empirical legs)
---

# T0.2: does the sr-regime structural work transfer to the standard step-reduced metric?

The question that decides whether the sr program produced transferable science or only
characterized one construction. **Verdict: H_dead** — the repo's signature structural assets
are properties of the cascade *solution manifold*, not of SHA-256's round function, and they
have no analog on the standard (100%-schedule, active-register-trail) axis.

## The decisive measurement: carry-diff invariance is manifold-specific, not round-function

The repo's flagship "round-function property" candidate is the **42% (up to 88% on the
a-path) carry-diff invariance** (`writeups/carry_structure_unified.md`). I measured the
a-path carry-diff invariance of the addition T2 = Σ0(a) ⊞ Maj(a,b,c) on **generic random
differentials** (the regime a *standard* trail's active a-register sits in) vs the cascade:

| Differential regime | a-path carry-diff invariant bits (N=8) | (N=32) |
|---|---|---|
| Generic / random (standard-trail-like, active a-path) | **12%** (only the trivial LSB) | **3%** |
| Cascade collision set (da=0 + shift-register-structured db,dc) | **88%** (documented) | — |

With generic active-register differences, **there is no carry-diff structure** beyond the
trivial carry-into-LSB=0. The 88% appears ONLY inside the cascade manifold, where da56=0
propagates through the shift register to zero/structure the whole a-path. **Standard local
collisions keep the a-register active across the disturbance window** (that is what a
disturbance *is*), so they land in the 3–12% regime, not the 88% one. The invariance is a
property of the cascade *solution set*, not of the SHA-256 round function. (Deterministic
measurement, seed=12345; reproduce: `lib/sha256.py` Σ0/Maj + carry = (x+y)^x^y.)

## Three converging legs (all point H_dead)

1. **Metric orthogonality (T0.1).** The standard axis enforces **100% schedule compliance**.
   The entire sr apparatus — gap placement, the σ1-recurrence enforcement, the sr=60/61
   boundary, the "freed-equation" structure — is *about which schedule equations to relax*.
   When the schedule is fully enforced there is nothing to relax: the structure has **no
   home** on the standard axis. The σ1-conflict statistic (the other transfer candidate) is
   by definition a statement about the schedule boundary; standard trails have no such
   boundary, so it is not merely non-transferable but inapplicable.

2. **The repo's own predictor-falsification.** de58-image-size and hard-bit-total predictors
   are **search-irrelevant** to the sr solver itself (Spearman ρ ≈ 0 at 10M conflicts;
   `CLAIMS.md`). A structural quantity that does not even predict its *own* solver's behavior
   is not a candidate transferable lever.

3. **Subsumption by signed-DC.** Whatever genuine carry structure the cascade exposes is
   already captured natively by the **signed-difference / wordwise-modular-carry** machinery
   the record-holders use (Mendel signed-DC; the SAT+CAS wordwise propagator of arXiv
   2406.20072 decomposes exactly these carry cascades). The repo's "147 invariant carry-diff
   bits reject 100% of non-collisions" is the kind of necessary-condition propagation that
   framework performs automatically — a re-discovery in cascade coordinates, not a new lever.

## What this means for direction

- The sr/cascade structural program (carry automaton, de58 law, treewidth, sr boundary) is a
  **deep characterization of one construction**, not transferable science for the standard
  metric. Continued sr-axis structural analysis has low EV.
- The one defensible *standalone* output of the sr program is the **boundary/clarification
  paper** (the T0.1 lattice + the sr=60 certificate + the honest "orthogonal axes, does not
  beat 37/39" framing) — valuable as a clarification, not as a step record.
- **All remaining experimental EV is on the standard / R-axis**: the block-2 absorber and the
  SAT+CAS engine (Tier 1) and the decoupled local-collision search (Tier 2). That is exactly
  where the rest of this program goes.

## Honest scope

This is EVIDENCE, not proof. The measurement falsifies the strongest H_real candidate (carry
invariance) directly; the other legs are structural/definitional. A residual H_real
possibility — that the carry-*automaton* permutation property (branching ≤2) is round-function
intrinsic — is not separately tested here, but it too is a statement about the cascade
collision set's parameterization and is already implied by signed-DC carry determinism. The
σ1-conflict-on-standard-trails measurement was not run (it needs cloned standard trails, and
T0.1 shows it is structurally inapplicable); if a standard trail is obtained in Tier 2 it can
be checked opportunistically, but the verdict does not hinge on it.
