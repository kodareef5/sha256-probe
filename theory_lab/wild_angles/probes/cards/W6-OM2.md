# W6-OM2 — Pila–Wilkie → 0.74 as the dimension of the algebraic part   ·   VERDICT: KILLED

**Card claim:** split collisions into cascade/ALGEBRAIC (de58 follows the linear-propagation law; positive-dim families) vs LUCKY/TRANSCENDENTAL; Pila–Wilkie says the off-algebraic points are sub-polynomial, so 2^{0.74N} is *entirely* the algebraic part → 0.74 = its normalized dimension.

**Probe run:** N=4 exact (this engine) + the verified counts at N=8/10 and the repo's best-kernel table (cascade_structure_complete.md sec 7), throttled. (1) Applied the *pre-registered* de58-law classifier (algebraic ⇔ de60=0 cascade law) to every N=4 collision and to the 260 verified N=8 collisions. (2) Least-squares-fit log₂(#collisions) vs N for the MSB kernel and for the paper's best-kernel counts; reported the slope, the per-N local slope (scatter), and incremental N→N+1 slopes; compared to 0.74 and to finding #2's canonical 0.673.

**Result (numbers):**
- **Split is degenerate:** N=4 = 49/49 algebraic, 0 off-algebraic. All 260 N=8 cascade collisions are algebraic (de60=0 holds ALWAYS, sec 3). The transcendental class is **EMPTY**.
- **Actual exponent:** LS slope log₂(count)/N = **0.617** (paper best-kernel, N=4..12) and **0.832** (MSB, N=4/8/10). Per-N local slopes (cumulative log₂/N) range **[0.99, 2.00]**, spread 1.01; incremental N→N+1 slopes oscillate **+2.81, −3.63, +2.17, +2.14, +3.12, −2.96, +0.57, +0.43** (violent N-mod-4 swing). Finding #2's 0.673 sits inside the fitted range; 0.74 does not match the slope.

**Kill_criterion:** "off-algebraic also grows ~2^{cN} (c not ≪0.74), OR algebraic slope ∉ 0.74±0.05." — **fired? yes (both clauses).**

**Verdict reasoning:** Both kill clauses fire. (i) The off-algebraic part is empty (every cascade collision satisfies the de58 law by construction), which doesn't *pass* the "≪" test so much as **vacuate the Pila–Wilkie split**: you cannot call 0.74 "the dimension of the algebraic part" as distinct from a transcendental remainder when there is no remainder — it would just be the dimension of the whole set. (ii) The measured growth exponent is 0.617 (best-kernel LS) / 0.673 (canonical, finding #2), NOT 0.74, and it is not sharp — the per-N slope scatters across 0.99–2.00 with a ±3 N-mod-4 oscillation, exactly the "0.74 is not sharp; the small-N plateau drifts" finding. The 0.74 figure is a small-N artifact, not a stable algebraic dimension.

**Cross-check / skeptic note:** The classifier circularity the card flags is moot here because the split collapses entirely (no transcendental points to mis-assign). The slope estimate is kernel-dependent (MSB 0.832 vs best-kernel 0.617) precisely because the N-mod-4 scatter dominates at these small N — which is itself the point: there is no clean 0.74 to read off. A larger-N fit (N≥16) would tighten the asymptote, but every measurement here lands at 0.62–0.83, straddling 0.673 and never settling at 0.74.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OM2.py`
