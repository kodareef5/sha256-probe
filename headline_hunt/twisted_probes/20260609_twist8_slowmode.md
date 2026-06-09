---
date: 2026-06-09
author: subagent (fable session)
evidence_level: EVIDENCE
twist: 8
title: "Slowest-diffusing differential eigen-mode of SHA-256 (richer than single-bit)"
script: headline_hunt/twisted_probes/twist8_slowmode.py
---

# Twist 8 — Hunting SHA-256's slowest-diffusing differential "eigen-mode"

## Question
Twist 4 swept all 256 single-bit input-state differences and found register-b
high bits diffuse slowest (b[31] best, 3.62x spread at R=4). This twist asks
whether the **richer multi-bit difference space** contains a "resonant"
slow-mode — a structured delta that diffuses markedly slower than the best
single bit, which would be a genuinely weak differential direction.

Method: avalanche = mean total Hamming weight of the output state difference
after R rounds, averaged over random base states + random messages, applying
the candidate delta by XOR. Verified round function reused exactly from
`fresh_batch.py`. Two searches: (1) greedy hill-climb in difference space
starting from b[31], adding/removing diff bits to minimize avalanche;
(2) structured families (MSB-only, b-confined, rotation-symmetric, paired
high bits). R = 4 and R = 6. Fully deterministic (seeded). Runtime ~50 s.

## Key numbers (head-to-head, common fresh seed, Ksamp=4000)

| R | best single-bit (baseline) | greedy local-min | best structured |
|---|---|---|---|
| 4 | b[31], HW=1, av=**30.1** | b[31], HW=1, av=30.1 (1.000x) | MSB-only b[31], HW=1, av=30.1 |
| 6 | b[31], HW=1, av=**87.2** | b[31], HW=1, av=87.2 (1.000x) | MSB-only b[31], HW=1, av=87.2 |

**The greedy hill-climb, started from b[31], makes no move** — every single-bit
add/remove strictly increases the R-round avalanche. The local minimum IS the
single-bit b[31]. The best structured candidate is also exactly MSB-only b[31].
All three "winners" collapse to the same HW=1 difference.

Structured-family ranking confirms the picture (R=4 avalanche, ascending):
- MSB-only b[31]: **30.2**  (slowest)
- b two-high {b30,b31}: 39.1
- MSB-only a[31]: 48.0 ; MSB-only c[31]: 49.2
- b high nibble (4 bits): 51.8
- b top byte (8 bits): 67.9 ; b all-ones (32 bits): 96.5
- e rot-sym {6,11,25}: 119.9  (fastest — e feeds Sigma1+Ch, maximally active)

Adding ANY second difference bit raises avalanche: e.g. b[31]+b[30] is 39.1 vs
30.2 for b[31] alone. Diffusion is essentially **additive/superadditive** in
input difference bits — richer differences buy *faster*, not slower, diffusion.
Per-input-bit avalanche is flat (30.1/bit for all three winners at R=4): there
is no sub-linear "resonant" packing.

## Secondary observation: diffusion saturates fast
The slow/fast spread shrinks rapidly with rounds: 3.62x at R=4 (matching
Twist 4) collapses to **1.47x at R=6**. By R=6 even b[31] reaches av≈87 of a
~128 saturation ceiling (256 bits → ~128 expected at full mixing). The "slow
direction" is a short-lived head-start, not a persistent low-diffusion channel.

## Why b[31] is the slow direction (mechanism)
Register b at round r is just register a from round r−1; in the round function
b feeds only `Maj(a,b,c)`, and the top bit (bit 31) has no carry-out under
modular addition (XOR == modular at the MSB) and no left-rotation neighbor
above it. So a b[31] difference enters mixing through the single Maj term with
no carry propagation and no Sigma0/Sigma1 fan-out on the first round — the
minimal-activity entry point. Any extra bit (lower bits → carries; other
registers → Sigma/Ch fan-out) adds activity.

## Verdict
**No richer slow-mode exists.** The slowest-diffusing differential eigen-mode of
SHA-256's round function is the trivial single-bit MSB-of-b difference; the
multi-bit/structured search space contains nothing slower. Greedy hill-climb
confirms b[31] is a strict local (and apparently global) minimum at both R=4
and R=6. Diffusion here is **generic**: it grows with the number of active
input-difference bits, with no resonant cancellation. This is the negative
outcome — exactly what a well-designed diffusion layer should produce.

**Not exploitable.** Per the standing project lesson, slow diffusion ≠
exploitable without control leverage. Even the slowest mode (a) is only HW=1,
(b) yields no per-bit advantage, and (c) loses its edge by R=6 (spread → 1.47x),
let alone over the dozens of rounds where SHA-256 is unbroken. There is no
low-weight multi-bit direction to anchor a differential characteristic, and the
single-bit head-start carries no message-control freedom. This **closes** the
"rich slow-mode" door for register-state differences over the round function.

### What would change the assessment
- A multi-bit delta with avalanche meaningfully below the b[31] baseline
  (would indicate destructive interference / a true eigen-mode). None found.
- Persistence: a difference whose avalanche stays low through R≥8–10 instead of
  saturating. Not observed (saturation by R≈6).
- Coupling the state-difference search with message-schedule difference freedom
  (this probe holds W common across the pair). That is a different, larger
  search and is the only remaining avenue where "slow + controllable" could meet.
