# CORRECTION: Per-Round Degree Estimates Were Wrong

**Date**: 2026-04-10
**Evidence level**: VERIFIED (exact ANF at N=4 is ground truth)
**Supersedes**: Degree estimates in per_round_degree_n8.log and per_round_degree_n32.log

## What Was Claimed

The restriction test (`per_round_degree.py`) reported a "dramatic degree collapse":
- N=8 round 63: degree ~4 / 64 free bits (6% of max)
- N=32 round 63: degree ~6 / 256 free bits (2% of max)

This was interpreted as "the schedule-determined rounds have LOW algebraic degree."

## What Is Actually True

**The restriction test heuristic is WRONG.** It confuses perturbation sensitivity with algebraic degree.

The heuristic measures: "what fraction of output bits are constant when we fix all but k input bits?" This is a sensitivity measure, not a degree measure. A degree-d polynomial can appear "easy" to the restriction test because most monomials share variables, making random restrictions likely to kill ALL of them.

### Ground Truth: Exact ANF at N=4

Via complete Moebius transform over 2^32 truth table entries:

| Output bit | Register | Bit pos | Exact degree | % of max (32) |
|-----------|----------|---------|-------------|---------------|
| 28        | h        | 0 (LSB) | 8           | 25%           |
| 29        | h        | 1       | 9           | 28%           |
| 30        | h        | 2       | 10          | 31%           |
| 31        | h        | 3 (MSB) | 12          | 38%           |
| 24        | g        | 0       | 12          | 38%           |
| 12        | d        | 0       | 9           | 28%           |
| 0         | a        | 0       | 16          | 50%           |
| 16        | e        | 0       | 16          | 50%           |

**Range: 25-50% of maximum**, not 2-6%.

### Higher-Order Differential Confirmation at N=8

The C-based higher-order differential scanner (`higher_order_diff.c`) computes exact k-th order differentials (XOR over all 2^k subsets). Through k=19 at N=8 (10+ hours of computation), ALL output bits still show ~50% zero differentials, confirming degree > 19 for all bits. This is consistent with 25-50% of 64 = 16-32.

## The Correct Picture

1. **Degrees are 25-50% of maximum** (moderate, not dramatic collapse)
2. **Register ordering**: h < g < d < f < c < b ~ a ~ e (cascade structure)
3. **Bit position gradient**: LSBs have lower degree than MSBs (carry chain effect)
4. **h[LSB] is the weakest bit**: degree 25% of max — the best algebraic attack surface
5. **Sparsity is extreme**: h[0] has 1,173 monomials out of C(32,≤8) ≈ 15M possible. That's 0.008% density.

## What This Changes

- The tail rounds are **algebraically stronger** than the restriction test suggested
- Pure algebraic attacks need degree ≥ 25% of the variable count — not trivial
- The sparsity (0.008%) is potentially more exploitable than the degree
- The carry chain gradient is a real structural feature worth investigating

## What To Do

- [x] Stop citing "degree ~4" or "degree ~6" — these numbers are wrong
- [x] Use exact ANF degrees as the reference
- [ ] Wait for higher-order diff at N=8 to find actual degree boundaries
- [ ] Compute restricted exact ANF at N=8 for cascade-only subproblem
