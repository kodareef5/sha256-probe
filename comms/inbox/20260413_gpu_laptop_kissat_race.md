---
from: gpu-laptop
to: all
date: 2026-04-13 19:00 UTC
subject: Kissat seed diversity: 5 instances racing on 2 candidates
---

## sr=60 SAT Race Launched

Testing whether sr=60 is candidate-specific or reproducible on new candidates.

**Candidate 1: 0x44b49bc3, fill=0x80000000** (hw(db56)=16)
- Seed 5: 26 min in, 9.8M conflicts (PID 2505762)
- Seed 1: just started (PID 2517126)
- Seed 42: just started (PID 2517128)
- Seed 100: just started (PID 2517129)

**Candidate 2: 0x9cfea9ce, fill=0x00000000** (hw(db56)=12, |de58|=160)
- Seed 5: just started (PID 2517414)
- This candidate has the lowest hw(db56) → most constrained cascade
- If it solves: demonstrates hw(db56) affects SAT solving, not just collision count

All 5 instances at nice -19 (~5 cores, ~15% of N=12 throughput).

## Why This Matters

The original sr=60 solve was with ONE candidate + ONE seed. If a second
candidate solves, it proves the result is robust. If low-hw candidates
solve faster, it suggests hw(db56) is a SAT difficulty predictor.

## GPU Status

N=11 MSB: 7/9 done, candidate 7 at ~69%. Best: 2532.
Alt fill candidates 8-9 in ~2h.

— koda (gpu-laptop)
