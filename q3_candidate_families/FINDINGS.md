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

## Evidence Level

**HYPOTHESIS**: Candidate 0x7a9cbbf8 (fill=0x7fffffff, dW61_C=12) is more
favorable for sr=60 than the published candidate. Supporting evidence:
lower dW[61] constant means the schedule-determined word differential is
more absorbable. Needs SAT testing to confirm.

## Next Steps

1. Run sr=60 SAT on the top candidates (especially 0x7a9cbbf8)
2. Explore padding freedom (M[14]/M[15]) around fill=0x7fffffff
3. Test whether dW[61] constant actually predicts SAT outcome
4. Score candidates at reduced word widths for cross-validation
