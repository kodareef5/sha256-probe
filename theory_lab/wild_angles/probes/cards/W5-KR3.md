# W5-KR3 — Aperiodicity threshold: star-free below 60, group-bearing at 61   ·   VERDICT: KILLED

**Card claim:** The da=0-preserving language is star-free / FO-definable (aperiodic syntactic monoid) for r<=60 and becomes group-bearing at r=61; a clean True->False aperiodicity flip at 60->61 explains why local/linearized methods plateau at 60.

**Probe run:** N=2,3 (throttled, `OMP_NUM_THREADS=2 taskpolicy -b`). For each round r=57..61 and 4 random conditioning "base states", built the transition monoid of one SHA round on the differential-head automaton (state = head (da,de); letters = all 2^N message words; cascade regime msgdiff=0), closed it under composition, and tested aperiodicity by detecting any element with functional period > 1 (a group element). The round OPERATION is identical for all r; only k = K[r]&mask changes.

**Result (numbers):**
- N=2: aperiodicity verdict per base = `[False, False, False, True]` — **byte-identical for every r in 57..61** (monoid sizes |M|~[5,4,5,5], head states ~[9,8,9,7] also identical across r).
- N=3: aperiodicity verdict per base = `[False, True, False, False]` — **byte-identical for every r in 57..61** (|M|~[7,7,10,49], states~[15,11,15,24]).
- There is NO 60->61 transition: r=57 already shows group-bearing monoids on some base states, and the set of group-bearing bases does not change with the round index.

**Kill_criterion:** "non-aperiodic at r<=58, OR still aperiodic at 61, OR flickers per-message." — **fired? YES** (two independent ways).

**Verdict reasoning:** The kill fires twice. (1) Group-bearing monoids already appear at r=57 (<=58) — there is no star-free-below-60 regime. (2) The verdict FLICKERS per conditioning base state (`[False,...,True]`), exactly the "flickers per-message" disqualifier; whether the monoid is aperiodic is decided by the conditioning state, not the round. Decisively, the aperiodicity outcome is independent of the round index r (the K[r] constant) — every column r=57..61 is identical — because the round function is the same map each round and an additive constant inside the adder cannot inject a round-specific cyclic subgroup. This is exactly prior finding #4: no round-60 knee; "star-free below 60, group at 61" is not a real round-localized property.

**Cross-check / skeptic note:** A skeptic could argue the head-completion (out-of-set images fixed to themselves) could mask a group; but completion can only ADD fixed points, never destroy a recurrent permutation, so any genuine nontrivial period would still be detected — and indeed some bases DO show periods (group elements), they just appear identically at every round. The per-base flicker is itself the signal that this "language" has no presentation-independent aperiodicity at the round granularity the card needs. Convergence with W5-KR1 (group element appears at r=55, not 61) corroborates: group structure is round-invariant, not localized to the wall.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-KR3.py`
