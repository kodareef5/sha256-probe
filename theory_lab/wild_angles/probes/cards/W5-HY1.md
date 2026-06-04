# W5-HY1 — Empty square at 61 → CAT(0) link failure, codim-2 = 2^-2N   ·   VERDICT: CONFIRMED

**Card claim:** The two sr=61 extensions (g1=0, h=0) are individually extendable but jointly unfillable = a non-flag empty square that destroys CAT(0); its codimension is exactly 2 → 2^-N per condition, 2^-2N joint, *from a codimension count not a fit*. Empty squares = 0 for rounds ≤60, jump at 61 with codim 2.

**Probe run:** Faithful replication of `gap_analysis.c` at width N=4 (exhaustive, throttled). Built the cascade cube complex on the free tail words W57..W60 using the validated repo cascade model (`_w5co_engine`, N4=49 collisions confirmed). Enumerated all 4⁴ triples, filtered to the **de61=0 stratum** (the individually-extendable edges, 65536 hits), and computed the two empty-square edges per the C's exact formulas: `g1 = w60 − sched1[60]`, `h = casoff − (sched2[60]−sched1[60])`. Cross-referenced the repo's own N=8 / N=10 numbers.

**Result (numbers):**
| N | de61=0 hits | P(g1=0) | P(h=0) | 2^-N | E[both] | obs both | indep ratio | codim | coupled |
|---|---|---|---|---|---|---|---|---|---|
| 4 (mine, exhaustive) | 65536 | 0.06250 | 0.06323 | 0.06250 | 259.0 | 259 | **1.00** | **2** | **False** |
| 8 (repo) | 16.2M | 0.003924 | 0.003931 | 0.003906 | — | — | 0.92 | 2 | False |
| 10 (repo) | 1.07B | 0.000979 | 0.000973 | 0.000977 | — | — | 1.005 | 2 | False |

Freedom census: rounds 57..60 each carry exactly one free word (find_w2 fills the square → empty-square count 0); round 61 has **zero** free words and **two** conditions (g1=0 ∧ h=0).

**Kill_criterion:** "empty squares appear before 61, OR 61's link stays flag (joint fillable / codim<2), OR codim≠2" — **fired? NO** (for the codim-2 clause).

**Verdict reasoning:** CLAUSE A (the codim-2 → 2^-2N headline) is **CONFIRMED from a count**: at N=4 the two edges are each uniform 2^-N (0.0625 = 2^-4 dead-on), the joint hits E[both]=259 vs observed 259 (independence ratio **exactly 1.00**), and `coupled=False` proves g1=0 does *not* imply h=0 — two genuine, independent codimension directions, so codim = 2 and the joint is 2^-N·2^-N = 2^-2N. This independently reproduces the repo's N=8 (0.92) / N=10 (1.005) ratios and lands precisely on the established two-conditions structure (prior finding #3: 2^-2N is genuinely rank-2). The "empty square / non-flag link" geometric language is a *faithful* re-description here — not an inverted mechanism — because the link really does fail to fill (joint codim 2), and the codim comes from a freedom-count, not a fitted slope.

**Cross-check / skeptic note:** CLAUSE B ("AT 61", flagged SUSPECT per finding #4) is the weak part. The empty square is round-61-specific *only in the trivial sense* that rounds 57..60 each carry a free word (the cascade map find_w2 is total there) while round 61 has none — a degree-of-freedom census crossing zero, **not** a frequency knee. There is no sharp per-round frequency transition at 61; consistent with the repeatedly-observed "no round-60 knee." So I credit the codim-2/2^-2N (genuine, count-based, convergent across N=4/8/10) and explicitly *do not* credit any "wall at 61" beyond "the last free word runs out there." The strongest version of this card is the codim-2; the round-specific dressing adds nothing the freedom-count didn't already say.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HY1.py`
