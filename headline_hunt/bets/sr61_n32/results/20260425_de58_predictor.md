# de58 distribution: structural predictor for sr=61 candidate promise

## What I built

Extended the apath_first_n8.c finding (de58 class 4× density variation at N=8) to N=32. For each of the 9 cross-kernel candidates, sample 16384 random W57 values and tabulate the de58 distribution.

`headline_hunt/bets/sr61_n32/de58_histogram.py` — single-file Python, 100 LOC, runs in <2s for all 9 candidates.

## Result: dramatic candidate-level non-uniformity

| Candidate | distinct de58 values (of 16384) | Entropy (bits) | concentration |
|---|---:|---:|---|
| MSB (bit-31) | 15393 (94%) | 13.88 | nearly uniform |
| bit-0 | 14532 (89%) | 13.77 | nearly uniform |
| bit-6 | 14510 (89%) | 13.76 | nearly uniform |
| bit-10 (σ1) | 12901 (79%) | 13.55 | nearly uniform |
| bit-11 (σ1) | 10371 (63%) | 13.18 | mild concentration |
| bit-13 | 12916 (79%) | 13.55 | nearly uniform |
| bit-17 | 16138 (98%) | 13.97 | nearly uniform |
| **bit-19** | **256 (1.6%)** | **7.99** | **HEAVY: 6 bits of concentration** |
| **bit-25** | 4022 (25%) | **11.81** | **moderate: 2.2 bits** |

## bit-19 in particular: extraordinary structure

**bit-19's de58 takes only 256 distinct 32-bit values across all sampled W57.** That's a structural fact (not sampling noise — 256 is the empirical ceiling of 16384 samples).

de58 effectively occupies an **8-bit subspace of 32 bits** for this candidate. The cascade's a-path constraints REDUCE the de58 image at bit-19 by a factor of 2^24.

## Why this is a candidate predictor

This addresses BET.yaml#true_sr61_n32's identified gap: "no structural predictor identified that distinguishes promising from hopeless candidates."

For sr=61 cascade-DP search:
- Naive search: 2^96 (W57, W58, W59) input space.
- Per-candidate: cascade-sr=61 SAT prob ~2^-32 per the structural finding.
- WITH de58 partitioning: search space becomes (image-of-de58) × (per-class-W57-count) × W58 × W59.

For bit-19 at N=32:
- de58 image: 2^8 = 256 (empirical)
- Per-class W57 average: 2^32 / 256 = 2^24
- Effective search: 2^8 × 2^24 × 2^32 × 2^32 = 2^96 (same as naive at full coverage)
- BUT structural concentration means SAT solutions likely cluster in a few de58 classes. Empirical apath_first_n8 at N=8 showed 4× variation across classes.
- If similar at N=32, focusing on top-quartile de58 classes saves 4× expected compute on bit-19.
- And per-class search can be 2^24 W57 (much smaller than naive 2^32 search) within each class.

## Cross-validates with other findings

bit-19 is THE SAME candidate that:
- Showed 32 max bits forced in a single Rule 4 sample (commit `e814b3d`) — highest among 9 kernels
- Has 209 Rule 4 fires per 50k conflicts, 4.18× cadical Mode B speedup (commit `f9f212b`) — highest non-MSB

Three independent measurements (de58 entropy, Rule 4 firing density, Mode B speedup) point at bit-19 as the most-concentrated kernel. **Strong corroboration that bit-19's underlying structure is unusually tight.**

bit-25 secondary concentration is also corroborated — highest Rule 4 firing rate (249).

## What this implies for the headline-hunt

**If any cascade-sr=61 SAT exists, bit-19 (m=0x51ca0b34, fill=0x55555555) is the most likely place to find it.**

The structural concentration suggests:
1. Lower effective entropy in the search space.
2. More-deterministic constraint propagation (CDCL would propagate further on average).
3. Smaller "haystack" for the needle.

For a multi-hour validation experiment (4h+ kissat or cadical), **prioritize bit-19 over the priority-cert MSB candidate.** The MSB has 94% de58 entropy (nearly uniform) — least structural concentration.

## Concrete next-step

A future user-authorized multi-hour run should target:
1. bit-19 (best structural promise per de58, Rule 4, Mode B measurements)
2. bit-25 (secondary structural promise)
3. bit-11 (third — entropy 13.18, sigma1-aligned)

Skip bit-31 MSB despite cert existence — the cert is a single point in a 94%-uniform distribution, not a structural attractor.

## Compute spent

~1.4s on macbook for the 9-candidate sweep at 16k samples each.

## Caveats

- 16k samples is a coarse estimate. A full 2^32 sweep would give exact de58 image sizes. Expected runtime: ~7 min/candidate × 9 = ~1 hour. Worth doing if user authorizes.
- The "structural concentration → SAT-friendly" conjecture is plausible but UNPROVEN. The actual SAT distribution per de58 class needs measurement (likely from the apath_first_n8 prototype scaled to N=32).
- bit-19 might still have ZERO sr=61 SAT solutions; structural concentration doesn't guarantee SAT existence, just that IF one exists the search is faster.

## Files

- `de58_histogram.py` — runnable predictor
- `results/de58_n32_2026-04-25.jsonl` — 9-candidate output
- This writeup

## What this gives the fleet

A new structural-predictor diagnostic. Cheap (1.4s for 9 candidates). Future workers picking up sr61_n32 should:
1. Run de58_histogram.py first
2. Pick the candidates with lowest entropy
3. Allocate multi-hour budget to those

The bet portfolio's "where to spend CPU-h" question now has empirical guidance.
