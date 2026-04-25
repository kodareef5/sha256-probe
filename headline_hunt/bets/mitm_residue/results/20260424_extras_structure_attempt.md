# Carry-extras: structural correlate exploration (N=27, partial finding)

The closed-form predictor is a true lower bound (validated 27/27, mean extras 1.52). But what predicts the extras themselves?

## Looked at

For each of the 27 validated candidates, computed:
- HW(db56_xor) — the lower-bound contribution
- longest_1run — the longest contiguous run of 1s in db56_xor
- islands — number of 1-runs (i.e., maximal contiguous 1-blocks)

## Pattern (visible but noisy)

| extras | HW range | longest range | islands range | n |
|---:|---|---|---|---:|
| 0 | 15-23 | 3-11 | 4-10 | 6 |
| 1 | 14-20 | 3-8 | 7-10 | 9 |
| 2 | 12-19 | 2-7 | 6-11 | 6 |
| 3 | 14-15 | 2-3 | 10 | 2 |
| 4 | 13-17 | 3-9 | 7-8 | 3 |

No clean monotonic relationship. The extras=0 candidates lean toward longer runs (max=11) and fewer islands (min=4), but the overlap with other extras-counts is large.

## Why a clean rule probably doesn't exist

Extras come from carry-chain propagation in `Maj_1 - Maj_2` (modular). The position-i extra fires when:
- db56_xor[i] = 0 (so xor1-set lower bound doesn't include it), AND
- The modular subtraction at lower positions produces a borrow that lands at position i

This depends on the *integer pattern* of `Maj_1` and `Maj_2`, not just the XOR-set. Two candidates with identical HW(db56_xor) and identical island structure can have different `Maj` values that produce different carries.

A clean predictor for extras likely requires reasoning about the modular `Maj_1 - Maj_2` directly (Lipmaa-Moriai-style), not just the xor-pattern of db56.

## What's good enough

Mean extras = 1.52 with max=4 across 27 candidates. The lower-bound predictor with a +2 correction gives:
- A point estimate of empirical hard-bit count accurate to within ±2 in 70%+ of cases
- A safe upper bound of `pred_lb + 5` accurate in 100% of cases

That's useful for MITM-table sizing without needing to predict extras exactly.

## Concrete next-actions if anyone wants to chase this

1. Larger sample: run sweep on synthetic candidates (random m0/fill at sigma1-aligned bits) to grow N from 27 to 1000+ and look for a tighter structural correlate.
2. Lipmaa-Moriai derivation: for two bit-strings A, B with known XOR mask m = A XOR B, characterize the bit-i probability of (A − B) over uniform A.

Both are multi-day investigations. For now: lower bound + 2 is a working point estimate.
