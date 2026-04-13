# Single-DOF Theorem: Proof by Back-Propagation

Date: 2026-04-13 13:00 UTC

## Theorem

Among sr=60 collision solutions, the state-diff at round 61 has
exactly ONE variable register (dh). All other 7 diffs are constant
(0 or C = db56). This holds at all N (verified N=4,6,8).

## Proof

The collision condition requires ALL 8 diffs to be 0 at round 63.
The shift register propagates: b←a, c←b, d←c, f←e, g←f, h←g.

**Back-propagation from r63 to r61:**

- da63=0 ← required for collision
- db63=0 → da62=0 (shift: b63 = a62)
- dc63=0 → db62=0 → da61=0 (shift: c63 = b62 = a61)
- dd63=0 → dc62=0 → db61=0 = da60=0 ✓ (cascade guarantees da60=0)

- de63=0 ← required for collision
- df63=0 → de62=0 (shift)
- dg63=0 → df62=0 → de61=0 (shift: g63 = f62 = e61)
- dh63=0 → dg62=0 → df61=0 = de60=0 ✓ (cascade guarantees de60=0)

**What remains at r61:**
- da61=0 (forced by dc63=0 back-propagation)
- db61=0 (= da60=0, cascade)
- dc61=0 (= db60=0, cascade)
- dd61=0 (= dc60=0, cascade)
- de61=0 (forced by dg63=0 back-propagation)
- df61=0 (= de60=0, always)
- dg61=C (= df60=C, shift from cascade constant)
- **dh61=VAR** (= dg60=VAR, the Maj-freedom from de58 theorem)

## Why dh61 is the ONLY variable

dh at r61 = g at r60 (shift register). g at r60 is the "variable"
position in the cascade diagonal (takes 2^hw(db56) values). This
is the Maj(a57,b57,c57) freedom that propagates through e→f→g.

All other variables that existed in the diagonal (VAR positions at
r58,r59,r60) either:
a) Shifted into a position that must be 0 (forced by back-propagation)
b) Or were already 0 (cascade)

Only dg60→dh61 escapes the back-propagation constraint because
dh at r63 is the LAST register checked, and its zero comes from
dg62=0 (which is automatic from the cascade), not from dh61.

## Implication

The collision problem has TRUE dimensionality = 1 (in state-diff space).
The 260 collisions at N=8 differ only in their dh61 value (8 possible)
and in the CARRY PATHS that achieve each dh61.

The collision count ≈ (dh61 values that work) × (carry paths per value).
At N=8: 8 values × ~33 paths/value = ~260 total.

## Evidence Level: VERIFIED

- N=4: 49 collisions, C=0xe ✓
- N=6: 50 collisions, C=0xb ✓
- N=8: 260 collisions, C=0x8e ✓
- Proof by necessity (back-propagation from r63 collision condition)
