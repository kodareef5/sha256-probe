# cb_decide() Path A — solver trajectory shaping doesn't unlock compounding

## Setup

After establishing that Rule 4@r=62 fires preprocessing-only (front-loaded behavior persists with continuous trigger), implemented Path A from `MODULAR_VS_XOR_FORCING_ISSUE.md`: a `cb_decide()` heuristic that injects decision SUGGESTIONS for actual-register bits, forcing CDCL into the propagator's input domain.

Heuristic: scan a_61 pair-1's PartialReg; suggest the lowest-bit undecided bit. The propagator returns this var as the next decision.

## Results on bit-19, 50k vs 500k

| Setup | Conflicts | Rule 4 fires | cb_decide suggestions | Decisions | Wall |
|---|---:|---:|---:|---:|---:|
| continuous trigger only | 50k | 520 | 0 | 356k | 2.51s |
| **+ shape-decisions**   | 50k | **977** (+88%) | **128,326** | 507k | 2.50s |
| + shape-decisions       | 500k | **977 (SAME!)** | 989,839 | 3.6M | 25.6s |

## Three findings

### 1. Decision-shaping nearly DOUBLES Rule 4 firings at same wall time

977 vs 520 fires at 50k — solid 88% increase. cb_decide suggestions are being honored by cadical (128k accepted at 50k → solver IS taking the propagator's hints). And wall time is unchanged (2.50s vs 2.51s) because the cost of fewer wasted decisions roughly balances the cost of decision-shaping.

### 2. Decisions UP 42% (356k → 507k)

The solver takes more decisions per conflict because decision-shaping pulls it into less-natural search regions. But the extra decisions correspond to extra Rule 4 firings — net not catastrophic.

### 3. Rule 4 firings STILL CAP at 977 — even at 500k conflicts (the deeper finding)

500k with decision-shaping shows 977 Rule 4 fires — the SAME as at 50k. Despite ~990k cb_decide suggestions during 500k conflicts, no new Rule 4 fires past the first ~50k.

**This refutes Path A as well.**

## Why Rule 4 caps at a finite number

Rule 4's modular relation `dA[62] - dE[62] = dT2_62` (where dT2_62 = dSigma0(a_61) + dMaj(a_61, a_60, a_59)) is a SINGLE algebraic equation over 32-bit modular values. The propagator can force IMPLIED LITERALS of this equation under partial knowledge of the inputs.

But the SET OF ALL SUCH IMPLIED LITERALS — across every (a_61, a_60, a_59, a_62) partial state CDCL might visit — is FINITE. The propagator can't fire more constraint-injection than the underlying equation contains. Once all derivable literals are forced, no further pruning possible.

For bit-19 candidate, that finite set has ~977 elements. For bit-25, ~250 (from the cross-kernel sweep). For other kernels in between.

## What this means structurally

**The propagator is a constant-pruning rule, not a compounding one.** No matter how aggressively you trigger or shape decisions, Rule 4@r=62 contributes at most ~977 forced bits per search tree. That's roughly equivalent to ~30 unit clauses worth of constraint information.

Mode B's static unit clauses provide the same kind of constant-pruning effect with no propagator overhead. The propagator and Mode B are NOT additive — they're alternative implementations of the same constraint class.

## Final verdict on the propagator bet

**The bet's "compounding pruning at multi-hour budgets" hypothesis is empirically refuted at three levels**:
1. Sample-based trigger fires preprocessing-only (commit `4a45d20`).
2. Continuous trigger fires preprocessing-only (commit `9329f72`).
3. Decision-shaping fires preprocessing-only (this commit).

The trigger is not the bottleneck. The DECISION strategy is not the bottleneck. The bottleneck is **the algebra**: Rule 4 is a finite-pruning constraint, not a generative one.

Recommend FULL kill of the bet. The engineering substrate (~750 LOC C++ + ~560 LOC tests + Sigma0/Maj/dT2/modular-sub primitives) remains useful as a learning artifact and could feed future bets if a generative-pruning rule is identified, but Rule 4 alone — and likely Rule 6 by the same algebra — won't deliver the bet's headline-class hypothesis.

## What survives

The infrastructure has value beyond Rule 4:
- The encoder's modular-diff aux variables (Phase 2C-r62/r63) are useful for ANY constraint-based reasoning over modular differences. Future encodings can reuse them.
- The varmap v3 schema bridges encoder ↔ propagator cleanly. Reusable.
- The unit-tested partial-bit primitives (sigma0, maj, modular sub with borrow chain) are general — applicable to any modular-arithmetic propagator design.
- The decision-shaping cb_decide() framework is in place. Future workers can plug new heuristics.

## Cumulative empirical pillar count for the propagator bet

1. ✓ engineering substrate complete (~750 LOC + ~560 LOC tests)
2. ✓ Rule 4 firing IS implemented and works on real CNFs
3. ✗ Rule 4 doesn't compound at higher budgets (front-loaded firing)
4. ✗ Continuous trigger doesn't help (CDCL doesn't visit input domain)
5. ✗ Decision-shaping doesn't help (algebra has finite implied literal set)

3-out-of-5 negatives on the value-add hypothesis. The bet is empirically dead.
