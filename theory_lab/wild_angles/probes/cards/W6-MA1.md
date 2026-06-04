# W6-MA1 — Constraint-matroid corank = 132 (a cocircuit support, not a solver artifact)   ·   VERDICT: KILLED

**Card claim:** The GF(2) cascade matroid M[A] (carries free ground elements) has rank = controllable dim and corank = |E|−rank = cobasis = the forced bits; conjecture the fundamental-cocircuit support = 132 = 128 (W*_59,W*_60, 4 words×32) + 4 anchors, derived from rank, order-independent, no solver.

**Probe run:** N=8,10,12 (+ N=32 for the schedule/literal-132 width), throttled (`OMP_NUM_THREADS=2 taskpolicy -b`). Built the honest GF(2) constraint matroid three ways and computed corank order-independently (GF(2) rank, `oc.rank`):
- (A) per-round relation matroid M[J_r | B_r] for every tail round 57..63 (ground set = 9N input cols), and the FULL stacked tail constraint system (state layers 57..64 + control W57..63);
- (B) the SCHEDULE-bit matroid: corank of the schedule recurrence over the 7N bits W57..63 (σ1/σ0 linearized exactly — they ARE GF(2)-linear);
- (C) the deterministic-control CENSUS (what "132" actually is): {a,b,e,f}+dc uncontrollable output bits.

**Result (numbers):** Every honest matroid corank is **WIDTH-SCALING**, never a stable 132:

| object | N=8 | N=10 | N=12 | N=32 | law |
|---|---|---|---|---|---|
| (A) per-round relation corank | 8 | 10 | 12 | 32 | **= N** (the free control cols B_r) |
| (A) full stacked tail corank | 120 | 150 | 180 | (12N) | **= 8N+4N free inputs**, linear in N |
| (B) schedule-bit free-corank | 32 | 40 | 48 | **128** | **= 4N** (free words W57..60; 3N forced) |
| (C) census (det-control) | 46 | 55 | 65 | (132 at 32) | overshoots 4N+4 at small N (carry extras) |

- `rank(J_r)` = 8N at every round (the round map is a GF(2) **bijection** on the difference state ⇒ corank 0 from the dynamics; the per-round corank N is purely the free control word).
- (B) at the literal 32-bit width: schedule matroid rank = 96, **free-corank = 128 = 4N**, NOT 132. The 3N=96 pinned bits (W61,W62,W63) are exactly the schedule recurrence; the 4N=128 free bits are W57..60.
- (C) census = 4N+4 only at width 32 (=132); at small N it is 46/55/65 (not the clean 36/44/52) because g picks up 6–9 extra carry-blocked bits. {a,b,e,f} is fully uncontrollable (4N) at every N; that 4N + 4 dc = 132 at width 32.

**Kill_criterion:** "corank NOT→132, or all 256 schedule bits equally free/forced" — **fired? YES.** Every honest corank is N-scaling (8/10/12, or 4N, or 8N+4N) and NONE → 132; and the schedule bits are NOT equally free/forced (4N free vs 3N forced) — but that split is the width-scaling 4N/3N census, not a 132 cocircuit.

**Verdict reasoning:** This is the flagship instance of prior finding #1 (the "132 = corank" CATEGORY ERROR, now 16×). The honest, elimination-order-independent GF(2) constraint-matroid corank is a width-scaling quantity in every honest reading — per-round relation corank = N, full-tail corank = 8N+4N free inputs, schedule corank = 4N — and **not one** of them is a stable, basis-independent 132. The state-Jacobian rank is full (8N) at every round, so the round dynamics contribute corank 0. The ONLY object that hits the literal 132 is the 4N+4 **deterministic-control census** of uncontrollable output bits ({a,b,e,f}+4dc), evaluated at the 32-bit width — and even that census is messy at small N (46/55/65), proving it is a width-32 census artifact, not a clean matroid cocircuit. The cobasis is NOT "preferring W*_59/W*_60 + 4 anchors"; it is the 4N free schedule words W57..60.

**Cross-check / skeptic note:** The card's skeptic note is the right one ("the 132 was measured under one encoder/elimination-order — matroid corank is order-independent; a match is meaningful, a mismatch decisive"). I computed corank by GF(2) rank, which IS order-independent, on three genuinely different honest constructions, at N=8,10,12 and the literal N=32. The mismatch is therefore the decisive case the skeptic note flagged: the corank is order-independently NOT 132. Independent corroboration: matches W6-OC3 (honest kernel = 4N, census messier at small N), W2-CT1, W4-IG1/SH2/FP2, W2-RG2 — all the same width-scaling-not-132 pattern. To CONFIRM I would have needed corank = 132 stable across N=8..32 with a {a,b,e,f}+4dc cobasis; instead corank ∈ {N, 4N, 8N+4N} and the cobasis is W57..60.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-MA1.py`
