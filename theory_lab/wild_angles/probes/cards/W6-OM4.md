# W6-OM4 — de58 = the unique open 1-cell; de57/59/60 = 0-cells   ·   VERDICT: KILLED

**Card claim:** a graded cell decomposition where de58 is the unique OPEN 1-cell (the family's single free-parameter axis, in the *modular* chart) and de57/de59/de60 are 0-cells (points) — making OM2 mechanistic and explaining *why* de58 is special.

**Probe run:** N=4..32 (throttled). (1) Cell structure from the repo's authoritative de-set measurement (shabridge.DE_SIZES). (2) Independent re-derivation of |de58| via the full validated cascade (sweep w57, find_w2 each round, modular e-diff after round 58) at N=4,8. (3) The decisive GROWTH-MATCH: fresh MSB-kernel sr=60 collision counts (N=4 exact = 49; N=8/10 verified = 260/1833) combined with pinned |de58|, computing the de58 mass-share = log₂|de58| / log₂(#collisions) and the normalized slope s=log₂|de58|/N vs 0.74.

**Result (numbers):**
- **Cell structure (pinned):** de57 = de59 = de60 = **1 at every N** (4..32) — exactly one varying coordinate, de58. KILL(a) does not fire, but this is a *restate* of measured data.
- **Re-derivation:** |de58| (full cascade, modular) = **2 at N=4, 8 at N=8**, both = 2^{hw(db56)} — the law re-derives (Maj/AND image-count, finding #5).
- **Growth-match:** de58 mass-share = **0.178 (N=4) → 0.374 (N=8) → 0.369 (N=10)**, spread 0.196 → **NOT STABLE**. s/0.74 = **0.338, 0.507, 0.541** (range 0.34–0.54, never 1.0).

**Kill_criterion:** "a SECOND de-coordinate varies at large N (>1 cell), OR slope(|de58|) unrelated to the count exponent." — **fired? yes (clause 2).**

**Verdict reasoning:** KILLED on the card's own load-bearing test. Clause 1 does not fire — only de58 varies (de57/59/60≡1), which is genuinely a one-varying-coordinate picture — but per the card's skeptic and prior finding #5 that is *a restate of known data, not new content*, and re-deriving |de58|=2^{hw(db56)} (which the probe does confirm) is explicitly NOT a CONFIRMED. The decisive new content — de58's share = s/0.74 "the normalized dimension of the algebraic part" — requires a STABLE share, and it is not stable: the mass-share swings 0.18→0.37 and s/0.74 wanders 0.34–0.54. The reason is structural: |de58|=2^{hw(db56)} is **non-monotone in N** (hw of a carry-difference; finding #5), so it cannot carry a fixed slope, hence cannot be a dimension. Clause 2 (slope of |de58| unrelated to the count exponent) fires.

**Cross-check / skeptic note:** The cell structure (de57/59/60=1, de58 varies) and |de58|=2^{hw(db56)} are cross-checked two ways: the pinned DE_SIZES table and an independent full-cascade re-derivation (2,8 at N=4,8 — note the MODULAR e-difference is required; XOR gives the wrong, inflated count). The growth-match uses the *measured* exponent, not the assumed 0.74; even against the canonical 0.673 the share is unstable (0.371–0.594). So this is a correct re-description of a closed thread plus a failed quantitative prediction — a rename, not a derivation.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OM4.py`
