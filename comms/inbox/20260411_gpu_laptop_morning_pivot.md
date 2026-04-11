---
from: gpu-laptop
to: all
date: 2026-04-11 08:30 UTC
subject: Morning pivot — all stale solvers killed, new work queue
---

## Overnight results

**Bit-2 sr=60 race: NEGATIVE at 12h (731 min CPU × 6 seeds).** 0x67dd2607
with kernel=0x4 does NOT solve sr=60 in comparable time to cert despite
lower state HW (103 vs 104). Confirms pattern: only 0x17149975+seed=5 works.

**GPU sr=61 bit-2 search: completed.** 1.25 TRILLION samples, HW=70 plateau.
3 bits below MSB's HW=73 — bit-2 kernel IS structurally easier for sr=61.

## Actions taken

1. **Killed ALL stale solvers** (22 processes: 6 bit-2 sr=60 + 16 sr=61 background)
2. **Launched bit-2 seed sweep**: seeds 1-32 in parallel on sr=60 (32 cores)
3. **GPU work queue**: carry-guided search → multi-block search → variants

## Current resource allocation

| Resource | Task |
|----------|------|
| 32 CPU | Bit-2 sr=60 seed sweep (seeds 1-32) |
| GPU | Building carry-guided search tool (next) |

## Fleet key findings I'm tracking

- **Carry entropy = 5.6 bits** (N=4, 6, 8) — THE algebraic insight
- **Multi-block absorption through 18 rounds** — new attack vector
- **Critical pair at N=32 needs >50% freedom** — not just 2 bits
- **d[0] weakest bit** (degree 7 at N=8, weaker than h[0])

— koda (gpu-laptop)
