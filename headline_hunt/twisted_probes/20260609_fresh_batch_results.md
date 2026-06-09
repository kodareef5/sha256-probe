---
date: 2026-06-09
status: fresh batch (twists 4-6) — all three yield real structural findings
author: macbook-claude (fable model test)
evidence_level: EVIDENCE (deterministic avalanche sampling, N=32, lib/sha256)
---

# Fresh batch: twists 4-6

## Twist 4 — diffusion spectrum (the weakest difference direction)
Swept all 256 single-bit input differences, avalanche HW @ R=4. Slowest-diffusing are the
HIGH bits of register **b** (b[31]=30.1, b[30], b[29]...); fastest are register **e**
(e[12,13,20]=107.8). **3.6x spread.** Structural: e directly feeds the nonlinear T1 path
(Sigma1, Ch) so it mixes instantly; b is farthest from it (b->c shift, only reaches Maj).
**Duality with Twist 3:** forward, b is slowest / h fastest; backward, h is slowest / b
fastest — opposite ends of the register shift-chain, roles swapped under time-reversal.

## Twist 5 — where resistance lives: CARRIES > booleans
Avalanche @ R=4 (drop from baseline 70.1): remove Ch/Maj (=0) -> 55.6 (drop 14.5); replace
all modular adds with XOR (no carries) -> 44.6 (drop **25.5**). **SHA-256's diffusion comes
MORE from the modular-addition carries than from its famous Ch/Maj nonlinearity.** Validates
this repo's carry-focused program. With Twist 2 (no single carry is load-bearing): carries
dominate resistance, collectively and redundantly.

## Twist 6 — are the rotations tuned?
Avalanche @ R=4 swapping the state Sigma0/Sigma1 rotation amounts: SHA-256 actual 69.4;
tiny rots (1,2,3) 29.9; all-same (7) 35.6; generic wide-spread 66.6. **The rotations ARE
tuned for diffusion (~2x over naive) but not uniquely magic — a generic well-spread set nearly
matches.** Spread is what matters, not the specific nothing-up-my-sleeve constants. (Caveat:
only the state sigmas were swapped here, not the schedule sigmas.)

## Net
Better hit rate than batch 1 (all 3 informative). None is an attack lead (Twist 3's lesson
holds: slow diffusion != exploitable, since control leverage is what matters). But together
they form a coherent structural picture: resistance is carry-dominated, redundantly
distributed, with register b/h the slow-diffusion extremes and rotations tuned-but-generic.

## Reproduce
```
python3 headline_hunt/twisted_probes/fresh_batch.py
```
