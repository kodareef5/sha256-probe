# Wild angles — a growing, distributable catalog of SHA-256 reframings

This is the "wilder ideas" wing of the theory lab: structural reframings of the SHA-256 collision
problem generated in **waves** of divergent ideation (the standard cryptanalysis toolkit banned each
wave). Full cards live in [`CATALOG.md`](CATALOG.md); this file is the navigator.

> 🔬 **The cards were RUN — read [`probes/FINDINGS.md`](probes/FINDINGS.md) for the empirical verdict.**
> 185/185 probed (small-N, read-only, no SAT): **11 CONFIRMED (all `2^-2N`), 25 renames, 147 KILLED**. The
> catalog's convergence did **not** survive computation — only `2^-2N` (two independent conditions) is real;
> `132`-as-corank is a category error and `0.74` is non-sharp. Everything below is the *pre-execution* map.

> **Generation is closed at wave 8** (185 cards; breadth saturated — see [SYNTHESIS.md](SYNTHESIS.md)).
> Three reading orders: **[SYNTHESIS.md](SYNTHESIS.md)** = what they converge on (the result) ·
> this file = browse by what each card derives · **[DISTRIBUTION.md](DISTRIBUTION.md)** = hand the
> catalog to a fleet, batched by the shared artifact each group needs built once.

**Each card is a self-contained research workload** you can hand to an agent:
- the **probe** is the first task (the smallest small-N computation that decides it, reusing `../../sha256_review/lib/sha256.py` — no SAT),
- the **kill_criterion** is the stop condition,
- the **"why NOT a rebrand"** line guarantees it isn't a renamed dead end.

Honest framing: most of these most plausibly yield a rigorous **"why the ~60-round wall exists"**
result, not a finished collision. That's the prize for a theory lab — and the striking thing is how
many *independent* lenses **triangulate the same four numbers**.

---

## The convergence (why this isn't noise)

Unrelated fields keep landing on the same structural facts. That mutual triangulation is the
strongest signal here:

- **"Why round ~60?"** is independently predicted by **~10** lenses: RG eigenvalue-crossing
  (`W1-PH2`), control rank-collapse (`W2-CT2`), rigidity isostatic point (`W2-RG1`), magic-saturation
  (`W2-QI1`), stabilizer-rank (`W2-QI4`), expansion-width (`W2-PC1`), definability-jump (`W2-PC4`),
  Rauzy fixed point (`W3-IE3`), Minkowski covolume-crossing (`W3-GN2`), irreducibility cliff (`W3-CR3`).
- **The `2^-2N` floor** is *derived* (not fitted) by **~10**: zero-mode count (`W1-PH1`), LQR corank
  (`W2-CT4`), Maxwell codim-2 (`W2-RG1`), singular-series double-zero (`W2-NT4`), PC-degree slope-2
  (`W2-PC2`), **lens-law breakage** (`W3-CA1`), LLL squared-weight (`W3-LL3`), covolume quadrupling
  (`W3-GN2`), Rauzy two-endpoint (`W3-IE3`), CRN deficiency δ=2 (`W3-CR1`). All pin the **"2"** to the
  repo's own *two independent conditions* `g1=0 AND h=0` — and `W3-CA1` shows those two ARE the two
  broken lens laws (PutGet, PutPut).
- **The `2^0.74N` growth** is *derived* by **~7**: transfer-operator eigenvalue (`W1-DY1`), path-integral
  saddle (`W1-PH3`), singular-series main term (`W2-NT1`), SOC avalanche exponent (`W2-SO3`), Sinkhorn
  coupling entropy (`W3-OT2`), Ehrhart leading coeff (`W3-GN1`), KZ Lyapunov exponent (`W3-IE1`).
- **The 132 hard-core bits / HW~74 plateau** gets a mechanism from **~10** angles: Morse index, control
  cokernel, rigidity self-stress, Weil subspace, Turing band, neutral-net min-cut, quasispecies
  threshold, Galois precision-loss (`W3-CA3`), zonotope degeneracy (`W3-GN3`), Nash locked-bits (`W3-OT4`).

If even two unrelated probes confirm the same crossing, that's a real result.

---

## Navigator — by what each angle would DERIVE or EXPLAIN

★ = cheapest / highest-leverage probe in its group.

### Derive the `2^-2N` floor
| card | the mechanism |
|---|---|
| `W1-PH1` | floor = count of independent zero modes (2 per round) |
| `W2-CT4` ★ | appending the two sr-conditions adds corank `2N` per round |
| `W2-RG1` | each round past isostatic adds 2 constraints (codim-2) |
| `W2-NT4` | singular series with a double-order zero (two local densities ×2^-N) |
| `W2-PC2` | polynomial-calculus degree grows slope-2 per held round |

### Derive the `2^0.74N` growth
| card | the mechanism |
|---|---|
| `W1-DY1` ★ | `0.74 = log₂ λ_max` of a (de58-low-rank!) transfer operator — also a poss. poly-time counter |
| `W1-PH3` | saddle-point fluctuation determinant of a carry path-integral |
| `W2-NT1` | circle-method main term = product of per-round survival fractions |
| `W2-SO3` | a self-organized-criticality avalanche exponent |

### Explain "why round ~60"
| card | the mechanism |
|---|---|
| `W2-CT2` ★ | controllability rank drops below "enough to zero δH"; rotation-constant-dependent |
| `W2-PC1` ★ | constraint hypergraph's boundary expansion jumps (Hall deficit) at 61 |
| `W2-QI1` | cumulative non-Clifford "magic" saturates the free-bit budget |
| `W1-PH2`,`W2-RG1`,`W2-QI4`,`W2-PC4` | RG eigenvalue→1 · isostatic point · stabilizer-rank · locality-radius blow-up |

### Explain the 132 hard-core bits / HW~74 plateau
| card | the mechanism |
|---|---|
| `W2-CT1` ★ | the uncontrollable subspace (cokernel of the reachability matrix) — with a named basis |
| `W2-RG2` ★ | the states-of-self-stress dimension of the rigidity matrix |
| `W1-GE3` | the index of a Morse-Bott degenerate critical manifold (132 = Hessian kernel) |
| `W2-SO1`,`W2-SO2` | a neutral-network min-cut · a quasispecies error threshold |
| `W1-GE4`,`W2-NT2`,`W2-SO4` | Euler-cocycle support · Weil-cancelling subspace · Turing-unstable band |

### A provable BARRIER ("why it's hard, period")
| card | the mechanism |
|---|---|
| `W1-IN2` ★ | XOR/ADD uncertainty: no basis is sparse — `support_⊕ · support_+ ≥ 2^cn` |
| `W2-PC5` ★ | strip nonlinearity: the surviving Tseitin-graph expansion is the obstruction |
| `W1-GE1` | Čech/contextuality: locally satisfiable, globally a nonzero cohomology class |
| `W2-PC3`,`W1-IN5` | feasible-interpolation circuit bound · communication-complexity lower bound |

### A genuinely new computational OBJECT / tool
| card | what's new |
|---|---|
| `W1-GE5` ★ | Ollivier-Ricci "slack atlas" — testable *today* vs the 67-candidate table the old predictors failed |
| `W1-DY1` | a Ruelle dynamical zeta whose zeros encode collision rates |
| `W1-IN1`,`W2-CT5` | quotient out the bijection → one coincidence-map · a Kalman observer that peels off determined bits |

### Explain "de58 grows, de57/59/60 constant"
`W2-NT3` (Weyl equidistribution — SHR10 is lacunary) · `W2-QI3` (monogamy forces all slack into one channel).

---

## Waves (territories mined)

- **Wave 1** (20): physics/field-theory · geometry/topology/obstruction · dynamical-systems/spectral · computation/information/algebra.
- **Wave 2** (27): control & signal · rigidity & constraint-geometry · circle-method & arithmetic · quantum stabilizer/magic · proof & descriptive complexity · self-organization & fitness-landscapes.
- **Wave 3** (29): optimal-transport & games · category/optics/PL-semantics · geometry-of-numbers & Ehrhart · probabilistic-method/LLL · interval-exchange & Teichmüller · reaction-networks & computational-irreducibility.
- **Wave 4** (23): information-geometry/Fisher · free-probability/S-transform · lattice-gauge/Wilson-loops · cellular-sheaf-Laplacian · causal-structural-models.
- **Wave 5** (29): Krohn–Rhodes automata · coalgebra/bisimulation · effective-resistance · hypergraph-containers/sunflowers · CAT(0)/systolic · topos/forcing.
- **Wave 6** (19): Pontryagin optimal-control · o-minimality/tame-geometry · matroid/Tutte · IFS/fractal-dimension.
- **Wave 7** (25): combinatorial-game-theory · Ramsey/density · formal-concept-analysis · quantum-walks/Szegedy · nonstandard-analysis.
- **Wave 8** (13): cluster-algebras · computability/Weihrauch · k-core/jamming · rate-distortion. _(saturation — late territories re-derive the constants more than they add)_

~185 cards across 8 waves. **→ [SYNTHESIS.md](SYNTHESIS.md): what they all converge on — the headline result.** Many share **one cheap kernel** — a finite-difference GF(2) linearization of
the masked round map (per-round `A_i`, `B_i`, `C`) — after which CT1/CT2/CT4/CT5/RG1/RG2/PC5 are all
one-line rank queries. That's the obvious first build for a distributed sprint.

## How to run a sprint
**See [DISTRIBUTION.md](DISTRIBUTION.md)** — it batches the 185 cards by the shared artifact each group
needs (build one GF(2) Jacobian → ~15 corank cards; one transfer operator → ~20 "0.74" cards; …), with a
run-order and the two highest-information experiments (is 132 a corank? · measure the sr=62 rate). In short:
1. Build a shared **kernel** (K1–K4 in DISTRIBUTION); the cards in its batch become near-free queries.
2. Run the batch's ★/flagship card first; the probe is the task, the kill_criterion the stop.
3. Two independent probes confirming the same crossing/number ⇒ promote to a repo bet
   (`../50_meta/LIFECYCLE.md`); a clean negative ⇒ archive with the reason.
