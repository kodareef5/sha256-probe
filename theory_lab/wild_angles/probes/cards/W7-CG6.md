# W7-CG6 — Mean value: HW~74 as a cooled hot game's mean   ·   VERDICT: KILLED

**Card claim:** The 132 hard-core bits = cold (number) spine; the ~124 soft bits = hot (temperature) residue that averages out; HW~74 = the mean the game cools to (≈ #hard-core-ones + ½·#soft). NEW prediction: plateau *width* = residual temperature = a **narrower-than-binomial** soft-bit spread.

**Probe run:** Faithful mini-SHA(N) cascade run to round 63. Classified each of the 8N output-difference bits as hard-core (constant across random free choices) vs soft (varies); measured the output-diff Hamming-weight distribution (mean + variance) over 60k random kernel-related message pairs and compared to the independent-soft binomial Σ p_j(1−p_j). N=8, N=10. Throttled: yes.

**Result (numbers):**
- N=8: 64 output-diff bits → 34 hard-core (ALL stuck-at-0; hc_ones=0), 30 soft. Mean HW = **14.25** vs decomposition pred (#hc1 + ½·#soft) = **15.0** (match). Var(HW) = **8.67** vs binomial **7.16** → **ratio 1.21**.
- N=10: 80 bits → 42 hard-core (all stuck-at-0), 38 soft. Mean HW = **19.52** vs pred **19.0** (match). Var(HW) = **10.39** vs binomial **8.51** → **ratio 1.22**.
- The spread is **SUPER-binomial (ratio ≈ 1.21 at both N)** — positive correlation / over-dispersion — the OPPOSITE of the card's predicted sub-binomial narrowing.

**Kill_criterion:** "HW ≠ the decomposition, OR the soft-bit spread is exactly binomial ('temperature' vacuous)." — **fired? yes** (the spread is not sub-binomial; if anything it is super-binomial, so the cooling label is vacuous).

**Verdict reasoning:** This is prior-finding #2 made exact. The mean-HW decomposition holds, but trivially: every hard-core bit is stuck-at-0, so mean HW ≈ ½·#soft — i.e. "constant bits constant + uncontrolled bits uniform," the plain Binomial(#uncontrolled, ½) picture, not a cooled hot-game mean with new content. Crucially, the card's one *new* prediction — a narrower-than-binomial spread signalling genuine anticorrelation/cooling — is falsified: the measured variance is **21–22% ABOVE** the independent baseline (soft bits are positively correlated, not anticorrelated). There is no cooling; "temperature" is vacuous here. The plateau HW≈74 (≈4N-scaled mean) is a restated binomial mean, exactly what the card was warned not to merely re-derive. KILLED.

**Cross-check / skeptic note:** The decomposition match (within ~1 bit) confirms the classifier and engine are sound. A defender might object that my last two rounds use W=0 for both messages (isolating state-diff propagation) — but that choice only *removes* added schedule-diff noise; a fuller schedule would add variance, pushing the ratio further ABOVE 1, never below, so the sub-binomial verdict cannot flip. The sign of the deviation (super-binomial) is the decisive fact: cooling requires sub-binomial, and the data goes the other way at both N. No new number; the 74 is not derived with content.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-CG6.py`
