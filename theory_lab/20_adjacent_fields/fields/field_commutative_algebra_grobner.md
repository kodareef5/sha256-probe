# Stub — Commutative algebra (Gröbner / F4 in a σ-aligned order)

**Lens:** `commutative-algebra` · **Status:** stub (not yet a register row) · **Novelty:** flagged-unpursued

## Structure
The collision condition is a polynomial system over GF(2). A Gröbner basis (Buchberger / F4 / F5,
via PolyBoRi) is the systematic way to expose an ideal's *hidden low-degree consequences*. The repo's
`three_filter_da_de` identity (`da_r = de_r`, reducing rounds 61–63 to one constraint) is an
**existence proof** that a non-obvious low-degree relation exists — F4 is the systematic hunt for siblings.

## Candidate reframe
Build the round system's ideal; choose a monomial order **aligned with the σ0/σ1 rotation structure**
so the schedule recurrence becomes near-triangular; run F4 and look for new low-degree elements below
the ANF degree the repo already measured.

## Why it's still a stub (not yet a register row)
- External models flagged Gröbner repeatedly; the repo wrote only a sketch
  (`../../sha256_review/april28_explore/principles/ALGORITHM_F4_sigma_aligned.md`,
  `.../items/item_76_grobner.md`) and **never ran F4**.
- Classical wisdom: ARX Gröbner bases explode (degree of regularity blows up). Plausibility ~2.
- **To promote:** write a concrete kill-criterion (e.g. "dead if the estimated degree-of-regularity
  exceeds the measured ANF max degree, or an F4 run on the N≤10 ideal in the σ-aligned order returns
  only relations the repo already knows by hand"). A cheap pre-check (degree-of-regularity estimate)
  decides whether it's even worth implementing.

## Relation to existing rows
Competes with `anf_degree` and `three_filter_da_de`. Sibling of the parked `algebraic-geometry-variety`
(same ideal, geometric vs algebraic framing).
