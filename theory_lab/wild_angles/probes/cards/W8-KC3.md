# W8-KC3 — Solution-set freezing -> 132 = frozen variables, 0.74 = cluster entropy   ·   VERDICT: KILLED

**Card claim:** The collision solution set is a d1RSB-frozen cluster; the repo's "132 universal bits" ARE the frozen variables; the 88 free bits carry cluster entropy 0.74N; sr=61 is the freezing/shattering threshold.

**Probe run:** Enumerated the full N=8 collision set (260 collisions) lab-side via `/tmp/bc_dump` — a verbatim copy of the repo's `headline_hunt/bets/block2_wang/trails/backward_construct_n10.c` (cross-validated 260/260, independently verified 260/260, M0=0x67). Took the solution coordinates = free words (w57,w58,w59,w60) = 4N = 32 bits. Measured per-bit frequency (frozen = 0%/100%), frozen-fraction, cluster-entropy log2(#colls)/N, frozen-bit location, and single-bit flip-distance Hamming clustering. N=8, throttled.

**Result (numbers):**
- **Frozen bits = 0 / 32 → frozen-fraction = 0.000** (vs claimed 132/256 = 0.516). Every solution-coordinate bit varies; P(=1) ranges 0.315–0.708, mostly ≈0.50. NOT a single frozen bit.
- **Cluster entropy log2(260)/8 = 1.003**, |diff from 0.74| = 0.263 (>>0.10). The "0.74" does not appear.
- Frozen-bit location: 0 in every word (W57/58/59/60) — "frozen = late-round W59/W60" is vacuously false.
- Hamming flip-dist-1 clustering: **257 components** for 260 solutions (largest cluster size 2). Solutions are nearly all isolated — the opposite of one frozen mega-cluster.

**Kill_criterion:** "frozen-fraction ∉[0.45,0.58], or 0.74 off by >0.1, or frozen bits not the late-round set" — **fired? YES (all three).**

**Verdict reasoning:** All three independent kill conditions fire. The card commits the category error flagged in prior finding #1: the repo's "132 universal bits" are OUTPUT-difference bits (registers a,b,e,f @ round 63 = 4N+4), measured across kernels — NOT input/solution-coordinate frozen variables within one cluster. When you actually enumerate the within-cluster solution set and census its coordinates, the frozen set is EMPTY (0/32) and the entropy is ~1.0 bit/word, not 0.74. The 0.74 constant is dead (prior finding #2). The solution set is not a frozen d1RSB cluster — it is a scattered set (257 singleton-ish components).

**Cross-check / skeptic note:** The enumerator is the repo's own, ground-truth-verified at 260 (matches `_w5co_engine` self-test target). Could the freezing live at a coarser flip-distance? Even dist≤2 gives 255 components — no mega-cluster emerges, so the "single cluster freezing" picture fails at the cheapest honest test. One caveat: "frozen" could be redefined over OUTPUT bits, but that just restates the known 132 census (a category swap, not a confirmation) and still isn't 0.74-sharp. N=8 is the card's own requested regime (260 colls), so this is not an N-too-small artifact.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W8-KC3.py` (after building/running `/tmp/bc_dump` from the repo C enumerator with N=8 to regenerate `/tmp/colls_n8.csv`).
