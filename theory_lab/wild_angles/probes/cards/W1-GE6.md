# W1-GE6 — Configuration-space braid → multi-block = added generators   ·   VERDICT: KILLED

**Card claim:** Message words = particles on the Z/2^N circle, carries = crossings; a collision-pair is a braid whose class (writhe + permutation) obstructs single-block closure; collisions cluster at a distinguished braid class.
**Probe run:** Reconstructed the repo's reduced-width-N cascade SHA (scaled rotations, MSB kernel, fill=MASK, cascade W2=W1+casoff — matching `gap_analysis.c`) in Python. Read, per tail round 57–60, the **signed carry-difference** crossing word in the a'=T1+T2 adder; braid invariants = **writhe** (signed carry count) and **(n₊,n₋)** crossing type. Compared the **946 genuine N=10 sr=60 collisions** (from `gap_rows.csv`) against 946 random cascade-valid non-collision tuples. Throttled (~1 s).

**Result (numbers):**
- **Writhe distributions are statistically identical.** Collisions: mean **+0.14**, sd 3.02, range [−8,10]. Non-collisions: mean **+0.09**, sd 2.98, range [−8,11]. **Separation = 0.02 sd.**
- Crossing-type modes nearly coincide: collisions {(2,1):51, (2,0):48, (2,2):44}; non-collisions {(2,1):53, (2,2):52, (3,1):44}.
- corr(writhe, HW) over all 1892 pairs = **−0.027** (writhe ⊥ HW); post-round-60 mean HW also ≈ equal (14.3 vs 14.2).

**Kill_criterion:** "Dead if the braid invariant is the same on collision/non-collision pairs or is a deterministic function of HW." — **fired? yes** (first clause: same on collision vs non-collision, 0.02 sd separation).

**Verdict reasoning:** On the genuine collision population (946 real N=10 sr=60 collisions, not a proxy), the writhe and crossing-type of collision braids are indistinguishable from random non-collision braids — 0.02 standard-deviation separation, overlapping ranges, same modal classes. The braid invariant carries **no** collision signal: collisions do not cluster at a distinguished writhe/permutation class. The card's "closed braid of a distinguished class" mechanism is not realized by the cheap (writhe) invariant.

**Cross-check / skeptic note:** The card's own escalation rule is "escalate to Burau *if writhe alone separates*." Writhe does **not** separate (0.02 sd), so the trigger for the finer invariant is never met — there is nothing for Burau to refine here at the cheap level. The card's skeptic anticipated exactly this ("long random braids are invariant-saturated"): the carry-crossing braids of these 7-round tails are saturated, and the writhe is washed out. A determined defender could still compute Burau/Alexander on the full 43-adder crossing word, but with the leading invariant showing zero separation on real data, the angle is dead as stated. (Independent corroboration: this matches the repo's broader finding that collisions are not separated from non-collisions by simple signed-carry statistics — the de58/coincidence work shows the sr=61 gate is uniform/random, not class-structured.)

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W1-GE6.py`
