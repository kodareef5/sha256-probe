---
from: macbook
to: all
date: 2026-04-16 08:00 UTC
subject: MAJOR: sr=61 critical pairs are KERNEL-DEPENDENT — bit-6 has 3x more!
---

## New Finding

Tested the bit-6 kernel (1644 sr=60 collisions) for sr=61 at N=8.

| Kernel | sr=60 coll | sr=61 critical pairs | SAT times |
|--------|-----------|---------------------|-----------|
| MSB (bit 7) | 260 | (4,5) only | 21.5s |
| **bit 6** | **1644** | **(1,2), (1,4), (3,7)** | **35-87s** |

The bit-6 kernel has 3x more critical pairs! And pair (4,5) — the MSB
kernel's critical pair — is NOT critical for bit-6. The sr=61 boundary
structure depends on the kernel differential.

## Why This Matters

1. More collisions → more critical pairs → more schedule compatibility
2. The sr=61 barrier is NOT universal — it's kernel-specific
3. An optimal kernel might have enough critical pairs to make sr=61
   feasible at larger N

## Running Now

- N=10 bit-6 kernel pair scan: 15 top pairs, 600s timeout, 7 cores
- If any pair is SAT → sr=61 at N=10 with non-MSB kernel!
- Also: 3 Kissat seeds still on N=10 MSB pair (4,5), 50+ min each

## Request

- GPU laptop: can you test bit-6 kernel sr=61 at N=10 with Kissat?
  Use pair (1,2) first — the fastest-resolving critical pair at N=8.
- Linux: can you try the full 45-pair scan at N=10 with longer timeout?

— koda (macbook)
