# Q3 Findings: Candidate Family Search

## Scan Coverage (2026-04-05)

8 uniform fill patterns × 2^32 M[0] values = **34.4 billion probes**.

12 da[56]=0 candidates found. Rate: ~3.5 × 10^-10.

## Key Result: New Best Candidate

**M[0]=0x7a9cbbf8, fill=0x7fffffff** has:
- dW[61] constant HW = **12** (vs 16 for published candidate — 25% improvement)
- hw56 = **91** (lowest of all 12 candidates)
- boomerang gap = 12

This is the most promising candidate family found so far for sr=60 SAT testing.

## Full Candidate Table

| Rank | M[0] | Fill | hw56 | dW61_C | Boom | min_gh60 | min_hw63 |
|------|------|------|------|--------|------|----------|----------|
| 1 | 0x7a9cbbf8 | 0x7fffffff | 91 | **12** | 12 | 19 | 96 |
| 2 | 0x189b13c7 | 0x80000000 | 122 | 14 | 17 | 19 | 98 |
| 3 | 0x23b8329b | 0x0f0f0f0f | 111 | 14 | 17 | 20 | 99 |
| 4 | 0x2e05fe70 | 0xf0f0f0f0 | 110 | 14 | 16 | 18 | 97 |
| 5 | 0x9cfea9ce | 0x00000000 | 103 | 15 | 18 | 18 | 97 |
| 6 | 0x17149975 | 0xffffffff | 104 | 16 | **9** | **16** | 96 |
| 7 | 0x3f239926 | 0xaaaaaaaa | 107 | 16 | 16 | 19 | 103 |
| 8 | 0xa22dc6c7 | 0xffffffff | 115 | 16 | 18 | 19 | 97 |
| 9 | 0x01727cad | 0x0f0f0f0f | 123 | 16 | 17 | 18 | 99 |
| 10 | 0x015c3838 | 0xf0f0f0f0 | 107 | 17 | 12 | 18 | 102 |
| 11 | 0x44b49bc3 | 0x80000000 | 106 | 18 | 13 | **17** | **94** |
| 12 | 0x64085a33 | 0x55555555 | 110 | 18 | 14 | 18 | 100 |

## Metric Observations

1. **dW[61] constant HW ranges 12-18** across all candidates and fills.
   The published candidate (HW=16) is not optimal by this metric.

2. **Boomerang gap ranges 9-18.** Published candidate 0x17149975 has the
   smallest gap (9), but our new best by dW[61] has gap=12. These metrics
   are not strongly correlated.

3. **min_hw63 is tightly clustered at 94-103** — the "thermodynamic floor"
   is ~94 bits regardless of candidate. This confirms that random free-word
   search cannot reach collision (0 HW) regardless of candidate choice.

4. **min_gh60 (MITM hard residue) ranges 16-20.** The published candidate
   has the best score (16), suggesting its MITM geometry is favorable despite
   the high dW[61] constant.

5. **mean_hw63 is nearly constant at 127-128** across all candidates.
   The average random evaluation produces ~half of 256 bits differing.

## Cross-Validation Results (2026-04-05)

**dW[61] constant does NOT predict reduced-width SAT solve time.**

| M[0] | dW61_C | N=10 | N=12 |
|------|--------|------|------|
| 0x44b49bc3 | **18** | **24.8s** | **66.0s** |
| 0x3f239926 | 16 | **24.4s** | 235.9s |
| 0x9cfea9ce | 15 | 40.7s | 109.3s |
| 0x7a9cbbf8 | **12** | 123.1s | TIMEOUT |

The worst dW61 candidate is the fastest solver. The best dW61 candidate
is the slowest. Correlation is *negative*.

**Better predictors appear to be min_hw63 and min_gh60** (Monte Carlo
thermodynamic metrics). The fastest candidate (0x44b49bc3) has:
- min_hw63 = **94** (best of all 12 candidates)
- min_gh60 = **17** (second-best)

## Padding Freedom (2026-04-05)

12 M[14]/M[15] variations tested around fill=0x7fffffff:
- 7 of 12 produced ZERO candidates (da[56]=0 destroyed)
- Non-uniform padding generally increases dW61_C (worsens metric)
- Uniform fill=0x7fffffff is locally optimal

## Evidence Level

**RETRACTED**: dW[61] constant as primary predictor. Cross-validation
falsifies this at reduced widths. Retained as one metric among several.

**HYPOTHESIS**: min_hw63 and min_gh60 (Monte Carlo thermodynamic floor)
are better predictors of candidate quality. Needs further validation.

**EVIDENCE**: Candidate 0x44b49bc3 (fill=0x80000000) is the most favorable
for SAT solving at reduced widths. Has the lowest min_hw63 (94) and
the fastest solve times at N=10 and N=12.

## Next Steps

1. Investigate WHY 0x44b49bc3 solves fast — differential trace, carry analysis
2. Push 0x44b49bc3 to higher N (16, 18, 20) on the Mac homotopy pipeline
3. Rescore all 12 candidates by min_hw63 and min_gh60 with more MC samples
4. Test whether min_hw63 predicts at N=16+ (higher widths)
