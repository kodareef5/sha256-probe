---
date: 2026-06-09
author: subagent (fable session)
evidence_level: EVIDENCE
twist: 10
title: "Schedule-coupled local-collision length — message-expansion re-injection bounds the thin trail to ~1 round"
script: headline_hunt/twisted_probes/twist10_schedule_coupled.py
---

# Twist 10 — schedule-coupled local-collision length (the most attack-relevant twist)

## Question
Twists 3–8 measured "controllability" by letting the per-round message word `W`
be **independent** across the two messages: a fresh low-weight difference `dW`
was injected EVERY round, chosen greedily to cancel the state-diff trail
(Twist 7: register **h** sustains **6.59** forward rounds at `HW≤8`). That is a
schedule-**uncoupled** fantasy attacker with unlimited per-round message freedom.

A REAL local collision has no such freedom. The attacker picks ONE difference in
the 16 input words `W[0..15]`; the schedule recurrence
`W[i] = σ1(W[i-2]) + W[i-7] + σ0(W[i-15]) + W[i-16]` then **determines** the
difference in every later word, **re-injecting** it (notably through `σ1(W[i-2])`).
This re-injection is exactly why SHA-2 local collisions are bounded (~9 rounds)
and why the message expansion is the modern bottleneck.

**Twist 10:** two messages differing in the input words, both schedules expanded,
both run through the compression rounds from a common random start state. We sweep
which input word and which bit to perturb (single-bit, MSB, MSB-pairs), measure the
state-diff Hamming-weight trail, and ask: does schedule coupling let a thin trail
run **longer** than the uncoupled greedy 6.59, or does re-injection **hurt**?

Method: full N=32 words, R=32 rounds, common start state, deterministic (seed
20260609), K=300–400 samples/cell. Verified `fwd` round + schedule recurrence
copied exactly from `twist7_controllability.py` / `fresh_batch.py`. Runtime ~35 s.

## The metric that matters (and the artifact it removes)
A difference seeded in input word `w` produces **zero** state-diff for the first
`w` rounds simply because `W[w]` has not been consumed yet. So the naive "leading
run kept `HW≤T` from round 0" is dominated by **entry latency**, not by any
sustain property — word-15 trivially "lasts 16 rounds" because its disturbance
hasn't entered. We therefore report **SUSTAIN-after-entry**: consecutive thin
rounds *starting at the entry round* (first round with nonzero state-diff). That
is the genuine local-collision span.

## Key numbers

| quantity | value |
|---|---|
| **Schedule-coupled SUSTAIN @ `HW≤8`** (best over all word×bit) | **1.00 round** |
| Schedule-coupled SUSTAIN @ `HW≤16` (best) | ~1.25 rounds |
| Schedule-coupled SUSTAIN @ `HW≤32` (best) | ~2.0 rounds |
| Schedule-**uncoupled** greedy baseline (Twist 7, reg h, fwd) | **6.59 rounds** @ `HW≤8` |
| Textbook SHA-2 local collision (full msg-mod freedom) | ~9 rounds |
| **Δ (coupled − uncoupled)** | **−5.59 rounds → coupling HURTS** |

**Sustain is 1.00 round for EVERY input word and EVERY bit, including the MSB**
(the classic disturbance site where XOR == modular and there is no carry-out).
Once the disturbance enters the state, the trail explodes immediately and
identically:

```
trail at entry, entry+1, ... :  2 → 19 → 48 → 80 → 110 → 126 → 128 → 128 ...
```

i.e. full avalanche (~128 of 256 bits) by entry+5. No input word, no bit, no
MSB-pair `{w1,w2}` does any better — every candidate collapses to the same
explosion. **MSB does not win**; it ties everything else at sustain = 1.

## Why coupling hurts — the re-injection profile (Part 2)
A single-bit input-word difference does not stay single-bit. Mean schedule-diff
HW per word, for an MSB disturbance in `W[0]`:

```
W[0]=1 ... W[16]=1, W[18]≈5, W[20]≈9, W[22]≈16, W[24]≈16, W[26]≈16, W[28..31]≈16
```

The difference **re-injects at round 16** (first expanded word) and the
XOR-difference **expands** from 1 bit toward ~16 bits/word by round ~22, because
each `σ0`/`σ1` application fans a single bit out across three rotate/shift copies
and the modular adds spawn carries. So even if a thin state-diff trail could be
held through the free window, the expansion guarantees a fresh, *heavier*
difference is fed back in starting round 16. This is the message-expansion
bottleneck made concrete.

## The fair test against the ~9-round local collision (Part 4)
The uncoupled greedy gets a free fresh `dW` *every* round forever — not a real
budget. A real attacker only has free message words in `W[0..15]`; rounds 16+ are
schedule-determined. So we **fix** an MSB disturbance in `W[0]` (a real collision
must keep the two messages genuinely different — it is never cancelled away) and
let the attacker greedily use the remaining free input words `W[1..15]` to keep
the trail thin, then hand over to the schedule:

- **In-free-window greedy thin run (`HW≤8`): 1.00 round.** Even *with* the genuine
  free-input budget, a single-bit-per-round correction cannot hold the trail thin,
  because the round-0 disturbance hits both `a′` and `e′` through `T1` and has
  already diffused to `HW≈19` by round 1 — one input word per round touches one
  register and cannot claw a ≥19-bit diff back under 8. Trail sits at ~113 through
  rounds 8–15.
- **Survival past the schedule handover: 0% still `HW≤8` at round 16 / 20 / 24.**
  The locally-corrected segment does not survive message expansion at all.

(Note on a subtlety: if the disturbance is allowed to be *corrected away* in the
free window, the greedy trivially drives the two messages identical — a non-
collision. Requiring the disturbance to be preserved, as a real collision must, is
what produces the 1-round / 0%-survival result.)

## Verdict
**Schedule coupling HURTS — decisively.** The attack-relevant, schedule-coupled
local-collision span is **~1 round at `HW≤8`**, versus 6.59 rounds for the
uncoupled greedy and ~9 for the textbook full-freedom local collision. The two
asymmetries from the prior twists now have a clean joint explanation:

1. **No per-round free `dW`.** The uncoupled 6.59 came from injecting an arbitrary
   fresh single-bit difference every round and from seeding directly in the
   leverage register `h`. Neither is available to a real attacker: the only
   message freedom is in 16 input words, and the disturbance enters wherever the
   schedule puts it (registers `a`/`e` via `T1`), not in `h`.
2. **Re-injection + expansion.** The schedule recurrence brings the difference
   back starting at round 16 and *amplifies* it (1 bit → ~16 bits/word) via the
   `σ0`/`σ1` fan-out — so even a hypothetically thin free-window trail is reseeded
   with a heavier difference exactly when message freedom runs out.

This is a concrete, quantitative restatement of why SHA-2 resists message-
modification collision attacks past a short span: **the message expansion is the
binding constraint, and coupling the state-diff search to it shortens the
controllable thin trail by ~5.6 rounds rather than extending it.** It directly
answers the avenue Twist 8 flagged ("the only remaining place slow + controllable
could meet"): coupling the two does **not** open that door — it closes it harder.

**Not an attack lead.** The honest outcome: the schedule-coupled local collision
is shorter, not longer, than the toy uncoupled control trail, and the MSB
disturbance (classic seed) holds no advantage here — it ties at 1 sustained round.

## What would change the assessment
- A multi-word input-difference vector (not just single-bit / MSB-pairs) whose
  expanded schedule difference *cancels* the re-injection over several rounds —
  i.e. a true correction sequence with sustain meaningfully > 1 at `HW≤8`. The
  small MSB-pair search found none; a larger structured/ILP search over `W[0..15]`
  difference vectors is the next step if one wanted to push this.
- Richer per-round correction (2+ bit `dW`) in the free window lifting the
  in-window sustain above 1 round (Twist 7 showed only ~+1 round even uncoupled).
- Working over a reduced-round / message-expansion-truncated variant where rounds
  16+ stay free (then it reduces to the uncoupled regime by construction).

## Reproduce
```
python3 headline_hunt/twisted_probes/twist10_schedule_coupled.py
```
