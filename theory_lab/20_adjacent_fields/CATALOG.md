# Adjacent-field catalog — one-line tags

The fields prospected as fresh lenses on the SHA-256 collision problem, ranked by
(plausibility of a real foothold) × (cheapness to probe). This is the navigation layer; the
canonical record is `../30_register/ideas.yaml`. A field becomes a **register row** only once a
concrete reframe + a falsifiable kill-criterion is articulated; until then it lives as a **stub** in
`fields/`. The recurring killer across the dead tier: SHA-256 collision-finding is *construction
under a rigid constraint*, while most imported tools *count, distinguish, or bound worst-case* — they
characterize the wall beautifully and breach it not at all.

## The spine (top 3 — they cross-feed)

Put a **metric / algebraic invariant on the carry obstruction** and attack *that*, instead of
enumerating messages. #1 produces the additive invariant, #3 is its solver, #2 bounds the sparsity
both depend on.

| # | Field / lens | What it could reframe | novelty | probe | lives at |
|---|---|---|---|---|---|
| 1 | **2-adic analysis / FCSR span** (number-theory-padic) | carries as a 2-adic *metric*; `v2(ΔH)` growth = additive form of `2^-2N` | genuinely-new | cheap | `register:2adic-carry-valuation-newton` + `dive` |
| 2 | **Coding theory** of the message-expansion code | min-distance bound = static sparsity budget; the 60-round wall as a (conditional) theorem | flagged-unpursued | cheap | `register:expansion-code-min-distance` + `dive` |
| 3 | **Lattice** (carry-lifted LLL/BKZ) | schedule compliance = "does a lattice coset hold a 0/1-carry vector" | genuinely-new | cheap | `register:carry-lifted-lattice` + `dive` |

## Worth a cheap probe (lower expectation)

| Field / lens | What it could reframe | novelty | probe | lives at |
|---|---|---|---|---|
| **Statistical physics** (survey propagation) | is the residual glassy/clustered or UNSAT-dense? SP-decimation heuristic | adjacent-untested | cheap | `register:survey-propagation-factor-graph` |
| **Walsh / cLAT** (boolean-function) | correlation oracle to prune trails before SAT (Wallén) | flagged-unpursued | cheap | `register:walsh-clat-pre-sat-oracle` |

## On deck (stubs — need a concrete reframe + kill-criterion to become register rows)

| Field / lens | Candidate reframe | novelty | stub |
|---|---|---|---|
| **Commutative algebra** (Gröbner/F4, σ-aligned order) | compute the collision ideal's basis to expose hidden low-degree relations (da=de is one found by hand) | flagged-unpursued | `fields/field_commutative_algebra_grobner.md` |
| **Persistent homology / TDA** (graph-spectral) | topology of the W-witness / HW landscape — find regions the sampler misses | adjacent-untested | `fields/field_persistent_homology.md` |
| **Spectral graph theory** | eigenvalues of the round-state dependency graph as a structural invariant | adjacent-untested | `fields/field_graph_spectral.md` |

## Parked — dead-for-construction (one-line kill reason; cf. register rows)

| Field / lens | Why parked | lives at |
|---|---|---|
| Algebraic geometry / variety | = Gröbner over GF(2), astronomically high degree, no usable smoothness/genus | `register:algebraic-geometry-variety` |
| Additive combinatorics | counts structure / proves existence-of-many; can't exhibit ONE collision under rigid constraint | `register:additive-combinatorics-sumset` |
| Tropical (min/max-plus) | bounds carry-chain *length* (latency), not existence | `register:tropical-carry-maxchain` |
| Quantum / Grover | only √ over the *residual*; zero classical progress; no HW in scope | `register:quantum-grover-residual` |
| Tensor networks / MPS | **repo-killed**: corpus high-rank, bond dim scales linearly, MPS loses to naive | `register:cascade-corpus-mps-hostile` |
| Dynamical systems / ergodic | the rigorous version *is* Anashin's 2-adic ergodic theory → subsumed by #1 | folded into `register:2adic-carry-valuation-newton` |
| Representation theory on (Z/2^n,+) | irreducible characters *are* the Walsh basis → collapses to the cLAT angle | folded into `register:walsh-clat-pre-sat-oracle` |

See `../10_community_scan/landscape.md` for the mainstream (non-adjacent) frontier these are measured against.
