# Cross-candidate residual corpus comparison
**2026-04-25 evening** — block2_wang residuals/by_candidate/

## What

Built block-1 residual corpora for the SURPRISE and BOTTOM candidates from
today's de58 family analysis to check whether their de58 structural
distinctiveness translates to better block2_wang residuals.

| Candidate                       | de58 image | hardlock | corpus records | min HW | max HW |
|---------------------------------|-----------:|---------:|---------------:|-------:|-------:|
| msb_m17149975 (cert)            |     82,826 | 10/32    | (existing 104k corpus) |     62 |    136 |
| **msb_m9cfea9ce (SURPRISE)**    |      4,096 | 10/32    |          3,735 |     62 |    127 |
| **msb_m189b13c7 (BOTTOM)**      |    130,049 |  4/32    |          3,787 |     63 |    126 |

Same 200k samples, same HW threshold (80), same kernel (MSB bit-31),
different m0/fill candidates.

## Finding

**de58 structural distinctiveness does NOT translate to lower-HW residuals
under random sampling.** All three candidates have min HW 62-63 across 200k
samples — the structural floor identified in the bet's earlier negative
results.

This CONFIRMS the bet's BET.yaml claim ("Random sampling and hill-climb are
CLOSED") for the SURPRISE and BOTTOM candidates as well. Adds 2 data points
to the existing 1-candidate negative.

## Implication for the bet

The de58 family of findings (image-size predictor, hardlock pattern, low-HW
reachability) are structurally interesting but **do not predict block-1
residual quality** at the random-sampling level. The path to <24-HW
residuals (Wang threshold) remains backward-construction (M10/M12/M16-MITM
ladder per SCALING_PLAN), not random sampling on different candidates.

This is a **narrow EVIDENCE-level closure**: random sampling is closed
across ALL tested MSB candidates (including those de58-distinctive), not
just the cert.

## Files

- `corpus_m9cfea9ce_fill00000000.jsonl` — SURPRISE corpus (3735 records)
- `corpus_m189b13c7_fill80000000.jsonl` — BOTTOM corpus (3787 records)
- This file
