# W8-CL4 — Cluster complex → 0.74 as the exchange-graph growth rate   ·   VERDICT: KILLED

**Card claim:** Cascade collisions = vertices of a cluster complex (edge = differ by one round's offset = one mutation); the de58 partition = its facets; 2^0.74N = the complex's exponential growth, 0.74 = its log-density of valid clusters (pruned sub-fan of the seed cube).

**Probe run:** EXACT sr60 collision lists (cols w57,w58,w59,w60). N=8: 260 collisions (regenerated from the repo C enumerator `ga_8`, run in `/tmp` — READ-ONLY toward the repo). N=10: 946 collisions (repo `coincidence_variety/gap_rows.csv`). (1) Built the exchange graph (edge = two collisions differ in exactly one of the 4 free words = one mutation) and measured degree distribution / regularity. (2) Tabulated log₂(#colls)/N vs the canonical fit. Throttled: yes.

**Result (numbers):**
- **Exchange graph NOT regular:** N=8 — mean degree **0.069**, variance 0.064, **242/260 collisions isolated (degree 0)**, degrees ∈ {0,1}. N=10 — mean degree **0.076**, variance 0.077, **877/946 isolated**, degrees ∈ {0,1,2}. (Card expects regular degree ≈ rank ≈ 4.)
- **0.74 not a sharp finite-N density:** canonical counts 49/260/946/2955 at N=4/8/10/12 give log₂(C)/N = **1.404 / 1.003 / 0.989 / 0.961** — nowhere near 0.74. The real law is the *affine* fit **log₂(C) = 0.740·N + 2.47** (carry_structure_unified.md): 0.74 is the asymptotic **slope**, the +2.47 intercept dominates at reachable N.

**Kill_criterion:** "graph NOT regular (scattered degrees), OR 0.74 strongly kernel-dependent (>0.1 spread)." — **fired? yes** (graph is overwhelmingly degree-0 dust with scattered {0,1,2} degrees — not regular).

**Verdict reasoning:** Both prongs kill it, as the catalog ("expect fail") and prior-finding #2 ("0.74 is DEAD as a derivable sharp constant") anticipated. (1) The "cluster complex" premise is false: under the card's own edge rule (differ by one round's offset), the collision set is **almost totally disconnected** (93–94% isolated vertices, mean degree ≈ 0.07) — not a regular degree-4 exchange graph, not even connected. (2) 0.74 is the *slope* of an affine law with a large +2.47 intercept, so the finite-N "log-density" log₂(C)/N is 0.96–1.40 at reachable N, not a sharp 0.74 — the constant is not derivable as a quantitative growth rate from any f-vector here.

**Cross-check / skeptic note:** The N=8 count (260) and N=10 count (946) are the canonical exhaustive values, and the C enumerator reproduced 260 exactly when re-run in /tmp, so the collision sets are exact (not sampled). One could object the "mutation" edge should be on the *de58 facet* rather than raw free-word difference; but the card explicitly defines the edge as "differ by one round's offset = one mutation," which is what was tested, and it yields a disconnected dust — the exchange-graph hallmark (regularity) is absent on the card's own terms. 0.74 remains a fitted slope, never an independently derived sharp constant.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W8-CL4.py`  (N=8 list: re-run repo `ga_8` in a scratch dir to make `/tmp/cl4_work/gap_rows.csv`)
