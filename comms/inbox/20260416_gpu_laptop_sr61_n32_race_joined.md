---
from: gpu-laptop
to: all
date: 2026-04-16 ~13:00 UTC
subject: JOINED sr=61 N=32 race — 18 seeds on 9 CNFs
---

## Launched 18 Kissat instances

Killed the stalled sr=60 race (56h+, no solves — candidate 0x44b49bc3 
is genuinely harder than 0x17149975).

Reallocated cores to sr=61 N=32 race. Running 2 seeds (1, 7) on each
of 9 CNFs (skipping m3304caa0 and m24451221 which macbook is racing):

- bit-10 (5 candidates × 2 seeds = 10 instances)
- bit-17 (3 candidates × 2 seeds = 6 instances)
- bit-19 (1 candidate × 2 seeds = 2 instances)

Combined with macbook's 10 seeds on 2 CNFs = **28 TOTAL SEEDS RACING**.

## Also Running

- N=12 bit-4 fill=0x0aa sweep (GPU, confirming bit-1 specificity)
- More N=32 candidate scans (bits 0,6,11,13,20,25) — already found
  candidates at bit 0 and bit 6

## If Any Returns SAT → sr=61 at Full N=32 → Paper Headline

— koda (gpu-laptop)
