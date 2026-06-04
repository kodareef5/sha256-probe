# W2-NT3 — Weyl equidistribution of {σ1(W)/2^N} → why de58 grows   ·   VERDICT: KILLED

**Card claim:** Each de_r is a Weyl sum of the schedule orbit; de58 grows because the σ1-SHR10 coordinate is lacunary ({2^k θ}) and its Weyl sum doesn't cancel, so its difference set grows with N — while de57/59/60 equidistribute (→ constant). The de58 round should be the *worst-equidistributed* round, with discrepancy slope matching the |de58| slope within 20%.

**Probe run:** N=4,8,10 (N=6 has no cascade-eligible M0 under the all-ones fill, skipped), exact, throttled. Built the scaled-rotation mini-SHA (MSB kernel, auto-M0, fill=all-ones — same recipe as `gap_analysis.c`), reconstructed the cascade, and enumerated the de57..de60 difference SETS over the da57=0-preserving tail freedoms. Computed db56 (=b-register XOR difference at round 56), hw(db56), and the star-discrepancy of the σ1 fractional-part orbit {σ1(W)/2^N}.

**Result (numbers):**
- |de| = (1,2,1,1) @N=4, (1,8,1,1) @N=8, (1,16,1,1) @N=10 — **exactly** matches repo `DE_SIZES`.
- |de58| = 2^hw(db56) at **every** N (hw(db56) = 1,3,4 → 2,8,16). The Maj-image law holds exactly.
- de57 = de59 = de60 = 1 at every N (only de58 grows). ✓
- σ1 orbit star-discrepancy = 0.5625 (N=4), 0.0117 (N=8), 0.0049 (N=10) — it **SHRINKS** with N, slope d(disc)/dN = −0.099. The σ1 orbit is *increasingly* equidistributed, the OPPOSITE of "lacunary / doesn't cancel."
- Measured d(log2|de58|)/dN = 0.500 = d(hw(db56))/dN = 0.500. The growth law is hw(db56), not σ1 discrepancy.

**Kill_criterion:** "Dead if de58 isn't the worst-equidistributed round, or its discrepancy slope misses the measured |de58| slope by >20%." — **fired? yes.**

**Verdict reasoning:** Two independent kills. (1) σ1 is the *same* function at every schedule position, so its orbit discrepancy is a single number per N — it is identical for the de57, de58, de59 and de60 rounds and therefore *cannot single out de58* as the worst-equidistributed round (the card's central mechanism is undefined). (2) The actual growth law |de58| = 2^hw(db56) is reproduced exactly here and is a Maj/AND-image count governed by db56's bit pattern; the σ1 discrepancy does the opposite of what the card needs (it decreases toward equidistribution as N grows), so its "slope" cannot track the +0.5/N growth of log2|de58|. The σ1-lacunary story is the wrong object: de58 grows by a carry/Maj-image mechanism on db56, not by failure of fractional-part equidistribution.

**Cross-check / skeptic note:** The de-set sizes match the pinned ground truth `sb.DE_SIZES` at all three N exactly, so the enumeration is trustworthy. One could argue the card means a *2-D* (pairwise) discrepancy of the schedule orbit, but the skeptic line in the card itself concedes this "dissolves the story," and no 2-D object recovers the precise 2^hw(db56) law — only the Maj-image count does. The N=6 skip doesn't affect the verdict (N=4/8/10 already span the law).

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-NT3.py`
