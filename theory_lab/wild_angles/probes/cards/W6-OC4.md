# W6-OC4 — Conjugate point → the costate norm blows up into round 61   ·   VERDICT: KILLED

**Card claim:** The solvable/unsolvable-BVP boundary is a conjugate point: the control-augmented transition map [J_r | ∂F/∂u] becomes ill-conditioned at the free→schedule transition (61), where the dW[61] column drops; ‖λ_60‖ spikes.

**Probe run:** N=8 and N=10, throttled. Same exact-carry cascade engine as OC1. Propagated the full backward costate λ_r = J_rᵀλ_{r+1} from λ_64 = I; per round measured (1) corank of the feasible augmented map A_r = [J_r | B_r^feasible] (state Jacobian plus only the schedule-granted control columns), (2) costate "norm" as GF(2) rank of λ_r (basis-independent) and Boolean-Frobenius magnitude. Seed-stability tested over 24 random free-tail-word seeds.

**Result (numbers):**
- rank λ_r = 8N (**full**, = 64 at N=8 / 80 at N=10) at **every** round 57..63, including 61 — costate never degenerates.
- ‖λ_r‖_F **decreases monotonically**, opposite to "blows up": N=8 → 2045, 1991, 1802, 1500, **1005**, 571, 241; N=10 → 3203, 3033, 2715, 2175, **1458**, 772, 294. Round-61 ratio to 60 = 0.67 (N=8) / 0.67 (N=10), identical to the smooth round-to-round taper — no isolated spike.
- corank[J|B_feas] = N for r≤60 and **0** for r≥61 — a step *down* (loss of N free control columns when the schedule pins W[61..63]), identical across all 24 seeds. "Spike isolated at 61?" = **False**; the feature is a downward step pinned to the schedule, never a conjugate-point corank rise.

**Kill_criterion:** "cond / ‖λ_r‖ flat (no spike at 61), or spike location wanders with seed" — **fired? YES** (first clause: no ‖λ_r‖ spike at 61 — it monotonically shrinks).

**Verdict reasoning:** The card predicts the costate norm *blows up* at 61; the measurement shows it monotonically *shrinks* through 61 with no discontinuity — the prediction is not just unmet, it's inverted. Because the round map is a bijection, J_r is full rank every round and λ_r stays full rank, so there is no conjugate point in the adjoint flow. The only 61-specific event is corank[J|B_feas] stepping N→0, which is the schedule pinning W[61] (the dW column is *removed from the optimization*, not a singularity of the transition map) — bookkeeping, identical across seeds, not a spike.

**Cross-check / skeptic note:** The skeptic warns the "condition number of a mod-arithmetic map is a heuristic" — so I used the rank (basis-independent, carry-noise-immune) of both the augmented map and the costate, which is unambiguous: full state-Jacobian rank, full costate rank, every round. The monotone ‖λ‖_F decay is the generic backward-reachability shrink (λ walking away from λ_64=I covers progressively fewer output directions), the same smooth phenomenon as OC1's switching taper. Consistent with prior finding #4 (no round-60/61 knee). Cross-validates OC1: same engine, same conclusion from the dual (costate vs switching) side.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OC4.py`
