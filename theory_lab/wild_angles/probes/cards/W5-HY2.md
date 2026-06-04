# W5-HY2 — Systole → the minimal collision differential as the shortest essential loop   ·   VERDICT: KILLED

**Card claim:** The feed-forward gluing turns the descent tree into a complex with π₁; a collision = a non-contractible loop; the minimal-HW collision = the **systole** (the "N=10 HW-1 boundary word" is a short-systole datum). #short essential classes vs 2^0.74N.

**Probe run:** N=4 exhaustive (throttled); N=8/10 collision counts from repo ground truth. Tested the card's own kill clauses: (1) do collision "loops" (difference trajectory returning to 0 = a full sr=60 collision) require the feed-forward gluing, or do they exist in the bare single-block cascade that has *no* gluing? (2) Is there a sharp, well-defined systole (a unique minimal-HW collision) or a degenerate flat distribution ("everything is a loop")? (3) #collisions vs 2^0.74N at reachable N.

**Result (numbers):**
- (1) **49 collision loops exist at N=4 in the single-block cascade with NO feed-forward gluing.** The gluing is absent in this model, yet the loops are there.
- (2) Minimal internal activity = **6** (not 1); **39 of 49** collisions sit at the same min-act=6, only **2 distinct** activity values (6, 7). Flat, not sharp — no unique systole, no "HW-1" datum.
- (3) Count exponent log₂(#coll)/N: N=4 → 1.40, N=8 → 1.00, N=10 → 0.99 (#coll = 49/260/946 vs 2^0.74N = 7.8/60.5/168.9). **~1.0, not 0.74.**
- The cited "N=10 HW-1 boundary word" could not be located anywhere in the repo (block2_wang collisions live at HW 36–139, not 1).

**Kill_criterion:** "systole ≠ the N=10 minimal collision, OR essential loops exist without the feed-forward gluing" — **fired? YES (both arms).**

**Verdict reasoning:** The second kill arm fires literally: 49 collision "loops" exist in the bare single-block cascade with **no feed-forward gluing at all**, so the gluing is not what creates them — they are endpoint coincidences (de63=0), which are *contractible*, not the non-contractible loops a π₁/systole story requires. Without a strict gluing model "essential" is undefined and every collision is trivially a loop — exactly the skeptic's stated failure mode. The first kill arm also fires: there is no sharp systole (min activity = 6, 39/49 tied at the minimum, only 2 distinct values — a flat distribution, not a single shortest essential class), and the anchoring "N=10 HW-1 boundary word" datum does not appear to exist in the repo. The count likewise does not behave systolically: ~2^1.0·N at reachable N, not 2^0.74N. So the topological framing has no carrier object here and contradicts its own kill criteria.

**Cross-check / skeptic note:** To rescue this card one would need (a) the actual two-block feed-forward construction (block2_wang) with an explicit gluing that makes collision differentials non-contractible, and (b) a demonstrably *unique* minimal-HW witness equal to a known datum. Neither is available: the single-block cascade (where the repo's exhaustive collisions live) has no gluing, its minimal collisions are degenerate-flat at HW≈6, and the block2_wang two-block corpus sits at HW 36–139 with no HW-1 witness. The 0.74 exponent is the asymptotic collision-growth rate, not a systole count, and it doesn't match at any reachable N. This is a vocabulary overlay (`mech: count`) onto "collisions are coincidences of endpoints" with no π₁ content; the systole = minimal collision identification fails.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HY2.py`
