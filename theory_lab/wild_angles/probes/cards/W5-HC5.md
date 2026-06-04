# W5-HC5 — de58 single-petal: why only de58 grows, and the count decomposition   ·   VERDICT: KILLED

**Card claim:** de57/59/60 constant = a frozen 3-coordinate sunflower CORE; de58 = the
unique PETAL coordinate with |de58| ~ 2^{0.31N}; the petal-exponent + a fiber-exponent
should ≈ 0.74 (the collision-growth slope). "Mostly names an observed fact + tests the split."

**Probe run:** exact de57..de60 image sizes at the fast cascade-eligible widths N=4,5,8,10
(live, via the faithful mini-SHA cascade sweep); the repo's published exact table (Fig 3,
read-only) cited for N=11,12,13,14,16,32. Collision counts 49/260/946 (N=4/8/10) for the
fiber. Pure-python, throttled.

**Result (numbers):**
- **CORE:** de57 = de59 = de60 = **1** at every N (live and published). TRUE — but a restatement.
- **de58 = 2^hw(db56)** holds for all N ≤ 14 (live N=4,5,8,10 ✓; published N=11,12,13,14,16 ✓);
  breaks at N=32 (1024 ≠ 2^17, carry collapse). This law is **INPUT**, not derived by petals.
- **petal exponent log2|de58|/N is NOT 0.31:** spans **0.25 … 0.75**, jagged/non-monotone
  — (N=4,5,8,10,11,12,13,14,16,32) → (0.25, 0.60, 0.38, 0.40, 0.45, **0.75**, 0.38, 0.36, 0.50, 0.31).
  It is just hw(db56)/N, which oscillates; "2^{0.31N}" is not a real exponent.
- **petal+fiber is a tautology:** petal_exp + fiber_exp = log2|de58|/N + log2(#coll/|de58|)/N
  = **log2(#coll)/N identically** (|de58| cancels). Measured sums (N=4/8/10): **1.40 / 1.00 / 0.99**;
  verified two-point anchor 260@8→946@10 gives slope **0.932** — not 0.74, not 0.31+anything sharp.

**Kill_criterion:** "core leaks (de57/59/60 not constant), OR petal+fiber exponents don't
sum to the slope (±0.1)." — **fired? YES** (clause 2): petal+fiber = the raw growth exponent
(0.99–1.40 across these N; cleanest slope 0.932), nowhere near 0.74±0.1, and the petal
exponent is not the claimed stable 0.31.

**Verdict reasoning:** KILLED. Per finding #5, this card was flagged to CONFIRM *only* if the
sunflower-petal decomposition **derives** 2^hw(db56). It does not: the de58 = 2^hw(db56) law
is supplied as input ground truth, and the petal/fiber language merely re-partitions known
numbers. The "0.31 petal exponent" does not exist (the quantity is a jagged 0.25–0.75 tracking
hw(db56)/N). The "petal+fiber ≈ 0.74" claim is an algebraic identity (|de58| cancels) that
reproduces the *noisy* collision-growth exponent — 0.99–1.40 at these N, 0.673 in the repo's
fuller fit, 0.932 at the cleanest anchor — none of which is a sharp 0.74 (finding #2). So the
card is a correct RENAME of two established facts (de57/59/60 = 1; de58 = 2^hw(db56)) with no
new number or prediction (finding #6 ⇒ not a CONFIRMED).

**Cross-check / skeptic note:** The de-law itself reproduces cleanly (independent corroboration
of #5), so the kill is not nihilistic — the *facts* are real. What dies is the *mechanism* claim:
(a) "petal exponent = 0.31" (false; it's non-monotone hw(db56)/N), and (b) "petal+fiber = 0.74"
(a tautology equal to the raw, noisy growth exponent). A defender might argue the *core/petal
labeling* is apt (only de58 varies) — granted, but that is exactly the pre-existing observation,
not a derivation, and it predicts nothing new. Per finding #5 the real driver is the Maj/AND
image-count on db56, which is group-free and has no deeper invariant.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HC5.py`
