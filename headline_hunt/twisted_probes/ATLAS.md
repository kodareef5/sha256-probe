---
date: 2026-06-09
status: ATLAS — 11-twist synthesis
author: subagent (fable session)
evidence_level: EVIDENCE
title: "A Structural Atlas of SHA-256 Collision Resistance (11 twists)"
---

# A Structural Atlas of SHA-256 Collision Resistance (11 twists)

Eleven "twisted-constraint" micro-experiments, each deliberately distorting a
different part of the collision problem (the coordinate system, the operations,
the direction of time, the diffusion spectrum, the carries, the rotations, the
control surface, the slow modes, the linear distance, the schedule coupling, the
deterministic corridor) and measuring where SHA-256's collision resistance
actually lives. Methods are deterministic avalanche / greedy-local-collision /
determinism-counting probes on full N=32 words using the verified `lib/sha256`
round and its checked inverse. Source memos: the seven `20260609_*.md` files plus
`20260609_three_twists_results.md` and `20260609_fresh_batch_results.md` in this
folder; every twist is reproducible from the script named in its memo.

## Executive summary — the unified picture

SHA-256's collision resistance is **carry-dominated**: under both an avalanche
lens (Twist 5: carries drop diffusion by 25.5 vs 14.5 for Ch/Maj, 1.76x) and a
sharper determinism lens (Twist 9: removing carries unlocks +48.4 determinism
points at R=4 vs +4.2 for both Boolean functions, ~11x), the modular-addition
carries — not the famous Ch/Maj nonlinearity — carry the resistance. That
resistance is **redundantly distributed**: no single coordinate system linearizes
it (Twist 1), no single addition is load-bearing (Twist 2), and no richer
multi-bit "resonant" slow mode beats the trivial single bit (Twist 8). The
function is **not symmetric in time** — it diffuses ~2x faster forward than
backward (Twist 3), with register b (forward) and register h (backward) the
time-reversal-dual slow extremes (Twist 4). But this asymmetry is **not
exploitable**, because the **softness and the control leverage live in different
places**: forward (the only direction real message-modification attacks run)
diffusion-softness and controllability are essentially uncorrelated (Twist 7,
corr +0.06), the most-steerable register (h) is a *fast* diffuser, and the
slow+steerable spot exists only backward where control is intrinsically weak. And
when you couple the state-difference search to the real message-schedule freedom,
**re-injection through the expansion closes the gap** (Twist 10: sustain collapses
from the uncoupled 6.59 rounds to ~1 round). The design constants are **tuned but
generic** — SHA's rotations beat naive ~2x but a generic wide-spread set nearly
matches, so spread matters, not the magic numbers (Twist 6). And the
deterministic / MSB structure that motivates the repo's kernels is **broad but
only ~1 round deep** before saturating (Twist 11: 92.3% per-bit determinism at R1,
50% floor by R3, the full-determinism corridor exactly one round wide).

Net: SHA-256 is **balanced against greedy/local steering** because every soft
direction is either un-pluckable, mislocated relative to control, or shallow. This
is a *structural-understanding* contribution — a unified map of where resistance
lives and why each apparent weakness is neutralized — **not an attack.** It
validates the repo's historical carry-focus and explains *why* the function holds.

## Table of all 11 twists

| # | Twist axis (what was distorted) | Headline finding | Sign | What it closed / established |
|---|---|---|---|---|
| 1 | **Coordinates** (XOR vs modular-difference) | Both ~19% linear on the schedule (XOR 96 / MOD 98 of 512 determined bits); best-of-both hybrid gains **0%** | NEG | Closes the "magic coordinate" hypothesis; MSB coord-agreement does not generalize |
| 2 | **Operation** (which single add is load-bearing) | Linearizing any one add (T1, T2, a=T1+T2, e=d+T1) = identical to all-modular baseline at R=3,4,8 | NEG | Closes "single weak knot"; resistance is distributed across carries |
| 3 | **Direction of time** (fwd vs bwd diffusion) | Backward diffuses ~2x slower (ratio 2.19x @R3); backward buys +2 rounds to half-diffusion | POS | Establishes a real directional asymmetry; the follow-up shows it's NOT exploitable (control favors forward) |
| 4 | **Diffusion spectrum** (slowest input bit) | Register b high bits slowest (b[31]=30.1) vs e fastest (107.8) @R4 — **3.6x spread**; b/h are time-reversal-dual slow extremes | POS | Pinpoints the slow direction; b far from T1, e feeds Σ1+Ch |
| 5 | **Carries vs booleans** (where resistance lives) | Carries contribute MORE diffusion (drop 25.5) than Ch/Maj (drop 14.5) | POS | **Validates carry-focus**; combined with #2, carries dominate *and* are redundant |
| 6 | **Rotation tuning** | SHA's rotations ~2x better than naive but a generic wide-spread set nearly matches (66.6 vs 69.4) | POS/NEG | Spread matters, not the nothing-up-my-sleeve constants (state Σ only) |
| 7 | **Controllability spectrum** | h is the message-control leverage point both ways (fwd ~6.6 / bwd ~3.6 rounds); **forward corr(diffusion,control)=+0.06**, h is a FAST diffuser; bwd corr −0.97 but bwd leverage weak | NEG | Closes the "slow+steerable grail" in the strong direction — the two asymmetries cancel |
| 8 | **Slow-mode eigen-difference** | b[31] is a strict local & global diffusion minimum; no richer slow mode; diffusion additive in bits; 3.6x spread collapses to 1.47x by R6 | NEG | Closes "rich slow-mode" door; diffusion is generic, saturates by R6 |
| 9 | **Linear distance** | Best affine approx Ch~g, Maj~a^b^c (agreement 0.75); nonlinearity budget carries +48.4 ≫ Ch +4.2 ≫ Maj ~0 (~11x carry dominance) | POS | Sharpens #5; within booleans **Ch ≫ Maj** (Maj near-useless); carries are the floor |
| 10 | **Schedule-coupled local collision** | Coupling state-diff search to schedule difference freedom HURTS: sustain ~1 round vs uncoupled 6.59; σ1's W[i-2] re-injection collapses the trail; MSB does not win | NEG | **Closes** the avenue #8 & #11 flagged — the message expansion is the binding constraint |
| 11 | **Prob-1 corridor** | Per-bit determinism 92.3% @R1 → 50% floor by R3; MSB channel real (b31 247/256 avg); max prob-1 differential MSB{f,g} (4 flipped bits), 0% by R6; corridor exactly 1 round wide | POS/NEG | Quantifies the MSB-kernel rationale; the "free" structure is broad but one-round-deep |

## Three recurring walls

Across all 11 twists, every apparent soft spot runs into one of three walls. They
are why no twist became an attack lead.

**(a) Carry-dominance is real, but distributed and un-pluckable.** The carries —
not Ch/Maj — are the dominant source of both diffusion (Twist 5) and irreducible
nonlinearity/determinism-killing (Twist 9, ~11x over the booleans). But you cannot
collapse them: no single addition is load-bearing (Twist 2), no coordinate change
linearizes them (Twist 1), and no structured multi-bit difference resonates
against them — diffusion is additive in active bits, so richer differences buy
*faster* mixing, not slower (Twist 8). The resistance is collectively and
redundantly held by 64 rounds of carry chains. There is no knot to cut.

**(b) Slow-diffusion ≠ exploitable, because control leverage is elsewhere.** SHA
does have a genuinely soft passive direction — backward (Twist 3), seeded in
register b/h (Twist 4), with b[31] the strict slow-mode minimum (Twist 8). But
passive softness is the wrong metric: attacks need *control leverage* (how well a
chosen low-weight message difference cancels the trail). Forward — the direction
real attacks run — diffusion and controllability are uncorrelated (Twist 7, corr
+0.06), and the one highly-steerable register, h, is among the *fastest*
diffusers. The slow+steerable grail exists only backward (corr −0.97, h the joint
extreme), the direction where the message barely steers anything (~3.6 controlled
rounds). The two asymmetries cancel by construction: SHA offers no register that
is simultaneously slow-diffusing and steerable in the strong direction.

**(c) Every deterministic / controllable structure is ~1–6 rounds deep, then
saturates.** Whatever surface you pick, the usable structure is shallow. The
prob-1 corridor is exactly 1 round wide and gone by R6 (Twist 11). The diffusion
slow/fast spread collapses 3.6x → 1.47x by R6 (Twist 8). Determinism decays
geometrically 92%→72%→50% over R1–R3 and to 0 by R8 (Twists 9, 11). The uncoupled
greedy control trail sustains ~6.6 rounds and richer 2-bit control adds only ~+1
(Twist 7). And once coupled to the real schedule, even that drops to ~1 round
(Twist 10). Nothing usable survives the handful of rounds it would take to matter
over SHA-256's 64.

## What would change the picture

Two independent agents (and Twists 8 and 11) flagged the same single genuinely-
untested coupling: **state-difference structure + message-schedule difference
freedom**, run together rather than either in isolation. That was the one place
"slow + multi-round" or "deterministic + multi-round" could plausibly meet — the
prior twists all held the message common (state-only) or gave the attacker
unlimited per-round freedom (schedule-uncoupled fantasy). **Twist 10 tested it
directly and closed it harder:** coupling the searches shortens the controllable
thin trail by ~5.6 rounds (6.59 → ~1), because the schedule recurrence re-injects
the difference at round 16 and *amplifies* it (1 bit → ~16 bits/word via σ0/σ1
fan-out) exactly when message freedom runs out. The message expansion is the
binding constraint, and coupling to it hurts rather than helps.

So a real breakthrough would have to look like something none of the 11 found: a
**multi-round corridor that is simultaneously (deterministic OR controllable) AND
slow**, surviving meaningfully past R≈6 either as a persistent prob-1 channel or
as a sustained thin local-collision trail under *real* (16-input-word, schedule-
determined) message freedom. Concretely, the open follow-up flagged by Twist 10
is a structured/ILP search over multi-word input-difference vectors `W[0..15]`
whose expanded schedule difference *cancels* the re-injection for several rounds
(sustain ≫ 1 at HW≤8) — the single-bit and MSB-pair searches found no such vector.
Absent that, the atlas's verdict stands.

## Honest framing

This is a **structural-understanding** contribution, not an attack. Its value is
the unified map: nobody had assembled where SHA-256's collision resistance lives
(carries, redundantly), why the obvious soft directions don't pay (control is
mislocated, structure is shallow, the schedule re-injects), and how the design
choices (tuned-but-generic rotations, MSB-deterministic-but-shallow corridor)
fit. Every individual twist's verdict is "not an attack lead"; their *combination*
is a coherent explanation of *why* SHA-256 is balanced against greedy and local
steering, and it independently re-derives and quantifies the repo's standing
carry-focus and MSB-kernel rationale from eleven orthogonal directions. All
findings are EVIDENCE-level (deterministic sampling probes, full N=32 words, on
verified `lib/sha256` primitives), reduced-to-round-function in scope, and should
not be over-generalized as "properties of SHA-256" beyond the round-function /
schedule structure actually probed.
