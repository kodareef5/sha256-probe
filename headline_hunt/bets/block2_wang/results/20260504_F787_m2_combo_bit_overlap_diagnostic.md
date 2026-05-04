---
date: 2026-05-04
bet: block2_wang
status: M2_COMBO_BIT_OVERLAP_DIAGNOSTIC_COMPLETE
parent: F786 aggregate lane-delta negative
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F787: M2 combo bit-overlap diagnostic

## Setup

F787 adds `analyze_m2_combo_bit_overlap.py`, a diagnostic for combo records.
For each selected combo record, it re-evaluates:

```text
init final-state diff bits
standalone pair final-state diff bits
combo final-state diff bits
```

Then it compares actual combo repairs/additions against the union of standalone
pair repairs/additions. This tests whether HW82 records are distinguished by
better bit-level overlap than the near misses.

Compared records:

```text
F760 HW82/HW84/HW85 records
F763 HW82 record
F782 best HW87 record
F783 best HW90 record
F786 best HW93 record
```

## Result

The simple overlap metrics do not separate the HW82 records.

```text
record          HW   removed covered/total   added covered/total
F760 best       82   50/52                   44/49
F763 best       82   53/54                   53/54
F782 best       87   62/62                   66/67
F783 best       90   54/54                   57/62
F786 best       93   52/52                   61/63
```

The near misses can cover their eventual repaired bits as well as the HW82
records. F782 and F786 are not failing because the standalone pair repairs miss
the final repaired positions.

The failure is simpler but harder to preselect:

```text
record          removed bits   added bits   net final effect
F760 best       52             49           HW -3
F763 best       54             54           HW  0
F782 best       62             67           HW +5
F783 best       54             62           HW +8
F786 best       52             63           HW +11
```

The problem is suppressing new added bits while keeping the repairs. Aggregate
lane deltas, word graph motifs, and standalone repair coverage all miss that
distinction.

## Interpretation

The next useful selector should estimate addition risk before full evaluation.
The current pair-potential atlas knows which bits each standalone pair adds,
but the combo outcome depends on which additions cancel under composition.
That suggests a new pre-eval score: penalize selected pair sets whose
standalone added-bit union is large unless the same bits are repeatedly toggled
by multiple pairs.

## Artifact

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F787_m2_combo_bit_overlap.json
```

## Next

Prototype a pair-set overlap filter for sampled six-pair combos:

```text
reward repeated standalone-added bits
penalize broad added-bit union
keep high standalone repair union
allow radius 10..12
```

This is a different selector from word graph or aggregate lane-delta filters.
