# Continuous trigger doesn't help — Rule 4 still preprocessing-bound

## Setup

After the sample-based trigger (every 64 actual-reg bit assigns) showed Rule 4 firing 209× at 50k AND 209× at 500k (front-loaded), implemented a **continuous trigger** (call `try_fire_rule4_r62` after every notify_assignment) to test whether sample-based was missing fleeting fires between backtracks.

## Results on bit-19 (highest-firing kernel)

| Trigger | Conflicts | Rule 4 fires | Decisions | Wall |
|---|---:|---:|---:|---:|
| sample (every 64) | 50k  | 209 | 431,452 | 2.33s |
| **continuous**    | 50k  | **520** | **356,360** | 3.0s |
| sample            | 500k | 209 | (extrapolated) | 22.7s |
| **continuous**    | 500k | **520** (same!) | 2,545,009 | 26.0s |

## Two findings

### 1. Continuous trigger catches 2.5× more fires at 50k

520 vs 209 fires — confirms the sample-based trigger was missing fleeting states between backtracks. The propagator now sees more of Rule 4's actual firing potential.

**Decision count drops from 431k → 356k** at the same 50k conflict budget — a 17% reduction. The extra fires DO help solver navigation, just not enough to compensate for per-conflict overhead.

### 2. Continuous trigger ALSO front-loaded — 520 fires at both 50k and 500k

This is the more important finding. **Even with continuous firing, Rule 4 fires the SAME number of times at 50k as at 500k.** Zero new fires across 50k–500k window.

The bottleneck isn't the TRIGGER — it's the underlying SOLVER BEHAVIOR.

## Why Rule 4 can't compound during deep search (structural finding)

CDCL's search trajectory through cascade-DP CNF:
- **Phase 1 (preprocessing + early CDCL, ~0–50k conflicts)**: cascade-zero unit clauses (Mode B's force) and dE[61..63]=0 unit clauses propagate massively. This propagation BUSILY DECIDES many actual-register bits via unit propagation. Rule 4's input bits (a_61, a_60, a_59 in both pairs) become decided in lots of state combinations.
- **Phase 2 (deep search, 50k+ conflicts)**: CDCL navigates the residual search space by deciding **diff-aux variables** (XOR diffs of register bits, dE[r] aux, etc.), NOT actual register values. The actual a_61, a_60, a_59 bits are decided IMPLICITLY via unit propagation FROM the diff-aux decisions — but CDCL rarely backtracks to a level where they get re-decided in the right combination for Rule 4.

So Rule 4's input domain (actual register values) is **NOT NATURALLY EXPLORED by CDCL** during deep search. CDCL focuses on the diff-aux variable subspace. Rule 4 fires only during the initial propagation cascade when cascade-zero structure puts everything into a known state.

## Implication for the bet (sharpened)

**The bet's value-add hypothesis is empirically refuted not because the propagator is implemented poorly, but because CDCL doesn't visit the propagator's trigger states during deep search.**

Two paths could revive the bet:

### Path A: Force CDCL to decide on actual register bits
Use `cb_decide()` callback to inject decision suggestions that CDCL would otherwise not make — specifically, decisions on actual register bits that would unlock Rule 4 firings. This is a major shift in propagator philosophy: from "passively wait for trigger conditions" to "actively shape the search."

Cost: ~200 LOC + careful heuristic design. Risk: random decisions hurt solver more than they help.

### Path B: Translate Rule 4 to fire on diff-aux variables
Reformulate the partial-bit reasoning to use only diff-aux inputs (the variables CDCL DOES decide on). This loses access to Sigma0/Maj on actual values — those would have to come from CNF clauses, not propagator computation.

Cost: ~400 LOC + likely returns to Mode B-equivalent behavior.

### Path C (recommended): kill the bet
Accept the empirical evidence: Rule 4-style propagation doesn't help cascade-DP search at the budgets that would matter. Mode B's static unit clauses provide equivalent preprocessing benefit at far lower cost.

The propagator engineering substrate (~750 LOC + tests) remains useful as a reference / learning artifact. The bet's headline hypothesis is empirically dead.

## Cumulative empirical evidence on the bet

1. Phase 2C-Rule4 firing IS implemented and works (commit `f90ebfa`).
2. Cross-kernel firing varies 5× (52–249) — bit-25 highest (commit `df398e2`).
3. 500k confirms front-loaded (commit `4a45d20`).
4. Continuous trigger gives 2.5× more fires at 50k but STILL front-loaded (this commit).
5. Decision count drops 17% with continuous trigger — modest pruning effect.
6. Wall time is consistently ~1.9× slower with the propagator.

## What this teaches the broader bet portfolio

**This experiment turned an "empirical conjecture" into an "empirical certainty."** The propagator path for cascade-DP requires either fundamental redesign (Path A or B) or graceful retirement (Path C). Future bets in the portfolio should not assume "propagator-style dynamic constraint injection beats static encoding" without reconsidering this finding.

For the wider headline-hunt: cascade-DP search is dominated by diff-aux variable decisions. Mechanisms that operate ON those (cascade_aux Mode B, programmatic propagator targeting diff-aux, encoding tweaks that exploit XOR-domain structure) have natural synergy with how CDCL actually navigates. Mechanisms that operate on actual register values (Rule 4-style modular reasoning) operate in a DIFFERENT subspace from CDCL's natural exploration — they need to FORCE the solver into their domain rather than wait for it.
