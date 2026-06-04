# W3-OT3 — Kantorovich potential whose gradient IS the cascade   ·   VERDICT: KILLED

**Card claim:** Duality gives potentials φ,ψ; tightness set φ⊕ψ=C = collisions, and ∇φ = the cascade map (collisions = level sets, not points). The c-transform argmax should reproduce the cascade on enumerated collisions.

**Probe run:** The cascade map is M2 = M1 + casoff = a translation by t in the round-60 gating coordinate Z/2^N. Built μ = uniform on a random forward support S (K=24), ν = the cascade push-forward S+t, cost C[x,y] = carry-HW(y−x) (the card's specified cost), and solved the EXACT min-cost assignment (Hungarian) at N=5,6. Measured how often the OT optimal map T satisfies T(x)=x+t (= cascade). Control: a non-cascade random target. Robustness over 6 seeds/shifts. Throttled.

**Result (numbers):**
- OT map agrees with the cascade on the cascade-pushforward data: **0.0% (N=6), 4.2% (N=5)** — i.e. ~100% disagreement.
- Robustness (N=6, 6 seeds, t varied): cascade-agreement **0.0–8.3%** in every run.
- Cause: matched-cost ranges **0..2/0..3**, but carry-HW(t)=2–5. The assignment finds **cost-0 off-translation pairs** (carry-HW is zero for many non-translation pairs), so the OT optimum is strictly cheaper than — and structurally unlike — the cascade translation.

**Kill_criterion:** "disagrees on >20%" — **fired? YES** (100% disagreement, robust across seeds).

**Verdict reasoning:** Under the card's OWN cost (carry-HW), the Kantorovich optimal map is NOT the cascade — it disagrees ~100%. The reason is structural: carry-HW(y−x) is highly degenerate (many off-diagonal pairs cost 0), so it is not a Monge-regular cost for which translation is optimal; the OT solver actively prefers cheaper non-cascade matchings over the +casoff translation. ∇φ therefore does not equal the cascade. The identity the card wants requires a strictly convex transport cost, which carry-HW is not.

**Cross-check / skeptic note:** The card's skeptic ("duality always exists; the content is φ=cascade") cuts the other way here — duality exists, but its content is FALSE under carry-HW. Note the would-be-tautology trap I tested for: even for a perfectly translation-invariant cost, OT between μ and its exact translate would be solved by the translation *if* the cost were convex; carry-HW's degeneracy breaks even that. A strictly-convex cost (e.g. squared lattice distance) WOULD make the translation optimal and recover ∇φ=cascade — but then the identity is the trivial "OT between a measure and its translate is the translation," restating M2=M1+casoff with no new mechanism. Either way the carry-HW-specific claim is dead.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-OT3.py`
