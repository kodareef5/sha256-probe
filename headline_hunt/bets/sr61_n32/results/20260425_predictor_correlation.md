# Cross-predictor correlation: de58_size vs hard_bit_total_lb
**2026-04-25 evening** — sr61_n32 / structural predictor sanity check.

## Question

Today shipped two structural-compression predictors:
1. **de58_size** (image-size of de58 across W57 trials, mostly empirical)
2. **hard_bit_total_lb** (closed-form lower bound from mitm_residue's
   predict_hard_bits.py: h60 + f60 + g60_lb)

Are they measuring the same thing? If yes, redundant. If no, two
independent axes for candidate ranking.

## Result: Spearman ρ = 0.731 (strong but not identical)

```
Top 5 by hard_bit_total_lb (smallest = easiest):
  cand_n32_bit19_m51ca0b34_fill55555555   de58=  256, lock=13, hard_lb=15
  cand_n32_bit10_m27e646e1_fill55555555   de58=16379, lock= 5, hard_lb=19
  cand_n32_msb_m9cfea9ce_fill00000000     de58= 4096, lock=10, hard_lb=20
  cand_n32_bit11_m45b0a5f6_fill00000000   de58=16376, lock= 6, hard_lb=21
  cand_n32_msb_ma22dc6c7_fillffffffff     de58=32159, lock=14, hard_lb=22

Bottom 5:
  cand_n32_bit13_m4e560940_fillaaaaaaaa   de58=103191, lock= 7, hard_lb=26
  cand_n32_bit13_me01ff7c0_fillaaaaaaaa   de58= 82762, lock= 4, hard_lb=26
  cand_n32_bit17_mb36375a2_fill00000000   de58=115967, lock= 5, hard_lb=26
  cand_n32_bit06_m6781a62a_fillaaaaaaaa   de58=123067, lock= 6, hard_lb=27
  cand_n32_msb_m189b13c7_fill80000000     de58=130049, lock= 4, hard_lb=29
```

Top-5 overlap: **2 of 5** (bit-19 and m9cfea9ce in both top-5s).

## Findings

1. **Strong directional agreement**: small de58 image ↔ low hard_bit_lb.
2. **Disagreement on specific rankings**: top-5s overlap only 2/5. Each
   predictor reorders the middle-tier differently.
3. **bit-19 is #1 in BOTH** (most compressed by de58, fewest hard bits).
   Robust signal at the extreme.
4. **msb_m189b13c7 is #36 in BOTH** (largest de58 image, most hard bits).
   Robust signal at the other extreme.
5. **In-between, the predictors disagree**: e.g., bit-25 is #3 by de58
   (image=4096) but only mid-tier by hard_bit (>21).

## Implication for the validation matrix

The de58 validation matrix (running this evening) is testing whether
de58 rank predicts solver behavior. If the answer is "no" (preliminary
verdict suggests this), it does NOT necessarily kill the hard_bit_lb
predictor. They're correlated but not identical; hard_bit_lb might still
predict solver behavior even when de58 doesn't.

A future validation matrix could test **hard_bit_total_lb as a separate
predictor**:
- 5 candidates by hard_bit_lb (vs current 5 by de58 mix).
- Same solver/budget axes.
- Same dec/conf metric.

If hard_bit_lb DOES predict solver behavior where de58 doesn't, it's the
better candidate-priority axis.

## What this CHANGES

- **candidates.yaml metrics now carry both predictors**: de58_size,
  de58_hardlock_*, hard_bit_h60, hard_bit_f60, hard_bit_g60_lb,
  hard_bit_total_lb. Future fleet workers can grep either axis.
- **bit-19's status as "#1 candidate" is robust** (top in BOTH predictors).
- **For sr=61 SAT search**, the right candidate-priority is bit-19 if
  EITHER predictor is correct. If both are null (de58 verdict suggests
  this), candidate priority should be by COVERAGE (disjoint de58 regions)
  not RANK.

## Closed form: where hard_bit_total_lb comes from

Per `mitm_residue/results/`:
- h60 = de57 (closed form, exact, candidate-fixed)
- f60 = de59 (closed form, exact, candidate-fixed)
- g60 = de58 (varies with W57; `g60_lb` is HW(db56_xor) lower bound)

So hard_bit_total_lb = HW(de57) + HW(de59) + HW(db56_xor).
de57, de59 are deterministic from candidate (not W57-dependent).
HW(db56_xor) is the structural bottleneck on g60.

## Caveats

- hard_bit_total_lb is a LOWER BOUND, not exact. Actual hard bits may be
  higher.
- Spearman 0.731 means "positively correlated" but not identical. Don't
  assume bit-19's #1 status will replicate at the SAT-finding level — the
  validation matrix preliminary verdict already shows neither predictor
  is monotonic with kissat dec/conf.
- 36 candidates is a small sample for rank correlation; 0.731 is
  statistically meaningful but not overwhelming.

## Files

- `headline_hunt/bets/mitm_residue/prototypes/predict_hard_bits.py`
- `headline_hunt/registry/candidates.yaml` (now carries hard_bit_* fields)
- This writeup
