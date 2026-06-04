# W5-TO5 — Geometric morphism: MITM as a functor that loses faithfulness at the wall   ·   VERDICT: KILLED

**Card claim:** the cascade/MITM join is a geometric morphism Sh(B)→Sh(F); an embedding (f* full+faithful) through round 60 (each backward residue pins a unique forward continuation) that LOSES faithfulness at 61 (distinct backward states share a forward image); generic fiber size = MITM blow-up = reciprocal 2^-2N.

**Probe run:** Exact full-grid enumeration of the cascade-DP tail at N=4 (65536 tail inputs, 49 full sr=60 collisions). For each split round m=57..63, the MITM "forward image" = the path-1 forward state at the cut; the f*-fiber over it = the set of colliding tail-inputs sharing that cut-state. mean fiber = (#colliding)/(#distinct colliding cut-states). Also ran the carry-free (XOR) control. Throttled.

**Result (numbers):**
- mean f*-fiber by split round (REAL modular model): r57 = **4.455** (max 9), r58 = 1.633, r59 = 1.633, r60 = **1.000**, r61 = **1.000**, r62 = 1.000, r63 = 1.000.
- The fiber is FATTEST at the EARLIEST split (57), shrinks monotonically, reaches **size-1 (faithful) at r60 and STAYS size-1 at and past the wall** (61, 62, 63).
- 2^(2N) = 256 (the card's predicted r61 fiber); observed r61 fiber = 1.000. No blow-up.
- Carry-free (XOR) control: 0 collisions (the cascade construction has no eligible M0 / no collisions under XOR), so the control is uninformative for the card's "linear toy stays size-1" sub-claim, not confirming.

**Kill_criterion:** "fibers fat well before 61, OR grow smoothly (no faithful→unfaithful transition), OR stay size-1 past the wall." — **fired? yes (two clauses).** Fibers are fat *well before 61* (fattest at 57), AND they *stay size-1 past the wall* (r61=r62=r63=1.000). There is no faithful→unfaithful transition at 61.

**Verdict reasoning:** The card's mechanism is not merely absent but INVERTED. It predicts faithful (size-1) through 60 then an exponential blow-up at 61; the data show the exact opposite shape — information-LOSING early (fiber 4.45 at r57, because many free-word choices haven't yet been pinned), converging to perfectly faithful by r60 and remaining faithful through the schedule rounds 61-63. This is the natural reading of the cascade: the free words 57-60 are what carry the freedom, so a cut placed before they're consumed has a fat fiber; once past round 60 the colliding completion is determined. The "wall at 61" produces no fiber jump. KILLED as stated.

**Cross-check / skeptic note:** Consistent with the prior W1-IN5 finding (MITM is an upper-bound sweet-spot, not a barrier; no low→full / faithful→unfaithful transition at any frontier) and with the repo's mitm_residue results (each backward residue already pins the forward continuation through the boundary — Theorem 4 da=de). The shape is N-invariant in mechanism: the boundary proof (Thm 1-4, all-N) makes rounds 57-60 the free/cascade region and 61-63 the schedule region, so the fiber must collapse to 1 by the end of the free region regardless of N. The one honest gap: exact enumeration is only feasible at N=4 (N∈{6,7,9} have no cascade-eligible M0; the N=8 grid is 256⁴≈4.3e9, infeasible), and the XOR control is degenerate (0 collisions). Neither rescues the card — the real-model fiber is faithful precisely where the card needs a blow-up. Does TO5 add anything over W1-IN5? No: same conclusion (MITM = upper-bound geometry, not a wall), reached via fiber-size instead of communication-rank.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-TO5.py`
