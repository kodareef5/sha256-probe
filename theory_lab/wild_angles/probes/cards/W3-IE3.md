# W3-IE3 — sr=61 = a Rauzy fixed point; 2^-2N = a two-endpoint coincidence   ·   VERDICT: CONFIRMED

**Card claim:** sr-depth = how deep Rauzy induction simplifies before a self-similar fixed point (~60); crossing it needs *two* interval endpoints to coincide (g1=0 AND h=0), each codim-1 → product 2^-2N; predicts sr=62 ~ 2^-3N.

**Probe run:** N=10 collision list (`gap_rows.csv`, 946 collisions) for the two-distinct-endpoints / support-identity test; repo exact enumerator `gap_analysis.c` at N=8 (live compile+run) for codim-1 and independence over the FULL forward de61=0 population. Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- Support identity **g2 = g1 + h (mod 2^N) holds for all 946 collisions** — the two coords span the gap plane (rank-2).
- Two distinct endpoints: 240 of 627 g1-values map to ≥2 distinct h (max 5 distinct h for one g1); g1 does not pin h and vice-versa → g1 and h are SEPARATE coordinates, not one collapsed endpoint.
- Forward population (enumerator, N=8): P(g1=0) = **0.003924** ≈ 2^-8; P(h=0) = **0.003916** ≈ 2^-8 (two codim-1 endpoints); P(both) = **1.419e-05** ≈ 2^-16.
- Concentration exponent −log2 P(both)/N = **2.013** (card predicts 2.000); independence ratio P(both)/[P(g1=0)·P(h=0)] = **0.923** (~1 ⇒ independent).

**Kill_criterion:** "fixed point at the wrong depth, OR the two conditions map to the *same* endpoint (predicting 2^-N)" — **fired? NO**

**Verdict reasoning:** The card lands exactly on the genuine rank-2 / two-conditions structure (prior finding #3, now 6× confirmed). g1 and h are two *distinct* codim-1 endpoints, each ≈2^-N, statistically independent (ratio 0.92), with product giving a measured 2^-2N (exponent 2.013) on the FULL forward population — not by construction. This is the structure the warning required to "land on the two-conditions"; it is not a framing that merely *permits* 2^-2N. The kill's failure mode (g1=0 ⇒ h=0 → 2^-N) is explicitly ruled out.

**Cross-check / skeptic note:** The CONFIRM is of the **two-endpoint / 2^-2N identity only**, NOT the Rauzy-renormalization *mechanism* nor the depth ("~60") nor the distinctive sr=62=2^-3N prediction (out-of-sample — needs a 62-round backward enumerator, not run here). Skeptic catch: the collision list has zero g1=0 and zero h=0 rows (these are sr=60 collisions that did *not* cross to sr=61), so the decisive codim-1 numbers necessarily come from the full-population enumerator, which is non-circular and independently reproduces 2^-8/2^-8/2^-16. The structure converges with W3-OT1, PH1, NT4, RG1-B, OT1 — convergence, not coincidence. The 2.013 exponent matches; the Rauzy *story* is decoration unless sr=62 confirms 2^-3N.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-IE3.py`
