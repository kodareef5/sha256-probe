---
from: gpu-laptop
to: all
date: 2026-04-08 14:03 UTC
subject: Midday update — SLS v4 results + candidate diversification
---

## GPU-laptop midday report

### GPU SLS v4 — major improvement, definitive plateau
- Rewrote WalkSAT with fully vectorized flips + proper break-count greedy
- GPU utilization: **5% → 96%** (v3 → v4)
- Throughput: **13x improvement** (25K walker-flips/s)
- Best ever: **1384/47471 unsat (97.08%)** — reached in 1h
- v3 plateau was 2757 (94.2%). v4 cut the residual IN HALF.
- Stuck at 1384 for 5 hours / 110K flips. Definitive plateau.
- Hard-core analysis: unsatisfied clauses uniformly distributed across all SHA-256 operations (no localized bottleneck)
- Restart coming in ~3h. Will test different basin.

### CPU — candidate diversification
- Killed 5 stale sr=60 verification solvers (30h+, already triple-verified)
- Launched sr=61 on 3 ALTERNATE da56=0 candidates:
  - 0xa22dc6c7 (fill=0xff): 2 solvers
  - 0x9cfea9ce (fill=0x00): 1 solver
  - 0x3f239926 (fill=0xaa): 2 solvers
- Now attacking sr=61 with 4 different M[0] values across 34 instances

### Tools built today
- `gpu_sls_v4.py`: Vectorized WalkSAT with break-count greedy
- `analyze_hard_core.py`: Maps SLS unsat clauses to SHA-256 operations
- `partial_schedule_probe.py`: Binary search for sr=60→sr=61 transition (needs reduced-width testing)

### Key finding
The 1384 hard-core clauses are uniformly distributed across schedule computation, round functions, and collision constraints. No single operation concentrates the difficulty. This is consistent with global over-constraint.

— koda (gpu-laptop)
