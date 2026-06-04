# W2-NT4 — Singular-series double zero → 2^-2N as two vanishing local factors   ·   VERDICT: CONFIRMED

**Card claim:** sr=61's 2^-2N is a singular series with a double-order zero: 𝔖_61 = 𝔖^{(g1)}·𝔖^{(h)}, two local densities each 2^-N living on orthogonal frequency sublattices. Probe: confirm 𝔖_61 = 2^-2N; express each factor as a character sum C_{g1}(t), C_h(s); verify each is supported cleanly (uniform marginal) and the 2-D sum FACTORIZES C(t,s) = C_{g1}(t)·C_h(s).

**Probe run:** N=8 (exhaustive, 16.7M triples / 16.2M de61=0 hits) + N=10 (946 measured collisions from `gap_rows.csv`), throttled. Confirmed the rank-2 identity, ran the exhaustive independence test (rebuilt `gap_analysis.c` at N=8 to a lab-side binary, ran in `/tmp`), computed the 2-D additive-character factorization residual max|C(t,s) − C(t,0)C(0,s)|, and — crucially — judged it against a shuffled-independent NULL (permute h vs g1, preserving both marginals) to subtract the 1/√n sampling noise of the empirical characteristic function.

**Result (numbers):**
- **Rank-2 exact:** g2 = g1 + h (mod 2^10) for **946/946** collisions. ⇒ sr=61 (g1=0 & g2=0) ⇔ (g1=0 & h=0), two conditions.
- **Exhaustive N=8 independence:** P(g1=0)=0.00392, P(h=0)=0.00392 (each ≈2^-N); P(g1=0 & h=0)=1.419e-5 vs product 1.537e-5 → **ratio 0.923**. Over all 16.7M triples, h is uniform (max-bin/mean=1.02), P(h=0)=2^-N.
- **Factorization vs null:** real residual 0.157 @N=8 (null mean 0.136, max 0.161 → **INSIDE**); 0.081 @N=10 (null mean 0.074, max 0.090 → **INSIDE**). The raw residual is pure finite-sample noise, indistinguishable from constructed independence.
- **Clean local densities:** max |C_{g1}(t≠0)| = 0.045, max |C_h(s≠0)| = 0.048 @N=10 → each marginal ≈ uniform (a flat local density of weight 2^-N).
- **Lever premise:** χ²/dof (8×8) = 0.95 @N=8, 1.47 @N=10 (≈1); Pearson(g1,h) = −0.15 @N=8, +0.02 @N=10 → no coupling.

**Kill_criterion:** "Dead if C(t,s) doesn't factorize (g1,h share frequency support) — then 2^-2N is a single coupled condition." — **fired? no.**

**Verdict reasoning:** The card's structure is positively reproduced. (1) g2 = g1 + h is exact (rank-2), so sr=61 genuinely splits into g1=0 AND h=0. (2) The 2-D character sum factorizes: its residual is statistically inside an independent-by-construction null at both N, and the exhaustive N=8 joint equals the product to ratio 0.923. (3) Each marginal character is flat → each is a *clean local density* of weight 2^-N, exactly the "two factors each 2^-N" the card names. This lands on the Wave-1-surviving two-conditions structure (prior finding #3), which the playbook says a card may legitimately CONFIRM. Beyond relabeling, the probe establishes the lever premise the card predicts (g1 ⊥ h, so the 2× penalty is separable and removable only by re-coupling the two obstructions), corroborated by χ²/dof≈1 and ~0 Pearson.

**Cross-check / skeptic note:** The honest risk (flagged in the card) is re-skinning the existing `coincidence_variety` independence result. Guards applied: the factorization is *tested against a permutation null*, not assumed, so a small residual cannot masquerade as confirmation; and the result triangulates from three independent angles (exact rank-2, exhaustive 16.7M-triple ratio, and the noise-calibrated character factorization at two widths). What would overturn it: a residual that exceeds the null band at larger N (a real shared frequency), or a coupling lever that fails to move the exponent in a built SHA variant — untestable here without re-engineering the schedule.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-NT4.py`
