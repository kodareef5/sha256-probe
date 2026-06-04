# W4-FP4 — Free entropy → 2^-2N as a free large-deviation rate, factor-2 = two free constraints   ·   VERDICT: KILLED

**Card claim:** Voiculescu free entropy χ = the LDP rate for atypical product spectra; extending a collision one round forces one more contracted axis; factor-2 = two *free* spectral constraints each costing one unit. Probe: χ via the logarithmic-energy double sum ∬log|s−t|dμdμ at depths 57..61; is Δχ constant for 57/59/60, jumping at de58, scaling like 2N?

**Probe run:** (1) Ground-truth two-conditions from the repo gap data (N=10, 946 collisions). (2) The card's χ probe: log-energy χ=(1/n²)Σ_{i≠j}log|s_i−s_j| of the depth-k tail-round difference-Jacobian product (depths 1..5 = de57..de61 cross-sections), averaged over 8 base points, N=4,6, throttled. (3) Adjudicate rename-vs-mechanism.

**Result (numbers):**
- (1) **g2 = g1 + h (mod 2^N) holds 946/946** — the rank-2 / codim-2 fact. Independence at the estimable resolution: P(g1 even)=0.501, P(h even)=0.518, P(both even)=0.260 = exactly the product 0.260. (The naive full MI=8.36 bits is finite-sample-saturated, n=946<2^N=1024, and is *not* real dependence; real independence is the repo's 1.005 ratio over ~10⁹ samples.) So sr61 = (g1=0)∧(h=0) = two independent N-bit conditions → 2^-2N. The factor-2 is genuine.
- (2) χ probe: Δχ per added depth = [46.6, 1.92, 0.30, 0.27] (N=4), [41.9, 1.86, 0.33, 0.26] (N=6). Δχ/(2N) = [5.82, 0.24, 0.038, 0.033] vs [3.49, 0.155, 0.028, 0.022] — does NOT collapse across N, and the first increment (the single-round spectral collapse) dominates. No de57/59/60-constant-then-de58-jump pattern; no clean 2N law.

**Kill_criterion:** "Δχ unrelated to 2N, or doesn't reproduce de57/59/60-constant-vs-de58-grows" — **fired? YES.**

**Verdict reasoning:** The two-conditions structure is real and re-confirmed (g2=g1+h mod 2^N, 946/946; independent low bits) — but that fact was already CONFIRMED 8× by prior cards. This card's *new* asset is the free-entropy χ *mechanism*, and it fails its own probe: χ's increments neither single out de58 nor scale like 2N, and Δχ/(2N) does not collapse across N. So free entropy does not *derive* the factor-2; at best it permits 2^-2N — the RENAME outcome that prior finding #3 explicitly excludes from CONFIRM.

**Cross-check / skeptic note:** The decisive reason χ can't be the mechanism: the genuine factor-2 lives in (Z/2^N) — it is the *modular* relation g2=g1+h with g1=0 AND h=0, an arithmetic/finite-ring fact. Free entropy χ is a *real* spectral log-energy, and the card's own note flags that the N²-LDP is rigorous only for unitarily-invariant ensembles, which SHA's fixed-Σ product is not. The "2" the data hands us is two arithmetic constraints, not two free spectral axes; equating them would be a coincidental log-energy fit. Hence the two-conditions survives (it's ground truth), but the free-entropy framing is KILLED as the explanation.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-FP4.py`
