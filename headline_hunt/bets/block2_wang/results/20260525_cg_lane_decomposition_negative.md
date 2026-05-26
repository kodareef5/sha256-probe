---
date: 2026-05-25
bet: block2_wang
status: NEGATIVE
author: macbook-claude
evidence_level: EVIDENCE
---

# c/g lane locks are NOT (w57,w58)-vs-(w59,w60) decomposable

## Context

macbook-claude took over block2_wang (P1, was dormant). First attempt at the
F449-recommended "coordinate change" out of the radius-4 Path C plateau
(HW 43/44/45), motivated by this session's mitm_residue result: at round 60,
`gh60 = (e58, e57) = f(w57,w58)` and is orthogonal to W60. Hypothesis: the locked
c63/g63 lanes (F449/F446: "no accepted pair reduces c or g") are primarily
controlled by `(w57,w58)`, a coordinate Path C only moved LOCALLY (radius-4) — so a
GLOBAL `(w57,w58)` search could reach lower c/g than the W60-centric search.

## Method

`encoders/decompose_cg_lane_probe.py` (reuses `block2_bridge_beam.run_full`, no SHA
reimpl). From a random valid base config, sweep one axis while fixing the other and
record min/median HW(c63)+HW(g63):

| cand | vary (w57,w58) min c+g | vary (w59,w60) min c+g | full-HW min (either) |
|---|---:|---:|---:|
| bit24 | 10 | 11 | 65 |
| bit13 | 12 | 11 | 64 |
| bit28 | 11 | 14 | 63 |

(60k / 40k samples per axis.)

## Result — REFUTED

Both axes reduce c+g comparably (within ~3). The c63/g63 lanes are **not**
preferentially controlled by `(w57,w58)`; the gh60⊥W60 orthogonality that holds at
**round 60** does **not** survive to **round 63** — by then the lanes are coupled
across all four free words. This is consistent with F449's diagnosis ("local moves
repair one lane while damaging another") and rules out the specific
`(w57,w58)`-then-W60 decomposed-search coordinate change.

Side data: single-2-word-axis variation floors at full HW ~63-65 (≈ the random
forward floor); the Path C frontier (HW 43) is well below this, confirming Path C
found genuine low-HW basins (not reachable by this naive decomposition).

## Where this leaves it

The F449 live levers remain: (1) compensation-aware pair composition, (2) geometry
relaxation, (3) backward carry-chart construction (choose target lane deltas first),
(4) small-N algebraic calibration of the c/g locks. The mitm_residue orthogonality
is a round-60 property only; it does not give a round-63 lane lever. Cheap negative
(~5 min), narrows the coordinate-change space before investing in a big search.
