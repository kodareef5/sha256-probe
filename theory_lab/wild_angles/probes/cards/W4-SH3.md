# W4-SH3 — Sheaf diffusion IS the cascade; plateau = a slow non-harmonic mode   ·   VERDICT: KILLED

**Card claim:** the heat flow ẋ=−Lx converges to the harmonic projection = a collision; the cascade's fixed points (da=0, de60=0) ARE the harmonic projector, and HW≈74/132 is a near-harmonic slow mode (tiny λ₁) explaining the XOR-linearized timeout (ill-conditioned L).

**Probe run:** real Hodge Laplacian L=δᵀδ of the difference sheaf, N=2,3,4, tail depth R=4 (~sr=60). Three sub-tests: (1) project random x onto ker(L) and measure the energy fraction surviving on the a-block and the e-block (cascade fixed point would auto-zero them); (2) condition number κ=λ_max/λ₁ across the tail sweep; (3) Hamming-weight fraction of the λ₁ eigenvector vs 74/132=0.56. Throttled (OMP=2, taskpolicy -b).

**Result (numbers):**
- **[1 FIXED POINTS] FAIL.** Harmonic projection does NOT zero a or de60: a-block ker(L)-energy = **0.085 (N=3), 0.041 (N=4)** — essentially equal to its *proportional* share **0.083**; e-block = 0.035–0.038. Random-vector projection keeps a-fraction 0.04–0.08, e-fraction 0.03–0.06 (both nonzero). The harmonic subspace treats a/e like any other block — it does **not** realize the cascade fixed point (da=0, de60=0).
- **[2 CONDITIONING] non-monotone, peaks at the WRONG round.** κ = λ_max/λ₁ = **141827 at R=3 (sr=59)**, drops to **2009 at R=4 (sr=60)**, 2068 at R=5 (sr=61). Ill-conditioning is *worst at 59*, not 60 — it does not single out the sr=60 wall, and the tiny λ₁ driving it is the same seed-erratic artifact seen in SH1.
- **[3 SLOW-MODE HW] FAIL.** λ₁-eigenvector HW fraction = **0.85–1.00** (abs>1e-2) or trivially **0.500** (median split) — neither matches the predicted **0.56**.

**Kill_criterion:** "harmonic projection ≠ cascade fixed points, or L well-conditioned while linearized sr=60 is hard." — **fired? YES (first disjunct).**

**Verdict reasoning:** KILLED. The load-bearing claim — that the linear sheaf's harmonic projector *is* the cascade's fixed point — is false: ker(L) carries ordinary proportional energy on the a- and de60-blocks (≈0.04–0.08 = their dimensional share), so projecting onto it does not impose da=0 or de60=0. The "da=0, de60=0" cascade fixed point is a modular/nonlinear attractor, not a harmonic subspace of the carry-dropped sheaf. The conditioning story also misfires (κ peaks at sr=59, not 60, and is a small-eigenvalue artifact), and the 0.56 plateau-HW does not appear in the λ₁ eigenvector (0.85–1.0). Renaming the cascade "sheaf diffusion" buys no new prediction — every concrete consequence (fixed-point support, gap location, slow-mode HW) is wrong.

**Cross-check / skeptic note:** The skeptic note in the card ("linear diffusion → linearized space; true metastable HW may differ") is exactly what bites: the linear sheaf's harmonic/slow structure does not encode the nonlinear cascade's fixed points. I sharpened sub-test (1) with an orthonormal ker-basis energy computation (independent of random sampling) and it confirms a-block energy = proportional share, not 0. The conditioning non-monotonicity (worse at 59) matches the wave-wide "no round-60 knee". No independent quantity converges on 0.56 here; the only place ~74/132 is real is the output-difference plateau, a different space. A rename, not a mechanism.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-SH3.py`
