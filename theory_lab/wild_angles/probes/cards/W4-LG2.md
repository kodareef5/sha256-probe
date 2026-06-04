# W4-LG2 — Strong-coupling expansion → 0.74 as a plaquette-tiling constant   ·   VERDICT: KILLED

**Card claim:** log₂(#collisions) ≈ (#free links) − (frustration cost); the N-slope is a *derived* geometric free-link density = 0.74. The frustration fraction f(r) should spike at de58 and round 61.

**Probe run:** Empirical slope of log₂(#collisions) vs N from the canonical best-kernel counts (`writeups/paper_figures_data.md` Fig 2, N=4..12 — the dataset the 0.74 is fit to); global least-squares slope plus per-N-mod-4-class slopes (4 documented scaling classes). The geometric model's "frustration cost" extracted as 4N − log₂(C). Per-round frustration fraction f(r) from the real width-N carry-difference field (`/tmp/wfield8.txt`, N=8, 260 collisions). Same-kernel cross-check from our MSB enumerator (`/tmp/lg_diff*`). Throttled.

**Result (numbers):**
- **Global least-squares slope d log₂(C)/dN = 0.634** (card: 0.74; finding #2: 0.673).
- Per-class slopes (N mod 4 = 0,1,2,3): **0.634, 0.950, 1.036, 0.717** — a 1.6× spread.
- Per-point log₂(C)/N spread: **1.022 … 2.000**; 0.74 is below every single per-point value and is not a sharp constant.
- Geometric model: frustration_cost = 4N − log₂(C) ≈ **2.66·N mean** (paper Fig 6 independently: 3.33·N), so log₂(C) ≈ (4 − 3.33)N = **0.67·N**, not 0.74·N.
- f(r) over rounds 57..63: **0.442, 0.451, 0.231, 0.000, 0.000, 0.000, 0.000** — peaks at r57–58, identically zero at r60–63; **no spike at round 61.**

**Kill_criterion:** "slope off >2× with no N-convergence, or f(r) flat" — **fired? Literally NO; substantively YES.** The slope (0.634) is off from 0.74 by 1.17× (under the loose 2× bar), and f(r) is not flat. But the card's actual thesis — "the slope is a *derived 0.74*" — is refuted: the measured slope is 0.63–0.67, it is class-dependent (0.63–1.04), and f(r) peaks at the cascade column (de58) not at round 61.

**Verdict reasoning:** KILLED on the substantive claim. (1) 0.74 is not reproduced: the global slope is 0.634, matching finding #2's 0.673 to within the choice of N-points, and it is a class-dependent spread, not a sharp tiling constant. (2) The "geometry" predicts nothing: log₂(C) = 4N − 3.33N is the enumeration relabelled (skeptic's exact worry — "if the constraint sets the count, the field-theory is decoration on enumeration"); the 3.33N "frustration" is itself a measured fit (paper Fig 6), not derived from any plaquette tiling. (3) f(r) does not spike at round 61 (it is zero there); the only feature is de58/r58, which is the cascade's lone varying column. I record KILLED rather than SURVIVES because the loose >2× numeric bar is a weak proxy; the headline content (0.74 sharp, derived) is the thing under test and it is false.

**Cross-check / skeptic note:** Two independent repo measurements agree the exponent is ~0.63–0.67 (the slope fit here, and paper Fig 6's 4N−3.33N). The best-kernel data is the proper source; our MSB enumerator (N=4→49, N=8→260) is sparser (N=5,6 give 0 collisions) and not suited to a slope fit, so I did not over-read it. A defender could claim 0.74 is an asymptotic large-N limit, but the data trend is flat/decreasing in log₂(C)/N (2.00 at N=5 → ~1.02 at N=12), i.e. converging *below* 0.74-per-... no — note log₂C/N here includes the kernel multiplicity; the *slope* (marginal) is the right comparator and it is 0.63.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-LG2.py`
