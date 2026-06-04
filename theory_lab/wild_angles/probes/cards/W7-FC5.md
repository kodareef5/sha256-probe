# W7-FC5 — Arrow relations → localize the wall to one (object,attribute) cell   ·   VERDICT: KILLED

**Card claim:** FCA arrow relations (↓↑↕) mark the irreducible "load-bearing absences"; they CONCENTRATE on the W[60]-schedule-match / dT1_61=0 column at near-collision objects — the fingerprint of "the 7-round problem collapses to ONE equation"; double-arrow count tracks the 24-bit residue (~2^-N).

**Probe run:** N=8, N=10 (N=6 has no cascade kernel), throttled. Built the formal context with attributes {de61=0, de62=0, de63=0, dT1_61=0, W[60]-match=(g1=0)} over free-word objects, clarified+reduced, and computed the down/up/double arrow tables, reporting per-column double-arrow totals and the share on the conjectured target columns {dT1_61, Wmatch}. Ran twice: (1) mixed sampling with near-collision bias; (2) a hard near-collision pass keeping only the 600 lowest-output-Hamming-weight objects (min outHW=9).

**Result (numbers):** Double-arrows are **uniform across all columns**, with no concentration:

| N | double-arrows per column (de61, de62, de63, dT1_61, Wmatch) | target share |
|---|---|---|
| 8 (mixed) | 3, 3, 3, 3, 3 | 6/15 = **0.40** |
| 10 (mixed) | 2, 2, 0, 2, 2 | 4/8 = **0.50** |
| 8 (hard near-collision, min HW=9) | 3, 3, 3, 3, 3 | 6/15 = **0.40** |
| 10 (hard near-collision) | 1, 1, 1, 1, 1 | 2/5 = **0.40** |

- Every column receives the *same* double-arrow count; the "target share" (0.40–0.50) is just the fraction of columns that are targets (2 of 5), i.e. proportional, not concentrated.
- The clarified context collapses 3000–6000 objects to only **2–5 distinct rows** — the five attributes are so sparse (densities 0–8) and mutually correlated that the reduced context has essentially no structure for arrows to localize onto.

**Kill_criterion:** "arrows spread uniformly over all columns (no localization)" — **fired? YES.** Double-arrows are flat across {de61, de62, de63, dT1_61, Wmatch} under both ordinary and hard near-collision sampling; the dT1_61/Wmatch columns get no more than the others.

**Verdict reasoning:** The conjectured FCA fingerprint — double-arrows piling on the W[60]-schedule-match / dT1_61=0 cell at HW-1 near-collision objects — does not appear. The arrow distribution is uniform across all five tail attributes, so the irreducible "load-bearing absences" are not localized to one (object,attribute) cell; the wall does not show up as a single arrow-marked column. The card's own skeptic worry (arrows live on the reduced context and are sample-sensitive) is the proximate cause: oversampling near-collisions even hard (min output HW=9) only shrinks the clarified context to 2–5 rows with a flat arrow table — there is no concentration to find, because at the per-round-scalar granularity all five tail conditions are roughly interchangeable rare events. This matches prior finding #4: the "7 rounds collapse to one equation" intuition is real at the level of DOF counting (sr=61 is one extra schedule condition), but it does not manifest as a localized FCA arrow structure singling out the schedule column.

**Cross-check / skeptic note:** Robust across sampling regimes (mixed vs. hard near-collision) and both N — the uniformity is not a sampling fluke. No 2^-N double-arrow count on the target column emerged; the per-column counts are O(few) and equal, set by the tiny clarified context, not by a 24-bit residue. Converges with FC1/FC2/FC3 in this wave: the FCA invariants (meet-irreducibles, concept count, implication base, arrows) all either rename known facts or fail to localize the wall; none produces a NEW localized object or number. To CONFIRM I would have needed double-arrows concentrated on {dT1_61, Wmatch} (target share → 1.0) with a ~2^-N count on HW-1 objects; instead the share is exactly the column-count proportion (0.40) and the table is flat.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-FC5.py`
