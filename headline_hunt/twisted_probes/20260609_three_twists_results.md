---
date: 2026-06-09
status: three novel "twisted-constraint" probes — 2 clean negatives, 1 strong positive
author: macbook-claude (fable model test)
evidence_level: EVIDENCE (sampling probes, deterministic, N=32 full word; lib/sha256 round + verified inverse)
---

# Three twisted-constraint probes

Motivation (user's instinct): Viragh's *non-standard* relaxation (freeing schedule equations)
surfaced real structure (cascade, carry automaton, sr boundary). So probe other twists.
Each twists a different part of the collision problem. Deterministic sampling, full N=32.

## Twist 1 — coordinates (XOR vs modular-difference): NEGATIVE
In modular-difference coords every modular add is exactly linear (carries vanish); the
nonlinearity moves onto Σ/σ. Tested on the message schedule (XOR linearizes its 2 σ's, modular
linearizes its 3 adds). Averaged over random 1-bit perturbations: **XOR 96 / MOD 98 / HYBRID 98
determined bits out of 512** — both ~19% linear, and a per-round best-of-both hybrid gains
**0%**. Neither coordinate linearizes the schedule meaningfully more; mixing doesn't help.
(A bit-0/LSB perturbation gives a misleading "complementarity"; it does not survive averaging.)
The MSB-kernel fact "coordinates agree at MSB" does NOT generalize to a coordinate advantage.

## Twist 2 — operation (which addition holds the resistance): NEGATIVE
Linearized (carries→XOR) one modular-addition site at a time (T1 5-op, T2 2-op, a=T1+T2,
e=d+T1) and measured determined output-diff bits and spontaneous-collision rate at R=3,4,8.
**Every site is identical to the all-modular baseline** (74/256 at R=3, 10/256 at R=4, HW 128
at R=8). **No single addition is load-bearing** — SHA-256's collision resistance is robustly
*distributed* across the carries; you cannot collapse it by linearizing any one addition.

## Twist 3 — direction of time (forward vs backward diffusion): STRONG POSITIVE
SHA-256 rounds are invertible (inverse verified on 1000 cases). From a 1-bit difference:

| metric | forward | backward |
|---|---|---|
| HW at round 3 | 42.2 | 19.2 (**ratio 2.19×**) |
| rounds to half-diffuse (HW=64) | 4 | **6** (+2) |
| rounds to HW=100 | 6 | **8** (+2) |

**SHA-256 diffuses ~2× faster forward than backward** in the early rounds (ratio 1.8–2.2× over
rounds 2–5). The backward direction is the **soft side** — differences stay localized ~2 rounds
longer. Localizing further: backward diffusion @round 4 by which register holds the initial
1-bit difference —

```
  h: 18.4   g: 24.2   e: 25.0   a: 32.3   d: 34.4   f: 38.1   c: 43.6   b: 65.2
```

**A difference placed in register h, propagated backward, stays ~3.5× more localized than the
worst register (b).** Structurally h is the last register recovered by the inverse round, so it
spreads backward slowest.

## Why it matters / what to do
This quantifies, for the first time here, a **directional asymmetry** in a function usually
treated as symmetric, and pinpoints the softest control surface (register h, backward). It
explains *why* the repo's earlier "backward construction" reached N=10/12, and points to a
concrete attack geometry: an **unbalanced meet-in-the-middle** that gives the backward part
MORE rounds (it diffuses slower → more controllable), seeding the controlled difference in h.
The two negatives are also useful: they cleanly close the "magic coordinate" and "single weak
addition" hypotheses.

## Reproduce
```
python3 headline_hunt/twisted_probes/three_twists_v2.py
```
