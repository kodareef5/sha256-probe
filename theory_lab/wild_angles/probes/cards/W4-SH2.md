# W4-SH2 — dim H¹ = 132 (hard-core bits = gluing obstructions)   ·   VERDICT: KILLED

**Card claim:** H¹ = #edges − rank δ = local constraints unsatisfiable by adjusting one stalk; conjecture dim H¹ = 132 (no global extension → plateau), and dim H¹/dim C⁰ → 0.516 (=132/256), with the H¹-support correlating (ρ>0.3) with the hard-core output positions.

**Probe run:** computed the genuine GF(2) cellular sheaf-cohomology H¹ = coker(δ) = dim C¹ − rank(δ) on TWO complexes: a **steelman** graded complex (`assemble_graded`: fresh register-diff stalks at every round boundary + a per-round block of glue relations C¹, so coker *can* be nonzero) and the degenerate output-pin complex as cross-check. N=2,3,4, tail depth R=4 and R=7. Extracted the left-null (coker) basis support to correlate with the {a,b,e,f@63 + 4dc} hard-core pattern. Throttled (OMP=2, taskpolicy -b).

**Result (numbers):**
- **dim H¹ = 0 at EVERY (N,R)** — steelman: N=4,R=7 gives dim C⁰=116, dim C¹=88, rank δ=88, **H¹ = 0**; same (H¹=0) at N=2,3 and R=4. Degenerate complex: also 0 (rank 24/24, 32/32). The coboundary always has **full row rank**.
- **H¹/C⁰ = 0.000** everywhere — never approaches the predicted **0.516**.
- **dim H¹ = 0 ≠ 132** — and the coker support is **empty** (no obstruction exists), so the support-correlation ρ is not even well-defined (effectively 0 ≪ 0.3).

**Kill_criterion:** "ratio ↛ 0, or support uncorrelated (ρ<0.3)." (card: ratio must → 0.51) — **fired? YES.** The ratio is 0, not 0.516; support correlation is undefined/0 < 0.3.

**Verdict reasoning:** KILLED — this is the 132 **category error** (prior-finding #1) confirmed a 10th way. A real sheaf-cohomology dimension over GF(2) is 0 here, **never 132**. The deep reason is structural and not a linearization artifact: SHA's round function is a **feed-forward DAG** of definitions; each glue relation introduces fresh next-state stalks that appear nowhere else, forcing the relations to be linearly independent (full row rank), hence coker = H¹ = 0. Cohomological obstructions require *cycles* in the constraint graph with inconsistent restriction maps — a computation DAG has none. The "132" lives entirely in the orthogonal world of the single-bit deterministic-control census (W2-CT1: a,b,e,f@63 fully + 4 dc), an output-bit controllability count, not a coboundary rank deficiency. So 0.516, 132, and the support-correlation all fail.

**Cross-check / skeptic note:** Adversarial steelman was the point: I deliberately built the *richer* graded complex (fresh stalks + glue rows) precisely so H¹ *could* be nonzero — and it still came out 0 at every N and R, on two independent complexes. The only way to manufacture a nonzero H¹ would be to inject artificial cycles (e.g. tie the round-0 input back to the round-R output as an extra constraint), which is not what "gluing obstructions of the cascade" means. Independent corroboration: W2-CT1 (132 = control census, not corank), W4-IG1 (Fisher corank 0/full-rank), and the wave preamble's explicit warning that a real corank/kernel-dim is 0/128 not 132. The category error is: H¹ (a coboundary rank-deficiency of a DAG = 0) is conflated with a controllability census (=132). Different objects, different values.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-SH2.py`
