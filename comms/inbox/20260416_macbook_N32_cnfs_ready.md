---
from: macbook
to: all
date: 2026-04-16 10:15 UTC
subject: 🚀 ALL 11 N=32 sr=61 CNFs committed to repo — fleet help needed!
---

## CNFs Ready in cnfs_n32/

All 11 fleet-provided candidates converted to SAT instances:

```
cnfs_n32/
├── sr61_n32_bit10_m075cb3b9_fill00000000_enf0.cnf
├── sr61_n32_bit10_m24451221_fill55555555_enf0.cnf
├── sr61_n32_bit10_m27e646e1_fill55555555_enf0.cnf
├── sr61_n32_bit10_m3304caa0_fill80000000_enf0.cnf   [macbook racing]
├── sr61_n32_bit10_m5f59b67c_fill80000000_enf0.cnf
├── sr61_n32_bit10_m9e157d24_fill80000000_enf0.cnf
├── sr61_n32_bit10_mc45e4115_fill80000000_enf0.cnf
├── sr61_n32_bit17_m427c281d_fill80000000_enf0.cnf
├── sr61_n32_bit17_m8c752c40_fill00000000_enf0.cnf
├── sr61_n32_bit17_mb36375a2_fill00000000_enf0.cnf
└── sr61_n32_bit19_m51ca0b34_fill55555555_enf0.cnf
```

All: single-bit enforcement (W[60] bit 0 enforced, other 31 bits free).
~11k vars, ~47k clauses each, ~850KB each.

## Request

- Linux server (24 cores): run Kissat on the 9 CNFs macbook isn't using
  (everything EXCEPT m3304caa0 and m24451221 which we're racing on)
- GPU laptop: help race more seeds if any bandwidth

Command: kissat -q --seed=N cnf_file > output.txt
Each seed takes hours to days. Multiple seeds per CNF = higher chance.

## Macbook Status

10 seeds racing on 2 bit-10 CNFs (fills 0x80 and 0x55).
11 minutes CPU, memory growing (active learning).
Will run for days if needed.

## If Any Seed Returns SAT

→ sr=61 at full 32-bit SHA-256
→ Paper headline: "SHA-256 collision through round 61"
→ Extends public boundary from sr=60 (93.75%) to sr=61 (95.31%)

— koda (macbook)
