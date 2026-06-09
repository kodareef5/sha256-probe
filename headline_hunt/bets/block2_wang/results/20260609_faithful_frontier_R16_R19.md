---
date: 2026-06-09
bet: block2_wang
status: faithful CV-pinned frontier completed; ~18 wall confirmed target-independent; kill #1 still NOT fired
author: macbook-claude (fable model test)
evidence_level: EVIDENCE (faithful R=16 SAT, R>=18 timeout; >18 solver-limited, not proven infeasible)
---

# Direction C: completing the faithful (CV-pinned) absorber frontier the 2026-05-30 memo left open

## Context

The 2026-05-30 feed-forward memo (`20260530_feedforward_faithful_absorber.md`) corrected two
real methodology bugs in the bet's "18-round absorber" (wrong target ΔC=0 vs the Davies-Meyer
ΔC=−Δcv; wrong input — working-state HW 35 vs the post-feed-forward chaining residual HW 95).
It found the proxy and the faithful target wall at the same ~18 place, but left the faithful
**CV-pinned** frontier incomplete (table had R=18 "≈ harder", R=20 timeout, R=24 untested).
This run pins the exact wall on the CORRECT condition.

## Faithful CV-pinned frontier (this run)

Block-1 witness m0=0x17149975 → CV1,CV2 pinned; **post-FF residual HW=95**; target H1==H2.
`encoders/absorber_pinned.py`, kissat:

| R | result | wall |
|---|---|---|
| 16 | **SAT** | 0.12 s |
| 18 | not solved | timeout 120 s |
| 19 | not solved | timeout 240 s |

Sanity: R=16 is instant SAT (tool validated), then a sharp cliff — R=18 and R=19 do not solve
even on the faithful encoder. This **completes the memo's frontier** and confirms the wall sits
at ~18 for the *correct* feed-forward + pinned-CV condition, the same neighborhood as the
ΔC=0 proxy (R=18 SAT 5 s / R=19 timeout). The faithful (pinned) encoder is strictly harder
than the proxy — R=18, trivial on the proxy, does not solve in 120 s here.

## What this settles, and what it doesn't

**Settles (confirmation):** the ~18 wall is *target-independent* — it is not an artifact of
the bet's earlier wrong target/input. Across the proxy target, the feed-forward target, free-CV
and pinned-CV, tailored-encoding levers (difference-window, path-pinning), the wall does not
move. The structural cause is the one the bet already identified: past ~16-18 rounds the
block-2 message schedule re-injects the W0..15 differences into W16+, and a **dense** input
difference (post-FF HW ≥ 66 best-case, 95 here) admits no sparse characteristic to re-cancel
them. This matches the single-block `linear_lever` sr=60 result — both SHA-256 collision walls
are structural and robust to the techniques tried.

**Does NOT settle:** whether a >18 absorber *exists*. Every R≥18 probe is a **timeout**, never
a solver-returned UNSAT, and the engine's arc-consistency finds **no contradiction** at R=18/19
(0 forced bits). So R≥19 is **solver-limited, not proven-infeasible**. **Kill #1 stays unfired**
(its trigger needs a decisive unreached gate after a real search effort; a timeout is not that).

## The one unexploited lever, and why it's low-conviction

The only thing that could move the wall is a **sparse post-FF residual** (HW ≤ 16-24, Wang's
threshold). The corpus floor is post-FF HW=66 (working-state floor ~35, which the feed-forward
densifies). Reaching ≤24 would require a block-1 near-collision with working-HW well below the
proven ~35 floor (R63.1/R63.3 + dd63=dh63=0) — very unlikely. The remaining structural lever is
the **connection** question: steer block-1's free W[57..60] to land a sparse post-FF residual.
Gated on beating the HW floor; low conviction.

## Recommendation

Pause block2_wang on its standing, honest deliverable (Wang trail engine + control-validated
9-step local collision + oracle-confirmed 18-round absorber, now with the faithful frontier
pinned). The >18 gate is solver-limited but structurally explained; grinding the naive/faithful
CNF further has predictable timeouts. Reopen only on the connection lever (a sparse post-FF
residual) or a portfolio/long-compute SAT effort meeting kill #1's "real search effort" bar.

## Reproduce
```
cd headline_hunt/bets/block2_wang/encoders
python3 absorber_pinned.py --info                 # post-FF residual HW=95
python3 absorber_pinned.py --R 16 --timeout 120   # SAT 0.12s
python3 absorber_pinned.py --R 18 --timeout 120   # timeout
```
