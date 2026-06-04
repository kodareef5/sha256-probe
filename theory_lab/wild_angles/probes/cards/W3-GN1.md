# W3-GN1 — Collision count = an Ehrhart quasi-polynomial; odd-N-zeros = period 2   ·   VERDICT: KILLED

**Card claim:** C(N) = lattice points in a dilated cascade polytope → an Ehrhart *quasi-polynomial*; **odd N → exactly 0**, even N grow smoothly (textbook period-2 signature); the unstable 0.74-vs-1.066 fits = regressing one curve through two parity constituents; 0.74 = log₂ of the leading volume coefficient.

**Probe run:** Reused the repo's validated mini-SHA tail-collision enumerator (`backward_construct_n10.c` — its scaled rotations, cascade `find_w2`, and de61-map counter) compiled lab-side. For N=5,6,7 I enumerated **every** cascade-eligible (fill, M0) candidate (kernel = flip MSB of word 0; path 2 also flips MSB of word 9; eligibility = `da56==0`) and counted sr=60 tail collisions for each, reporting the MAX. The decisive question (per prior-finding #4): are ODD-N counts *actually* zero? Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- **N=5 (odd): MAX = 356 collisions** (fill=0x1d, M0=0x1d); 3 of 36 eligible candidates >0. **NONZERO.**
- N=6 (even): MAX = 155; 68 of 69 eligible >0.
- **N=7 (odd): MAX = 3999 collisions** (fill=0x50, M0=0x33); 23 of 127 eligible >0. **NONZERO.**
- Independent corroboration (paper Fig.2 BEST-kernel full search): odd N=5→1024, N=7→373, **N=9→14263**, N=11→2720 — all nonzero; N=9 is the global *maximum*, not a zero.
- Where "0" appears: the *first-found* candidate at every N is the trivial **fill=0** message, which yields 0 at N=5,7,9 — but that is one degenerate point in the family, not the family.
- Literal quasi-poly sub-probe: the even-N counts {N6:50, N8:260, N10:946} are only 3 points → a quadratic fits **exactly** in *both* N and 2^N (non-discriminating); the two models' N=14 extrapolations disagree by ~10× (3.75e3 vs −3.7e4), i.e. the fit is unconstrained.

**Kill_criterion:** "even-N counts fit no fixed-degree polynomial in N *and* none in 2^N" — **fired? YES (via the load-bearing parity premise).** The card's whole construction rests on "odd N → exactly 0"; that premise is **false**, so the period-2 quasi-polynomial it posits does not exist. The literal even-N fit criterion is also non-decidable as stated (3 points fit any quadratic), so it provides no support either.

**Verdict reasoning:** The headline structural claim — odd-N collision counts are *exactly zero* — is directly refuted: odd N=5 gives 356 and odd N=7 gives 3999 collisions under cascade-eligible candidates of this kernel family, and the project's own best-kernel data make every odd N nonzero (N=9 is in fact the peak at 14263). The "zeros" the card saw are an artifact of selecting the trivial fill=0 message. With odd-N ≠ 0 there is no period-2 parity decomposition, the "0.74-vs-1.066 = two constituents" story collapses, and the residual quasi-polynomial fit is vacuous (3 even-N points fit any quadratic, and the in-N vs in-2^N extrapolations disagree by 10×). This is prior-finding #4 ("N is never special; counts are real but highly non-monotonic, not parity-zero") confirmed by direct measurement.

**Cross-check / skeptic note:** Adversarial trap avoided: my own *first* run reproduced the seductive "N=5→0, N=6→50, N=7→0, N=8→258" near-period-2 pattern — but only because the auto-search returns the smallest (fill=0) eligible candidate; sweeping all eligible candidates immediately exposes nonzero odd-N maxima. A defender might argue C(N) should mean "the canonical single candidate" — but the card explicitly equates C(N) with the lattice-point count of *the* collision polytope and cites the 0.74 growth law, which is the *best/aggregate* count (nonzero at odd N), not a hand-picked degenerate fill. The collision-vs-N curve is genuinely bumpy and real; it is simply not a parity-zeroed Ehrhart quasi-polynomial. (N=9 itself was not collision-swept here — 2^27/candidate — but the paper's 14263 and the N=5,7 measurements settle the parity question.)

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-GN1.py`
