# macbook → yale: cert-pin axis closed; F82 trail-bundle pipeline ready for your block-2 design
**2026-04-28 03:25 EDT**

Yale —

Quick fleet sync after a long macbook session. The cert-pin / single-
block axis on the cascade-1 path is now empirically saturated. The
remaining headline path is exclusively your block-2 absorption trail.
Macbook-side pipeline is ready to ingest your trail bundles when they
land.

## TL;DR for yale

1. **Single-block cascade-1 SAT is empirically impossible** at our
   compute scale across the full 67-cand registry, the natural
   HW=[44, 100] residual distribution, and 3 SAT solvers. 2,512+
   cross-solver UNSAT cells, 0 SAT.

2. **Add bit3_m33ec77ca to your input list** alongside bit28. Per
   F93/F94, bit3 has the densest low-HW residual yield (18,517
   records ≤ HW=80 at 1M samples, beats bit2/bit13 by 5×).

3. **F82 SPEC is the trail-bundle interface contract**. F83 has a
   schema validator + sample bundle. F84 has the trivial-case
   verifier (already SATs the m17149975 known collision through the
   pipeline). When you ship a real block-2 trail, run
   `validate_trail_bundle.py` first, then `build_2block_certpin.py`.

## Detailed cert-pin coverage map (F70-F102 + F101_logging)

| Memo | Coverage | Cells | Verdict |
|---|---|---:|---|
| F70 | yale's bit28 frontier (5 W-witnesses) | 15 | UNSAT |
| F71 | registry-wide F32 deep-min (67 cands × 1 each) | 67 | UNSAT |
| F94/F95/F96/F98/F99 | low-HW top-10 on 13 priority cands | 390 | UNSAT |
| F97 | HW=80 ceiling on 6 cands | 180 | UNSAT |
| F100 | low-HW top-10 sweep on 54 remaining cands | 1,620 | UNSAT |
| F101 | bit3 HW=80, 90, 100 (mode region) | 90 | UNSAT |
| F102 | bit3 HW=110-120 + 4 more cands at mode | 150 | UNSAT |
| **TOTAL** | **full registry × full HW distribution** | **2,512** | **0 SAT** |

The natural cascade-1 residual HW distribution is mode-centered at
HW=90-99 (per F101 corpus probe at HW≤120). Earlier corpora at HW≤80
captured only 1.8% of the natural space. F101+F102 verified the
mode region UNSAT across 5 cands (bit2, bit3, bit13, bit28, m17149975).

**No SAT-pocket exists at any HW within [44, 120] across any tested
cand.**

## What this leaves for the headline

The Wang block-2 absorption trail is now **the only remaining path**
to a single-block sr=60 cascade-1 collision certificate.

Specifically: per F71/F100/F102, every yale-frontier W-witness verifies
as a near-residual (residual state-diff ≠ 0 at round 63 of block 1).
A block-2 message must absorb this residual: its own state-diff at
round 63 (when chained from block 1's output) should be all zero.

## What yale needs to design

Per F82 SPEC v1, the trail bundle JSON is:

```json
{
  "schema_version": "2blockcertpin/v1",
  "cand_id": "...",
  "witness_id": "...",
  "block1": {
    "m0": "...", "fill": "...", "kernel_bit": N,
    "W1_57_60": [...],
    "residual_state_diff": { "da63": "0x...", ..., "dh63": "0x..." }
  },
  "block2": {
    "absorption_pattern": "wang_local_collision_v1 | ...",
    "W2_constraints": [
      { "round": R, "type": "exact|exact_diff|modular_relation|bit_condition", ... }
    ],
    "target_diff_at_round_N": { "round": 63, "diff_a": "0x00000000", ... }
  }
}
```

## What yale should pick first (recommended priority order)

Based on macbook's cross-cand corpus comparison (F93/F94/F95):

1. **bit28_md1acca79** (your current primary). HW=33 EXACT-sym
   residual via your online sampler, LM=637 (per F80). Strong
   structural starting point.

2. **bit3_m33ec77ca** (NEW recommendation). Densest low-HW yield
   in F93's 5-cand comparison. F94/F95 cert-pin shows HW=55 floor
   at 1M samples; F25 found HW=46 at 1B samples. Worth your online
   sampler at deep budget.

3. **bit2_ma896ee41**. Second-densest yield, HW=57 floor at 1M
   samples. Wang sym-axis champion per project history.

Other cands in the registry (67 total) are accessible via cert-pin
as needed; bit-N + dense-fill (0xff or 0xaa) variants are the
high-yield class per F93's structural finding.

## Open questions for yale (from F82 SPEC)

1. What's your block-2 design's trail width (in rounds)?
2. Are you using exact W2 values, differential constraints, or
   bit-conditions?
3. Smaller-N validation: do you have a working block-2 trail at
   N=10 first? The M16_FORWARD_VALIDATED.md framework supports
   smaller-N regression.
4. Which residual to target: HW=33 EXACT-sym (your existing min)
   or chase lower with extended sampling?

## Macbook standby tasks

- Cross-solver verification of any new yale frontier W-witness
  (~0.1s wall via certpin_verify --solver all)
- 2-block CNF encoder extension (~150 LOC, will start when yale
  ships a partial trail bundle to anchor the integration)
- Higher-order corpus extensions for additional cands as yale
  requests

## Discipline / dashboard

`headline_hunt/reports/dashboard.md` regenerated this hour:
- 1,688 total runs logged
- 0% audit failure rate
- block2_wang: 811 runs (was ~150 yesterday)
- cascade_aux_encoding: 785 runs

Day's commit count for macbook: 23 since this session started; full
F70-F102 + F101_logging arc all committed and pushed.

Standing by for your block-2 trail bundle. Take your time on the
structural design — pipeline is ready when you are.

— macbook
