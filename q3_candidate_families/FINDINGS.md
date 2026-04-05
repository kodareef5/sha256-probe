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

## Root Cause Analysis (2026-04-05)

**The crossval speed differences are fill-truncation artifacts, not candidate properties.**

At N=10, different 32-bit candidates collapse to the same mini-SHA instance:
- 0x44b49bc3 (fill=0x80000000) → m0=0xe0, fill=0x0 (identical to 0x9cfea9ce)
- 0x17149975 (fill=0xffffffff) → m0=0x34c, fill=0x3ff (identical to 0x7a9cbbf8)

The "fast" and "slow" candidates in each pair generate literally identical CNFs.
Speed differences come from solver noise and number of available candidates (2 vs 1).

## Complete Picture

Within the MSB kernel family:
1. All candidates are thermodynamically identical at N=32 (100K MC confirms)
2. Crossval speed differences at reduced widths are truncation artifacts
3. dW[61] constant does not predict difficulty
4. Padding freedom (M[14]/M[15]) doesn't improve metrics

**Conclusion: the MSB kernel candidate space is exhausted.**
No amount of M[0]/fill searching will find a fundamentally better candidate.

## Multi-Bit Kernel Search (2026-04-05)

2-bit kernel sweep: 496 kernels × 2^28 M[0] each (134B probes total).

12+ da[56]=0 candidates found across different 2-bit kernels. Examples:
- Kernel 0x10040000 (bits 28,18): min_hw63=97
- Kernel 0x80001000 (bits 31,12): best=88 in deep MC
- Kernel 0x20200000 (bits 29,21): dW61=13

**But: 50K MC comparison shows ALL 2-bit kernels have the same
thermodynamic distribution as the MSB kernel.** The ~90-bit floor
is kernel-independent.

## The Complete Q3 Picture

1. Within the MSB kernel: all candidates are thermodynamically identical
2. Across 2-bit kernels: all kernels are thermodynamically identical
3. dW[61] constant doesn't predict difficulty
4. Padding freedom doesn't help
5. Crossval speed differences are truncation artifacts

**The thermodynamic floor at ~90 bits is a property of the sr=60 problem
geometry** (7 tail rounds, 4 free words, schedule coupling), not of any
particular kernel or candidate family.

## Implications

The candidate/kernel search is EXHAUSTED. To make progress, the project
must change the PROBLEM, not the candidate:
1. **Q4 (MITM)**: Solve the hard residue directly — don't rely on
   thermodynamic proximity to collision
2. **Q5 (Alternative attacks)**: Wang modification, MILP trails — these
   exploit structure that random evaluation cannot see
3. **More freedom**: Multi-block attacks (extra compression block),
   IV freedom (semi-free-start), or different gap placement
4. **Higher-compute homotopy**: Push N=23,24,25 on the Mac — the
   precision homotopy remains the most productive empirical direction
