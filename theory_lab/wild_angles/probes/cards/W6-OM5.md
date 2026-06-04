# W6-OM5 — QE-depth → the wall as loss of bounded definability / Skolem functions   ·   VERDICT: KILLED

**Card claim:** below 60 the cascade gives definable Skolem functions (solve for carries) → the collision predicate eliminates to bounded depth (short certificate); at 61 no joint Skolem function exists → elimination depth (∝ ANF degree after carry-projection) explodes. Catalog flag: **disqualify early — run the kill first.**

**Probe run:** N=4,5,8 exact (throttled). Built the collision indicator as a Boolean function f_r(w57) of the free word's N bits (w58=w59=w60=0; tail eliminated by enumeration) for r∈{≤60 (cube), 61 (de61=0), 63 (collision)}, computed the ANF via fast Möbius transform, and read the ANF degree (max possible = N) and term count vs round.

**Result (numbers):**
| N | r-condition | ANF degree (max=N) | #ANF terms |
|---|---|---|---|
| 4 | cube r≤60 | 0 | 1 |
| 4 | de61=0 r61 | **4** | 8 |
| 5 | de61=0 r61 | **5** | 1 |
| 8 | de61=0 r61 | **8** | 8 |

The de61=0 indicator hits **degree = N exactly** at every N (fully saturated). The cube (r≤60) is the constant 1 (degree 0). The r63 slice (w58=w59=w60=0) is empty (no collisions there), degree 0.

**Kill_criterion (run first):** "ANF already ≈degree-N for all r≥57 (the repo's 'ANF dense' memo is a live threat)." — **fired? yes.**

**Verdict reasoning:** KILLED, disqualified early exactly as the catalog anticipated. There is no "bounded QE-depth ≤60 that explodes at 61" regime: for rounds ≤60 the predicate is *constant* (degree 0) — bounded only because the free cascade imposes no condition (nothing to Skolemize), not because of a clever bounded-depth elimination — and the instant a real condition appears (r=61, de61=0) the ANF is **already at maximal degree N** (4/4, 5/5, 8/8). This directly confirms the repo's "ANF dense in message vars (degree N)" memo. The card needs a sub-saturated low-degree predicate below the wall that climbs to degree N at 61; instead the degree is 0 then immediately N, with no intermediate "bounded depth" stage and no transition *at* 61 specifically.

**Cross-check / skeptic note:** ANF degree is the card's own (acknowledged loose) proxy for QE-depth, and it shows no transition — the kill is on the proxy the probe was told to run. The r63 slice is degenerate (zero collisions at w59=w60=0), but the verdict rests on r61, where the degree is unambiguously maximal at all three N. The de61 indicator is sparse in *term count* (8 terms at N=4 and N=8) yet maximal in *degree* — sparsity in coefficients does not give bounded QE-depth; the top-degree monomial is present. A carry-projected formula could in principle be shorter, but the message-variable ANF (what the probe builds) is degree-N, matching the dense-ANF prior.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OM5.py`
