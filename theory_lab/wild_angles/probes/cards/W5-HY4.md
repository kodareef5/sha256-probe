# W5-HY4 — Cascade diagonal = CAT(0) geodesic; the wall = geodesic non-existence   ·   VERDICT: SURVIVES

**Card claim:** Theorem-1's da=0 diagonal IS the unique normal-cube-path geodesic through a *flat* 4-cube of the commuting free rounds 57..60 (CAT(0) ⇒ unique geodesics, *why* the cascade works to 60); at 61 the two required hyperplanes don't co-bound a cube → no geodesic continuation. Dual to HY1.

**Probe run:** N=4,5,6 (throttled). (1) Encoded the four free rounds 57..60 as message-word injection directions into the difference state, transported through the XOR-linearized round operator (`linround`), and measured the dimension of their combined span (flat 4-cube ⟺ span = 4N) plus pairwise commutation. (2) Confirmed the cascade map `find_w2` is single-valued / deterministic (unique descent) over sampled paths at N=4,5. (3) Over the de61=0 stratum at N=4 (exhaustive, exact `gap_analysis.c` g1/h), tested whether {g1=0} and {h=0} are the same event (a co-bounding cube, codim 1) or distinct (empty square, codim 2).

**Result (numbers):**
- Flat 4-cube: span dim = **4N exactly** (16/16 @N4, 20/20 @N5, 24/24 @N6); **6/6** pairs independent at every N.
- Cascade descent: unique=True, deterministic over 64 sampled paths (N=4 and N=5).
- Round-61 co-bounding: 65536 de61=0 hits; g1=0 in 4096, h=0 in 4144, both in 259; **same_event = False** → no co-bounding cube → empty square.

**Kill_criterion:** "free rounds not pairwise-commuting, OR cascade non-unique at ≤60, OR the 61-move finds a co-bounding cube" — **fired? NO** (commute ✓, unique ✓, no co-bounding cube ✓).

**Verdict reasoning:** Every clause of the kill criterion is *negated*: the free rounds form a flat 4-cube (span = 4N, all pairs commute), the cascade descent is unique, and at 61 the two conditions do not co-bound (same_event=False, dual to HY1's codim-2). So the angle SURVIVES and the directionality is correct (commutation holds 57→60, fails at 61 — not backwards, cf. finding #5). **But I withhold CONFIRMED because this is a reframe (`mech: reframe`) that adds no independent number.** The "flat 4-cube" is the near-trivial fact that there are four free words entering four distinct shift-register slots (independent injection directions ⇒ span 4N automatically in the linear model); the only load-bearing quantity, the codim-2 non-co-bounding at 61, is exactly HY1's result re-described in cube-complex vocabulary. A rename is not a CONFIRMED.

**Cross-check / skeptic note:** The flat-cube test is in the XOR-linearized (carry-free) model, so it certifies the *linear skeleton* commutes, not the full nonlinear round — but that is the right model for "do the free-word hyperplanes co-bound," and it agrees with the exact nonlinear cascade being deterministic to 60. The genuine content (codim-2 at 61) is independently and more rigorously established in HY1 over the exact nonlinear stratum (N=4 ratio 1.00; repo N=8/10: 0.92/1.005). If anything HY4 *corroborates* HY1 from the geodesic side; it does not stand on its own number.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HY4.py`
