# W5-HY3 — δ-hyperbolicity → collisions rare & rigid; de58 = the tree axis   ·   VERDICT: KILLED

**Card claim:** Thin-triangle hyperbolic difference graph ⇒ unique geodesic corridors ⇒ rigid, rare collisions; 132/HW~74 = sphere-concentration; de58-grows/others-constant = a *tree-graded* structure with **de58 the branching axis**.

**Probe run:** N=4 cascade-eligible, exhaustive (throttled). Built the difference-state graph of the cascade tail (vertices = distinct 8-tuple XOR difference states at rounds 56..60 across all cascade paths; edges = actual one-round transitions). Computed (1) the Gromov 4-point δ and δ/diameter, (2) the branching factor per round on the full graph, and (3) the **collision-restricted** de-sets (the repo's actual de57=de59=de60=1, de58 varies) to test the "de58 axis" claim fairly.

**Result (numbers):** |V|=111, |E|=110 (= V−1, i.e. **the graph is a tree**); db56=0x2, hw=1.
- (1) **δ = 0.0**, diameter = 8, **δ/diam = 0.000** (constant).
- (2) Branching factor on the full graph: round 57 → **5**, round 58 → 4, round 59 → 3, round 60 → 1. **Branching peaks at round 57, monotonically decreasing — NOT at de58.**
- (3) Collision-restricted de-sets: |de57|=1, |de58|=**2**, |de59|=1, |de60|=1 → de58 the only varying axis, and |de58|=2 = 2^hw(db56) (MATCH) — but only under the collision restriction.

**Kill_criterion:** "δ grows with diameter (flat), OR branching not on de58" — **fired? YES (second arm)**: on the natural difference graph the branching axis is round 57 (factor 5), not de58 (factor 4).

**Verdict reasoning:** Two independent reasons to KILL. First, the δ-hyperbolicity is **trivially true and evidentially empty**: the difference graph is literally a tree (E = V−1 = 110), so δ = 0 by tautology — exactly the "finite graphs are trivially hyperbolic" trap the card's own skeptic note warned about, and δ/diam is a flat 0, not a bounded-vs-growing trend that could distinguish hyperbolic from flat. Second, the headline structural claim "de58 = the branching axis" is **false on the honest (unrestricted) reachability graph**, where branching is *maximal at round 57* and decreases through 58→59→60. It only becomes true after restricting to collisions — and that restriction simply re-expresses the **already-closed de58 thread** (finding #6: |de58| = 2^hw(db56), Maj/AND image-count), which is the only number that matches (2 = 2¹). So the card delivers a tautological δ=0, a directionally-wrong branching axis, and a single number that restates a closed thread under a cherry-picked stratum.

**Cross-check / skeptic note:** What *would* rescue it: a δ/diameter ratio that stays bounded *while the graph is genuinely not a tree* (so δ=0 carries information) AND a branching concentration on de58 *without* hand-restricting to collisions. Neither holds. The collision-restricted |de58|=2=2^hw(db56) is real and convergent with the repo (DE_SIZES N=4..10), but it is the closed de58 thread, not a new hyperbolic invariant — and "de58 the branching axis" is contradicted by round 57 branching more on the full graph. The rigidity/rarity intuition (collisions are few) is true but generic; nothing here adds a hyperbolic-geometry number beyond the closed de58 law.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HY3.py`
