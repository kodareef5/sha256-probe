# W8-CL1 — Laurent pole-order → the wall = the first non-Laurent cascade step   ·   VERDICT: KILLED

**Card claim:** `casoff(r)` (the offset forcing da=0) is Laurent in the free seed (denominators cancel) for r≤60; at 61 W[61] is schedule-pinned (no free variable to divide by) → a real pole, an invalid cluster mutation. Predict pole_order(r)=0 for r≤60, ≥1 at 61.

**Probe run:** Faithful mini-SHA(N) cascade (matching repo `backward_construct_n10.c` / `gap_analysis.c`: MSB kernel, word-pair (0,9), fill=all-ones, scaled rotations, cascade DP). N=8 (M0=0x67), N=10 (M0=0x34c), N=12 (M0=0x22b). For thousands of random free seeds, computed `casoff(r)=find_w2(...)−w1` (the pure state-difference offset) at every round 57..62, tested (P1) totality/no-division at each round, (P2) the 3-term exchange-relation hallmark `casoff(60)·casoff(58) − casoff(59)²`. Throttled: yes.

**Result (numbers):**
- `casoff` is **TOTAL** (defined, no division/inverse-of-zero) at **every** round 57..62 at all three N — so pole_order(r)=0 identically, r≤60 and r=61 alike.
- casoff is just as seed-dependent at 61/62 as at 58/60: distinct-value counts at N=10 are r58=513, r59=1008, r60=957, **r61=425, r62=317** — round 61 is not a structural pole, it is well-defined.
- Exchange-relation test: `casoff(60)·casoff(58) − casoff(59)²` takes **987 distinct values over 3980 seeds** (N=10; 256/3965 at N=8; 1844/2498 at N=12) — **not constant** → no cluster binomial exchange relation. casoff is additive-random in the seed.

**Kill_criterion:** "pole_order(61)=0, OR some r≤60 already >0." — **fired? yes** (pole_order(61)=0 — measured 0 at *all* rounds).

**Verdict reasoning:** `find_w2`/`casoff = (w1 + r1 − r2 + T21 − T22) mod 2^N` is a **purely additive** map in the group Z_{2^N} — no inversion, hence no denominator and no pole at any round, refuting the card's central claim. Round 61 is not a Laurent singularity; it is the additive **value-match condition** (g1=0 ∧ h=0, the established schedule gate). This is exactly prior-finding #4: rounds 57–60 are the free cascade and 61 is the schedule condition — the cascade is "Laurent-trivial" (denominator-free) *throughout*, including 61. The skeptic's real bar (a genuine 3-term exchange relation `casoff(r+1)·casoff(r−1)=M₊+M₋`) is also failed: the product is seed-random, not a binomial, so casoff is not a cluster variable.

**Cross-check / skeptic note:** The engine reproduces the known cascade (M0=0x67 at N=8 matches the repo; de-cascade structure matches W7-CG1). The result is robust across N=8/10/12. A defender might argue casoff *would* divide if recast over a field of fractions; but the actual object is the mod-2^N additive offset the enumerator computes, which is total everywhere — the "pole at 61" is imported vocabulary, not a feature of the map.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W8-CL1.py`
