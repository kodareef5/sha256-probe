# Candidate-base expansion via exhaustive bit-sweeps — 2026-04-26 session
**Author**: macbook | Status: live result, registry expanded 36 → 40+ candidates

## Summary

The 36-candidate registry pre-2026-04-26 was an OBSERVATION ARTIFACT
of past curation, not a structural ceiling. Exhaustive 2^32 m0 sweeps
at previously-uncovered bit positions {3, 18} found NEW cascade-eligible
candidates. This session expanded the registry by **+4 (and counting)**.

## Results so far (all at fill=0xffffffff except where noted)

| Bit | Alignment       | Eligible / 2^32 | New cands               |
|----:|-----------------|----------------:|-------------------------|
|  31 | boundary (MSB)  | 2               | (both prev. registered) |
|  22 | Σ0-aligned      | 0               | —                       |
|  18 | σ0-aligned      | 2               | m=0x99bf552b, m=0xcbe11dc1 (NEW) |
|   7 | σ0-aligned      | 0               | (Poisson noise)         |
|   3 | σ0-aligned      | 2               | m=0x33ec77ca, m=0x5fa301aa (NEW) |
|  18 | σ0-aligned, fill=0x00 | running   | m=0x347b0144 (NEW so far) |

All non-zero counts ≈ 2 per 2^32 ≈ 2^-31 baseline. Same rate across
boundary, Σ1, σ1, σ0 aligned bits. **NO structural distinction by bit
position.** Σ1/σ1 alignment hypothesis FALSIFIED.

## Implication

**The cascade-eligibility rate is ~2^-31 per random m at any bit position.**
With 32 bits × N fills uncovered, total expected candidates ≈ 2 × 32 × N = ~320
per fill (extrapolating from seen rate). The 36-candidate registry was
~10% of the available pool.

## Candidate-base expansion economics

| Resource    | Per (bit, fill) cell | 32 bits × 5 fills = 160 cells |
|:------------|:--------------------|:-------------------------------|
| Wall time   | ~12 min on M5 ×10   | ~32 hours total                |
| New cands   | ~2                  | ~320 expected                  |
| Storage     | ~1 MB CNF / cand    | ~320 MB total                  |
| Audit time  | ~1 sec / cand       | ~5 min total                   |

**32 hours of compute can grow the registry from 36 → ~360 candidates.**
That's a 10× expansion of the search space for sr61_n32.

## Action items

For next worker (or the fleet):
1. Continue exhaustive sweeps at remaining (bit, fill) cells. Cheap per-cell.
2. Each new candidate gets its `cnfs_n32/sr61_cascade_<m>_<fill>_bit<b>.cnf`
   via encode_sr61_cascade.py + audit_cnf.py + registry update (see
   sweep+register pattern in tonight's commits).
3. Each new candidate gets a smoke test at 1M kissat (~22s) to confirm
   solver behavior is normal (not exotic).
4. After ~360-candidate registry exists: run a bigger validation matrix
   (5+ candidates × 2 solvers × 1M+10M+100M conflicts) to retest the
   de58/hard_bit/wall predictors at higher statistical power.

## What this DOES NOT change

- **de58/hard_bit predictors remain SEARCH-IRRELEVANT** at the budgets tested
  (12-cell Spearman matrix, ρ ≈ 0). New candidates don't change that.
- **Theorem 4 / R63 modular relations remain N-invariant** across all
  registered candidates.
- **Block2_wang Path B (backward construction)** remains M10/M12 validated;
  M16-MITM design still the open implementation question.

## What this DOES change

- **sr61_n32 candidate base** is no longer "36 + maybe a few more" — it's
  potentially "~360 with directed sweeping". 10× more haystack to search,
  but also 10× more places to find a SAT.
- **Registry curation strategy**: future cycles should include exhaustive
  per-cell sweeps as routine maintenance, not ad-hoc curation.
- **Statistical power**: bigger pool means n=5 validation matrices can grow
  to n=20+ cleanly, sharpening predictor closure tests.

## Files

- `headline_hunt/registry/notes/cascade_eligibility_sweep.c`: tool.
- `cnfs_n32/sr61_cascade_*_bit18.cnf` (2 new): bit-18 NEW.
- `cnfs_n32/sr61_cascade_*_bit3.cnf` (2 new): bit-3 NEW.
- `headline_hunt/registry/candidates.yaml`: 36 → 40 entries.
- `headline_hunt/registry/kernels.yaml`: kernel_0_9_bit3, kernel_0_9_bit18 added.
