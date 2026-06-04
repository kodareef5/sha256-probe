# W5-ER3 — Commute-time divergence → 2^-2N as two series resistors   ·   VERDICT: KILLED (substrate real, W[60]-shortcut mechanism falsified)

**Card claim:** The cascade is a random walk; hitting time to the collision set = 2m·R_eff. sr=60→61 = cutting the W[60] shortcut, forcing current through **two series resistors** (g1=0, h=0) → commute time **multiplies** (the factor-2 in 2^-2N). Commute-time exponent c ≈ 1.26.

**Probe run:** N=8,10, throttled. Three pieces: (A) commute-time exponent from target density; (B) the rank-2 substrate from the real N=10 `gap_rows` data; (C) the discriminating sub-claim — does cutting the W[60] lever *multiply* commute time by ~2^N, specifically gating one of the two conditions? Part (C) uses avalanche (single-bit-flip sensitivity of each free word onto residues r_g=a, r_h=e) and GF(2) reachable-dimension with vs without W[60]. (An initial Hamming-descent hitting walk was discarded — it censored regardless of W[60], measuring greedy-descent pathology, not the shortcut.)

**Result (numbers):**

(B) **Substrate is real:** g2 = g1+h exact for **946/946** N=10 collisions → genuinely rank-2; the two conditions {g1=0, h=0} are independent (bit-0 χ²(g1,h)=0.004 ≪ 3.84). So 2^-2N = P(g1=0)·P(h=0) = 2^-N·2^-N, two independent N-bit conditions. **This part matches finding #3.**

(A) Exponent: two N-bit factors give c=2 (absolute target) or c=1.26 (relative to the 2^0.74N collision set). Either framing is "two N-bit factors," so part (A) is near-tautological (does not by itself fire |c−1.26|>0.3).

(C) **The card's mechanism FAILS.** All four free words avalanche both residues *equally*:

| N | av W57→r_h | av W58→r_h | av W59→r_h | av W60→r_h | r_h dim drop (cut W60) | r_g dim drop |
|---|---|---|---|---|---|---|
| 8  | 0.493 | 0.501 | 0.499 | 0.510 | **0** (8→8) | 0 |
| 10 | 0.499 | 0.503 | 0.504 | 0.505 | **0** (10→10) | 0 |

Joint reachable dim [r_g\|r_h] stays full (16/16, 20/20) with W[60] removed — W57/58/59 already span the whole residue space. Real-data cross-check: among 946 collisions, w60 takes 593 distinct values, corr(w60, h)=−0.015, and the linear coefficient of w60 on h (−0.015) is no larger than the other words'. **W[60] is not a privileged shortcut for the h-condition.**

**Kill_criterion:** "commute-time exponent c clearly ≠ 1.26 at N=8,10, OR removing W[60] changes it sub-exponentially." — **fired? YES (second clause).** Removing W[60] changes reachability by **zero** (dim drop = 0) — maximally sub-exponential; commute time does not multiply.

**Verdict reasoning:** KILLED. This is a rename/wrong-mechanism case (the pattern flagged in finding #5): the card lands on the *real* substrate — the genuine rank-2 two-conditions {g1=0,h=0} (part B is CONFIRM-grade) — but the **discriminating** sub-claim (b), that W[60] is *the* shortcut whose removal forces a second series resistor and *multiplies* commute time, is falsified. W[60] is interchangeable with the other free words; cutting it leaves full reachability. Per the card's own skeptic, only sub-claim (b) reproducing the **2** via the W[60]-cut is discriminating — and it does not. So "2^-2N = two series resistors with W[60] as the cut shortcut" is a re-description of the two-conditions with a false causal story, not a derivation.

**Cross-check / skeptic note:** One could argue the a/e residues only proxy g1/h. But the real `gap_rows` regression independently shows w60 has no distinguished control of h (coef −0.015, corr −0.015), confirming the structural finding on the genuine gating quantities. The two-conditions fact itself (part B) is rock-solid and is the legitimate, mechanism-correct content — but it belongs to the sr-step's independent-conditions structure (already CONFIRMED ~9×), not to a W[60]-resistor-cut. Promoting this to CONFIRMED would reward the rename, which the playbook forbids.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-ER3.py`
