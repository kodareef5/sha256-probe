---
date: 2026-05-01
bet: block2_wang
status: PATH_C_CARRY_CHART_PAIR_ATLAS_COMPLETE
parent: F445 pair-delta combo synergy pilot
evidence_level: VERIFIED
compute: 24384 exact pair evaluations; 0 solver runs
author: yale-codex
---

# F446: carry-chart pair atlas

## Setup

F445 showed that pair-delta combinations do not beat the top-three Path C
records. F446 asks a more diagnostic question: can exact two-bit moves
repair specific final-register lanes, or does every local repair force
larger damage elsewhere?

New tool:

`headline_hunt/bets/block2_wang/encoders/carry_chart_pair_atlas.py`

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F446_bit24_hw43_carry_pair_atlas.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F446_bit13_hw44_carry_pair_atlas.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F446_bit28_hw45_carry_pair_atlas.json`

## Result

| Candidate | Base `hw63` | Bridge pairs | Best pair HW | Best repair pair |
|---|---|---:|---:|---|
| bit24_mdc27e18c | `[14,5,1,0,14,8,1,0]` | 8,128 / 8,128 | 49 | repairs 10, net +38 |
| bit13_m916a56aa | `[13,8,3,0,10,7,3,0]` | 8,003 / 8,128 | 58 | repairs 7, net +36 |
| bit28_md1acca79 | `[12,6,3,0,12,11,1,0]` | 8,125 / 8,128 | 52 | repairs 7, net +31 |

Best pair moves remain far above the seed HW:

- bit24 best pair: HW=49, delta `[+1,+7,0,0,-2,0,0,0]`
- bit13 best pair: HW=58, delta `[+3,+3,+1,0,+4,+3,0,0]`
- bit28 best pair: HW=52, delta `[-3,+4,+1,0,+3,-1,+3,0]`

## Lane Repair Findings

The pair atlas exposes lane locks:

- bit24: no accepted pair reduces b, c, or g. The best a repair reduces a by
  7 but still has net +12 HW; the best e repair reduces e by 8 but net +32.
- bit13: no accepted pair reduces c or g. The best a repair reduces a by 7
  but net +36.
- bit28: c can be repaired by 2 bits with net +8, but no accepted pair
  reduces g. Larger e/f repairs carry net +19 to +27.

So the local problem is not merely finding a pair that reduces a heavy lane.
The compensation cost dominates.

## Verdict

The top-three records have strong pair-level carry-chart locks. In
particular, the c/g lanes are nearly frozen under accepted two-bit moves,
and repairs to a/e/f are paid for by larger damage in other active lanes.

The next operator needs to coordinate repairs across lanes simultaneously,
not rank local moves by scalar HW. Useful next variants:

1. Build a multi-lane objective that requires nonpositive deltas in c/g
   while reducing a/e/f.
2. Search over composed pair moves with cancellation of compensation lanes,
   not just top pair HW.
3. Test geometry relaxation to see whether the c/g lock is fingerprint-bound.
