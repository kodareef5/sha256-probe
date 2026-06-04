# W3-OT4 — The HW~74 plateau is a Nash equilibrium   ·   VERDICT: KILLED

**Card claim:** Two players (M1,M2), payoff −HW(output diff); cascade = best-response dynamics; the plateau = a strict Nash where no 1-bit flip lowers HW, and the 132 hard-core bits = the locked coordinates. Probe: greedy 1-bit best-response → sharp terminal-HW mode? locked-bit fraction ≈0.52? does a 2-bit move escape?

**Probe run:** Self-contained scaled mini-SHA-256 (rotations round(k·N/32), 64 rounds, MSB kernel). CRITICAL setup fix: the plateau is a property of the REAL freedom budget, not unconstrained search — with all 16 message words free (16N≫8N bits) greedy descent trivially zeroes HW. So search ranged over only the 4 free tail words W[12..15] (small-N analogue of W[57..60]; bulk message pinned). Greedy 1-bit best-response → 1-bit Nash; measured terminal-HW mode, hard-core locked fraction, per-register residual, and the decisive 2-bit escape. N=6,8, 24 random starts. Throttled.

**Result (numbers):**
- **Sharp terminal-HW mode EXISTS:** N=6 mode=15 (×7/24), mean 15.17, sd 1.40; N=8 mode=22 (×7/24), mean 21.29, sd 1.51.
- Terminal HW/total-bits = **0.316 (N=6), 0.333 (N=8)** — between the cascade-prediction 74/256=0.289 and the binomial floor 0.5. Plausibly consistent with the plateau.
- **Locked fraction = 0.000 (N=6), 0.094 (N=8) — NOT 0.52.** Off by ~5×.
- Per-register residual nonzero bits are **roughly EVEN** across all 8 registers (N=8: a=2.5 b=2.6 c=2.8 d=2.8 e=2.6 f=2.6 g=2.7 h=2.6) — NOT concentrated on a,b,e,f. The 132-bit a,b,e,f hard-core structure does NOT reproduce at reachable N.
- **2-bit escape: 6/8 (N=6), 8/8 (N=8)** converged points where a simultaneous 2-bit move beat the 1-bit terminal → it IS a unilateral trap.

**Kill_criterion:** "no mode, OR locked-fraction ≠0.52, OR 2-bit doesn't beat 1-bit" — **fired? YES** (middle clause: locked-fraction = 0.00–0.09 ≠ 0.52).

**Verdict reasoning:** Two of three sub-claims survive — there IS a sharp terminal-HW mode, and 2-bit moves DO escape the 1-bit Nash (so the basin is a genuine unilateral/coordination trap, not a global minimum). But the load-bearing quantitative claim — locked-bit fraction ≈0.52, the part that ties the "Nash" to the 132 hard-core bits — FAILS: the measured locked fraction is 0.00–0.09 and the residual HW is a roughly-even floor across all registers, not the a,b,e,f hard core. Because the kill criterion is an OR and the 0.52 clause fires, the card is KILLED as stated.

**Mechanism vs rename (the assigned question):** Partial. The 2-bit escape shows a real unilateral-trap structure (more than a pure binomial floor — that's mechanism-flavored). But the reframing does NOT reproduce the 132-bit / 0.52 identification it claims, so it does not establish a NEW mechanism beyond "a constrained-search local optimum exists"; the specific tie to the 132 hard core (the only content that would make it more than a rename) does not hold at reachable N.

**Cross-check / skeptic note:** The 0.52 = 132/256 is a full-32-bit-width measurement; the locked fraction does trend UP with N (0.000→0.094 from N=6→8), so it is conceivable it climbs toward 0.52 at full width — but at reachable N it is decisively not 0.52, and the per-register evenness argues against the a,b,e,f concentration even qualitatively. The binomial-floor skeptic is half-right: the residual is floor-like (even across registers) yet the 2-bit escape shows it is NOT a pure global floor. Honest status: the plateau and trap are real; the 132-bit Nash identification is not demonstrated here.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-OT4.py`
