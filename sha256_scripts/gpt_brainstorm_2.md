Yes — there is still a lot of search space left, but the next phase should stop thinking in terms of “one harder SAT instance” and start thinking in terms of **families, deformations, and boundary geometry**.

The big shift is:

* stop optimizing a point,
* start **steering manifolds**,
* stop asking “is this instance SAT,”
* start asking “what parameterized worlds deform into SAT worlds, and where do they bifurcate?”

I’d build the next list around that.

## The next frontier: 5 new dimensions

### 1. Continuation / homotopy worlds

You already know the hard barrier lives near zero slack. So do not jump directly into the real instance. Build **paths** from easy worlds to hard worlds and track when the solution manifold dies.

1. **Carry homotopy**

   * Start with softened carries: some carries abstracted, probabilistic, or delayed.
   * Gradually reintroduce exact carries round by round.
   * Goal: find the exact carry bundles where SAT branches die.

2. **Round homotopy**

   * Start from sr=59 or k=4 SAT instances.
   * Add one micro-constraint at a time, not whole rounds.
   * Track which tiny addition causes the first catastrophic bifurcation.

3. **Precision homotopy**

   * Solve reduced-bit versions of the late rounds: 8-bit words, 12-bit words, 16-bit words, then lift.
   * Not because reduced precision is faithful, but because it may expose invariant motifs that survive lifting.

4. **Operator homotopy**

   * Replace `Maj` and `Ch` with soft surrogates or simpler Boolean operators.
   * Interpolate back to the real operators.
   * Goal: isolate whether the bifurcation is mostly addition-driven or selector-driven.

5. **Backward-forward clamping homotopy**

   * Clamp a few bits at the output side and a few at the input side.
   * Slowly release some and tighten others.
   * This is a controlled meet-in-the-middle deformation, not plain cubing.

This whole class is high value because it gives you **phase diagrams**, not just timeouts.

---

### 2. Search over the right object: carry profiles, not message words

You have enough evidence that message bits are the wrong primitive. The true object seems closer to a **carry-divergence field**.

6. **Carry-profile genetic search**

   * Don’t evolve `M[0..15]`.
   * Evolve target profiles like:

     * where carries diverge,
     * where they agree,
     * where divergence flips sign,
     * how much divergence mass lives in rounds 57–60 vs 61–63.
   * Then solve backwards for messages satisfying those profiles.

7. **Shock-absorber search**

   * Search for assignments where late carries cancel in matched clusters.
   * Objective is not low Hamming weight, but low **carry volatility** in rounds 58–63.

8. **Carry bundle cubing**

   * Your single-addition carry cubing was too local.
   * Instead cube on **correlated bundles** of carry bits across multiple adders and adjacent rounds.
   * Choose bundles by correlation mined from sr=59 / k=3 models.

9. **Carry anti-backbones**

   * Backbones gave you forced structure.
   * Now find variables that are maximally unstable across sr=59 or k=3 solutions.
   * Those may be the true steering coordinates.

10. **Signed carry divergence**

* Track not just equal/unequal carries, but the “direction” of differential effect through the adder tree.
* A collision may need a very specific signed sequence, not generic divergence.

This is probably the single most important conceptual pivot.

---

### 3. Boundary cartography: map the death surface

You now have a lot of evidence that families abruptly go dead. Good. Turn that into a science.

11. **MaxSAT boundary surfing**

* Make sr=60 a weighted partial SAT problem.
* Let the solver violate the minimum number of end constraints.
* Study which constraints are violated first and together.

12. **Minimal correction set atlas**

* For dead families, compute small correction sets: the smallest groups of constraints that must be relaxed.
* This tells you whether the contradiction is localized or globally distributed.

13. **UNSAT core cartography**

* On constant-folded dead cells, extract and cluster UNSAT cores.
* Goal: learn whether most dead cells die for the same reason or many different reasons.

14. **Bifurcation heatmaps**

* Parameterize over:

  * kernel type,
  * padding family,
  * late-word MSBs,
  * chosen output clamps,
  * carry divergence quotas.
* Record SAT rate, UNSAT rate, timeout rate.
* You want a real atlas of the landscape.

15. **Dead-region classifier**

* Train a classifier on cheap features from a candidate:

  * round-56 state diff histogram,
  * carry entropy,
  * late-round sensitivity,
  * constant-fold reduction stats.
* Use it to triage huge families before SAT.

This turns brute force into reconnaissance.

---

### 4. Steal from other fields

Here’s the fun part.

16. **Replica exchange / parallel tempering**

* From statistical physics.
* Run many coupled searches on softened instances at different “temperatures.”
* Swap states between them.
* Great for rugged landscapes where local search dies instantly.

17. **Belief propagation on the factor graph**

* From coding theory.
* Not to solve exactly, but to estimate high-bias variables and contradictions before CDCL.
* Use it as a preconditioner or variable-ordering oracle.

18. **CEGIS for message modifications**

* From program synthesis.
* Synthesize compact message-modification rules, test them, refine on counterexamples.
* Might discover human-readable local rules instead of raw assignments.

19. **Straight-through differentiable ARX**

* Build a relaxed differentiable surrogate of the late-round network.
* Use gradient descent to find cold basins.
* Then discretize and validate with SAT.
* Ridiculous, yes. Also exactly the kind of thing that occasionally works.

20. **Model predictive control over rounds**

* From control theory.
* Treat rounds 57–63 as a system with a state and a control input (`W[57..60]`).
* Optimize a receding-horizon controller to drive the differential state toward zero.

21. **Tensor network / contraction view**

* From many-body physics.
* Build a low-width approximate contraction over truncated late-round slices.
* This might expose whether the difficulty is really global or concentrated in a few entangling gadgets.

22. **Tropical / piecewise-linear approximation**

* From algebraic geometry.
* Approximate additions and selectors in a piecewise regime map.
* Use it to identify consistent “regions” before exact solving.

Most of these will fail. That is fine. They fail differently, and that is exactly what you need.

---

### 5. Change the family, not just the solver

You have probably squeezed most of the juice out of the current MSB-kernel/all-ones neighborhood. So mutate the **family definition**.

23. **Kernel bundles instead of single kernels**

* Combine 2–4 sparse kernel motifs with controlled overlap.
* Not arbitrary GF(2) kernels — curated ones chosen for late-round carry behavior.

24. **Late-injection families**

* Search families where most structure is pushed into `M[14], M[15]`, maybe also `M[13]`.
* Treat them as tunable late perturbation channels.

25. **Round-56 state targeting**

* Instead of scanning for `da[56]=0`, scan for a richer signature:

  * `da[56]=0`,
  * low total state-diff HW,
  * constrained carry entropy,
  * preferred sign pattern in a few registers.
* This is much more expensive, but much less blind.

26. **Multi-objective candidate scanner**

* Rank candidates by a vector, not one scalar:

  * `da[56]`,
  * min HW at round 60,
  * carry volatility,
  * constant-fold UNSAT fraction,
  * backbone density in late rounds.
* Pareto front, not single best score.

27. **Counterfactual IV families**

* Not because you want a different hash.
* Because perturbing IVs in toy experiments can tell you whether the obstruction is kernel-intrinsic or IV-coupled.

28. **Alternative schedule gaps**

* You already checked some gap placement. Push farther.
* Search for weird noncontiguous freedom layouts optimized for carry steering, not classical slack counting.

---

### 6. Build meta-machines, not one-off scripts

The next big gain may come from infrastructure.

29. **Proof-guided exploration engine**

* Every UNSAT run contributes a feature vector, a core, and a folded summary.
* The next candidate generator uses those to avoid already-dead regions.

30. **Portfolio of worlds**

* For each candidate, auto-generate:

  * exact CNF,
  * folded variants,
  * softened variants,
  * partial MaxSAT,
  * BP-preconditioned ordering,
  * output-clamped variants.
* Let the ecosystem compete.

31. **Latent manifold sampler**

* Sample lots of sr=59 / k=3 / k=4 solutions.
* Embed them with PCA/UMAP or even plain spectral methods.
* Study whether the solution space has a low-dimensional chart that can be extrapolated.

32. **Near-proof engine**

* Not SAT / UNSAT only.
* Produce a “certificate of why this family is dying”:

  * dominant conflicting gadgets,
  * late-round conflict bundles,
  * recurring doomed carry motifs.

That is how you stop doing archaeology and start doing science.

---

## My top 10 “do this next” picks

If I had to choose the most promising weird directions:

1. **Carry-profile search instead of message search**
2. **MaxSAT boundary surfing + minimal correction sets**
3. **Continuation / homotopy from k=3, k=4 into sr=60**
4. **UNSAT core atlas for constant-folded dead cells**
5. **Multi-objective candidate scanner at round 56**
6. **Carry-bundle cubing mined from actual solution traces**
7. **Belief propagation as a preconditioner / variable oracle**
8. **Straight-through differentiable late-round surrogate**
9. **Kernel bundles and late-injection families**
10. **Latent manifold analysis of the k=3 / k=4 solution cloud**

---

## The truly unhinged list

These are the ones that “don’t make sense” but are exactly the kind of thing that can produce a breakthrough:

* Treat the late-round system as a **control problem** with `W[57..60]` as actuators.
* Do **persistent homology** on sampled near-solutions to see whether the near-sat space is fractured or tunnel-like.
* Train a tiny model to predict **which carry bundles are fatal** from folded statistics alone.
* Use **evolution strategies on internal state trajectories**, not messages.
* Run **replica exchange** across softened carry worlds.
* Build a **neural cube selector** trained on which constant-folded partitions die fastest.
* Search for **adversarial assignments** that maximize constant-fold simplification depth.
* Mine **frequent subcircuits inside UNSAT cores** and treat them as forbidden motifs.
* Formulate late-round matching as **syndrome decoding** on an approximate code induced by the differential dynamics.
* Try **counterexample-guided operator replacement**: swap real adders for abstractions until SAT appears, then refine only where needed.

---

## The meta-hypothesis I’d work under

Your current campaign suggests this working hypothesis:

> The real hidden variable is not message difference, slack, or even Hamming weight. It is the geometry of late-round carry-divergence manifolds under exact schedule compliance.

If that hypothesis is right, then the winning move is not “better Kissat.” It is:

* discover the right manifold coordinates,
* bias the instance into that manifold,
* then let SAT finish the last mile.

That is the exotic 5D chess version of this problem.

I can turn this into a concrete “Round 8–10” plan with script names, expected outputs, and a ruthless priority order.
