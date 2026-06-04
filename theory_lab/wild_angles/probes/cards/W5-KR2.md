# W5-KR2 — Holonomy decomposition: de58's power-of-2 image is a cyclic-group order   ·   VERDICT: KILLED

**Card claim:** The carry monoid's holonomy groups are tiny/cyclic; de58 is the unique register at the one poset level with nontrivial (Z/2^k) holonomy, k = log2|de58|, EXPLAINING "de58 grows (power of 2), de57/59/60 constant (trivial holonomy)."

**Probe run:** N >= 6 (and exact for the carry monoid, which lives on the 1-bit carry state independent of N; throttled). (A) Built the binary-addition carry transformation monoid (generators KILL: c->0, GENERATE: c->1, PROP: c->c) and computed its size, aperiodicity, and per-idempotent maximal-subgroup (holonomy group) orders. (B) Checked whether any product of holonomy-group orders equals |de58|=2^hw(db56) for N=8..14. (C) Identified the true source of 2^hw.

**Result (numbers):**
- Carry monoid: |M| = 3 (elements {KILL, PROP=id, GENERATE}), **max functional period = 1 -> APERIODIC (group-free)**. Maximal-subgroup (holonomy) orders per idempotent = [1, 1, 1] — all trivial. No nontrivial holonomy group exists.
- de58 vs holonomy: |de58| = 8,16,32,512,32,32 at N=8,10,11,12,13,14 (all powers of 2, 2^hw(db56)); the product of holonomy-group orders is **1 in every case** — it never equals 8/16/32/512. holonomy-derives-exponent = **False** for all N.
- Source of 2^hw: de58 = #{distinct Maj/carry images} = 2^(free image bits) = 2^hw(db56) — an image COUNT of a group-free map, not a Z/2^k group order.

**Kill_criterion:** "holonomy groups non-cyclic at N>=6, OR de58 image not a power of 2 at N=8..14." — **literal clauses fired? NO** (holonomy is trivial = order-1, technically cyclic; de58 IS always a power of 2). **Mechanism refuted? YES.**

**Verdict reasoning:** KILLED. The two literally-worded kill clauses do not fire — but that is because the kill_criterion is mis-specified: it tests "non-cyclic" and "not a power of 2", whereas the card's actual mechanism is "de58's 2^k IS a nontrivial cyclic HOLONOMY GROUP ORDER." That mechanism is positively FALSE: the integer-addition carry monoid is the textbook flip-flop monoid {0,1,id}, which is aperiodic / group-free, so ALL its holonomy groups are trivial (order 1). A trivial holonomy cannot supply the exponent — the product of holonomy orders is 1, never 2^hw. Per prior finding #6 (explicit instruction: "CONFIRM only if holonomy DERIVES the hw(db56) exponent, else it's a restate"), holonomy does NOT derive hw(db56); worse than a restate, the cyclic-group-order interpretation is provably wrong. The real 2^hw(db56) is a Maj/AND image-count of a group-free map. de57/59/60 being constant is likewise NOT "trivial holonomy" (all four registers have the same trivial carry holonomy) — it's that only db56's free-bit count feeds de58.

**Cross-check / skeptic note:** Could a *coarser* carry monoid (tracking multi-bit carry state, or the Maj gate as a 3->1 map) carry a hidden group? No — addition's Krohn-Rhodes decomposition is the canonical group-free (combinationally-aperiodic) example; multi-bit carry states still compose to the same flip-flop semilattice, and Maj/Ch/AND are monotone/aperiodic boolean functions (no group). The power-of-2 is genuine and matches 2^hw exactly (consistent with the pinned DE_LAW), but it is a counting coincidence of free image bits, not holonomy. To revive KR2 one would have to exhibit a nontrivial cyclic subgroup in the carry/Maj monoid at N>=6 — Part A shows there is none.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-KR2.py`
