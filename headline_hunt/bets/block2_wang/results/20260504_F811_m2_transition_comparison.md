---
date: 2026-05-04
bet: block2_wang
status: M2_TRANSITION_COMPARISON
parent: F808 witness comparison
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F811: M2 transition comparison

## Setup

F811 adds `summarize_m2_transitions.py`, which compares bit-level M2 changes
between named witnesses from the F808 witness table.

Compared transitions:

```text
successful: F788 HW86 -> F789 HW78
weak:       F800 HW86 -> F802 HW85
```

## Result

```text
transition                         HW      M2 weight  distance  added  removed
F788_HW86 -> F789_HW78             86->78  40->44     12        8      4
F800_HW86 -> F802_HW85             86->85  50->56      8        7      1
```

Word histograms:

```text
F788 -> F789 added words:   {1:1, 3:1, 4:2, 7:1, 8:1, 13:2}
F788 -> F789 removed words: {1:1, 3:2, 10:1}

F800 -> F802 added words:   {5:1, 6:1, 9:1, 12:1, 15:3}
F800 -> F802 removed words: {8:1}
```

## Interpretation

The weak bridge over-fills. F800->F802 has fewer toggled bits than F788->F789,
but it adds seven bits and removes only one, increasing M2 weight by six. The
successful F788->F789 transition is more balanced, adding eight and removing
four for a net M2-weight increase of four.

This suggests a hard M2-weight cap is a better next test than a soft sparse
penalty. The cap can forbid the exact over-filled F802 endpoint while allowing
F788-like net growth.

## Artifacts

```text
headline_hunt/bets/block2_wang/encoders/summarize_m2_transitions.py
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F811_m2_transition_comparison.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F811_m2_transition_comparison.md
```

## Next

Run F812: repeat the F800 -> F788-lane bridge with `--max-m2-weight 54`, so
the previous M2-weight-56 F802 endpoint is disallowed.
