---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT28_HW45_FULL_RADIUS4_CLOSED
parent: F408/F427 bit28 HW=45, F431 Hamming-3 closure, F434 radius-6 stability
evidence_level: VERIFIED
compute: 11017632 exact forward evaluations; 592.05s wall; 0 solver runs
author: yale-codex
---

# F442: bit28 HW=45 full W57..W60 radius-4 closure

## Setup

F408/F427 established bit28 at HW=45. F431 closed Hamming radius 3 and
F434 confirmed radius-6 seeded stability. F442 completes the exact
radius-4 closure for the top-three Path C panel by enumerating every
Hamming radius 1..4 bit flip over all 128 bits of W1[57..60].

Input witness:

`W1 = 0x307cf0e7 0x853d504a 0x78f16a5e 0x41fc6a74`

Artifact:

`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F442_bit28_hw45_full_radius4_enumeration.json`

## Result

| Radius | Total | Cascade-1 pass | Bridge pass | HW <= 45 | HW < 45 |
|---:|---:|---:|---:|---:|---:|
| 1 | 128 | 128 | 127 | 0 | 0 |
| 2 | 8,128 | 8,128 | 8,125 | 0 | 0 |
| 3 | 341,376 | 341,376 | 341,371 | 0 | 0 |
| 4 | 10,668,000 | 10,668,000 | 10,667,990 | 0 | 0 |
| total | 11,017,632 | 11,017,632 | 11,017,613 | 0 | 0 |

Best seen remained the seed itself:

- HW=45
- score=74.146
- `hw63=[12,6,3,0,12,11,1,0]`
- `diff63=[0xe20f5022,0x04041380,0x00380000,0x00000000,0x20fc2a12,0x5c0613c0,0x00080000,0x00000000]`

## Verdict

The third-best Path C record, bit28 HW=45, is exactly closed through
radius 4 across W57..W60.

Top-three exact local status:

- bit24 HW=43: full W57..W60 radius-4 closed.
- bit13 HW=44: full W57..W60 radius-4 closed.
- bit28 HW=45: full W57..W60 radius-4 closed.

This is a useful stopping point for raw Hamming-radius-4 enumeration.
Further progress should shift toward nonlocal/carry-chart operators,
geometry relaxation, or a selective radius-5 strategy with a strong reason
to spend the much larger exact budget.
