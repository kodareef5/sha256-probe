# W1-PH5 — Bragg / phase-matching → the N=10 interference   ·   VERDICT: KILLED

**Card claim:** The schedule recurrence is a diffraction grating (taps {2,7,15,16} = slits, rotation amounts = phase delays); the empirical N=10 constructive interference is a Bragg commensurability of the scaled rotations. A commensurability score should peak at N=10 and predict the next resonant N (which should show a yield anomaly).

**Probe run:** Computed scaled rotation sets {round(k·N/32)} for N=4..16 (Sigma0/Sigma1/sigma0/sigma1). Defined **four** principled Bragg/commensurability scores (to avoid post-hoc single-score fishing): phase_coherence (ring structure factor |Σ exp(2πi r/N)|), tap_commensurate (fraction of (rotation,tap) pairs with r·L≡0 mod N), gcd_resonance (mean gcd(r,N)/N), pairwise_diff (fraction of degenerate-phase rotation pairs). Correlated each with measured collision yield (paper_figures_data.md Fig 2). Throttled.

**Result (numbers):**
- **No score peaks at N=10.** Peaks land at N=9 (phase_coherence), N=4, N=4, N=4 (the other three). N=10 is unremarkable in every score.
- **The premise is empirically false:** measured yield is N=9 → 14263, N=10 → 1467. **N=10 is a relative *trough*, not a bright fringe**; N=9 dwarfs it by ~9.7×. The dominant structure in the yield is the N-mod-4 oscillation, not an N=10 resonance.
- Correlations with yield: phase_coherence +0.60 (weak, and it points at **N=9** not N=10); the other three are *negative* (−0.69, −0.62, −0.65). The sr60/MSB yield (260@N=8 → 946@N=10) is a smooth ~2^0.93N rise with no N=10 anomaly either.

**Kill_criterion:** "Dead if the score doesn't peak at N=10 or its predicted second resonance shows no yield anomaly." — **fired? yes**

**Verdict reasoning:** Kill clause A fires unambiguously: not one of four reasonable commensurability scores peaks at N=10. Worse, the card's foundational premise — that N=10 is an empirical constructive-interference peak — is contradicted by the data: N=10 is a yield *trough* (N=9 is the peak). The "N=10 is special" framing traces to N=10 having been the *gold-standard sampling point* for the 1e9-sample independence test, not to any yield resonance. This is precisely the card's own skeptic warning realized: *"with one data point (N=10) the score is easy to overfit post-hoc; only a correct prediction saves it"* — and there is nothing at N=10 to predict. KILLED (as stated).

**Cross-check / skeptic note:** A clean negative; not softened. To be fair to a Bragg story, the one genuine signal is that phase_coherence peaks at **N=9** (the actual yield peak) with r=+0.60 — so a diffraction reframing might have legs *at N=9*, but the card specifically stakes N=10, which fails. Could a different score rescue N=10? Possibly by construction (4 free score-knobs over ~9 data points invites overfit), but that would be the failure mode the card itself names, not a save. The N-mod-4 oscillation (a number-theoretic, not optical, effect) is the real driver of the yield pattern. Independent corroboration: in both yield measures available (best-kernel Fig 2 and sr60-MSB counts), N=10 shows no anomaly.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W1-PH5.py`
