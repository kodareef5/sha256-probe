# W3-OT1 — Cascade as a Brenier map; non-regularity = the 2^-2N cost   ·   VERDICT: CONFIRMED

**Card claim:** Cascade M1↦M2 is a Monge transport map (μ=forward-reachable, ν=backward-required); valid to sr=60, but at 61 ν concentrates on a measure-2^-2N set → no map, only a mass-wasting coupling. The per-round mass-concentration ratio should be ≈2^-2N.

**Probe run:** Two-part, throttled. (A) N=10 collision list (gap_rows.csv, 946 collisions): characterize ν's support in the round-60 gating coordinates (g1, h). (B) μ = the FULL forward de61=0 push-forward via the repo's exact enumerator (gap_analysis.c, N=8, ~16.2M hits) — NOT the collision sublist — to read the forward mass landing on ν's backward point.

**Result (numbers):**
- Support identity **g2 = g1 + h (mod 2^N) holds for ALL 946 collisions** → ν's target is genuinely 2-coordinate.
- g1 covers 61.2%, h covers 60.5% of Z/2^10; mean #distinct h per fixed g1 = 2.3 over 627 g1-values → ν lives on a **2-torus** (codim-2 backward point (0,0)), not a curve.
- Forward push-forward: P(g1=0)=0.003924, P(h=0)=0.003916 (≈2^-8); **forward mass on ν's point P(both) = 1.419e-05** (2^-16 = 1.526e-05).
- **Concentration exponent = -log2 P(both)/N = 2.013** (card predicts 2.000).
- Factorizes: P(both)=1.419e-05 vs P(g1=0)·P(h=0)=1.537e-05, independence **ratio 0.923** → two independent 2^-N costs.

**Kill_criterion:** "ratio ≠ 2^-2N" — **fired? no.** (concentration exponent 2.013 ≈ 2.000)

**Verdict reasoning:** The forward push-forward concentrates on ν's codim-2 point at exactly the rate 2^-2N (exponent 2.013), and it factorizes as two independent 2^-N costs (ratio 0.92). This is the genuine rank-2 (g1=0 AND h=0) structure that prior findings PH1/IN3/NT4/RG1-B confirmed 4× — so OT1 legitimately CONFIRMS rather than renaming. The Brenier framing adds a coherent picture: ν is a point mass on a 2-torus while μ is near-uniform, so no deterministic Monge map exists (would have to collapse a positive-measure set to one point) → "non-regularity = the 2^-2N cost" is the correct reading of the verified two-condition wall.

**Cross-check / skeptic note:** The card's own skeptic — "ν defined from collisions → risk of deriving 2^-2N by construction" — is the danger I avoided: the load-bearing P(both)=2^-16 is measured on the FULL forward de61=0 population (the enumerator), not on the collision sublist. If 2^-2N were a definitional artifact of "ν=collisions," the forward-population P(both) would not be ≈2^-2N; it is. The 2-torus geometry is read from the collision list (legitimately — that IS ν's support). Same number reached independently (forward push-forward + collision-support geometry) → convergence, not coincidence.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-OT1.py`
