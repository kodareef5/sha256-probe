# Distribution guide — how to hand the 185 cards to a fleet

Generation is **closed at wave 8** (saturation; see SYNTHESIS §wave-8). This file is the hand-off:
how to turn the catalog into parallel work without 185 agents each rebuilding the same thing.

**The key fact for distribution:** the cards do *not* split one-per-agent. They split into a handful of
**batches that share one buildable artifact.** Build the artifact once and a dozen cards collapse to
near-free queries on it (a rank, a spectrum, a table lookup). So the unit of work is the *batch*, and
the first task in every batch is the same: **build the shared kernel**, then fan the cards out.

> Scope: this covers the 185 `wild_angles/` cards only — not the 25-entry conservative register in
> `../30_register/`. All probes are read-only toward `../../sha256_review/` and reuse its `lib/sha256.py`. No SAT.

---

## The 4 shared kernels (build these; everything hangs off them)

| kernel | what it is | unlocks |
|---|---|---|
| **K1 · GF(2) round-Jacobian** | finite-difference linearization of the masked round/difference map (per-round `A_i,B_i,C`) + a corank/kernel routine. The repo's `block2_wang/encoders/preimage_lift.py::gf2_eliminate` is ~ready (rank 96 / 416-free already computed); `schedule_dep_analysis.py` gives the dependency graph. | **Batch A** (whole), most of **Batch D** |
| **K2 · small-N collision counts** | exact collision lists / counts at N=2…14 — **already on disk** in the repo (BDD collision-list builder). | **Batch C** (whole), the calibration side of **Batch B** |
| **K3 · per-round gating-count** | extend `coincidence_variety/gap_analysis.c` to count, per round, the independent conditions gating a collision, and re-verify `g1 ⟂ h` (the 1.005-ratio independence). | **Batch B** (whole) |
| **K4 · cascade-differential image sizes** | the `\|de57\|,\|de58\|,\|de59\|,\|de60\|` table under the **modular** (not XOR) differential — repo already measured `\|de58\|=2^10` at N=32, others constant. | **Batch E** (whole) |

A coordinator who builds K1–K4 (≈4 spikes, all cheap, all read-only) unlocks ~150 of the 185 cards.

---

## Batch A — "Is 132 a corank?"  ·  kernel K1  ·  **flagship**

The single prediction the most lenses share: the 132 hard-core bits are the **corank / kernel / self-stress /
frozen-set** of one linear map — *not* a CDCL artifact (which is all the repo currently calls them).

**Cards (≈15):** `W2-CT1` (controllability cokernel) · `W2-CT5` (unobservable subspace) · `W2-RG2`
(self-stress dim) · `W4-IG1` (Fisher kernel) · `W4-FP2` (S-transform zero-atom) · `W4-SH2` (dim H¹) ·
`W4-CS1` (do-orphans) · `W6-OC3` (costate kernel) · `W6-MA1` (matroid cocircuit corank) · `W7-FC1`
(meet-irreducibles) · `W7-QW3` (discriminant corank) · `W8-RD3` (IB sufficient-statistic dim) · `W8-KC1`
(active-difference 2-core) · `W8-KC3` (frozen variables) · `W1-GE3` (Morse–Bott Hessian kernel).
Adjacent: `W3-GN3` (zonotope degeneracies), `W2-NT2` (Weil subspace), `W2-SO4` (Turing modes).

**Run order:** `W6-MA1` first — it runs on the existing `gf2_eliminate`, so it's nearly free *today*.
Then the others are one-line corank/kernel queries on the **same K1 matrix**.

**Decisive:** compute the corank and its basis; check alignment with the named 132 = {da,db,de,df @ r63}
∪ {4 dc anchors}. **A clean hit confirms ~15 cards at once and upgrades "132 = solver artifact" → "132 =
corank of an explicit map."** A clean miss (corank ≠ 132, or wrong support) kills the whole cluster — the
single highest-information experiment in the catalog.

---

## Batch B — "Is the wall exactly two independent conditions?"  ·  kernel K3

`2^-2N` per enforced round, pinned to the repo's own `g1=0 ∧ h=0` (two independent N-bit conditions, ratio 1.005).

**Cards (≈25):** `W1-PH1` · `W2-CT4` · `W2-RG1` · `W2-NT4` · `W2-PC2` · **`W3-CA1`** (cascade = lens;
the two conditions ARE PutGet ∧ PutPut — plausibility 5, nearly free from `gap_rows.csv`) · `W3-LL3` ·
`W3-GN2` · `W3-IE3` · `W3-CR1` · `W4-FP4` · `W4-CS2` · `W4-IG2` · `W4-SH4` · `W5-ER3` · `W5-HY1` ·
`W5-TO2` · `W6-OC2` · `W6-FR2` · `W6-MA3` · `W7-CG3` · `W7-RA3` · `W8-CL2` · `W8-WE1` · `W8-RD2` · `W8-KC2`.

**Run order:** `W3-CA1` first (~free, plausibility 5). Then K3 gives the per-round count that the rest interpret.

**Decisive — and it has a *forward* test the whole batch shares:** if the wall is two-conditions-per-round,
then **sr=62 must cost `2^-4N`** (`W8-CL2`, `W8-RD2` state this explicitly). Measuring the sr=62 rate
tests the entire cluster's extrapolation in one shot, and adjudicates "linear continuation" vs any
"rate-cliff" reading. This is the batch's headline experiment.

---

## Batch C — "Is 0.74 the log of a spectral / growth / dimension quantity?"  ·  kernel K2

**Cards (≈20):** **`W1-DY1`** (`0.74 = log₂ λ_max` of a de58-low-rank transfer operator — HEADLINE) ·
`W1-PH3` · `W2-NT1` · `W2-SO3` · `W3-OT2` · `W3-GN1` (Ehrhart leading coeff; odd-N→0 = period 2) ·
`W3-IE1` · `W4-FP1` · `W4-IG5` · `W4-LG2` · `W4-SH5` · `W5-ER2` · `W5-HC1` · `W5-HC4` · **`W6-FR1`**
(Moran equation from carry-branching ratios — HEADLINE) · `W6-MA2` · `W6-OM2` · `W7-QW2` · `W7-NS2` · `W8-RD1` · `W8-CL4`.

**Run order:** build the small-N differential transfer operator once (`W1-DY1`); then `W4-FP1`, `W7-QW2`,
`W4-SH5`, `W6-OM2` read off its spectrum, and `W6-FR1`/`W5-ER2`/`W6-MA2` are branching/tree counts on the
same carry graph. `W6-FR1` and `W1-DY1` are the two that predict 0.74 from *independently measured*
quantities — run both; agreement is the result.

**Decisive:** any *two* of these landing on 0.74 from different measured inputs ⇒ 0.74 is structural, not fitted.

---

## Batch D — "Why round 60 specifically?"  ·  kernel K1 + a per-round sweep harness

A scalar structural quantity computed per round 50…63; look for the discontinuity at 60→61.

**Cards (≈22):** `W1-PH2` · **`W2-CT2`** (controllability-rank collapse — HEADLINE) · `W2-RG1` · `W2-QI1` ·
`W2-QI4` · **`W2-PC1`** (boundary-expansion jump → resolution bound firing at 61 not 59 — HEADLINE) ·
`W2-PC4` · `W3-CR3` · `W4-LG1` · `W4-SH4` · `W5-KR1`/`W5-KR3` · `W5-HY1`/`W5-HY4` · `W5-TO1` · `W6-OC1` ·
`W6-OC4` · `W6-OM1` · `W6-OM3` (NIP→IP) · `W6-MA4` · `W7-CG2` · **`W7-FC2`** (concept-count explosion) ·
`W7-FC3` · `W7-QW1`/`W7-QW5` · `W8-WE2`.

**Run order:** `W2-CT2` and `W2-PC1` first (both on K1 / the dependency graph). Same sweep harness, one
quantity per card — cheap to add cards once the harness exists.

**Decisive:** the win is *convergence* — if ≥2 unrelated quantities (rank-collapse, expansion-jump,
concept-explosion, …) all step at the **same** round, "why 60" stops being a coincidence.

---

## Batch E — "Why does only de58 grow?"  ·  kernel K4

**Cards (≈16):** `W2-NT3` (Weyl / SHR10 lacunary) · `W2-QI3` (monogamy) · `W3-CA2` (delta-lens fibre) ·
**`W3-IE2`** (unique-ergodicity — HEADLINE) · `W4-FP5` · `W4-LG3` (the one charged column) · `W4-CS3`
(collider d-separation) · `W5-KR2` (cyclic-group order = power-of-2 image) · `W5-HC5` (single petal) ·
`W6-OM4` (the unique 1-cell) · `W6-FR3` (set-renormalization) · `W7-CG1` (the one live nim-heap) ·
`W7-FC4` (low-stability coordinate) · `W7-QW5` (step at r=58) · `W8-CL3` (TNN positive coordinate) · `W8-KC2` (the one floppy mode).

**Run order:** these are *interpretations of the same K4 table* — build K4 once, then each card is a
labelling of why `de58` is singular. Cheapest unit in the catalog: one measurement, sixteen readings.

**Decisive:** K4 already half-exists in the repo memory (`|de58|=2^10`, others constant) — the open part is
*which* of the 16 mechanisms predicts the **growth law** `|de58|(N)`, not just the constancy of the others.

---

## Batch F — standalone (own kernel; run solo, high-value)

Not batchable — each needs its own small build, but each is individually worth it:

- **`W1-IN2`** — XOR/ADD uncertainty principle. **Cheapest probe in the catalog** (`[P4 · trivial]`): a pure
  support-product bound `support_⊕ · support_+ ≥ 2^{cn}`. A provable "no basis is sparse" barrier. Do this first, anywhere.
- **`W2-PC5`** — Tseitin linearization-survival. *The clean experiment*: linearize the CNF and test whether
  the obstruction is graph-expansion vs carries. Directly tests the repo's "0-slack geometry, not carry-length" finding.
- **`W1-GE5`** — Ollivier–Ricci "slack atlas." **Testable today** against the 67-candidate table the old
  predictors failed — it has a ready validation set, unlike everything else.
- **`W3-LL2`** — Moser–Tardos resampling. Distinctive: a *constructive* collision-finder (not a "why-wall"
  result) that should provably diverge at 61 — the one card that could output a pair, not just a theorem.

---

## TL;DR for a coordinator

1. Build **K1** → run **Batch A** (`W6-MA1` is nearly free now). *Is 132 a corank?* — the flagship hit/miss.
2. Build **K3** → run **Batch B**; its forward test is **measure the sr=62 rate** (predicted `2^-4N`).
3. Build **K2** → run **Batch C** (`W1-DY1` + `W6-FR1` agreement = 0.74 is structural).
4. **K4** is half-done → **Batch E** is sixteen readings of one table; chase the `|de58|(N)` growth law.
5. Fire **`W1-IN2`** (trivial) and **`W1-GE5`** (has a ready validation set) in parallel from the start.

A confirmed corank=132 (A) **and** a measured sr=62=`2^-4N` (B) would, together, convert the bulk of the
catalog from "convergent conjecture" into "two anchored data-points with ~40 consistent narrations."
