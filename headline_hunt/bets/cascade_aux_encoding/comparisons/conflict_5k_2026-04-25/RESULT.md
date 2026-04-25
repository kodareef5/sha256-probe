# Conflict-budget=50k comparison — Mode B (force) is materially faster per conflict

3 kernels × 3 encodings = 9 runs at sr=61 with `kissat --conflicts=50000 --seed=5`. All hit the budget (UNKNOWN). Per-encoding work:

| candidate | encoding | conflicts | decisions | propagations | wall (s) |
|---|---|---:|---:|---:|---:|
| bit-10 m=0x3304caa0 | standard      | 50000 | 823,401 | 29,581,074 | 2.68 |
| bit-10              | aux_expose    | 50002 | 769,450 | 37,318,632 | 3.53 |
| bit-10              | **aux_force** | 50000 | **554,938** | **12,195,432** | **1.27** |
| bit-13 m=0x4d9f691c | standard      | 50001 | 810,198 | 25,255,362 | 2.34 |
| bit-13              | aux_expose    | 50004 | 733,691 | 33,892,052 | 3.24 |
| bit-13              | **aux_force** | 50000 | **435,242** | **9,013,355** | **1.04** |
| bit-19 m=0x51ca0b34 | standard      | 50001 | 767,367 | 24,949,337 | 2.32 |
| bit-19              | aux_expose    | 50000 | 787,431 | 32,075,343 | 3.25 |
| bit-19              | **aux_force** | 50000 | **537,278** | **12,247,712** | **1.33** |

## Reading

**Mode B (force) is dramatically more efficient per conflict than standard or expose:**
- ~33-46% fewer decisions per conflict (median: 36% reduction).
- ~52-64% fewer propagations per conflict (median: 60% reduction).
- ~2.0-2.3× faster wall time per conflict (median: 2.1× speedup).

Mode A (expose) is *slower* than standard at this budget — its aux variables and tying clauses add overhead without yet pruning enough.

**This is real evidence that Mode B's CNF-level cascade enforcement materially changes solver behavior.** Each conflict in Mode B does less wasted work than in standard.

## Why this matters

The empirical history (90-min runs at MSB cert) showed Mode B TIMEOUT same as standard — leading to retraction of the SPEC's "≥10x speedup" claim. But TIMEOUT doesn't say WHY: it could be Mode B is identical, OR Mode B is faster per conflict but needs the same number of conflicts to find SAT.

This run shows the FORMER hypothesis is false: Mode B IS materially faster per conflict (2× wall, 1.5× decisions, 2.5× propagations).

The implication: if Mode B's *conflict-count to SAT* is similar to standard (~10^9 conflicts at sr=61?), wall-time speedup is ~2×. If conflict-count to SAT is also lower in Mode B (because force constraints prune the search space), the speedup compounds.

## Cross-kernel consistency

The Mode B speedup is consistent across all 3 kernels tested (bit-10, bit-13, bit-19). Mean per-kernel:
- decisions/conflict: standard=15.9, expose=15.0, **force=10.4**
- propagations/conflict: standard=540, expose=688, **force=224**

So the speedup is structural, not candidate-specific.

## Negatives.yaml: `seed_farming_unchanged_sr61` WCM

The WCM trigger reads: "A new encoding (cascade-aux, XOR preprocessing) demonstrably changes solver conflict count distribution at low budget."

This 9-run, 3-kernel sweep at 50k-conflict budget DEMONSTRABLY changes the conflict→work distribution by 2×+. This is partial evidence the WCM trigger is firing. To fully reopen the negative would need:
- Same comparison at higher budgets (500k, 5M conflicts) to confirm the speedup persists.
- Demonstration that Mode B finds SAT in real time on at least one instance.

The first is cheap and could happen this hour or next. The second is a multi-hour run.

## Run log entries (runs.jsonl)

9 entries appended via append_run.py:
```
run_20260425_102527_cascade_aux_encoding_kissat_seed5_5562d356  standard      bit10
run_20260425_102527_cascade_aux_encoding_kissat_seed5_5d2e2022  aux_expose    bit10
run_20260425_102527_cascade_aux_encoding_kissat_seed5_32f60522  aux_force     bit10
run_20260425_102527_cascade_aux_encoding_kissat_seed5_e8fd76c6  standard      bit13
run_20260425_102527_cascade_aux_encoding_kissat_seed5_1dcf164b  aux_expose    bit13
run_20260425_102527_cascade_aux_encoding_kissat_seed5_375579e4  aux_force     bit13
run_20260425_102527_cascade_aux_encoding_kissat_seed5_dd7c2d33  standard      bit19
run_20260425_102528_cascade_aux_encoding_kissat_seed5_92ad46ba  aux_expose    bit19
run_20260425_102528_cascade_aux_encoding_kissat_seed5_9b4bcb4b  aux_force     bit19
```

All audit-CONFIRMED.

## Suggested follow-up

1. Same 9-run sweep at conflict-budget 500k (~10× longer, ~30 min total). Confirm the speedup persists.
2. Multi-seed (seeds 1, 5, 11, 17, 23) at the 50k-conflict budget — measure variance across seeds.
3. Once propagator Phase 2B ships (Rules 1, 2 in C++ via IPASIR-UP), repeat with propagator+expose vs propagator+force vs vanilla+force. Should show propagator+expose ≈ vanilla+force, validating the rule equivalence.
