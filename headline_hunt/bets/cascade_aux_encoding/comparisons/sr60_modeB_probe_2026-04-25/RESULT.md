# sr=60 Mode B sanity probe — Mode B advantage shrinks at sr=60

Pulse-suggested move: "sr=60 Mode B sanity test." Tested whether Mode B finds SAT on 4 non-MSB candidates at sr=60, plus comparison against Mode A.

## Setup

- Solver: CaDiCaL 3.0.0
- Seed: 5
- Budget: 1,000,000 conflicts
- 4 non-MSB candidates × 2 encodings = 8 runs
- All sr=60 CNFs from `bets/cascade_aux_encoding/cnfs/`

## Results

| candidate | encoding | status | conflicts | wall (s) |
|---|---|---|---:|---:|
| bit-10 | aux_force  | UNKNOWN | 1,000,001 | 24.32 |
| bit-13 | aux_force  | UNKNOWN | 1,000,000 | 24.92 |
| bit-19 | aux_force  | UNKNOWN | 1,000,000 | 24.81 |
| bit-25 | aux_force  | UNKNOWN | 1,000,004 | 24.19 |
| bit-10 | aux_expose | UNKNOWN | 1,000,002 | 28.36 |
| bit-13 | aux_expose | UNKNOWN | 1,000,000 | 23.96 |
| bit-19 | aux_expose | UNKNOWN | 1,000,000 | 27.36 |
| bit-25 | aux_expose | UNKNOWN | 1,000,000 | 26.37 |

Total wall: 99 + 107 = 206 s for 8 × 1M-conflict runs.

## Aggregates

| metric | force mean | expose mean | force advantage |
|---|---:|---:|---:|
| wall (s) | 24.56 | 26.51 | **1.08×** |

Compare to sr=61 (from cadical_50k_full9 at 50k conflicts):
| sr-level | budget | force mean | expose mean | force advantage |
|---|---:|---:|---:|---:|
| sr=61 | 50k   | 1.40s | 8.49s | 6.06× |
| sr=60 | 1M    | 24.56s | 26.51s | **1.08×** |

**The Mode B advantage at sr=60 is dramatically smaller than at sr=61** (1.08× vs 6×).

## Why does sr=60 Mode B help less?

Two compatible explanations:

1. **The conflict budget is at steady-state**, not preprocessing. At 50k sr=61 conflicts, we're still inside the Mode B preprocessing-advantage window. At 1M sr=60 conflicts we're well past it — same erosion seen at sr=61 between 50k and 500k budgets.

2. **sr=60 has a different free-rounds structure** (4 free rounds 57-60 vs sr=61's 3 free rounds 57-59), so the Mode B unit clauses prune a smaller fraction of total search space. The cascade-zero diagonal still applies, but the additional `dE[61..63]=0` three-filter is less impactful when there's already more freedom upstream.

Pulling the two hypotheses apart needs:
- sr=60 at 50k conflicts (same budget-relative-to-warmup as sr=61's earlier comparison).
- sr=61 at 1M conflicts (already done for 500k — saw 1.05× ratio, consistent).

## SAT-finding implication

None of these 4 candidates produce SAT at 1M conflicts in cadical Mode B at sr=60. Background context:
- The MSB cert (m=0x17149975 fill=0xff bit=31) is the ONLY known sr=60 cascade-DP SAT instance.
- Standard encoding takes ~12h on MSB cert to find SAT.
- 1M conflicts ≈ 25s of wall time → this is far below the conflict count typically needed to find SAT on hard cascade-DP instances.

So the "no SAT in 1M conflicts" finding is consistent with prior expectations. It does not refute the existence of sr=60 SAT for these 4 candidates; it just doesn't confirm it either.

To probe sr=60 SAT existence on a non-MSB candidate, we'd need ~10^9 conflicts (≈ 12h × 3× Mode-B-speedup ≈ 4h per candidate). That's a real compute commitment — NOT initiating without explicit user direction.

## What this confirms

1. **Mode B's per-conflict advantage is regime-dependent.** It's 6× at sr=61 50k (preprocessing-dominated), 1.05× at sr=61 500k (steady state), 1.08× at sr=60 1M (steady state). The pattern is clear: Mode B's CNF-level cascade-zero unit clauses give a one-time preprocessing speedup that erodes during long CDCL search.

2. **Cross-candidate consistency.** All 4 non-MSB candidates show essentially identical per-conflict cost (24-28s for 1M conflicts). The Mode B effect doesn't depend on candidate-specific structure, only on encoding.

3. **Mode A is no longer markedly worse than Mode B at sr=60 1M-conflict budget.** This contrasts with the 6× gap at sr=61 50k. Suggests Mode A's overhead is also paid only in preprocessing — once the solver enters steady-state CDCL, the encoding effect normalizes.

## Run logs (8 entries to be appended via append_run.py)

All cadical 3.0.0, seed=5, sr=60, conflict-budget=1M.
