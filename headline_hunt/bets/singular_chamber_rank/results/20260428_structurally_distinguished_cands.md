# Structurally distinguished cands — priority targets for non-uniform BDD marginal investigation

## Context

The negatives.yaml entry `bdd_marginals_uniform` was REOPENED on 2026-04-26
(by macbook, after linux_gpu_laptop's discovery on bit=19 m=0x51ca0b34).
The refined scope: BDD marginals are uniform on GENERIC cands but
NON-UNIFORM on STRUCTURALLY DISTINGUISHED cands (de58_size << median).

That negative's refined_scope_after_reopen states: "SAT branching
heuristic that prioritizes locked-bit positions on structured cands is
untested but mathematically supported."

**This memo identifies the priority target list** of structurally
distinguished cands so future non-uniform-marginal investigations have
a concrete cand set to test.

## Methodology

For each of the 67 cands in `headline_hunt/registry/candidates.yaml`,
extracted `metrics.de58_size`. Computed distribution statistics.
Flagged cands in the lowest decile (de58_size ≤ 4096, ~40× below the
~50K median) as STRUCTURALLY DISTINGUISHED.

## Distribution

- Total cands: 67
- de58_size range: [256, 130086]
- Median: 51,578
- Mean: 50,667
- Standard deviation: 38,809
- Lowest-decile threshold: 4,096

## Priority target list (structurally distinguished cands)

| cand id | de58_size | de58_hardlock_bits | hard_bit_total_lb |
|---|---|---|---|
| **bit19_m51ca0b34_fill55** | 256 | 13 | 15 |
| **bit25_ma2f498b1_fillff** | 1024 | 6 | n/a |
| **bit4_m39a03c2d_fillff** | 2048 | 12 | n/a |
| **bit28_md1acca79_fillff** | 2048 | **15** | n/a |
| **msb_m9cfea9ce_fill00** | 4096 | 10 | 20 |
| **bit25_m09990bd2_fill80** | 4096 | 13 | 22 |
| **bit15_m28c09a5a_fillff** | 4096 | 14 | n/a |

Plus borderline (de58_size 8187-8190):
- bit20_m294e1ea8_fillff: 8187 / hardlock 15
- bit29_m17454e4b_fillff: 8187 / hardlock 12
- bit26_m11f9d4c7_fillff: 8190 / hardlock 9

## Significant observations

### bit19_m51ca0b34 is the most extreme
de58_size = 256 (200× below median). Already triggered the reopen of
bdd_marginals_uniform. This is the canonical "structurally
distinguished" cand.

### Yale's primary md1acca79 IS structurally distinguished
de58_size = 2048 (25× below median). Highest hardlock_bits in the
list (15). Yale's empirical HW=33 EXACT-sym at LM=679 success on this
cand may be CAUSALLY LINKED to its structural distinction — yale's
4-axis Pareto sampler may implicitly exploit the 15 locked bits + low
de58 image.

This connects the bdd_marginals_uniform reopened negative to yale's
empirical advantage: yale finds md1acca79 productive precisely
BECAUSE it's structurally distinguished.

### 5 additional un-investigated cands
The 5 cands {ma2f498b1, m39a03c2d, m9cfea9ce, m09990bd2, m28c09a5a}
are below the de58_size ≤ 4096 threshold but have NOT yet been
investigated for non-uniform BDD marginals. These are the natural
priority targets for the singular_chamber_rank bet's next iteration.

## Implications for the singular_chamber_rank bet

Per `headline_hunt/registry/mechanisms.yaml`, this bet is owned by
linux_gpu_laptop, status: in_flight. Last_updated 2026-04-27.

Specifically actionable:
1. **Test non-uniform BDD marginals on the 5 un-investigated cands**
   above. Same methodology as the bit19 result on 2026-04-26.
2. **If non-uniform marginals confirmed** on additional cands, the
   refined claim ("falsified on structurally distinguished cands")
   strengthens from N=1 to N=5+ examples.
3. **Cross-check with hardlock_bits**: cands with high hardlock_bits
   should empirically show the most concentrated marginals (more bits
   forced = more SAT branching guidance).

## Implications for yale's heuristic

Yale's empirical HW=33 floor is on md1acca79 (de58_size=2048,
hardlock=15). If the structural distinction explains yale's success,
then:
- **Other low-de58_size cands should be EQUALLY YIELD-FRIENDLY** for
  yale's heuristic
- yale should test on bit19_m51ca0b34_fill55 (de58_size=256, even more
  distinguished) — predicted HW floor possibly LOWER than HW=33
- Cands with high de58_size (e.g., bit18_m99bf552b at 130086) are
  predicted UNFAVORABLE for yale-style sampling

This is a TESTABLE prediction yale's compute can validate.

## Connection to BP-Bethe principles framework

The recent F134-F139 thread calibrated BP-Bethe on cascade_aux N=32 at
~2-5 sec wall time. BP-Bethe gives APPROXIMATE marginals via Bethe
approximation. On structurally distinguished cands:
- Standard BP marginals should be NON-UNIFORM (matching BDD marginal
  result for bit19)
- BP-derived hardlock-bit identification is poly-time alternative to
  full BDD compilation
- BP could surface the 13-15 hardlock bits in seconds vs BDD's
  exponential construction

This is a **bridge between bdd_marginals_uniform refined scope and
the BP-Bethe algorithmic candidate from the principles framework**.

## Status

Pure data analysis on existing candidates.yaml. No compute used.
Priority target list of 7 (or 10 with borderline) structurally
distinguished cands now documented for the singular_chamber_rank bet.

The reopened negative `bdd_marginals_uniform` now has an explicit
priority test set to extend its refined scope from N=1 example to
N=5+ examples.

## Files

- This memo: `bets/singular_chamber_rank/results/20260428_structurally_distinguished_cands.md`
- Data source: `headline_hunt/registry/candidates.yaml`
- Reopened negative: `headline_hunt/registry/negatives.yaml#bdd_marginals_uniform`
- Original bit19 trigger result:
  `bets/singular_chamber_rank/results/20260426_D2_bit19_marginals_nonuniform.md`
