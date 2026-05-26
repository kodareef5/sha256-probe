---
date: 2026-05-26
bet: block2_wang
status: CONTROL VALIDATED
author: macbook-claude
evidence_level: VERIFIED (independent reproduction of a known result, oracle cross-checked)
---

# Wang trail engine reproduces the known SHA-256 9-step local collision (control)

## Why this matters

The block2_wang bet needs a real differential-trail engine (generalized conditions +
message modification), not the exact_diff-pin probe that was FORWARD_BROKEN
(`20260525_block2_absorber_exactdiff_negative.md`). I built one incrementally
(`encoders/wang_trail_engine.py` + `encoders/wang_search.py`); this memo records the
**control validation**: before trusting the engine on the open block-2 question, it must
reproduce a *known* SHA-256 cryptanalytic result. It does.

## The engine (commits 5e18885b, 71e86e8f, 14c430a2, e8ea725d, 77e400b1, 8fc05e0a)

- Generalized (de Cannière–Rechberger) bit-conditions as 4-bit masks over pair-values (x,x*).
- Forward propagation through Σ/σ (XOR-of-rotations), Ch, Maj, and **carry-aware modular
  addition** (a per-bit full-adder transducer carrying the carry-pair condition).
- Backward / arc-consistency refinement for every op (`refine_*`), with carry-chain refine.
- A bit-level **constraint network** (`wang_search.Net`) wiring a full multi-round
  characteristic, with a worklist propagate-to-fixpoint.
- A **guess-and-determine search** (`run_search`) on top of propagate(): branch on the
  lowest-entropy undetermined bit, refine, backtrack on contradiction.

Each layer is self-tested against the `lib.sha256` concrete oracle (no SHA-256
reimplementation): 6000 modular-add cross-checks, 3000+500 round/multi-round trails as
fixpoints, 200/200 planted contradictions caught, 120 oracle-confirmed planted-diff searches.

## Control experiment

Inject a **single-bit XOR difference in message word W0**, leave the correction words
W1..W_{R-1} as **free** message words (full message modification), pin the input state to
no-difference and require the state difference to **vanish after R rounds** (a local
collision). Search for the correcting differences; oracle-recheck any solution.

```
W0 disturbance, free corrections, require state collision @ round R:
  R = 1..8 :  INFEASIBLE   (contradiction by propagation alone, before any branching)
  R = 9    :  COLLISION    active words W0..W8, oracle_ok=True, ~580 search nodes
  R = 10..15: COLLISION    (longer spans also realizable; oracle_ok=True)
  R = 16   :  search node-budget exceeded (heuristic, not a feasibility statement)
```

Robust across disturbance-bit positions (tested bits 0,5,8,15,20,31): **always INFEASIBLE
at R≤8, COLLISION at R=9**, with the active correction words always spanning W0..W8 (the
9-step endpoints W0 and W8 are always active; some interior corrections are optional
depending on the bit). Sanity: the trivial all-zero collision is FEASIBLE at R=9, so the
INFEASIBLE verdicts are not a degenerate always-contradict bug.

## Result — independent reproduction of a known fact

The minimal span of a single-message-word SHA-256 local collision is **9 steps** (W_i..W_{i+8})
— the standard local collision used throughout SHA-2 cryptanalysis (Nikolić–Biryukov,
Sanadhya–Sarkar, Mendel et al.). The engine derives this from scratch:

1. It **proves** (by sound arc-consistency, no search) that ≤8 rounds is impossible.
2. It **constructs** a 9-round collision and the concrete `lib.sha256` oracle confirms the
   two messages collide in the state after 9 rounds.

This is a real control: a falsifiable, well-known threshold, reproduced exactly, with the
solution cross-checked against an independent oracle. It validates the engine end-to-end —
soundness (no false rejection of a real trail), completeness enough to *find* the collision,
and correct message-modification search.

## Honest scope and what's next

- This control uses **free** message words (the local-collision literature's setting). The
  block-2 absorber question adds the **message schedule** constraint for rounds ≥16
  (W_t = σ1(W_{t-2}) + W_{t-7} + σ0(W_{t-15}) + W_{t-16}), which the engine does not yet
  encode. That schedule coupling is exactly block2_wang's hard core (cf. the W44↔init2
  coupling in `mitm_residue`).
- The kill_criterion (#1) is an **absorber trail > 18 rounds** that cancels the *specific*
  block-1 residual (e.g. the bit13 HW35 record), not a single-bit disturbance. Next
  increment [6]: add the message-schedule constraints, pin ≥5 residual clusters as the input
  difference, target a zero (or low-weight) output difference, and report the best achievable
  absorber-round count vs the >18 gate. The search node-budget already strains at R=16 with
  free words; with schedule constraints + a dense input difference it may blow up — if so,
  that combinatorial hardness is itself the bet's answer and will be recorded as such.

## Reproduce

```
python3 headline_hunt/bets/block2_wang/encoders/wang_search.py   # runs all self-tests incl. control
python3 -c "import sys; sys.path.insert(0,'headline_hunt/bets/block2_wang/encoders'); \
            from wang_search import local_collision_search; \
            print(local_collision_search(8,8)['status'], local_collision_search(9,8)['status'])"
# -> INFEASIBLE COLLISION
```
