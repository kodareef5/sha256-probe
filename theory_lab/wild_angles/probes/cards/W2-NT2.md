# W2-NT2 — Weil square-root cancellation → origin of the 132 / HW~74 plateau   ·   VERDICT: KILLED

**Card claim:** Each output bit's bias is a Kloosterman/Salié-type sum S(a,b) = Σ_x e^{2πi(ax + b·σ1(x))/2^N}; Weil bounds give |S| ≤ C·2^{N/2} for non-degenerate frequencies and full 2^N only on a thin degenerate set. The # degenerate directions = soft/biasable bits (~124); the √-cancelling directions = hard-core bits pinned near ½ (~132). Cancelling fraction should ≈ 132/256, and swapping SHR10→SHR9 should shift the plateau.

**Probe run:** N=8, exact, throttled. Computed |S(a,b)| for **all** 65536 = (2^8)² frequency pairs (σ1 = scaled-rotation SHR), classified degenerate (|S| ≥ 0.75·2^N) vs √-cancelling (|S| ≤ 2·2^{N/2}=32), measured histogram bimodality, and re-ran the classification under SHR ∈ {1,2,3} to test the predicted plateau shift.

**Result (numbers):**
- max|S| = 256 = 2^N (the single trivial a=b=0 direction); min 0; mean 11.7 (≈ 2^{N/2}/1.4).
- **Degenerate count = 1** (not ~124). **Cancelling fraction = 0.947** (62071/65536), not 132/256 = 0.516 — off by 0.43. canc_frac·256 = 242.5, nowhere near 132.
- **Histogram is a smooth unimodal decay**: bin0=24485, bin2=11120, bin4=2766, … tapering monotonically to 0 by bin18. **No valley, no second mode** → not bimodal.
- **SHR swap is inert:** cancelling fraction = 0.938 / 0.947 / 0.942 for SHR = 1 / 2 / 3. The predicted "plateau shift" does not appear; the fraction is essentially SHR-invariant.

**Kill_criterion:** "Dead if |S| is a smooth continuum (no clean bimodal Weil dichotomy)." — **fired? yes.**

**Verdict reasoning:** The character sums show *no* bimodal Weil dichotomy — there is one degenerate direction (the trivial frequency) and a smooth continuum of √-cancelling-and-below magnitudes, exactly the kill condition. The cancelling fraction (0.947) misses 132/256 by 0.43, and the SHR swap fails to move it, so the card's mechanism is falsified on its own terms. Weapon #1 lands cleanly: even if the fraction had grazed 0.516 it would be a numerical coincidence, because 132 is a per-output-bit deterministic-control *census* over 256 bits (registers a,b,e,f fully uncontrolled at round 63 = 128, +4 scattered dc — a carry-nonlinearity census per `writeups/hard_core_132_bits.md`), whereas this object is a per-frequency-pair cancellation count over 65536 pairs. The units do not match; the 132 plateau is not a Weil-degenerate-direction dimension.

**Cross-check / skeptic note:** The single degenerate direction at a=b=0 is the expected trivial full sum, confirming the computation. The skeptic line in the card itself anticipates this ("132 ≈ entropic, nothing arithmetic") — and indeed the smooth continuum is consistent with a single-round single-bit sum being the *wrong object* (carries couple all bits). What could revive it: a genuine bimodal split of the SAME 256 output bits into 132 √-cancelling vs 124 degenerate under a per-output-bit complete sum that includes the full round (Ch/Maj + carry), which this single-σ1 sum does not capture — but that is a different, much larger probe and there is no evidence here that it would land on 132.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-NT2.py`
