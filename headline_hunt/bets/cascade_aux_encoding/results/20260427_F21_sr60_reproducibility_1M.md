# F21: sr=60 reproducibility at 1M conflicts — 10 seeds, all UNKNOWN
**2026-04-27 01:15 EDT**

Empirical reproducibility test on the verified sr=60 cert candidate
(msb_m17149975) at modest budget. Tests whether the historical 12h
seed=5 success was specific to that seed or whether other seeds find
SAT at moderate budgets.

## Setup

- CNF: cascade_aux Mode A sr=60 for msb_m17149975 (no hints)
  `headline_hunt/datasets/certificates/aux_expose_sr60_n32_bit31_m17149975_fillffffffff.cnf`
- 13,248 vars, 54,919 clauses, audit CONFIRMED
- 10 seeds × 1M conflicts (60s wall cap)
- Single-threaded sequential (overnight kissat using 6 cores)

## Result

| seed | wall | status |
|---:|---:|---|
| 1 | 27.38 s | UNKNOWN |
| 2 | 27.09 s | UNKNOWN |
| 3 | 27.46 s | UNKNOWN |
| **5** | 26.73 s | UNKNOWN |
| 7 | 26.18 s | UNKNOWN |
| 11 | 27.68 s | UNKNOWN |
| 13 | 27.26 s | UNKNOWN |
| 17 | 25.26 s | UNKNOWN |
| 19 | 24.60 s | UNKNOWN |
| 23 | 28.04 s | UNKNOWN |

**0/10 seeds returned SAT at 1M conflicts.** Including seed=5, the
historical SAT-finding seed.

## Interpretation

The historical seed=5 12h SAT find used MUCH more than 1M conflicts.
Estimating: 12h = 43,200s wall. At ~37K conflicts/sec (1M/27s), seed=5
would have processed ~1.6 BILLION conflicts to find SAT. That's
~1600× the budget tested here.

This is consistent with the project's empirical claim that sr=60 finds
require deep search. The seed=5 result is a SPECIFIC SEED + DEEP BUDGET
combination, not "any seed at moderate budget."

## Implications for paper

The "Why this seed succeeded" section (Section 4 of paper outline)
should include:
1. **At 1M conflicts: 0/10 seeds find SAT** (this memo)
2. **At ~1.6B conflicts: seed=5 finds SAT** (historical, 12h)
3. **At 100M conflicts (Phase A overnight): TBD by ~14:30 EDT today**
4. The Viragh-style "TIMEOUT > 7200s" claim is consistent — at his
   wall budget, no seeds tested found SAT.

The project's contribution is showing that **at sufficient budget on a
specific m0, kissat does find sr=60 SAT** — the predicted "structural
barrier" yields to deeper search.

## What this rules in/out

- **Doesn't rule out**: other seeds finding SAT at deep budget. Only
  seed=5 has been validated; other seeds at 12h wall have not all been
  tested.
- **Confirms**: 1M conflicts is far below the threshold for sr=60 SAT
  on this cand. The wall budget needs to be ~1B+ conflicts.
- **Implication for cross-cand search**: any sr=60 search needs deep
  budget. Don't expect SAT at moderate kissat budgets.

## Discipline ledger

10 runs to be logged via append_run.py (next commit). Both CNFs
audit CONFIRMED.

EVIDENCE-level: VERIFIED at the budgets tested. Higher-budget
verification (for SAT finding rate per seed) would require ~10× 12h
wall budgets — not feasible without dedicated cluster compute.
