# sr=60 Mode B sanity test (cert candidate)
**2026-04-25 evening** — cascade_aux_encoding bet sanity check.

## Question

Does kissat with Mode B (cascade_aux force) encoding find the known sr=60
SAT (cert m17149975) at modest conflict budgets?

## Result

| Budget | Status | Wall | dec/conf | conf/s |
|-------:|--------|-----:|---------:|-------:|
| 1M     | TIMEOUT | 19s |     5.73 |  51,775 |
| 10M    | TIMEOUT | 278s|     3.81 |  36,078 |

**No SAT at either budget.** The historical sr=60 cert was found by kissat
seed=5 at 12+ wall hours; modest budgets don't find it via Mode B encoding.

## Interpretation

This MATCHES the bet's existing characterization (Mode B is front-loaded
preprocessing speedup, not a path to SAT discovery). Confirms the encoder
hasn't drifted: CNF audits CONFIRMED, kissat runs to completion, no
errors. Mode B is healthy but limited.

Cross-comparison with sr61 cascade kissat 10M cert (validation matrix):
- sr=60 Mode B 10M: 3.81 dec/conf, 36k conf/s
- sr=61 cascade 10M: 3.45 dec/conf, 31k conf/s (uncontended)

sr=60 has HIGHER dec/conf (3.81 vs 3.45) despite being a structurally
easier problem (12h SAT find historically). Mode B's front-loaded
preprocessing doesn't translate to lower dec/conf at this budget.

## Implication

- Mode B is sanity-OK; encoder + audit pipeline working.
- 10M conflict budget is below the threshold for sr=60 Mode B SAT find.
- For a future "Mode B can find sr=60 SAT" experiment, budget would need
  to be 12h-equivalent (~10G+ conflicts at this rate). NOT authorized
  tonight.

## Files

- `headline_hunt/bets/cascade_aux_encoding/runs/20260425_sr60_modeB_sanity.log` (1M)
- `headline_hunt/bets/cascade_aux_encoding/runs/20260425_sr60_modeB_10M_sanity.log` (10M)
- runs.jsonl entries 17579342 (10M), 16c269ae (1M)
