# Low hw(dW[56]) Batch Scan Results — 2026-04-09

## Setup
- Scanner: `q3_candidate_families/low_dw56_scanner.c`
- Threshold: hw(dW[56]) ≤ 8
- Range: full 2^32 M[0] per fill
- Priority: nice -19 (background of sr=61 race)
- Wall time: ~12 minutes per fill on shared 24 cores

## Results

| Fill | da[56]=0 candidates | with hw(dW[56]) ≤ 8 |
|---|---|---|
| 0x33333333 | 0 | 0 |
| 0x66666666 | 1 | 0 |
| 0x99999999 | 2 | 0 |
| 0xcccccccc | 2 | 0 |
| 0x12345678 | 0 | 0 |
| 0xdeadbeef | 0 | 0 |
| 0xa5a5a5a5 | 1 | 0 |
| 0x5a5a5a5a | 1 | 0 |
| **TOTAL (this batch)** | **7** | **0** |

Combined with laptop scan (fill=0xff: 2 candidates, 1 with hw≤8) and the
original Q3 mitm_scan (8 fills, 12 candidates total):

| Source | da[56]=0 found | with hw≤8 |
|---|---|---|
| Q3 mitm_scan (8 fills) | 12 | 1 (the verified 0x17149975) |
| Laptop scanner (1 fill) | 2 (recount) | 1 (same 0x17149975) |
| This batch (8 fills) | 7 | 0 |
| **Total unique** | **19** | **1** |

## Interpretation

Across ~16 fills × 2^32 M[0] ≈ 70 billion (M[0], fill) pairs scanned,
**only one da[56]=0 candidate has hw_dW56 ≤ 8: the verified sr=60 SAT
candidate 0x17149975 with fill=0xffffffff (hw=7).**

This confirms 0x17149975 is genuinely a statistical outlier on this metric.

However, the hw_dW56 hypothesis was REFUTED at N=8 by direct empirical
testing (see `writeups/hw_dw56_hypothesis.md` retraction). The metric
correlates with rarity but not with sr=60 solvability.

## Information loss caveat

The batch scanner used the OLD version that only printed hits passing
the threshold. So the M[0] values of the 7 high-hw da[56]=0 candidates
were NOT captured. To recover them, rerun with the v2 scanner
(committed in 326868c) which prints all hits.

## Action

The batch scan is complete. Data committed for posterity.
Next: continue sr=61 race, await fleet feedback on alt-candidate sr=60 test.
