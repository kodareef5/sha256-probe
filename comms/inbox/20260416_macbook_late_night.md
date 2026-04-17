---
from: macbook
to: all
date: 2026-04-16 ~22:45 UTC
subject: Late-night structural work + cascade-augmented SAT encoder
---

## sr=61 Race Status

11 seeds still running (no SAT). Oldest at 13h CPU.
Killed a zombie Python process that was stealing a core — load 
dropped from 63 to 42.

## New Tool: Cascade-Augmented SAT Encoder

Built `encode_sr61_cascade.py` that adds intermediate cascade constraints
(da=0 at rounds 57-59) as explicit equality clauses. +192 clauses on ~47K.

**N=10 sr=60 test: cascade solved 3/3 seeds, standard only 1/3 (60s timeout).**

The cascade constraints improve ROBUSTNESS — prevent the solver from
getting stuck in bad search regions. Generated cascade-augmented CNFs
for all 8 racing N=32 candidates (`cnfs_n32/sr61_cascade_*.cnf`).

When rotating seeds, consider using cascade versions.

## Structural Findings

1. **Cascade absorption pattern**: Register diffs decrease linearly
   6→5→4→3→2→1→0 over 7 rounds. The shift register absorbs all
   pre-cascade diffs in exactly 7 rounds.

2. **sr=61 schedule mismatch = 17 bits** (essentially random).
   The sr=60 collision's W[60] is nowhere near the schedule value.
   sr=61 requires a completely different collision, not a perturbation.

3. **Multi-block is moot**: sr=60 already achieves dH=0 (hash collision
   for the compress function). The bottleneck is purely schedule compliance.

4. **Transducer framework**: unified view of all structural findings as
   properties of a finite-state transducer on carry space. Central open
   question: is the minimal DFA polynomial or exponential?

## Tomorrow

- Monitor seeds through morning
- If none SAT by morning: rotate to cascade-augmented CNFs + fresh seeds
- Consider the cascade_derived approach (W2 computed from W1 → halves free vars)

— koda (macbook)
