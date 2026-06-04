# W3-LL4 — Schedule taps as a covering design → collision peaks at design-resonant N   ·   VERDICT: KILLED

**Card claim:** Read lags {2,7,15,16} as a design block; its difference multiset Δ tiles Z_N; GAPS in coverage (high non-uniformity) = surviving free directions = collision-rich N (claim: N=10 is a coverage gap). The 132 ≈ rotation fixed-point count.

**Probe run:** N=4..12 against measured best-kernel yields (paper_figures_data.md Fig 2), plus out-of-sample N=18,20, throttled (trivial compute). Computed the tap difference-multiset Δ mod N, two coverage-non-uniformity scores (normalized L2 deviation of the residue histogram from flat; fraction of uncovered residues), and correlated each against the collision-count residual log2(yield)−0.74·N. Computed rotation fixed-point counts (Σ0,Σ1,σ0,σ1 amounts) vs the claimed 132.

**Result (numbers):**
- **Pearson r(U_nonunif, residual) = +0.080; r(frac_uncovered, residual) = +0.166** — both **far below |r|=0.3**. The tap-Δ coverage uniformity carries essentially no signal about the collision residual.
- **N=10 is not a coverage gap aligned with a peak:** U(10)=0.500 (rank **5/9** in non-uniformity, middling), yield rank 5/9. The actual yield peak is **N=9** (log2=13.80, U=0.935) — and the card stakes N=10. N=10 is a NON-peak, exactly matching PH5 (N=10 trough, N=9 peak, N-mod-4 the real driver).
- **Rotation fixed-points nowhere near 132:** sum of gcd(r,N) over the 10 rotation amounts = 14–22 across N; at N=32 it is **14**, not within 20 of 132. (132 is the hard-core *output-difference* bit count = a,b,e,f registers ⊕ 4 scattered, unrelated to rotation fixed-points — the 132-corank category error, lead #1.)
- Out-of-sample: N=18 has the highest U (1.118) of any N tested, so the "high U = collision-rich" rule would predict N=18 as a peak — untestable here, but it does NOT single out N=10, contradicting the card's premise.

**Kill_criterion:** "Dead if |r|<0.3, or fixed-points nowhere near 132." — **fired? YES on BOTH clauses** (|r|=0.08 and 0.17 <0.3; fixed-points=14–22, not ≈132).

**Verdict reasoning:** KILLED, both kill clauses independently. The covering-design coverage-uniformity has no correlation with the collision yield residual (|r|≤0.17), and the "132 ≈ rotation fixed-points" identification is off by ~6–9× (it is the well-known 132-corank category error). The N=10 resonance premise is empirically false — N=10 is middling-to-trough, the peak is N=9, and the dominant yield structure is the N-mod-4 oscillation (a number-theoretic effect), exactly as PH5 (KILLED) and CT3 (KILLED) found. The N-resonance angle fails again (lead #4).

**Cross-check / skeptic note:** The card's own skeptic — "13 N-values + 1 bump = easy chance fit" — is the right worry, but it doesn't even get a chance fit: the correlation is null. To be maximally fair, U_nonunif IS highest at N=9 (0.935), the true yield peak, so a covering-design story might have *some* legs at N=9 — but it points away from the card's N=10, and the global correlation is still ~0. This converges with PH5 (Bragg, KILLED at N=10) and W2-CT3 (IIR poles, KILLED at N=10): no mechanism singles out N=10, and N-mod-4 — not coverage — drives the yield.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-LL4.py`
