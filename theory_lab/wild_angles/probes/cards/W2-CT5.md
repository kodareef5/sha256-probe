# W2-CT5 — Kalman observer: the unobservable subspace = the residual search   ·   VERDICT: KILLED (mechanism; 132-as-corank refuted, self-duality holds at 0)

**Card claim:** finding M₂ = estimating `δ = M₂ − M₁` from the back-propagated `δH=0` measurements; the observability Gramian's kernel = the δ-directions the constraint leaves free = the residual brute force. Dual to CT1: self-duality of the feed-forward add predicts **observable corank = controllable corank, both = the 132 hard core.** Probe: corank of `O = [C; CA; CA²; …]` over GF(2); compare to CT1 corank; verify the observer recovers the brute-forced collision partner's bits.

**Probe run:** built `O = [C; CA; …; CA^{63}]` over GF(2) on the 8N-dim difference state. `A` = one XOR-linearized SHA-256 round (`kernels/linround.py`). `C` = measurement map: (i) the `a`-register difference (the per-round enforced equation, N rows) and (ii) the full `δH=0` (all 8 registers, 8N rows). Computed `corank_obs = 8N − rank(O)` and the dual controllable `corank_ctrl` (CT1-style `R=[B,AB,…]`). N = 8,10,12, and **N=32** (the width where "132" is claimed). Throttled.

**Result (numbers):**

| N | measure | rank(O) | corank_obs | rank(R) | corank_ctrl | duality |
|---|---|---|---|---|---|---|
| 8 | a_reg / full | 64 | **0** | 64 | **0** | MATCH |
| 10 | a_reg / full | 80 | **0** | 80 | **0** | MATCH |
| 12 | a_reg / full | 96 | **0** | 96 | **0** | MATCH |
| 32 | a_reg / full | 256 | **0** | — | — | **132? NO** |

- Observability corank is **0 at every N** (both measurement choices). Self-duality **holds**: `corank_obs = corank_ctrl = 0` everywhere — but the shared value is **0, not 132**.
- At **N=32**, `corank_obs = 0`; **132 does not appear** as a corank.

**Kill_criterion:** "Dead if the observer predicts no bits (unobservable = everything) **or** observable/controllable coranks don't match." — **fired? Neither literal clause fires** — but in a way that *refutes the card*, see below.

**Verdict reasoning:** KILLED as a **mechanism**, exactly mirroring the flagship W2-CT1. The card makes three sub-claims; the probe splits them:
1. **"unobservable subspace = the residual search"** — **FALSE.** The linear unobservable subspace is **empty** (corank 0): the linear observer claims `δM₂` is *fully* determined by `δH=0`. Yet the residual search is provably real and large (sr=61 costs `2^-2N`). So the residual brute force is **not** a linear unobservable subspace — it lives in the **modular carries the linear observer cannot model** (precisely the card's own skeptic note). The literal kill clause ("observer predicts no bits") does not fire, but its *opposite* failure does: the observer over-claims (predicts everything), which is just as fatal to "unobservable = residual."
2. **"both coranks = the 132 hard core"** — **FALSE.** Both coranks are **0**, never 132. This is the **finding-#1 category error** again: 132 is *not* a basis-independent linear corank; a genuine GF(2) observability corank is 0 (full observability). 132 only arises from the nonlinear single-bit deterministic-control census (W2-CT1.py) — re-deriving it from `[C;CA;…]` is impossible without secretly re-running that census.
3. **"observable corank = controllable corank" (self-duality)** — **TRUE, but vacuous here**: both equal 0. The feed-forward add genuinely is self-dual, so the structural prediction survives — at the trivial value, which carries no information about the hard core.

So the card's headline ("the unobservable subspace IS the residual search, = 132, = the controllable corank") is dead: the unobservable subspace is empty, it is not 132, and the only surviving piece (duality) holds at 0.

**Cross-check / skeptic note:** This is consistent with W2-CT1_kalman (controllable corank 0 generic / 128 single-point, never 132) — here the *dual* lands on the same 0. The honest nuance: the card's kill clauses are worded for the *other* failure mode (unobservable = everything), so a literalist could say "kill didn't fire." But corank 0 = "observable = everything," which equally destroys "unobservable subspace = residual search," and it refutes the "= 132" and "both = hard core" claims outright. To probe the *real* residual one would need a carry-aware (nonlinear / 2-adic) observer, not a GF(2) `[C;CA;…]` Gramian — which is no longer the Kalman-observer reframe the card sells.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-CT5.py`
