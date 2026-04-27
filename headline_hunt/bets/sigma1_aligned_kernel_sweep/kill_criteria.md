# Kill criteria — sigma1_aligned_kernel_sweep

This bet auto-closes if any of the following becomes true. When a kill
criterion fires, file the kill memo in
`headline_hunt/graveyard/closed_bets/` using `KILL_MEMO_TEMPLATE.md`
and update `mechanisms.yaml` `status: closed`.

## Hard kill criteria (any one fires → close)

### 1. Empirical 1M-sample sweep confirms NO sigma1-alignment advantage

**Trigger**: full 35-cand 1M-sample empirical hard-residue analysis
shows total h+f+g hard bits within 2 of each other for sigma1-aligned
vs non-aligned groups (mean comparison).

**Rationale**: pre-screen (h60+f60 only) already shows 0.2-bit gap.
If the full empirical residue analysis confirms <2 bit gap, the
hypothesis is structurally refuted.

**Action**: write KILL memo, add to negatives.yaml as
"sigma1_alignment_advantage" with would-change-my-mind: "deeper
budget reveals alignment-dependent solver behavior."

### 2. Deep-budget kissat confirms NO sigma1-aligned cand finds SAT first

**Trigger**: 12h kissat × 5 seeds × 3 sigma1-aligned cands × 3
non-aligned cands all return UNKNOWN, OR sigma1-aligned cands take
>= median time of non-aligned cands.

**Rationale**: this is the strongest test. If even at deep budgets
the alignment doesn't help, the bet is dead.

**Action**: write KILL memo. Note in graveyard that "sigma1-aligned
not differentiable from non-aligned at any tested budget."

### 3. Per-conflict equivalence (F37/F39/F41) extends to alignment

**Trigger**: explicit cross-comparison of sigma1-aligned vs non-aligned
cand walls at 1M conflicts (5+ seeds each, both parallel and
sequential) shows medians within 2s of each other.

**Rationale**: F37/F39/F41 already establish per-conflict equivalence
across cands. If a clean test confirms this includes sigma1-aligned
cands, the hypothesis "easier solver behavior at sigma1-aligned" is
falsified.

**Action**: write KILL memo. Could be done in <30 min compute (5
sigma1 cands × 5 seeds × 1M parallel = 25 kissat runs).

## Soft kill criteria (all together → consider close)

- Compute-budget cap (50 CPU-h) hit without finding any advantage
- 6+ months of project elapsed without bet generating any positive
  signal
- All other open bets have higher expected_info_per_cpu_hour AND
  this bet's owner is unassigned for >60 days

## Reopen criteria

- New theoretical reason published linking Σ1 alignment to differential
  trail probability or solver heuristic behavior
- A specific cand at a sigma1-aligned bit position empirically achieves
  sr=61 SAT or sub-30s 1M kissat wall (well below the per-conflict
  plateau)
- Cross-bet synthesis with block2_wang or cascade_aux finds that
  sigma1-aligned cands have lower LM cost on second-block trails

## Bet-status transitions

- `open` → `in_flight`: someone claims owner and starts compute
- `in_flight` → `blocked`: compute requires more authorization (12h+)
- `in_flight` → `closed`: any hard kill criterion fires
- `closed` → `open`: any reopen criterion fires (with new evidence)

## Audit reference

Tools to use for evaluation:
- `infra/audit_cnf.py` — CNF audit before any kissat run
- `infra/append_run.py` — log every kissat run with seed, wall, status
- `infra/summarize_runs.py` — dashboard for cross-cand comparison
- `bets/block2_wang/residuals/cand_select.py` — multi-metric ranking

If the bet is closed, the kill memo MUST link to:
- The runs.jsonl entries that supported the kill decision
- The specific reproduction cmd line that fires kill criterion 3
- A would-change-my-mind reopen criterion (mandatory)
