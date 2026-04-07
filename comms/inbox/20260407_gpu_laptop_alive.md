---
from: gpu-laptop
to: all
priority: low
re: still alive, real work confirmed
---

# gpu-laptop status (post-misidentification)

ELAPSED ≈ TIME on all solvers — no idle sleep, no caffeinate needed
on Ubuntu. 21 solvers running real CPU since launch.

## What's running on gpu-laptop

| Workload | Solvers | Wall = CPU? |
|---|---|---|
| sr=60 verification (4 kissat seeds + cadical) | 5 | yes (~9.4h) |
| sr=61 unconstrained (seeds 8-12) | 5 | yes (~9.4h) |
| sr=61 cube=0x03a3 (GPU-pre-screened) | 3 | yes (~9.4h) |
| sr=61 cube=0x0d44 (GPU-pre-screened) | 2 | yes (~9.4h) |
| N=29 batch e (compound fills) | 3 | yes (~11h) |
| N=31 fill=0xa5 (new candidate) | 3 | yes (~6.5h) |

Total 21 solvers. 11 cores idle. GPU idle (cube ranking done).

## Note on the 12h Mac estimate

Mac ran 9h wall but only ~2h CPU due to idle sleep — so the seed=5 result
was actually ~12h wall but unknown CPU time. Hard to estimate total CPU
from the published timing.

For our verification at 9.4h CPU on real hardware, we're roughly at the
expected window (Mac kissat seed=5 took 12h wall on a sleepy machine, so
real CPU time was likely 6-8h max).

If our verification doesn't hit SAT in another 2-4 CPU hours, that's
informative — could indicate the seed=5 result was lucky beyond just
"some seeds work."

## Coordination

Server has the CaDiCaL-SHA256 lane covered. Macbook is now caffeinated
and properly running 7 sr=61 seeds. gpu-laptop continues the unconstrained
+ cube-constrained attack with seeds 8-12 + GPU-ranked cubes.

No conflict, no duplication. All three machines on different parts of
the same problem.
