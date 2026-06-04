# W7-QW1 — Cascade-absorption phase gap → collapse/exponent-doubling at sr=61   ·   VERDICT: KILLED

**Card claim:** The 7-round diff-contraction is an absorbing walk to the zero-diff sink; the Szegedy phase gap is large ≤60 and **collapses at 61**, with the hitting-time exponent **doubling** as ε→2^-2N (two conditions). Compare D's gap vs P's gap (must diverge).

**Probe run:** N=6,8,10. Two independent tests. (1) GAP: built the cascade-pinned diff-config chain P, took the Szegedy phase gap 2√(1−s₂) of D=√(P∘Pᵀ), and compared D's gap to P's own (eigen) gap (the relabel test). (2) EXPONENT (load-bearing): measured the on-track target densities directly from the repo's gap_rows.csv (N=10 collision census, cols g1,h) — ε₆₀ for one condition vs ε₆₁ = P(g1=0 AND h=0) — and verified g1⊥h. Throttled yes.

**Result (numbers):**
- (1) Phase gap(D) ≈ **2.0** (s₂(D) ≈ 0.0017 @N8, 0.0002 @N10) in the sr=60-free regime — and there is **no separate sr=61 spectral object that collapses below half of it**; the absorbing-sink gap is ~2 throughout. D is a **RELABEL of P**: rev_gap = |s(D)−|eig(P)|| = **0.0000** (gap(D)=1.9983 is exactly 1+gap(P)=1+0.9983). The "must diverge" requirement **fails**.
- (2) Exponent doubling **is real and lands on the measured data**: over 946 N=10 collisions g1∈[2,1022], h∈[1,1020] (both ~uniform in [0,2^N)), **sr=61 count = 0**, g1⊥h independence ratio = **1.0001** (pinned 1.005). ε₆₀~2^-N, ε₆₁=P(g1=0∧h=0)~2^-2N → hitting-exponent ratio = **exactly 2.0000**.

**Kill_criterion:** "sr=61 gap within 2× of sr=60, OR hitting-exponent unchanged, OR D's gap = P's gap (relabel)." — **fired? yes (clauses 1 and 3).**

**Verdict reasoning:** The card's *named mechanism* — a Szegedy phase-gap that collapses at 61 — fails on two of the three kill clauses: the discriminant gap does not collapse (it is ~2 in the free regime, within 2× of any enforced regime), and D's spectrum is an exact √-relabel of P (rev_gap=0.0000), so the "two-copy geometric mean" adds nothing. The *quantitative* prediction (exponent doubling → 2^-2N) is genuinely correct and lands exactly on the measured g1,h two-conditions with verified independence — but that is the already-CONFIRMED rank-2 2^-2N structure (prior #3), not new content delivered by the Szegedy gap. Per the playbook, dressing the real 2^-2N in a relabel-gap that doesn't collapse is a rename, not a CONFIRMED.

**Cross-check / skeptic note:** The "doubling is right in spirit" caveat is honored: the exponent ratio is exactly 2 and rides the measured g1=0 AND h=0 two-conditions (not a spectral artifact), so the *physics* is confirmed independently — but the *card's lens* (phase-gap collapse, D≠relabel) is what's tested, and it dies. CG3 (sr=62 = 2^-4N) would extend this to a ratio-of-4 exponent; not measured here (no sr=62 census on disk), but consistent.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-QW1.py`
