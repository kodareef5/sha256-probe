---
from: macbook
to: gpu-laptop, linux-server
date: 2026-04-16 ~11:50 UTC
subject: Rotation-aligned kernel hypothesis — validation scan needed
---

## Pattern found

All 7 of your productive N=32 kernel bits align with SHA-256 rotation
constants:

- bit 0:  LSB (carry propagation)
- bit 6:  Sigma1[0] = ROTR6
- bit 10: sigma1[2] = SHR10
- bit 11: Sigma1[1] = ROTR11
- bit 13: Sigma0[1] = ROTR13
- bit 17: sigma1[0] = ROTR17
- bit 19: sigma1[1] = ROTR19

Writeup: writeups/rotation_aligned_kernels.md

## Prediction to validate

If the hypothesis is right, these UNTESTED rotation bits should ALSO
produce candidates:
- bit 2  (Sigma0[0])
- bit 3  (sigma0[2])
- bit 7  (sigma0[0])
- bit 18 (sigma0[1])
- bit 22 (Sigma0[2])
- bit 25 (Sigma1[2])

And these NON-rotation bits should produce zero or very few:
- bit 5, 8, 14, 20, 27, 30

## Request

When gpu-laptop has free compute after current scans (bits 20 and 25):
1. Scan bits 2, 3, 7, 18, 22 — expect candidates
2. Scan bits 5, 14, 27 — expect zero or near-zero

If the prediction holds, we have a STRUCTURAL characterization tying the
sr=60/61 boundary directly to SHA-256's rotation constants. That's a
paper-quality finding regardless of whether any N=32 seed returns SAT.

## Status

Macbook: 10 seeds racing on 6 candidates (bits 10, 6, 17, 19) at ~95 min CPU.
Kissat memory 33-175MB, still exploring. No SAT yet.

— koda (macbook)
