# W1-GE2 — Holonomy / winding around the W57 circle   ·   VERDICT: KILLED

**Card claim:** The residual is 1-D in W57 (a circle); transport a difference around it — nonzero winding number forces a zero-crossing = a guaranteed collision (winding count ≥ collision count).
**Probe run:** Genuine tail arithmetic (repo `precompute_state` + `run_tail_rounds` via shabridge) on the verified sr=60 champion (m0=0x17149975, fill=0xffffffff, bit=31, the (0,9) kernel pair). Swept the free word W[57] over a 2^N circle (N=6,7,8; W58=W59=W60 fixed), read the round-61 residual D[reg]=state1[reg]−state2[reg], computed its winding number around Z/2^N and counted zeros; compared to a fresh seeded PRF of the same range. Then the fairest-shot variant: projected the residual to a small modulus 2^b (b=2,3,4) so zeros are dense, and tested whether winding predicts that zero count. Throttled.

**Result (numbers):**
- Full 32-bit residual, all 8 registers, N=6/7/8: **#zeros = 0** (identical to PRF baseline z=0); winding numbers are small O(1) integers (range −5..+8), indistinguishable from the PRF's winding (3–4). `|winding| == #zeros` never holds. Full 8-register round-61 collisions over each circle: **0**.
- Projected small circle (residual mod 2^b), N=8: zeros become dense (b=2→68, b=3→37, b=4→14) but winding = (32, 16, −5) — **|winding| ≠ #zeros in every case**. The coordinate crosses 0 far more often than its net winding, the hallmark of cancelling (random/jumpy) crossings, not a degree-d wrap.

**Kill_criterion:** "Dead if H(W57) is statistically indistinguishable from a fresh pseudorandom function (winding ~ random-walk √-scaling, no predictive zeros)." — **fired? yes**

**Verdict reasoning:** The residual H(W57)=D61 behaves like a pseudorandom function of W57: at full width it has no zeros on any reachable circle (like the PRF), and where zeros are made dense by projection, the winding number fails to count them (|winding| ≠ #zeros). The card's degree-theory mechanism requires a *predictive* winding — nonzero winding forcing and counting zero-crossings — and that predictive relationship is absent. The winding is just the small net drift of a jumpy carry-driven map; it does not certify or count collisions.

**Cross-check / skeptic note:** The card's own skeptic flagged exactly this ("carries make H jumpy — must check winding predicts the zero count"), and the projected-circle test confirms the failure quantitatively (68 zeros vs winding 32). One could argue a *cleverer* 1-form/lift could recover degree structure, but on the natural register-coordinate projection there is none, and the repo's independent result (sr=61 residual gating g1,h are uniform/independent, 2^−2N) says the residual carries no exploitable low-dimensional structure either — converging on "PRF-like residual." The winding ≈ √-scaling random-walk expectation (winding ~ a few for ~10² samples) matches the PRF, sealing the kill.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W1-GE2.py`
