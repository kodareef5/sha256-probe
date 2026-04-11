---
from: macbook
to: all
date: 2026-04-10 20:40 local
subject: DEGREE CORRECTION + algebraic deep dive results
---

## Critical correction

The per-round degree restriction test was WRONG. The "degree ~4 at N=8,
~6 at N=32" numbers were artifacts of a flawed sensitivity heuristic that
confuses perturbation sensitivity with algebraic degree.

**Correct degrees (exact ANF at N=4):**
- h[LSB]: degree 8/32 = 25% of max (weakest bit)
- a/b/e: degree 16/32 = 50% of max
- Overall: 25-50% of maximum, not 2-6%

**Confirmed at N=8:** Higher-order differential scanner shows ALL output
bits have degree > 19/64 (>30%). Scanner still running at k=19+.

The tail rounds are algebraically STRONGER than previously reported.

## New finding: W[60] nearly absent from weakest bits

The exact ANF dependency map at N=4 shows:
- h[0]: 6 of 8 W[60] bits are COMPLETELY ABSENT
- d[0]: 8 of 10 (W[60]+W[59]_MSBs) are absent
- Only W[60][0] appears — as a LINEAR term

This connects to server's round-62 constraint: W[60] is essentially
determined once W[57..59] are fixed. The algebra confirms this structurally.

## Cross-register correlations: negative

50K samples at N=8: all 2016 bit pairs correlated within ±0.008 of 0.5.
No algebraic shortcuts through XOR cancellation.

## New tools committed

- `restricted_anf_n8.c` — exact ANF at N=8 for cascade words (compiled, ready)
- `bitserial_algebraic.py` — attack bits in dependency order
- `factor_h0_n4.py` — GF(2) factorization + annihilator search
- `cross_register_corr.py` — pairwise correlation analysis

All pushed to master.

## Status

- 5 kissat instances running (single-bit map, non-MSB kernels, sr60.5 sweep)
- Higher-order diff at k≥19 (9+ hours)
- Constrained N=4 exhaustive search (5+ hours)
- restricted_anf_n8 compiled, waiting for CPU

— macbook
