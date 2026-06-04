# W3-IE4 — Modular add as a billiard; collisions as closed orbits   ·   VERDICT: KILLED

**Card claim:** a carry/wraparound = a billiard reflection off a 2^i wall; a SHA run = a billiard path in an N-cube; a collision = a near-closed orbit returning to the diagonal; rotation constants = launch angles (rational → periodic → collision-rich).

**Probe run:** N=4..10. Realized "modular add as a billiard" faithfully as rotations x→(x+θ) mod 2^N (carry/wrap = wall hit, closed orbit = rotation cycle, θ = launch angle from the SHA rotation constants); counted periodic orbits and fit log2(#orbits)/N; ran the kill-test (orbit-count vs real collision-count) and the skeptic test (are the carry walls fixed?). Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- Carry-billiard periodic-orbit count = **17 at every N** (4..10) — flat. #orbits per angle = gcd(θ, 2^N) = 1 for odd θ, 2 for θ=2; **data-independent of N**. Fit log2(#orbits)/N = **0.000** → not 0.74, not 0.673.
- Real collisions: 146, 1024, 83, 373, 1644, **14263 (spike@9)**, **1467 (trough@10)** — non-monotone.
- N=9→10: collisions DROP 14263→1467; orbits 17→17 (no drop) → orbit-count does not track collisions; correlation undefined (orbits constant).
- Skeptic test: #distinct carry-wall sets over 300 operand pairs = **50 (N=6), 111 (N=8), 175 (N=10)** — a real billiard would have **1** fixed table.

**Kill_criterion:** "orbit count and collision count diverge with N" — **fired? YES**

**Verdict reasoning:** Maximal divergence. The carry-billiard orbit count is constant (17) for all N — because gcd(odd-rotation-constant, 2^N) = 1 — so it carries no N-dependence at all, let alone the non-monotone collision profile (it cannot produce the N=9 spike or N=10 trough). The growth slope (0.000) matches neither 0.74 nor 0.673. The card's own skeptic is decisively confirmed: the carry "walls" are data-dependent (up to 175 distinct wall-sets per N), so there is no fixed billiard table — the construction is decoration on carry arithmetic, not a billiard.

**Cross-check / skeptic note:** The rotation realization is the most charitable faithful reading of "modular add as a billiard on Z/2^N"; one could instead try a 2D N-cube billiard with the rotation constants as a slope, but any such fixed polygonal billiard has a smooth/quasi-polynomial periodic-orbit count and still cannot reproduce a non-monotone collision curve with a spike@9 and trough@10 — the kill fires regardless. The constant-17 result is robust (closed-form gcd, not a fit). This is consistent with prior findings #2 (no construction gives a clean 0.74) and #4 (N is never special; the bumps are kernel/cascade combinatorics, not billiard resonances).

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-IE4.py`
