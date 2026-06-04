# W3-CR4 — Detailed-balance breaking at the feed-forward ADD   ·   VERDICT: KILLED

**Card claim:** Every round is a permutation (reversible/detailed-balanced); the one irreversible 2-to-1 reaction is the Davies-Meyer final ADD (H_out = H_in + state) — so all entropy-production / Wegscheider deficiency localizes there, and the **collision baseline = the ADD's fiber multiplicity**.

**Probe run:** At N=3,4,5 verified the round-core is a bijection by exact image-size enumeration over a 4-lane (a,e,h,d) sub-state. At N=4,6,8 computed the exact Davies-Meyer ADD fiber histogram |{(A,B): A+B = C mod 2^N}|. Compared the ADD fiber multiplicity to the two collision baselines (count 2^0.74N, rate 2^-2N) by exponent, and checked whether |de58| matches an ADD fiber. Exact enumeration, throttled.

**Result (numbers):**
- Round-core is a **bijection**: image size = domain size exactly (4096, 65536, 1048576 at N=3,4,5) → zero entropy production in the core; all folding is at the DM ADD. (Card's structural premise: correct.)
- ADD fiber is **perfectly uniform = 2^N for every C**: histograms {16:16}, {64:64}, {256:256}. It carries no round structure.
- Exponent mismatch: ADD-fiber per lane ~ 2^N (exp **1.0**); collision count ~ 2^0.74N (exp **0.74**); rate 2^-2N (exp **−2**). None equal.
- |de58| follows **2^hw(db56)** (2,8,8,16,32,512 at N=4,6,8,10,11,12), the Maj-image-under-difference law — **NOT** 2^N. de58 fingerprints the round-internal Maj/carry nonlinearity, not the ADD fold.

**Kill_criterion:** "entropy production smeared across rounds, OR ADD fibers unrelated to the collision baseline." — **fired? YES (second clause)**

**Verdict reasoning:** The structural half is true and even elegant — the round is a genuine permutation (zero entropy production), so the only 2-to-1 fold is the Davies-Meyer ADD. But the *predictive* half fails: the modular-add fiber is trivially uniform (exactly 2^N for every output, no structure whatsoever), and its multiplicity matches **none** of the collision baselines — the exponents 1.0 vs 0.74 vs −2 are all different — and |de58| is governed by 2^hw(db56), not 2^N. So the ADD fibers are unrelated to the collision baseline; the second kill clause fires. The collision-relevant structure lives in the round-internal Maj/carry nonlinearity (the de58 law), exactly where the card says it *isn't*.

**Cross-check / skeptic note:** This is precisely the skeptic note's prediction — "an invertible permutation has no thermodynamic equilibrium" (so "detailed-balanced" is a loose reading, though "bijection / measure-preserving" is the defensible content and it checks out) and "`+ mod 2^N` fibers are ~uniform and hold none of the round structure" (confirmed exactly: uniform 2^N). The bijectivity check used a 4-lane sub-state; full 8-lane bijectivity is a standard consequence of the invertible shift-register + adders, and the sub-state being a perfect permutation is consistent with it. The kill is on the count-prediction, not the structural observation; the structural observation could be recycled as a (true but non-predictive) framing note.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-CR4.py`
