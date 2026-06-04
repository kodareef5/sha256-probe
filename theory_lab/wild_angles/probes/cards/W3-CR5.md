# W3-CR5 — Mass-action analog computer → collisions as ODE fixed points, 2^-2N as codim-2 bifurcation   ·   VERDICT: KILLED

**Card claim:** Engineer a mass-action ODE whose positive stable steady states ↔ collisions; #steady-states realizes 2^0.74N, and the codimension of the bifurcation annihilating them along the round axis = 2 (two zero eigenvalues) realizing 2^-2N.

**Probe run:** Ran the card's own decisive, non-circular test — the Jacobian-injectivity (Craciun–Feinberg) criterion — on the genuine difference-reaction network (the same carry/shift gates used by CR1/CR2). Implemented numerically (no sympy available): build the mass-action species-formation Jacobian J(x)=S·(dv/dx), sample sign(det J) over the positive orthant. Constant sign ⟹ det J never vanishes ⟹ injective ⟹ monostationary (≤1 positive steady state). N=3,4 (main) plus N=3,4,5 robustness across 3 seeds and rate/concentration spans up to 20 orders of magnitude. Throttled.

**Result (numbers):**
- **Injective at every N**: sign(det J) constant (20000/20000 negative at N=3,4; 8000/8000 negative across all robustness runs), **zero sign flips**.
- det J robustly **nonzero** (median |det| ≈ 4.0, 8.5, 12–17 at N=3,4,5) → not the degenerate-continuum case either.
- ⟹ **monostationary**: ≤1 positive steady state. But 2^0.74N collisions needs ~4.7 (N=3), ~7.8 (N=4), exponentially many — impossible.
- Ground truth re-anchored: collision count 2^0.74N; rate 2^-2N = two independent conditions (g1=0, h=0; g2=g1+h exact, indep 1.005).

**Kill_criterion:** "injectivity says monostationary (can't encode an exponential count), OR count ≠ 2^0.74N, OR bifurcations are codim-1." — **fired? YES (first clause)**

**Verdict reasoning:** The mass-action difference-network is robustly injective, hence monostationary by Craciun–Feinberg — it admits at most one positive steady state and therefore **cannot** encode 2^0.74N collisions as distinct fixed points. With a unique steady state on a single branch there is no multi-state fold, so the "codim-2 bifurcation annihilating exponentially many states" has nothing to act on; any "codim-2 = 2^-2N" would be a label imposed by a non-canonical GF(2)→mass-action encoding, not derived. **CR5 does NOT land on the genuine two-conditions structure** (g1,h) — it cannot even produce the multistationarity the story requires. The first kill clause fires cleanly.

**Cross-check / skeptic note:** This is exactly the card's own flagged risk ("no canonical GF(2)→positive-mass-action encoding — a match risks being imposed/circular; the boldest, softest idea here"). The injectivity test is sound and decisive in the falsifying direction: a single observed sign flip would have disproven injectivity, and none occurred across wide ranges/seeds, while the determinant stayed bounded away from zero (ruling out the conservation-law continuum loophole). I tested the network built from the genuine round gates; a different *contrived* network might be made multistationary, but that would be reverse-engineering the answer, not a derivation — precisely the circularity the kill is meant to catch. KILLED.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-CR5.py`
