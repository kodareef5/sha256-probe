# W7-CG1 — de58 = the one live nim-heap; the wall = the heap you can't empty   ·   VERDICT: KILLED

**Card claim:** (de57,de58,de59,de60) = a 4-pile Nim disjunctive sum; de57/59/60 constant = size-0 (terminal) heaps; de58 the lone positive heap; whole-game Grundy value = de58's nimber; collision = nim-sum 0; wall = where no move zeros de58.

**Probe run:** Built the faithful mini-SHA(N) cascade de-vector (matching repo C enumerator `backward_construct_n10.c`: MSB kernel, word-pair (0,9), fill=all-ones, scaled rotations, cascade DP `da_{r+1}=0`). N=8 (M0=0x67, matches the repo) and N=10 (M0=0x34c). Computed (de57,de58,de59,de60) as modular e-diffs under (a) 40 000 generic random 4-word moves and (b) each free word varied ALONE over its full 2^N range. Throttled: yes.

**Result (numbers):**
- de-coord reachable-value counts under generic moves: **(1, 8, 1, 1)** at N=8; **(1, 16, 1, 1)** at N=10. Only de58 varies; |de58| = 8 = 2^3 and 16 = 2^4 = the pinned 2^hw(db56).
- Baseline de-vector (free4=0): **(163, 194, 142, 0)** at N=8 — i.e. de57=163, de59=142 are NONZERO constants; only de60=0.
- Which single free word moves de58: **{w57: 8, w58: 1, w59: 1, w60: 1}** — de58 is moved by **w57**, not w58; w58/w59/w60 leave it fixed.

**Kill_criterion:** "G(4-tuple) ≠ G(de58) when others=0 (sub-games not disjunctively independent — a move couples coordinates)." — **fired? yes** (and the premise itself is false before Grundy is even reached).

**Verdict reasoning:** Three independent failures. (1) **"Terminal heaps" premise false:** de57=163 and de59=142 are nonzero constants, not "size-0" heaps; only de60=0. (2) **No nimber to compute:** de58 is the image of the carry-collapsed, group-free, non-monotone w57→de58 map (prior finding #5) — there is no subtraction order, hence no Nim moves and no well-defined Grundy value; the image SIZE (2^hw=8) is a set cardinality, not a nimber (a Nim heap of that image would have top-nimber 7, ≠ 8 anyway). (3) **Heap-indexing is misattributed:** the coordinate that the live free word moves is de58, but the live word is **w57** — the round index of the heap and its controlling word disagree, so even the labeling is wrong. The nim-value does NOT derive 2^hw(db56) (it cannot — there is no game).

**Cross-check / skeptic note:** The mini-SHA independently reproduces the pinned |de58|=2^hw(db56) law (8 at N=8, 16 at N=10) and de57=de59=de60 constant, confirming the engine is faithful before the kill is read. The most generous "treat de58-image as an ordered heap" reading was tried and still fails (top-nimber V−1 ≠ size 2^hw; map is non-monotone). This is a rename/category error, not a live angle.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-CG1.py`
