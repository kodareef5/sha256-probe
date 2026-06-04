# W4-FP1 — S-transform of the 64-fold product → 0.74 as the top singular-edge   ·   VERDICT: KILLED

**Card claim:** Per-round difference-Jacobians as free factors; product singular law = ⊠ via S_{μP}=∏S_{μi}; its top edge → the 0.74 collision-count edge.

**Probe run:** N=4,6,8, throttled (`taskpolicy -b`, OMP=2). For each N I built the EXACT local GF(2) difference-Jacobian of one N-bit compression round at a random base point (Ch, Maj and the modular-add carries linearized at that point), as a real 0/1 matrix of shape 8N×8N — "the per-round difference-Jacobian" the card names. 64 such Jacobians at independent base points; per-round SVD; the ordered 64-fold matrix product (top sv tracked in log-space, true value ~10^30–10^44 overflows float64); and a 30-line S-transform free-multiplicative-convolution (ψ-inversion → S(w)=(1+w)/w·χ(w), S_P=S_A·S_B) predicting the 2-round box-times edge vs the direct 2-round SVD.

**Result (numbers):**
| N | per-round top sv (geomean) | direct 64-fold top sv | normalized per-round edge =top^(1/64) | FREE ⊠ 2-round edge | DIRECT 2-round edge | rel.diff |
|---|---|---|---|---|---|---|
| 4 | 5.27 | 10^30.30 | 2.975 | 26.39 | 19.76 | 33.5% |
| 6 | 7.15 | 10^39.70 | 4.172 | 56.95 | 37.66 | 51.2% |
| 8 | 8.57 | 10^44.77 | 5.007 | 71.73 | 54.58 | 31.4% |

**Kill_criterion:** "free vs direct edge differ >15% with no N-convergence, or edge ∉[0.6,0.9]" — **fired? YES (both clauses).**

**Verdict reasoning:** The free ⊠ prediction overshoots the direct product edge by 31–51% — far past the 15% bar — and does NOT converge as N grows 4→8 (33.5%→51.2%→31.4%, no monotone shrink). Independently, every natural "top edge" of these Jacobians is a GAIN > 1 (the round is expansive in difference space): the per-round singular edge is ~5–9 and the normalized per-round edge (top^(1/64)) is 2.97/4.17/5.01 — outside [0.6,0.9] and growing with N. Both kill clauses fire.

**Cross-check / skeptic note:** Per the wave's prior finding #2, 0.74 isn't even sharp (real growth slope ≈0.673), but that's moot here: the probe's edges miss it by an order of magnitude and trend the wrong way. The category error the card commits is units — a 64-fold matrix-product top edge scales like (per-round gain)^64 ≈ 10^44, whereas 0.74 is bits per unit word-width N (a per-N collision-count slope). They are different objects; no normalization makes a >1 expansive gain into the sub-1 collision exponent. Freeness also fails on its own terms here: SHA's Σ-layer is a *fixed* matrix every round (not asymptotically free), so the ⊠ approximation degrades rather than improving with N.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-FP1.py`
