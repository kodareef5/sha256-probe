---
date: 2026-04-30
bet: programmatic_sat_propagator
status: LEARNED_NEIGHBORHOOD_ROWS57_58
parents: F417
---

# F418: learned-neighborhood scan for dW57/dW58

## Summary

Conflict cap: 50000. Watches all 64 aux vars in `dW57` and `dW58`, baseline and F343-injected, for the bit2/bit24/bit28 panel.

| Candidate | Condition | Audit | Decisions | Learned exported | Learned touching rows | Touch % | Top row-bit touches |
|---|---|---|---:|---:|---:|---:|---|
| `bit2_ma896ee41_fillffffffff` | baseline | CONFIRMED | 353889 | 47054 | 0 | 0.000% | none |
| `bit2_ma896ee41_fillffffffff` | f343 | CONFIRMED | 350989 | 46769 | 0 | 0.000% | none |
| `bit24_mdc27e18c_fillffffffff` | baseline | CONFIRMED | 396658 | 46775 | 0 | 0.000% | none |
| `bit24_mdc27e18c_fillffffffff` | f343 | CONFIRMED | 407049 | 46696 | 0 | 0.000% | none |
| `bit28_md1acca79_fillffffffff` | baseline | CONFIRMED | 367451 | 46674 | 0 | 0.000% | none |
| `bit28_md1acca79_fillffffffff` | f343 | CONFIRMED | 322416 | 46843 | 0 | 0.000% | none |

## F343 Delta With Same Watcher

| Candidate | Δ decisions | Δ backtracks | Δ learned exported | Δ learned touching rows |
|---|---:|---:|---:|---:|
| `bit2_ma896ee41_fillffffffff` | -2900 (-0.82%) | -262 (-0.45%) | -285 (-0.61%) | +0 |
| `bit24_mdc27e18c_fillffffffff` | +10391 (+2.62%) | +160 (+0.27%) | -79 (-0.17%) | +0 |
| `bit28_md1acca79_fillffffffff` | -45035 (-12.26%) | -598 (-1.03%) | +169 (+0.36%) | +0 |

## Initial Read

F417 showed zero learned-clause touch on the specific F343 triple. F418 broadens the watch surface to the whole `dW57`/`dW58` aux neighborhood so the next operator can target variables that actually appear in learned clauses.

The result is still zero: none of the 46k-47k exported learned clauses per run touched any watched `dW57` or `dW58` aux var. This is stronger than F417. It means the learned neighborhood for these capped programmatic traces is outside the two aux rows that motivated the F343/F344 clause family.

The decision deltas in this memo should be compared only within F418's same-watcher arms. This run intentionally removes the first-touch trace arguments and replaces them with a wider learned-clause watch surface.

## Verdict

Do not spend the next cycle on more `dW57`/`dW58` aux-row nudges. The learned-clause neighborhood is elsewhere. The next useful scan is actual W variables and/or the `aux_modular_diff` family, ranked by learned-clause touch count.

## Compute Discipline

- 6 CNFs audited before solver launch.
- 6 solver runs appended with `append_run.py`.
- Logs: `/tmp/F418/*.stderr.log` and `/tmp/F418/*.stdout.log`.
