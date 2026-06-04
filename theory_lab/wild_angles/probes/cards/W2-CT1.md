# W2-CT1 — Controllability Gramian = the hard-core mask   ·   VERDICT: ❌ KILLED (mechanism) — the number 132 is real, but it is NOT a corank

**Card claim:** linearize the round map on the XOR-difference state; the *uncontrollable subspace (cokernel of the reachability matrix `[B,AB,A²B,…]`)* should **be** the 132 frozen bits. Probe target: corank → 132/256 ≈ 0.516.

**Two probes were run.** They disagree, and the disagreement is the result.

### Probe 1 — single-bit deterministic-control census (`cards/W2-CT1.py`), N=32, 80 base-points
Reproduces the repo's `hard_core_132_bits.md` method (output bit *j* is "hard" iff **no single** input-bit flip flips it in **all** base-points):
- zero-control output bits = **132**, support = a,b,e,f @63 (128) + 4 dc (positions 19,20,22,24); d,g,h fully controlled. Per-register table matches the repo exactly.

### Probe 2 — the literal Kalman/reachability corank (`cards/W2-CT1_kalman.py`), N=32 — THE ADJUDICATOR
The card's *actual* object: the GF(2) span of the single-bit-flip output responses (multi-bit linear combinations allowed), the row-reduced `[B,AB,…]`:
- single base point: rank 128, **corank 128**;
- union over ≥5 base points (most generous linear control): rank **256, corank 0 (full controllability)**.

**Result (numbers):** the literal reachability **corank is 0** (generic) **/ 128** (single point) — **never 132**.

**Kill_criterion:** "Dead if corank ~0 (full controllability) generically, **or** no stable value across base-points/N." — **fired? YES, on both clauses.** Generous corank = 0 (full controllability); and the value is not stable (128 → 0 as base-points are added).

**Verdict reasoning:** ❌ KILLED as a *mechanism*. The card conflates two different objects. The 132 is the repo's **single-bit deterministic-control census** — and it reproduces perfectly — but that is a particular *nonlinear/operational* protocol (which bits no single lever deterministically moves at every base-point, because a,b,e,f receive nonlinear T1+T2), **not** the cokernel of a reachability matrix. The genuine linear reachability corank is 0 (everything is controllable by *some* linear combination at *some* base-point). So "132 = corank of one explicit mod-2 reachability matrix, basis-independent, with a named basis" is **false**.

**Why this matters for all of Batch A (the ~13-formalism "132 = corank" cluster):** this is the canonical corank card, and it KILLS the corank *mechanism* while confirming only the *number*. The implication for the cluster (W2-CT5, W4-IG1, W4-FP2, W4-SH2, W4-CS1, W6-OC3, W6-MA1, W7-FC1, W7-QW3, W8-RD3, W8-KC1, W8-KC3, W1-GE3): **each must be checked for the same category error.** If a formalism computes a genuine basis-independent linear corank, it should land on 0 / 128 / 256 — *not* 132. If it lands on 132, it is (knowingly or not) re-running the single-bit deterministic census — i.e. relabeling the repo's known carry-census number, not deriving a corank. The "convergence on 132-as-corank" is, on this evidence, a **category error shared across the cluster**, not independent corroboration. (W1-GE3 already independently failed to reproduce 132 from a Morse–Bott Hessian kernel — consistent with this.)

**What survives:** the *number* 132 and its support {a,b,e,f}+4dc are real and reproduce independently (Probe 1) — but as the **deterministic-control census** (the repo's EVIDENCE-level result), whose true origin is the carry / T1+T2 nonlinearity, not linear algebra.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-CT1.py` and `…/W2-CT1_kalman.py`
