# M16-MITM backward enumerator: design-gap analysis
**2026-04-26 04:25 EDT** — block2_wang bet — substantive critique.

## What I tried to design

After validating `m16_mitm_forward.c` at N=8 and N=10 (200/200 each),
the next step in `M16_MITM_FOUNDATION.md` is a backward enumerator:
"For each W[60], compute the REQUIRED state at round 59 for cascade-2
(de60=0) to succeed."

## What goes wrong

**Cascade-2 trigger condition** at slot 60:
  de60 = pair1.s60[e] - pair2.s60[e] = 0 mod 2^N

Round-60 update:
  pair1.s60[e] = pair1.s59[d] + T1(pair1.s59, W1[60])
  pair2.s60[e] = pair2.s59[d] + T1(pair2.s59, W2[60])

Setting de60 = 0:
  pair1.s59[d] - pair2.s59[d] = T1_pair2 - T1_pair1

But T1 depends on the s59 itself (via Σ1, Ch). So the constraint is
ONE modular equation on (pair1.s59, pair2.s59) per W[60] choice.

**The "required state at round 59" is not a single state — it's a
codimension-1 surface in the joint (pair1.s59, pair2.s59) space.**

## Implication for matching

Forward enumerator emits state_59 records: 2^(3N) at full enumeration.
Backward "required" states: a codimension-1 surface in 16N-bit joint
state space → effectively 2^(15N) valid (pair1.s59, pair2.s59) per W[60].
× 2^N W[60] values = 2^(16N) backward-valid records.

Match probability per forward record: a random forward state_59 satisfies
a 1-bit mod constraint with probability 2^-1. So **half of forward
records match SOME backward W[60]** — but this is not a filter, it's
a pass-through.

The MITM design fails to filter the search space because:
1. Pair-1's state_59 is NOT independent of pair-2's state_59 — cascade-1
   ties them via deterministic round operations.
2. Cascade-2 trigger is a 1-bit modular constraint (low information).
3. The match key (state_59) is too informative — both forward and
   backward saturate it.

## What this means for the M16-MITM bet

The "MITM at slot 59" framing as written in `M16_MITM_FOUNDATION.md`
does **not** give a complexity advantage over backward-construction:
- Backward construction at N=10 found 946 collisions in 117s.
- A naive M16-MITM at N=10 would emit 2^30 forward records and 2^11
  cascade-2 backward records, with a half-pass match filter producing
  ~2^29 match candidates. Each candidate needs full verification = 2^29
  full forward runs. NOT FASTER than direct enumeration.

**The MITM advantage is mathematically illusory at this design level.**

## What COULD give MITM an advantage

A real MITM needs an ASYMMETRIC matching key — something forward
constrains tightly and backward constrains loosely (or vice versa),
so that match candidates are filtered by a high-information equation.

Candidates worth investigating:
1. **Match on full state at round 56** (pair1.s56 + pair2.s56). Forward
   emits at slot 59 with 8N+ bits of constraint; backward could derive
   what s56 is needed for cascade-2-triggered de60=0 at sl60. The
   match key has ~16N bits — heavy filter.
2. **Match on state_60 with cascade-extending constraint** (not state_59).
3. **Use XOR-linear approximation** to enumerate a low-rank subspace of
   (W57..W60) that triggers both cascades. This is the sr=60 approach
   used in the q5 prototype — already O(2^32) for sr=60, not O(2^96).

## Closing recommendation

**Do not implement m16_mitm_backward.c per M16_MITM_FOUNDATION.md as
written.** The design has a load-bearing assumption (state_59 as
informative match key) that does not hold.

Better leverage: re-derive the design starting from XOR-linear approximation
(à la Wang 2005) — enumerate the low-rank linear differential subspace
that triggers BOTH cascades simultaneously, then verify candidates.
Estimated effort: ~1 week of design work, more than the 2-3 days
estimated for the original M16-MITM port.

## Status

- M16-MITM forward enumerator: **complete + validated** at N=8/N=10.
- M16-MITM backward enumerator: **DESIGN-GAP IDENTIFIED**, do not
  implement as foundation memo specifies.
- M16-MITM is not a hot path until a better matching-key design is found.

EVIDENCE-level critique. Not a closure on the bet, but a redirect:
implementer attention should go to backward-construction scaling
(M14 → M16) or sat_pilots/, not MITM-as-written.
