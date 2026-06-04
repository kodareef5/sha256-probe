# W7-QW3 — Discriminant kernel → 132 = corank(D)   ·   VERDICT: KILLED

**Card claim:** A hard-core bit has a zero independent-transition prob → a zero singular value of D=√(P∘Pᵀ); conjecture corank(D)=132 (rank 124), corank/total → 0.516, projection-robust, kernel aligned with the known hard bits.

**Probe run:** N=6,8,10. Built two honest bit-level transition matrices, formed the Szegedy discriminant D=√(P∘Pᵀ), SVD'd, and swept the zero-threshold:
 (A) the 2N×2N per-bit avalanche/diff-Jacobian B[i,j]=P(out head-bit i flips | in head-bit j flipped);
 (B) the (da,de)-head diff-config chain P (transfer_operator). Throttled yes (`OMP_NUM_THREADS=2 taskpolicy -b`).

**Result (numbers):**
- (A) honest discriminant corank at strict thresholds (1e-9 and 1e-6) = **0 / 2N for every N** (N=6,8,10). No spectral gap: the corank "fraction" slides continuously 0.000 → 0.062 → 0.125 → **0.625** as the threshold sweeps 1e-6 → 1e-3 → 1e-2 → 1e-1 (N=8). Smallest singular values trail off smoothly (…0.064, 0.0054, 0.0004) — no cliff at any 0.516.
- (B) the named chain's "corank" at 1e-6 = **0.219 (N=6) → 0.754 (N=8)** — not a stable ~0.5; and these zeros are the unreachable rows left by the `max_heads` BFS cap (sampling-noise floor), i.e. a projection artifact, not structure.
- The chain P is **reversible**: max|s(D) − |eig(P)|| = **0.0001** → D merely √-relabels P (the explicitly *banned* outcome).
- 132 = HARDCORE census = 128 (registers a,b,e,f fully at round 63) + 4 scattered dc bits, living in the **256-wide output-bit census**, with no corresponding zero in any D's singular spectrum.

**Kill_criterion:** "corank not a stable ~0.5 fraction across N, or kernel = numerical noise / a projection artifact." — **fired? yes (both clauses).**

**Verdict reasoning:** The honest discriminant corank is 0 at any noise-free threshold and otherwise a threshold-/sampling-cap-dependent number that ranges from 0.000 to 0.754 — it is neither stable nor ~0.516, and where it is nonzero it is sampling noise. The 132 is a *census* of zero-control output bits, a basis-dependent count in a 256-dim space, not a basis-independent matrix corank — exactly the "132 = corank" category error flagged 16× prior. The reversibility (s(D)=|eig(P)|) means D doesn't even earn its keep over P.

**Cross-check / skeptic note:** A surprising near-132 would have demanded a stable basis-independent corank; none exists. The only way to *manufacture* 132 here is to project P onto exactly the 132 hard bits by hand (the skeptic's own warning) — i.e. put the answer in. Independent corroboration: the matroid/SVD-corank cluster (prior #1) and the repo's own writeup both locate 132 in the output-bit census, never in a kernel dimension.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-QW3.py`
