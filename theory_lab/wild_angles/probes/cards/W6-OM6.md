# W6-OM6 — 1-D monotonicity → de58 membership: intervals (tame) vs fractal (wild)   ·   VERDICT: KILLED   [screening]

**Card claim:** along the de58 axis, the set of values completing to a collision is a finite union of INTERVALS (tame) for rounds ≤60 and a pseudo-random SIEVE (wild) at round 61; the sieve's entropy = the HW~74/132 plateau. "The sharpest 1-D o-minimality test."

**Probe run:** N=4,5 exact (throttled) + N=8 corroboration. w57 is the de58 1-cell coordinate (de58 is computable from w57 alone — cascade_structure_complete.md). Built the membership indicator s[w57]=1 iff ∃(w58,w59,w60) achieving the round-r condition, for r=61 (de61=0) and r=63 (full collision), exhaustively over the remaining words; measured density, maximal-run (interval) count, order-1/3 block entropy, and LZ78 size. N=8: projected the 260 verified collisions onto the w57 axis (length 256) and measured the same.

**Result (numbers):**
- **N=4:** r61 membership = `1111111111111111` (all-1, **1 interval, H1 = 0**, perfectly TAME). r63 = `1110011101100111` (density 0.688, 7 runs, 4 one-blocks, **H1 = 0.896**, sieve-like).
- **N=5:** r61 = all-1 (tame). r63 = all-0 (MSB kernel has no collisions at N=5; the family uses an ALT fill there).
- **N=8 (260 collisions on the w57 axis):** r63 membership density 0.594, **134 runs, 67 intervals, H1 = 0.974, H3 = 0.965**. r61 membership again all-1 structurally (entropy 0, tame).

**Kill_criterion:** "entropy already ≈1 bit/symbol for r≤58, OR run-count never breaks at 61." — **fired? yes (no break at 61).**

**Verdict reasoning:** KILLED (screening-strength). The card places the tame→wild break at round **61**, but the round-61 membership (de61=0) is **perfectly tame at every N — all-1s, one interval, entropy 0** (the free cascade always admits a de61=0 completion). The high-entropy sieve (H1 ≈ 0.97 at N=8) appears only at round **63**, the full-collision terminus — not at the claimed wall. So "run-count never breaks at 61" fires: nothing happens at 61; the sieve is at the terminus, which the boundary proof already characterizes as a finite-chain residue, not a fractal phase transition. The o-minimal dichotomy (tame intervals ≤60, wild sieve at 61) is not exhibited — below-and-at the wall it is trivially tame, and the apparent wildness is a measure-0 terminal sieve.

**Cross-check / skeptic note:** The skeptic's caveat (need N≥12; an LFSR-like sieve looks random yet is tame) is the reason this is *screening* not a deep kill — at N=4 the r63 string is only 16 bits (interval-vs-sieve is fragile), so the decisive evidence is (a) the structural all-1 tameness of the r61 wall at every N including N=8, and (b) the N=8 r63 projection over 256 points showing near-maximal entropy (0.974) only at the terminus. High r63 entropy alone does not prove "wild" (could be a tame pseudo-random sieve), but it certainly is not the *interval* structure the card predicts below the wall, and crucially the wall (61) shows zero entropy. Confirm-direction was OM1 (also KILLED): cube=1 cell ≤60, fragmented sieve only at the terminus — consistent.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OM6.py` (N=8 reads /tmp/coll_n8.txt from the verified enumerator at `#define N 8`).
