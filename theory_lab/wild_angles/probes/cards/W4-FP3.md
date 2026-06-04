# W4-FP3 — Asymptotic freeness of the ARX layers → the round spectrum factorizes   ·   VERDICT: KILLED

**Card claim:** If the fixed XOR-rotation layer L and the carry-add layer A are free, μ(AL)=μ_A⊠μ_L → 64 rounds reduce to ⊠ of two alternating laws.

**Probe run:** N=4,6,8,10, throttled. Sharp Voiculescu free identity for free a,b: τ(abab)=τ(a²)τ(b)²+τ(a)²τ(b²)−τ(a)²τ(b)². I built L = the fixed XOR-rotation/shift-register layer (carry-dropped round operator = linround, real 8N×8N), and A = J·L⁻¹ (the carry-add correction, verified A·L = J_local exactly at the base point), with τ(·)=(1/8N)tr(·). Measured τ(ALAL) directly vs the free prediction from marginals; defect = |measured − free|/|measured|, averaged over 6 base points per N. Also reported the commutator ‖[A,L]‖/‖AL‖.

**Result (numbers):**
| N | freeness defect of τ(ALAL) | spread | ‖[A,L]‖/‖AL‖ |
|---|---|---|---|
| 4 | 0.567 | 0.47–0.69 | 1.89 |
| 6 | 0.289 | 0.23–0.33 | 2.52 |
| 8 | 0.590 | 0.51–0.66 | 2.48 |
| 10 | 0.697 | 0.64–0.75 | 2.31 |

**Kill_criterion:** "deviation doesn't shrink, or μ_{AL}≠μ_L⊠μ_A" — **fired? YES.**

**Verdict reasoning:** The freeness defect does not shrink toward 0 as N grows — it is non-monotone (0.57→0.29→0.59→0.70) and ends *larger* than it started, never approaching the 0 that asymptotic freeness requires. The free mixed-moment identity is violated by 30–70% at every N. The two layers are strongly interlocked (commutator norm ≈ 1.9–2.5× the product norm), so they are nowhere near free. Kill fires on the "deviation doesn't shrink" clause.

**Cross-check / skeptic note:** This confirms the card's own baked-in skeptic note: L is a *fixed* matrix sharing the exact bit-lane geometry of A (rotations and carries act on the same lanes), so SHA's layers are designed to interlock — the opposite of the genuine randomness + large dimension that asymptotic freeness demands. The non-monotonicity (the N=6 dip) is a finite-size artifact of the scaled rotation amounts, not a trend toward freeness; the surrounding N=4,8,10 values bracket it well away from 0. A skeptic's null check: if the layers *were* free the defect would fall like O(1/N) — instead it stays O(0.1–1), so this is a real KILL, not a reachable-N limitation.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-FP3.py`
