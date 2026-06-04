# W3-OT2 — Sinkhorn coupling entropy = the 0.74 exponent   ·   VERDICT: KILLED

**Card claim:** The entropic-OT optimal coupling between forward/backward boundary states has entropy ≈0.74·N·log2; carry-HW sets the cost matrix, ε the regularization. H(π*)/N should →0.74 with an ε-plateau.

**Probe run:** Built the carry-HW cost matrix C[i,j]=hw(i⊕j) on the genuine 2^N-state alphabet at N=6 (64²) and N=8 (256²), uniform marginals (the untuned/neutral choice). Ran Sinkhorn to convergence over a 12-point ε sweep (0.05→8.0) and reported H(π*) (bits) and H/N at each ε. Throttled.

**Result (numbers):**
- H/N is a **strictly monotone increasing function of ε** at both N: floors at **1.000** (ε→0, = the per-marginal entropy log2(M)/N = N/N) and rises to **1.997** (ε→∞, = uniform-product 2N/N).
- N=6: H/N = 1.000, 1.001, 1.058, 1.304, 1.527, 1.739, 1.840, 1.924, 1.956, 1.980, 1.993, 1.997 across the ε grid. N=8: identical shape (1.000 → 1.998).
- **The curve never crosses 0.74 at any ε** ("crosses 0.74 at ε in []"). There is no locally-flat plateau anywhere, let alone at 0.74.

**Kill_criterion:** "H/N doesn't →0.74 or no ε-plateau" — **fired? YES** (both clauses: never reaches 0.74, and no plateau — H/N sweeps continuously with the regularization knob).

**Verdict reasoning:** The entropic-OT coupling entropy is a monotone function of ε with no scale-invariant fixed point; its minimum (ε→0, with uniform marginals) is already 1.000·N (the marginal entropy floor), strictly above 0.74·N, and it only grows from there. So H/N=0.74 is not merely "tunable" — it is **unreachable** in the natural normalization, and there is no ε-plateau. This is the exact failure mode the card's own skeptic names ("cost-matrix choice is a knob"): any target value would be a transient crossing, and here 0.74 isn't even crossed.

**Cross-check / skeptic note:** Per prior finding #2, 0.74 is not sharp anyway (the repo's own collision table refits to slope 0.673, per-(N mod 4) class spread 0.72–1.04), so even a value "in the right range" would prove nothing — but the probe doesn't even land in the range. A different cost-matrix or non-uniform marginals could be tuned to hit 0.74 at some ε, but that is post-hoc knob-fitting, not the predicted scale-invariant plateau. Could the support of the zero-cost cells = collisions (the card's secondary claim)? At ε→0 the coupling becomes deterministic (H→ the marginal floor), independent of any 0.74 structure. Dead as stated.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-OT2.py`
