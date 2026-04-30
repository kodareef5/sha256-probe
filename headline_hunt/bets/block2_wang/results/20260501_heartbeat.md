---
date: 2026-05-01
bet: block2_wang
type: heartbeat
---

# block2_wang heartbeat — 2026-05-01

## What moved 2026-04-30 (yesterday)

User direction landed: combine F374 + yale F378-F384 into a bridge-guided
block2 search toolchain, **not** Phase 2D propagator yet. 5 deliverables
named; 4 shipped:

- **F378** `bridge_score.py`: per-W-witness selector with hard constraints
  (active_regs, da≠de, bridge polarity per F377) + soft asymmetry score.
  Validation: 18% of 447k corpus hard-rejected; F371 sub-floor cands
  rank in top 30/368k.
- **F379** `block2_bridge_beam.py`: greedy hillclimb in 128-bit W-space
  using forward_table_builder cascade-1 primitives. Found
  `bit2_ma896ee41` HW=56 — **below the corpus empirical floor of HW=57**.
  Other 3 cands plateaued (greedy single-bit-flip can't escape).
- **F380**: cert-pin verified F378 top-10 + F379 NEW HW=56 → **22/22
  UNSAT**. Bridge_score formally characterized as a near-residual
  selector (falsified as collision-finder per user's unit-of-progress).

Per F100 + F371-F373 + F380, single-block sr=60 cascade-1 collisions
if reachable are point-singular per F98, not basin-singular —
gradient-search misses them by design. Headline-class output not
delivered yet; structural understanding of the deep tail tightens.

## Open

- Deliverable #5 (cross-cand learned-clause clustering) pivoted to
  F347-F369 60s cadical instances since cert-pin is UP-trivial.
  Next session's main work.
- Beam improvements (SA + restarts) for the 3 plateaued cands.
- F349 closed as UNREPRODUCED_PENDING_EVIDENCE — no further chase.
