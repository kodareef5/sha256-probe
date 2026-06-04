# W5-CO2 — Hennessy–Milner: 132 = the minimal distinguishing-formula set   ·   VERDICT: KILLED

**Card claim:** Bisimilar states satisfy the same modal formulas; the 132 hard-core bits = the irreducible distinguishing formulas (cofree observations) no message-move can equalize; HW~74 = where the distinguishing set saturates. Probe target: greedy output-bit-modality distinguishing set = empirical hard-core bits (Jaccard), fraction tracks 132/256 = 0.516.

**Probe run:** N=4, 8, 10 (validated engine). Built the genuine Hennessy–Milner object: the minimal set S of output-difference bit positions (the modalities/observations) such that "de63 = 0 on S" already separates every collision from every sampled non-collision — i.e. greedy set-cover over non-collision diff-vectors. Compared |S| and its support against (a) the repo single-bit hard-core census and (b) a flat per-bit influence ranking. Stability over 3 seeds × {2k,4k,8k} non-collisions. Throttled.

**Result (numbers):**
- HM distinguishing-set size: **8–11**, and it grows with the *non-collision sample size* (8→9→10 as samples 2k→4k→8k), **not with N**. This is ~log2(#non-collisions) — the generic number of coordinates needed to shatter M random points, a set-cover artifact.
- Fraction of 8N: N=4 ≈ 0.28, N=8 ≈ 0.14, N=10 ≈ 0.11 — **monotonically decreasing**, the opposite of tracking the constant 0.516.
- Jaccard(S support, census hard-core) = **0.000** at every N.
- Bit positions in S are **unstable across seeds** (different bits each run) — not a canonical object.
- Bonus category-error evidence: the single-bit "hard-core" census in this small-N cascade gives **2N** bits (8 at N=4, 16 at N=8) on registers **d, h** — which are simply *pinned to 0* by the cascade (dd63=da60-shift=0, dh63=de60=0). That is the OPPOSITE support from the repo's full-N "a,b,e,f" 132. So the "132" support flips with the (operational) definition of "control" — d,h here vs a,b,e,f at N=32 — confirming it is not basis-independent.

**Kill_criterion:** "Jaccard < 0.3 OR fraction doesn't track across N." — **fired? yes, on both clauses.** Jaccard = 0.000; fraction decreases (0.28→0.14→0.11) instead of tracking 0.516.

**Verdict reasoning:** KILLED, and it re-commits the prior #1 category error. The honest HM distinguishing set is a *sample-size-dependent set-cover* of size ≈ log2(M), with unstable support and a *shrinking* fraction of the output — it is neither the 132 census nor a stable, basis-independent invariant with {a,b,e,f}+4dc support (the bar #1 demands). The "132" only appears as the single-bit deterministic-control census, whose support is not even stable across word-width-scaled models (it lands on the pinned-zero d,h here). So "132 = minimal distinguishing-formula set" is false: the minimal distinguishing set is a generic log-sized separating code, unrelated to the hard-core support.

**Cross-check / skeptic note:** The skeptic note asked whether the *modality* structure beats a flat influence ranking. The greedy modal cover (size 9) does beat flat popcount-ranking (size 12–22) at fixed N — but that only shows greedy set-cover < greedy-by-marginal, a generic combinatorial fact; it does NOT make the set the 132, since the set neither scales as width nor matches the hard-core support (Jaccard 0). An independent corroboration of the category error: the census support itself (d,h vs a,b,e,f) depends on the operational notion of "control," exactly as W2-CT1 found for the corank cluster.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-CO2.py`
