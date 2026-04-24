# First end-to-end solver run — pipeline validated, SPEC prediction NOT confirmed at 10min

**Date**: 2026-04-24
**Machine**: macbook
**Run ID**: `run_20260424_225636_cascade_aux_encoding_kissat_seed5_011585d6`
**Status**: TIMEOUT at 600s budget

## What was tested

`SPEC.md` line: *"For sr=61 TRUE instances, Mode B is expected to UNSAT fast (seconds to minutes, not hours) because Theorem 5 says the cascade break has P=2^{-N} — the schedule constraint on dW[61] almost always conflicts with the cascade requirement."*

Test:
- CNF: aux-force sr=61 for candidate `cand_n32_bit10_m3304caa0_fill80000000`
- Audit: CONFIRMED via fingerprint
- Solver: kissat 4.0.4
- Seed: 5
- Wall budget: 600s

Result: **TIMEOUT (exit code 0, status UNKNOWN)** at 600s. Neither SAT nor UNSAT in 10 minutes.

## What this means for the SPEC

The "fast UNSAT (seconds to minutes)" prediction for Mode B on sr=61 did NOT hold within the 10-minute budget on this single instance. Three possible explanations:

1. **UNSAT genuinely requires more time**: 10 min may simply be too short. Theorem 5 says cascade-DP sr=61 is structurally hard with success probability 2^{-N}; that same structure could also make UNSAT proof hard for a CDCL solver. Retry with 1h or 4h budget would settle this.

2. **Mode B's force constraints aren't tight enough alone**: The 512 force-cascade clauses encode Theorems 1-4 directly, but kissat may still need to traverse a large search space because the underlying CSA adders carry implicit constraints CDCL has to learn. The bet's pairing with `kc_xor_d4` (XOR preprocessing) may be needed to expose more structure.

3. **The cascade-DP solution exists** (would be SAT, not UNSAT): Theorem 5 says probability 2^{-N}=2^{-32} that cascade-DP sr=61 has a solution, NOT zero. A SAT result would be a headline — sr=61 collision found via cascade. But 600s is also short for SAT discovery.

## Revising the SPEC

The SPEC's "seconds to minutes" estimate is now empirically refuted at 10min. Update the prediction to:

> Mode B on sr=61 is expected to either:
> - find SAT within compute budget (unlikely; would be a headline) OR
> - reach UNSAT after substantially more time than seconds-to-minutes (likely hours at 600s/instance).
>
> A 600s-per-seed × 10-seed sweep across 5 candidates = 50 CPU-hours is the minimum
> reasonable trial. Earlier termination on a "fast UNSAT" signal is no longer expected.

Will update `SPEC.md` directly in a follow-up commit.

## Pipeline validation (positive)

End-to-end discipline confirmed working:
- `cascade_aux_encoder.py --mode force` produced a valid CNF
- `audit_cnf.py` returned CONFIRMED via the `sr61_n32_cascade_aux_force` fingerprint
- `kissat --seed=5` ran cleanly with 600s timeout
- `append_run.py` captured: git commit, machine, CNF sha256, audit verdict, all timing info — auto-populated, no manual mistakes possible
- `summarize_runs.py` immediately picked up the new run; dashboard shows 1 run, 0 audit failures

The first runs.jsonl entry is in place. Future runs from any fleet machine will append cleanly.

## Concrete follow-up for next worker

1. **Longer budget on Mode B sr=61**: same instance, 4h budget. Records: did it eventually UNSAT? At what time?
2. **Mode B sr=60 sanity**: known-SAT instance (MSB cert) with Mode B. SPEC predicts ≥10x speedup over standard. ~5min budget should suffice if speedup is real; longer is also informative.
3. **Mode A vs Mode B vs standard, multi-seed**: 5 seeds × 3 encodings × 1h each = 15 CPU-h on the MSB candidate, gives a real comparison rather than a single anecdote.

These are the right next experiments. The pipeline is ready; the question is just compute allocation.

## Run record

```json
{
  "run_id": "run_20260424_225636_cascade_aux_encoding_kissat_seed5_011585d6",
  "bet_id": "cascade_aux_encoding",
  "candidate_id": "cand_n32_bit10_m3304caa0_fill80000000",
  "kernel_id": "kernel_0_9_bit10",
  "encoder": "cascade_aux_force_v1",
  "solver": "kissat",
  "solver_version": "4.0.4",
  "seed": 5,
  "status": "TIMEOUT",
  "wall_seconds": 600,
  "sr_audit": "CONFIRMED"
}
```
