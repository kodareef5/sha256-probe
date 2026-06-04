# W7-CG3 — 2^-2N = the P/N-position measure (density of winnable positions)   ·   VERDICT: KILLED

**Card claim:** A boundary position is an N-position (winnable) iff a free-word move reaches g1=0 ∧ h=0; two independent 2^-N conditions ⇒ N-target has measure 2^-2N. **Predicts sr=62 → 2^-3N.**

**Probe run:** (A) From the repo's measured N=10 collision set (`gap_rows.csv`, 946 sr60 collisions) verified the structural identity that *defines* the two conditions. (B) The load-bearing test: extended the faithful mini-SHA(N) cascade to round 61 and measured the four sr=62 gap variables (g1_60, h_60, g1_61, h_61) over 400k (N=8) / 250k (N=10) random cascade prefixes, to decide the card's 2^-3N prediction vs the mechanism's 2^-4N. Throttled: yes.

**Result (numbers):**
- **(A)** g2 = g1 + h (mod 2^N) holds **946/946**; g1 spans 627 distinct values, h 620 — so sr61 ⟺ g1=0 ∧ h=0 exactly. CG3 lands precisely on the established two conditions.
- **(B)** All four gap marginals ≈ 2^-N: at N=10, P(g1_60=0)=1.06e-3, P(h_60=0)=9.84e-4, P(g1_61=0)=9.88e-4, P(h_61=0)=7.52e-4 (target 2^-10=9.77e-4). Product of the 4 marginals ⇒ log2 ≈ **-40** at N=10 (= -4N) and **-32** at N=8 (= -4N). sr=61 reproduces 2^-2N (P(g1_60=0 ∧ h_60=0) ≈ 2^-2N). **sr=62 = 2^-4N, NOT the card's 2^-3N.**

**Kill_criterion:** "N-fraction ≠ 2^-2N (conditions correlate, or carry structure leaks extra winnable moves)." — **fired? partial/no for sr=61** (it IS 2^-2N), **but the card's keep-earning sr=62→2^-3N prediction is FALSIFIED** (it is 2^-4N).

**Verdict reasoning:** Per prior-finding #3, landing on the two conditions g1,h is the *established* mechanism, so the bare 2^-2N reproduction is a rename — exactly what Part A shows (g2=g1+h, 946/946). The card itself concedes "risks relabeling the known 2^-2N — the sr=62→2^-3N prediction is what earns its keep." That prediction is wrong: each *enforced round* contributes **two** independent 2^-N conditions (g1 and h), so holding one more round (W[61]) for sr=62 multiplies by 2^-2N, giving **2^-4N**, not 2^-3N. The card is internally inconsistent — it asserts 2 conditions for the first held round (2^-2N) yet only 1 per additional round (2^-3N). KILLED: a rename of the known result, whose one novel quantitative claim is falsified.

**Cross-check / skeptic note:** The four-marginal factorization is exactly the method the repo used to establish 2^-2N for sr=61 (independence ratio 1.005 over 1.07B). Rare-event joint counts here are sampling-noisy (~1 event per 250k), but the *marginals* — which decide 3N vs 4N — are clean and each ≈ 2^-N. A defender could argue "sr=62 frees one extra word so only one new condition"; but freeing W[61] does not remove the requirement that *both* messages match the schedule there (g1_61 AND h_61), which is what the measurement shows. No new content survives; the impartial P/N census adds a label, not a number.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-CG3.py`
