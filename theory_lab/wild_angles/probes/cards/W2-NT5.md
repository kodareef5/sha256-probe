# W2-NT5 — Canonical height → collisions as height-zero preperiodic coincidences   ·   VERDICT: KILLED

**Card claim:** Give the schedule a canonical height ĥ(M) = lim(bit-spread/depth); preperiodic (ĥ=0) points are messages whose carry-orbit collapses — the low-HW structured fills (0x55, 0x15) the repo keeps rediscovering. A collision is a height-zero coincidence; small-height equidistribution predicts collisions concentrate at low ĥ. Probe: do colliding pairs have lower ĥ? do 0x55/0x15 sit at ĥ≈0?

**Probe run:** N=8 and N=10, throttled. Defined a height proxy ĥ(M) = mean over R=48 rounds of the state bit-spread (popcount over 8 registers / 8N); a collapsing/preperiodic orbit → low ĥ, a scrambling orbit → ≈0.5. Compared the measured N=10 sr=60 collision tails (from `gap_rows.csv`, embedded as schedule words on the MSB-cascade base) against matched random tails; scored ĥ for structured fills 0x55/0x15/0xAA/zero/all-ones/MSB; and correlated ĥ with input Hamming weight to test the skeptic's "ĥ is just HW" worry.

**Result (numbers):**
- **Collision vs random (N=10):** collision mean ĥ = 0.4924 vs random 0.4913 → difference **+0.0011** (collisions are if anything *higher*, not lower); **KS separation = 0.057** (negligible). The two distributions coincide.
- **Structured fills are not low-height:** N=8 — 0x55 at percentile **0.84 (HIGH)**, 0x15 at 0.18; N=10 — 0x55 at 0.41, 0x15 at **0.50 (dead center)**, 0xAA at 0.81 (high). Scattered around the middle, no clustering at ĥ≈0.
- **ĥ saturates at ~0.5** (full scrambling) for nearly everything; random mean 0.503 (N=8) / 0.502 (N=10), sd ~0.016.
- **HW confounder:** corr(ĥ, input HW) = +0.04 (N=8), −0.05 (N=10) → ĥ is not even tracking HW; it's measuring almost nothing structured.

**Kill_criterion:** "Dead if colliding pairs have the same ĥ distribution as random pairs, or structured fills aren't low-height." — **fired? yes (both clauses).**

**Verdict reasoning:** Both kill clauses fire independently. (1) Colliding tails and random tails have statistically identical ĥ (mean gap +0.001, KS 0.057) — collisions do not concentrate at low height. (2) The structured fills 0x55/0x15 are not low-height; 0x55 is actually *high* at N=8 (84th percentile) and central at N=10. The height proxy saturates at ≈0.5 for essentially all inputs, meaning the round map scrambles every orbit — there is no preperiodic/collapse locus to be the ĥ=0 set. The "canonical height over Z/2^N" does not converge to a discriminating invariant here; the arithmetic-dynamics framing has no traction on this digest.

**Cross-check / skeptic note:** The card's own skeptic line ("the proxy may just re-measure Hamming weight") is *more* damning than feared — ĥ correlates with neither HW (~0) nor collision membership (KS 0.057), so it measures nothing useful, ruling out even a trivial HW-restatement "pass." A different proxy (e.g. 2-adic valuation depth, or a true carry-orbit period) might behave differently, but that is the 2-adic lens the card explicitly says it is *not* a rebrand of; under the Archimedean bit-spread height the card specifies, the locus is empty. What would change this: a height with a genuine ĥ=0 attracting set that the structured fills provably hit — none is visible at N=8,10.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-NT5.py`
