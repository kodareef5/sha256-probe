# W3-OT6 — Rotation constants as a coordination mechanism; N=10 = a focal point   ·   VERDICT: KILLED

**Card claim:** The σ rotations are a correlation device; N=10 constructive interference = a Schelling focal point where period-N patterns stay phase-locked (rotation 10 ∈ Σ1). Probe: collision counts N=4..14 vs a per-N phase-alignment score of the rotation set; predict the next peak N out-of-sample.

**Probe run:** Computed scaled rotation sets r=round(k·N/32) for the SHA-256 constants (Σ0={2,13,22}, Σ1={6,11,25}, σ0={7,18,3}, σ1={17,19,10}). Phase-alignment score = order parameter |mean exp(i·2π·r/N)| (the card's "phase-locked" coherence) for all rotations and Σ1-only, N=4..14. Correlated with log2(collision yield) from paper_figures_data.md Fig 2. Throttled.

**Result (numbers):**
- phase-coherence(all rotations) **peaks at N=4**; coherence(Σ1) **peaks at N=6**. Collision **yield peaks at N=9** (14263, the actual global anomaly).
- **N=10 phase-coherence rank = #9 of 11** (nearly the LEAST phase-aligned); N=10 yield rank = #5 of 9 (a TROUGH: 1467, vs N=9's 14263, ~9.7× larger).
- Pearson r(phaseCoh(all), log2 yield) = **−0.434**; r(Σ1, log2 yield) = −0.363 (NEGATIVE, not positive).
- Out-of-sample: no score's peak coincides with the yield peak. The card's premise "N=10 is the anomaly" is false (N=9 is).
- Factual error in the card: "rotation 10 ∈ Σ1" — 10 is the small-σ1 SHR **shift**, not a Σ1 rotation (Σ1 = {6,11,25}).

**Kill_criterion:** "score uncorrelated with the per-N anomaly" — **fired? YES** (correlation is negative; no score peaks at N=10; N=10 is a yield trough).

**Verdict reasoning:** Every clause fails. No phase-alignment score singles out N=10 (it ranks #9/11 in alignment); the correlation with yield is negative; and the foundational empirical premise is wrong — N=10 is a yield trough, N=9 is the peak. This is the THIRD independent kill of an "N=10 is special" claim (after PH5: N=10 a yield trough via 4 commensurability scores; CT3: N=10 not singled out), directly confirming prior finding #4. The "rotation 10 ∈ Σ1" hook is also factually incorrect.

**Cross-check / skeptic note:** The card's own skeptic ("one bump N=10 is easy to overfit") is generous — there is no bump at N=10 to overfit; it is a trough. The real driver of the per-N yield pattern is the N-mod-4 oscillation (a number-theoretic effect: the odd/even and mod-4 structure of round(k·N/32)), not optical phase-locking; and the one genuine signal (phase-coherence peaking near the actual yield peak) points at N=9/N=4–6, never N=10. Independently corroborated by both yield measures (best-kernel Fig 2 and the sr60-MSB counts in PH5). Dead as stated.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-OT6.py`
