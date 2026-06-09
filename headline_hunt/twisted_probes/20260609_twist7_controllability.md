---
date: 2026-06-09
status: Twist 7 — controllability spectrum mapped; h is the leverage register in both directions; no slow-diff+high-ctrl grail in the strong (forward) direction
author: subagent (fable session)
evidence_level: EVIDENCE (deterministic greedy local-collision, N=32 full word, R=12, K=600/cell, lib/sha256 round + verified inverse)
---

# Twist 7 — the controllability spectrum (the attack-relevant dual of diffusion)

## Motivation
The recurring lesson from Twists 3–6: passive *diffusion*-softness is NOT exploitable; the
attack-relevant quantity is *control leverage* — how well a chosen low-weight MESSAGE difference
`dW` cancels the state-difference trail round after round. Twist 3 showed control is ~2× stronger
forward and that register **h** is the leverage point. Here we map the full spectrum (8 seed
registers × 2 directions) and cross-reference the Twist 4 diffusion spectrum to hunt the holy
grail: a register that is BOTH slow-diffusing AND highly controllable.

Method: seed a 1-bit diff in register `R_seed`; each round inject the best `dW ∈ {0} ∪ {32
single-bit flips}` to minimize the resulting state-diff HW; count leading rounds kept `HW ≤ T`.
R=12, K=600 samples/cell, deterministic (seed 20260609). Kernel convention matches Twist 3
(fwd uses `K[r]`; the r-th inverse step consumes `K[R-1-r]`).

## 1. Controllability spectrum (single-bit `dW`, mean leading rounds `HW ≤ 8`)

| seed reg | FORWARD ctrl | BACKWARD ctrl |
|---|---|---|
| a | 0.90 | 2.65 |
| b | 2.17 | 0.21 |
| c | 1.91 | 1.07 |
| d | 1.31 | 1.99 |
| e | **0.36** (min) | 2.71 |
| f | 4.34 | 1.88 |
| g | 6.19 | 2.82 |
| h | **6.59** (max) | **3.58** (max) |

(Full T∈{4,8,16} table reproduced by the script.)

- **Forward**: control rises monotonically along the tail of the register-shift chain
  `f(4.34) < g(6.19) < h(6.59)` and is lowest in **e (0.36)**. Structural reason: forward, W
  enters T1, which immediately drives both new a′,e′; registers g and h are the *last* recovered
  /closest to a free-W cancellation in the early greedy trail, so a single-bit `dW` cancels them
  best. e is the worst — it feeds Σ1/Ch and explodes instantly (consistent with e being the
  fastest *diffuser* in Twist 4).
- **Backward**: **h is again the most controllable (3.58)** and **b the least (0.21)** — exactly
  the Twist 3 finding (W enters h's recovery directly backward; b is untouched by W).
- **h is the single leverage register in BOTH directions.** Forward control (~6.6 rounds) is
  ~1.8× the backward control (~3.6), re-confirming the Twist 3 "control favors forward" asymmetry.

## 2. Cross-reference with diffusion — is there a slow-diff + high-ctrl grail?

Diffusion = avalanche HW @ R=4 (Twist 4), re-derived here per direction; controllability = rounds@T≤8.

| | FORWARD | BACKWARD |
|---|---|---|
| Pearson corr(diffusion, controllability) over 8 regs | **+0.06** (≈ none) | **−0.97** (near-perfect anti-correlation) |

- **Forward (the strong, attack-relevant direction): correlation ≈ 0.** Diffusion-softness and
  controllability are essentially *independent* forward. Forward, the most-controllable register
  h is one of the *fastest* diffusers (HW 87.6) — the opposite of a soft spot. The slowest forward
  diffuser, **b (37.8)**, has only middling control (2.17). **There is NO forward register that is
  both slow-diffusing and highly controllable.** The naive grail does not exist in the direction
  that matters.
- **Backward: corr −0.97.** Slow-diffusing backward ⇒ highly controllable backward, cleanly — and
  **h is the joint extreme** (slowest backward diffuser HW 18.4 AND most controllable, 3.58). So a
  real slow-diff+high-ctrl spot DOES exist — but only *backward*, the *weak-leverage* direction,
  where even the best register sustains just ~3.6 controlled rounds. The grail is in the wrong room.

(The script's per-row "holy grail candidate" tags are median-split labels and include several
near-median coincidences; the load-bearing signal is the two correlations and h's joint-extreme
status backward.)

## 3. Does richer (2-bit) control materially extend the trail?

`{0} ∪ single-bit ∪ 200 sampled 2-bit` flips (set size 33 → 233), paired seeds vs part 1:

| dir | reg | 1-bit `T≤8` | 2-bit `T≤8` | Δ | 1-bit `T≤16` | 2-bit `T≤16` | Δ |
|---|---|---|---|---|---|---|---|
| fwd | h | 6.59 | 7.53 | **+0.94** | 6.82 | 7.81 | +0.99 |
| bwd | h | 3.58 | 4.17 | +0.59 | 4.80 | 5.28 | +0.48 |

Richer control gives a consistent **~+1 round forward / +0.5 backward (~14%/16%)** — a real but
*incremental* gain, not a regime change. The trail length is set by the round function's
intrinsic per-round cancellation budget, not by the poverty of a single-bit dictionary; doubling
the dictionary buys a fraction of a round. (A full 2-bit set — 528 candidates — would likely add
a little more, but the diminishing-returns shape is already clear.)

## Verdict — exploitability

- **Standout:** register **h** is the unambiguous control-leverage point in both directions
  (fwd 6.59, bwd 3.58 rounds @T≤8); the forward control gradient is `e ≪ a,c,d ≲ b < f < g < h`.
- **Holy grail?** **No — not where it would help.** Forward (the only direction real
  message-modification attacks run), diffusion and controllability are *uncorrelated* (+0.06), and
  the most-controllable register h is a *fast* diffuser. A genuine slow-diff+high-ctrl spot exists
  only *backward* (corr −0.97, h the joint extreme), but backward control is intrinsically weak
  (~3.6 rounds) because W barely steers the inverse. The two asymmetries cancel — the same
  balance Twist 3 found, now mapped register-by-register: **SHA-256 offers no register that is
  simultaneously soft (slow-diffusing) and steerable in the strong direction.**
- **Richer control** extends the trail only ~14% (single→single+2bit). The ceiling is the round
  function's cancellation budget, not the dW dictionary.

Honest assessment: **not an attack lead.** Twist 7 confirms and quantifies *why* — the soft spot
and the steerable spot are in different directions, so you can never put a difference somewhere
that is both hard to diffuse and easy to control forward. This is a concrete structural reason
SHA-256 resists greedy local-collision steering, and it sharpens the prior twists into a single
statement: control leverage (forward, register h) is the real attack surface, and it is *not*
co-located with diffusion softness.

## Reproduce
```
python3 headline_hunt/twisted_probes/twist7_controllability.py
```
