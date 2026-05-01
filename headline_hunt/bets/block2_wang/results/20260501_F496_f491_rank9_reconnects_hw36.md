---
date: 2026-05-01
bet: block2_wang
status: PATH_C_F491_RANK9_RECONNECTS_HW36
parent: F491 refreshed seed manifest / F494-F495 rank-7 side basin
evidence_level: VERIFIED
compute: one pair-beam run; no solver runs
author: yale-codex
---

# F496: F491 rank-9 seed reconnects to the known HW36 basin

## Setup

F496 tested F491 rank 9, a HW40 seed from the F486 manifest-tail run:

`0x5228ed8d 0x61a1a29c 0x6a3a8409 0x14ac6d7b`

Artifact:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F496_bit13_f491_rank9_hw40_pair_beam_cg.json`

## Result

F496 re-found the prior HW36 basin:

- W1=`0x5228ed8d 0x61a1a29c 0x6a3a8409 0x2c9e917b`
- HW=36
- score=85.471
- hw63=`[11,3,1,0,13,7,1,0]`
- expanded=3,481,732
- bridge pass=3,481,703
- HW <= 40: 12
- HW < 40: 10
- wall=303.17s

Depth summary:

| Depth | Best HW | Best score |
|---:|---:|---:|
| 1 | 47 | 75.333 |
| 2 | 46 | 76.273 |
| 3 | 42 | 80.000 |
| 4 | 37 | 84.571 |
| 5 | 37 | 84.571 |
| 6 | 36 | 85.471 |

## Verdict

F491 rank 9 is connected to the known HW36 basin and does not threaten the
current HW35 panel floor. It is useful as a connectivity marker, but it should
not receive another direct pair-beam restart under the current operator.
