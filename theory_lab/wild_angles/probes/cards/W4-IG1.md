# W4-IG1 — Fisher corank census → 132 hard-core = the metric kernel   ·   VERDICT: KILLED

**Card claim:** inject a Bernoulli-ε input perturbation; output bit k acquires a difference-Bernoulli law; the pullback Fisher metric g=JᵀWJ has a kernel = output bits "pinned at p=½ for every input direction" = conjecturally the 132 hard-core bits (informative complement → HW~74).

**Probe run:** N=32 (literal width — 132 is a 32-bit phenomenon), real modular sr=60 tail (rounds 57..63, carries in), 128 single-bit input directions (free W[57..60]), 64 random base points. Throttled (OMP=2, taskpolicy -b). Computed THREE objects: (A) the card's literal "pinned-at-½" census R[k,j]=Pr[flip]−½; (B1) the genuine basis-independent Fisher-metric corank (= null space of the real sensitivity matrix J, via real-rank); (B2) the exact GF(2) corank of the linearized differential reachability (the CT1 adjudicator).

**Result (numbers):**
- (A) Bits pinned at p=½ for every direction (max|R|≤0.02): **0**, not 132. The count has **NO plateau**: it slides continuously with the threshold τ — 0 @ τ=0.10, 8 @ τ=0.15, 76 @ τ=0.20, 98 @ τ=0.25, 119 @ τ=0.35, **131 @ τ=0.49**. To reach ~132 you must count nearly every bit as "pinned" (τ≈½). No basis-independent gap → tuned, not a kernel.
- Per-register mean|flip-prob−½|: **a,b,e,f ≈ 0.05** (most-avalanched/closest to ½) vs **c,d,g,h ≈ 0.10–0.24** (steerable). The hard-core support {a,b,e,f} faintly shows as the low-mean cluster, but no bit is exactly pinned.
- (B1) Genuine Fisher-metric corank = **0/128** input-dim (every input direction moves some output bit's law).
- (B2) Exact GF(2) reachability corank = **0/256** (rank 256, full). Stable across re-seeds (0,0,0).

**Kill_criterion:** "unsteerable count ≠ 132 (off >25), or doesn't converge with N, or is highly base-dependent." — **fired? YES.** The honest count is 0 (off by 132), and the only way to manufacture ~132 is to slide τ to ≈0.49 — i.e. it is *highly threshold-dependent*, the continuous analog of "base-dependent." Both the numeric and exact coranks are 0.

**Verdict reasoning:** KILLED. This is exactly prior-finding #1 realized: a genuine basis-independent metric/linear corank lands on **0** (full informativeness/reachability), not 132 — matching W2-CT1's adjudication (corank 0 generic / 128 single-point, never 132). The repo's 132 is the *single-bit deterministic-control census* — a particular nonlinear/operational protocol — and IG1's Fisher framing, computed honestly, does NOT reproduce it as a stable corank. The flagged worry ("IG1 may literally BE the repo's census in disguise") is *confirmed in spirit*: the only residue of "132" here is a threshold-tuned count of near-½ bits (131 @ τ=0.49), which is the avalanche, not a Fisher kernel. The card's predicted "rank-124 → HW~74" complement does not materialize (informative dim = 256).

**Cross-check / skeptic note:** The card's skeptic ("a bit unsteerable by singletons may be steerable by a pair — rerun with full N-direction rank") cuts the *wrong* way here: I used the *full* 128-direction span (B1/B2 are basis-independent ranks over all directions), and still got corank 0 — so even generous multi-direction control reaches everything. The faint {a,b,e,f}-vs-{c,d,g,h} mean|R| split is real and consistent with the carry/T1+T2 avalanche concentrating on those four registers, but that is the *deterministic census's* origin (nonlinearity), not a metric kernel. Independent corroboration: identical conclusion to W2-CT1 (the canonical corank card) and W1-GE3 (Morse–Bott Hessian also failed to reproduce 132).

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-IG1.py`
