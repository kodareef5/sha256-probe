# Theorem 4 boundary pinpointed: holds at r=61 modular, breaks at r=62

Earlier writeup (`bets/block2_wang/residuals/CLUSTER_ANALYSIS.md`) noted that 0/104,700 records have da63 == de63 (XOR), suggesting Theorem 4 fails at r=63. This sharpens the picture.

## Method

Per cascade-held forward run on the priority candidate, dump round-61, round-62, round-63 register diffs and check both XOR-equality and MODULAR-equality of da and de.

## Result (5,000 cascade-held samples)

| round | da_XOR == de_XOR | da_MOD == de_MOD |
|---:|---:|---:|
| **r=61** | 2/5000 (0.04%) | **5000/5000 (100%)** |
| r=62 | 0/5000 (0.00%) | 0/5000 (0.00%) |
| r=63 | 0/5000 (0.00%) | 0/5000 (0.00%) |

## Interpretation

1. **Theorem 4 (`writeups/sr60_sr61_boundary_proof.md`) is empirically CONFIRMED at r=61 in modular form**. da_mod = de_mod for 100% of samples — no exceptions, no probabilistic relaxation.

2. **The XOR form is a much weaker statement**: at r=61, da_xor == de_xor only ~0.04% of the time, even though the modular values are identical. Reason: same modular integer can have many XOR representations (the carry chain in modular addition produces specific bit patterns).

3. **At r=62, both forms fail completely** (0/5000). The shift from 100%-modular-equal to 0%-modular-equal happens in exactly one round. This is a clean structural transition.

## Why this matters

The boundary proof's Theorem 4 is precise about r=61 (the cascade-2 directly enforces de60=0, then T1+T2 propagation at round 61 with da60=db60=dc60=0 forces da61=de61 modularly). But Theorem 4 doesn't claim da=de extends to r=62 or beyond — and the empirical data confirms it doesn't.

So:
- **r=61: da=de modular** (proven, empirically validated 5000/5000)
- **r=62: da, de diverge** (round 62 introduces new T1/T2 contributions that break the equality)
- **r=63: da, de fully diverged** (continued divergence)

## Refines my earlier writeup

The block2_wang `CLUSTER_ANALYSIS.md` claim "Theorem 4 doesn't extend to r=63" is true but incomplete. The boundary is sharper: **r=61 modular = perfect; r=62+ modular = 0%**. The XOR-form check I used in the cluster analysis is too strict (would only catch 0.04% even when Theorem 4 holds).

For block2_wang trail design: at the residual round (r=63), no clean "da=de" relationship to exploit. Trail engine has to handle da and de independently.

For mitm_residue cascade theory: round-61 da=de IS a clean modular invariant — could be useful as a constraint in any cascade-aware SAT propagator.

## Concrete note for cascade_aux_encoding

The Mode B "force-cascade" encoding currently enforces `dA[61] = dE[61]` via XOR equality (per SPEC.md step 4). If the empirical result at the round-61 transition is **modular** equality, this XOR encoding may be either:
- Too strong (forces a stronger constraint than needed) — could reduce SAT space artificially
- Or still consistent with the modular equality (which holds anyway) — XOR equality is a strict-subset sample of modular-equal cases

Worth checking: is the SPEC's XOR-form `dA[61] = dE[61]` filter a soundness issue? Re-deriving Theorem 4's PROOF in the SPEC suggests modular is the natural form. The encoder's XOR form is wrong-by-form even if it happens to admit the cert solution.

This is a **bug in the cascade_aux force-mode SPEC** that should be flagged for review.

## Concrete next-actions

1. Audit cascade_aux_encoding/encoders/SPEC.md and cascade_aux_encoder.py: is `dA[61] = dE[61]` enforcing XOR or modular equality? If XOR, that's incorrect per Theorem 4 — fix.
2. Larger sample (1M instead of 5k) to confirm r=61 modular equality holds at any scale.
3. Theoretical: derive WHY r=61 is the exact boundary — what specific computation at round 62 breaks da=de? Probably the dT1_62 contribution where dCh involves f61, g61 that aren't shift-zero.
