---
date: 2026-05-01
bet: block2_wang
status: PATH_C_RELAXED_BRIDGE_RADIUS4_CLOSURE
parent: F440/F441/F442 full radius-4 closures
evidence_level: VERIFIED
compute: 22035264 exact forward evaluations; 0 solver runs
author: yale-codex
---

# F448: relaxed-bridge radius-4 closure

## Setup

F440/F441/F442 closed the top-three Path C records through full W57..W60
radius 4, but the original Hamming-ball enumerator only counted candidates
after `bridge_score` accepted them. F448 adds `--relax-bridge`, which counts
all cascade-valid records for HW ties/improvements even when `bridge_score`
rejects.

Tool update:

`headline_hunt/bets/block2_wang/encoders/enumerate_hamming_ball.py`

New option:

`--relax-bridge`

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F448_bit13_hw44_full_radius4_relaxed_bridge.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F448_bit28_hw45_full_radius4_relaxed_bridge.json`

Bit24 did not need a relaxed rerun because F441 had bridge pass
11,017,632 / 11,017,632.

## Result

| Candidate | Init HW | Total radius <= 4 | Bridge pass | Bridge reject | HW <= init | HW < init |
|---|---:|---:|---:|---:|---:|---:|
| bit13_m916a56aa | 44 | 11,017,632 | 10,691,880 | 325,752 | 0 | 0 |
| bit28_md1acca79 | 45 | 11,017,632 | 11,017,613 | 19 | 0 | 0 |

The seed remained best in both relaxed runs:

- bit13: HW=44, score=71.526
- bit28: HW=45, score=74.146

## Verdict

The top-three Path C radius-4 closure does not depend on the bridge
selector:

- bit24 HW=43: all radius-4 neighbors passed bridge in F441.
- bit13 HW=44: 325,752 bridge rejects checked; none tied or improved.
- bit28 HW=45: 19 bridge rejects checked; none tied or improved.

This closes a real loophole in the earlier wording. Any next improvement
requires radius >= 5, a nonlocal operator, or geometry relaxation beyond
the current cascade setup itself.
