# W3-IE2 — de58 = the unique uniquely-ergodic IET coordinate   ·   VERDICT: KILLED

**Card claim:** an IET splits into minimal (growing) + periodic (constant) components; de57/59/60 constant = periodic Rauzy components; de58 = the lone minimal component whose Rokhlin-tower height grows with N, matching the |de58| table.

**Probe run:** Tested against `shabridge.DE_SIZES` (the pinned, NT3-confirmed ground truth) at N=4..32. (1) Confirmed the 3-constant + 1-growing component count. (2) Built an IET Rokhlin-tower-height model (CF-convergent return times of the Σ rotation numbers) and asked whether it *derives* the exact log2|de58| = hw(db56) sequence. (3) Argued the provenance of 2^hw(db56). Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- Structure: de57 = de59 = de60 = 1 for all 10 N; de58 > 1 — **3 periodic + 1 minimal confirmed**.
- Actual law: log2|de58| = hw(db56) = **[1,3,3,4,5,9,5,5,8,10]** for N=[4,6,8,10,11,12,13,14,16,32]; first diffs [2,0,1,1,4,**−4**,0,3,2] → **NON-monotone** (spike to 9 @N=12, **drops to 5** @N=13,14).
- IET tower-height model: predictive error **MAE = 1.88 bits**; reproduces the N=12 spike? **No**; reproduces the N=13 drop? **No** → captures neither decisive feature (loose corr 0.71 is spurious on 8 points).

**Kill_criterion:** "induction predicts 0/2/4 periodic, OR wrong growth form" — **fired? YES (wrong growth form)**

**Verdict reasoning:** The IET framing reproduces the *component count* (3 constant + 1 growing), but the card's own skeptic already concedes that's plain linear algebra (3 linearly-determined de-coords, 1 nonlinear) — it earns the IET lens nothing. The decisive test is the growth *law*. A Rokhlin tower height is a return time under Rauzy–Veech induction; return times are monotone non-decreasing in renormalization depth and **cannot drop**. The real log2|de58| = hw(db56) is non-monotone (9 at N=12, 5 at N=13/14), so no genuine IET tower height can produce it (MAE 1.88 bits; misses spike+drop). Per prior finding #5, the framing **RESTATES de58's uniqueness; it does not DERIVE 2^hw(db56)**.

**Cross-check / skeptic note:** 2^hw(db56) is independently established (NT3) as a Maj/AND differential image-count on db56 = b56₁⊕b56₂ — an algebraic property of *one* cascade-eligible message-pair's bit pattern, with no N-indexed ergodic return-time reading; the law carry-collapses (1024 < 2^17) at N=32, another non-ergodic signature. Skeptic on my own probe: the CF-denominator proxy is not a faithful RV induction (its wobble comes from off % N changing, not a true return time); I therefore judged on *predictive accuracy of the exact sequence + the two decisive features*, not the proxy's accidental wobble — and on that honest bar it fails. A loose corr of 0.71 on 8 points is not derivation.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-IE2.py`
