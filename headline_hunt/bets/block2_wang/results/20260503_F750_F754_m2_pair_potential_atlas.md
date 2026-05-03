---
date: 2026-05-03
bet: block2_wang
status: M2_PAIR_POTENTIAL_ATLAS
parent: F749 absorber portfolio atlas
evidence_level: VERIFIED_JSON_ARTIFACTS
author: yale-codex
---

# F750-F754: M2 pair-potential atlas

## Tool

Added:

```text
headline_hunt/bets/block2_wang/encoders/m2_pair_potential_atlas.py
```

The tool enumerates every two-bit M2 flip around a witness and records:

- total HW and lane HW,
- lane delta relative to the witness,
- c/g objective delta,
- distance to a target lane vector,
- per-register repair directions.

This is not another beam search. It is a local geometry atlas for choosing
future non-local compositions.

Target lane for F750/F752/F753/F754:

```text
bit13 HW82 lane = [10, 11, 9, 12, 9, 7, 10, 14]
```

## Summary

| Run | Witness | Init HW | Init target L1 | HW-improving pairs | c/g-improving pairs | target-improving pairs | Best pair HW | Best target pair |
|---|---|---:|---:|---:|---:|---:|---:|---|
| F751 | bit13 HW82 | 82 | 0 | 0 | 0 | 0 | 93 | HW93, L1 19 |
| F752 | rank18 HW83 | 83 | 13 | 0 | 0 | 0 | 94 | HW95, L1 17 |
| F750 | bit24 HW85 | 85 | 25 | 0 | 1 | 107 | 90 | HW96, L1 16 |
| F753 | bit3 HW86 | 86 | 24 | 0 | 0 | 73 | 92 | HW97, L1 17 |
| F754 | bit4 HW89 | 89 | 13 | 0 | 0 | 0 | 93 | HW93, L1 13 |

Each atlas enumerated 130,816 two-bit M2 moves.

## Findings

No mapped endpoint has a non-worse two-bit HW move. This is stronger than the
beam closures: even before ranking or composition, the immediate two-bit
neighborhood is uphill for all five witnesses.

The two deepest bit13 basins are especially rigid:

```text
bit13 HW82: no HW, c/g, or target-lane improvement
rank18 HW83: no HW, c/g, or target-lane improvement
```

Bit24 and bit3 do have lane-signature moves, but only by taking large total-HW
damage:

```text
bit24: best target move L1 25 -> 16, but HW85 -> HW96
bit3:  best target move L1 24 -> 17, but HW86 -> HW97
```

Bit4 is shallow but also locally rigid:

```text
bit4 HW89: no target-lane improvement; best pair is HW93
```

## Implication

The next operator cannot be a greedy local pair rule. Useful moves toward the
HW82 lane signature exist in bit24/bit3, but they require accepting a large
temporary HW increase and then composing compensating repairs. That points to
a constrained multi-pair planner:

1. choose pairs that reduce target-lane distance,
2. require a second stage that repairs the induced high-HW lanes,
3. score the whole composition by final HW, not by any prefix state.

The immediate next experiment should be a target-lane pair-combo pilot on
bit24 HW85: select the top target-L1-improving pairs from F750, then compose
2-4 of them with repair-ranked pairs instead of using the fixed c/g beam pool.
