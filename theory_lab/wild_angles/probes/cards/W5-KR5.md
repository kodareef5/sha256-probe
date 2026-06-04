# W5-KR5 — Group kernel: all group complexity localizes to the feed-forward ADD   ·   VERDICT: KILLED

**Card claim:** The whole-compression monoid's maximal group quotient G(M) equals the feed-forward translation group <H_in + .>, with the 64 reversible rounds sitting in the APERIODIC (group-trivial) kernel — the algebraic form of "collisions born in the ADD"; hardness constant in round count. Probe asks: is rounds-only G trivial?

**Probe run:** N=2,3 (throttled). (A) For a representative tail round constant k=K[60] and several message words w, built the permutation each SHA round induces on the (a,e) head carrier, computed its cyclic order, and computed the order of the permutation GROUP the round-maps generate. (B) Recorded the Davies-Meyer feed-forward translation group order.

**Result (numbers):**
- N=2: each round map IS a permutation of the 16 head states with nontrivial cyclic order (w=0->order 12, w=1->8, w=2->12, w=3->8). The rounds-only GROUP they generate has **order 36864** (fully enumerated). Rounds-only group-trivial? **FALSE.**
- N=3: round maps are permutations of order 120, 24, 60, 21; the generated rounds-only group exceeds 2,000,000 (cap). Group-trivial? **FALSE.**
- Feed-forward translation group (Z/2^N)^8: order 65536 (N=2) / 16.7M (N=3) — nontrivial abelian, where collisions are forced.

**Kill_criterion:** "rounds-only (no feed-forward) has a NONTRIVIAL group quotient (rotations carry group complexity) — a valuable negative." — **fired? YES.**

**Verdict reasoning:** The kill fires cleanly. The reversible rounds are NOT in the aperiodic kernel — they generate a large permutation group (order 36864 at N=2 from just four word-actions; round-map orders 8/12/24/60/120). Group complexity therefore does NOT localize to the feed-forward ADD: the rotations / reversible round permutation carry abundant group complexity on their own. The card's predicted G(M) = "feed-forward translation group alone, rounds-only trivial" is the opposite of what the data shows. This is the "valuable negative" the card itself flags. Per prior finding #5, a CONFIRMED would require a NEW number for the "carries = hardness" fact; KR5 produces no such number and in fact contradicts its own localization premise.

**Cross-check / skeptic note:** A skeptic might say the (a,e)-head restriction with pinned tail lanes overstates group structure — but restriction can only QUOTIENT a monoid, so a nontrivial group on the head is a faithful WITNESS (lower bound) of group complexity in the full round monoid; the true rounds-only group is at least this large. Independent corroboration: W5-KR1 found the SAME group element (period 12) in the round monoid, and the round update is literally invertible (a permutation given w). The genuinely many-to-one, collision-producing step is indeed the final feed-forward ADD — but the card's stronger claim that the rounds are group-FREE is false.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-KR5.py`
