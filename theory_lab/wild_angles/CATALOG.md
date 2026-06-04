# Wild-angle catalog — workload-ready reframings of the SHA-256 collision problem

Each card is a **self-contained research workload**: a structural reframe + the cheapest small-N
probe that decides it + a kill-criterion. Hand any card to an agent. Generated in waves of divergent
ideation (standard cryptanalysis toolkit banned). Honest framing: most of these most plausibly yield a
rigorous *"why the ~60-round wall exists"* result, not a finished collision — and several **derive**
the repo's empirical constants (the `2^-2N` floor, the `2^0.74N` growth, the `132` hard-core bits,
"why round 60") from a principle, which is the prize.

Plausibility is honest 1–5 (5 = near-certain to *say something*, even a clean negative). Probe cost:
trivial / cheap (small-N Python reusing `../../sha256_review/lib/sha256.py`) / moderate.

---

# WAVE 1 — physics · geometry · dynamics · information (2026-06-03)

## Physics & field theory

### W1-PH1 · Instanton zero-mode count → derives `2^-2N`  `[P4 · cheap]`
- **one_liner:** Each held schedule round adds two independent "zero modes" (g1, h); the rare-event rate is Π2^-N = 2^-2N, derived not fitted.
- **lens** field-theory/large-deviation · **locus** differential-trail, state-cross-section · **mechanism** lower-bound
- **analogy:** The sr=60 survivor ensemble is a thermodynamic system; a held expansion equation is a constraint that must vanish, and the repo's own factorization shows it splits into two independent scalar conditions = two collective coordinates / zero modes. A rare event with k independent N-bit zero modes costs 2^-kN. So `2` in `2^-2N` = mode count, and the **per-round** multiplication = additivity of the action over independent modes.
- **reframes:** "we measured ratio 1.005" → "exponent = rank of the constraint factorization," predicting a candidate's exponent before measuring.
- **probe:** Reuse the sr=60 enumerator at N=8; for each held round decompose its constraint into scalar factors, measure the entropy-deficit rank; predicted exponent = rank·N; check stacked sr=61/62 rates = 2^-2kN.
- **kill:** Dead if per-round rank isn't a stable integer across candidates, or stacking two rounds ≠ (single-round rate)².
- **skeptic:** May just restate "two independent uniform conditions" with no new predictive content unless rank predicts a *new* candidate's exponent.
- **not a rebrand of:** cascade-DP — it treats the *already-enumerated* ensemble as a statistical field and extracts an action exponent; the DP is the data source, not the method.

### W1-PH2 · RG fixed point → explains "why round 60"  `[P3 · cheap]`
- **one_liner:** The 64-round iteration is an RG flow; the boundary is where the controllable difference-operator turns irrelevant (eigenvalue crosses 1).
- **lens** renormalization-group · **locus** round-function→whole-function · **mechanism** structural-invariant
- **analogy:** Coarse-grain the difference distribution; the cascade-controllable directions are "relevant" early, the 132 hard-core bits are "irrelevant." The boundary = the round where the largest eigenvalue of the linearized difference-propagation Jacobian crosses 1 — and that eigenvalue is set by the **exact rotation constants**, so the boundary location should be *computable*, not just observed.
- **reframes:** "Why 60?" → "where does the round-Jacobian's controllable-subspace eigenvalue cross 1?"
- **probe:** N=8,10,12: XOR-linearize one round on the difference state, form the per-round transfer matrix, track the still-controllable subspace dimension vs round; look for a knee near the boundary; permute the rotation constants to confirm the knee moves.
- **kill:** Dead if the controllable dimension decays smoothly (no knee), or if permuting rotations doesn't move the knee.
- **skeptic:** XOR-linearization may wash out the carry nonlinearity that *sets* the boundary.
- **not a rebrand of:** Walsh/linear — no correlation is computed; the object is control-dimension-vs-round and a knee location.

### W1-PH3 · Carry path-integral / stationary phase → derives `0.74`  `[P3 · cheap]`
- **one_liner:** Write collision count as a character-sum over carry-histories; the saddle's fluctuation determinant gives the 0.74N exponent.
- **lens** path-integral/stationary-phase · **locus** carries · **mechanism** count
- **analogy:** `1[Δ=0] = 2^-N Σ_t e^{2πi tΔ/2^N}` turns the count into a discrete path integral over carry-histories with a character "action"; rotation constants set which bits couple. Dominant contributions are stationary-phase carry-histories; the Gaussian (Hessian) fluctuation determinant yields ~2^{cN} with c claimed = 0.74.
- **reframes:** the fitted 0.74 → log₂(fluctuation determinant), and *which* carry positions dominate.
- **probe:** N=6,8,10: enumerate exact collisions AND compute the leading-saddle character-sum estimate from the carry-coupling matrix; compare slopes.
- **kill:** Dead if the saddle slope deviates from 0.74 beyond fit error, or no isolated stationary points exist (phase too flat).
- **skeptic:** carry chains are discrete; stationary phase (a continuum approx) may not dominate.
- **not a rebrand of:** 2-adic — Archimedean characters `e^{2πi/2^N}` + Hessian determinant, opposite metric; deliverable is one exponent from a saddle, not a sumset bound.

### W1-PH4 · Feed-forward as Jarzynski ratchet (localization sub-claim)  `[P2 · cheap]`
- **one_liner:** The non-invertible final add is the only entropy producer; a fluctuation-theorem bound converts its entropy production into a collision-rate floor.
- **lens** non-equilibrium-stat-mech · **locus** feed-forward · **mechanism** lower-bound
- **analogy:** P (64-round permutation) is a bijection → zero entropy production. The feed-forward `H_in+P` is the unique dissipative step, so ALL collision cost is localized there; Crooks/Jarzynski relate forward/reverse path ratios to e^Σ, with Σ_min (nats) claimed = 2N·ln2.
- **reframes:** locates the *entire* floor in one operation, separating "P (reversible, free)" from "feed-forward (the whole cost)."
- **probe (the cheap high-value yes/no):** N=8,10: measure the feed-forward-only difference-closure rate; **is it 2^-2N?** (i.e., is the floor born at the add, or distributed through P?). Verify P-without-final-add is rate-flat.
- **kill:** Dead if feed-forward-only closure rate ≠ 2^-2N (floor not localized at the add).
- **skeptic:** Jarzynski on a deterministic Boolean map may give a true-but-vacuous identity; the *localization* sub-claim is the part with teeth.
- **not a rebrand of:** MITM — never searches; asks where irreversibility is produced.

### W1-PH5 · Bragg / phase-matching → the N=10 interference  `[P2 · cheap]`
- **one_liner:** The schedule recurrence is a diffraction grating; the empirical N=10 constructive interference is a Bragg commensurability of the scaled rotations.
- **lens** optics/phase-matching · **locus** message-schedule · **mechanism** reframe
- **analogy:** taps (lags 2,7,15,16) = slits, rotation amounts = phase delays; collisions = bright fringes where modular path-differences cancel. At width N, certain scaled-rotation/N ratios become commensurate → a Bragg peak → predicts *specific* resonant N.
- **reframes:** "N=10 is special, empirically" → "N=10 satisfies a Bragg-commensurability"; predicts the next resonant N.
- **probe:** Compute scaled rotation sets {round(k·N/32)} for N=4..16, define a commensurability score, correlate with measured collision yield; must *predict* an unseen resonant N.
- **kill:** Dead if the score doesn't peak at N=10 or its predicted second resonance shows no yield anomaly.
- **skeptic:** with one data point (N=10) the score is easy to overfit post-hoc; only a correct *prediction* saves it.
- **not a rebrand of:** Walsh/spectral — the "phase" is the literal rotation-induced shift; prediction is a commensurate N, not a spectral bias.

## Geometry, topology & obstruction

### W1-GE1 · Čech / contextuality obstruction of the per-adder cover → the wall as a cohomology class  `[P4 · cheap]`
- **one_liner:** Every adder is locally satisfiable (proven) but they can't glue; the sr-wall is a nonzero Čech H¹, not a rarity.
- **lens** sheaf-cohomology/contextuality · **locus** carries (the 43 active adders) · **mechanism** lower-bound
- **analogy:** Adder = open set; its Lipmaa-Moriai-compatible carry patterns = its (nonempty) local sections; shared carry/bit between adders = the overlap + restriction map. A collision = a global section; sr=61 impossibility = Ȟ¹≠0. Carries ARE a gluing phenomenon (carry-out of bit k = carry-in of bit k+1 = a literal restriction map), so contextuality ("locally consistent, globally inconsistent") is the exact frame.
- **reframes:** the central paradox "each round satisfiable, the whole isn't" from a *rarity* (2^-2N) to a *qualitative invariant* (a specific nonzero class), and names *which adders* carry the obstruction.
- **probe:** N=4/5: enumerate each adder's LM-compatible local carry patterns; build the overlap nerve by shared carry-variable; compute Ȟ⁰/Ȟ¹ over Z/2 (boundary-matrix rank). Predict: collision-N ⇒ cocycle is a coboundary; wall-N ⇒ class ≠ 0.
- **kill:** Dead if the class is nonzero where collisions provably exist or vanishes at a no-collision N.
- **skeptic:** Čech H¹ of a *tree* nerve is always 0 — must first verify the carry-overlap nerve has loops (rotations should create them).
- **not a rebrand of:** algebraic-geometry variety — that studied the *global* zero-locus's dimension; this studies the *overlaps* and the failure of local sections to be compatible (an H¹ phenomenon invisible to the variety's dimension).

### W1-GE2 · Holonomy / winding around the W57 circle → an existence *certificate*  `[P3 · cheap]`
- **one_liner:** The residual is 1-D in W57 (a circle); transport a difference around it — nonzero winding number forces a zero-crossing = a guaranteed collision.
- **lens** differential-geometry/degree-theory · **locus** message-schedule (W57 circle) · **mechanism** solve
- **analogy:** Each tail round = parallel transport of the difference fiber (da..dh) over the W57-circle base; the feed-forward add = the curvature/twist; the residual the repo calls de58/D61 = the holonomy. A collision = a W57 where holonomy integrates to 0. If the holonomy 1-form has nonzero **winding** around the circle, a zero is *topologically forced* (degree theory) — a rare topology tool that **constructs**, not describes.
- **reframes:** the brute-force W57 scan → a winding-number index count: nonzero winding ⇒ collision count ≥ |winding|.
- **probe:** N=6–8: compute residual H(W57)=D61 for all 2^N W57 (reuse `run_tail_rounds`); check H=0 exactly at enumerator collisions; project to one register coordinate, compute winding number around the circle; compare to actual count.
- **kill:** Dead if H(W57) is statistically indistinguishable from a fresh pseudorandom function (winding ~ random-walk √-scaling, no predictive zeros).
- **skeptic:** mod-2^N winding is delicate; carries make H jumpy — must check winding *predicts* the zero count.
- **not a rebrand of:** carry-automaton/2-adic — holonomy is about transport around a *closed loop* and path-dependence (a global degree/winding), not forward dynamics or one map's valuation.

### W1-GE3 · Morse–Bott on the HW landscape → the 74 plateau = index of a degenerate manifold  `[P4 · cheap]`
- **one_liner:** The HW≈74 plateau is a Morse-degenerate critical manifold whose 132 null directions ARE the hard-core bits; Morse inequalities bound the low-HW basins.
- **lens** Morse-theory · **locus** whole-function/differential-trail · **mechanism** structural-invariant
- **analogy:** HW(output diff) is a function on free-word space; the 132 hard-core bits (zero deterministic control) = the kernel of its Hessian → a 132-dim degenerate critical manifold, not isolated points. The repo's own "74 = 66+8 = half of 132 random bits" is *exactly* the expected index of such a Morse-Bott manifold. Sublevel-set Betti numbers then lower-bound the number of disconnected low-HW basins (the N=10 "constructive interference").
- **reframes:** "the plateau is where search dies" → "the plateau's topology tells you how many independent basins exist and at what HW they branch."
- **probe:** N=8: build the sublevel filtration {f≤k} as a single-bit-flip graph, compute b_0(k) by union-find; predict component count/location matches observed basins and the dominant band's index = #hardcore/2.
- **kill:** Dead if b_0≡1 until the global min (no branching matching observed basins).
- **skeptic:** Morse theory is the textbook *descriptive* tool; survives only because the Hessian kernel is pre-identified (the 132 bits) and 74 is half-confirmed — must tie a Betti number to an observable.
- **not a rebrand of:** spectral/additive — this is the filtration topology of the HW *search landscape* (what stops hill-climbers); index=hardcore/2 has no spectral analog.

### W1-GE4 · Davies-Meyer feed-forward as an Euler class  `[P3 · cheap]`
- **one_liner:** Without feed-forward the difference bundle is trivial (collisions glue freely); the feed-forward is the section whose zero-set's Euler class localizes the whole easy/hard gap.
- **lens** obstruction-theory/characteristic-classes · **locus** feed-forward/whole-function · **mechanism** reframe
- **analogy:** Bare P is invertible → the difference bundle has a global section (inner rounds easy). Re-attach feed-forward → "collision" = "section s(M)=ΔP+ΔH_in vanishes," a nonvanishing-section (Euler/primary-obstruction) problem. Since the *one* non-invertible step is the only place a characteristic class can be nonzero, the topology concentrates exactly where the repo already located difficulty; the 132 hard-core bits = the cocycle's support.
- **reframes:** *why* "92% breaks" but the tail resists — the obstruction is a localized class on the feed-forward patch, not spread across rounds; predicts the hard-core set is candidate-independent (matches repo).
- **probe:** N=4: enumerate s(M)=ΔP+ΔH_in; compute its Z/2 zero-support per output bit; compare to the hard-core set; check the rounds-1..59 subproblem section is everywhere-zeroable.
- **kill:** Dead if the zero-support is just the diff-linear-rank statistic re-expressed (no new bits, no new prediction).
- **skeptic:** "Euler class of a (Z/2^N)^8 bundle" risks being vocabulary — earns its keep only if the cocycle-support is computed by a *different method* yet agrees with the hard core.
- **not a rebrand of:** MITM — localizes the obstruction to a class on a fiber rather than meeting-in-the-middle.

### W1-GE5 · Ollivier–Ricci curvature → the "0-slack" barrier, computable today  `[P4 · cheap, has ready validation set]`
- **one_liner:** "0-slack" = strongly negative discrete Ricci curvature on carry edges; a signed local predictor that can beat the repo's dead predictors.
- **lens** discrete-differential-geometry · **locus** carries/round-function · **mechanism** structural-invariant
- **analogy:** The repo's barrier is literally "0-slack constraint geometry" = a bottleneck/constriction, and the canonical detector of bottlenecks is negative Ollivier-Ricci curvature (Wasserstein spread of neighbor distributions). The most-negative carry edges = the 0-slack "bridges" no message freedom relaxes.
- **reframes:** gives a falsifiable structural predictor to replace the ones that *failed* (de58_size, hard_bit_lb had Spearman ρ≈0): mean negative carry-edge curvature should predict solver behavior because it measures *slack*, the true barrier.
- **probe:** N=8: build the variable-interaction graph of the bare arithmetic (carries+rotations, NOT the CNF clause graph); compute edge-wise Ollivier-Ricci; test (i) sr=61 more negative than sr=60, (ii) curvature vs kissat dec/conf across the 67 candidates, |ρ|>0.1.
- **kill:** Dead if |ρ|≲0.1 against the same table where de58 already failed (informative: barrier isn't graph-geometric).
- **skeptic:** must compute on the variable-interaction graph, not the Tseitin clause graph, or you measure the encoder.
- **not a rebrand of:** spectral-graph/RMT — Ollivier-Ricci is local, edge-wise, signed; gives a per-edge slack atlas a global spectrum/treewidth cannot.

### W1-GE6 · Configuration-space braid → multi-block = added generators  `[P2 · cheap]`
- **one_liner:** Message words are particles on the Z/2^N circle, carries are crossings; a collision-pair is a braid whose class obstructs single-block closure.
- **lens** topology/braid-groups · **locus** message-schedule/carries · **mechanism** reframe
- **analogy:** "rolled around a circle" = configuration space of points on a circle, π₁ = braid group; the schedule is a fixed move-word (rotations = circular shifts, adds = crossings recording carries). A collision = a closed braid; the sr-wall = the required braid class isn't realizable in one block; **multi-block adds generators** (a second strand bundle) that can realize it — a topological reason the highest-EV repo bet (block-2) is the right move-class change.
- **reframes:** "why does multi-block change the mechanism class" → "it enlarges the braid group, making a non-closable braid closable."
- **probe:** N=4: record the 43-adder carry pattern of collision vs non-collision pairs as a crossing sequence; compute writhe (signed carry count) + underlying permutation; do collisions cluster at a distinguished class? escalate to Burau if writhe alone separates.
- **kill:** Dead if the braid invariant is the same on collision/non-collision pairs or is a deterministic function of HW.
- **skeptic:** long random braids are invariant-saturated; need a fine invariant (Burau), but cheap first.
- **not a rebrand of:** carry-automaton/coding — records the isotopy class of the whole crossing history, orthogonal to forward state and linear distance.

## Dynamical systems & spectral

### W1-DY1 · Differential transfer operator + Ruelle zeta → collisions as a leading eigenvalue  `[P4 · cheap · HEADLINE]`
- **one_liner:** Build a weighted Perron–Frobenius operator on round-differentials; its leading eigenvalue IS 2^0.74N, its zeta zeros encode collision rates; de58-low-rank says it's tiny.
- **lens** transfer-operator/dynamical-zeta · **locus** differential-trail/whole-function · **mechanism** count
- **analogy:** Define L[Δ',Δ] = #(carry/message configs realizing the round transition Δ→Δ') — a weighted adjacency on differentials. Then (L^64) over feed-forward-closed states = the collision count; log₂ λ_max(L) = the growth rate (topological entropy / pressure); the dynamical zeta ζ(z)=det(1−zL)^{-1} has zeros = collision rates (primes↔Riemann analogy). **The de58 growth law (de57/de59/de60 constant, |de58| only 2^10 at N=32) independently says L is LOW-RANK and N-stable** → possibly a poly-time, even O(1)-rank, collision *counter*.
- **reframes:** "count collisions by O(2^4N) enumeration" → "find the leading eigenvalue of a small operator"; the headline candidate.
- **probe (seconds, numpy):** N=6: enumerate the *small* set of reachable per-round modular differentials; build L by brute-counting per-round realizations; compute λ_max; **is log₂λ_max ≈ 0.74?** Repeat N=4,8,10 for N-stability; bonus: zeros of det(1−zL).
- **kill:** Dead if log₂λ_max isn't within ~10% of the measured exponent at two N, or λ_max drifts with N.
- **skeptic:** the feed-forward is terminal/non-recurrent, so "iterate to a stationary measure" is really a finite-time approximation; clean story is for the recurrent interior (rounds 16–59).
- **not a rebrand of:** carry-automaton (a Boolean acceptor; integer state count) — this is a *weighted* operator whose *spectrum/zeta* is the object; the automaton can't even ask "what is the exponential growth rate." Not 2-adic (real non-negative matrix).

### W1-DY2 · Bowen pressure → the sr-cliff as a phase transition  `[P3 · cheap]`
- **one_liner:** Collision rate = root of a pressure function P(β)=0; the sr=60→61 cliff is a first-order phase transition (a kink in P).
- **lens** thermodynamic-formalism · **locus** differential-trail · **mechanism** lower-bound
- **analogy:** Assign each per-round transition a potential φ = log(realization prob); pressure P(β)=lim (1/n)log Σ_orbits exp(βΣφ). Bowen's equation: the rate = β* solving P(β*)=0. The sr-cliff = a non-analytic kink because the W[60]-freedom-loss makes one transition forbidden (φ→−∞), severing the high-pressure branch; the 2^-2N = the potential value at the boundary.
- **reframes:** "sr=61 costs 2^-2N" → "the potential at the phase boundary"; predicts where other transitions sit (N=10 = a negative-temperature dip).
- **probe:** Reuse the DY1 matrix as L_β[Δ',Δ]=(count)^β; compute P(β)=log λ_max(L_β) on a β-grid at N=6,8; does P(β)=0 reproduce the rate? does fixing W[60] create a slope discontinuity?
- **kill:** Dead if P(β) is smooth across the round-60 fix/free switch (no kink), or β*-rate disagrees >10%.
- **skeptic:** pressure needs a thermodynamic (n→∞) limit; SHA has fixed n=64 — the "transition" could be a finite-size crossover.
- **not a rebrand of:** carry-automaton — a one-parameter family L_β and the non-analyticity of β↦P(β), which a finite automaton has no language for.

### W1-DY3 · Differential Lyapunov spectrum → the floor as an exponent, the "2" as a 2-D unstable subspace  `[P3 · cheap]`
- **one_liner:** The per-round 2^-2N is a negative Lyapunov exponent; collisions must ride the contracting subspace; the "2" = dimension of the unstable subspace at the boundary.
- **lens** Lyapunov/Oseledets · **locus** differential-trail · **mechanism** lower-bound
- **analogy:** Linearize per-round differential propagation A_r; Lyapunov exponents = log-growth of singular values of ∏A_r. A collision pins the orbit to the most-contracting (stable) directions; cost/round = gap between the typical expanding exponent and the contracting one forced onto. The repo's "two independent N-bit conditions" = a 2-D unstable subspace to annihilate ⇒ factor 2 ⇒ 2^-2N.
- **reframes:** explains the "2" structurally (unstable-subspace dimension) and "cascade depth ≈60" as an Oseledets rank crossing.
- **probe:** N=6/8: build per-round differential Jacobians empirically (perturb incoming diff, average over realizing carries), SVD of ∏A_r; is χ_min ≈ −log2/round (two give −2N)? does #(χ<0) predict cascade depth?
- **kill:** Dead if the differential Jacobian has no clear contracting directions (all |χ|≈0 — which the near-injective carry hint actually predicts).
- **skeptic:** **directly conflicts** with the near-injective carry finding (suggests χ≈0); must explain why bit-injectivity ≠ modular-metric isometry (area can contract under a bijection, à la a hyperbolic toral automorphism) — kill fast if not.
- **not a rebrand of:** carry-automaton — singular values of a matrix *product* (a cocycle), an infinitesimal expansion/contraction the automaton has no notion of.

### W1-DY4 · Carry subshift + shadowing lemma → a barrier *certificate*  `[P3 · cheap]`
- **one_liner:** Encode carry-histories as a subshift; shadowing decides whether a near-collision is tracked by a true collision — where it fails is a no-collision certificate.
- **lens** symbolic-dynamics/shadowing · **locus** carries · **mechanism** lower-bound
- **analogy:** Symbol = per-round carry pattern; admissible transitions = an SFT. A δ-pseudo-orbit = a near-collision (the HW~74 plateau population); shadowing asks if every pseudo-orbit has a true orbit (collision) within ε. Hyperbolic SFTs satisfy shadowing (every near-collision ⇒ a real one); where shadowing *fails* marks rounds/HW-radii where near-collisions are genuinely isolated = a barrier. The only idea here that yields a *negative* guarantee.
- **reframes:** the fuzzy "does a near-collision imply a collision?" → a decidable property of a finite graph + a δ-radius barrier certificate.
- **probe:** N=6: build the carry-SFT adjacency; for known near-collisions check whether a true collision sits within small Hamming radius (search the enumerated list); find the smallest δ with no nearby collision; cross-check the SFT's topological entropy against DY1's λ_max.
- **kill:** Dead if every near-collision up to the plateau radius already has a nearby true collision (shadowing trivial → no barrier), or shadowing fails at δ→0 (wrong encoding).
- **skeptic:** shadowing is a *uniformly hyperbolic* theorem; partial hyperbolicity (likely, given near-injectivity) gives a vacuous modulus — stays HYPOTHESIS-grade unless the SFT is genuinely Anosov-like.
- **not a rebrand of:** carry-automaton — uses the subshift only as substrate for orbit-tracking/gluing theorems (metric closeness of trajectories), which an acceptor cannot pose.

## Computation, information & algebra

### W1-IN1 · Feed-forward coincidence operator → quotient out the bijection  `[P4 · cheap]`
- **one_liner:** Quotient out the invertible permutation; collisions become coincidences of a single deterministic modular-add map Φ; study its fibers.
- **lens** information-theory/group-action · **locus** feed-forward · **mechanism** reframe
- **analogy:** P is a bijection; define Φ(M)=P(IV,M)⊟IV per lane. A collision ⇔ Φ(M)=Φ(M'). Since the *only* non-injective op is the final 8×32-bit add, Φ inherits all non-injectivity from carry-merging — collision-finding = "find two inputs landing in the same coset of the add-kernel." The 64 rounds become a change of coordinates on the domain of one adder (the moment-map/quotient of a group action; all loss happens at the level set).
- **reframes:** "64-round search" → "characterize the fiber structure of P∘(one add)"; gives the cascade a closed-form *target set* (the kernel coset).
- **probe:** N=4,6,8: fix 14 message words, vary 2; compute Φ; over colliding pairs measure the per-lane pre-add modular-difference distribution — predict concentration at low 2-adic valuation (low carry depth).
- **kill:** Dead if the pre-add differences are uniform (KL<0.02 bits) — the quotient buys nothing.
- **skeptic:** "quotient out P" is free conceptually but P is the hard part; earns its keep only if the target coset has a description the backward cascade can exploit.
- **not a rebrand of:** MITM — never splits rounds; isolates the single non-invertible operation and studies its algebraic fiber.

### W1-IN2 · XOR/ADD uncertainty principle → a provable "no basis is easy" barrier  `[P4 · trivial · HEADLINE, cheapest probe]`
- **one_liner:** Any function sparse in the Walsh (XOR) basis is forced dense in the cyclic-DFT (ADD) basis; SHA lives where both are dense.
- **lens** harmonic-analysis · **locus** round-function/carries · **mechanism** lower-bound
- **analogy:** Z/2^n carries two character groups — Walsh (diagonalizes XOR/rotation) and cyclic DFT (diagonalizes add). Carry = the obstruction between them = the [X,P] commutator of a Weyl-Heisenberg pair. **Conjecture:** for the round R, support_⊕(R)·support_+(R) ≥ 2^{cn}. This *unifies* the repo's two dead ends — GF(2) fails (cyclic spectrum spread by carries) and Walsh fails (Walsh spectrum spread by add) — into one principle: no basis diagonalizes both.
- **reframes:** "no basis makes SHA easy" from an empirical lament to a *provable support-product lower bound with a constant* — retiring whole attack classes (ANF, linear, 2-adic) at once.
- **probe (cheapest, ~30 lines, seconds):** N=4,6,8,10: take a single masked lane round e' as a function of one word; compute its Walsh transform (FFT over (Z/2)^N) → S_⊕ and cyclic DFT → S_+; plot log₂(S_⊕·S_+) vs N (use effective/entropy support). Control: replace add by xor → product should collapse.
- **kill:** Dead if log₂(S_⊕·S_+) is flat/sub-linear in N, or a cheap basis change drives it below 2^{0.3N}.
- **skeptic:** support-products are sensitive to tiny coefficients — use a robust effective support; one lane may be too simple, the constant matters for 64 rounds.
- **not a rebrand of:** plain Walsh/linear (which *seeks* one big coefficient) — this proves sparsity is *impossible in both bases at once*, a barrier invoking the ADD/cyclic transform linear cryptanalysis never touches.

### W1-IN3 · Algorithmic mutual information (basis-fixed) → an order parameter for the frontier  `[P3 · cheap]`
- **one_liner:** The colliding pair has a short joint description (the cascade); minimal joint-circuit size should jump exactly at the sr-frontier.
- **lens** resource-bounded-information · **locus** message-schedule/whole-function · **mechanism** structural-invariant
- **analogy:** M,M' aren't independent — the cascade is a tiny program emitting M' from M + k correction words. Resource-bounded algorithmic mutual info I_t(M:M'), approximated by the smallest fixed-ARX-basis circuit emitting both, is computable (dodging "Kolmogorov is uncomputable"). Hypothesis: at sr=60 the joint description is O(1) words shorter (cascade compresses); at sr=61 it blows up to ≈2|M| (no compression) → 2^-2N.
- **reframes:** a single scalar (joint-description deficit, bits) predicting solvability across all frontiers; the 132-bit plateau = "can't compress below 132 free residual bits."
- **probe:** N=6,8: construct the cascade joint program, count correction words k(sr) needed per depth; at N=6 brute-search for any shorter joint ARX circuit; predict k(sr) jumps discontinuously at sr=60→61 with nothing shorter below.
- **kill:** Dead if k(sr) grows smoothly across the frontier, or a ≥2-word-shorter circuit is routinely found.
- **skeptic:** min-circuit-size is NP-hard; only the cascade *upper bound* is certain at larger N — can't prove minimality.
- **not a rebrand of:** raw Kolmogorov (dead, uncomputable) — fixes a finite gate basis + bounded depth, tied to the *measured* correction-word count.

### W1-IN4 · 2D PEPS over the round×bit lattice → an entanglement anisotropy  `[P3 · cheap]`
- **one_liner:** The killed MPS was 1D along bits; a 2D tensor network over round×bit may be area-law across the round-cut even where the bit-cut is volume-law.
- **lens** tensor-network · **locus** whole-function · **mechanism** reduce
- **analogy:** Tensor at each (round,bit); horizontal bonds = carry propagation (bit→bit), vertical = round recurrence. The killed MPS cut along bits (carry chain = large bond dim). But the **round-cut** is exactly the MITM cut, and MITM's 232/256 says only ~24 bits cross it → a low boundary entropy. PEPS would quantify whether pushing the cut past round 60 blows it up.
- **reframes:** "MITM gives 232/256" → one point on an entanglement-vs-cut-position curve; computing it shows *why round 60* and whether any contraction order beats the round-cut.
- **probe:** N=4,6 reduced-round: don't contract — measure boundary rank (Rényi-0 = log distinct boundary states) for the round-cut vs bit-cut across cut positions; predict bit-cut ≈ 2^N (MPS death) but round-cut grows slowly (area law) with a knee near the frontier.
- **kill:** Dead if round-cut boundary rank grows as fast as the bit-cut (slope ≥0.8/round) — brute force in every direction.
- **skeptic:** Rényi-0 is pessimistic; weighted (Rényi-1) entanglement may differ; reduced→full-round extrapolation is risky.
- **not a rebrand of:** killed MPS (1D along bits) — this is 2D and the object is the orthogonal round-direction cut; predicts an anisotropy a scalar treewidth can't express.

### W1-IN5 · Communication complexity of the round-60 predicate → MITM as a barrier  `[P2 · cheap]`
- **one_liner:** Split the collision predicate at round 60 between two parties; a communication lower bound bounds ALL forward/backward attacks (not just MITM).
- **lens** communication-complexity · **locus** state-cross-section (round 60) · **mechanism** lower-bound
- **analogy:** Alice holds forward freedoms (IV→r60), Bob backward (target→r60); collision ⇔ their round-60 state-sets intersect = Set-Intersection/Disjointness on the 256-bit state. MITM's 232/256 = the effective input length. A communication *lower* bound (Disjointness is Ω(n)) would prove no forward/backward split beats 2^b — a real barrier, vs MITM's upper bound.
- **reframes:** MITM from an *attack* (upper bound 232) to a potential *barrier* (lower bound); the 92%-but-stuck as a communication phase transition at the round where the predicate jumps from low- to high-communication.
- **probe:** N=4,6: build the communication matrix M[a][b]=1 iff forward-a, backward-b collide at the reduced-round cut; measure log-rank, fooling-set size, distance from the Disjointness pattern; predict low-rank below the frontier, full-rank just past it.
- **kill:** Dead if the matrix is low-rank on *both* sides (always easy) or full-rank everywhere (no transition).
- **skeptic:** the two-party model is a choice the adversary needn't respect; explicit communication lower bounds are a graveyard of hard open problems — expect to *measure* rank, not *prove* a bound.
- **not a rebrand of:** MITM (an algorithm/upper bound) — studies the communication complexity of the *predicate itself*, aiming for a lower bound constraining all such algorithms.

---

# WAVE 2 — control · rigidity · circle-method · quantum-magic · proof-complexity · self-organization (2026-06-03)

**Cross-wave spine:** a striking number of wave-2 angles converge on *one cheap artifact* — a
finite-difference **GF(2) linearization** of the masked round map giving per-round matrices A_i
(state→state), B_i (message→state), C (feed-forward). Build it once and the control-Gramian (CT1),
rank-collapse (CT2), LQR-corank (CT4), observer (CT5), rigidity Jacobian (RG1/RG2), and the
linearization-survival graph (PC5) all become one-line rank/corank queries. Independently, several
angles **predict the same boundary** (round ~59–60) by different accounting — magic saturation (QI1),
stabilizer-rank (QI4), expansion-width (PC1), PC-degree (PC2) — which is itself a strong signal.

## Control theory & signal processing

### W2-CT1 · Controllability Gramian = the hard-core mask  `[P3 · cheap · HEADLINE]`
- **one_liner:** Linearize the round map on the XOR-difference state; the uncontrollable subspace should *be* the 132 frozen bits.
- **lens** control-reachability · **locus** round-function/feed-forward · **mechanism** structural-invariant
- **analogy:** δ-state `x_{i+1}=A_i x_i + B_i u_i` (u = schedule-diff input). The reachable set after 64 rounds is Im[B,AB,A²B,…]; its **cokernel** = output functionals you can't independently steer = the hard-core bits. The Kalman controllability object, with a *named basis* replacing the "132" slogan.
- **reframes:** "132/256 hard-core, HW~74" from a count to the corank of an explicit mod-2 reachability matrix with a basis telling you exactly which bits are free vs forced.
- **probe:** N=4..12: finite-difference linearize (flip an input bit, XOR masked-round outputs = one column of B; same for A); GF(2) row-reduce [B,AB,…]; report corank; does it →132/256≈0.516?
- **kill:** Dead if corank ~0 (full controllability) generically, or no stable value across base-points/N.
- **skeptic:** the Gramian is point-dependent (Ch/Maj/carry nonlinear); 132 may only emerge after averaging — or the corank lives entirely in the linearization gap.
- **not a rebrand of:** carry-automaton (forward state machine) — this is the *dual* reachability matrix + cokernel basis; not spectral-graph (no Laplacian/ensemble).

### W2-CT2 · Controllability-rank collapse pins "round 60"  `[P4 · cheap · HEADLINE]`
- **one_liner:** Track the rank of the round-by-round reachability matrix; the round it drops below "enough to zero δH" is the cascade death.
- **lens** LTV-control/finite-horizon-reachability · **locus** differential-trail/state-cross-section · **mechanism** lower-bound
- **analogy:** "sr=k reachable" ⇔ the target δH=0 ∈ Im R_t. The σ/Σ maps are *singular* over GF(2) (SHR drops bits), so each round's A_i can contract rank; the round where cumulative rank can no longer cover δH=0 = the cascade death. That crossing should be ~60 and **rotation-constant-dependent**.
- **reframes:** "why 60?" → a deterministic rank-threshold crossing in a product of explicit singular GF(2) matrices.
- **probe:** N=8..12: rank(R_t) vs round; locate r* where target ⊄ Im R_t; **kicker:** swap a rotation constant (ROR7→ROR8) and check r* moves.
- **kill:** Dead if rank monotone-saturates (no collapse) or r* is insensitive to large rotation perturbations.
- **skeptic:** small-N "round 60" is scaled; the threshold dim may shrink too — need the N-sweep to show r*/rounds→60/64.
- **not a rebrand of:** cascade-DP (a state DP) — computes no states, just one scalar (GF(2) rank) per round and a threshold round.

### W2-CT3 · Schedule as an IIR filter → poles predict the N=10 interference  `[P2 · trivial]`
- **one_liner:** The schedule recurrence is a linear IIR filter; its z-transform poles/resonances predict trail spacing and the N=10 anomaly.
- **lens** LTI/z-transform · **locus** message-schedule · **mechanism** reframe
- **analogy:** W[i]=σ1 W[i-2]+W[i-7]+σ0 W[i-15]+W[i-16] is a recurrence in round-index i; in the bit-rotation DFT basis it block-diagonalizes into 32 scalar sub-filters with poles z(ω). Resonances (|z|≈1, low damping) = rounds where differences don't decay = long trails; a dominant pole's natural period commensurate with the word width selects the constructive-interference N.
- **reframes:** "N=10 is special" → a pole-period commensurability of an explicit characteristic polynomial.
- **probe:** numpy `roots` of the 16-degree characteristic polynomials per DFT frequency (ROR caricature first, then SHR correction); check the empirical masked-schedule difference-echo envelope tracks the dominant pole modulus.
- **kill:** Dead if the echo envelope doesn't track the dominant pole modulus at small N (linearization too lossy).
- **skeptic:** SHR breaks the clean cyclic diagonalization; poles are exact only for a σ-without-SHR caricature.
- **not a rebrand of:** Walsh/linear — computes transfer-function poles in the *round-index* domain, no correlation/bias.

### W2-CT4 · Minimum control-energy (LQR) → derives `2^-2N` and `0.74` as a Gramian corank  `[P3 · cheap]`
- **one_liner:** Energy to force δH=0 is an LQR cost; appending the two sr-conditions adds corank 2N per round = 2^-2N.
- **lens** LQR/min-energy · **locus** feed-forward/differential-trail · **mechanism** lower-bound
- **analogy:** Min-energy `x_f^T W_c^{-1} x_f`; enforcing one more sr-round forces the trajectory into a codim-2N target (the two N-bit conditions). Over GF(2) the "energy" is a corank/count → `2^-2N = 2^-codim`; the collision exponent `0.74` = ratio of free- to constrained-direction GF(2) volume.
- **reframes:** both empirical exponents become coranks/eigenvalue-products of one explicit Gramian.
- **probe:** append the g1=0, h=0 functionals as output rows to the CT1 reachability matrix; `extra_codim = rank([R;constraints])−rank(R)`; **is it 2N per enforced round?** free-bit slope → 0.74?
- **kill:** Dead if extra_codim ≠ 2N (e.g. N — contradicting the verified 2^-2N), or the slope isn't 0.74.
- **skeptic:** "energy" is a real inner-product notion; the clean derivation only holds in the GF(2) corank reading, not the real determinant.
- **not a rebrand of:** 2-adic/MITM — a Gramian corank, no valuations, no forward/backward match.

### W2-CT5 · Kalman observer → the unobservable subspace is the residual search  `[P3 · cheap]`
- **one_liner:** Build an observer estimating M₂ from M₁ + the collision constraint; its unobservable subspace = the bits you can never pin.
- **lens** observability/estimation · **locus** whole-function/feed-forward · **mechanism** reframe
- **analogy:** Finding M₂ = estimating δ=M₂−M₁ from the back-propagated δH=0 "measurements." The observability Gramian's kernel = δ-directions the constraint leaves free = the residual brute-force. Dual to CT1; self-duality of the feed-forward add predicts observable corank = controllable corank (both = the hard core).
- **reframes:** "residual search cost" → unobservable-subspace dimension; yields a *constructive* observer that peels off the linearly-determined bits of M₂.
- **probe:** N=8: corank of O=[C;CA;CA²;…] over GF(2); compare to CT1 corank (self-duality test); verify the observer recovers exactly the predicted bits of a brute-forced collision partner.
- **kill:** Dead if the observer predicts no bits (unobservable = everything) or observable/controllable coranks don't match.
- **skeptic:** linear observability may say M₂ is fully determined while the true nonlinear residual hides in carries the observer can't model.
- **not a rebrand of:** MITM — a fixed linear observer matrix (Gramian corank), no meeting-in-the-middle table.

## Rigidity theory & geometric constraint systems

### W2-RG1 · Maxwell–Calladine isostatic point → "why round 60" as a rigidity transition  `[P4 · cheap · HEADLINE]`
- **one_liner:** The sr-boundary is where the collision framework becomes isostatic — floppy modes hit zero, rigidity saturates.
- **lens** Maxwell-Calladine/generic-rigidity · **locus** cascade enforcement sequence · **mechanism** lower-bound
- **analogy:** Each enforced round (da=0 at r) = geometric constraints (bars) tying message DOF through the carry structure. Maxwell: floppy(r) − selfstress(r) = D(r) − C(r). At r≈60 this crosses zero from under- to over-constrained = the boundary; each round past isostatic adds exactly two constraints (the g1=0 AND h=0 pair) → 2 units of over-constraint = the codim behind 2^-2N.
- **reframes:** "why round 60?" → the integer r where D(r)−C(r) first goes nonpositive; derives 2^-2N from codimension-2 over-constraint, independent of carry-length.
- **probe:** N=4..12: build the per-round agreement-constraint Jacobian via `add_word(track_carries=True)` linearized at a known sr=60 solution; compute D(r)−C(r) and the *measured* rank for r=57..61; nullity→trivial = predicted boundary; codim increment per round should be ~2.
- **kill:** Dead if D(r)−C(r) never changes sign in 57..61, or the per-round codim increment isn't ≈2.
- **skeptic:** SHA constraints are highly non-generic (shared words, structured carries); the naive count can be far from true rank — use the *measured* rank.
- **not a rebrand of:** Gröbner/AG — no ideal/basis/elimination; a single numerical Jacobian rank with a kinematic kernel/cokernel split.

### W2-RG2 · Floppy modes = controllable bits, self-stresses = the 132 hard-core  `[P4 · cheap · HEADLINE]`
- **one_liner:** Kernel of the rigidity matrix = steerable message freedoms; cokernel = the 132 uncontrolled output bits.
- **lens** bar-joint-rigidity · **locus** feed-forward (256 output-diff bits) · **mechanism** structural-invariant
- **analogy:** Rows = output-bit constraints (bars), columns = controllable message-diff coords (joints). Right-null = floppy modes = freedoms that don't move pinned outputs = controllable bits; left-null = states of self-stress = output bits forced regardless of message = hard-core. Predict dim(left-null)≈132, rank≈124.
- **reframes:** the 132/256 split and HW~74 from a statistical observation to a self-stress dimension you can write down and inspect (which bit positions span it?).
- **probe:** N=8,10,12: linearize the output-diff-vs-freedom map at several collisions via `track_carries`; compute rank, left-/right-null dims; compare left-null support to the known hard-core positions.
- **kill:** Dead if self-stress dim doesn't scale toward 132 at N=32, or its support doesn't overlap the hard-core positions above chance.
- **skeptic:** only the *dimensions* are basis-invariant; *which* bits smear with the linearization point — support-overlap may be noisy.
- **not a rebrand of:** ANF-Jacobian (taken w.r.t. message bits for degree) — taken w.r.t. *difference* coords and split into floppy/self-stress; not a parity-check matrix (no syndrome decoding).

### W2-RG3 · Pebble-game generic rigidity → rigid clusters = forced cores, explains the linearization timeout  `[P3 · cheap]`
- **one_liner:** Run the (k,ℓ)-pebble game on the carry-coupling graph; maximal rigid clusters are the uncontrollable forced sub-structures.
- **lens** combinatorial-rigidity/pebble-game · **locus** carry-coupling graph · **mechanism** reduce
- **analogy:** Vertex per carry/diff bit, edge when two bits co-occur in one addition. Generic rigidity is *combinatorial* (depends only on coupling topology, not values), so it predicts forced structure from the wiring — exactly the regime where XOR-linearized sr=60 still timed out ("geometry not length"): linearization removes carry magnitude but not the coupling topology, so the percolated rigid cluster survives.
- **reframes:** explains the 0-slack timeout directly; gives a sub-quadratic combinatorial predictor of which words are floppy without solving.
- **probe:** N=8..16: emit the full-adder coupling graph from the encoder wiring; run a pebble game; report rigid-cluster sizes, percolation N, redundant-edge count; **run on both true and XOR-linearized wiring — clusters should be ~identical** (explaining why linearization didn't help).
- **kill:** Dead if clusters don't percolate near the boundary, or true-vs-linearized graphs differ a lot (carry length mattered after all), or (k,ℓ) needs ad-hoc tuning.
- **skeptic:** pebble games are exact only for specific matroids; the carry coupling may not be (k,ℓ)-sparse → clusters meaningless; k,ℓ must come from the adder's intrinsic DOF, not fit to 132.
- **not a rebrand of:** carry-automaton — ignores time and value, asks only about the static coupling matroid (same clusters even with carries linearized away).

### W2-RG4 · Prestress (second-order) rigidity → the N=10 interference + the factor-of-2  `[P3 · cheap]`
- **one_liner:** sr=60 collisions are first-order floppy but second-order rigid via cascade prestress; sr=61 fails two PSD conditions = 2^-2N.
- **lens** tensegrity/second-order-rigidity · **locus** cascade/state-cross-section · **mechanism** reframe
- **analogy:** A framework can be infinitesimally floppy yet rigid if prestress makes 2nd-order energy PSD on every flex. The cascade injects prestress; sr=60 collisions are marginal (1st-order floppy, 2nd-order rigid at a point); the N=10 constructive interference = a zero eigenvalue of the stress matrix on the flex space; sr=61 needs the stress matrix PSD on flexes, and the 2^-2N = measure of flexes satisfying the *two* quadratic conditions.
- **reframes:** unifies (i) XOR-linear sr=60 exists-but-times-out = 1st-order floppy/2nd-order obstructed, (ii) N=10 interference = stress eigenvalue crossing, (iii) 2^-2N = two prestress conditions.
- **probe:** at a known sr=60 collision, compute the 1st-order flex space (Jacobian nullspace); expand carries to quadratic order, restrict to the flex space, test PSD / count negative eigenvalues; look for a near-zero eigenvalue at N=10 and exactly 2 obstructions to sr=61.
- **kill:** Dead if the 2nd-order form is generically definite (no marginal modes, incl. N=10) or the # quadratic obstructions to sr=61 isn't 2.
- **skeptic:** quadratic carry expansion may need cubic+ terms; a spurious PSD result could be truncation; must verify the 1st-order nullspace is nonempty first.
- **not a rebrand of:** instanton/RG — a static PSD test of a fixed quadratic form on a fixed subspace; no action, flow, or fluctuation sum.

## Analytic number theory — circle method & arithmetic dynamics

### W2-NT1 · Collision singular series → derives `2^0.74N` as a product of local densities  `[P4 · cheap · HEADLINE]`
- **one_liner:** Write the collision count as a complete exponential sum; the major arc gives 2^0.74N as a singular series of per-round survival fractions.
- **lens** circle-method/exponential-sums · **locus** whole diff-constraint system · **mechanism** count
- **analogy:** R(N)=Σ_{M,M'} Π_r 1[Δ_r≡0]; expand each indicator in additive characters → a sum over frequency vectors. Major arcs (small-denominator resonances) = the main term = a singular series 𝔖=Π(local density); minor arcs (generic frequencies, scrambled by rotations) are negligible by square-root cancellation. The 0.74 exponent is forced by which rounds contribute a full vs partial factor of 2^N.
- **reframes:** "collisions ~2^0.74N" from a measured slope to a predicted main-term exponent (and constant) with a rigorous error term.
- **probe:** N=6,8: enumerate exact R(N); compute per-round survival fraction f_r=#{Δ_r≡0}/#{Δ_{r-1}≡0}; **does Σ_r log₂ f_r / N → 0.74?** separately confirm minor-arc mass is O(2^{-N/2}) over ~10⁴ random frequencies.
- **kill:** Dead if Σ log₂ f_r/N ≠ 0.74 (rounds too coupled for an Euler-product factorization).
- **skeptic:** SHA rounds are coupled (the schedule links them), so the product-of-local-densities may fail badly — the empirical 0.74 may be a global eigen-property with no Euler product.
- **not a rebrand of:** 2-adic (ultrametric |·|₂) or path-integral (one Hessian determinant) — Archimedean characters + a *sum over a frequency lattice* split into arcs; 0.74 = a count of resonant directions.

### W2-NT2 · Weil square-root cancellation → the origin of the 132 / HW~74 plateau  `[P3 · cheap]`
- **one_liner:** Rotation constants make per-round character sums Kloosterman-like; Weil caps bit concentration → the hard-core split.
- **lens** Weil/Kloosterman-bounds · **locus** round-function (per output bit) · **mechanism** structural-invariant
- **analogy:** Each output bit's bias is a sum S=Σ_x e^{2πi(ax+b·σ(x))/2^N}, structurally Kloosterman/Salié (linear + rotation-permuted term). Weil: |S|≤C·2^{N/2} for non-degenerate frequencies, full 2^N only on a thin degenerate set. # degenerate directions = biasable "soft" bits (~124); √-cancelling directions = bits pinned near ½ = hard-core (~132).
- **reframes:** *why exactly ~132* bits are hard-core (and which positions) — the dimension of the Weil-cancelling subspace fixed by SHA's rotation constants; predicts changing a rotation moves the plateau.
- **probe:** N=8: exactly compute S(a,b)=Σ_x e^{2πi(ax+b·σ1(x))/2^8} over all (a,b); classify degenerate (|S|≈2^N) vs cancelling (≲2^{N/2}); does the cancelling fraction ≈132/256? swap SHR10→SHR9 and check the predicted plateau shift.
- **kill:** Dead if |S| is a smooth continuum (no clean bimodal Weil dichotomy).
- **skeptic:** carries couple all bits, so a single-round single-bit sum may be the wrong object; the plateau could be a binomial-concentration artifact (132 ≈ entropic), nothing arithmetic.
- **not a rebrand of:** 2-adic (valuations) or path-integral (saddle) — the *size* of a complete Archimedean sum, a global cancellation theorem valid precisely when there's no dominating critical point.

### W2-NT3 · Weyl equidistribution of {σ1(W)/2^N} → why de58 grows, others constant  `[P3 · cheap]`
- **one_liner:** Schedule fractional parts equidistribute except the σ1-SHR10 (lacunary) coordinate — which is exactly the growing de58.
- **lens** Weyl-discrepancy/arithmetic-dynamics · **locus** message-schedule recurrence · **mechanism** structural-invariant
- **analogy:** Each de_r is a Weyl sum of the schedule orbit; "constant size" = equidistributing (discrepancy→0, difference set saturates); "growing" = non-equidistributing/lacunary. SHR10 is the textbook multiply-by-2^{-10}-then-truncate (lacunary {2^k θ}) whose Weyl sum doesn't cancel → its difference set grows with N. The *one* growing coordinate (de58) is exactly the one with an uncompensated lacunary shift.
- **reframes:** "de58 grows, others constant" (which already drives the repo to use modular diffs) → an equidistribution statement predicting |de58|~2^{αN} with α from the σ1-shift discrepancy.
- **probe:** N=6,8,10: per round compute the star-discrepancy of {W_t/2^N} and |de_r| (reuse `gap_analysis.c`); does the worst-equidistributed round = the unique growing de58, with matching slope? confirm de57/59/60 equidistribute (→constant).
- **kill:** Dead if de58 isn't the worst-equidistributed round, or its discrepancy slope misses the measured |de58| slope by >20%.
- **skeptic:** difference-set size depends on *pairwise* correlations; you may need 2-D discrepancy that equidistributes even when the 1-D orbit doesn't, dissolving the story.
- **not a rebrand of:** 2-adic — {x/2^N} is an Archimedean fractional part; the lacunary {2^k θ} phenomenon is classical real analysis.

### W2-NT4 · Singular-series double zero → derives `2^-2N` as two vanishing local factors  `[P4 · cheap]`
- **one_liner:** sr=61's 2^-2N is a singular series with a double-order zero: two independent local densities (g1=0, h=0) each = 2^-N.
- **lens** singular-series/local-obstruction · **locus** de60→de61 transition · **mechanism** lower-bound
- **analogy:** 𝔖_61 = 𝔖^{(g1)}·𝔖^{(h)}, two local densities each 2^-N living on orthogonal frequency sublattices (the verified independence, ratio 1.005). Like sums-of-three-squares failing for n=4^a(8b+7) (a vanishing local factor), sr=61 rarity = local-density suppression; the factorization into two independent conditions = two distinct local obstructions multiplying.
- **reframes:** the repo's hardest fact (sr=61=2^-2N) from an enumerated rarity to a structural double zero with *named* obstructions — and predicts that re-coupling g1,h moves the exponent toward 1 (an attack lever).
- **probe:** N=8,10 (reuse `gap_analysis.c`): confirm 𝔖_61=2^-2N; express each factor as a character sum C_{g1}(t), C_h(s); verify each is supported on a single frequency (clean local density) and the 2-D sum **factorizes** C(t,s)=C_{g1}(t)C_h(s).
- **kill:** Dead if C(t,s) doesn't factorize (g1,h share frequency support) — then 2^-2N is a single coupled condition.
- **skeptic:** most at risk of re-skinning the existing coincidence_variety independence result — must predict the attack lever or exact frequencies, not just relabel.
- **not a rebrand of:** 2-adic — an Archimedean local density, not a 2-adic 𝔖_2 from Hensel lifting.

### W2-NT5 · Canonical height → collisions as height-zero preperiodic coincidences  `[P2 · cheap]`
- **one_liner:** Give the schedule a canonical height; structured fills (0x55,0x15) are the preperiodic ĥ=0 points where collisions cluster.
- **lens** arithmetic-dynamics/heights · **locus** feed-forward coincidence locus · **mechanism** reframe
- **analogy:** ĥ(M)=lim (bit-spread/depth) à la Call–Silverman; preperiodic (ĥ=0) points = messages whose carry-orbit collapses = the low-HW structured fills the repo keeps rediscovering. A collision = a height-zero coincidence (two ĥ=0 messages with equal feed-forward image); equidistribution-of-small-height predicts collisions concentrate there.
- **reframes:** *why structured fills over-produce collisions* — they're the ĥ=0 locus; gives a height threshold for "collision-eligible."
- **probe:** N=8,10: compute a proxy ĥ (normalized carry/state bit-spread after the rounds); do colliding pairs have systematically lower ĥ? do 0x55/0x15 sit at ĥ≈0? is the da=0 cascade family the ĥ≈0 set?
- **kill:** Dead if colliding pairs have the same ĥ distribution as random pairs, or structured fills aren't low-height.
- **skeptic:** "canonical height" over Z/2^N is a stretch (no projective variety, limit may not converge); the proxy may just re-measure Hamming weight.
- **not a rebrand of:** 2-adic — Archimedean log-size height, not a 2-adic valuation/local height.

## Quantum-information structure (used classically) — stabilizer & magic

### W2-QI1 · Magic saturation → why 92% breaks and the wall sits at ~59  `[P4 · cheap · HEADLINE]`
- **one_liner:** XOR/rotate are Clifford-like (free); the carry is the non-Clifford "magic"; the wall is where cumulative magic rank saturates the free-bit budget.
- **lens** stabilizer/magic-accounting · **locus** per-round Boolean map · **mechanism** lower-bound
- **analogy:** Gottesman-Knill: Clifford+T simulable in time exp(T-count). SHA's affine shell (Σ,σ,ROR,XOR) is Clifford-free; the only "T-gates" are carry/Ch/Maj ANDs. The effort to *linearize away* the nonlinearity (what every differential attack does) scales with accumulated AND-count, not degree, and breaks when it exceeds the free-bit budget — predicting the round-59 boundary.
- **reframes:** the *location* of the 92%/round-59 boundary from an empirical surprise to "where M(r) ≈ free-bit budget"; explains why XOR-linearized sr=60 sits right at the budget edge (timeout-not-UNSAT).
- **probe:** N=4..10: per round, fit the best affine approximation, take the **rank of the residual** {round(x)⊕affine(x)} = independent non-affine directions μ(i); plot cumulative M(r); look for saturation near r≈59. **Critical:** measure the *incremental* rank vs the running affine span (the contextual version), since the isolated per-round magic is constant.
- **kill:** Dead if even the *contextual/cumulative* magic increment is constant (then the wall is just free-bit exhaustion, the null hypothesis).
- **skeptic:** the round function is identical each round → naive per-round magic is constant and featureless; survives only if the *absorbable-vs-forced* magic relative to the running frame grows.
- **not a rebrand of:** ANF-degree (Maj is degree-2 from round 1, saturates immediately) — magic *rank* keeps growing after degree maxes; not Grover (no amplitude search).

### W2-QI2 · Message schedule as a stabilizer code → trail weight = code distance  `[P4 · cheap]`
- **one_liner:** Schedule parities = stabilizer generators; minimal trail weight = code distance; neutral moves = logical operators; carry = the non-stabilizer perturbation.
- **lens** stabilizer-codes/CSS-distance · **locus** the GF(2) schedule check matrix · **mechanism** lower-bound
- **analogy:** The (exact, linear) σ-recurrence defines a binary code on 512 message bits; a schedule-preserving differential = a codeword, its weight = the dominant trail cost; d(C) lower-bounds trail weight; logical operators (syndrome-fixing cosets) = neutral message modifications. Carries make the true map a *coset perturbed by ANDs*, so (trail weight − d(C)) = the QI1 magic budget, measured independently.
- **reframes:** *why neutral-modification freedom collapses in late rounds*; a pure-linear-algebra lower bound on trail weight; compare d(C) to the HW~74 plateau / 132 count.
- **probe:** N=4..12: build the check matrix H for the first r rounds; low-weight-codeword search (information-set decoding) for d(r); does d(r) jump near round 59? does the logical-operator count track 256−132? **report the carry-gap (trail weight − d(C)), not just d(C).**
- **kill:** Dead if d(r) grows smoothly with no jump near 59 and the logical count shows no link to 132/256.
- **skeptic:** closest neighbor to banned coding theory — the non-rebrand is the *carry-gap = magic budget* claim; if you only compute d(C), you've done banned coding theory.
- **not a rebrand of:** ANF-degree (distance is degree-1) or Grover (classical min-weight search).

### W2-QI3 · Feed-forward monogamy → why de58 carries all the differential freedom  `[P3 · cheap]`
- **one_liner:** The feed-forward "clones" internal state into the output; a monogamy inequality forces all slack into the de58 channel.
- **lens** monogamy/no-cloning (GF(2) counting) · **locus** feed-forward · **mechanism** lower-bound
- **analogy:** A collision forces the round-64 internal diff Δ_int to match *both* input-diff and output-diff. Monogamy: Δ_int can be strongly correlated with at most one; forcing both incurs a deficit paid only by the modular-add carry. Since de58 is the only varying differential, the monogamy slack should live *entirely* in the de58 channel — a sharp testable localization.
- **reframes:** *why exactly de58* carries all freedom while de57/59/60 stay constant — a monogamy ledger where only one channel holds slack.
- **probe:** N=4..10: measure corr(Δ_int,Δ_in)+corr(Δ_int,Δ_out) and per-channel slack; **predict slack≈0 in de57/59/60, all in de58.**
- **kill:** Dead if the correlation sum has no consistent ceiling, or slack is spread evenly across de57–60.
- **skeptic:** "GF(2) monogamy" is borrowed loosely; the inequality may be vacuous/trivially true — earns its keep only by *quantitatively predicting* the de58-only localization.
- **not a rebrand of:** ANF-degree (a correlation/sharing quantity, no degree) or Grover.

### W2-QI4 · Stabilizer rank χ → branch count of any case-splitting search saturates at the wall  `[P4 · cheap]`
- **one_liner:** Minimum affine-piece cover of each round (its stabilizer rank χ) counts carry case-split branches; Σ log χ_i explodes near round 59.
- **lens** stabilizer-rank/Bravyi-Gosset · **locus** single-round Boolean map · **mechanism** lower-bound
- **analogy:** Bravyi-Gosset simulate Clifford+T in time ~χ (stabilizer rank). The classical analog: the smallest # affine branches (AND-gated) reproducing the round = the carry case-split branching factor a piecewise-linear attack enumerates. Π χ_i = predicted enumeration cost; XOR-linearized sr=60 timing out means Σ log χ_i already exceeded the budget by round 60. A *second, piece-counting* estimate of the boundary cross-checking QI1's direction-counting.
- **reframes:** "the solver times out" → a predicted quantity (timeout onset = round where Σ log₂ χ_i exceeds log₂ budget); two independent magic measures landing on ~59 = strong corroboration.
- **probe:** N=2..8: per round build the truth table, compute the minimum affine cover χ_i (greedy set-cover over affine subfunctions); track Σ log₂ χ_i; measure χ of the *cumulative* map (where ranks multiply); does it grow super-linearly toward the budget near 59? cross-plot vs QI1's μ(i).
- **kill:** Dead if χ_i is O(1) and round-independent even for the cumulative map (merely linear growth, no saturation).
- **skeptic:** same identical-round worry as QI1 — must measure the *cumulative* χ, more expensive but tractable at N≤6.
- **not a rebrand of:** ANF-degree (χ and degree independent) or Grover (classical branch counting).

## Self-organization, fitness landscapes & population dynamics

### W2-SO1 · Neutral-network percolation → search as drift, plateau as a graph bottleneck  `[P4 · cheap · HEADLINE]`
- **one_liner:** The cascade's da=0 set is a neutral network; collisions exist iff it percolates to HW=0; every solver is the same walk on it.
- **lens** neutral-networks/neutral-drift · **locus** the da=0 neutral set · **mechanism** reduce
- **analogy:** All da=0 messages have equal "fitness"; adjacent ones (bit-flips staying on da=0) form edges. Collision-finding = neutral *drift* to HW=0, a pure graph question: does the component reach HW=0, and what's the mixing/cover time? The HW~74 plateau = a region with no escape edges to lower HW; all solvers stall at the same HW because they hit the same graph bottleneck.
- **reframes:** "search is hard" → "does the neutral network percolate to HW=0, and what's its conductance?"; explains why SAT/hill-climb/GPU all stall identically.
- **probe:** small N (reuse collision lists): build the da=0 graph (edges = bit-flips preserving da=0); (a) are HW=0 collisions in the same component as high-HW starts? (b) conductance/spectral gap + min-cut location (predict ≈0.74N-equivalent); (c) constrained-walk cover time vs diameter; sweep N to see if conductance collapses.
- **kill:** Dead if the network is one well-mixed component with constant conductance and poly drift to HW=0, or the plateau doesn't coincide with the min-cut.
- **skeptic:** the network may simply be *disconnected* across HW levels (collisions isolated, reachable only by big jumps) → "drift" is a non-starter; the edge definition is load-bearing.
- **not a rebrand of:** Morse-Bott (static critical-point topology) — this is *motion*: conductance/cover-time of a walk constrained to a level set; not generic SAT-stat-mech (a concrete combinatorial graph, not a clause ensemble).

### W2-SO2 · Quasispecies error threshold → the plateau as an information-maintenance limit  `[P4 · cheap · HEADLINE]`
- **one_liner:** A mutating message-population selected toward low HW delocalizes above a critical mutation rate; the plateau is the error catastrophe.
- **lens** Eigen-quasispecies/error-threshold · **locus** a population of messages under mutation+selection · **mechanism** reframe
- **analogy:** Fitness f(m)=exp(−β·HW); per-bit mutation μ. Eigen: below μ_c the population localizes as a cloud around low-HW masters (can climb); above μ_c mutation overwhelms selection and it delocalizes (HW→N/2). The HW~74 plateau = the system pinned *at* its error threshold — selection toward low HW exactly balanced by mutational entropy.
- **reframes:** the plateau from "energy trap" to "information-maintenance limit": no search can *hold* a population below ~74; gives μ_c(N) and the optimal solver schedule (sit just below μ_c).
- **probe:** (a) simulate a Moran/Wright-Fisher message population, fitness exp(−βHW), sweep μ, find the sharp HW-jump transition; does localized HW saturate near the plateau? (b) build the coarse-grained HW-shell quasispecies matrix from collision-list neighbor stats, diagonalize, read μ_c from where the dominant eigenvector delocalizes.
- **kill:** Dead if μ-sweep shows a smooth crossover (no sharp threshold), or the localized phase concentrates at HW≈0 (collisions easy to localize), or the dominant eigenvector is delocalized for all μ>0.
- **skeptic:** quasispecies needs a roughly single-peaked fitness; SHA's HW-vs-message may be rugged/multi-peak → glassy freezing, not a clean error catastrophe.
- **not a rebrand of:** Morse-Bott or SAT-stat-mech — a *population* statement; order parameter = localization of a distribution over genotypes; control parameter = mutation rate.

### W2-SO3 · Carry-avalanche SOC → 0.74 as a sandpile avalanche exponent  `[P3 · cheap]`
- **one_liner:** ARX carry chains are toppling avalanches; if SHA self-organizes to criticality, 0.74 is the avalanche exponent.
- **lens** self-organized-criticality/sandpile · **locus** carry propagation in the adds · **mechanism** count
- **analogy:** A carry into bit i can topple into i+1 (a 1-D avalanche; quasi-2-D across rounds via feed-forward). SOC produces power-law avalanche-size distributions with no tuning; 0.74 may be the signature exponent of this toppling geometry. Constant channels (de57/59/60) = subcritical; the growing de58 = the critical avalanching one.
- **reframes:** "why 0.74?" → "what's the toppling exponent of this automaton?"; recasts the constant-vs-growing channels as off-critical vs critical.
- **probe:** instrument masked adds to record carry-cascade-length and avalanche-size distributions per random pair; fit for a power law, extract the exponent, relate to 0.74; test whether constant channels are subcritical (exp cutoff) and de58 critical (scale-free); test abelian/order-independence (an SOC fingerprint).
- **kill:** Dead if cascade-length distributions are exponential (clear cutoff) at all N, or the exponent is far from a simple function of 0.74, or no subcritical/critical channel contrast.
- **skeptic:** power laws are over-claimed; a ≤32-bit chain gives <1 decade — too short to assert SOC; and SHA is *designed*, so any criticality is engineered, not self-organized ("critical by construction").
- **not a rebrand of:** Morse-Bott (an avalanche-size distribution from a toppling process, no Morse function) or generic SAT-stat-mech (a specific carry-statistics claim tying 0.74 to the ARX carry rule).

### W2-SO4 · Reaction-diffusion Turing instability → the 132 hard-core bits as unstable modes  `[P3 · cheap]`
- **one_liner:** The difference field is an activator-inhibitor medium; the 132 hard-core bits are its Turing-unstable, self-amplifying modes.
- **lens** reaction-diffusion/Turing · **locus** the round-to-round difference field · **mechanism** structural-invariant
- **analogy:** Linearize the difference map around da=0: rotations = diffusion (spatial coupling on the bit lattice), carries = reaction (activator amplification / XOR inhibition). A Turing instability makes specific *wavelengths* grow even when the uniform state is stable. The 132 hard-core bits = the unstable Fourier band (can't be driven to zero because they self-amplify), forcing the HW floor.
- **reframes:** the 132 hard-core bits from "stubborn bits" to a dispersion-relation prediction; predicts *which* positions are hard-core and ties them to the rotation constants.
- **probe:** build the per-round linearized difference-propagation Jacobian around da=0 (masked primitives), compose over rounds, compute the eigen/singular spectrum; identify growth-factor>1 modes; does their support match the 132 hard-core positions? near-circulant → a dispersion-vs-wavelength plot with an unstable band of width ~132.
- **kill:** Dead if there are no growth-factor>1 modes (da=0 fully stable → hard core is nonlinear), or unstable-mode support doesn't align with the measured hard-core bits.
- **skeptic:** ARX difference behavior is dominated by *nonlinear* carry events; a linearization may miss the hard core entirely; "Turing" strictly needs an activator-inhibitor sign structure the round may not honor.
- **not a rebrand of:** Morse-Bott (linear amplification/growth rates, not critical-point topology) or SAT-stat-mech (a deterministic spectral-stability analysis predicting named bit positions).

## Proof complexity & descriptive complexity (the rigorous "why it's hard to *prove*")

### W2-PC1 · Boundary-expansion width jump → a resolution lower bound that fires at 61, not 59  `[P4 · cheap · HEADLINE]`
- **one_liner:** Measure boundary expansion of the collision constraint hypergraph; show it jumps at sr=61, forcing large resolution width.
- **lens** resolution/Ben-Sasson–Wigderson · **locus** the sr=k constraint bipartite graph · **mechanism** lower-bound
- **analogy:** BW: boundary-expanding formulas need width ≥ Ω(c·s), tree-resolution size ≥ 2^Ω(w²/n). At sr=60 the system has exactly 4 free words for 2 triggers + boundary = a perfect constraint→private-variable matching exists (expansion collapses, short certificates). At sr=61, 3 free words vs ≥4 binding equations; Viragh's **slack=−64** = the constraint side over-saturates → Hall-deficit → no matching → surviving expanding core → width lower bound. Linearization keeps the incidence structure, so the expanding core survives (explaining the XOR-linear timeout).
- **reframes:** the sr-boundary from a solver-runtime fact to a proof-theoretic invariant (the matching/expansion phase transition of the constraint hypergraph).
- **probe:** N=4..10 (solver-free): build G_k for k=58..61 from masked primitives; (a) Hopcroft–Karp — does G_61 fail the constraint→private-variable matching while G_60 passes? (b) plot min boundary δ(s)/s; a constant lower bound only at 61 is the headline.
- **kill:** Dead if G_60 already fails the matching (also over-determined yet easy), or a bounded-size UNSAT sub-core exists at sr=61 (short refutation by inspection).
- **skeptic:** BW gives *width* for general resolution but exponential *size* only for tree-resolution; CDCL≈general-resolution-with-restarts may get lucky; SHA's adversarial structure may concentrate hardness in a *small dense* core (opposite of what BW needs).
- **not a rebrand of:** running-SAT (a static hypergraph property via Hopcroft-Karp + min-boundary sweep) or communication-complexity (no input partition/protocol).

### W2-PC2 · Polynomial-Calculus degree from the two-condition structure  `[P3 · cheap]`
- **one_liner:** Each held sr-round adds two algebraically independent ideal generators; PC refutation degree grows slope-2 per round, jumping at 61.
- **lens** Polynomial-Calculus/PCR-degree · **locus** the collision ideal I_k · **mechanism** lower-bound
- **analogy:** PC *degree* (not Gröbner *attack*) is the allowed barrier. The verified "each held round = two independent conditions g1=0, h=0" = adjoining two algebraically independent generators per round; independence is the engine of degree lower bounds (no cheap syzygy cancels them), so degree ramps with slope 2 — the algebraic fingerprint of 2^-2N and the dual of PC1's width.
- **reframes:** "2^-2N rarity" (counting) → a degree lower bound (proof complexity): you can't cheaply *certify* sr=61 because the certifying identity has degree past the 60↔61 line.
- **probe:** N=4,5,6: bit-polynomials for sr=58..61; degree-bounded PC simulation — for increasing d, Macaulay matrix of generators×monomials ≤ d, check 1 ∈ row-space (GF(2) rank); tabulate degree(k); look for slope-2 jump per round and a bump at 61. (Never runs Buchberger to completion = not the banned attack.)
- **kill:** Dead if PC degree is flat across k, jumps by 1 not ~2, or shows no discontinuity at 61.
- **skeptic:** statistical independence ≠ algebraic (ring) independence; PC degree bounds need system expansion (Alekhnovich-Razborov); carries are *sparse* (low-degree XOR layers) which could keep degree low.
- **not a rebrand of:** running-SAT/Gröbner-attack — measures *minimum degree* via a fixed-degree rank check, a property of the ideal.

### W2-PC3 · Feasible interpolation off the two-block absorber → proof size from a circuit lower bound  `[P3 · cheap]`
- **one_liner:** A short sr-proof would yield a small circuit separating absorbable from non-absorbable junction states; the 128-bit hard core bounds that circuit below.
- **lens** feasible-interpolation (Krajíček/Pudlák) · **locus** the cascade-junction interface z (de57/58/59, W58–W59) · **mechanism** lower-bound
- **analogy:** Pudlák: a short refutation of A(x,z)∧B(y,z) yields a small circuit C(z) deciding which side fails. Structure as A="block-1 yields residual with signature z" ∧ B="block-2 absorbs z" (the block2_wang frontier), sharing only the junction z. A short proof ⇒ a small absorbable-z separator; but the 128-bit hard core / HW~74 plateau is evidence that separator has *no* small circuit → interpolation converts that into a refutation-size lower bound.
- **reframes:** connects the two-block absorber geometry and the 128-bit hard core into one statement: short sr-refutations are impossible *because* the absorber-separating circuit is large; the 1800-CPU-hour wall as a shadow of a circuit lower bound.
- **probe:** small N: enumerate the junction interface z (tiny: |de58|=2 at N=4, 8 at N=6), label absorbable/not via `gap_analysis.c`; measure the separator's decision-tree depth / DNF size / sensitivity / monotonicity; does complexity *grow* with N?
- **kill:** Dead if the separator has small DT / low sensitivity at every N (cheap circuit ⇒ short proof, not a barrier); or if only resolution (not cutting-planes) applies (weak, known bounds).
- **skeptic:** feasible interpolation is *known to fail* for strong systems under crypto assumptions — and SHA *is* such an assumption (darkly ironic); confined to weak systems where bounds may not reach sr=61.
- **not a rebrand of:** running-SAT (reduces proof size to circuit size, both static) or communication-complexity (bounds the interpolant *circuit* directly, no two-party game).

### W2-PC4 · Definability jump → "collision exists" stops being local at 61  `[P2 · cheap]`
- **one_liner:** Bounded-variable / FO+fixed-point definability of "collision through round k" may collapse at the same k=61 the search does.
- **lens** descriptive-complexity/finite-variable-hierarchy · **locus** the structure A_k + property COLL_k · **mechanism** reframe
- **analogy:** Below 60: the cascade is a shift register propagating zeros diagonally, de57/59/60 constant → COLL is a bounded-radius *local* check (FO(LFP), round-independent pebble count). At 61: da=de kicks in and W[61] couples back via the schedule (t−7, t−16 long-range feedback) → the deciding neighborhood radius blows up → COLL_61 leaves FO^k. An EF/pebble phase transition.
- **reframes:** the boundary as a *logical phase transition in expressibility* — the round where collision-existence stops being local — machine-independent.
- **probe:** N=4,5: play the EF/pebble game (small reachability game on the product structure) between a collision and a minimal near-miss; tabulate the least distinguishing pebble count p*(k); headline = p* flat for k≤60, jumps at 61. Cheaper proxy: Gaifman-locality radius via BFS on the dependency graph (a ready substrate exists in the repo).
- **kill:** Dead if the locality radius / p* is already growing at k≤59 (never local even when easy), or flat through 61 (no jump).
- **skeptic:** FO(LFP)≈PTIME on ordered structures, but finding collisions is plausibly not PTIME → COLL may fail FO(LFP) *everywhere*, washing out the gap; N=4,5 may not extrapolate.
- **not a rebrand of:** running-SAT (a game-tree search on a static product graph, solver-independent) or communication-complexity (a one-structure definability game, no input partition).

### W2-PC5 · Linearization-survival (Tseitin) test → proves the obstruction is expansion, not carries  `[P4 · cheap · the clean experiment]`
- **one_liner:** XOR-linearized sr=60 still times out, yet linear systems are Gauss-easy; so the hardness is the surviving Tseitin-graph expansion, not nonlinearity.
- **lens** Tseitin/Urquhart-expansion · **locus** the GF(2)-linearized system L_k · **mechanism** lower-bound
- **analogy:** Tseitin formulas over an expander are *linear* yet resolution-hard (Urquhart): width Ω(n) from graph expansion despite trivial Gaussian solvability. If L_61 is Tseitin-like over an expanding carry-incidence graph while L_59 isn't, you recover PC1's width jump *with nonlinearity stripped away* — proving the obstruction is the graph, not the carries. The scalpel experiment of the whole program.
- **reframes:** settles *what the boundary is made of* — a graph-expansion/proof-width phenomenon, not a carry phenomenon; validates PC1 and demotes "carries are the only nonlinearity so carries are the barrier."
- **probe:** small N: Gaussian-eliminate the genuinely-linear vars from L_k; compute the *residual* carry-incidence graph's edge/vertex expansion for k=59,60,61 (constant expansion only at 61 = headline); plus block-sensitivity bs(L_k) (truth table at N=4,5) — a jump at 61 says hardness is structural.
- **kill:** Dead if the residual graph at sr=61 is small/non-expanding (timeout was an encoding artifact — itself valuable), or bs(L_k) is flat.
- **skeptic:** linearizing modular addition is *not* faithful (deletes the carries); "XOR-linearized sr=60" is a different problem whose timeout might reflect over-constrained-rank nonsense, not expansion — verify it's genuinely Tseitin-like (consistent charges) first.
- **not a rebrand of:** running-SAT (residual-graph expansion + block-sensitivity, solver-independent; the timeout is only *motivation*) or communication-complexity (single-prover width via expansion).

---

# WAVE 3 — optimal-transport · category/optics · geometry-of-numbers · LLL/probabilistic · interval-exchange · reaction-networks (2026-06-03)

**Wave-3 standouts:** `W3-CA1` (cascade-is-a-lens; PutGet=g1, PutPut=h — **plausibility 5**, probe nearly free),
`W3-GN1` (Ehrhart quasi-polynomial; odd-N-zeros = period 2), `W3-IE2` (de58 = the lone uniquely-ergodic
IET coordinate). New convergences: the **two-condition 2^-2N** now also falls out of LLL's squared
vertex-weight (`W3-LL3`), a covolume-quadrupling-per-round (`W3-GN2`), and a Rauzy two-endpoint
coincidence (`W3-IE3`); **0.74** now also = a Sinkhorn coupling entropy (`W3-OT2`), an Ehrhart leading
coeff (`W3-GN1`), and a KZ Lyapunov exponent (`W3-IE1`).

## Optimal transport & game theory

### W3-OT1 · Cascade as a Brenier map; non-regularity = the 2^-2N cost  `[P3 · cheap]`
- Cascade M1↦M2 is a Monge transport map (μ=forward-reachable, ν=backward-required); it's a valid map to sr=60, but at 61 ν concentrates on a measure-2^-2N set → no map, only a mass-wasting coupling. **lens** optimal-transport · **locus** feed-forward · **mech** lower-bound.
- **probe:** N=6,8,10 histogram μ (push all M1 to boundary) and ν (from collision lists); the per-round mass-concentration ratio should be ≈2^-2N. **kill:** ratio ≠ 2^-2N. **skeptic:** ν defined from collisions → risk of deriving 2^-2N by construction. **≠MITM:** compares two *measures* for a map's existence, never intersects lists.

### W3-OT2 · Sinkhorn coupling entropy = the 0.74 exponent  `[P4 · cheap]`
- The entropic-OT optimal coupling between forward/backward boundary states has entropy ≈0.74·N·log2; carry-HW sets the cost matrix, ε sets the regularization. **lens** entropic-OT/Sinkhorn · **locus** state-cross-section · **mech** count.
- **probe:** build cost C[s_fwd,s_back]=carry-HW (≤1024² at N=10), run Sinkhorn, compute H(π*)/N vs 0.74; the zero-cost support = collisions. **kill:** H/N doesn't →0.74 or no ε-plateau. **skeptic:** cost-matrix choice is a knob — must be the carry-HW one, not tuned. **≠MITM:** a scalar entropy of a dense doubly-stochastic matrix, not a match list.

### W3-OT3 · Kantorovich potential whose gradient IS the cascade  `[P3 · cheap]`
- Duality gives forward/backward potentials φ,ψ; the tightness set φ⊕ψ=C = collisions, and the claim ∇φ = the cascade map (collisions = level sets, not points). **lens** Kantorovich-duality · **locus** whole-function · **mech** structural-invariant.
- **probe:** solve the small-N OT LP for φ,ψ; does the c-transform argmax reproduce the cascade map on enumerated collisions? **kill:** disagrees on >20%. **skeptic:** duality always exists; the content is φ=cascade. **≠MITM:** a scalar field + a gradient identity, no search.

### W3-OT4 · The HW~74 plateau is a Nash equilibrium  `[P4 · cheap]`
- Two players (M1,M2), payoff −HW(output diff); the cascade = best-response dynamics; the plateau = a strict Nash where no 1-bit flip lowers HW, and the 132 hard-core bits = the locked coordinates. **lens** game-theory/Nash · **locus** differential-trail · **mech** reframe.
- **probe:** N=8,10 greedy 1-bit best-response from random starts; is there a sharp terminal-HW mode? locked-bit fraction ≈0.52? does a 2-bit move escape (proving it's a unilateral trap)? **kill:** no mode, or locked-fraction ≠0.52, or 2-bit doesn't beat 1-bit. **skeptic:** plateau could be a pure binomial floor. **≠MITM:** a fixed-point/basin analysis, no intersection.

### W3-OT5 · Collision = stable matching; sr=61 = loss of the Hall condition  `[P3 · cheap]`
- Forward × backward boundary states as a bipartite graph (edge = carry-consistent); a collision = a matched edge; sr=61 = the round the perfect matching (Hall) fails, the 2^-2N = the deficiency. **lens** stable-matching/Hall · **locus** state-cross-section · **mech** count.
- **probe:** N=6,8 build the consistency graph at sr=60 vs 61, Hopcroft–Karp max-matching; does matching size track collision count and deficiency jump by ~2^-2N? **kill:** matching ≠ count, or no deficiency jump. **skeptic:** edge def risks circularity (edge=collision is trivial) — need a *local* carry rule. **≠MITM:** a stable assignment + Hall certificate, can exclude a consistent pair MITM would report.

### W3-OT6 · Rotation constants as a coordination mechanism; N=10 = a focal point  `[P2 · trivial]`
- The σ rotations are a correlation device; N=10 constructive interference = a Schelling focal point where period-N patterns stay phase-locked (rotation 10 ∈ Σ1). **lens** mechanism-design · **locus** message-schedule · **mech** bridge-scales.
- **probe:** collision counts for N=4..14 vs a per-N phase-alignment score of the rotation set; predict the next peak N out-of-sample. **kill:** score uncorrelated with the per-N anomaly. **skeptic:** one bump (N=10) is easy to overfit. **≠MITM:** predicts the *difficulty profile across N*, runs no search.

## Category theory, bidirectional lenses & PL semantics

### W3-CA1 · The cascade IS a lens; sr=61 = PutGet ∧ PutPut both breaking  `[P5 · ~free · HEADLINE]`
- The cascade is a state-based lens (get: recover M1-view; put: correct M2 = `casoff`). The three laws: **GetPut** vacuous (da=0 held), **PutGet** `get(put)=v'` = the `g1=0` per-message value match, **PutPut** = the `h=0` difference compatibility. The repo's *verified* `sr=61 ⇔ g1=0 AND h=0` (independent, ratio 1.005) is identically the textbook split of "very-well-behaved lens" — so `2^-2N` = "drop PutGet lose 2^-N, drop PutPut lose another." **lens** bidirectional-lenses · **locus** round-60→61 boundary · **mech** lower-bound.
- **probe (~1h, numbers already in `gap_rows.csv`):** per-round violation rates of the 3 laws; must partition as {GetPut→0, PutGet→1−2^-N, PutPut→1−2^-N} with the two 2^-N's on *distinct* laws, and P(both|r=61)=P(PutGet)·P(PutPut).
- **kill:** if the rates don't partition cleanly, or both g1,h map to the *same* law (can't explain 2^-2N vs 2^-N), or GetPut shows violations at r≤60. **skeptic:** risk of being a clean *renaming* of g1→PutGet — defended by the falsifiable 3-way partition. **why-not-vocab:** the load-bearing numbers (1−2^-N jump heights, 1.005 ratio) are already measured; wrong partition ⇒ dead.

### W3-CA2 · Delta-lens → why de58 is the lone non-trivial fibre  `[P4 · cheap]`
- A delta-lens acts on *differences*; de57/59/60 constant = identity deltas (the functor sends them to identities), de58 = the unique non-identity image. Functoriality predicts |de58| is the lone DOF. **lens** delta-lenses · **locus** de-register vector · **mech** structural-invariant.
- **probe:** N=8..12 take message triangles M1→M2→M3, check the delta composition law `de_r(1→3)=de_r(1→2)⊕de_r(2→3)` (modular for de58, identity for the constants); count de58's fibre = 2^hw(db56)? **kill:** constants don't compose, or de58 fibre ≠ 2^hw(db56). **skeptic:** modular differences compose additively almost tautologically — the content is *which* register is the generator. **why-not-vocab:** predicts which register, a relabel can't.

### W3-CA3 · Abstract interpretation → the 132 hard-core = a Galois precision loss  `[P4 · cheap]`
- A sound {0,1,⊤} carry abstraction (Galois connection) propagated from the cascade pre-conditions marks exactly the uncontrolled output bits as ⊤ → recovers 132 as a *certified* superset, HW~74 as a provable residual. **lens** abstract-interpretation · **locus** feed-forward/tail · **mech** structural-invariant.
- **probe:** ~150-line 3-valued propagator over masked `add/Sigma/Ch/Maj`, seed da57..=0, de60=0, count ⊤ bits at round 63; must reproduce the 132/124 *partition* (da/db/de/df→⊤, dd/dg/dh→definite). **kill:** marks far more than 132 (too coarse to get dd/dg/dh definite). **skeptic:** risks reinventing BCP — the distinct claim is the soundness *guarantee* (certified superset). **why-not-vocab:** must match 132 *and* the 124 controlled.

### W3-CA4 · Coequalizer / kernel pair; epi–mono factorization localizes collisions to the ADD  `[P3 · cheap, flagged borderline]`
- Collisions = off-diagonal kernel-pair of f; the regular epi–mono factorization f=ADD∘P forces P (invertible) to own 0% of collisions and the ADD 100% — a *categorical theorem* that "collisions are born in the feed-forward." **lens** kernel-pairs/coequalizers · **locus** whole-function/feed-forward · **mech** count.
- **probe:** N=4,6,8 union-find on f-values (the coequalizer); off-diagonal size slope = 0.74 (consistency); **the real test:** kernel-pair(P)=diagonal (P has no slice collisions) while kernel-pair(whole)=kernel-pair(ADD). **kill:** P's kernel pair non-trivial, or slope misses. **skeptic:** kernel-pair size is *definitionally* the count → (a) just re-derives 0.74; only the factorization claim is new (borderline relabel, flagged). **why-not-vocab:** the P-owns-0% check is the falsifiable content.

## Probabilistic method, LLL & designs

### W3-LL1 · LLL slack crossing → the boundary as e·p(d+1)=1  `[P4 · cheap]`
- One bad event per round (individually unlikely-to-fail-given-freedom, sparse dependency from taps {2,7,15,16}); LLL guarantees a collision when e·p·(d+1)≤1. Conjecture: slack <1 through sr=60, ≥1 at 61. **lens** Lovász-Local-Lemma · **locus** schedule dependency graph · **mech** lower-bound.
- **probe:** Monte-Carlo p_i per round (sample free bits *consistent with the cascade prefix*), static d_i from the recurrence, tabulate S(sr)=e·p·(d+1) for sr=58..61; look for the 1-crossing at 60→61. **kill:** no crossing, or p≈1 makes the bound vacuous everywhere. **skeptic:** LLL gives *sufficiency* only; p_i must use the *conditioned* measure. **≠SP:** a single scalar inequality from a static degree count, no message passing/cavity.

### W3-LL2 · Moser–Tardos resampling = a collision-finder that diverges at 61  `[P4 · cheap]`
- Resample any violated round's free bits until consistent; MT's entropy-compression bound says it halts fast when LLL holds. Convergence below 60, divergence at 61, and at convergent rounds the output *is* a collision. **lens** Moser–Tardos · **locus** free message bits · **mech** solve.
- **probe:** ~few-dozen lines; for sr=58..61 run 10³ restarts, plot steps-to-converge (sharp knee at 61?); validate against the entropy-compression runtime from LL1's p_i. **kill:** converges at 61 as readily as 60, or fails even at 58 (mis-specified move). **skeptic:** uniform resampling from the product measure may stall if the collision measure is far from it — calibrate at 58–60 first. **≠SP:** a stochastic walk with a witness-tree bound, no marginals.

### W3-LL3 · Lopsided/cluster-expansion → derives 2^-2N as a Shearer sign change  `[P3 · cheap]`
- The cascade's *negative* round-correlations put it in the lopsided regime; the independent-set (Shearer) polynomial Z's sign = existence. The two-condition round squares a vertex weight (p→p², ≈2^-2N), flipping Z through zero at exactly sr=61. **lens** lopsided-LLL/cluster-expansion · **locus** held-block · **mech** lower-bound.
- **probe:** measure pairwise joints Pr[B_i∧B_j]<p_i p_j (confirm negative correlation), build local Z over a ~5-round window, slide it; Z>0 through 60, ≤0 once the squared-weight sr=61 round enters. **kill:** positive correlations (wrong regime), or Z's sign is truncation-dependent. **skeptic:** Shearer needs the *full* polynomial — local truncation is uncontrolled. **≠SP/additive-comb:** a signed sum over independent sets, no cavity free-energy, no sumset.

### W3-LL4 · Schedule taps as a covering design → collision peaks at design-resonant N  `[P2 · trivial]`
- Read lags {2,7,15,16} as a design block; its difference multiset Δ tiles Z_N; *gaps* in coverage (high non-uniformity) = surviving free directions = collision-rich N (N=10 a coverage gap); the 132 ≈ rotation fixed-point count. **lens** design-theory · **locus** schedule taps · **mech** structural-invariant.
- **probe:** Δ mod N coverage-uniformity score U(N) for N=4..16 vs the collision-count residual (after 0.74N); does N=10 align with a gap? rotation fixed-points ≈132? predict N=18,20 out-of-sample. **kill:** |r|<0.3, or fixed-points nowhere near 132. **skeptic:** linear coverage ignores carries; 13 N-values + 1 bump = easy chance fit. **≠additive-comb/coding:** uses design covering/incidence + the probabilistic existence count, not sumsets or distance.

### W3-LL5 · Second-moment method → 0.74 as a calibrated mean, sr=61 as E[X]<1  `[P3 · ~free]`
- X = #colliding pairs; E[X]≈2^{2N}·2^{-cN} calibrates c to 0.74; concentration (Var/E²→1) says collisions are *typical*; sr=61 = where E[X] crosses 1 (the squared-condition drags the mean below unity). **lens** second-moment-method · **locus** global count · **mech** count.
- **probe:** fit log₂E[X] vs N → 0.74 and c; estimate Var[X] from the exotic-kernel count samples (0,9),(0,14),(0,1); is Var/E² small & N-independent? does calibrated E[X](sr) cross 1 at ~61? **kill:** Var/E² grows with N (no concentration), or E[X] crosses 1 far from 61. **skeptic:** the cascade *forces* shared structure → off-diagonal correlations may be large. **≠SP/spectral:** elementary moments of an indicator sum.

## Interval-exchange, Teichmüller & billiards

### W3-IE1 · Σ-mixing as a 3-IET; 0.74 as a KZ Lyapunov exponent  `[P3 · cheap]`
- Σ0={2,13,22}, Σ1={6,11,25} are rotation-only (no SHR) — three circle-offsets = a 3-IET; round-to-round composition = Teichmüller iteration; the bit-spread rate = the top Kontsevich–Zorich Lyapunov exponent, claimed = 0.74. **lens** IET/KZ-cocycle · **locus** round Σ-maps · **mech** count.
- **probe:** N=4..14 treat the offsets as a 3-IET on the bit-position circle, count periodic orbits (three-distance theorem), fit log(#orbits)/N; compare to the *real* 1-bit diffusion exponent. **kill:** exponent independent of {2,13,22} (random triples give the same). **skeptic:** XOR isn't interval *exchange* — may be a random-walk exponent in IET costume. **≠IIR/transfer-op:** a KZ cocycle growth rate, not a pole or Perron root.

### W3-IE2 · de58 = the unique uniquely-ergodic IET coordinate  `[P4 · cheap · HEADLINE]`
- An IET splits into minimal (equidistributing→growing) + periodic (closing→constant) components. de57/59/60 constant = periodic Rauzy components; de58 = the lone minimal component whose Rokhlin-tower height grows with N (matching the |de58| table). **lens** unique-ergodicity/Masur–Veech · **locus** de-coordinate space · **mech** structural-invariant.
- **probe:** Rauzy–Veech induction on the schedule IET at N=4..14; predict exactly 3 periodic + 1 minimal coordinate (data already matches), and tower-height(N) vs the |de58| growth {1,3,3,4,9,…}. **kill:** induction predicts 0/2/4 periodic, or wrong growth form. **skeptic:** "3 constant 1 grows" is also plain linear algebra (3 linear-determined, 1 nonlinear) — IET may add nothing beyond renaming unless the growth *rate* matches. **≠IIR/transfer-op:** a measure-theoretic component decomposition, no eigenvalue.

### W3-IE3 · sr=61 = a Rauzy fixed point; 2^-2N = a two-endpoint coincidence  `[P3 · cheap]`
- sr-depth = how deep Rauzy induction simplifies before a self-similar fixed point (~60); crossing it needs *two* interval endpoints to coincide (g1=0 AND h=0), each codim-1 → product 2^-2N; predicts sr=62 ~ 2^-3N. **lens** Rauzy renormalization · **locus** sr boundary · **mech** lower-bound.
- **probe:** N=8,10 run Rauzy induction; does it reach a fixed point at the sr-depth, with the two surviving constraints = two distinct endpoints? predict & test the sr=62 rate. **kill:** fixed point at the wrong depth, or the two conditions map to the *same* endpoint (predicting 2^-N). **skeptic:** 2^-2N already explained by coincidence-variety — IET adds nothing unless sr=62=2^-3N confirms. **≠IIR/transfer-op:** a fixed point of the Rauzy *combinatorics* map, not a frequency-domain pole.

### W3-IE4 · Modular add as a billiard; collisions as closed orbits  `[P2 · cheap]`
- A carry/wraparound = a billiard reflection off a 2^i wall; a SHA run = a billiard path in an N-cube; a collision = a near-closed orbit returning to the diagonal; rotation constants = launch angles (rational→periodic→collision-rich). **lens** polytope-billiards · **locus** modular adds · **mech** count.
- **probe:** N=4..10 render carry events as N-cube wall hits, count periodic orbits ≤ length r, compare log(#orbits)/N to 0.74; vary a rotation constant, check collisions track its CF/rational character. **kill:** orbit count and collision count diverge with N. **skeptic:** carry "walls" are data-dependent (non-polygonal) — likely not a real billiard. **≠IIR/transfer-op:** periodic-orbit lengths + angle classification, no transfer function.

### W3-IE5 · Three-distance theorem → the bumpy collision-vs-N features  `[P2 · trivial]`
- {7,18,3},{17,19,10} mod N give ≤3 distinct gaps (Steinhaus); the multiset's CF-transition points predict the discrete jumps in collision multiplicity (the N=10 spike, the |de58| jumps). **lens** three-distance/continued-fractions · **locus** rotation amounts · **mech** structural-invariant.
- **probe:** pure arithmetic N=4..40: gap-multiset + CF-convergents of (amount/N) vs the collision-count and |de58|-jump tables; pre-register the next jump's N. **kill:** no alignment with the empirical jumps. **skeptic:** the most numerology-prone — 3 constants + free combination can fit any bumpy curve; only an out-of-sample prediction counts. **≠IIR/transfer-op:** gap-lengths of a rotation orbit (Ostrowski/CF), no spectral root.

## Geometry of numbers, polytopes & Ehrhart

### W3-GN1 · Collision count = an Ehrhart quasi-polynomial; odd-N-zeros = period 2  `[P4 · cheap · HEADLINE]`
- C(N) = lattice points in a dilated cascade polytope → an Ehrhart *quasi-polynomial*. Odd N → exactly 0, even N grow smoothly = the textbook signature of period 2; the unstable 0.74-vs-1.066 fits = regressing one curve through two parity constituents; 0.74 = log₂ of the leading (volume) coefficient. **lens** Ehrhart-theory · **locus** the exact-count table · **mech** count.
- **probe:** fit a period-2 quasi-polynomial to the exact even-N counts {49→N4? use even} {50,260,946,~2955}; **also** try polynomial-in-u=2^N (the resolution of "exponential vs Ehrhart": then 0.74·N_freebits = an integer dimension d); predict N=14 and check. **kill:** even-N counts fit no fixed-degree polynomial in N *and* no degree-d in 2^N. **skeptic:** 2^0.74N is exponential in N — Ehrhart-in-N needs t=2^N, making 0.74 a fractional effective dimension (the key thing the probe must nail). **≠carry-lifted-lattice:** counts ALL points in a given polytope + fits the count function; never reduces a basis or seeks a short vector.

### W3-GN2 · 2^-2N = the covolume quadrupling per round (Minkowski threshold)  `[P3 · cheap]`
- Each sr-round shrinks the feasible body's volume by 2^-2N (= two independent N-bit slices, the "2"); the sr-boundary is the round its covolume crosses the Minkowski lattice-point-existence bound (R-nonempty but Z-empty). **lens** geometry-of-numbers/Minkowski · **locus** sr transition · **mech** lower-bound.
- **probe:** N=8,10,12 instrument the cascade to count *survivors per round* r=55..61; is survivors(r+1)/survivors(r)≈2^-2N? compute implied covolume and find the Minkowski-crossing round — does it = 60→61? **kill:** per-round factor ≠2^-2N, or predicted r* off by >2 rounds. **skeptic:** modular conditions aren't a convex body — use the constraint *sublattice* covolume; Minkowski gives sufficiency not necessity (an upper bound on the ceiling). **≠carry-lifted-lattice:** computes a covolume scalar feeding an existence inequality, never exhibits a vector.

### W3-GN3 · Reachable-difference zonotope; 132 hard-core = its degenerate directions  `[P3 · cheap]`
- Modular adds are Minkowski sums of segments → output diffs form a zonotope; its *collapsed* directions (cokernel of the generator matrix) = forced/hard-core bits; vol(Z)=Σ|det| = collision density; HW~74 = the L1-radius mode. **lens** zonotopes · **locus** the add chain · **mech** structural-invariant.
- **probe:** N=8,10,12 build the segment-generator matrix G of the masked-add tail; rank(G) & cokernel-dim → tracks 132? enumerate the N=8 zonotope vertices/volume, L1-radius histogram mode ≈74? vol(Z) vs the exact 260? **kill:** cokernel doesn't track the hard-core fraction, or L1 mode ≠ plateau. **skeptic:** carries make generators *data-dependent* (a union of zonotopes over carry cells) — check if *one* zonotope already gives rank-132 or it collapses to the parked carry view. **≠carry-lifted-lattice:** enumerates a bounded polytope's vertices/volume (combinatorial), no basis reduction.

### W3-GN4 · LP integrality gap = the structural-pruning exponent; vertices = extreme collisions  `[P2 · cheap, flagged]`
- Relax the collision IP to an LP polytope P_LP; gap = vol(P_LP)/#integer-points = the "bits of pruning" (0.74 = volume-exponent − gap-exponent); P_LP vertices = extreme collision configs (the N=10 dW[63] hw=1 anatomy is a candidate vertex); sr-boundary = LP-feasible-but-IP-empty. **lens** LP-relaxation/integrality-gap · **locus** the constraint polytope · **mech** reduce.
- **probe:** N=8 lift the mod-2^N cascade constraints to integer+carry vars, form P_LP, compute vol & gap vs 260; fit the gap exponent; enumerate vertices, do they = real collisions (incl. the hw=1 anatomy)? **kill:** gap is O(1) (no exponential gap → subsumed by GN1), or vertices ≠ collisions. **skeptic:** volume-vs-count *is* the Ehrhart object (risks collapsing into GN1); the modular lift touches the parked carry vars — gate on the un-lifted version. **≠carry-lifted-lattice:** drops integrality, computes a continuous hull's volume/gap, no short vector.

## Chemical reaction networks & computational irreducibility

### W3-CR1 · Difference-CRN deficiency → derives 2^-2N as δ=2  `[P3 · cheap]`
- Model one round on a difference-pair as a CRN (species = difference bits, reactions = XOR-flip/carry-birth gates); a collision = the all-zero-difference steady state. Feinberg deficiency δ=n−ℓ−s; conjecture δ=2 at sr-active rounds (the two conditions) → 2^-2N = "2 codimensions × N bits"; δ jumps to 3 at 61. **lens** CRN-deficiency · **locus** per-round difference update · **mech** lower-bound.
- **probe:** N=3,4,5 build the difference-CRN from masked `Ch/Maj/Sigma/add`, assemble the stoichiometric matrix, compute δ; does δ(sr-active)=2 and δ(61)=3, tracking −log₂rate/N? **kill:** δ constant/zero across rounds or unrelated to 2^-2N. **skeptic:** deficiency governs *positive mass-action* steady states; collisions are discrete GF(2) boundary events where the theorems are weakest. **≠Turing/proof-complexity:** δ is one integer from stoichiometric-matrix algebra (no diffusion), predicting the function's rate (no refutation).

### W3-CR2 · The da=0 cascade is a stoichiometric siphon  `[P4 · cheap]`
- A siphon = a species set that, once empty, can never refill (every producing reaction also consumes one in it) — *verbatim* the cascade's "da=0 propagates forward as 0." Minimal siphons + moiety conservation laws (left-nullspace of S) are the invariants the cascade exploits; a *second* siphon may be the leftover tail-gap. **lens** chemical-organization/siphons · **locus** the cascade · **mech** structural-invariant.
- **probe:** N=4..8 compute moiety laws (Smith normal form of S) + enumerate minimal siphons; does the minimal Δa-siphon = the da=0 cascade front bit-for-bit? a second siphon over the tail? conserved-moiety dim vs 132? **kill:** siphons bear no relation to the cascade, or no nontrivial siphon exists. **skeptic:** ± stoichiometry (XOR cancellation) may need an awkward Δ⁺/Δ⁻ split → siphon could be an encoding artifact. **≠Turing/proof-complexity:** null-space + incidence combinatorics, a conserved invariant not a proof.
- *Note:* the reaction-networks agent rates this the lowest-risk wave-3 idea (near-definitional cascade↔siphon match) and it directly attacks the open "is there a better-than-cascade drain?" question.

### W3-CR3 · Computational-irreducibility onset → a compressibility cliff at ~60  `[P3 · cheap]`
- For each round r, P_r(M) = "da=0 admissible at r"; measure the *minimal representation size* of P_r vs r. Reducible early rounds → small circuits; the wall = where size(P_r)/(cost of r rounds) plateaus at ~1 (no shortcut). The XOR-linearized-sr=60-timeout is exactly "the cheapest shortcut fails at the wall." **lens** Wolfram-irreducibility · **locus** the sr boundary · **mech** reframe.
- **probe:** N=3,4,5 truth-table P_r for r=1..R; plot three compressibility proxies (LZMA bytes, decision-diagram node count via existing DD tooling, greedy circuit size) vs r; is there a knee scaling toward 60 as N grows? **kill:** smooth/monotone, no knee, or knee independent of round structure. **skeptic:** "smallest circuit" is uncomputable — proxies measure *a* compressibility; the N=32 knee may be invisible at N=4. **≠proof-complexity:** compressibility of *computing* the function (output shortcut), never refutation size; no diffusion (≠Turing).

### W3-CR4 · Detailed-balance breaking at the feed-forward ADD  `[P3 · cheap]`
- Every round is a permutation = reversible/detailed-balanced; the *one* irreversible 2-to-1 reaction is the Davies-Meyer final ADD — so the entire entropy-production / Wegscheider deficiency is localized there, and the collision baseline = the ADD's fiber multiplicity. **lens** CRN reversibility/Wegscheider · **locus** feed-forward · **mech** structural-invariant.
- **probe:** N=4..8 verify the round-core satisfies detailed-balance (cycle conditions) and that *all* non-detailed-balance concentrates at the ADD; histogram the ADD fiber sizes |{(A,B):A+B≡C}|; does de58 (the lone modular/carry-bearing growing difference) fingerprint this fold? **kill:** entropy production smeared across rounds, or ADD fibers unrelated to the collision baseline. **skeptic:** an invertible permutation has no thermodynamic equilibrium — "detailed-balanced" is a loose reading; `+ mod 2^N` fibers are ~uniform and may hold none of the round structure. **≠Turing/proof-complexity:** steady-state stoichiometric algebra + map-fiber geometry, no pattern, no proof.

### W3-CR5 · Mass-action analog computer → collisions as ODE fixed points, 2^-2N as a codim-2 bifurcation  `[P2 · cheap, flagged]`
- Engineer a mass-action ODE whose positive stable steady states ↔ collisions; #steady-states realizes 2^0.74N, and the codimension of the bifurcation that annihilates them along the round axis = 2 (two zero eigenvalues) realizing 2^-2N. **lens** CRN-multistationarity/bifurcation · **locus** the constraint system · **mech** count.
- **probe:** N=3,4 build the mass-action steady-state polynomial system, count real positive solutions per round (sympy resultants/grid); does the count grow like 2^0.74N and do steady states annihilate in a codim-2 fold near sr=61? run the Jacobian-injectivity test (is multistationarity even possible?). **kill:** injectivity says monostationary (can't encode an exponential count), or count ≠ 2^0.74N, or bifurcations are codim-1. **skeptic:** there's no canonical GF(2)→positive-mass-action encoding — a "match" risks being imposed/circular; the boldest, softest idea here. **≠Turing/proof-complexity:** a well-mixed ODE's steady-state *count* via sign conditions, no diffusion, no refutation.

---

# WAVE 4 — information-geometry · free-probability · lattice-gauge · cellular-sheaf · causal-SCM (2026-06-03)
_(appending as agents return)_

## Information geometry (Fisher–Rao)

**One matrix, three numbers:** IG1/IG4/IG5 share a single object — the pullback Fisher metric of the
output-difference response to input-difference perturbations (`R[k,j]=Pr[flip out k | flip in j]−½`).
Its **corank → 132** (IG1), its **degeneracy-induced stall → 74** (IG4), its **√det-growth exponent →
0.74** (IG5). One ~seconds probe at N=8..14 tests all three. The load-bearing risk (stated once): Fisher
needs a *distribution*, and SHA is deterministic — the whole edifice rests on injecting input randomness
(a Bernoulli "input temperature" ε); if the first probe's corank isn't ≈132, IG1/4/5 fall together.

### W4-IG1 · Fisher corank census → 132 hard-core = the metric kernel  `[P3 · cheap · HEADLINE]`
- Make the input difference a random ε-Bernoulli perturbation → each output bit k has a difference-Bernoulli law; the pullback Fisher metric g=JᵀWJ measures how informatively input directions steer it. Output bits pinned at p=½ for *every* input direction = the metric kernel = conjecturally the 132 hard-core bits (rank-124 informative complement → HW~74). **lens** information-geometry · **locus** differential-trail · **mech** structural-invariant.
- **probe:** N=8..14, B random bases; R[k,j]=Pr[outbit_k(M)≠outbit_k(M⊕e_j)]−½; count output bits with ‖R[k,·]‖≈0 across all j; →132? expected weight of the informative bits →74? **kill:** unsteerable count ≠132 (off >25) or doesn't converge with N, or is highly base-dependent. **skeptic:** single-bit-flip steering ≠ general differential — a bit unsteerable by singletons may be steerable by a pair; rerun with full N-direction rank. **≠control-Gramian/Walsh:** zero Fisher = the *distribution doesn't move* (Hessian-of-KL), strictly stronger than "not reachable"; no transform.

### W4-IG2 · Cramér–Rao floor → 2^-2N as an inverse Fisher volume  `[P3 · cheap]`
- Finding the partner = estimating a latent parameter; the two enforced conditions (g1=0, h=0) are two independent observations whose Fisher informations *add* → a block-diagonal Fisher metric whose √det factorizes into 2^-N·2^-N. The "2" appears because the two blocks are independent (det of block-diagonal = product), and the empirical independence (1.005) becomes a *prediction* of zero cross-Fisher-information. **lens** Cramér–Rao/Fisher-volume · **locus** state-cross-section · **mech** lower-bound.
- **probe:** N=6..14, build the 2×2 Fisher matrix of (C1=g1-diff=0, C2=h-diff=0); check off-diagonal≈0 (independence), det≈(single)², and log₂Pr[both]≈−2N with slope *2*. **kill:** slope ≠ −2, or cross-Fisher-information significantly nonzero. **skeptic:** risks being a dressed-up Pr[A∧B]=Pr[A]Pr[B] — the non-trivial content is *why* the cross-block is structurally zero (g1,h on disjoint carry chains?). **≠control-Gramian/Walsh:** a variance floor from a determinant-of-information-metric, not a reachability rank.

### W4-IG3 · Dual-flatness rupture → the sr-boundary as a Pythagorean defect  `[P2 · cheap]`
- Forward-reachable law P_fwd vs backward-required law P_bwd on the round-r state-difference; the per-round cost = KL projection D(P_bwd‖P_fwd). On a dually flat manifold the generalized Pythagorean theorem makes this clean; the boundary = where the m-geodesic stops meeting the e-flat forward submanifold (dual-flatness breaks), so the cost *jumps* rather than increments. The non-invertible feed-forward is the natural e-flatness breaker. **lens** Amari α-connections · **locus** state-cross-section/feed-forward · **mech** reframe.
- **probe:** histogram P_fwd(r), P_bwd(r) (filter samples by output-collision) in the de57..de60 coords near the boundary; does KL(P_bwd‖P_fwd) *jump* at 60→61? does the Pythagorean identity hold for r≤60 and break at 61? **kill:** KL increases smoothly (no jump), or Pythagoras holds/fails equally on both sides. **skeptic:** P_bwd needs conditioning on collisions (rejection sampling) — sample-starved exactly at the rare boundary; ARX-with-carries almost certainly isn't an exponential family, so Pythagoras may fail on *both* sides (still informative). Weakest of the five. **≠control-Gramian/Walsh:** a relationship between two *distributions* under dual connections, no controllability analog.

### W4-IG4 · Natural-gradient plateau → the cascade IS (Fisher)⁻¹·grad, stalling at Fisher-flat  `[P3 · cheap]`
- The cascade's "zero da first" rule is what natural gradient prescribes (it attacks highest-Fisher-information directions first); it *must* stall where the remaining coordinates (the 132) have zero Fisher information (inverse-Fisher blows up), fixing the residual at HW~74 — unifying the static kernel (132) and the dynamic stall (74). A lower bound on *all* greedy difference-zeroing attacks. **lens** natural-gradient · **locus** whole-function · **mech** reframe.
- **probe:** reconstruct the cascade trajectory; at each step compute the smallest Fisher eigenvalue of the live coordinates; is per-round progress ∝ inverse-smallest-eigenvalue, halting when it →0 at residual HW≈74? does the (Fisher)⁻¹·grad step quantitatively predict the real cascade's da-reduction? **kill:** no correlation between progress and the Fisher spectrum, or the stall HW decouples from the Fisher-flat dimension. **skeptic:** the cascade computes no Fisher matrix — "is natural gradient" needs a *quantitative* step match, not just "both attack steerable directions first." **≠control-Gramian/Walsh:** an optimization *dynamics* preconditioned by the information metric, no static reachable set.

### W4-IG5 · Jeffreys volume → 0.74 as the Fisher–Rao volume-growth exponent  `[P2 · cheap]`
- The number of statistically-distinguishable, output-near-collision input directions = the Fisher (Jeffreys) volume ∫√det(g) of the input-difference manifold; with effective metric-dimension d_eff<N (the IG1 degeneracy), it grows as 2^{cN} with c claimed ≈0.74 — tying 0.74 and 132 to the *same* metric (corank sets degenerate directions, surviving √det-growth sets 0.74). **lens** Fisher–Rao volume · **locus** message-schedule/differential-trail · **mech** count.
- **probe:** N=8..16, build g=JᵀWJ, compute √det restricted to collision-relevant directions (product of nonzero Fisher eigenvalues^½); is log₂V(N) linear with slope ≈0.74? **kill:** slope clearly ≠0.74, or wildly sensitive to ε/weighting (no intrinsic exponent). **skeptic:** deriving a *specific* 0.74 from a volume integral is the most numerology-prone ask; √det of a sampled Fisher matrix is noisy (small eigenvalues dominate det and are worst-estimated) — treat a hit as suggestive only unless robust across N/ε/locus and non-circular with IG1. **≠control-Gramian/Walsh:** Fisher–Rao (Jeffreys) volume on a distribution family, not a reachability-Gramian determinant.

## Free probability & products of random matrices

**Through-line:** the 64-fold round-Jacobian *product* — its singular law via free multiplicative
convolution (⊠)/the S-transform. Top edge → 0.74 (FP1); zero-atom from SHR rank-loss → 132 (FP2);
free-entropy gap → the factor-2 in 2^-2N (FP4). Shared risk: freeness wants large dimension + genuine
randomness, but SHA's Σ-layer is a *fixed* matrix every round — demand *convergence as N grows 4→8*.

### W4-FP1 · S-transform of the 64-fold product → 0.74 as the top singular-edge  `[P3 · cheap]`
- Per-round difference-Jacobians as free factors; product singular law = ⊠ via S_{μP}=∏S_{μi}; its top edge → the 0.74 collision-count edge. **lens** free-mult-convolution · **locus** whole-function · **mech** count.
- **probe:** N=4,6,8 SVD-histogram each per-round Jacobian; predict the product law by ⊠ (30-line S-transform), compare top edge to the *direct* product SVD and to 0.74. **kill:** free vs direct edge differ >15% with no N-convergence, or edge ∉[0.6,0.9]. **≠RMT/Lyapunov:** the whole singular *measure of a product*, not one matrix's eigenvalues or a log-mean Lyapunov exponent.

### W4-FP2 · S-transform zero-atom → 132 from SHR rank-loss  `[P4 · cheap]`
- SHR drops bits → rank-deficient Jacobians → an atom at 0; under ⊠ zero-atoms compound to saturation = the cokernel → conjecturally 132/256. **lens** free-prob atoms · **locus** carries · **mech** structural-invariant.
- **probe:** per-round corank (singular values <ε), combine via the ⊠ zero-atom rule, compare to the *direct* product corank; corank(P)/N → 0.516? removing SHR kills the atom? **kill:** direct corank ≈0 or ≈1, or SHR-removal barely changes it. **skeptic:** over ℝ the add-Jacobian is generically full-rank and may refill SHR's drop — the deficiency may be a GF(2) statement classical free-prob can't see. **≠RMT/Lyapunov:** Lyapunov discards kernel directions; the zero-atom *weight* is exactly what dynamics throws away.

### W4-FP3 · Asymptotic freeness of the ARX layers → the round spectrum factorizes  `[P2 · cheap]`
- If the fixed XOR-rotation layer L and the carry-add layer A are free, μ(AL)=μ_A⊠μ_L → 64 rounds reduce to ⊠ of two alternating laws. **lens** asymptotic-freeness · **locus** round-function · **mech** reduce.
- **probe:** sharp test = one mixed moment (1/N)tr((LA)²) vs the free-prediction from τ(L^k),τ(A^k); does the deviation shrink 4→8? **kill:** deviation doesn't shrink, or μ_{AL}≠μ_L⊠μ_A. **skeptic:** L is fixed & shares the bit-lane geometry with A — SHA's layers are *designed to interlock*, the opposite of free; expect detectable non-freeness (value = quantifying it). **≠RMT/Lyapunov:** a two-subalgebra freeness question, no single-matrix or dynamics analog.

### W4-FP4 · Free entropy → 2^-2N as a free large-deviation rate, factor-2 = two free constraints  `[P2 · cheap]`
- Voiculescu free entropy χ = the LDP rate for atypical product spectra; extending a collision one round forces one more contracted axis; factor-2 = two *free* (independent) spectral constraints each costing one unit. **lens** free-entropy · **locus** state-cross-section · **mech** lower-bound.
- **probe:** depths k=57..61, χ via the logarithmic-energy double sum ∬log|s−t|dμdμ; is Δχ_k constant for k=57/59/60 and jumps at de58, scaling like 2N? **kill:** Δχ unrelated to 2N, or doesn't reproduce de57/59/60-constant-vs-de58-grows. **skeptic:** the N²-LDP is rigorous only for unitarily-invariant ensembles; SHA's product has no ambient invariance — agreement could be a coincidental log-energy fit. Most fragile. **≠RMT/Lyapunov:** χ = logarithmic energy of the whole measure (sees atoms/edges Lyapunov can't); factor-2 from free *independence* has no dynamical counterpart.

### W4-FP5 · Free subordination → why exactly de58 grows  `[P3 · cheap]`
- The ⊠-product's subordination functions ω_i say how much each factor leaks into the product; conjecture only ω_{de58} is mobile while de57/59/60 are pinned — deriving the split from the algebra. **lens** free-subordination · **locus** message-schedule · **mech** structural-invariant.
- **probe:** build the W57..W60 Jacobian columns; compute each subordination function (fixed-point on Stieltjes transforms); is ω_{de58} the only non-flat one, magnitude tracking the 2^10 growth? **kill:** doesn't single out de58 (1-of-4), or magnitude misses the growth law. **skeptic:** 4 factors is far from asymptotic — a 1-in-4 pick could be luck; the magnitude/growth match is the guard. **≠RMT/Lyapunov:** subordination is intrinsic to a *product's* free convolution, foreign to single spectra and to rates.

## Lattice gauge theory (round × bit lattice; carry = gauge connection)

**Through-line:** a Z₂ gauge link on every edge from the local carry-difference; a collision = a flat
connection. Wilson-loop area-vs-perimeter law = the boundary order parameter (LG1); string tension →
2^-2N; Gauss-law source → de58 (LG3); center vortices → the 132 (LG4). Test first: do the carry "links"
transform as a connection `U→g(x)U g(y)⁻¹` under base-message relabeling? else Wilson loops aren't observables.

### W4-LG1 · Wilson-loop confinement → the wall as a deconfinement→confinement transition  `[P3 · cheap · HEADLINE]`
- Horizontal links = carry-difference across bit boundaries; plaquette = frustration; ⟨W(C)⟩ perimeter-law (deconfined, findable) below the wall vs area-law (confined) at 61, string tension σ → 2^-2N. **lens** Z₂-lattice-gauge/Wilson-loops · **locus** round×bit lattice · **mech** lower-bound.
- **probe:** sample colliding-pair ensembles at sr=59/60/61, extract per-column carries (bit-serial `add`), build links; fit log⟨W(a×b)⟩ vs perimeter vs area; perimeter for ≤60, area onset at 61; σ_61 vs 2^-2N. *first verify the gauge transformation law numerically.* **kill:** same law both sides, or ⟨W⟩≈1 everywhere. **skeptic:** the vertical link is an imposed parity — if it doesn't transform as a connection, ⟨W⟩ isn't physical. **≠holonomy(W1-GE2)/Čech(W1-GE1):** a *field* + plaquette action + order-parameter *scaling across loop sizes*, not one loop or a cocycle.

### W4-LG2 · Strong-coupling expansion → 0.74 as a plaquette-tiling constant  `[P2 · cheap]`
- log₂(#collisions)≈(#free links)−(frustration cost); the N-slope = a geometric free-link density = a derived 0.74. **lens** strong-coupling/character-expansion · **locus** whole-function · **mech** count.
- **probe:** N=4..12 count flat-plaquette configs per round-column; predict log₂(#collisions) from geometry alone vs the 2^0.74N data; does the frustration fraction f(r) spike at de58 and round 61? **kill:** slope off >2× with no N-convergence, or f(r) flat. **skeptic:** the Z₂ sum is *constrained* to message-realizable configs — if that constraint sets the count, the field-theory is decoration on enumeration. **≠holonomy/Čech:** a partition function + series → an exponent.

### W4-LG3 · Lattice Gauss law → de58 is the unique charged column  `[P3 · cheap]`
- da=0 clean propagation = ∇·E=0; a forced differential = a source. de57/59/60 constant = source-free, de58 grows = the lone charged column. **lens** Gauss-law · **locus** cascade round-slices · **mech** structural-invariant.
- **probe:** per-round divergence D(r); ≈0 for r∈{57,59,60}, ≠0 growing for 58? linking: collisions force a de58-encircling loop charge-neutral. **kill:** sourced at columns ≠de58, or zero everywhere, or linking vacuous. **skeptic:** must show *locality* (pinned to a column, not smeared) or it's an avalanche; modular-only conservation → group is Z/2^k not Z₂. **≠holonomy/Čech:** the *constraint* (charge-conservation) side, testable as "de58 is the unique charged column."

### W4-LG4 · Center vortices → the 132 hard-core as vortex-pierced plaquettes  `[P3 · cheap]`
- Long carry chains = Z₂ center vortices; the 132 = plaquettes pierced in nearly every collision (topologically pinned → HW~74). **lens** center-vortices · **locus** carries (line defects) · **mech** structural-invariant.
- **probe:** extract carry chains + bit-footprints; small-N hard-core = per-bit variance over collisions; test piercing-correlation *above a carry-density baseline*; vortex free energy = collision-cost of forcing a chain to terminate, area-law only at 61? **kill:** hard-core positions independent of chain footprints (vs carry-density baseline), or no free-energy change 59→61. **skeptic:** without a genuine connection "linking" = "loop crosses chain" (tautology); must beat a *carry-density* baseline. **≠holonomy/Čech:** line defects + an insertion free energy.

## Cellular sheaf theory & the sheaf Laplacian

**Through-line:** a cellular sheaf on the difference computation graph (stalks=GF(2)^N, restriction
maps=linearized round relations); L=δᵀδ. ker(L)=collisions (SH1); dim H¹=132 (SH2); cascade=heat-flow
(SH3); a **rank-2** gap collapse at 61 (SH4); carry-filtration → the true count → 0.74 (SH5). One artifact —
`assemble_delta(N,last_round)` + `eigvalsh(δᵀδ)` — feeds all five. A *linear* sheaf overcounts; test trend.

### W4-SH1 · Sheaf-Laplacian kernel = collision count; spectral-gap collapse = the boundary  `[P3 · cheap · HEADLINE]`
- dim ker(L=δᵀδ) = harmonic difference-sections = the linear collision space; λ₁ = energy of the least-inconsistent non-collision, conjectured to collapse adding round 61. **lens** cellular-sheaf/Hodge · **locus** rounds 57→61 · **mech** count.
- **probe:** N=2,3,4 assemble δ from GF(2) round Jacobians (Σ/σ exact, Ch/Maj linearized, add as XOR), eigvalsh(δᵀδ); does dim ker track the brute-force count? λ₁(60) vs λ₁(61)? **kill:** ker doesn't track the count, or λ₁ doesn't collapse (2×). **skeptic:** linear sheaf overcounts — test predictiveness not equality. **≠Čech(W1-GE1):** an explicit matrix's real spectrum/kernel (`eigvalsh`), a Hodge subspace, not a cocycle on a cover's nerve.

### W4-SH2 · dim H¹ = 132 (hard-core bits = gluing obstructions)  `[P2 · cheap]`
- H¹ = #edges−rank δ = local constraints unsatisfiable by adjusting one stalk; conjecture dim H¹=132 (no global extension → plateau). **lens** sheaf-cohomology · **locus** full round graph · **mech** structural-invariant.
- **probe:** N=2,3,4 dim H¹/dim C⁰ → 0.516? extract the H¹-basis support (ker δᵀ) and correlate with hard-core positions. **kill:** ratio ↛0.51, or support uncorrelated (ρ<0.3). **skeptic:** linear H¹ counts linear obstructions. **≠Čech:** dim H¹ as a coboundary-matrix rank deficiency + a concrete bit-support.

### W4-SH3 · Sheaf diffusion IS the cascade; plateau = a slow non-harmonic mode  `[P3 · cheap]`
- ẋ=−Lx → the harmonic projection (a collision); conjecture the cascade's fixed points (da=0,de60=0) = the harmonic projector, HW~74 = a near-harmonic slow mode (tiny λ₁) — explaining the XOR-linearized timeout (ill-conditioned L). **lens** sheaf-diffusion · **locus** rounds 57→60 · **mech** reframe.
- **probe:** N=2,3,4 project random x(0) onto ker(L); does the limit zero a- and de60-components for free? λ_max/λ₁ already large at sr=60? λ₁-eigenvector HW ≈74/132? **kill:** harmonic projection ≠ cascade fixed points, or L well-conditioned while linearized sr=60 is hard. **skeptic:** linear diffusion → linearized space; true metastable HW may differ. **≠Čech:** a flow with a mixing time set by L's eigenvalues.

### W4-SH4 · Spectral-gap order parameter → a rank-2 degeneration at 60→61  `[P2 · cheap]`
- Sweep last-glued round r=57..62; conjecture λ₁ is O(1) for r≤60 and **exactly two** eigenvalues cross to zero at 61 (g1=0, h=0), localized on the round-61 g/h slots. **lens** Hodge-Cheeger gap · **locus** the tail sweep · **mech** lower-bound.
- **probe:** full spectrum of L_{F_r}, r=57..62; plot λ₁(r), count near-zero modes; predict a drop + *two* new modes at 60→61, localized on g/h. **kill:** λ₁ flat (no anomaly at 61), or new-mode count ≠2 (and ≠2N). **skeptic:** the gap could move at 61 for a trivial one-fewer-free-word reason — eigenvector-localization separates the interesting case. **≠Čech:** a spectral gap is undefinable in the cocycle frame; rank-2 is intrinsically Hodge.

### W4-SH5 · Carry-filtered sheaf → graded H⁰ sheds the overcount, exponent → 0.74  `[P3 · cheap]`
- Grade stalks by carry-order (F⁰=linear, F^k=needs ≥k carries); modular-add restriction raises filtration; dim ker(gr⁰L)=the overcount, higher pieces subtract carry-forbidden directions → dim H⁰ → the *true* count, 0.74 = its growth rate. Fixes SH1's overcount. **lens** filtered-Hodge · **locus** modular-add edges · **mech** count.
- **probe:** N=2..5 dim ker(L⁰) vs dim ker(L¹, +order-1 carry constraints) vs the brute-force count; do carry layers *monotonically decrease* ker toward the true count, log₂/N → 0.74? **kill:** carry layers don't shrink ker toward (or past) the true count, or exponent ∉[0.6,0.9]. **skeptic:** finite filtration truncates the N-deep carry chain; extrapolating 0.74 assumes stabilization. **≠Čech:** a graded Laplacian's per-degree kernel dimensions (an exponent from a Hodge growth rate).

## Causal structural models & do-calculus

**Through-line:** the cascade is *literally* Pearl graph-mutilation (`do(M2=cascade(M1))`); work on the
twin-world *difference* DAG where the feed-forward add is a non-invertible collider, intervening only on
*exogenous* words. 132 = do-orphans (CS1) = counterfactually-rigid bits (CS4); 2^-2N = an identification
order-deficit (CS2); the de58 anomaly = a collider-opened path (CS3).

### W4-CS1 · The 132 hard-core = do-orphans of the cascade mutilation  `[P4 · cheap · HEADLINE]`
- The cascade replaces M2's free edges with M2:=cascade(M1) — exactly Pearl's do()-surgery. A do-orphan = an output-diff bit whose every path in is severed → conjecturally the 132 (124 reachable → HW~74). **lens** SCM/graph-mutilation · **locus** feed-forward collider · **mech** structural-invariant.
- **probe:** small N: run the real cascade; for each output-diff bit + each admissible *exogenous* do(W_j=v), recompute Δout_b; classify reachable vs do-orphan; orphan→132, reachable→124, mean reachable-weight→74? **kill:** orphan count ↛132 (≈0/256) or wildly intervention-set-dependent. **skeptic:** the core is a bijection — non-trivial *only* on the twin-world difference node + *only* under exogenous interventions. **≠Gramian:** counts *severed difference-paths after edge-deletion + a nonlinear collider* (a bit can be Gramian-reachable yet a do-orphan).

### W4-CS2 · 2^-2N = an instrumental-variable identification order-deficit  `[P4 · cheap]`
- sr=61 needs two targets (g1=0,h=0) identified from the residual free words; if the admissible-instrument→target Jacobian has *rank 1* (one exclusion-valid lever), the second is under-identified → 2^-N per missing dimension → 2^-2N. **lens** IV-identifiability · **locus** sr boundary · **mech** lower-bound.
- **probe:** small N: Jacobian ∂(T1,T2)/∂(free words) over levers preserving sr=60; rank over GF(2)/mod-2^N/ℝ; predict rank=1, hit-rate of "both=0" = 2^{-N(targets−rank)}=2^-2N. **kill:** rank=2, or hit-rate exponent ≠ targets−rank. **skeptic:** discrete-Jacobian rank is base-dependent + carries non-smooth (report all three); "preserve sr=60" is a constraint-set not a clean exclusion. **≠Gramian:** counts *exclusion-valid identifying instruments*; the Gramian "reaches" both while confounding them.

### W4-CS3 · The feed-forward collider d-separates the two halves → the de58 anomaly  `[P3 · cheap]`
- out=IV+state_64 is a collider; forcing a collision *conditions* on it, opening a back-door between IV-path and compression-path; round 60 = where the opened path dominates (d-separation breaks), de58 carries it. **lens** d-separation/collider-bias · **locus** feed-forward · **mech** reframe.
- **probe:** small N: MI of forward-half message-diffs vs backward-half state-diffs, unconditional vs conditioned-on-collision, over the M1 ensemble; plot induced dependence vs cut-round (knee at the round-60 analog?); de58 the most collider-sensitive coordinate? **kill:** no round-localized jump, or de58 not special. **skeptic:** on a deterministic core CI-given-output is degenerate — MI must be over the *input ensemble*; massive fan-in may make it all-connected. **≠Gramian:** collider bias (conditioning opens a path between parents) is invisible to forward linear reachability.

### W4-CS4 · Counterfactual rigidity → the plateau as a stable attractor (cross-checks CS1)  `[P3 · cheap]`
- For a found collision, a message bit is *rigid* if do(flip) keeps output-diff HW low; conjecture collisions sit at counterfactually-rigid configs, the output-side rigid set = CS1's do-orphans (132), residual = 74 — a fixed point of the unit-intervention operator. **lens** counterfactuals · **locus** collision manifold · **mech** structural-invariant.
- **probe:** small N: rigid-bit fraction of each collision vs matched random near-miss; elevated for collisions? output-side rigid set → 132 and = CS1's do-orphans? **kill:** no elevated rigidity, or the rigid set unrelated to 132 / disagrees with CS1 (must coincide). **skeptic:** near-perfect avalanche → almost every flip brittle, signal swamped at small N; if rigidity is generic it doesn't single out collisions. **≠Gramian:** a per-solution nonlinear counterfactual, not ensemble-linear reachability — rigidity can hold where the Gramian says "reachable."

---

# WAVE 5 — Krohn-Rhodes · coalgebra · effective-resistance · hypergraph-containers · CAT(0)/systolic · topos (2026-06-03)
_(appending as agents return)_

## Electrical networks & random walks (effective resistance, matrix-tree, commute time)

**Note:** the 132 hard-core bits are a *named* set — the round-63 **recompute-registers** (da,db,de,df +4
dc), which receive a fresh T1+T2; the 124 controllable bits are **pass-through** shift-register slots
(dd,dg,dh = earlier a/e slid down). That recompute-vs-passthrough wiring is the seed for ER1.

### W5-ER1 · Davies–Meyer ground node → 132 = the high-resistance (recompute) registers  `[P4 · cheap · HEADLINE]`
- Make the message-input layer the electrical ground; controllability = 1/effective-resistance-to-ground. Recompute registers are screened from input by the T1+T2 carry-bottleneck (long thin resistor = high R_eff = hard-core); pass-through registers are wired near-directly to earlier a/e (low R_eff). **lens** effective-resistance-to-ground · **locus** round-63 outputs/feed-forward · **mech** structural-invariant.
- **probe:** N=8,10,12 build the round×bit graph (conductance = avalanche sensitivity), L⁺=`pinv`, R_eff(out-bit,ground)=L⁺_uu+L⁺_vv−2L⁺_uv; do the top-132 R_eff bits = {da,db,de,df,+4dc}? AUC vs the known set. **kill:** top-132 overlap ≤ chance (AUC≤0.55) at N=12, or no recompute/pass-through R_eff gap. **skeptic:** R_eff and avalanche-sensitivity may be the same measurement — must show the *network/path* structure (multi-hop screening) beats raw sensitivity column-sums. **≠spectral-graph/Ollivier:** L⁺ *entries* (current-flow distance), not eigenvalues, not an edge curvature.

### W5-ER2 · Matrix-tree spanning-forest count → 0.74 as tree-entropy  `[P3 · cheap]`
- Each collision ↔ a unique carry vector; reinterpret admissible carry assignments as weighted spanning forests of the carry-coupling graph; Kirchhoff counts them as a Laplacian minor det; log₂det ~ 0.74N. **lens** matrix-tree/all-minors · **locus** carries (tail) · **mech** count.
- **probe:** N=4,8,10,12 (known counts 49,260,946,~2955); build the carry-coupling Laplacian (edge weight = local carry-prop probability), `slogdet` of a minor; slope vs N near 0.74? count tracks C (r²>0.9)? **kill:** best-fit slope ∉[0.70,0.78] for ALL physically-motivated weightings, or r²<0.9 on the 4 points. **skeptic:** carries are nonlinear/not XOR-closed — a determinant may be the wrong counting class and hit 0.74 only via a free constant; weights must be fixed *a priori* from carry physics, not tuned. **≠spectral-graph/Ollivier:** a det of a Laplacian *minor* (cofactor), never the eigenvalue list.

### W5-ER3 · Commute-time divergence → the boundary as a resistance blow-up, 2^-2N as two series resistors  `[P3 · cheap]`
- The cascade is a random walk; hitting time to the collision set = 2m·R_eff. Plateau = a high-resistance basin far (in commute time) from any collision; sr=60→61 = cutting the W[60] shortcut, forcing current through *two series resistors* (g1=0, h=0) → commute time *multiplies* (the factor-2 in 2^-2N). **lens** commute-time identity · **locus** the W57..61 lever · **mech** lower-bound.
- **probe:** N=8,10 (enumerable collision sets); single-bit-flip move graph weighted by acceptance; commute-time-to-collision via L⁺ and via short walks; **sub-claim (b):** does removing the W[60] edge *multiply* commute time by ~2^N (not add)? **kill:** commute-time exponent c clearly ≠ 1.26 (|c−1.26|>0.3) at N=8,10, OR removing W[60] changes it sub-exponentially. **skeptic:** "commute time ~ 1/target-density" is generic — only the *series-resistor sub-claim (b)* reproducing the **2** is discriminating; (a) alone is near-tautological. **≠spectral-graph/Ollivier:** L⁺ entries (R_eff×volume), not λ₂/mixing-time.

### W5-ER4 · Foster's theorem audit → the round-60 boundary as a resistance-budget depletion  `[P2 · cheap]`
- Foster pins Σ_edges w_e·R_eff(e) = n−1 (a conserved budget). Conjecture early/mid rounds absorb almost all of it (good diffusion), the tail is starved — and that starvation is the slack the cascade exploits; the boundary = where the cumulative Foster share crosses a threshold (a knee near r≈59). **lens** Foster resistance-sum · **locus** full round graph · **mech** structural-invariant.
- **probe:** N=8,12 full rounds; R_eff(e) from L⁺; verify Foster (a free correctness oracle); plot cumulative Foster share vs round — a knee near 57–59? tail depleted vs mid? **kill:** featureless curve (no knee within ±3 of 59) across N and all conductance choices, or tail not depleted. **skeptic:** Foster pins the *total*, not the *per-round allocation* — "where the budget concentrates" is an artifact of the (tunable) conductance choice unless physics-forced; weakest of the four. **≠spectral-graph/Ollivier:** a trace-of-pseudo-inverse-against-conductances identity (n−c), provable without any eigenvalue; a global edge-sum, not a single-edge curvature.

## Krohn–Rhodes / algebraic automata (transformation-monoid decomposition)

**Through-line:** decompose the round's *transformation monoid* (not its reachability graph) into simple
groups + flip-flops; the cascade's forced da=0 IS a flip-flop reset, so the wall = the first round needing
a non-reset *group* coordinate. The aperiodicity test (KR3) is decidable & cheap and joins the why-60 convergence.

### W5-KR1 · Group-complexity jump → the wall is a +1 in the Eilenberg hierarchy  `[P3 · cheap]`
- Conjecture #G(M_≤r)=0 (aperiodic) for r≤60 and increments at 61; the reversible rounds are the flip-flop part, the feed-forward collision the group part; the 2^-2N = the index of the forced simple group. **lens** KR group-complexity · **locus** round transformation monoid · **mech** lower-bound.
- **probe:** N=2,3 build the round transformation monoid over all W[r]; first round with a nontrivial idempotent-power element (a group element)? predict r=61. **kill:** group element appears at r≤58. **≠carry-automaton:** "which *functions* are realizable by composition" (a divisor/quotient algebra invariant), not state reachability.

### W5-KR2 · Holonomy decomposition → de58's power-of-2 image is a cyclic-group order  `[P4 · cheap]`
- The carry monoid's holonomy groups are tiny/cyclic; de58 is the unique register at the one poset level with nontrivial (Z/2^k) holonomy, k=log₂|de58| — explaining "de58 grows (power of 2), de57/59/60 constant (trivial holonomy)." Anchored to the measured power-of-2 de58 images. **lens** Zeiger holonomy · **locus** carry monoid / de58 · **mech** structural-invariant.
- **probe:** build the N-bit adder carry monoid, compute holonomy group factors (cyclic?); cross-check de58 image = product of holonomy orders along the de58 add-path, and candidate-image disjointness = coset structure on existing N=32 sweep data. **kill:** holonomy groups non-cyclic at N≥6, or de58 image not a power of 2 at N=8..14. **≠carry-automaton:** the *group of subtile permutations* (representation-theoretic), invisible to width counts.

### W5-KR3 · Aperiodicity threshold → star-free (FO-definable) below 60, group-bearing at 61  `[P4 · cheap]`
- Schützenberger: aperiodic syntactic monoid ⟺ star-free ⟺ first-order. The cascade to 60 is pure local pattern-matching (per-round resets) = star-free; round 61's two coupled non-local conditions need "remember-and-compare" = a group/counter. A *descriptive-complexity* characterization of the wall, and it explains why local/linearized methods plateau at 60. **lens** Schützenberger aperiodicity · **locus** the da=0 diff-sequence language · **mech** reframe.
- **probe (the cheapest, decidable):** N=2,3,4 build the syntactic monoid of L_r={diff-sequences keeping da=0 through r}; test x^{|M|}=x^{|M|+1} (aperiodic?) for r=57..61; predict a clean True→False flip at 60→61, invariant across several base states. **kill:** non-aperiodic at r≤58, or still aperiodic at 61, or flickers per-message. **≠carry-automaton:** a property (an identity) of the canonical *syntactic monoid*, presentation-independent; the reachability tool can't even express "is this language star-free."

### W5-KR4 · Wreath-length / first group factor → the hard part is one localized group gate  `[P3 · moderate]`
- KR coordinatizes the tail map into a flip-flop cascade with group factors at specific levels; conjecture the first group factor appears at round 61, sits at the top level, has order m (≈4 = two conditions×2). Gives a *constructive* circuit whose one group gate is the precise hard part. **lens** KR wreath coordinatization · **locus** accumulated tail transform · **mech** lower-bound.
- **probe:** N=2 build T_r tables, holonomy-coordinatize (or the Green's-relations group-J-class lower bound); does γ(r) jump 0→1 at 61, m relate to 2^-2N? **kill:** γ≥1 at r≤59, or γ(61)=0, or m a huge prime. **≠carry-automaton:** a hierarchical wreath factorization (tower of semidirect products), not a flat reachability table.

### W5-KR5 · Group kernel → all group complexity localizes to the feed-forward ADD  `[P2 · cheap]`
- The whole-compression monoid's maximal group quotient G(M) = the feed-forward translation group ⟨H_in+·⟩, with the 64 reversible rounds in the aperiodic kernel — the algebraic form of "collisions born in the ADD"; would say hardness is *constant in round count*. **lens** Type-II / Ash kernel · **locus** whole-function · **mech** structural-invariant.
- **probe:** N=2,3 compute G(M) of full compression (J-class/group-H-class route); = the feed-forward group alone? rounds-only G trivial? **kill:** rounds-only (no feed-forward) has a nontrivial group quotient (a valuable negative — rotations carry group complexity). **≠carry-automaton:** the maximal-group-image (homomorphic images in groups), uncomputable from reachability.

## Coalgebra, bisimulation & coinduction

**Through-line:** the round as a coalgebra; collisions as *behavioral* (coinductive) equivalence, not
reachability. The carry makes next-diff depend on the absolute state → the *backward/observational* quotient
genuinely differs from the repo's already-killed forward Myhill-Nerode. Up-to-context = message modification.

### W5-CO1 · Backward bisimulation quotient → routes around the killed forward Myhill-Nerode  `[P3 · cheap]`
- Forward reachability-quotient is near-injective (255/260, killed). Run partition-refinement *backward* from the ds=0 sink under observational equivalence; the surviving non-singleton block = the colliding basin, a greatest-fixpoint object the inverse (non-invertible) feed-forward makes genuinely merge. **lens** bisimulation/Paige-Tarjan (backward) · **locus** the tail · **mech** reduce.
- **probe:** N=4,8 backward refinement from ds=0; does the surviving block track the count (260 at N=8) and *collapse to singletons at sr=61 but stay fat at sr=60*? **kill:** collapses to singletons at *both* (no richer than the killed forward quotient). **≠carry-automaton:** greatest-fixpoint coinductive quotient under observational equivalence, not forward reachability.

### W5-CO2 · Hennessy–Milner → the 132 = the minimal distinguishing-formula set  `[P3 · cheap]`
- Bisimilar states satisfy the same modal formulas; the 132 hard-core bits = the irreducible distinguishing formulas (the cofree observations) no message-move can equalize; HW~74 = where the distinguishing set saturates. **lens** coalgebraic modal logic · **locus** 256 output bits · **mech** structural-invariant.
- **probe:** N=8 greedily select output-bit modalities separating collisions from non-collisions; does the set = the empirical hard-core bits (Jaccard) and its fraction track 132/256? **kill:** Jaccard<0.3 or fraction doesn't track across N. **skeptic:** risks being a bit-influence skin (near banned Walsh) — must show the *modality* structure beats a flat influence ranking. **≠carry-automaton:** a logic of observations + the HM characterization, no reachability.

### W5-CO3 · Up-to-context bisimulation → message modification, and why it's unsound at 61  `[P4 · cheap]`
- Wang-style message modification IS bisimulation-up-to-context (the free word = the "context" re-closing da=0). The closure is *sound* through 60 (4 free context-moves) and becomes *unsound/inapplicable* at 61 (W[61] schedule-fixed → no context move) → the bare relation pays 2^-2N. The wall = the soundness boundary of an up-to enhancement. **lens** Sangiorgi up-to-context · **locus** the cascade · **mech** lower-bound.
- **probe:** N=8 compare bare vs up-to-context bisimulation relation-size to certify the basin at sr=60 vs 61; up-to-context shrinks it ~2^N per free word at 60, zero at 61? **kill:** same shrinkage at 61 as 60, or none even at 60. **skeptic:** "free word helps" is near-tautological — the 2^N-per-word *quantitative* prediction is the discriminator. **≠carry-automaton:** an enhancement of the coinductive proof method, no automata counterpart. (Ties to the block2_wang bet.)

### W5-CO4 · Final coalgebra → collision count as fiber sizes; power-of-2 quantization  `[P2 · cheap]`
- The behavior map to the final coalgebra; collisions = its fibers; image size = 2^(domain−0.74N). The sharp test: are fiber sizes *quantized to powers of 2* (already weakly observed) — a bisimulation-class regularity a random oracle lacks? **lens** final coalgebra · **locus** whole-function · **mech** count.
- **probe:** N=8,10 fiber-size histogram of the behavior map; mean ≈2^0.74N, and is it power-of-2-quantized vs a Poisson null? **kill:** indistinguishable from the random-oracle Poisson. **skeptic:** "fibers=collisions" is true of any function — only the quantization-as-bisimulation-phenomenon earns it. **≠carry-automaton:** the *terminal* object (all behaviors), dual to reachability.

## Extremal set theory — hypergraph containers & sunflowers

**Through-line:** the collision *set family* — count it by containers (0.74), find its sunflower core (132),
its VC-dimension, its de58 petal. HC2/HC5 are near-confirmatory given the measured 42%-carry-invariance and
de57/59/60-constant facts. Shared primitive: enumerate the small-N collision family once.

### W5-HC1 · Container exponent → 0.74 as a container-packing size  `[P3 · cheap]`
- Collisions = independent sets of a sparse "conflict hypergraph" on the 4N free bits (edges = minimal cascade-violating patterns); the container method packs all of them into few containers of size ≤2^{cN}, with c=0.74. **lens** hypergraph containers/supersaturation · **locus** free-word block · **mech** count.
- **probe:** N=4..12 enumerate collisions, build H empirically (minimal forbidden bit-patterns), compute its degree distribution + the predicted container exponent vs the measured slope. **kill:** H has unbounded co-degree (no container bound) or predicted exponent off >0.1 from the slope. **skeptic:** containers are *upper* bounds; matching an exact count needs a supersaturation lower bound. **≠additive-comb/coding/LLL:** counts independent sets by *degree structure*, no sumset/distance/existence-threshold.

### W5-HC2 · Sunflower core → the 132 as the bits common to all collisions  `[P4 · cheap]`
- The Sunflower Lemma forces a common core; conjecture the 132 hard-core bits = the carry-difference core shared by ~all collisions (the petals = the free 124). Anchored to the measured 42% carry-invariance (0.42·256≈108, a testable near-miss to 132). **lens** sunflower/Δ-system · **locus** carry-difference supports · **mech** structural-invariant.
- **probe:** N=8,10,12 intersect all collisions' carry-diff supports (= empirical core); is it a stable fraction → 132/256? are residual petals low-overlap (disjoint-ish)? **kill:** core fraction unstable across N, petals high-overlap, or extrapolated core misses 132/256 by >15%. **≠additive-comb/coding/LLL:** the literal set-intersection structure of a family.

### W5-HC3 · Frankl shifting → HW~74 as a compressed-family extremal weight  `[P2 · cheap]`
- Combinatorial shifting compresses the collision family without changing size; conjecture 74 is the shift-invariant extremal weight (structural, not a thermodynamic floor). **lens** compression-shifting · **locus** message-diff bit-vectors · **mech** structural-invariant.
- **probe:** N=8,10 implement S_{ij} (flip iff still a collision), iterate to fixed point; is the family even shiftable, and is max-HW preserved at the per-N hard-core fraction? **kill:** family is shift-rigid (no admissible shifts → idea dead), or max-HW not preserved. **skeptic:** crypto families are notoriously not down-closed — this is a go/no-go on shiftability. **≠additive-comb/coding/LLL:** a structure-canonicalization (shadow/weight profile).

### W5-HC4 · VC-dimension → 0.74 and 132 as two faces of one Sauer–Shelah quantity  `[P3 · cheap]`
- The collision family as a concept class; forced coordinates (never shattered) = the 132 hard-core bits; VC-dim d gives #collisions via Sauer–Shelah, so log-count≈d·log(4N/d)=0.74N solves for d. **lens** VC/Sauer–Shelah · **locus** 4N free bits · **mech** count.
- **probe:** N=4..10 count forced coordinates (→132/256?), find the largest fully-shattered subset (VC-dim), plug into Sauer–Shelah vs the actual count. **kill:** forced-coordinate count doesn't track 132/256, or Sauer–Shelah count wildly off with no N-trend. **skeptic:** Sauer–Shelah is an *upper* bound (rarely tight) — a "predicted" 0.74 may be coincidental. **≠additive-comb/coding/LLL:** combinatorial richness of projections (realizable patterns), the dual of distance reasoning.

### W5-HC5 · de58 single-petal → why only de58 grows, and the count decomposition  `[P4 · cheap]`
- de57/59/60 constant = a frozen 3-coordinate sunflower core; de58 = the unique petal coordinate; |de58|~2^{0.31N} is the petal exponent, and petal-exponent + fiber-exponent should ≈0.74. Mostly *names* an observed fact correctly + tests the count split. **lens** Δ-system core/petal · **locus** de57..de60 · **mech** count.
- **probe:** N=8..14 confirm de57/59/60 single-valued, tabulate the de58 petal set (log/N → petal exponent) and fiber sizes (→ fiber exponent); does the sum ≈0.74? **kill:** core leaks (de57/59/60 not constant), or petal+fiber exponents don't sum to the slope (±0.1). **≠additive-comb/coding/LLL:** a coordinate core/petal partition counted by petal-set + fiber size.

## Hyperbolic / systolic / CAT(0) geometry (the assignment cube complex)

**Through-line:** build a cube complex on partial cascade assignments; CAT(0) (Gromov's flag/link condition)
up to 60 = unique-geodesic descent (= the cascade), and an **empty square** (g1 ⊥ h, codim-2) at 61 breaks it
— *deriving the 2^-2N from a non-flag codimension*. Shared `build_cascade_complex(N,last_round)` feeds all six.

### W5-HY1 · Empty square at 61 → CAT(0) link failure, codim-2 = 2^-2N  `[P4 · cheap · HEADLINE]`
- Two extensions (g1=0, h=0) individually extendable but jointly unfillable = the textbook empty-square (non-flag link) that destroys CAT(0); its codimension is exactly 2 → 2^-N per condition, 2^-2N joint, from a codimension count not a fit. **lens** Gromov link condition · **locus** cascade complex 60→61 · **mech** lower-bound.
- **probe:** N=4,5,6 build the cascade cube complex, per round run the flag test (compatible edge-pair ⇒ filled square?); empty-square count =0 for ≤60, jumps at 61 with codimension 2, slope −2N? **kill:** empty squares appear before 61, or 61's link stays flag, or codim≠2. **≠Ollivier/PH:** a yes/no combinatorial link test on named vertices, not an edge-curvature average or a barcode.

### W5-HY2 · Systole → the minimal collision differential as the shortest essential loop  `[P4 · cheap]`
- The feed-forward gluing turns the descent tree into a complex with π₁; a collision = a non-contractible loop; the minimal-HW collision = the systole (the N=10 HW-1 boundary word is a short-systole datum). **lens** systolic geometry · **locus** difference complex + feed-forward · **mech** count.
- **probe:** N=6,8,10 shortest essential cycle (crosses the feed-forward gluing oddly) by weighted BFS; does it = the known minimal-HW collision at N=10? #short essential classes vs 2^0.74N? **kill:** systole ≠ the N=10 minimal collision, or essential loops exist without the feed-forward gluing. **skeptic:** "essential" needs a strict gluing model or everything is a loop. **≠Ollivier/PH:** one shortest-loop length, not a curvature or a persistence interval.

### W5-HY3 · δ-hyperbolicity → collisions rare & rigid; de58 = the tree axis  `[P3 · cheap]`
- Thin-triangle hyperbolic difference graph ⇒ unique geodesic corridors ⇒ rigid, rare collisions; 132/HW~74 = sphere-concentration; de58-grows/others-constant = a tree-graded structure with de58 the branching axis. **lens** Gromov δ-hyperbolicity · **locus** global difference metric · **mech** structural-invariant.
- **probe:** N=4,6,8 4-point δ test; does δ/diameter stay bounded as N grows (hyperbolic vs flat)? is branching concentrated on de58? **kill:** δ grows with diameter (flat), or branching not on de58. **skeptic:** finite graphs are trivially hyperbolic — report δ/diameter trend, not raw δ. **≠Ollivier/PH:** a global thin-triangle Gromov-product scalar, not an edge curvature or barcode.

### W5-HY4 · Cascade diagonal = the CAT(0) geodesic; the wall = geodesic non-existence  `[P4 · cheap]`
- Theorem-1's da=0 diagonal IS the unique normal-cube-path geodesic through the flat 4-cube of the (commuting) free rounds — *why* the cascade deterministically works to 60 (CAT(0)⇒unique geodesics); at 61 the two required hyperplanes don't co-bound a cube → no geodesic continuation. Dual to HY1. **lens** normal-cube-path/unique-geodesic · **locus** the da=0 matrix · **mech** reframe.
- **probe:** N=4,5,6 encode free rounds as hyperplanes, test pairwise commutation (flat 4-cube?), cascade path unique?; at 61 no co-bounding cube? Theorem-2 (de60=0 ∀ messages) as a free hyperplane. **kill:** free rounds not pairwise-commuting, or cascade non-unique at ≤60, or the 61-move finds a co-bounding cube. **≠Ollivier/PH:** path/hyperplane-crossing machinery, no curvature average or homology.

### W5-HY5 · Boundary-at-infinity → the 132 as the Gromov boundary, HW~74 as its visual sphere  `[P3 · cheap]`
- The 132 hard-core bits = geodesic rays escaping to ∂X (non-relaxable directions); HW~74 = the visual-sphere radius; the sharp 132/124 split + a scale-invariant ratio = a boundary-dimension constant. **lens** Gromov boundary · **locus** asymptotic difference graph · **mech** structural-invariant.
- **probe:** N=4,6,8 classify each output coordinate as escaping (always forced) vs bounded; do boundary-bits/total and plateau-HW/total *converge* with N (vs drift)? **kill:** no sharp dichotomy (smooth gradient), or ratios drift with N. **skeptic:** plateaus also arise from plain concentration — pair with an independent δ-hyperbolicity confirmation (HY3). **≠Ollivier/PH:** an asymptotic large-scale invariant (rays at infinity), not a local curvature or barcode.

### W5-HY6 · Special-cube hyperplane osculation → carries as the sole specialness obstruction  `[P3 · cheap]`
- Haglund–Wise specialness forbids hyperplane self/inter-osculation; XOR-only walls are special (clean CAT(0)), and *carries* (the only nonlinearity) make walls osculate — localizing nonlinearity to a named pathology with a measurable osculation depth (a finer cut than round 61). **lens** special cube complexes · **locus** carry hyperplanes · **mech** structural-invariant.
- **probe:** N=4,5,6 run specialness checks (self-crossing/osculation/inter-osculation) per round; carry-off (XOR-linearized) control → walls embedded/non-osculating? first osculation depth vs carry-chain length, vs the sr=61 empty square? **kill:** osculation even in the carry-free model, or none up to the wall, or depth unrelated to carry length. **skeptic:** must run the carry-on/off control or "osculation" is relabeled adjacency. **≠Ollivier/PH:** discrete wall-embedding predicates, no averaging, no filtration.

## Topos theory, categorical logic & forcing

**Through-line:** the collision predicate's *truth value* in the Heyting Ω (not {0,1}). TO2 is anchored to a
number the repo already has: the 1.005 independence ratio = the failure-of-factorization of a meet in Ω, so
2^-2N = μ(U_A)·μ(U_B). The wall = a forcing/genericity threshold (TO1); the 132 = the LEM-failing bits (TO3).

### W5-TO1 · Forcing threshold → collision is a dense open through 60, nowhere-dense at 61  `[P3 · cheap]`
- On the poset of partial-consistent assignments, Φ="extends to a collision" is *forced* (dense-open below p) for r≤60 and becomes *nowhere-dense* at 61; the residual open measure = 2^-2N; the ¬¬-vs-actual gap = "no obstruction ≠ constructible." Explains why XOR-linearization still times out (it preserves which extensions are refuted). **lens** Kripke–Joyal forcing · **locus** the boundary · **mech** reframe.
- **probe:** N=6,8,10 forcing-density δ_r(p) = fraction of children still forcing Φ; plateau (dense) for ≤60, crash to ~0 at 61? δ_61/δ_60→0 like 2^-2N? **kill:** δ_r smooth/monotone (no knee at 61), or the ¬¬-gap is empty everywhere (Ω Boolean → framing buys nothing). **≠sheaf-Laplacian/Čech:** a sieve-measure in Ω (a forcing relation ⊩), no complex/coboundary/spectrum.

### W5-TO2 · Heyting-meet measure → 2^-2N as μ(U_A)·μ(U_B), anchored to the 1.005 ratio  `[P4 · cheap]`
- The two sr=61 conditions are two opens U_A={g1=0}, U_B={h=0} in Ω; the collision truth value is the meet U_A∩U_B, whose measure factors as 2^-N·2^-N *iff* the opens are independent — which is exactly the measured ratio 1.005. The deviation of ρ_r from 1 across rounds = a *map of which conditions share a carry chain* (a lever). **lens** subobject-classifier Ω (Heyting meet + measure) · **locus** sr=61 · **mech** lower-bound.
- **probe:** Monte-Carlo ρ_r=μ(A∧B)/(μ(A)μ(B)) per round; ≈1.000 at the 61-analog (→2^-2N), departs from 1 where conditions share carries? **kill:** ρ_r≈1 for *every* round (independence generic, no fingerprint), or ρ noisy/unstable. **skeptic:** the round-dependence of ρ−1 must predict known carry-sharing or the topos dressing is inert. **≠sheaf-Laplacian/Čech:** a measured Heyting meet (product-of-measures), not orthogonality of cochains or a gluing cocycle.

### W5-TO3 · Non-Boolean Ω → the 132 = the LEM-failing (undecided) bits  `[P3 · cheap]`
- A bit is LEM-failing at a stage if neither value is forced (¬¬ true but not constructible); conjecture the 132 hard-core bits = the deep-decidability bits (undecided until almost-full input, because the non-invertible feed-forward mixes them through all-input carries); HW~74 = the uniform measure on the undecided coordinates. **lens** intuitionistic internal logic (LEM failure) · **locus** 132 bits/feed-forward · **mech** structural-invariant.
- **probe:** N small: per output bit, decidability depth d(b) = smallest input-prefix forcing it; bimodal histogram (shallow=LEM holds vs deep=LEM fails)? deep-cluster fraction →0.52, expected HW→74? toggle feed-forward→XOR: deep cluster shrinks? **kill:** d(b) unimodal/continuous (no Boolean/non-Boolean split), or invertible feed-forward doesn't shrink the deep cluster. **≠sheaf-Laplacian/Čech:** per-proposition p∨¬p=⊤? facts in a Heyting algebra, no Laplacian or cocycle.

### W5-TO4 · Sheafification gap → locally-consistent fragments that fail to glue, blowing up at 61  `[P3 · cheap, best fan-out]`
- On a round-window site, local sections = collision fragments (presheaf F); the sheaf F⁺ keeps only those that glue to a global collision; the gap |F|−|F⁺| is small through 60 and blows up at 61 (many locally-consistent fragments disagree on the g1∧h overlap); 2^-2N = the gluing-success rate there. **lens** sheafification (gluing-axiom failure) · **locus** round-windows · **mech** count.
- **probe:** enumerate local sections per round-window, count matching adjacent pairs and the fraction that extend to a global collision (gluing rate g_i); does g_i drop sharply at the 61-window, un-gluable count ~2^-2·width? control: a linear toy has g_i≈1 throughout. **kill:** g_i smooth/featureless across rounds, or un-gluable count doesn't scale like 2^-2N. **≠sheaf-Laplacian/Čech:** a set-theoretic |F|−|F⁺| (raw fragment gluing rate), not a cohomology quotient or a Laplacian.

### W5-TO5 · Geometric morphism → MITM as a functor that loses faithfulness at the wall  `[P2 · cheap, touches mitm_residue bet]`
- The cascade/MITM join is a geometric morphism Sh(B)→Sh(F); an embedding (f* full+faithful) through 60 (each backward residue pins a unique forward continuation) loses faithfulness at 61 (distinct backward states share a forward image); the generic fiber size = the MITM blow-up = reciprocal 2^-2N. **lens** geometric morphism / faithfulness · **locus** the MITM split · **mech** structural-invariant.
- **probe:** sweep the split round m; mean |f*-fiber| (backward preimages per forward image) = 1 (faithful) for ≤60, jumps to exp ~2^(2·width) at 61? control: a linear toy stays size-1. **kill:** fibers fat well before 61, or grow smoothly (no faithful→unfaithful transition), or stay size-1 past the wall. **skeptic:** the most topos-cosplay-prone — keep only if the fiber-jump is sharp. **≠sheaf-Laplacian/Čech:** faithfulness/fiber-size of an inverse-image functor, not a complex or spectrum. (Touches the live mitm_residue bet.)

---

# WAVE 6 — Pontryagin optimal-control · o-minimality · matroid/Tutte · IFS/fractal (2026-06-03)
_(appending as agents return)_

## Optimal control — the Pontryagin Maximum Principle

**Through-line:** the cascade IS a control law (W2[r]=W1[r]+offset(r) steering the difference-state to 0
over a 64-step horizon). The Pontryagin costate λ_r (backward adjoint) + Hamiltonian switching function give:
the wall as a **singular arc** (OC1), 2^-2N as a **codim-2 singular surface** (OC2), the 132 as the **costate
kernel** (OC3). One ~40-line helper (forward trajectory + finite-diff Jacobians + backward costate λ_r=J_rᵀλ_{r+1}
+ switching function s_r) powers all five; runs in ms at N=8. Caveat: over Z/2^N these are finite-diff proxies.

### W6-OC1 · The wall is a singular arc → ∂H/∂u dies at round 61  `[P4 · cheap]`
- The control dW[r] enters T1 additively, so H is affine in u → the optimal cascade is bang-bang (the unique offset) for r≤60; at 61 the control isn't free, so the switching function s_61=λ_{62}ᵀ(∂F/∂u) collapses on the feasible cone → a singular arc → no unique steering. **lens** Pontryagin/singular-control · **locus** message-schedule · **mech** reframe.
- **probe:** N=8,10 compute s_r=λ_{r+1}ᵀ(∂F_r/∂u_r) for r=57..63 (project ∂F_61/∂u onto the schedule-feasible dW[61]); is ‖s_r‖ full-width for ≤60 and ≈0 at 61? **kill:** ‖s_61‖ same order as ‖s_60‖ (no collapse). **skeptic:** mod-2^N carry kinks make ∂/∂u set-valued — a discrete proxy, and the collapse could just restate "W[61] isn't free." **≠control-Gramian/LQR:** the costate + Hamiltonian switching function (backward adjoint), not a reachability rank or Riccati cost.

### W6-OC2 · 2^-2N = the codimension of the singular surface (two conditions, one control)  `[P4 · cheap]`
- h=0 (the singular-surface/∂H/∂u condition) and g1=0 (the endpoint transversality condition) are two functionally-independent scalars; one control dW[61] can't satisfy both → the BVP is overdetermined by codim 2 → 2^-2N. Predicts: +1 control DOF drops it to 2^-N. **lens** TPBVP transversality + singular surface · **locus** feed-forward/schedule · **mech** lower-bound.
- **probe:** N=8,10,12 compute the constraint normals n_h=∂h/∂control, n_g=∂g1/∂control; are they linearly independent (codim 2, matching the 1.005 ratio)? then unfreeze a second tail word → density 2^-2N→2^-N? **kill:** n_h ∥ n_g (dependent → not codim 2), or +1 control doesn't move density toward 2^-N. **skeptic:** independence is already measured (1.005) — the new content is the codim geometry + the +1-control prediction. **≠control-Gramian/LQR:** counts *simultaneous endpoint constraints vs control DOF*, which a rank-Gramian can't distinguish (codim 1 vs 2).

### W6-OC3 · The 132 hard-core bits = the costate's kernel  `[P4 · cheap]`
- A final bit with zero costate support is a direction Pontryagin can't steer to first order (flat Hamiltonian gradient); conjecture the 132 = ker of the pulled-back costate map (da,db,de,df at r63), zeroed only by 2nd-order carry effects; HW~74 = kernel-dim/2 + small. Joins the corank cluster. **lens** costate sensitivity · **locus** round-63 outputs · **mech** structural-invariant.
- **probe:** N=8,12 build S[bit,(r,j)]=∂(final bit)/∂(dW[r] bit j) by finite differences; do the all-zero rows concentrate in da,db,de,df (the 132) and predict the plateau HW from kernel-dim/2? **kill:** zero-rows don't match the measured hard core, or kernel-dim/2 mispredicts the plateau beyond noise. **skeptic:** "zero deterministic controller" was single-bit; costate is a linearization — a bit could be costate-supported yet need carries. **≠control-Gramian/LQR:** the *backward costate along the specific cascade trajectory* tells you *which output bits* are flat to the MP's first-order condition; the Gramian gives only a global static rank.

### W6-OC4 · Conjugate point → the costate norm blows up into round 61  `[P3 · cheap]`
- The boundary between "solvable BVP" and "no smooth solution" is a conjugate point, signaled by the control-augmented transition map [J_r|∂F/∂u] becoming ill-conditioned at the free→schedule transition (61), where the dW[61] column drops; ‖λ_60‖ spikes. **lens** conjugate-point/adjoint flow · **locus** differential-trail 57→63 · **mech** structural-invariant.
- **probe:** N=8,10,12 propagate λ_r=J_rᵀλ_{r+1} from λ_63=I; is cond([J_r|∂F/∂u]) moderate for ≤60 and spiking at 61, pinned across seeds and (rescaled) N? **kill:** cond/‖λ_r‖ flat (no spike at 61), or spike location wanders with seed. **skeptic:** condition number of a mod-arithmetic map is a heuristic; the spike may be the near-tautological "fewer columns." **≠control-Gramian/LQR:** a conjugate point = invertibility of the adjoint/transition flow over the horizon, not a static Gramian rank.

### W6-OC5 · Min-effort extremal → dT1_61=0 is the switching surface  `[P3 · cheap]`
- The repo proved collisions reduce to ONE equation dT1_61=0; read it as the switching function s=∂H/∂u of a minimum-effort reaching problem — drive to {dT1_61=0} and bang, then the e-path (de60=0 + shift register) coasts to x_63=0 for free. Collision cost = control effort Σ‖u_r‖; low-HW collisions cluster near the surface. **lens** min-effort/switching-function · **locus** round 61/carries · **mech** solve.
- **probe:** N=8,12 compute dT1_61, control effort E=Σ hw(dW[r]); does a costate/switching-gradient-guided min-effort descent reach a collision in fewer evals than random? **kill:** costate-guided descent no faster than random (true-but-useless = kill by this lab's standard). **skeptic:** dT1_61=0 is already established; the new claim is the *effort metric* + that gradient descent beats random; carry kinks may make the switching gradient a poor descent direction. **≠control-Gramian/LQR:** an L1/Hamming min-effort *bang at a switching surface*, governed by the zero of s=∂H/∂u — the hallmark non-LQR Pontryagin object, no Riccati/Gramian.

## Model theory / o-minimality / tame geometry

**Through-line:** the collision set as a *definable* set; tame (bounded cell-count, NIP, bounded QE-depth)
below 60, *wild* at 61. OM3 is the sharpest: "two independent conditions" IS the literal definition of the
**independence property** (IP), so the wall = an NIP→IP dividing line, with alternation rank as the
thermometer. Reuses one da=0-cascade collision enumerator. (VC/Sauer–Shelah is the *taken* hypergraph wave.)

### W6-OM1 · Cell-count explosion → the wall = loss of uniform finiteness  `[P3 · cheap]`
- Per-round count of "cells" (maximal solution-runs in a fixed coordinate order); bounded (O(1) fat cascade cells) ≤60, explodes at 61 (the two conditions fracture each slice) — the o-minimal signature of a wild set. **lens** cell decomposition / uniform finiteness · **locus** the collision set as a family · **mech** structural-invariant.
- **probe:** N=4,6,8 enumerate da=0 collisions, fix a sweep coordinate, count maximal runs per slice (avg over random coordinate orders) vs round; bounded ≤60, discontinuity at 61? **kill:** already Θ(2^N) for r≤58, or smooth/monotone with no break near 60/61. **skeptic:** run-count is coordinate-order-dependent (a real cell count is intrinsic) — average over orders, report variance. **≠VC:** counts connected components/cells of the set (uniform finiteness), orthogonal to a shatter bound.

### W6-OM2 · Pila–Wilkie → 0.74 as the dimension of the algebraic part  `[P4/3 · cheap]`
- Split collisions into cascade/algebraic (low-degree carry relations, positive-dim families) vs lucky/transcendental; Pila–Wilkie says the off-algebraic points are sub-polynomial, so 2^0.74N is *entirely* the algebraic part → 0.74 = its normalized dimension. **lens** Pila–Wilkie counting · **locus** the full count split · **mech** count.
- **probe:** N=4..10 classify each collision algebraic (de58 follows the linear-propagation law, de57/59/60 constant — a *pre-registered* classifier) vs off-algebraic; fit both log-counts; algebraic slope →0.74, off-algebraic ≪? **kill:** off-algebraic also grows ~2^cN (c not ≪0.74), or algebraic slope ∉0.74±0.05. **skeptic:** "algebraic part" over GF(2) must be defined by hand — the de58 law is the pre-committed split that avoids circularity. **≠VC:** a dimensional/stratification statement (which points carry the mass), inexpressible in Sauer–Shelah.

### W6-OM3 · NIP→IP dividing line → the wall as the independence property  `[P4 · cheap · HEADLINE]`
- "Two independent conditions g1=0 ∧ h=0" is the literal recipe for IP (an AND of independent predicates shatters index sequences); measure alternation rank of R_r(x,y)=[collide] along a structured (cascade-shift) sequence — bounded (NIP, tame) ≤60, blows up (IP, wild) at 61. **lens** NIP/IP, alternation rank · **locus** the 2-coordinate collision relation · **mech** lower-bound.
- **probe:** N=6,8,10 build a cascade-shift progression a_i, fix random b, count sign-changes of R_r(a_i,b); sub-linear & flat ≤60, jump at 61? test several sequence families. **kill:** already ~Θ(m) for r≤58, no upward break at 61, or alternation *decreases* at 61. **skeptic:** every finite relation is trivially NIP at fixed size — only the N-*scaling* of alternation carries content; arithmetic progressions aren't truly indiscernible. **≠VC:** the order/stability face of NIP (alternation along a sequence + a phase transition), not the shatter-function face.

### W6-OM4 · de58 = the unique 1-cell; de57/59/60 = 0-cells  `[P4/3 · cheap]`
- A graded cell decomposition: de58 is the open 1-cell (the family's one free-parameter axis, in the *modular* chart), de57/59/60 are 0-cells (points) — making OM2 mechanistic and explaining *why* de58 is special. **lens** dimension-typed cells + chart choice · **locus** the de-vector · **mech** structural-invariant.
- **probe:** N=4..16 confirm de57/59/60 constant, fit log₂|range(de58)|/N = slope s; does the de58 share of the total exponent ≈ s/0.74? **kill:** a second coordinate varies at large N (>1 cell), or slope(|de58|) unrelated to the count exponent. **skeptic:** mostly re-describes known data — must clear the *growth-matching* prediction or it's vocabulary. **≠VC:** dimension-typing + chart selection, zero VC analog.

### W6-OM5 · QE-depth → the wall as loss of bounded definability / Skolem functions  `[P3 · cheap, disqualify early]`
- Below 60 the cascade gives definable Skolem functions (solve for the carries) → the collision predicate eliminates to bounded depth (short certificate); at 61 no joint Skolem function exists → elimination depth (∝ ANF degree after carry-projection) explodes. Bridges to certificate complexity. **lens** effective QE / definable Skolem · **locus** projected defining formula · **mech** reframe.
- **probe:** N=4,6,8 build the collision indicator as a Boolean fn of the N message bits (eliminate tail by enumeration), ANF degree/sparsity via Möbius vs round; sub-saturated ≤60, degree→N at 61? **kill (run first):** ANF already ≈degree-N for all r≥57 (the repo's "ANF dense" memo is a live threat — run this as a cheap disqualifier). **skeptic:** ANF degree is a loose proxy for QE-depth; lowest-confidence on its proxy. **≠VC:** definitional/projection complexity of the *formula*, disjoint from a set-system shatter number.

### W6-OM6 · 1-D monotonicity → de58 membership: intervals (tame) vs fractal (wild)  `[P3 · cheap, screening]`
- Along the de58 axis, the set of values completing to a collision is a finite union of intervals (tame) ≤60 and a pseudo-random sieve (wild) at 61; the sieve's entropy = the HW~74/132 plateau. The sharpest 1-D o-minimality test. **lens** monotonicity theorem (definable ⊂ line = finite ∪ intervals) · **locus** the de58 1-cell · **mech** structural-invariant.
- **probe:** N=6..12 build s[v]=[de58 value v completes]; run-count + block-entropy/LZ vs round; low ≤60, →maximal at 61? **kill:** entropy already ≈1 bit/symbol for r≤58, or run-count never breaks at 61. **skeptic:** few populated points at small N make interval-structure fragile (need N≥12); an LFSR-like sieve looks random but is tame — screening only, confirm with OM1. **≠VC:** 1-D interval/monotone structure, not a shatter bound.

## Iterated function systems & fractal dimension

**Through-line:** the collision set as an IFS *attractor*; 0.74 = its box-counting dimension, *derived* from
per-bit carry-branching ratios via the Moran equation Σrᵢˢ=1 (FR1 — the real non-numerology test, and it
predicts log₂(1.69)≈0.757 should match the repo's existing O(1.69^N) skeleton enumerator); the wall = open-set-
condition failure (map overlap) with overlap measure 2^-2N (FR2). Reuses the small-N enumerator + carry skeleton.

### W6-FR1 · Moran equation → 0.74 from the carry-branching ratios  `[P4 · cheap · HEADLINE]`
- Each bit-slice carry-automaton transition = a contraction (ratio ½, one bit); admissible-children count = local branching b_k; the similarity dimension solves Σ 2^{-s}·(children)=1 → s = mean log₂ branching, claimed 0.74. *Derives* the exponent from independently-measured multiplicities, not a slope fit. **lens** Moran/similarity dimension · **locus** the carry-difference automaton · **mech** count.
- **probe:** N=4..12 walk the carry automaton LSB→MSB, record the per-slice branching histogram b_k; s_pred=(1/N)Σ log₂(mean b_k); is s_pred∈[0.70,0.78] and = log₂(1.69)≈0.757 (the skeleton enumerator base)? **kill:** s_pred not within ±0.05 of 0.74 (e.g. geo-mean branching gives 2^0.5 or 2^1.0). **skeptic:** 0.74-as-dimension is numerology *unless* the Moran derivation from branching lands independently — that's the load-bearing test (a clean negative rules out exact self-similarity). **≠interval-exchange/transfer-op:** a sum over geometric ratios Σr^s=1, not a Perron radius or a KZ cocycle.

### W6-FR2 · Open-set-condition failure → 2^-2N as the overlap measure  `[P4 · cheap]`
- The zero-forcing maps have *disjoint* images through 60 (de57/59/60 constant ⇒ non-overlapping cylinders ⇒ OSC holds ⇒ clean 2^0.74N); at 61 two independent conditions demand the same cylinder ⇒ images overlap ⇒ OSC fails ⇒ attractor measure on the overlap = (2^-N)² = 2^-2N. **lens** open-set condition / overlapping IFS · **locus** the de-maps + sr=61 conditions · **mech** lower-bound.
- **probe:** N=4,6,8 verify de57/59/60 single-valued (disjoint images, OSC holds) up to 60; do the sr=61 g1=0,h=0 satisfying sets *overlap* with joint density ≈(marginal)²? **kill:** sr=61 conditions partition (not overlap, ratio≠1), or OSC fails *before* 61 (mispredicts the wall). **skeptic:** 2^-2N=two-independent-conditions is already known — the non-trivial half is demonstrating OSC *holds* through 60 then fails at 61. **≠interval-exchange/transfer-op:** set-intersection of cylinder images, not a Lyapunov exponent.

### W6-FR3 · de58 set-renormalization → width-(N+1) collisions contain scaled width-N copies  `[P3 · cheap]`
- If the collision set is self-similar, each de58 class at width N+1, rescaled (drop one bit), = the full width-N collision set; the growth |de58|(N) is the renormalization branching, and C(N+1)≈2^0.74·C(N) is its fixed point (intercept 2.47 = the seed measure). A *constructive* lever (build N+1 from N). **lens** exact set self-similarity across N · **locus** the de58 partition · **mech** bridge-scales.
- **probe:** enumerate N=8 and N=10 da=0 collision sets, tag by de58 class; does a fixed bit-shift map send each N=10 class onto the N=8 set (multiset overlap >80%)? C ratios vs 2^0.74? **kill:** down-projected classes don't nest (overlap <50%, no consistent scaling map). **skeptic:** the map must be *pre-specified* and checked as a multiset, or it degenerates to "both sets are biggish"; |de58|={2,8,8,16,512,1024} is irregular (warns against *exact* nesting). **≠interval-exchange/transfer-op:** a static set identity A_{N+1}|class≅scale(A_N), no dynamical flow.

### W6-FR4 · Two-phase multifractal → the 132/124 split as two local dimensions  `[P3 · cheap]`
- The output-bit invariance measure is multifractal: 124 controlled bits = the regular phase (α≈0), 132 hard-core = the singular/dominant phase (α≈1) carrying the HW mass → HW~74 = the f(α)-weighted mean. The *value* is whether a genuine intermediate band exists (partially-controllable bits = new attack surface). **lens** multifractal f(α) spectrum · **locus** output/state diff bits · **mech** structural-invariant.
- **probe:** N=8,10,12 per-bit invariance frequency p_i; generalized dimensions D_q from Σp_i^q (q=0,1,2), Legendre → f(α); two concentrations with mass-mean=74, *and a non-trivial spread*? **kill:** the p_i histogram is a clean two-point mass (every bit p=1 or p=0.5, nothing between) → "multifractal" adds nothing over the 124/132 count. **skeptic:** most rebrand-prone — the entire value is the middle band; if empty, kill. **≠info-geometry/free-prob:** box-partition moments of one fixed measure, not a Fisher metric or a free convolution.

## Matroid theory & the Tutte polynomial

**Through-line:** ONE abstract GF(2) constraint matroid M (built by the repo's existing `gf2_eliminate` on the
linearized round relations — rank 96, 416 free already computed) whose **corank → 132** (MA1), **Tutte growth
→ 0.74** (MA2), **oriented-matroid cocircuit jump → 2^-2N** (MA3), **connectivity 2-separation → the wall** (MA4).
MA1 is the cheapest, most decisive, and *nearly runnable with existing tooling* — and the repo's own notes call
the 132 a "CDCL-search artifact, not a combinatorial derivation," explicitly wishlisting a matroid audit.

### W6-MA1 · Constraint-matroid corank = 132 (a cocircuit support, not a solver artifact)  `[P4 · cheap · HEADLINE]`
- The GF(2) cascade matroid M[A] (carries as free ground elements); rank = controllable dim, corank = |E|−rank = the cobasis = the forced bits. Conjecture the fundamental-cocircuit support = 132 = 128 (W*_59,W*_60, 4 words×32) + 4 anchors — *derived from rank*, order-independent, no solver. Joins the corank cluster from pure combinatorics. **lens** vector-matroid rank/cocircuit · **locus** rounds 57–63 GF(2) relations · **mech** structural-invariant.
- **probe:** N=8..32 assemble A (linear σ/Σ/XOR layer + carry ground elements), call `gf2_eliminate`; corank, cobasis labels; does the schedule-bit corank → 132±4, cobasis preferring W*_59/W*_60, the 4 anchors = W1_57[0],W2_57[0],W2_58[14],W2_58[26]? **kill:** corank ↛132, or all 256 schedule bits equally free/forced. **skeptic:** the 132 was measured under one encoder/elimination-order (a VSIDS habit); matroid corank is order-independent — a match is meaningful, a mismatch decisive. **≠rigidity-matroid/matrix-tree:** the vector matroid of the *GF(2) round-relation matrix* (ground set = bits, rank = independent constraints), no bars/kinematics, no Laplacian/spanning-tree.

### W6-MA2 · Tutte growth rate → 0.74 via Greene's code-weight-enumerator identity  `[P3 · cheap]`
- Collisions = carry-surviving codewords of the linear constraint code C=ker(A); Greene's theorem: the weight enumerator = T(M;x,y) on the hyperbola (x−1)(y−1)=2; conjecture 0.74 = lim (1/N)log₂ T at the SHA point — a Tutte growth rate, not a 11-point fit. **lens** Tutte polynomial / Greene · **locus** the M_57..M_63 filtration · **mech** count.
- **probe:** N=4,6,8 build M_63, code C=ker(A); compute the Tutte point / weight enumerator (enumerable small-N); compare (1/N)log₂T to the measured count exponent; the collisions/Tutte ratio = a "carry tax" exponent c, 0.74=ρ_Tutte−c? **kill:** no hyperbola point gives log₂T/N within ±0.05 of the target and c not stable. **skeptic:** the *cascade-specific* count is ~2^N (carry entropy = N bits), so fix one family and use its measured exponent — a clean 1.0 would beat chasing the blended 0.74. **≠matrix-tree:** non-graphic GF(2) matroid, evaluated on the code hyperbola (not (1,1)), counting codewords not trees.

### W6-MA3 · Oriented-matroid cocircuit collapse → 2^-2N as a corank 1→2 jump  `[P3 · cheap]`
- Promote carry signs to a chirotope; g1=0 and h=0 are two cocircuits with overlapping support but independent signs → joint vanishing = product 2^-N·2^-N = 2^-2N; cocircuit rank goes 1→2 at round 61. Predicts sr=62 → 2^-3N (a third cocircuit). **lens** oriented matroid / chirotope · **locus** round 61 carry signs · **mech** lower-bound.
- **probe:** N=8,10 sample pairs, record round-61 carry-sign vectors + (g1,h); find the two sign-supported functionals; verify overlapping supports, joint rate = product (the 1.005 ratio), and *one* cocircuit at round 60 vs two at 61; forward-test sr=62→2^-3N. **kill:** round 61 admits only one cocircuit (g1≡h up to sign), joint rate ≠ product, or carry signs violate chirotope axioms. **skeptic:** two independent GF(2) conditions already give 2^-2N without signs — the orientation earns its keep only if it predicts *which* candidates have g1,h accidentally dependent (an easier candidate). **≠rigidity:** discrete carry-in/out sign data, no bars/flexes.

### W6-MA4 · Matroid connectivity drop → the wall as a 2-separation at round 61  `[P2 · moderate]`
- Tutte connectivity λ(M_r): connected (cascade entangled with the collision condition) ≤60; at 61 W[61]=σ1(W[59])+… being schedule-determined induces a **2-separation** (free block ⊕₂ schedule block), the 2 connector elements = g1,h — the rank-additive form of Theorem-6's "cascade advantage exactly cancelled." Gives block2_wang a target: restore 3-connectivity across 61. **lens** matroid (Tutte) connectivity · **locus** the free/schedule interface · **mech** structural-invariant.
- **probe:** N=4,6,8 compute λ(M_r)=min over balanced partitions of [r(X)+r(E∖X)−r(M)+1] for r=58..62; a clean drop to λ=2 at 60→61, cut separating W*_57..60 from W*_61..63, connector = g1,h? universal across candidates? **kill:** λ doesn't drop at 61, the cut doesn't align free-vs-schedule, or connector rank ≠2. **skeptic:** at small N everything looks 2-3-separable — compute over *balanced* partitions with the cut *location* forced; won't scale to N=32 (a structural-explanation tool, not a search). **≠effective-resistance/spanning-tree:** λ from the abstract rank function r(·), no vertices/edges/resistance.

---

# WAVE 7 — combinatorial-game-theory · Ramsey/density · formal-concept-analysis · quantum-walks · nonstandard-analysis (2026-06-03)
_(appending as agents return)_

## Ramsey theory & density (unavoidable structure)

**Through-line:** color the bit×round carry grid (carry/no-carry); ask what structure is *forced*. Honest
caveat (the agent's own): real Ramsey/HJ/vdW thresholds dwarf SHA's 32-bit/64-round dimensions, so any
small-N "forced structure" is likely finite-size determinism, not asymptotic forcing — so the probes test
*geometry* (contiguity, AP-excess, density-variance spike), not mere existence, to tell a real Ramsey object
from an artifact. RA1/RA3 carry genuine new predictions; RA2/RA4/RA5 lean on schedule-linearity (lower plaus).

### W7-RA1 · The 132 as a forced monochromatic core (Gallai/Hales–Jewett)  `[P3 · cheap]`
- Carries 2-color the bit×slot grid; conjecture ~132 grid cells are color-frozen across (almost) all messages = the unavoidable monochromatic core, with the hard-core output bits downstream of it; HW~74 = its density. **lens** Gallai/Hales–Jewett · **locus** the carry matrix · **mech** structural-invariant.
- **probe:** N=4..12 extract the carry matrix per message (recompute each add, XOR sum vs XOR of addends → carry-ins); per-cell color entropy over the sample; count entropy≈0 (frozen) cells → 132 projected? are they *contiguous* (a sub-grid/line, the Ramsey signature) vs scattered? **kill:** frozen count grows like the full grid area, or frozen cells are scattered (no line geometry) across ≥3 N. **skeptic:** HJ numbers dwarf a 32×448 grid — a frozen core at small N is finite-size/propagation determinism, not asymptotic forcing; only contiguity+scaling rescue it. **≠containers/sunflower/additive-comb:** an unavoidability (forced-substructure-in-every-coloring) claim with a threshold round, not a covering/petal/sumset.

### W7-RA2 · Collision existence as a Hales–Jewett inevitability  `[P3 · cheap]`
- Message-difference vectors over a fixed difference-alphabet = points of [b]^n; color by output-diff class; a collision family with one free word = a monochromatic combinatorial *line* (a slidable coordinate, matching the cascade's one free axis). **lens** Hales–Jewett · **locus** message-difference cube · **mech** count.
- **probe:** b=2 ({no-diff, δ}), n=2..5 free words; enumerate, color by truncated output-diff class; does the zero-color class contain a combinatorial line? smallest n vs round count? **kill:** zero-diff points never align into a line at reachable n, or threshold n* independent of round count. **skeptic:** HJ(2,k) is enormous; n≤4 (cascade free words) is vastly sub-threshold — an observed "line" is σ-linearity leaking through, not HJ forcing. **≠containers/sunflower/additive-comb:** a monochromatic line forced in a colored cube, not packing/petals/sumset.

### W7-RA3 · The 2^-2N wall as a Szemerédi-regularity density increment  `[P4 · cheap]`
- The collision-survival bipartite graph has a regularity partition; sr=60→61 splits a regular pair and drops survival-density by one regular-pair factor, so 2^-2N=(2^-N)² is *two* density factors (one per condition); the wall = where density falls below ε (irregular/search-dominated). **lens** Szemerédi regularity / density increment · **locus** the difference-compatibility graph · **mech** lower-bound.
- **probe:** N=6..12 build G_r (message-pair classes × surviving classes), per-round edge density; does the ratio hit a clean 2^-N step then 2^-2N? **the new prediction:** a spike in inter-bucket density *variance* (regularity breakdown) at the wall round? **kill:** density drop is smooth/single-factor (no exponent doubling), or no variance spike at the boundary across N. **skeptic:** regularity is an asymptotic huge-graph tool; at small N the factorization may just *be* the known two-condition counting — the *variance spike* is the only genuinely new, load-bearing prediction. **≠containers/sunflower/additive-comb:** a density-partition threshold crossing + variance signature, not a covering/petal/sumset.

### W7-RA4 · Van der Waerden APs on the de58 axis  `[P3 · cheap]`
- de58 sits at the modular feed-forward (vdW-relevant additive structure), unlike XOR-frozen de57/59/60; conjecture its reachable set S⊂Z/2^N contains excess arithmetic progressions (structured generators), explaining why de58 alone grows and how. **lens** van der Waerden / Szemerédi APs · **locus** the de58 axis · **mech** structural-invariant.
- **probe:** N=4..14 collect the *modular* de58 reachable set S_N; count 3-APs and the longest AP vs a random equal-density subset; excess APs + a recurring common difference? **kill:** AP statistics indistinguishable from random at all N. **skeptic:** at density 2^-22 APs are NOT vdW-forced — any found are σ-linearity artifacts, not Ramsey inevitability; only the empirical AP-excess matters (and if only sumset-growth survives, kill as banned-adjacent). **≠additive-comb:** measures AP *counts* (density-forces-progressions), never |S+S| / Freiman.

### W7-RA5 · Ramsey-number clique threshold for the boundary round  `[P2 · cheap]`
- The message-word agreement graph (edge RED iff the pair stays a partial collision through r); a multi-word collision family = a RED clique; the boundary r* = where the coloring first forces / loses the needed RED clique (a Ramsey-number-vs-edge-density condition). **lens** graph Ramsey numbers R(s,t) · **locus** the agreement graph · **mech** structural-invariant.
- **probe:** N=4..10, K=16..64 sampled words; 2-color edges by pairwise partial-collision through r; max RED clique vs r; a sharp collapse at the sr-analog+1? clique-size scaling vs the random ~2log₂K? **kill:** max clique = the random Erdős value with no anomaly at the boundary, or no drop at sr+1. **skeptic:** the cliques SHA needs are tiny (a few words) → the Ramsey threshold is trivially met and non-predictive; only a *sharp clique collapse at exactly r** redeems it (weakest of the five). **≠containers/sunflower/additive-comb:** mutual-pairwise-compatibility clique forced by vertex count, no container/petal/sumset.

## Combinatorial game theory (impartial games, Sprague–Grundy)

**Through-line:** "extend the partial collision by one round" = a move in an *impartial* game; read the wall off
the Grundy/mex recursion. CG3 (P/N-measure) and CG1 (de58 = the one live nim-heap) are the standouts and
mutually reinforce (CG1: the game *value* is de58; CG3: the boundary *winnability census* is 2^-2N). Shared
fragility: disjunctive-sum independence — SHA's carry coupling may couple the four de-coordinates; every probe
measures the coupling first.

### W7-CG1 · de58 = the one live nim-heap; the wall = the heap you can't empty  `[P4 · cheap]`
- The (de57,de58,de59,de60) cross-section = a 4-pile Nim disjunctive sum; de57/59/60 constant = size-0 (terminal) heaps, de58 grows = the lone positive heap, so the whole game's Grundy value = de58's nimber; a collision = nim-sum 0; the wall = where no move zeros de58. **lens** Sprague–Grundy nim-sum · **locus** the de-vector · **mech** structural-invariant.
- **probe:** N=8..12 build the round-state game graph (nodes=(de57..60), edges=free-word moves, terminal=all-zero), Grundy bottom-up via mex; does G ≡ G(de58-heap) when the others=0? nim-value(de58) growth vs the 2^10 law? **kill:** G(4-tuple) ≠ G(de58) when others=0 (sub-games not disjunctively independent — a move couples coordinates). **skeptic:** carry coupling means a free-word move generically perturbs all four de's — measure the coupling first. **≠Conway-surreal:** nim-sum (XOR of heap sizes) + mex on an *impartial* game (single integer nimber), no {L|R} cut, no temperatures.

### W7-CG2 · Game thermography → temperature cools to 0 at the wall  `[P3 · cheap]`
- Each round is a "hot" move (many free-word options that reduce da-distance) cooling as freedom is spent; the wall = where the incentive (best−mean residual improvement) crosses 0 (no move strictly improves → pass control to carries). **lens** game temperature/thermography · **locus** message-schedule/feed-forward · **mech** reframe.
- **probe:** N=6..12 per round, 1-ply lookahead best vs mean residual improvement over free-word options = temperature; monotone cool-down + zero-crossing at the sr=61 analog? **kill:** temperature not monotone, or zero-crossing far from the boundary. **skeptic:** CGT temperature is from game *values* via cooling, not raw option counts — the proxy may just be a renamed "options shrink" difficulty curve. **≠Conway-surreal:** the single-scalar incentive of an *impartial* position (max over successors), no Left/Right masts.

### W7-CG3 · 2^-2N = the P/N-position measure (density of winnable positions)  `[P4 · cheap]`
- A boundary position is an N-position (winnable = can extend the collision) iff a free-word move reaches g1=0 ∧ h=0; two independent 2^-N conditions → the N-target has measure 2^-2N, so 2^-2N is the *fraction of positions from which a winning move exists* (not a probability). Predicts sr=62 → 2^-3N. **lens** P/N census · **locus** carries/feed-forward · **mech** lower-bound.
- **probe:** N=8,10,12 per boundary position brute-check if *any* free word achieves g1=0∧h=0 (N) else (P); is the N-fraction = 2^-2N (and joint=product, the 1.005 ratio)? push one round deeper → 2^-3N? **kill:** N-fraction ≠ 2^-2N (conditions correlate, or carry structure leaks extra winnable moves). **skeptic:** risks relabeling the known 2^-2N — the *sr=62→2^-3N* prediction is what earns its keep. **≠Conway-surreal:** the impartial Grundy-0-vs-nonzero Boolean census of the move graph, no surreal arithmetic.

### W7-CG4 · Misère cascade → is the wall intrinsic or an artifact of orientation?  `[P2 · cheap]`
- Flip to misère (last collision-completing move loses); if the wall is intrinsic the P-set is invariant (tame), if it *moves* the boundary is an artifact of pointing the objective at the normal-play terminal (wild). A robustness check no other lens gives. **lens** misère Grundy/genus · **locus** feed-forward terminal orientation · **mech** structural-invariant.
- **probe:** N=6..10 compute normal-play P-set (Grundy 0) and misère P-set on the same graph; coincide near the boundary (tame, intrinsic) or diverge (wild, conventional)? **kill:** P-sets identical everywhere (fully tame → misère adds nothing), or the graph too coupled to define disjunctive misère. **skeptic:** a monolithic single-position game makes misère just "swap the terminal label" (vacuous); the interesting wild case is the less likely one. **≠Conway-surreal:** purely impartial misère theory (how the Grundy-0 set changes), no {L|R}.

### W7-CG5 · Octal-game encoding → read the wall off the nim-sequence period  `[P3 · cheap, forced-fit risk]`
- Encode carry resolution as an octal/subtraction game on the de58 heap; octal games are eventually periodic (Guy–Smith), so the wall = where de58's size lands on a Grundy-0 slot of the (computable, periodic) nim-sequence — a number-theoretic prediction. **lens** octal games / eventual periodicity · **locus** carries · **mech** structural-invariant.
- **probe:** derive the octal code from the de58 carry-update at small N; compute G(n) by mex; eventually periodic? G(de58-size at the 61-analog)=0 while G>0 at the 60-analog sizes? **kill:** the SHA carry rule corresponds to *no* well-defined octal game (move legality depends on more than heap size). **skeptic:** the most forced-fit — SHA carries depend on the actual addend bits, not just size, which is the very state that makes SHA hard; likely a category error. **≠Conway-surreal:** integer Grundy sequences by mex + Guy–Smith periodicity, no {L|R}.

### W7-CG6 · Mean value → HW~74 as a cooled hot game's mean  `[P3 · cheap]`
- The 132 hard-core bits = the cold (number) spine, the ~124 soft bits = the hot (temperature) residue that averages out; HW~74 = the mean the game cools to (≈ #hard-core-ones + ½·#soft). The new prediction: plateau *width* = the residual temperature (a narrower-than-binomial soft-bit spread). **lens** mean/mast value, cooling · **locus** whole-function/state-cross-section · **mech** structural-invariant.
- **probe:** N=8..12 classify hard-core vs soft bits; does mean HW = #hardcore-ones + ½·#soft? is the HW spread *narrower than binomial* (genuine cooling/anticorrelation) vs exactly binomial (just statistics)? **kill:** HW ≠ the decomposition, or the soft-bit spread is exactly binomial ("temperature" vacuous). **skeptic:** weakest causal claim — a plateau is fully explained by "132 constrained + rest uniform"; only a sub-binomial spread earns the CGT label. **≠Conway-surreal:** the single-scalar mast value an impartial hot game cools to, no {L|R}.

## Formal concept analysis & Galois lattices

**Through-line:** build the collision *formal context* (objects × attributes cross-table); the concept lattice
+ implication base + irreducibles are concrete computable invariants. FC1 (132 = meet-irreducibles) and FC2
(concept-count explosion = the wall) are the standouts — and FC2 ties the wall to the *same* g1⊥h independence
that gives 2^-2N (two independent attributes → a Boolean-square sublattice). One next-closure routine, no SAT.

### W7-FC1 · The 132 = the meet-irreducibles of the output-agreement lattice  `[P4 · cheap]`
- Objects = message pairs, attributes = "output bit b agrees"; a controlled bit (dd,dg,dh) agrees as the *meet* of upstream agreements (reducible), a hard-core bit (da,db,de,df, zero controllers) is meet-*irreducible*; so 132 = the irreducible rank, not a correlation count; HW~74 = the expected intent-deficit of a random pair. **lens** FCA meet-irreducibles / attribute reduction · **locus** round-63 outputs · **mech** structural-invariant.
- **probe:** N=4..10 build the 256-column agreement cross-table (collisions + random same-kernel pairs), clarify+reduce, count & *name* the meet-irreducibles; are they {da,db,de,df}[*]+4dc, fraction →132/256? **kill:** irreducibles not concentrated on {da,db,de,df} (spread, or dd/dg/dh appear). **skeptic:** "zero single-flip controller" (a *linear* correlation notion) and "meet-irreducible" (a *lattice-closure* notion) may merely correlate; check sample-size stability. **≠topos/lens:** Birkhoff lattice irreducibles of a finite Galois connection, no Heyting-Ω/sheaf/optic.

### W7-FC2 · Concept-count explosion → the sr=60→61 wall  `[P4 · cheap · HEADLINE]`
- Below 60 the cascade is single-DOF → a near-*chain* concept lattice (few concepts); the two *independent* sr=61 attributes (g1=0 ⊥ h=0) turn a chain into a Boolean square, so |B(K)| jumps multiplicatively — the same independence that gives 2^-2N. A non-SAT, non-probabilistic hardness proxy vs round. **lens** concept-lattice size |B(K)| · **locus** cascade boundary 57–61 · **mech** lower-bound.
- **probe:** N=6,8 exhaustively enumerate W[57..60]; accumulate per-round zero-diff attributes, compute |B(K)| vs r (next-closure); add the two sr=61 attributes → a ~×k jump (vs the tame growth), appearing as an independent 2×2 sublattice? **kill:** |B(K)| grows as fast across tame rounds 57→60 as adding the sr=61 pair (no kink). **skeptic:** must use *exhaustive* small-N (|B| is sample-dependent); control by adding two *correlated* dummy attributes — they shouldn't cause the jump. **≠topos/lens:** the cardinality of a finite closure lattice, an integer from next-closure, not a subobject-classifier count.

### W7-FC3 · Duquenne–Guigues base → the wall is the one irreducible 2-premise rule  `[P3 · cheap]`
- The cascade's canonical implication base is all *unary*-premise ("de60=0 ⇒ …", the single-equation propagation) through 60; sr=61 is the first implication with a *2-element* pseudo-intent (g1=0 ∧ h=0 must hold jointly) — the FCA twin of 2^-2N. Max premise size ticks 1→2 at the wall. **lens** DG implication base / pseudo-intents · **locus** the cascade implications · **mech** structural-invariant.
- **probe:** N=6,8 exhaustive; compute the DG base, premise-size histogram per round-depth; all-1 ≤60, a size-2 premise at 61? control: the 9-step local collision should be all-unary (no wall). **kill:** 2-premise implications already appear below 60. **skeptic:** premise size is granularity-dependent (per-round scalar attributes, not per-bit, or the base floods with size-2 everywhere) — a modeling choice doing real work. **≠topos/lens/proof-complexity:** Horn implications read off a Galois lattice (minimum implicational cover), not refutation size or internal logic.

### W7-FC4 · Concept stability → de58 as the unique low-stability (soft) coordinate  `[P4 · cheap]`
- High-stability concepts (intent unshaken by object removal) = the 7/8 constant register diffs (cascade-rigid); low-stability = the lone varying dh61/de58 (carry-fragile = the single DOF). The de58-grows/de57,59,60-constant split = a stability spectrum; useful for block2_wang (the soft coordinate is where a 2nd-block correction acts). **lens** Kuznetsov stability index · **locus** the single-DOF trajectory · **mech** structural-invariant.
- **probe:** N=8,10 attributes = "(register,round) diff = modal value"; compute concept stability σ; do de57/59/60 + constant diffs cluster at σ≈1 and de58/dh61 form a distinct low-σ cluster growing N=8→10 (low-σ count ~2^0.74N)? **kill:** de58 concepts have the same stability as de57/59/60 (no separation). **skeptic:** "constant diffs → σ≈1" is near-tautological; the *only* payload is the de58-vs-others separation + its N-growth. **≠topos/lens:** a counting ratio on a concept's extent powerset, no Ω/sheaf/optic.

### W7-FC5 · Arrow relations → localize the wall to one (object,attribute) cell  `[P3 · cheap]`
- Arrow relations (↓↑↕) mark the irreducible "load-bearing absences"; conjecture they concentrate on the W[60]-schedule-match / dT1_61=0 column at near-collision objects — the FCA fingerprint of "the 7-round problem collapses to ONE equation," and the double-arrow count tracks the 24-bit residue. Also yields the minimal context still bearing the wall. **lens** FCA arrow relations · **locus** the W[60] lever-loss · **mech** structural-invariant.
- **probe:** N=6,8 exhaustive; attributes {de[61,62,63]=0, dT1_61=0, W[60]-match}; compute the ↓↑↕ table; do double-arrows pile on the schedule/dT1 columns + HW-1 near-collision objects, count ~2^-N? **kill:** arrows spread uniformly over all columns (no localization). **skeptic:** arrows live on the *reduced* context and are sample-sensitive — oversample HW≤2 pairs or use exact near-collision sets. **≠topos/lens:** incidence-table bookkeeping (a refinement of non-incidence), no classifier/morphism-laws.

## Quantum walks (Szegedy discriminant — used classically)

**Through-line:** lift the collision-search chain P to the Szegedy discriminant D=√(P∘Pᵀ) (a real matrix you
SVD on a laptop); its phase gap 2√δ → the wall (QW1), top singular edge → 0.74 (QW2), kernel → 132 (QW3).
Shared load-bearing caveat: classically D could just √-relabel P's own gap — it earns its keep ONLY because
the non-invertible feed-forward makes P non-reversible (so D≠relabel(P)); every probe compares D's spectrum vs P's.

### W7-QW1 · Cascade-absorption phase gap → a collapse/exponent-doubling at sr=61  `[P4 · cheap]`
- The 7-round diff-contraction is an absorbing walk to the zero-diff sink (the feed-forward = the sink making it non-reversible); the Szegedy phase gap is large (fast hitting) ≤60 and collapses at 61, with the hitting-time exponent *doubling* as ε→2^-2N (two conditions). **lens** Szegedy phase gap / hitting time · **locus** the 7 cascade rounds · **mech** lower-bound.
- **probe:** N=8..12 sample pairs → diff-config chain P (active-register set + de58 bucket), D=√(P∘Pᵀ), SVD → phase gap, sr=60-free vs sr=61-enforced; gap collapse + exponent doubling? **compare D's gap vs P's gap (must diverge).** **kill:** sr=61 gap within 2× of sr=60, or hitting-exponent unchanged, or D's gap = P's gap (relabel). **≠spectral-graph/commute-time/magic:** singular values of the *two-copy geometric-mean* matrix (cos of eigenphases), the single edge 2√δ + a target density ε, not a Laplacian spectrum or a spectrum-sum.

### W7-QW2 · Discriminant top edge → 0.74 = log₂ s_max(D)  `[P3 · cheap]`
- The bidirectional search operator's top singular value = the per-bit amplification of completable prefixes (geometric mean of forward×backward survival mass); 2^0.74N = s_max^N, so 0.74 = log₂ s_max(D) — computable from local transition stats, no collision enumeration. **lens** Szegedy discriminant edge · **locus** the constructive cascade tree · **mech** count.
- **probe:** N=8,10 build P on (W57,W58) prefixes (forward weight = #completions passing de61/62/63=0), s_max by power iteration; log₂ s_max ≈0.74, tracks across N, and ≠ s_max(P) (Perron)? **kill:** log₂ s_max ∉[0.6,0.9], or = the round-Jacobian's top singular value (relabel), or = P's Perron value (reversible). **skeptic:** if P reversible, s_max(D)=Perron(P) (*banned*) — the non-reversible feed-forward is the only thing saving it; probe compares explicitly. **≠spectral-graph/singular_chamber_rank:** the geometric-mean transition matrix's edge, not a Perron eigenvalue or a deterministic schedule-Jacobian SVD.

### W7-QW3 · Discriminant kernel → 132 = corank(D)  `[P3 · cheap]`
- A hard-core bit can't be flipped independently → either forward or backward independent-transition prob is 0 → its mode has a zero singular value; conjecture corank(D)=132 (rank 124), the soft 124 = the freely-explored bits (HW~74). Joins the corank cluster from a transition-matrix angle. **lens** discriminant kernel · **locus** bit-level transitions · **mech** structural-invariant.
- **probe:** N=8 build a bit-projected P, D=√(P∘Pᵀ), SVD, count near-zero singular values (threshold-sweep for a spectral gap); corank/total →0.516, projection-robust, kernel vectors aligned with the known hard bits? **kill:** corank not a stable ~0.5 fraction across N, or kernel = numerical noise / a projection artifact. **skeptic:** a connected reversible chain has 1-dim kernel — a 132-dim kernel needs strong non-reversibility (risk: putting 132 in by hand via the projection); sweep projections, demand robustness. **≠spectral-graph/commute-time:** kernel of the Hadamard product P∘Pᵀ, exactly what inverse-Laplacian commute time discards.

### W7-QW4 · Interference fringe → the N=10 bump as a singular-value coalescence  `[P3 · cheap, fragile]`
- Constructive interference = two eigenphases of the walk coalescing (a singular-value crossing in D); conjecture the rotations make D's top-two singular values cross at N=10 (the unique two-branching-bit N), splitting at 9,11. Predicts the *next* anomalous N. **lens** eigenphase degeneracy · **locus** the cascade discriminant vs N · **mech** structural-invariant.
- **probe (cheapest):** N=8..14 top-two singular-value gap s₁−s₂ of D(N) (two power iterations); a pronounced *dip* at N=10 coinciding with the collision bump? predict & test a second dip. **kill:** no local minimum at N=10, or the bump fails to replicate under alternating-fill corrections. **skeptic:** one data point + ~6 N's = weak; most story-like — but near-free and *predicts* further bumps, so cheaply falsifiable. **≠spectral-graph/RMT:** a *coalescence* (constructive, e^{iθ} amplitudes adding), the opposite of RMT level-repulsion; no phase content in a Laplacian.

### W7-QW5 · Hitting-time-exponent map → a step at r=58 (de58) and a cliff at 60→61  `[P4 · cheap]`
- α(r)=½(−log₂δ(r)−log₂ε(r))/N fuses gap and target density; flat 57–59 (de57/59 constant → ε constant), a *step at 58* (de58 opens 2^10 configs → ε spikes) whose height tracks log₂|de58|/N, and a cliff at 60→61 (δ collapses) — unifying de58-growth + single-DOF + the wall in one scalar. **lens** Szegedy hitting time 1/√(δε) · **locus** rounds 57→63 · **mech** structural-invariant.
- **probe:** N=8..14 per round build D(r), δ(r), ε(r) (the de61/62/63 on-track oracle); α(r,N) flat 57–59, step at 58 (height = log₂|de58|/N), cliff at 61? **kill:** α smooth/monotone (no step at 58, no cliff at 61), or the step doesn't scale with |de58|. **skeptic:** classically α is just −½log(δε) — the Szegedy *form* (the √, the product, the predicted step *height*) is the only novelty; if any monotone combo of δ,ε works as well, it's a relabel. **≠commute-time:** commute time is δ-only (no target-density ε), structurally unable to produce the r=58 ε-step.

## Nonstandard analysis & ultraproducts

**Honest framing (the agent's own):** ultraproduct/Loeb machinery has ZERO computational content alone; the
*only* falsifiable payload is the **internal (N-uniform, transfer-stable) vs external (N-drifting)** classification.
So every probe is an N-uniformity sweep over N=4..16 (reusing the repo's `make_helpers(N)` rotation-scaling). NS3
makes that classification the deliverable; NS2 makes a real cross-law convergence prediction. Watch the rotation-jitter
from `round(k·N/32)` — a "law" that merely tracks the jitter is external-by-artifact, not by cryptography.

### W7-NS2 · Loeb dimension → 0.74, the 132-fraction, and HW~74 as ONE invariant  `[P4 · cheap]`
- On the hyperfinite message space, μ_L(Coll)=0 but dim_L(Coll)=st(log₂#Coll/N)=0.74; hard-core bits = the coordinates whose pinning *drops* the dimension (non-infinitesimal conditional measure). Predicts 0.74, the dimension-dropping fraction, and the HW-plateau fraction *converge to one common limit*. **lens** Loeb measure/dimension · **locus** the collision set + per-bit marginals · **mech** count.
- **probe:** N=4..16 exhaustive Coll; d(N)=log₂#Coll/N; f(N)=fraction of dimension-dropping coordinates; h(N)=normalized HW of dropping coords; do d,f,h *converge* (differences shrink with N)? **kill:** the three fractions *diverge* at N=14,16 (more than at N=8,10) → 0.74 and 132/256 are independent numbers, framing inert (but informative). **skeptic:** Loeb does no work beyond "limit of a ratio"; earns its keep ONLY via the convergence-to-a-common-fraction prediction; 0.74 vs 0.516 differ *now* — the bet is whether they converge (don't prejudge from N=32 where jitter is absent). **≠o-minimality/2-adic:** a counting (Loeb) measure on the N→∞ ultrapower, not tame definable sets and not a 2-adic value completion.

### W7-NS3 · Internal/external audit → which laws transfer, which are walls (the deliverable)  `[P4 · cheap]`
- Łoś: transfer-stable ⟺ internal ⟺ N-uniform. Conjecture algebraic identities (da=de Thm 4, de57/59/60 constant, cascade da=0) are N-exact (internal → finitarily provable) while count-asymptotics (0.74, the 132-fraction) provably never lock (external → unprovable by finite-N methods) — explaining *why* sr=61 has no UNSAT proof. **lens** Łoś / transfer principle · **locus** the empirical-law ledger · **mech** reframe.
- **probe:** N=4..16 one-table audit: tag each law N-exact (internal) vs N-drifting (external); **the prediction: a clean no-crossover split, internal⇔hard-fact-provable, external⇔count-only.** A crossover (Thm 4 *failing* at some N, or 0.74 *locking* to an exact rational) is the most interesting outcome. **kill:** every writable law is N-exact (no external witnesses → the wall is internal, territory inert), or internal/external doesn't align with hard/easy. **skeptic:** risks "make a table, label columns" — saved only by the no-crossover prediction + the internal⇔provable bridge; if it just reproduces known N-uniformities (Thm 4, de-constancy) with no new prediction, it's a relabel. **≠o-minimality/2-adic:** transfer across the N-indexed family (opposite quantifier order to one-structure definability), not a value-metric completion.

### W7-NS1 · The wall as a definable cut → why no finite-N argument pins it  `[P3 · cheap, likely inert]`
- "sr-reachable within standard cost" mixes an internal quantity (the rate ρ(r), transfer-stable) with an external one (is the realization cost standard-finite) → a proper *cut* in *ℕ with no internal definition, which is exactly the kind of object no finite-N argument resolves (matching 1800 CPU-h, 0 SAT, no UNSAT). **lens** definable cut / external set · **locus** the round line · **mech** reframe.
- **probe:** N=8..16 measure −log₂(rate)/N at r=57..61; is the r=61 jump a *clean +2 step* for all N (internal → a step, not a cut, inert) or does it *interpolate* (+1.3→+1.7→+2, external → a genuine cut)? **kill:** jump = 2.00±0.05 for every N (clean uniform doubling) → `Reach` internal, framing is a relabel of the known 2^-2N (downgrade to "confirmed N-uniformity"). **skeptic:** most at risk of vocabulary; given g1⊥h is crisp at N=10, the doubling is probably already a clean step → likely inert. The *shape* (cut explains no-finite-proof) is the strongest conceptual match, but the probe likely returns "step." **≠o-minimality/2-adic:** an *external* (non-definable) cut in the ultrapower — the antithesis of o-minimal definability.

### W7-NS4 · Overspill → is the wall algebra (sharp round) or counting (no sharp round)?  `[P3 · cheap]`
- Underspill: an internal round-property's first failure is a *standard* round (sharp algebraic cliff); so if a boolean property flips at exactly 61 uniformly, 61 is a real cliff (provable obstruction); if *only counts* shrink at 61 (no boolean flip), the wall is external/measure-only → no UNSAT proof exists. Adjudicates rarity-vs-impossibility. **lens** overspill/underspill · **locus** internal round-properties P(r) · **mech** structural-invariant.
- **probe:** N=6..14 locate the exact breaking round of P1(da_r≡0), P2(de_r single-valued), P3(unique-w-solution) per N; same round for all N (internal cliff) or only a count shrinks at 61 (external)? **kill:** every internal property breaks at a *known* N-uniform round (e.g. de58 at 58) with nothing new flipping at 61 → reproduces known facts, subsumed by NS1/NS2. **skeptic:** mostly re-derives the rarity-vs-impossibility tension; keep only if a boolean property genuinely flips at 61 uniformly (a new internal target); else fold into NS1/NS2. **≠o-minimality/2-adic:** a pure nonstandard principle (false for standard ℕ), about properties leaking standard→nonstandard, not metric limits.

---

# WAVE 8 — cluster-algebras · computability/Weihrauch · k-core/jamming · rate-distortion (2026-06-03)
_(appending as agents return; terser cards — long-tail territories)_

## Cluster algebras & total positivity

**Through-line:** the cascade as seed mutation. CL2 (the verified g1⊥h = two sign-coherent c-vectors, predicting sr=62→2^-4N) is the standout; CL1/CL3 have crisp kills.

### W8-CL1 · Laurent pole-order → the wall = the first non-Laurent cascade step  `[P3 · cheap]`
- `casoff(r)` (the offset forcing da=0) is Laurent in the free seed (denominators cancel) for r≤60; at 61 W[61] is schedule-pinned (no free variable to divide by) → a real pole, invalid mutation. **lens** Laurent phenomenon · **locus** the cascade offset recurrence · **mech** reframe.
- **probe:** N=8,10,12 track pole_order(r) of casoff as a Laurent poly in W[57..60] (reuse gap_analysis.c); predict 0 for r≤60, ≥1 at 61. **kill:** pole_order(61)=0, or some r≤60 already >0. **skeptic:** needs a real exchange relation casoff(r+1)·casoff(r−1)=M₊+M₋, else it's Laurent-vocabulary on the existing recurrence. **≠prior:** pole-order of an offset polynomial, no prior wave touches the division-cancellation.

### W8-CL2 · c-vectors → g1⊥h is rank-2 sign-coherence; predicts sr=62 = 2^-4N  `[P4 · cheap]`
- The two sr=61 conditions are a (g-vector, c-vector) pair; their *verified* independence (ratio 1.005) = c-vectors non-parallel (rank-2 span) = 2^-2N codim; sign-coherence *forbids* the collision (no lucky 2^-N candidate, matching the empirical sweep). **lens** c-/g-vectors, sign-coherence · **locus** the g1/h decomposition · **mech** lower-bound.
- **probe:** reuse gap_analysis.c; for the *second* held equation form (g1',h'), measure the GF(2) rank of {g1,h,g1',h'} → predict 4 (→ sr=62 = 2^-4N); independence ratio stays [0.95,1.05] at N=12. **kill:** rank <4 at any cascade candidate, or any candidate with ratio ≳2 (a c-vector collision). **skeptic:** independence of two random functionals is the *default* — "c-vector" is unearned unless the seed-coordinate *signs* are one-signed (check sign-coherence). **≠matroid/lattice (waves 3,6):** the *signed* tropical vectors + why rank can't drop, not an independent-set count or a sublattice.

### W8-CL3 · TNN minors → de58 = the one positive coordinate of a TNN cell  `[P3 · cheap, clean kill]`
- The modular round-transfer on (de57..de60) is conjectured totally-nonnegative; its Bruhat cell freezes 3 coords (de57/59/60, the vanishing minors) and frees one (de58, the positive minors), with log₂|de58| = the cell rank. **lens** total positivity / TNN cells · **locus** the de-vector transfer · **mech** structural-invariant.
- **probe:** N=8..12 build the modular de-transfer matrix, compute *all minor signs*; predict 0 negative minors, vanishing pattern = {de57,59,60}-frozen, log₂|de58| = #strictly-positive maximal minors (vs 1,3,4,9,10). **kill (decisive):** *any* strictly-negative minor (not TNN), or the frozen set is the wrong three. **skeptic:** total positivity is a char-0/real notion; forcing a mod-2^N map into a TNN matrix may be a category error (clean kill if minors are mixed-sign). **≠Ehrhart/matroid:** *minor signs*, which no prior wave tests.

### W8-CL4 · Cluster complex → 0.74 as the exchange-graph growth rate  `[P2 · cheap, expect fail]`
- Cascade collisions = vertices of a cluster complex (edge = differ by one round's offset = one mutation); the de58 partition = its facets; 2^0.74N = the complex's exponential growth, 0.74 = its log-density of valid clusters (pruned sub-fan of the seed cube). **lens** cluster complex / exchange graph · **locus** the collision count · **mech** count.
- **probe:** N=8,10,12 build the collision adjacency graph (differ in one of 4 free-word offsets); is it *regular* (degree ≈ rank ~4, an exchange-graph hallmark)? log₂(#colls)/N → 0.74, kernel-invariant? **kill:** graph not regular (scattered degrees), or 0.74 strongly kernel-dependent (>0.1 spread). **skeptic:** a "differ-by-one-coord" graph is a hypercube subgraph, trivially regular-ish — weak evidence; deriving 0.74 *quantitatively* from f-vector growth is the real bar, expected to fail. **≠hypergraph/CAT0/quantum-walks:** the exchange-graph *regularity* + cluster-facet growth rate, not a walk on a given graph.

## Computability theory & Weihrauch degrees

**Honest framing (the agent's own):** at fixed N the task is finite/decidable, so the *literal* computability
objects are borderline — the content is a concrete integer the existing enumerator emits, stepping at 61. The
agent flagged that its ideas 1/3/4 are the SAME integer (the 1→2 jump = log₂ of 2^-2N) read three ways, so we
log them as ONE card with three readings, plus the reverse-math one. A genuinely fresh *axis* (which task reduces
to which), but low marginal content. One shared probe: the per-round independent-gating-condition count in gap_analysis.c.

### W8-WE1 · Weihrauch product jump → sr=60 is C_{2^N}, sr=61 is C_{2^N}⋆C_{2^N}  `[P4 · cheap · one number, three readings]`
- sr≤60 = a single bounded closed-choice (the cascade IS the reduction, solution guaranteed); sr=61's g1=0 ∧ h=0 = a *parallel product* of two independent choices → strictly harder. Three equivalent integers: the **independent-gating-condition count Q(r)** (parallel-product arity), the **nondeterministic advice bits A(r)** (LPO⋆LPO vs LLPO/C_2), the **reduction arity K(r)** (one search vs two). All step 1→2 (A: 0→2N) at 61. **lens** Weihrauch reducibility / closed choice / LPO · **locus** the sr boundary · **mech** lower-bound.
- **probe:** instrument gap_analysis.c at N=8,10 to count independent gating conditions per round (independence = the memo's ratio test); predict Q=1 for r∈{57..60}, Q=2 at 61 (and A=0→2N, K=1→2 agree = triangulation). **kill:** Q≥2 at some r≤60, or the two conditions are dependent at 61 (collapses to 1), or Q flat/smooth. **skeptic (brutal, the agent's):** finite ⇒ decidable, so this is a *query-complexity-within-finite* result dressed in lattice vocabulary, and Q=K=A/N is *the same number* as 2^-2N — the only NEW content is a non-existence-of-one-search-reduction argument (which the probe does NOT establish; it only shows the cascade needs 2). **≠proof-complexity/o-minimality/nonstandard:** which task *reduces to which* + its oracle arity (the cascade as an explicit Φ/Ψ reduction), not refutation size, defining formula, or model transfer.

### W8-WE2 · Reverse-math calibration → WKL₀ at sr≤60, ACA₀ at sr=61  `[P2 · cheap, vocabulary-risk]`
- sr≤60 existence = a WKL₀ fact (the cascade tree is extendible at every node — Thm 2 de60=0 ∀ words — so König gives a path, no set-formation); sr=61 needs ACA₀ (you must *comprehend* the compatible-W[60] set and intersect two independent ranges before choosing). The 3× ceiling = the WKL-locality payoff. **lens** reverse mathematics RCA₀⊂WKL₀⊂ACA₀ · **locus** the existence statement · **mech** reframe.
- **probe (finite surrogate):** two witness-finders at N=8,10 — a depth-first König search (O(rounds) live-set) vs a comprehension search (materialize the compatible set, O(2^N) live-set); does the *minimal-memory successful* finder's peak live-set step from O(1)-in-2^N (≤60) to Θ(2^N) at 61? **kill:** the König finder also certifies 61 with O(rounds) memory (still WKL₀), or even ≤60 needs comprehension (ladder placement wrong). **skeptic (brutal):** reverse-math wants *infinite* objects; a fixed-N collision has no infinite content — present ONLY as the finite witness-finder memory surrogate, never as literal provability, or it's fraudulent. Highest vocabulary-risk in the territory. **≠proof-complexity/o-minimality/nonstandard:** *which axiom is needed* (witness-finder memory), not proof size, defining formula, or transfer.

## Rate-distortion & information bottleneck

**Through-line:** the cascade as a lossy code. RD1 (de58 test-channel, R(0)=0.74N) and RD3 (132 = IB minimal-sufficient-statistic) are best; RD2 mostly re-explains 2^-2N (its novelty = the sr=62→4N prediction). All three are Blahut-Arimoto loops on empirical transition counts.

### W8-RD1 · de58 test-channel R(D) → 0.74N = R(0)  `[P4 · cheap]`
- de58 is the *entire* reconstruction alphabet (de57/59/60 constant = thrown-away bits); the cascade is the optimal distortion code, so R(0) (rate to hit D=HW(Δout)=0) = log₂#collisions = 0.74N; the de58 partition IS the codebook. **lens** Shannon R(D) / Blahut-Arimoto · **locus** w57→de58→Δout · **mech** count.
- **probe:** N=6..12 empirical p(de58-class, D=HW), Blahut-Arimoto → R(0); ≈0.74N? does the D=0 codeword set = the measured |de58|? **kill:** R(0) slope ∉[0.6,0.9] across N, or the B-A codebook unrelated to |de58|. **skeptic:** de58 is one register at one round — true reconstruction may need joint carry state (alphabet > |de58|, R(0) overshoots). **≠info-geometry/free-prob/uncertainty/coincidence:** a convex R(D) frontier (min I(Y;Ŷ) s.t. distortion), not a Fisher metric / free convolution / support product / fiber count.

### W8-RD2 · Rate cliff → 2^-2N as a +2N-bit R(0) discontinuity, sr=62 = 2^-4N  `[P4 · cheap]`
- Holding round 61 adds *two independent* refinement constraints (g1=0, h=0, each N bits), so R(0) jumps by 2N (chain rule, cross-term=0 by independence) → 2^-2N; explains Theorem 5's 2^-N undercount. Predicts sr=62 → 4N. **lens** R(D) discontinuity / successive refinement · **locus** the W[60] compliance · **mech** lower-bound.
- **probe:** N=6,8,10 R_61(0)−R_60(0) = −log₂P(g1=0∧h=0); is it 2N (not N), I(g1;h)≈0? extrapolate/spot-check sr=62→4N. **kill:** the gap is N (g1,h dependent, MI>0.1). **skeptic:** *explains* a known number — value rests on the sr=62→4N prediction, which may be unsamplable at small N. **≠coincidence-operator:** the *rate increment of the D=0 codebook* via the I(Y;Ŷ) chain rule, not feed-forward pre-image multiplicity.

### W8-RD3 · Information bottleneck → 132 = the minimal-sufficient-statistic dimension  `[P3 · cheap]`
- min I(W;T)−βI(T;collision): the 124 controllable bits compress into T; the 132 zero-control bits are incompressible relevant info (the minimal sufficient statistic); HW~74 = the bottleneck's residual distortion (132/2+~8). Joins the corank cluster. **lens** Tishby IB (β→∞) · **locus** free-words→132 bits · **mech** structural-invariant.
- **probe:** N=8..12 per-bit control via avalanche; hard-core dim/8N →132/256≈0.516? run a 2-var IB, does I(T;Y) saturate at 8N−d_hc (=124) and D_min≈d_hc/2≈74? **kill:** hard-core fraction not ~0.5 across N, or D_min not ≈d_hc/2±2. **skeptic:** "zero control" used *single-bit* flips; IB compresses over *arbitrary* functions → multi-bit interactions could shrink the true statistic below 132 (so 132 is an *upper* bound). **≠info-geometry:** the β→∞ *minimal-sufficient-statistic / compression* limit (what to throw away), the opposite regime from Fisher curvature.

## Random-graph k-core & jamming

**Through-line (the agent probed first):** the naive value/schedule constraint-graph k-core is *trivial* (density
0.996, avalanche saturates by round 4) — so all four dodge it onto the **sparse difference side** / **solution-set
geometry** / **folded-gate graph**. KC3 (freezing) is strongest (the repo *already measured* the 132 universal set =
the literal definition of frozen variables); KC2 re-derives 2^-2N from Maxwell counting (de58 = the one floppy mode).

### W8-KC1 · Active-difference 2-core collapse → the wall as a core dissolution, |2-core| = 132  `[P3 · cheap]`
- Peel the *sparse* differential-support hypergraph (only forced-nonzero dW-bits) by min-degree; a non-empty rigid 2-core (= the hard core) survives through 60 and *collapses* at 61 (the two new conditions strip the last support); k-core's discontinuous threshold = the sharp wall. **lens** k-core peeling (difference side) · **locus** the active-diff hypergraph · **mech** structural-invariant.
- **probe:** N=8..32 propagate active-diff support (reuse F839's `schedule_dep_analysis.py` on the *dW* side it was never run on), peel to the 2-core; |2-core| drops ≥2× at 60→61 while the full set shrinks smoothly? |2-core(60)|→~132 (W*_59/W*_60)? **kill:** |2-core(60)| ∉ 100–170 at N=32, or the 60→61 drop <1.3×. **skeptic:** carry-reachability *over-approximates* support → the 2-core may be an approximation artifact. **≠rigidity-matroid/SP/percolation:** integer degree-peeling (no matrix/rank, no cavity messages, no difference-spreading).

### W8-KC2 · Isostatic jamming → de58 = the one floppy mode; 2^-2N = 2 surplus contacts  `[P3 · cheap]`
- Maxwell count DOF(r)−C(r): the cascade hits isostaticity (DOF=constraints) at exactly round 60 with *one* residual floppy mode (de58, "1-D in W57"); sr=61's two conditions = two surplus contacts → jammed (over-constrained), cost = 2^-2N. Derives 2^-2N from counting. **lens** Maxwell/isostatic jamming · **locus** the per-round DOF ledger · **mech** lower-bound.
- **probe:** N=8..32 measure DOF(r) = log₂(realized difference-image size) per round; does DOF−C cross 0 at r=60, DOF(60)≈1 (= de58), DOF(61)−C(61)=−2 (→2^-2N)? **kill:** DOF(60) not ≈1, or surplus at 61 ≠2, or the zero-crossing ≠ round 60. **skeptic:** Maxwell counting ignores constraint redundancy (the rigidity-matroid wave exists to fix exactly this) — the bare count may ≠ true DOF; reproduces known numbers unless de58's *amplitude* falls out. **≠rigidity-matroid:** the *naive* scalar DOF−contacts count (modes by image-entropy), explicitly the non-matroid complement.

### W8-KC3 · Solution-set freezing → 132 = frozen variables, 0.74 = cluster entropy  `[P4 · cheap]`
- The repo's *measured* "132 universal bits (10/10 cands)" IS the textbook definition of frozen variables; the 88 free bits carry the cluster entropy 0.74N; sr=61 = the freezing/shattering threshold where the last cluster's free entropy → 0 (UNSAT). Near-identity to measured data. **lens** d1RSB freezing/clustering (measured, not cavity) · **locus** the collision solution set · **mech** structural-invariant.
- **probe:** N=8 (260 collisions, enumerable) per-bit frequency → frozen bits (0%/100%); cluster count by flip-distance; frozen-fraction→132/256≈0.52? log₂#colls/N≈0.74 = the unfrozen entropy? frozen bits = W*_59/W*_60? clusters→1 at 60, →0 at 61? **kill:** frozen-fraction ∉[0.45,0.58], or 0.74 off by >0.1, or frozen bits not the late-round set. **skeptic:** the repo's 132 is universal *across kernels*, NOT frozen-*within-one-cluster* — possible category error; cluster needs a flip-distance k (k-sensitive); N=8 may be too small. **≠survey-propagation:** *measures* the frozen set + complexity by direct enumeration (the ground truth SP only approximates), no cavity recursion.

### W8-KC4 · k-core onion of the folded gate graph → an inner shell of 128 nucleates at W59/W60  `[P2 · cheap, encoder-artifact risk]`
- After the encoder's constant-folding (cascade-zeros prune edges → genuinely sparse), the gate graph's coreness onion has an inner shell that *nucleates* at W_59/W_60 = the 128 round-bits, with the 4 anchors as the highest-coreness seeds; sr=61 adds a shell (giant k≥3-core emergence = the cost jump). F213's elimination data is *already a partial onion*. **lens** hierarchical k-core / onion (folded graph) · **locus** the Tseitin/AIG gate graph · **mech** structural-invariant.
- **probe:** N=8..32, sr=57..61: build the folded CNFBuilder incidence graph, compute coreness; max-coreness jump at 60→61? inner-shell size ≈128 = W_59/W_60 vars? 4 highest = the F286 anchors? **kill:** flat max-core (no nucleation), inner shell ∉128±20, **or (mandatory) shuffling the encoder's variable-numbering changes the onion** (→ it's allocation order, not structure — F324's artifact warning). **skeptic:** highest-risk; F324 warns the universal core is a search artifact, F213's deep chain is in arithmetic-progression IDs (smells like allocation) — the shuffle test is the whole point. **≠effective-resistance/SP/percolation:** non-spectral degeneracy peeling of the static folded circuit graph.

