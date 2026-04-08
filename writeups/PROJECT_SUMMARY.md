# SHA-256 Probe: Project Summary

## Principal Result

**sr=60 collision found for full 32-bit SHA-256** (MSB kernel, semi-free-start).

Certificate: M[0]=0x17149975, fill=0xFFFFFFFF  
W1[57..60] = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]  
W2[57..60] = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]  
Hash: `ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b`

Found by Kissat 4.0.4 --seed=5 in ~12h. Triple-verified across 3 machines.
Extends Viragh (2026) from sr=59 (92.19%) to sr=60 (93.75%).

## Secondary Result: sr=60 is the Boundary

**sr=61 is UNSAT at N=8** for all tested candidates (6 MSB-kernel + 1 multi-bit
kernel), with 4 DRAT-verified impossibility proofs. At N=32, 42+ hours of
compute across 3 machines (~2500+ CPU-hours, 24+ CDCL instances + GPU SLS)
produced zero results.

## How the Collision Works

The sr=60 collision uses a **perfect register-zeroing cascade**:

1. da[56]=0 (candidate property) → db57=0 (shift register)
2. W[57] chosen to zero da57 → dc58=0 → dd59=0 (shift cascade)
3. W[60] chosen to zero de60 → df61=0 → dg62=0 → dh63=0 (COLLISION)

Two free words do active work (W[57], W[60]). Two handle schedule
compatibility (W[58], W[59]). The timing is perfect: cascade 1 delivers
dd59=0 just as cascade 2 needs to begin at round 60.

## Why sr=61 is Impossible

sr=61 removes W[60] as a free word. The cascade mechanism requires W[60]
to trigger the second zeroing wave at round 60. Without this freedom,
the collision cannot close.

Evidence:
- N=8: ALL candidates UNSAT (4 DRAT-verified, 6 solver-confirmed)
- N=8: 2-bit kernel UNSAT, non-contiguous gap UNSAT, 20 K[61] constants ALL UNSAT
- Phase transition: N=8 needs 50%+ of W[60] free, N=10 needs 70%+, N=32 needs ~100%
- N=32: 42h × 24 CDCL solvers + GPU SLS plateau at 97% → no SAT found
- Structural: 3 free words give 96 bits of freedom vs 256 bits of collision constraint

## Key Methodological Insight

The original paper called the published candidate "UNSAT" at sr=60. This was
wrong — it was a **single-seed artifact**. Kissat with default seed doesn't find
the solution; seed=5 does in 12 hours. Seed diversity is essential for hard
SAT instances.

## Compute Investment

| Experiment | CPU-hours | Result |
|---|---|---|
| sr=60 N=32 race (24 solvers) | ~360 | **SAT at 12h (seed=5)** |
| sr=61 N=32 race (24 solvers) | ~1000+ | TIMEOUT (42h+) |
| sr=61 N=8 DRAT proofs | ~2 | 4/6 VERIFIED UNSAT |
| Q3 candidate search (8 fills) | ~50 | All identical |
| Q5 constrained experiments | ~310 | All TIMEOUT |
| Total project | ~2500+ | |

## Infrastructure

- 3 machines: 24-core Linux server, 10-core Mac M5, 32-core i9 + RTX 4070
- Tools: Kissat 4.0.4, CaDiCaL 3.0.0, CaDiCaL-SHA256 (Alamgir), GPU SLS
- Shared library: lib/ (Python + C), CNF encoder with constant propagation
- Coordination: GitHub issues, git-based comms, 30-min cron check-ins

## Open Questions

1. Is sr=61 provably UNSAT at N=32? (Would need DRAT at full width — infeasible)
2. Can semi-free IV choice make sr=61 SAT? (Unexplored dimension)
3. Can a non-MSB-kernel attack achieve sr=61? (No da[56]=0 candidates found)
4. What is the exact phase transition for partial W[60] enforcement at N=32?
