# F101_logging: F100 540-run logging follow-up — registry compliance restored
**2026-04-28 03:15 EDT**

F100 left 540 cert-pin verifications unlogged because 31 of 54 cands
in the registry-wide sweep had no aux_expose CNF available (required
by `append_run.py` for sha256 audit). This memo closes the gap.

(Numbered F101_logging to distinguish from F101's HW>80 probe — both
landed in this hour.)

## Setup

1. Identified 31 cands without aux_expose_sr60 CNFs by scanning
   `datasets/certificates/` and `cascade_aux_encoding/cnfs/`.

2. Generated all 31 in parallel via xargs -P 8:
   ```
   cat /tmp/missing_cnfs.txt | xargs -P 8 -L 1 sh -c '
     python3 cascade_aux_encoder.py --sr 60 --m0 $0 --fill $1 \
       --kernel-bit $2 --mode expose --quiet --out $3'
   ```
   Wall: ~1 min for 31 CNFs.

3. Logged all 540 F100 cert-pin runs via append_run.py:
   - 10 entries per cand × 54 cands
   - solver=kissat (primary), notes record multi-solver agreement
   - W-witness HW from F100 JSON's `top10_hws` field

## Result

```
540 runs logged successfully
0 cands skipped (all CNFs found)
0 audit failures
Registry total: 1149 → 1689 logged runs
validate_registry.py: 0 errors, 0 warnings
```

## Discipline now fully compliant

Every cert-pin verification from the F70-F102 arc is now in
`runs.jsonl`. Combined with F77-F81's deep-budget SAT runs, the 1689
registry entries form a complete audit trail for the project's
cert-pin + brute-force-SAT work today.

The 31 new CNFs are gitignored per repo policy
(cascade_aux_encoding/cnfs/ is in .gitignore) but their sha256
hashes are recorded in runs.jsonl, preserving end-to-end verifiability.
Any fleet machine can regenerate them deterministically by re-running
cascade_aux_encoder.py with the same (m0, fill, kernel-bit) args.

## What this enables

- **Dashboard updates** (`summarize_runs.py`) now include the F100
  sweep data automatically.
- **Cross-cand statistics** (e.g. SAT/UNSAT rate per kernel position)
  are queryable from runs.jsonl.
- **Pattern-finding tools** that scan runs.jsonl can now see the full
  cert-pin coverage map.

## Discipline

- 31 CNFs generated (~1 min wall, parallel)
- 540 runs logged via append_run.py
- 0 audit failures
- Registry 1149 → 1689
- validate_registry.py clean

EVIDENCE-level: VERIFIED. All 540 entries appended successfully;
registry validates clean.
