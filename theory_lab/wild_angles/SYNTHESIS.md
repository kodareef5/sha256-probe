# Synthesis — what ~99 independent reframings actually agree on

> ⚠️ **SUPERSEDED BY EXECUTION — read [`probes/FINDINGS.md`](probes/FINDINGS.md) first.** All 185 cards were
> later RUN as small-N probes. The convergence claimed below did **not** survive computation: of the "four
> numbers," only **`2^-2N` = two independent conditions** is real (confirmed ~12 ways, extended to
> `sr=62=2^-4N`). The **`132`-as-corank** convergence is a **category error** (every honest corank is 0/128;
> "132" is the width-scaling 4N+4 control census — refuted ~20×), and **`0.74` is not a sharp/derivable
> constant** (~0.673, scatter 0.6–1.0; every derivation failed). The triangulation was an artifact of
> *un-run reasoning*. This document is kept as the pre-execution hypothesis; FINDINGS.md is the verdict.

We generated ~99 wild reframings of the SHA-256 collision problem across 4 waves (24 territories, the
standard cryptanalysis toolkit banned each wave). **The individual cards are the distributable workloads;
this document is the result.** And the result is not any single angle — it is the *triangulation*: a
large number of mutually-unaware formalisms converge on the **same four numbers**, and several converge on
the *same explanation* of the same number. When fields that share no vocabulary keep landing on one
structure, the structure is real.

> Honest scope: most of these most plausibly yield a rigorous **"why the ~60-round wall exists"** result,
> not a finished collision. Many are plausibility-2 and flagged numerology-prone in their own cards. The
> value is (a) the convergence below, and (b) the cheap-probe portfolio in §3 that turns it testable.

> **Wave-5 update (counts below are pre-wave-5; the convergence only strengthened).** The `2^-2N`-from-two-conditions
> cluster gained: `W5-HY1` (CAT(0) empty-square, **codimension 2**), `W5-TO2` (Heyting-meet
> `μ(U_A)·μ(U_B)`, *anchored to the repo's own 1.005 ratio*), `W5-CO3` (up-to-context unsoundness),
> `W5-KR1` (group-complexity +1) — now ~18 lenses. The 132-as-corank/structural cluster gained `W5-HC2`
> (sunflower core = the measured 42% carry-invariance), `W5-ER1` (high-resistance recompute-registers — a
> *named* set), `W5-KR2` (de58 holonomy = power-of-2 order). "Why-60" gained `W5-KR3` (a clean
> aperiodicity/star-free→group flip, decidable & cheap) and `W5-TO1`/`W5-HY1`. The picture didn't dilute
> with breadth — it sharpened.

> **Wave-6 update — the corank cluster is now EIGHT-fold and nearly runnable.** `W6-MA1` (matroid corank),
> `W6-OC3` (Pontryagin costate kernel) join control-cokernel / rigidity-self-stress / Fisher-kernel /
> free-prob-zero-atom / sheaf-H¹ / causal-do-orphans: **eight independent formalisms predict the 132 hard-core
> bits as the corank/kernel of one linear map.** Crucially, `W6-MA1` is *nearly free to run*: the repo already
> has the GF(2) engine `gf2_eliminate` + a half-built constraint matroid (rank 96, 416 free), the 132 is
> currently only a "CDCL-search artifact," and a matroid-corank audit is **on the repo's own wishlist.** Also:
> `2^-2N` gained `W6-OC2` (singular-surface codim-2), `W6-OM3` (NIP→IP: "two independent conditions" IS the
> independence property), `W6-FR2` (open-set-condition overlap), `W6-MA3` (cocircuit rank 1→2). `0.74` gained
> `W6-FR1` (Moran equation from carry-branching ratios — and the repo's existing O(1.69^N)=2^0.756N enumerator
> matches), `W6-OM2` (Pila–Wilkie algebraic-locus dimension), `W6-MA2` (Tutte/Greene growth rate).

> **Wave-7 update — the corank cluster is now TEN-fold; healthy negative space appearing.** The 132-as-corank
> cluster gained `W7-FC1` (concept-lattice meet-irreducibles, with the exact bit-prediction {da,db,de,df}) and
> `W7-QW3` (Szegedy discriminant kernel) — **ten** independent formalisms. `2^-2N` gained `W7-FC2` (concept-count
> explosion from the two *independent* sr=61 attributes), `W7-CG3` (P/N-position measure, +a testable sr=62→2^-3N
> prediction), `W7-RA3` (regularity density-increment), `W7-NS3` (internal/external: "two conditions" = the model-
> theoretic independence property). `0.74` gained `W7-QW2`/`W7-NS2`. **Equally valuable: wave 7 surfaced honest
> negative space** — the nonstandard-analysis agent showed its whole territory's only falsifiable content is the
> internal-vs-external N-uniformity test (most of its cards "likely inert / a relabel of 2^-2N"); the Ramsey agent
> flagged that SHA's tiny dimensions sit far below any real Ramsey threshold. That the falsifiability bar keeps
> killing weak cards is the system working — the convergence survivors are the signal.

> **Wave-8 update — the corank cluster is ~13-fold, and breadth has saturated.** New 132-as-corank/frozen-core
> entrants: `W8-RD3` (IB minimal-sufficient-statistic), `W8-KC1` (active-difference 2-core), `W8-KC3` (frozen
> variables — the repo's *already-measured* 132-universal set IS the textbook definition of frozen). New `2^-2N`
> derivations: `W8-CL2` (c-vector rank-2, predicting sr=62→2^-4N), `W8-WE1` (Weihrauch parallel-product),
> `W8-RD2` (a +2N rate cliff, also sr=62→4N), `W8-KC2` (2 surplus isostatic contacts). New `0.74`: `W8-RD1`
> (R(0)), `W8-CL4` (cluster-complex growth). **But wave 8 is also where breadth visibly saturated:** the
> computability agent itself noted its ideas are "the same integer three ways"; rate-distortion's `W8-RD2` and
> k-core's `W8-KC2` *re-derive* `2^-2N` rather than add; the agents increasingly re-narrate the known constants
> in new vocabulary. **The catalog is comprehensive; the convergence is overwhelmingly established (~13 lenses on
> 132, ~20+ on `2^-2N`, ~10 on `0.74`). The marginal new content per territory has gone to near-zero — the
> productive move is no longer breadth but running the corank probe (§3).**

---

## 1. The convergence map

### `2^-2N` (the per-round floor) — derived, not fitted, by ~14 lenses
And — the deeper point — **every one pins the "2" to the same two independent conditions** the repo
already measured (`g1=0 AND h=0`, ratio 1.005). The formalisms are different *languages for the same fact*:

| card | lens | what the "2" IS |
|---|---|---|
| `W3-CA1` | bidirectional lenses | the two broken laws **PutGet (=g1)** and **PutPut (=h)** |
| `W1-PH1` | instanton | two independent **zero modes** |
| `W2-RG1` | rigidity | **codimension-2** over-constraint per round past isostatic |
| `W2-NT4` | singular series | a **double-order zero** (two local densities ×2^-N) |
| `W2-PC2` | polynomial calculus | PC-degree **slope-2** (two independent generators/round) |
| `W2-CT4` | control (LQR) | appended-constraint **corank 2N** |
| `W3-LL3` | Lovász local lemma | a **squared vertex weight** (p→p²) flipping Shearer's Z |
| `W3-GN2` | geometry of numbers | covolume **quadruples** per round (Minkowski) |
| `W3-IE3` | Rauzy renormalization | **two interval endpoints** must coincide |
| `W3-CR1` | reaction-network | **deficiency δ=2** |
| `W4-FP4` | free probability | **two free** (independent) spectral constraints, each one unit |
| `W4-SH4` | sheaf Laplacian | a **rank-2** spectral-gap degeneration at 60→61 |
| `W4-CS2` | causal/IV | an **order-deficit of 2** (two targets, rank-1 instruments) |
| `W4-IG2` | Fisher information | a **block-diagonal** 2×2 Fisher det (zero cross-information) |

That ~14 disjoint formalisms independently produce a *2* — and locate it in the *same* two conditions —
is the single strongest signal in the whole corpus.

### `2^0.74N` (the collision-count growth) — derived by ~9
`W1-DY1` transfer-operator top eigenvalue · `W1-PH3` path-integral saddle determinant · `W2-NT1`
singular-series main term · `W2-SO3` SOC avalanche exponent · `W3-OT2` Sinkhorn coupling entropy ·
`W3-GN1` Ehrhart leading coefficient · `W3-IE1` KZ Lyapunov exponent · `W4-FP1` ⊠-product top
singular-edge · `W4-SH5`/`W4-LG2` graded-kernel / plaquette-tiling growth rate.

### "Why round ~60" (the wall location) — explained by ~12
`W1-PH2` RG eigenvalue→1 · `W2-CT2` controllability rank-collapse · `W2-RG1` isostatic point ·
`W2-QI1` magic saturation · `W2-QI4` stabilizer-rank · `W2-PC1` boundary-expansion width-jump ·
`W2-PC4` definability/locality blow-up · `W3-IE3` Rauzy fixed point · `W3-GN2` Minkowski covolume
crossing · `W3-CR3` irreducibility cliff · `W4-LG1` confinement transition · `W4-SH4` gap collapse.

### The 132 hard-core bits / HW~74 plateau — explained by ~13
`W1-GE3` Morse-Bott index · `W1-GE4` Euler-cocycle support · `W2-CT1` controllability cokernel ·
`W2-RG2` rigidity self-stress dim · `W2-NT2` Weil-cancelling subspace · `W2-SO4` Turing-unstable band ·
`W2-SO1`/`W2-SO2` neutral-net min-cut / quasispecies threshold · `W3-CA3` abstract-interp ⊤-set ·
`W3-GN3` zonotope degeneracy · `W3-OT4` Nash locked-bits · `W4-IG1` Fisher-metric kernel ·
`W4-FP2` ⊠ zero-atom · `W4-SH2` sheaf H¹ dim · `W4-CS1`/`W4-CS4` do-orphans / counterfactually-rigid set ·
`W4-LG4` vortex-pierced plaquettes. **Six of these say the literal same thing:** 132 is the *corank /
kernel-dimension* of one linear map (control cokernel, rigidity self-stress, Fisher kernel, ⊠ zero-atom,
sheaf H¹, do-orphan severed-paths). If a rank computation returns ~132, many cards confirm at once.

### "de58 grows, de57/59/60 constant" — explained by ~6
`W2-NT3` Weyl lacunary (SHR10) · `W2-QI3` monogamy slack localization · `W3-CA2` delta-lens lone generator ·
`W3-IE2` unique-ergodicity · `W4-FP5` free-subordination mobile coordinate · `W4-LG3` Gauss-law charged column.

---

## 2. The two deep "same-thing-in-different-words" clusters

1. **The 132 is a corank.** Control (CT1), rigidity (RG2), information geometry (IG1), free probability
   (FP2), sheaf theory (SH2), and causal inference (CS1) each predict the 132 hard-core bits as the
   *kernel/cokernel/self-stress/zero-atom/H¹/severed-path dimension of one linear operator*. They disagree
   only on which operator — and several of those operators are the **same matrix** (see §3).
2. **The `2^-2N` is two independent constraints.** The 14 cards above. The lens-law card (`W3-CA1`) is the
   sharpest because it *names* the two: PutGet and PutPut, the two laws a "very-well-behaved lens" must
   satisfy — and the repo's own `g1`/`h` split is exactly that pair, already measured.

These two clusters are the falsifiable heart. If a single rank computation returns ≈132, and a single
two-vs-one rank-deficit returns the factor 2, a dozen cards are confirmed together.

---

## 3. The bridge from ideas to datapoints — ONE artifact tests ~30 of them

A striking fraction of all probes reduce to building **one object**: the finite-difference **GF(2)
linearization of the masked round map** — per-round Jacobians `A_i` (state→state), `B_i` (message→state),
and the feed-forward `C`. From that single ~150-line build (`assemble_jacobians(N, last_round)` over
`lib/sha256.py`, no SAT):

- **corank queries → 132:** `W2-CT1` (controllability cokernel), `W2-RG2` (self-stress), `W4-IG1`
  (Fisher kernel), `W4-FP2` (⊠ zero-atom), `W4-SH2` (sheaf H¹), `W4-CS1` (do-orphans). *Six formalisms,
  one number, one build.*
- **rank-collapse / gap → why-60:** `W2-CT2` (reachability rank vs round), `W4-SH4` (λ₁ collapse, rank-2).
- **product-spectrum → 0.74:** `W1-DY1` (transfer operator), `W4-FP1` (⊠ top edge), `W4-SH1` (sheaf ker count).
- **the factor-2 → 2^-2N:** `W2-CT4` (appended-constraint corank), `W4-CS2` (IV rank-deficit), `W4-SH4`.

**Recommended first sprint (highest signal/effort):** build the GF(2) Jacobian kernel once; compute its
relevant coranks; ask *"is the hard-core 132 a corank?"* from all six formalisms at once. If they agree
(and agree with the brute-force small-N hard-core set), that is a real, publishable structural result —
"the 132 hard-core bits are the cokernel of the linearized difference map," with six independent
derivations. If they disagree, you've falsified six cards in one run. Either outcome is worth far more than
card #100.

Cards needing a *different* cheap kernel: the Wilson-loop ensemble (`W4-LG*`, bit-serial carry extraction),
the neutral-network graph (`W2-SO1`), the LLL Monte-Carlo (`W3-LL*`), the Ehrhart count-fit (`W3-GN1`),
the lens-law violation curves (`W3-CA1`, *numbers already in the repo's `gap_rows.csv`* — nearly free).

---

## 4. What to ignore (honest negative space)

- **Anything plausibility-2 whose only hook is matching 0.74:** `W2-NT5`, `W3-IE5`, `W3-LL4`, `W4-LG2`,
  `W4-IG5` — with enough free parameters *some* construct hits 0.74; only an *out-of-sample* prediction
  (a new N, a new exponent like sr=62 → 2^-3N) counts. Treat single-number matches as suggestive at most.
- **The `de58` "lone coordinate" cluster** is over-explained (6 cards) and partly tautological — three of
  four difference-equations are linear-determined, so "1 grows" is half-expected. Demand the *growth-rate*
  match (|de58|~2^10 at N=32), not just the 1-of-4 selection.
- **Free-probability and Fisher both rest on a fragile premise** (asymptotic freeness needs large random
  dimension; Fisher needs a distribution from injected randomness). Their kill-criteria all demand
  *convergence as N grows*, not agreement at one small N. Don't trust a single-N hit.

---

## 5. One-paragraph takeaway

Across 24 unrelated mathematical territories, the SHA-256 collision wall keeps resolving into the *same*
small set of structural facts: a **corank-132 linear obstruction** (the hard-core bits), a **two-condition
codimension** (the `2^-2N` floor, and the "2" is provably the two lens-laws / two zero-modes / rank-2
gap), a **product-spectrum edge** (the `0.74` growth), and a **round-60 rank/gap/expansion collapse** (the
boundary). The most actionable consequence: **one GF(2) round-Jacobian build tests whether 132 is a corank
from six formalisms at once** — the cheapest high-value experiment in the whole catalog, and the natural
first hand-off when these workloads are distributed.
