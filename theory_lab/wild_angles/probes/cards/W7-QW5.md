# W7-QW5 — Hitting-time-exponent map: step at r=58 + cliff at 60→61   ·   VERDICT: SURVIVES

**Card claim:** α(r) = ½(−log₂δ(r) − log₂ε(r))/N is flat 57–59 (de57/59 constant → ε constant), has a **step at 58** (de58 opens 2^hw(db56) configs → ε spikes) of height tracking log₂|de58|/N, and a **cliff at 60→61** (δ collapses) — unifying de58-growth + single-DOF + the wall in one scalar.

**Probe run:** N=8,10,12,14. Built α(r) for r=57..61 from the pinned, repo-verified de-set sizes (ε(r)=|de_r|/2^N: de57=de59=de60=1, de58=2^hw(db56)) and a flat δ that collapses to the measured 2^-2N at r=61 (the QW1 wall). Tested: (1) flatness at 57/59/60, (2) step magnitude at 58 vs ½log₂|de58|/N, (3) cliff at 61, (4) whether the step is *derived* or *plugged in*. Throttled yes.

**Result (numbers):**
- **Flat at 57/59/60** (α = 0.5500 for all three at N=10) — yes, by de=1.
- **Step at r=58**, magnitude **exactly ½log₂|de58|/N**: −0.1875 (N=8, |de58|=8), −0.2000 (N=10, 16), −0.3750 (N=12, 512), −0.1786 (N=14, 32). It steps *down* (larger ε → lower hitting exponent); magnitude matches the prediction to machine precision and scales with |de58|.
- **Cliff at 60→61**: α₆₀=0.5500 → α₆₁=**1.500** (jump 0.95), driven by δ: 0.5→2^-2N. (α₆₁=1.5 = ½·(2N)/N = the rank-2 wall in α-units.)
- **Derivation test:** the step height is, by construction, just log₂|de58|/N — the *known* census 2^hw(db56) inserted into ε. The Szegedy √/product add **no independent derivation**; any monotone f(δ,ε) with ε∝|de_r| gives the identical step.

**Kill_criterion:** "α smooth/monotone (no step at 58, no cliff at 61), or the step doesn't scale with |de58|." — **fired? no** (the step and cliff are present and the step scales exactly with |de58|).

**Verdict reasoning:** The literal kill_criterion does NOT fire — α(r) is non-monotone with a genuine step at 58 (scaling with |de58|) and a cliff at 61, so the scalar does fuse the three known facts. But per prior-#5 it earns CONFIRMED only if the hitting-time form *derives* 2^hw(db56) with new content, and it does not: it restates the de58 census in α-units (the card's own skeptic clause — "if any monotone combo of δ,ε works as well, it's a relabel" — is satisfied). So it is consistent and a tidy unification, but not a positive confirmation of new structure → SURVIVES, not CONFIRMED.

**Cross-check / skeptic note:** Every ingredient is independently solid (de58 law VERIFIED ≤N=14; the 2^-2N wall confirmed in QW1), so α(r) is a faithful re-encoding — its value is pedagogical/organizational, not derivational. To promote to CONFIRMED one would need the Szegedy hitting-time *form itself* to predict 2^hw(db56) (the carry-collapse count) from gap+density without inputting |de58| — which this probe shows it cannot. The signed step (down, not up) is a presentation detail; magnitude and scaling are exact.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-QW5.py`
