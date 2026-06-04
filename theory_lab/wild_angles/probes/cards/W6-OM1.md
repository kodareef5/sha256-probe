# W6-OM1 — Cell-count explosion → the wall = loss of uniform finiteness   ·   VERDICT: KILLED

**Card claim:** per-round count of "cells" (maximal solution-runs in a fixed coordinate order) is BOUNDED (O(1) fat cascade cells) for rounds ≤60 and EXPLODES at 61 — the o-minimal signature of a wild set.

**Probe run:** N=4 exact (throttled): enumerated all 2^16 tuples (w57,w58,w59,w60), bucketed into the per-round solution sets — cube (consistent through r≤60), {de61=0} (r61), {full sr=60 collision} (r63) — and computed the cell count = average number of maximal solution-runs along a lexicographic sweep over 30 random coordinate orders + random per-axis value relabelings (±std). N=8 corroboration: cell count of the 260 verified C-enumerator collisions over 30 orders.

**Result (numbers):**
| per-round set | cells (mean ± std) | density |
|---|---|---|
| cube (r≤60) | 1.00 ± 0.00 (analytic: whole space, 1 solid cell) | 1.0000 |
| {de61=0} (r61) | 3833 ± 524 | 0.0740 (4848 pts) |
| {collision} (r63) | 47.2 ± 2.4 | 0.0007 (49 pts) |

N=8: collision-set = **260 cells over 260 points** (cells/point = 1.000 — totally disconnected sieve). Cube(r≤60) is still 1 solid cell.

**Kill_criterion:** "already Θ(2^N) for r≤58, or smooth/monotone with no break near 60/61." — **fired? yes (clause B / premise false).**

**Verdict reasoning:** The card's picture — "bounded O(1) *fat* cells ≤60 that explode at 61" — is structurally false. The cascade keeps da=0 for FREE at every round 57–60 (path-2's words solved by find_w2 for all tuples), so the solution set through any r≤60 is the **entire cube = exactly 1 solid cell**, with NO per-round cell growth across 57→58→59→60. The cell count does not gradually build toward 61; the only change is a single architectural step at round 61 (the first real condition, the boundary proof's cascade break), and the moment any real condition appears the set is ALREADY a maximally-fragmented sieve (cells ≈ points: 47/49 at N=4, 260/260 at N=8), not "fat cells." There is no progressive cell-count explosion approaching the wall — consistent with prior finding #4 (no 60/61 knee; the round function is identical each round).

**Cross-check / skeptic note:** Coordinate-order dependence is handled per the card's instruction (averaged over 30 random orders + value relabelings; std reported — small, ≈2.4 at N=4 collisions, 524 at the larger de61 set). The "cube = 1 cell" is order-independent (analytic: a full cube is contiguous in every lex order). The cells/point ≈ 1 at N=8 (260/260, std 0) confirms the collision set is a thin disconnected sieve, the opposite of a finite union of fat cells — but note this is *uniform-finiteness-style* fragmentation at the terminus, not a graded round-by-round explosion the card needs.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OM1.py` (N=8 line reads /tmp/coll_n8.txt, dumped by the verified enumerator `headline_hunt/bets/block2_wang/trails/backward_construct_n10.c` set to `#define N 8`, patched to fprintf all collisions).
