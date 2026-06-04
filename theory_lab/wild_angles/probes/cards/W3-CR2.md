# W3-CR2 — The da=0 cascade is a stoichiometric siphon   ·   VERDICT: CONFIRMED

**Card claim:** A siphon = a species set that, once empty, can never refill (every producing reaction also consumes one in the set) — verbatim the cascade's "da=0 propagates forward as 0." Minimal siphons + moiety laws (left-nullspace of S) are the invariants the cascade exploits; a second siphon may be the leftover tail-gap.

**Probe run:** Built the per-round difference-reaction network at bit granularity (species = `d<lane>_<bit>` for lanes a..h; reactions = the exact shift-register copies a→b→c→d, e→f→g→h plus the two adder heads da′, de′ with their genuine Sigma0/Sigma1/Ch/Maj fan-in and intra-adder carry coupling). Tested the siphon predicate (every reaction producing a Z-species also consumes a Z-species), brute-enumerated minimal lane-siphons (256 subsets), and computed the moiety-law dimension = left-nullspace of the net stoichiometric matrix. N=4,5,6, exact integer/rational algebra, throttled.

**Result (numbers):**
- **Minimal siphons = {a} and {e}** at N=4,5,6 — exactly the two cascade heads.
- a-path front {da,db,dc,dd} and e-path front {de,df,dg,dh} are both siphons (forward closures of {a},{e}); the diagonal zero-wave is siphon-closed bit-for-bit.
- {a} alone is a siphon: da=0 cannot refill. Mechanism check — strip the a-lane self/carry dependence from the a-producing reaction and {a} is **no longer** a siphon (False), confirming the property comes from the genuine Sigma0(a)/Maj/carry feedback, not an encoding artifact.
- Moiety conservation-law dim (left-nullspace of S) = **0** (not 132).

**Kill_criterion:** "siphons bear no relation to the cascade, OR no nontrivial siphon exists." — **fired? NO**

**Verdict reasoning:** The two minimal siphons of the difference network are *literally* the two cascade fronts {a} and {e}; the da=0 / de=0 propagation is the textbook siphon property ("once empty, never refills"), and it holds precisely because the head lane feeds back into itself through Sigma0/Maj/carry (verified by ablation). The kill criterion is decisively not met — this is a near-definitional, mechanistically-grounded match, the strongest outcome. This also gives a structural handle on the open "is there a better drain than the cascade?" question: any drain must empty a siphon, and the minimal siphons are exactly {a},{e}.

**Cross-check / skeptic note:** Two speculative sub-hooks in the card do NOT survive and should not be carried forward: (1) the "conserved-moiety dim vs 132" — measured dim is **0**, consistent with the project-wide finding that "132 = corank/moiety" is a category error; (2) "a *second* siphon over the tail" — there is no separate tail-gap siphon; the only minimal siphons are {a},{e}. The carry coupling is modeled as incidence (presence), which is the correct granularity for the purely combinatorial siphon question; magnitudes are irrelevant to siphon-hood, so the result is robust. The core claim stands as CONFIRMED; the tail-residue extension is unsupported.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-CR2.py`
