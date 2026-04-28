# F172: bit19 radius-1 scan — inconclusive at low budget; needs continuation

**2026-04-28**

## Summary

Per F170 hypothesis (bit19 winners are radius-1 from bit3's
{0,1,2,8,9}), ran a targeted scan over the 55 radius-1 neighbors at
3 restarts × 4000 iterations per mask (~9 min total wall).

**Result is INCONCLUSIVE** because the budget is insufficient.

```
Best F172 radius-1 score: 91 (mask {1,2,7,8,9})
Bit19 chunk-1 best: 87 (mask {0,1,3,8,9})  ← also a radius-1 neighbor
```

The known {0,1,3,8,9}@87 result IS a radius-1 neighbor (swap
W[2]→W[3]), so the radius-1 family DOES contain a sub-91 mask. F172's
inability to reproduce 87 reveals that 3×4000 is BELOW the budget
needed for {0,1,3,8,9}'s local minimum — F160 needed 8×50k
continuation to confirm 87.

## Top 10 from F172 batch

| score | msgHW | mask |
|---|---|---|
| 91 | 79 | {1,2,7,8,9} |
| 91 | 79 | {0,1,2,8,13} |
| 92 | 79 | {1,2,8,9,13} |
| 93 | 66 | {0,2,8,9,12} |
| 94 | 81 | {0,2,8,9,11} |
| 94 | 79 | {0,1,2,4,9} |
| 94 | 78 | {0,1,2,9,12} |
| 95 | 77 | {0,1,2,3,8} |
| 96 | 86 | {0,2,5,8,9} |
| 97 | 75 | {1,2,8,9,15} |

Note: {0,1,3,8,9} is NOT in this top-10 because its 3×4000 score is
above 91 — the local minimum 87 only emerges at higher budget.

## What this tells us

The 55 radius-1 neighbors INCLUDE the chunk-1 winner {0,1,3,8,9}@87.
F172 at 3×4000 budget reaches 91. F160 at 8×50k reaches 87.

The IMPLICATION: yale's F134 chunk-scan at 3×4000 budget is also
under-budget — it might MISS sub-87 masks in its already-scanned
chunks if continuations weren't run.

This is a calibration finding: **chunked scans need 8×50k
continuations on top-K masks per chunk to confirm local minima**.

Yale's pattern (chunk N at 3×4000 + continuation 8×50k on best of
chunk) is the right one. My F172 only ran the 3×4000 phase.

## Honest take

F172 doesn't FALSIFY the radius-1 hypothesis. It just shows that
3×4000 is insufficient to hit the radius-1 floor. To rigorously test
the hypothesis, EACH of the 55 masks needs an 8×50k continuation —
that's 55 × ~57sec = ~52 min compute, much more than F172's 9 min.

For now: bit19 floor empirically 87 from chunk 1 (with continuation).
The radius-1 hypothesis remains UNRESOLVED at this compute budget.

## What yale's F172 commit shipped (different from this F172)

Yale ALSO chose F172 today (independent F-numbering — collision noted
in coordination message `comms/inbox/20260428_macbook_to_yale_radius1_coordination.md`).

Yale's F172 added `--explicit-masks` to active_subset_scan.py and
shipped a 55-mask radius-1 list file. **Yale's tooling is the right
abstraction** for future targeted scans.

For future radius-1 / radius-2 / custom-list scans, use yale's
extended scanner. Mine was a shell-loop hack — disposable.

## Concrete next step

If yale or macbook commits ~52 min compute to per-mask 8×50k
continuations on the 55 radius-1 candidates, the radius-1 hypothesis
gets a definitive answer.

Lower-compute alternative: continuation only on top-10 from F172's
3×4000 batch (10 masks × 57 sec = 9.5 min). Tests whether any of
the F172 top-10 has an 87-or-lower local min that the 3×4000 budget
missed.

The 3×4000 → 8×50k continuation gap is the structural lesson here.

## Discipline

- 0 SAT compute (heuristic local search only)
- 0 solver runs to log
- F172 batch: 55 masks × ~10 sec = ~9 min wall total
- Honest negative-but-inconclusive result

This is the kind of "test the hypothesis at low budget; learn what
budget the hypothesis needs" iteration that keeps the project honest.

## Status

Radius-1 hypothesis remains OPEN. Compute upgrade (8×50k continuations
per mask) needed to resolve. Suggested follow-up either with yale's
new --explicit-masks tool or in a continuation batch.

The macbook ↔ yale loop is now at iteration 5+ with growing tooling
infrastructure (yale's F172) and refined methodology (this memo's
budget-calibration lesson).
