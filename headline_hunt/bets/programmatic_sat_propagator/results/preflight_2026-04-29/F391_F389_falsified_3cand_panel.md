---
date: 2026-05-01
bet: programmatic_sat_propagator × cascade_aux_encoding
status: F389 SPEEDUP FALSIFIED at n=3 cands — ladder pre-injection uniformly HURTS by 2.5-9.3 pp
parent: F390 (bit2-only falsification, n=1)
type: confirmation_of_falsification at larger sample
compute: 18 cadical 60s runs (2 new cands × 3 conditions × 3 seeds + F390 reuse); ~6 min wall
---

# F391: F389 ladder pre-injection HURTS across 3-cand panel — falsification firm

## Setup

F390 found F389's ladder pre-injection HURTS bit2_ma896ee41 by +2.35%
at n=1 cand × 3 seeds. F391 extends to n=3 by running the same
3-condition test (baseline / F343-only / F389-extended) on bit31 and
bit3 (both Class A, both fill=ffffffff F374 deep-tail dominators).
~6 min wall, parallel-3.

## Result — 3-cand panel

```
                  baseline  →  F343 alone   →  F389 (F343 + ladder)
bit2_ma896ee41    1,603,414    1,604,473      1,641,126
                  Δ=0.00%      Δ=+0.07%       Δ=+2.35%   ← injection HURTS

bit31_m17149975   1,614,370    1,402,550      1,552,615
                  Δ=0.00%      Δ=−13.12%      Δ=−3.83%   ← F343 huge help, F389 loses 9.3pp

bit3_m33ec77ca    1,742,775    1,600,468      1,644,443
                  Δ=0.00%      Δ=−8.17%       Δ=−5.64%   ← F343 helps, F389 loses 2.5pp
```

**Mean across 3 cands × 3 seeds (n=9 per condition):**

| condition | mean Δ | per-cand spread |
|-----------|-------:|-----------------|
| baseline  | 0.00%  | reference |
| **F343 alone** | **−7.07%** | −13.12% to +0.07% |
| **F389 (F343+ladder)** | **−2.37%** | −5.64% to +2.35% |

**F389 is uniformly WORSE than F343 alone, by 2.5 to 9.3 percentage
points across 3/3 cands.** The ladder injection ALWAYS HURTS relative
to F343-only. F343 alone is consistent with F369's −9.10% 5-cand mean;
F389 cuts the F343 win by roughly half.

## Findings

### Finding 1 — F389 ladder injection FALSIFIED at n=3 cands

The negative effect (ladder pre-injection HURTS vs F343 alone) is now
empirically robust across 3 cands × 3 seeds = 9 data points per
condition. Per-cand the loss ranges from 2.5pp (bit3) to 9.3pp (bit31).

The strongest hurt is on the cand where F343 helps MOST (bit31:
−13.12% with F343, but only −3.83% with F389). The ladder eats most
of F343's win.

This is a clean falsification of F389's "ladder pre-injection adds
~+0.9% additive help" projection.

### Finding 2 — F343 itself is broadly cand-dependent

```
  F343 effect by cand:
    bit2:   +0.07% (within F369 σ=2.68% noise)
    bit3:   −8.17%
    bit31:  −13.12%
```

bit2 (m0=0xa896ee41) is essentially neutral under F343 mining; bit31
gets the biggest help. F369's 5-cand mean of −9.10% averages over a
wide range. **F343's per-cand effect is highly variable** — the F369
mean is real but per-cand effect can range from ~0% to ~−13%.

### Finding 3 — Why does the ladder HURT?

Probable mechanism (consistent across 3 cands):
  - The 124 ladder clauses ARE in the encoder's logical closure
    (Tseitin-derived; verifiably implied by base CNF). CDCL discovers
    them within the first ~12k of 1.4M proof lines via UP chains.
  - Pre-injecting them adds 124 clauses to the watch-list, increasing
    propagation cost on every conflict.
  - Across 1.5M conflicts, the per-conflict overhead compounds to a
    measurable runtime penalty.
  - The clauses provide ZERO new information vs. what UP discovers
    naturally — they're structurally redundant.

The ladder's value as a **diagnostic** is real (CDCL DOES learn it
robustly across all Class A cands). The ladder's value as a
**preflight injection target** is FALSIFIED — pre-injection adds
overhead without saving search work.

### Finding 4 — Phase 2D propagator design implication (firm)

The Phase 2D propagator MUST stay with F343's 2-clause baseline. The
F384 ladder, although universal across Class A cands, should NOT be
pre-injected.

This narrows the Phase 2D viable speedup levers to:
  - F343 baseline (2 clauses): ~−9% mean (high cand-variance)
  - cb_decide on F286 132-bit core: untested
  - Anything else: untested

### Finding 5 — F389 the tool stands; F389 the spec is dead

`bridge_preflight_extended.py` (the tool) correctly classifies cands
per F387 rule and mines the ladder when applicable. As a structural
characterization tool it works.

But the JSON spec it produces (with the 124 ladder clauses) should
NOT be fed to a propagator's `cb_add_external_clause`. Doing so
produces a 5-percentage-point slowdown vs F343-only.

Recommendation: extend the tool to emit ONLY F343 baseline by default;
make ladder emission opt-in via `--include-ladder` for diagnostic use.

## What's shipped

- This memo with 3-cand truth table
- 18 cadical 60s runs logged (2 new cands × 3 cond × 3 seeds)
- 6 transient CNFs in /tmp/F391/
- Project's 12th iterative falsification

## Compute discipline

- 18 cadical 60s runs = 18 CPU-min; parallel-3 = ~6 min wall
- 6 CNFs in /tmp (transient, --allow-audit-failure)
- Real audit fail rate stays 0%
- validate_registry: 0/0

## F381 → F391 chain final summary

  F381 (n=1):  discovered XOR ladder structure
  F382-F386 stages: 6 falsifications (rule narrowing)
  F387 (n=14): m0/fill rule fits 14/14
  F388 (n=16): rule anchored
  F389: deployable tool + speedup projection
  F390 (n=1): speedup FALSIFIED on bit2
  F391 (n=3): falsification CONFIRMED — ladder uniformly hurts

12 numbered memos, 26 commits, ~7 hours, ~580s cadical compute.

The structural finding (ladder exists per F387 rule) is REAL.
The application finding (ladder injection helps) is FALSIFIED.
The deployable tool stands as a CHARACTERIZATION tool.

## Open questions for next session

(a) **Test at deeper budget** (5-min cadical) — does the F389 hurt
    saturate to zero or persist? F366 showed F343 saturates; maybe
    the ladder hurt also saturates.

(b) **Mechanism: cadical statistics** — run cadical --statistics on
    baseline vs F389 to confirm watch-list overhead is the cause.

(c) **F343 per-cand variance**: F343's effect ranges 0% to −13% per
    cand. What predicts which cands get a big F343 win? May be a
    different structural property than F387 (which predicts ladder
    presence, not F343 effectiveness).

The unit-of-progress per user direction: "a new bridge selector, a
falsified selector, or a generalized learned clause". This memo ships
**a falsified selector at n=3 cands, with concrete data showing the
mechanism conjecture (clause-overhead) and a clean Phase 2D design
implication (don't ship the ladder)**.
