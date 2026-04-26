# F8: stack speedup DECAYS past 200k, REGRESSES at 500k-1M
**2026-04-26 19:50 EDT**

CRITICAL caveat to F4b's 1.87× median deployment claim (commit 7be3536).
The de58+de59 64-bit stack is **preprocessing-only**, similar to the
13-bit marginal-locked variant before it. At budgets ≥500k the stack
HURTS performance.

## Result (3 cands × 4 budgets × 2 seeds)

Same kissat 4.0.4, M5 host, single-thread. Same F1/F4b CNFs. Median
of 2 seeds.

| cand | budget | base_med | stack_med | speedup |
|---|---:|---:|---:|---:|
| msb_m9cfea9ce_00 | 50k | 2.47 | 0.97 | **2.55×** |
| msb_m9cfea9ce_00 | 200k | 4.77 | 3.74 | 1.27× |
| msb_m9cfea9ce_00 | 500k | 10.34 | 10.72 | **0.96×** REGRESSION |
| msb_m9cfea9ce_00 | 1M | 21.87 | 23.21 | **0.94×** REGRESSION |
| bit14_m67043cdd_ff | 50k | 2.72 | 1.30 | **2.09×** |
| bit14_m67043cdd_ff | 200k | 5.06 | 4.39 | 1.15× |
| bit14_m67043cdd_ff | 500k | 10.86 | 11.52 | 0.94× REGRESSION |
| bit14_m67043cdd_ff | 1M | 22.63 | 23.26 | 0.97× |
| bit19_m51ca0b34_55 | 50k | 2.34 | 1.30 | **1.80×** |
| bit19_m51ca0b34_55 | 200k | 4.58 | 4.44 | 1.03× |
| bit19_m51ca0b34_55 | 500k | 10.33 | 11.71 | 0.88× REGRESSION |
| bit19_m51ca0b34_55 | 1M | 22.37 | 24.12 | 0.93× REGRESSION |

All 3 cands tested: speedup decays from 1.80×–2.55× at 50k to
0.88×–0.97× at 500k. Six of nine high-budget runs (≥500k) are
regressions vs base.

## Mechanism

The stack hints encode information the solver eventually derives
itself through unit propagation on the cascade clauses. At 50k, the
hints save the solver from repeating that early derivation. Past
~200k conflicts, the base solver has propagated all those facts; the
search-time difference is in the actual **search**, where the hints
contribute nothing extra.

Worse: the unit clauses force-fix variables to specific polarities
during early restarts, which can interact poorly with kissat's later
backjump / restart heuristics — likely the source of the 0.88-0.97×
regressions.

This MATCHES the 13-bit marginal-locked decay curve (commit 46961eb,
20260426_locked_bit_hints_speedup.md addendum). Both expose-side
hint variants share the same preprocessing-only character.

## Updated deployment recommendation

The wrapper docstring (commit 9427f17) said "recommended default for
new sr=61 cascade_aux runs." That is **WRONG for budgets ≥200k**.

Corrected guidance:
- **Budget ≤ 100k**: use `--hint-mode de58-de59-stack`. Median 1.5–2×
  speedup, 0% regression at the n=18 sweet spot of 50k.
- **Budget 100k–300k**: stack still positive but modest (~1.0–1.3×).
  Use stack only if seed-variance can be amortized.
- **Budget ≥ 500k**: do NOT use stack. Use Mode A baseline OR Mode B
  (Mode B has lasting value via solution-set restriction).
- **Long runs (1M+)**: Mode B is the right tool; stack hurts.

## Implications for the bet

- **The structural-hint approach** is real but limited to short
  preprocessing-window runs. It's a good "warm-start" tool for fan-out
  parallel search, not a deep-search accelerator.
- **Mode B remains the deep-search winner** (project's longstanding
  finding ~1.5× sustained at higher budgets via solution-set
  restriction).
- **Cross-bet leverage idea**: a "fan-out" deployment uses stack
  hints in 50k-budget bursts with N seeds × N chambers, then drops
  back to Mode B for the survivors. Stack does fast triage; Mode B
  does sustained search.

## Wrapper update needed

The docstring will be corrected in the next commit to reflect
budget-dependent guidance. Both `--hint-mode de58-at-w57` and
`--hint-mode de58-de59-stack` should print a warning when used in
any context that suggests >200k conflicts.

EVIDENCE-level: VERIFIED (3 cands × 4 budgets × 2 seeds; budget-decay
pattern is consistent across all 3 cands). Together with the prior
13-bit decay curve, this confirms expose-side hint speedups are
fundamentally preprocessing-only.
