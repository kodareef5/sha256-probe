# W6-OC1 — The wall is a singular arc → ∂H/∂u dies at round 61   ·   VERDICT: KILLED

**Card claim:** The control dW[r] enters T1 additively → H affine in u → bang-bang cascade for r≤60; at 61 the switching function s_61 = λ_{62}ᵀ(∂F/∂u) collapses on the feasible cone → a singular arc → no unique steering.

**Probe run:** N=8 and N=10, throttled (`OMP_NUM_THREADS=2 taskpolicy -b`). Built the exact-carry N-bit cascade trajectory (path-1 of the da=0 MSB-kernel collision), finite-diff control columns B_r = ∂F_r/∂W[r] and state Jacobians J_r at each trajectory point, propagated the full backward costate basis λ_r = J_rᵀλ_{r+1} from λ_64 = I, and formed the switching map s_r = λ_{r+1}ᵀB_r for r=57..63. Reported GF(2) rank and a Boolean-Frobenius magnitude.

**Result (numbers):**
- N=8: rank s_r = 8 (= N, full) at **every** round 57..63, **including 61**. Boolean ‖s_r‖_F = 248, 267, 258, 216, **149**, 88, 22 for r=57..63. s_61/s_60: rank ratio **1.000**, ‖·‖_F ratio **0.690**.
- N=10: rank s_r = 10 at every round 57..63. ‖s_r‖_F = 398,394,394,330,**241**,137,27. s_61/s_60: rank ratio **1.000**, ‖·‖_F ratio **0.730**.
- The Boolean magnitude tapers *smoothly*: adjacent-round ratios are 1.08, 0.97, 0.84, 0.69, 0.59, 0.25 (N=8) — round 61's 0.69 is mid-pack, not a cliff. The only round-61 discontinuity is the schedule free-DOF dropping 1→0.

**Kill_criterion:** "‖s_61‖ same order as ‖s_60‖ (no collapse)" — **fired? YES.**

**Verdict reasoning:** The intrinsic switching function does NOT collapse at 61: its rank is full (= N) at 61 exactly as at 60, and its magnitude is the same order (ratio ≈ 0.7, identical to the smooth round-to-round decay). The round map sha_round is literally identical at every round, so its own ∂F/∂u cannot "die" at 61. The only thing special at 61 is that the *message schedule* stops granting a free word (free-DOF 1→0) — a bookkeeping fact about which W are pinned, not a singular arc of the control Hamiltonian. The catalog's "project s_61 onto the feasible cone" is trivially 0 precisely and only because that cone has dimension 0 (W[61] is a determined variable), which restates the known schedule constraint.

**Cross-check / skeptic note:** Could the smooth ‖·‖_F taper itself BE the "collapse"? No — it is monotone across the whole horizon (the backward costate progressively spans fewer of the 8N output directions as it walks away from λ_64=I), and round 61 sits on the trend line. The rank (a basis-independent quantity, immune to the carry-kink magnitude noise the skeptic flags) is dead flat at N. This matches prior finding #4: every "dies at 61" claim dissolves into smooth growth + the schedule constraint. Same engine drives OC4 (costate norm) — see that card for the conjugate-point version of the same negative.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OC1.py`
