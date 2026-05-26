---
date: 2026-05-26
bet: block2_wang
status: VERDICT (interim) — kill #1 NOT fired; >18 gate search-limited; decision pending
author: macbook-claude
evidence_level: EVIDENCE (R=18 absorber VERIFIED; R>=19 search-limited, not proven-infeasible)
---

# block2_wang verdict: an 18-round absorber exists; >18 is search-limited (not refuted)

One day of dedicated trail-engine development (the bet's premise) produced a working,
control-validated engine and a clear — if not yet decisive — answer on the >18-round gate.

## What was built (all committed locally)

- **Wang trail engine** (`encoders/wang_trail_engine.py` + `wang_search.py`): generalized
  (de Cannière–Rechberger) condition algebra, carry-aware modular-addition propagation,
  full-round forward propagation, backward/arc-consistency refinement, a bit-level
  constraint network with worklist propagate-to-fixpoint, and a guess-and-determine search.
  Each layer self-tested against the `lib.sha256` oracle.
- **Control (required by kill #1)**: the engine independently reproduces the known SHA-256
  **9-step local collision** — provably uncancellable ≤8 rounds, constructible at exactly 9,
  oracle-confirmed (`20260526_local_collision_control.md`).
- **Message-schedule constraints** for t≥16 (`build_schedule`), self-tested vs the concrete
  `lib.sha256` schedule.
- **CNF encoder** (`encoders/absorber_cnf.py`) reusing `lib.cnf_encoder.CNFBuilder`, validated
  against the engine (bit13 R=4 UNSAT, R=8 SAT).

## What was found

**Self-absorption is impossible**: with no block-2 message difference, the dense residual
cannot vanish (contradiction by propagation, all clusters).

**An 18-round block-2 absorber EXISTS and is oracle-confirmed.** With message modification,
kissat on the validated CNF (bit13_HW35) gives:

```
  R=15: SAT (0.1s)   R=16: SAT (0.1s)   R=18: SAT (5.2s)   R=19: UNKNOWN (kissat 866s, cadical 300s — both timeout)   R=20: TIMEOUT (300s)
```

The **R=18** solution is verified by `lib.sha256`: input difference = the residual, **zero
state difference after 18 rounds**, block-2 message-difference HW 240. This *matches* the
naive-SAT 18-round frontier — it does not yet beat it.

**The naive guess-and-determine engine reaching only R=15 was a weak-search artifact**, not
structure: a real CDCL solver clears R=15/16 instantly and R=18 in seconds. (The engine's
value is its sound propagation + control validation, not its DFS.)

**R≥19 is a sharp hardness cliff.** R=18 solves in 5 s; R=19 is unresolved after 866 s of
kissat (UNKNOWN), and R=20 times out. So the practical solving frontier of this *naive* CNF
sits right at 18 — consistent with the project's prior "naive-SAT ≈ 18" figure.

## Decision — kill #1 NOT fired

- The **>18 gate is neither met nor refuted**: R≥19 is **search-limited (timeout), not
  proven-infeasible**. Propagation finds no contradiction at R=18/20/24, so a >18 absorber
  may well exist; we simply can't find or refute it with the naive encoding + a generic CDCL
  solver in reasonable time.
- Firing kill #1 requires a >18 trail to be *decisively unreached after a real search effort*;
  a timeout is not that, and the engine deliverable is substantial. **Kill #1 stays unfired.**
- **Caveat (scope of the R=18 result)**: the CNF leaves the chaining value CV **free** (the
  solver picks it), so the R=18 SAT is a >=18-round absorber *trail* for the residual
  *difference pattern* (kill #1's question) — **not yet a full 2-block collision pinned to
  block 1's actual output CV**. Pinning CV (and extending to all 64 rounds + feed-forward) is
  strictly harder and untested.

## Recommendation — pause for a direction decision (do not grind the naive CNF further)

The naive 2-message CNF has hit its practical ceiling at 18. Pushing past it is a real,
multi-increment effort, not more grinding. Options:
1. **Pause block2_wang here** with this deliverable (engine + control + oracle-confirmed
   18-round absorber). Strong, honest, recorded.
2. **Tailored encoding**: use the engine's differential-path conditions to *warm-start /
   constrain* the SAT instance (the actual Wang advantage — a good characteristic shrinks the
   search), aiming to push a solver past 18. Multi-increment.
3. **Redirect** the autonomous lane to another unowned mechanism.

## Reproduce
```
python3 headline_hunt/bets/block2_wang/encoders/absorber_cnf.py          # encoder self-test
python3 -c "import sys; sys.path.insert(0,'headline_hunt/bets/block2_wang/encoders'); \
  from absorber_cnf import solve_absorber, oracle_verify, CLUSTERS; d=CLUSTERS['bit13_HW35']; \
  s,_,(c,r,o)=solve_absorber(d,18,'bit13_HW35',timeout=120); print('R18',s, oracle_verify(d,18,r,o))"
```
