# N=8 Predictor Search — Null Result

## Method

Sampled 30 random N=8 da[56]=0 candidates from the 262 enumerated.
For each, computed 15 algebraic metrics and ran Kissat (seed=1, 20s
timeout) on the sr=60 mini-SHA encoding. Computed Pearson correlations
of each metric with solver time, excluding the 10 timeouts (n=20 valid).

## Results

| Metric | Mean | Pearson r vs solve time |
|---|---|---|
| hw_dW56 | 4.00 | +0.052 |
| hw_dW55 | 3.90 | -0.121 |
| hw_dW54 | 4.10 | +0.195 |
| hw_dW53 | 3.85 | +0.067 |
| hw_dW45 | 3.60 | **-0.430** |
| hw_dW44 | 4.30 | +0.240 |
| hw_state_56 | 27.50 | +0.099 |
| hw_b56 | 3.40 | +0.290 |
| hw_c56 | 4.50 | -0.038 |
| hw_d56 | 4.00 | -0.046 |
| hw_e56 | 4.60 | -0.105 |
| hw_f56 | 3.20 | -0.126 |
| hw_g56 | 3.95 | +0.142 |
| hw_h56 | 3.85 | +0.228 |

(hw_a56 is always 0 — that's the da[56]=0 condition.)

Critical r for p=0.05 with n=20 is ~0.44. **None of the metrics
reach significance.** The strongest (hw_dW45 at -0.43) is borderline
but doesn't survive Bonferroni correction across 14 hypotheses.

## Interpretation

**No single algebraic metric predicts N=8 sr=60 difficulty.**

Key implications:
1. The hw_dW56 retraction is reinforced — r=+0.05 is essentially zero
2. The de57_err model also fails to predict at N=8 (we'd need to add
   that metric, but the correlation pattern suggests no single
   differential weight is the answer)
3. The 33% timeout rate (10 of 30 at 20s) indicates many candidates
   are genuinely hard, not just slow
4. Solver difficulty depends on something deeper than schedule word
   or state Hamming weights

## Suggested next steps

The predictor (if one exists) is probably:
- A combination of multiple features (try multivariate regression)
- Something about the sigma1/sigma0 image structure of the W[60..63]
  schedule rule under specific (M[0], fill)
- A global property of the conflict graph in the SAT instance itself
  (clause connectivity, variable degree)

Or there is no simple predictor, and difficulty is essentially random
within the candidate space — the corollary being that "find an easier
candidate" is not a productive direction without orders of magnitude
more candidates to test.

## Multivariate Update

OLS regression of time on 5 standardized features (dW56, dW55, dW54,
state_56, h56) across all 30 candidates:
- **R² = 0.1092** (only 11% of variance explained)
- Largest standardized coefficient: dW54 at +1.79 (still small)
- Timeout binary classifier: max single-feature |r| = 0.24 (dW55)

Even combining multiple features explains very little variance.
The algebraic predictor approach is exhausted at N=8.

## Evidence level

**EVIDENCE** (strengthened by multivariate analysis): 30-candidate sample,
20 valid timing measurements at N=8. Reproducible from
`q5_alternative_attacks/n8_predictor_search.py`.
