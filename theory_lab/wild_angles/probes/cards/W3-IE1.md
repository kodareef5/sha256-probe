# W3-IE1 — Σ-mixing as a 3-IET; 0.74 as a KZ Lyapunov exponent   ·   VERDICT: KILLED

**Card claim:** Σ0={2,13,22}, Σ1={6,11,25} (rotation-only) form a 3-IET on the bit-position circle; round composition = Teichmüller iteration; the bit-spread rate = the top Kontsevich–Zorich Lyapunov exponent, claimed = 0.74.

**Probe run:** N=4..14 built the literal 3-IET (3 contiguous arcs of Z/N translated by the Σ offsets), counted periodic orbits (= cycles of the permutation), fit log2(#orbits)/N; computed the *actual* top Lyapunov exponent χ₁ of the round differential cocycle (`transfer_operator.lyapunov_qr`, N=6,8,10) as the literal "KZ Lyapunov" object; ran a kill-test vs 12 random triples. Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- Real repo growth slope (Fig-2 refit): pooled **0.6732**, per-(N mod 4) spread 0.72..1.04 — 0.74 is not even the true number.
- 3-IET periodic-orbit count grows ~O(N) (cycles of an N-point permutation): fit slope **0.166** (Σ0), 0.103 (Σ1) → log2(#orbits)/N → 0, NOT 0.74.
- Actual top Lyapunov exponent χ₁ = 1.636 (N=6), 2.017 (N=8), 2.253 (N=10), mean **1.97 bits/round** — not 0.74, not 0.673.
- KILL-TEST: random-triple orbit-slope mean **0.114 ± 0.062**; Σ0's 0.166 sits **0.84 σ** from the random mean → NOT special to {2,13,22}.

**Kill_criterion:** "exponent independent of {2,13,22} (random triples give the same)" — **fired? YES**

**Verdict reasoning:** Every leg fails. The literal 3-IET orbit exponent (a) is ~0 (permutation cycle counts grow polynomially, not 2^0.74N), (b) is statistically indistinguishable from random triples (0.84 σ), and (c) the genuine differential-cocycle Lyapunov exponent is ≈1.97 bits/round, an order of magnitude off 0.74 and not 0.673 either. Per prior finding #2, a value in 0.6–0.8 would prove nothing anyway, but here nothing even lands in that band. The card's own skeptic ("XOR isn't interval *exchange* — a random-walk exponent in IET costume") is exactly confirmed: the offsets carry no privileged IET signal.

**Cross-check / skeptic note:** Two independent objects (combinatorial orbit count + numeric cocycle Lyapunov) both reject 0.74, and the random-triple control directly fires the stated kill. The Lyapunov-QR raised raw-matmul overflow warnings at N=10, but QR reorthonormalization absorbs them and the χ₁ sequence is smooth/monotone (1.64→2.02→2.25), so the ~2 bits/round figure is robust. If anything the χ₁≈2 echoes the *de58/2^-2N rank-2* structure, not a KZ exponent.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-IE1.py`
