## RETRACTED 2026-04-09 — Empirical refutation at N=8

A direct test at N=8 mini-SHA refutes this hypothesis. Across 11 candidates
spanning hw_dW56_mini ∈ {0, 1, 7}:

| hw | n | min_times | mean (excl. timeouts) |
|---|---|---|---|
| 0 | 2 | 3.4s, TIMEOUT | 3.4s |
| 1 | 4 | 6.7s, 7.4s, 11.3s, 25.9s | 12.8s |
| 7 | 5 | 2.8s, 3.9s, 5.3s, 16.3s, TIMEOUT | 7.1s |

Within-hw variance dominates between-hw variance. The fastest candidate
(2.8s) is at hw=7, NOT hw=0. Both hw=0 and hw=7 have one timeout each.
There is no predictive power.

Mechanistic explanation: hw_dW56 is just one of many differential
characteristics. Carry propagation, cascade-1 cleanliness, and other
algebraic factors dominate solver difficulty. The single N=32 observation
(0x17149975 having lowest hw_dW56) was within the 1.4% chance of random
correlation.

CAVEAT: N=8 mini-SHA has different rotation amounts and constants than
N=32. The hypothesis MIGHT still hold at N=32 even though it's refuted at
N=8 — but the prior should drop substantially.

Test artifacts:
- `q5_alternative_attacks/n8_hw_dw56_test.py` — enumeration of 262 N=8 candidates
- `q5_alternative_attacks/n8_hw_dw56_solver_test.py` — kissat timing experiment

---

# Hypothesis (ORIGINAL, see retraction above): Low hw(dW[56]) Predicts sr=60 Solvability

## Statement

Among da[56]=0 candidates, those with low hw(dW[56]) (the differential
Hamming weight of schedule word 56) are more likely to admit sr=60 collisions.

## Evidence

Enriched all 12 known da[56]=0 candidates with per-word differential metrics
(see `q5_alternative_attacks/enrich_candidates.py`):

| M[0] | fill | hw_dW56 | sr=60 status |
|---|---|---|---|
| **0x17149975** | **0xffffffff** | **7** | **SAT (verified, 12h)** |
| 0x44b49bc3 | 0x80000000 | 13 | not solved |
| 0x189b13c7 | 0x80000000 | 13 | not solved |
| 0x23b8329b | 0x0f0f0f0f | 17 | not solved |
| 0x9cfea9ce | 0x00000000 | 15 | not solved |
| 0x01727cad | 0x0f0f0f0f | 15 | not solved |
| 0xa22dc6c7 | 0xffffffff | 14 | not solved |
| 0x015c3838 | 0xf0f0f0f0 | 14 | not solved |
| 0x3f239926 | 0xaaaaaaaa | 15 | not solved |
| 0x2e05fe70 | 0xf0f0f0f0 | 16 | not solved |
| 0x64085a33 | 0x55555555 | 21 | not solved |
| 0x7a9cbbf8 | 0x7fffffff | 16 | not solved |

The verified sr=60 SAT candidate has **the lowest hw_dW56 of all 12** by a
margin of 6 bits.

## Statistical significance

Distribution of hw(dW[56]) over 20,000 random (M[0], fill) pairs is
binomial(32, 0.5): mean 16.00, stdev 2.82.

- P(hw_dW56 ≤ 7) = 0.12% (1 in 833)
- P(at least one of 12 candidates has hw_dW56 ≤ 7 by chance) = 1.4%

So observing this in our solved candidate is mildly statistically significant
under the null hypothesis of random correlation. **Not conclusive** — could
be random selection bias since we only have one positive example.

## Mechanistic story (speculative)

The sr=60 cascade requires precise control over W[60..63] in both messages
to trigger the e-register zeroing cascade. The schedule rule is:
```
W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
...
```

Although W[56] does NOT directly enter the W[60..63] computation, it's
computed FROM W[40..55] via schedule arithmetic. A candidate where dW[56]
is small means the schedule-propagated noise has remained contained
through round 56. By correlation, the dW[44..55] values may also be
better-controlled, making the W[60..63] schedule rule produce more
"signal-friendly" W values.

This is consistent with our `enrich_candidates.py` table showing that
0x17149975 also has dW[55]=12 (below the mean of 15.8) and dW[54]=23
(unusually high — but mixed signal).

## Falsification

This hypothesis predicts:
1. A new candidate with hw_dW56 ≤ 8 should solve sr=60 faster than typical
2. Candidates with hw_dW56 ≥ 20 should be much slower (or UNSAT) at sr=60

To test, we need MORE candidates. Existing Q3 mitm_scanner found 12 from
8 fills × 2^32 M[0] sweeps. Building a candidate scanner that prioritizes
low hw_dW56 would enable testing.

## Action items

1. Build `low_dw56_scanner.c`: brute-force M[0] sweeps that collect candidates
   passing both da[56]=0 AND hw_dW56 ≤ 10 (or some threshold)
2. Test 2-3 such candidates with Kissat seed-diverse runs
3. If hypothesis confirmed → use as pre-filter for any large-scale
   candidate search going forward

## Evidence level

**HYPOTHESIS.** Single positive observation against single null model.
Could be (a) genuine structural property, (b) random correlation, or
(c) selection artifact (we only ran sr=60 SAT to completion on this
specific candidate; others were never given equal compute).
