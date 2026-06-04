# W3-CR1 — Difference-CRN deficiency → derives 2^-2N as δ=2   ·   VERDICT: KILLED

**Card claim:** Model one round on a difference-pair as a CRN; Feinberg deficiency δ = n − ℓ − s; conjecture δ=2 at sr-active rounds (the two conditions g1,h) → 2^-2N = "2 codim × N bits"; δ jumps to 3 at round 61.

**Probe run:** Built the difference-CRN of the round's modular-add carry chain at N=3,4,5 (species = per-bit difference indicators d_i + carry-birth species c_i; reactions = carry-birth and XOR-flip gates, the genuine cascade nonlinearity). Assembled the stoichiometric matrix S, computed exact rational rank s, counted complexes n and linkage classes ℓ, and δ = n−ℓ−s. Did so for the sr-active round-core and for a "round-61" network with the second independent condition (h-drain) added. Pure-python exact rational linear algebra, throttled.

**Result (numbers):**
- δ(sr-active) = **0** at N=3,4,5  (e.g. N=5: n=14, ℓ=5, s=9 → δ=0)
- δ(round-61)  = **0** at N=3,4,5  (e.g. N=5: n=15, ℓ=5, s=10 → δ=0)
- Encoding-robustness (N=4): baseline δ=0; +reverse-reactions δ=0; an artificial bimolecular variant only reaches δ=1 (by inflating complexes, not via two conditions).
- Ground-truth anchor (independently re-verified here): g2 = g1+h exactly on all 946 N=10 collisions; the two conditions g1=0, h=0 are each ~2^-N → 2^-2N.

**Kill_criterion:** "δ constant/zero across rounds, or unrelated to 2^-2N." — **fired? YES (both clauses)**

**Verdict reasoning:** The honest difference-CRN of a ripple-carry chain is a near-tree of complexes and comes out **deficiency-zero** at every N, and stays δ=0 when the round-61 condition is added. δ is therefore (a) **0, not 2**, (b) **constant**, not 2→3 across the sr boundary, and (c) by the Deficiency-Zero Theorem a δ=0 network has a *unique* steady state — the structural opposite of encoding an exponential collision count or a codim-2 annihilation. "δ=2" was a coincidental number with no anchor in the real two-conditions structure. Both halves of the kill criterion fire.

**Cross-check / skeptic note:** Deficiency depends on the (modeler-chosen) reaction set, so I tested three reasonable variants; none reaches 2 by the two-conditions mechanism — the only way to nudge δ up was an artificial bimolecular complex inflation giving δ=1 (an encoding artifact, exactly the skeptic's warning that "collisions are discrete GF(2) boundary events where the CRN theorems are weakest"). To resurrect this card one would need a *canonical, non-arbitrary* difference-CRN whose δ is provably 2 at sr-active rounds and 3 at 61 and matches −log₂(rate)/N; nothing here suggests that exists.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-CR1.py`
