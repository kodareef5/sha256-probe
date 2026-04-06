# Schedule Density Analysis: sigma1 Coupling Distribution

## Finding

dW[61] and dW[62] (the schedule differences at rounds 61-62) follow
near-identical binomial distributions centered at hw=16 when W[59]
and W[60] are chosen randomly.

## Key Probabilities (from 10M random samples, cand3)

| Metric | Value |
|--------|-------|
| P(dW61_hw ≤ 10) | 2.5% (1 in 40) |
| P(dW62_hw ≤ 10) | 2.5% (1 in 40) |
| P(both ≤ 10) | 0.063% (1 in 1,600) |
| Min observed dW61_hw | 3 |
| Min observed dW62_hw | 2 |
| Distribution center | hw=16 (both) |

## Implications

1. **GPU pre-screening** of W[59]/W[60] pairs identifies the 0.06% sweet
   spot where both schedule constraints are favorable.

2. Our **GPU cube ranking** (best hw=74 with da57=0) operates in this
   favorable regime — consistent with the density analysis.

3. The schedule coupling is **random-looking** (binomial) — there's no
   hidden structure to exploit beyond statistical filtering.

4. **dW[61]=0 requires extreme luck** — only ~10^-10 probability for
   random pairs, confirmed by our GPU search (found at 20B samples).
   But it's UNSAT when combined with collision (structurally impossible).

## Evidence Level

EVIDENCE: consistent across 10M samples, distributions are symmetric
and candidate-independent (checked for cand3, expected same for others
based on Q3's thermodynamic uniformity).
