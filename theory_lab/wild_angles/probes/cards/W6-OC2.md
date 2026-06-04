# W6-OC2 — 2^-2N = the codimension of the singular surface (two conditions, one control)   ·   VERDICT: CONFIRMED

**Card claim:** h=0 (singular-surface / ∂H/∂u condition) and g1=0 (endpoint transversality) are two functionally-independent scalars; one control dW can't satisfy both → BVP overdetermined by codim 2 → 2^-2N. Predicts: +1 control DOF drops it to 2^-N.

**Probe run:** N=8 and N=10, throttled. On the exact-carry cascade: (1) finite-diff the constraint normals n_g1 = ∂g1/∂control, n_h = ∂h/∂control over the 4 free words W57..60, take GF(2) rank; (2) re-derive g1⊥h from the measured N=10 gap_rows.csv (the actual sr=61 gating data); (3) **solvability** test of the +1-control prediction — does {g1=0 ∧ h=0} have a *solution* with 1 control (w60) vs 2 controls (w58,w60)? g1/h computed exactly per gap_analysis.c.

**Result (numbers):**
- **(1) codim = 2** at both N: rank[n_g1; n_h] = **2**. Per-word dependence is the load-bearing structure: W57(g1=0,h=1), W58(g1=1,h=1), W59(g1=0,h=1), **W60(g1=1,h=0)** — the last free control w60 moves g1 but is structurally **incapable of moving h**. This is literally "two conditions, one control."
- **(2)** corr(g1,h) = **+0.0167** ≈ 0 over the 946 measured N=10 collisions — consistent with the verified independence ratio 1.005.
- **(3) +1-control prediction HOLDS:** 1 control (w60) solvable fraction = 0.00267 (N=8) / 0.00167 (N=10) ≈ **2^-N** (h must already be 0). 2 controls (w58,w60) solvable fraction jumps to **0.617 / 0.642** — a ~230×/385× rise toward 1. The extra control DOF (w58 moves h) removes the obstruction.

**Kill_criterion:** "n_h ∥ n_g (dependent → not codim 2), or +1 control doesn't move density toward 2^-N" — **fired? NO** (neither clause: rank is 2, and +1 control moves solvability 2^-N → ~0.63).

**Verdict reasoning:** This lands on the GENUINE two-conditions object (prior finding #3), not a generic codim-2 rename. The normals are independent (rank 2), and the structure is specific and non-trivial: the conditions are exactly {g1, h}, w60 steers g1 only, so one control over the (g1,h) pair leaves a codim-2 obstruction → 2^-2N. Critically, the card's NEW falsifiable content — "+1 control DOF → 2^-N" — is confirmed quantitatively: a second word that moves h (w58) raises {g1=0 ∧ h=0} solvability from ≈2^-N to ≈0.63. The 2^-N → ~0.63 jump (not exactly 1) is precisely the codim-1 coupon-collector ceiling 1−1/e (h is not surjective in one w58), which is the *predicted* "obstruction removed, solution now exists" behavior. Both the codim-2 geometry AND its +1-control consequence reproduce with real numbers, so a new quantity (the solvability jump) emerges beyond merely re-labelling 2^-2N.

**Cross-check / skeptic note:** The skeptic warns "independence is already measured (1.005) — the new content is the codim geometry + the +1-control prediction." Exactly: the 2^-2N *magnitude* is a re-derivation of the verified result, so the CONFIRM rests on (a) the basis-independent rank-2 normals with the specific w60→g1-only signature, and (b) the +1-control solvability jump — both genuinely new and both borne out. Honest caveat: the 2-control solvability ceiling is ~0.63 (=1−1/e), not 1.0, because h ranges over only ~63% of its codomain as w58 varies; this is the correct codim-1 existence rate, not a shortfall. Reproduces identically at N=8 and N=10 (the per-word dependence pattern is bit-for-bit the same), arguing against coincidence.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OC2.py`
