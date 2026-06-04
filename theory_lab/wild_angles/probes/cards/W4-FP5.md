# W4-FP5 — Free subordination → why exactly de58 grows   ·   VERDICT: KILLED

**Card claim:** The ⊠-product's subordination functions ω_i say how much each factor leaks into the product; conjecture only ω_{de58} is mobile while de57/59/60 are pinned — deriving the split from the algebra. Probe: build W57..W60 Jacobian columns; compute each subordination function (fixed-point on Stieltjes transforms); is ω_{de58} the only non-flat one, magnitude tracking the 2^10 growth?

**Probe run:** N=4,6,8,10, throttled. The four factors = round-57/58/59/60 difference-Jacobian cross-sections (real 8N×8N, pooled spectra over 10 base points); product = their ordered composition. Subordination ω_i(z) solved by the fixed-point G_product(z)=G_factor_i(ω_i(z)) (1-D root-find above the spectrum); non-flatness = mean |ω_i(z)−z|/|z| over a real-z grid. Then the magnitude guard against the ground-truth |de58|=2^hw(db56) table including the non-monotone region.

**Result (numbers):**
- (A) Single-out test: the subordination non-flatness is **identical across all 4 factors** — factor-spread = 0.00e+00 at every N (de57=de58=de59=de60 = 1279.2 at N=4, 6271.8 at N=6, ...). The four cross-sections share the same singular law, so subordination CANNOT distinguish de58. de58 picked **0/4** (worse than the 1/4 random baseline). Factors distinguishable at 0/4 N.
- (B) Magnitude guard: a naive corr(ω_de58, log2|de58|)=0.747 exists only over the cherry-picked monotone subrange N=4–10. But ground truth |de58|=2^hw(db56) is **non-monotone**: 2,8,8,16,32,**512**,**32**,32,256 at N=4,6,8,10,11,**12**,**13**,14,16 — it drops from 512 (N=12) to 32 (N=13), and is carry-collapsed to 1024 at N=32 (vs 2^17 if XOR-linear).

**Kill_criterion:** "doesn't single out de58 (1-of-4), OR magnitude misses the growth law" — **fired? YES (both).**

**Verdict reasoning:** Both kill clauses fire. (1) Subordination is flat across all four factors (identical singular laws), so it never singles out de58 — it can't even do the easy 1-of-4 pick. (2) Even granting a per-factor number, the magnitude guard is fatal: |de58|=2^hw(db56) is non-monotone in N, so no smooth spectral quantity (subordination, eigenvalue spread, Lyapunov) can track it. This is restate-not-derive.

**Cross-check / skeptic note:** Confirms prior finding #4 (the de58 thread is essentially closed): |de58|=2^hw(db56) is a **Maj/AND image-count** — an arithmetic property of the round's nonlinear gates (verified by the repo's de58_enum.c: de58 = s1[e]−s2[e] after round 58, imaged over W57), not a subgroup/coset/ergodic/spectral invariant. Free subordination is a spectral construct; it sees the singular law (which is the same for all four rounds), not the arithmetic image-count, and certainly not the non-monotone exponent hw(db56). The 0.747 monotone-subrange correlation is exactly the "1-in-4 / fit luck" the card's own skeptic note flags as needing the magnitude guard — and the magnitude guard kills it.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-FP5.py`
