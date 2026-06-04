# Phase 2 — decisive sr=60 probe: VERDICT (2026-05-30)

Bet: `linear_lever_gaps`. Owner: macbook-claude. Outcome: **NEGATIVE — kill #2 fires.**

## TL;DR

The linear-lever idea does **not** beat the σ1 wall. Replacing the σ1 (t-2)
enforcement lever with full-rank linear (t-7) levers — which decouples the boundary
words {61,62,63} in principle — makes the SAT instance **strictly harder**, because
the linear lever structurally *requires* a deeper `tail_start` (more bit-blasted
nonlinear rounds), and that cost dominates any decoupling benefit. The sr=61 wall is
**not** an artifact of the lever choice; it is intrinsic. The adversarial review's
prediction (tail-cost + zero-slack dominate, lever-independent) is confirmed.

Per the bet's scope (chase SAT, fail-fast): no SAT at sr>59, no advantage over the
σ1 baseline → KILL and pivot.

## What was validated first (milestone, independent of the bet outcome)

The configurable encoder (`encoders/lever_gap_encoder.py`) reproduced the **paper's
"92% broken" sr=59 result** from scratch: top-block σ1 sr=59 (free {57..61}) solved
in **208s (seed 1) / 252s (seed 5)**, oracle-verified as a genuine sr=59 collision
(hash `719ad5ee…`, all 8 registers collide, exactly 43 schedule equations hold). The
encoder also passed a 6/6 validation gate incl. self-consistency on the deep
`tail_start=54` path. So every negative below is about the *idea*, not a tooling bug,
and the candidate (m17149975) is demonstrably tractable at sr=59.

## The evidence

All on candidate `m17149975 / fill ff / MSB kernel`, kissat 4.0.4 (+ cadical 5).

| config | free positions | tail | holds boundary | result |
|---|---|---|---|---|
| **top-block σ1 sr=59** (paper) | {57,58,59,60,61} | 7r | {62,63} | **SAT 208s / 252s** ✓ |
| 3-deep-linear sr=60 (decisive) | {54,55,56,57} | 10r | {61,62,63} | 6× TIMEOUT @ 1h |
| 3-deep-linear sr=59 | {54,55,56,57,58} | 10r | {61,62,63} | 2× TIMEOUT @ 900s |
| minimal sr=60, **hold W57** | {56,58,59,60} | 8r | {57,61,62,63} | **UNSAT 8–14s** |
| minimal sr=60, **hold W60** | {56,57,58,59} | 8r | {60,61,62,63} | TIMEOUT @ 600s |
| minimal sr=59 keep-triggers | {56,57,58,59,60} | 8r | {61,62,63} | 2× TIMEOUT @ 900s |
| keep-triggers sr=60 | {56,57,59,60} | 8r | {58,61,62,63} | TIMEOUT (expected) |

> The minimal sr=59 row is the sharpest single result: it keeps BOTH triggers free,
> has MORE freedom than any sr=60 config, uses only ONE linear lever (8-round tail) —
> yet times out where the σ1 top-block sr=59 (which frees W[61] instead of holding it)
> solves in 208s. Holding all of {61,62,63} is the hard part, and the linear lever's
> required deeper tail makes it worse, not better. Lever-independent confirmation.

## Why it fails (three independent reasons, all confirmed)

1. **Deep-tail SAT cost dominates.** The σ1 top-block sr=59 (7-round tail) solves in
   ~208s. The *same* sr=59 with linear levers (10-round tail, free {54..58}) — which
   has MORE freedom — times out at 900s (>4× longer, no SAT). The extra bit-blasted
   nonlinear rounds (54,55,56) swamp the decoupling benefit. This is intrinsic: a t-7
   linear lever for W[63] forces freeing W[56] (tail≥8); t-16 forces W[47] (tail≥17).
   You cannot use linear levers for the boundary without a deeper tail.

2. **Cascade triggers must stay free (counting wall).** The sr=60 collision needs the
   a-path trigger **W[57]** and e-path trigger **W[60]** free (cert anatomy: dW57 fires
   cascade-1, dW60 fires cascade-2). Holding W[57] → provable **UNSAT in 8s** (the
   a-cascade breaks cleanly). So any sr=k config must spend free words on: 2 triggers
   + ≥2 boundary levers = **≥4 free words = sr≤60**. The lever *kind* (σ1 vs linear)
   does not reduce this count. sr=61 (3 free) cannot fit 2 triggers + boundary levers.

3. **Zero-slack is unchanged.** As the adversarial review noted, the linear lever
   reshapes the freedom but does not add any (still 4 free words × 2 msgs = 256 bits =
   the collision condition). σ1 being full-rank at N=32 (Phase 0) means there was no
   image-restriction to escape either. So there was never a mechanism by which the
   lever could reduce the search; only the tail-depth penalty, which is adverse.

## Conclusion

The sr=61 wall documented in `writeups/sr61_impossibility_argument.md` and
`sr60_sr61_boundary_proof.md` (Thm 5) is **lever-independent**. The novel linear-lever
gap placement, fully implemented and tested, provides no path past it — it is strictly
worse than the σ1 cascade at every sr level tested. Kill #2 fires.

**Salvage value:** (a) a configurable, validated gap-placement encoder reusable for any
future free-position/lever experiment; (b) an independent general verifier; (c) the
clean structural finding that **W[57]/W[60] trigger-freedom is a hard counting
constraint** capping cascade-style gap placement at sr=60 regardless of lever — a sharper
statement of the wall than "σ1 conflicts," worth folding into the boundary writeup.

## Disposition

Move bet to `graveyard/closed_bets/`. Pivot to next thread (candidate: block2_wang
two-block connection). All 11 runs logged in `registry/runs.jsonl`.
