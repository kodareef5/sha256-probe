# cascade_aux audit-rot fix: 16 stale sr=61 CNFs regenerated
**2026-04-26 03:10 EDT** — cascade_aux_encoding bet — discipline fix.

## What I found

Routine audit sweep across all 100 cascade_aux CNFs found **16 with
CRITICAL_MISMATCH verdicts**: sr=61 filename but sr=60 content (var/clause
counts in the sr=60 fingerprint range, not sr=61).

Specifically: aux_{expose,force}_sr61_n32_bit{0,6,10,11,13,17,19,31}_*.cnf
× 8 candidates × 2 modes = 16 CNFs.

## Root cause

Encoder was UPDATED 2026-04-25 ("widened 2026-04-25 for modular-diff aux
(Phase 2C-Rule4); cap < sr61 range" comment in `cnf_fingerprints.yaml`).
The update added modular-diff aux variables to sr=61 CNFs, increasing
their var/clause counts. Old sr=61 CNFs from BEFORE the encoder update
no longer match the new sr61 fingerprint range — they fall in sr60 range.

Audit verdicts at original run-time were CONFIRMED (under old fingerprints).
After fingerprint-range update, those same CNFs became CRITICAL_MISMATCH.

## Risk assessment

The 16 stale CNFs were used in solver runs logged in `runs.jsonl` with
`sr_audit: CONFIRMED`. Examples:
- `run_20260425_122859_cascade_aux_encoding_cadical_seed5_5544e20c`
- `run_20260425_122859_cascade_aux_encoding_cadical_seed5_82d497e0`
- ... and many more from the 9-kernel cadical 50k sweep

These runs were tagged sr=61 but ACTUALLY ran sr=60-encoded CNFs. The
solver behavior data is for sr=60 content not sr=61. Those past
measurements are **misattributed**; the bet's earlier "Mode B 2-3.4×
front-loaded preprocessing" speedup characterization may have been
on sr=60 content, not sr=61.

## Fix applied

Regenerated all 16 stale CNFs using the current encoder. All 16 now
audit CONFIRMED. CNF sha256 hashes will differ from the runs.jsonl
records — older runs are now disconnected from the current files.

## Implications

1. **Past Mode B characterization may need re-verification at sr=61.**
   The bet's claim of 2-3.4× speedup at 50k conflicts may be SR-LEVEL-
   misattributed.
2. **Future runs against the regenerated CNFs will properly target sr=61.**
3. **Discipline lesson**: when fingerprint ranges change, need to
   automatically trigger re-audit of all referenced CNFs and flag
   mismatches.

## Concrete handoff for next worker

If precision matters: re-run a subset of Mode B comparison at properly
audited sr=61 CNFs, compare to the past sr=60-misattributed numbers.
~30 min compute would resolve the question.

## Files

- 16 regenerated CNFs in `headline_hunt/bets/cascade_aux_encoding/cnfs/`
- All 100 cascade_aux CNFs now audit CONFIRMED.

## Status update

- The cascade_aux_encoding bet's Mode B characterization (which heavily
  relied on sr=60 vs sr=61 comparison) is now VERIFIED-LEVEL on sr=60
  side but may have past-data attribution gaps on sr=61 side.
- Affected runs: ~16 of 130 total cascade_aux runs in dashboard
  (~12% misattributed).
