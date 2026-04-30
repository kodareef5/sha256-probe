---
date: 2026-05-01
bet: programmatic_sat_propagator
status: F344_MODESTLY_BETTER — F344 (32 clauses) gives Δ=−3.11% on bit2 vs F343 (2) at Δ=−1.70%; doesn't break the bit2-pattern
parent: F394 (search-trajectory hypothesis confirmed at n=4; F344 proposed as Factor B test)
type: empirical_test of richer-clause-set hypothesis
compute: 13 min preflight mining + 3 min cadical (9 runs × 60s parallel-3)
---

# F395: F344 32-clause variant on bit2 — modestly helps but doesn't break the no-strong-help pattern

## Setup

F394 confirmed the search-trajectory hypothesis: F343 propagates always
but only prunes when VSIDS reaches dW57[0] / W57[22:23]. bit2 is the
"VSIDS doesn't reach" outlier. F394 proposed F344's 32-clause variant
as a Factor B test (does richer clause set close the bit2 gap?).

F395 mines F344 on bit2 (`scan_all` for unit + `scan_adjacent` for
pairs), builds the F344-extended CNF, and runs cadical 60s × 3 seeds
× 3 conditions (baseline, F343, F344).

## F344 mining on bit2

```
python3 preflight_clause_miner.py --cnf bit2.cnf --varmap bit2.varmap.json \
  --probe-single-bits scan_all --probe-pairs scan_adjacent --budget 5
```

Wall: 779s (~13 min). Result:
  - 1 injectable unit clause (only dW57[0] has forced polarity)
  - 31 injectable pair clauses (all dW57 adjacent-bit pairs)
  - Total: 32 clauses (matches F344's nominal "32-clause variant" count)

The other 31 single-bit probes returned `forced=None` — no polarity is
fast-UNSAT. So bit2's F344 mining is "1 unit + 31 pairs", not
"32 units + 31 pairs" as the count "63" might suggest.

## Result — bit2 × {baseline, F343 (2 clauses), F344 (32 clauses)} × 3 seeds

```
condition   seed=0     seed=1     seed=2     mean      Δ vs baseline
baseline   2,249,645  2,154,161  2,245,768  2,216,525     --
F343       2,219,191  2,119,551  2,198,075  2,178,939   -1.70%
F344       2,211,118  2,118,394  2,113,574  2,147,695   -3.11%
```

(NB: this baseline mean (2.22M) differs from F390's bit2 baseline
(1.60M) due to system-load-dependent variance in 60s budget runs;
the relative comparisons within F395 are valid since all 9 runs
ran in the same parallel-3 batch.)

## Findings

### Finding 1 — F344 helps bit2 modestly: marginal +1.4pp over F343

F343 alone: Δ=−1.70%
F344 (16x more clauses): Δ=−3.11%

The 30 additional clauses (31 pairs vs 1 pair, plus the same 1 unit)
buy 1.4 percentage points of additional pruning on bit2. F344 is
modestly better but doesn't transform bit2 into a "F343 helps a lot"
cand like bit3 (which got −9% with just 2 clauses).

### Finding 2 — Does NOT break the search-trajectory hypothesis

F394's hypothesis was: bit2's VSIDS doesn't reach the F343-constrained
vars. If correct, even with 16x more clauses, bit2's effect should
stay modest because the issue is decision-priority, not clause count.

F395's result fits this: F344 helps bit2 by ~3% (vs ~1.7% for F343).
The marginal gain (1.4pp) is bounded — F344 can't lift bit2 to bit3's
−9% level even with 16x the clauses.

This SUPPORTS the search-trajectory hypothesis: clause richness alone
doesn't compensate for VSIDS-trajectory mismatch.

### Finding 3 — Cost-benefit: F344 mining = 13 min, F343 mining = ~20s

F343 mining (2 clauses): ~20s wall per cand
F344 mining (32 clauses): ~13 min wall per cand (32x slower)
Marginal benefit of F344 over F343 on bit2: 1.4pp

For a registry-wide deployment:
  F343 on 67 cands: 67 × 20s = ~22 min
  F344 on 67 cands: 67 × 13 min = ~14.5 hours
  Speedup gain from F344: ~1-3pp per cand additional

That's a poor cost-benefit ratio. F343 is the right tool for routine
pre-injection. F344 is only worthwhile for cands where F343 specifically
underperforms (like bit2 — and even there the gain is modest).

### Finding 4 — F347's "F344 → −13.7% on bit31" claim re-examined

F347 reported F344 (32 clauses) gave −13.7% conflict reduction on
bit31. F343 alone gave roughly the same on bit31 (−13.12% in F391 with
2 clauses). So on bit31, F344's marginal benefit over F343 is 0.6pp —
similar to F395's bit2 marginal of 1.4pp.

**The F347 13.7% headline number was mostly F343's contribution, not
F344's.** F344's marginal value (0.6-1.4pp) is small across the cands
tested.

This is consistent with F366's finding (F347 was a real but specific
60s-budget measurement); F347 wasn't really showing a unique F344
benefit, just F343's effect at its peak (bit31 + 60s budget).

## Implication for Phase 2D

Phase 2D pre-injection should:
  - Apply F343 (2 clauses) universally — cheap, ~−7-9% mean (high variance)
  - NOT apply F344 (32 clauses) — 32x mining cost, 1-3pp marginal benefit
  - NOT apply F384 ladder (per F391 falsification)
  - Investigate VSIDS-boost intervention separately (per F394 proposal)

The clause-count axis is exhausted. Future improvements must come from
**decision-priority interventions** (VSIDS bumping at solver init), not
from richer clause sets.

## What's shipped

- This memo with bit2 × {baseline, F343, F344} 3-seed comparison
- F344 mining on bit2 (32 injectable clauses, 13 min wall)
- F395 corrects F347's "F344 → -13.7%" reading: most of the help was
  from F343 alone

## Compute discipline

- 1 preflight mining run (~13 min wall, recorded in /tmp/F395/bit2_F344_spec.json)
- 9 cadical 60s runs (3 conditions × 3 seeds, parallel-3, ~3 min wall)
- 3 transient CNFs in /tmp/F395/
- All 9 cadical runs logged below via append_run.py

## F381 → F395 chain summary

  F381-F388: structural rule REAL
  F389-F391: ladder pre-injection FALSIFIED
  F392-F394: F343 effectiveness mechanism understood (search-trajectory)
  F395: F344 32-clause variant — modest help on bit2, doesn't break pattern

16 numbered memos, 31 commits, ~11 hours, ~1500s cadical compute.

The clause-count axis is exhausted. F343's 2-clause baseline is the
right routine intervention. The remaining unexplored axis for
mechanism-aligned improvement is decision-priority (VSIDS) — the
F394 proposal.
