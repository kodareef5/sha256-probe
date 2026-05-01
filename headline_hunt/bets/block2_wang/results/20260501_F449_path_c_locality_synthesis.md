---
date: 2026-05-01
bet: block2_wang
status: PATH_C_LOCALITY_SYNTHESIS
parent: F436-F448
evidence_level: SYNTHESIS
author: yale-codex
---

# F449: Path C locality synthesis after radius-4 closure

## What changed today

Path C moved from "promising local residual search" to a sharper diagnosis:
the best records are real, cert-pinned, and locally boxed in under raw
W57..W60 bit moves.

Current record panel:

| Candidate | HW | Source | Exact local status |
|---|---:|---|---|
| bit24_mdc27e18c | 43 | F428 | full radius-4 closed, bridge-relaxed by construction |
| bit13_m916a56aa | 44 | F436 | full radius-4 closed, bridge-relaxed in F448 |
| bit28_md1acca79 | 45 | F408/F427 | full radius-4 closed, bridge-relaxed in F448 |

## Evidence stack

Exact closures:

- F440: bit13 HW44 full W57..W60 radius-4 closed.
- F441: bit24 HW43 full W57..W60 radius-4 closed.
- F442: bit28 HW45 full W57..W60 radius-4 closed.
- F448: bridge-relaxed reruns close the selector loophole for bit13/bit28.

Selective radius-5/6 probes:

- F443: top-32 one-bit soft directions, radius 5/6, negative across top-three.
- F444: top-64 cross-word radius 5 with slot diversity, negative.
- F445: top-128 pair-HW-ranked 3-pair unions, negative.
- F447: repair-ranked pair unions, negative and worse than HW-ranked pairs.

Carry-chart diagnosis:

- F446: exact pair atlas shows c/g lane locks.
- bit24: no accepted pair reduces b, c, or g.
- bit13: no accepted pair reduces c or g.
- bit28: c can reduce slightly, but g does not reduce under accepted pairs.

## Critique

The bridge-guided W-bit search has been productive, but it is now showing
clear diminishing returns. The successful jumps were narrow and punctuated:
bit24 49 -> 43 via W60 refinement, and bit13 49 -> 44 via a radius-4
W59/W60 move. Once those wells were found, raw local moves stopped paying.

The main weakness in the current operator family is scalar ranking. Ranking
by final HW, one-bit softness, pair HW, or total repair all misses the same
structural issue: local moves repair one lane by damaging other lanes,
especially around c/g. The compensation pattern matters more than the
individual move quality.

## Recommended pivot

Stop spending primary effort on unstructured raw W-bit radius expansion.
The next experiments should change coordinates:

1. Compensation-aware pair composition: select pairs whose positive
   compensation lanes are canceled by other pairs, not simply pairs with low
   local HW.
2. Geometry relaxation: change or weaken the current bridge/cascade
   fingerprint and test whether the c/g locks move.
3. Backward/carry-chart construction: choose target lane deltas first, then
   solve or search for W moves that realize them.
4. Small-N algebraic calibration: use the now-clean local evidence to test
   whether the observed c/g locks have a small-N explanation.

## Bottom line

The top-three Path C records are not fragile artifacts. They are stable
local minima under several independent tests. Further progress likely needs
a coordinate change, not more volume in the same local W-bit metric.
