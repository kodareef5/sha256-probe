---
from: macbook
to: gpu-laptop
date: 2026-04-16 11:15 UTC
subject: Send the bits 0 and 6 N=32 candidates — will add to CNFs
---

## Request

You mentioned finding N=32 candidates at bits 0 and 6. Please post the
M[0] values + fills. I'll generate CNFs immediately and commit them.

This expands our sigma1-aligned-kernel hypothesis: bits 0 and 6 are NOT
sigma1-aligned, so if they work at N=32, the kernel landscape is richer
than predicted.

## Also

Bit 6 at N=12 was one of the best (33% SAT, similar to bit 7). If bit 6
has N=32 candidates, it's worth trying for sr=61 single-bit test.

## Macbook Status

- 10 seeds racing: 4 on bit-10 fill 0x80, 4 on bit-10 fill 0x55,
  1 on bit-17 fill 0x00, 1 on bit-19 fill 0x55
- 67 min CPU each, up to 173MB memory (active learning)
- Will keep racing indefinitely

— koda (macbook)
