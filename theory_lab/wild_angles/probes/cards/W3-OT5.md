# W3-OT5 — Collision = stable matching; sr=61 = loss of the Hall condition   ·   VERDICT: SURVIVES

**Card claim:** Forward × backward boundary states as a bipartite graph (edge = carry-consistent); a collision = a matched edge; sr=61 = the round the perfect matching (Hall) fails, the 2^-2N = the deficiency. Probe: build the consistency graph at sr=60 vs 61, Hopcroft–Karp max-matching; does matching size track collision count and deficiency jump by ~2^-2N?

**Probe run:** Bipartite graph with LEFT = per-message match values g1 ∈ Z/2^N, RIGHT = compatibility values h ∈ Z/2^N; **edge = LOCAL carry-realizability of the (g1,h) residue pair** (NOT "is-a-collision" — defeats the circularity skeptic). (A) Explicit Hopcroft–Karp at N=6 (64×64) on the realizable-cell relation (residues of the N=10 carry relation). (B) sr=61 deficiency from the FULL forward de61=0 population (enumerator, N=8). Throttled.

**Result (numbers):**
- N=6 graph: 849 realizable cells / 4096 (density 0.207); **Hopcroft–Karp max matching = 64/64** → a perfect matching EXISTS at sr=60 → **Hall satisfied**.
- sr=61 forces the matched edge to (g1,h)=(0,0). Surviving fraction = P(both) = 1.419e-05 (2^-16 = 1.526e-05).
- **Hall deficiency / collapse exponent = -log2 P(both)/N = 2.013** (card predicts 2.0) → 2^-2N.
- Deficiency is **codim-2**: P(both) ≈ P(g1=0)·P(h=0), independence ratio 0.923 → two independent 2^-N costs.

**Kill_criterion:** "matching ≠ count, or no deficiency jump" — **fired? no.** (perfect matching at sr=60; deficiency collapse exponent 2.013 ≈ 2 at sr=61)

**Verdict reasoning:** The reframing is consistent and lands on the verified rank-2 wall: at sr=60 the local-consistency bipartite graph admits a perfect matching (Hall holds, collisions exist), and forcing the sr=61 demand collapses the admissible neighborhood to the single (0,0) cell with deficiency exactly 2^-2N (exponent 2.013), factorizing as the two independent g1=0, h=0 conditions. The Hall-deficiency = the codim-2 collapse is a faithful re-description of the verified 2^-2N. I mark SURVIVES (not CONFIRMED) because the "matching size tracks the collision COUNT" clause was only weakly checked (realizable-cell count, not a positive count-vs-matching fit), and the N=6 graph density inherits from collision residues.

**Cross-check / skeptic note:** The skeptic's circularity warning is the real risk: the EDGE relation at sr=60 is built from observed (g1,h) residues, which is collision-adjacent — so "Hall holds at sr=60" is partly by construction (a near-regular relation always matches). What is genuinely independent and load-bearing is the **deficiency = 2^-2N**, taken from the full forward de61=0 enumerator population (16.2M hits), not from collisions — and it agrees with OT1/PH1/IN3/NT4 (the verified rank-2 structure, ratio ~1). A deeper probe would build the edge purely from the round-60 carry rule at multiple N and fit matching-size vs the 260/946 counts directly. As stands: the Hall/2^-2N identity is real; the "matching = count" half is plausible but not positively demonstrated.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-OT5.py`
