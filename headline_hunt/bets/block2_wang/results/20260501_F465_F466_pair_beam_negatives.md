---
date: 2026-05-01
bet: block2_wang
status: PATH_C_PAIR_BEAM_NEGATIVE_FOLLOWUPS
parent: F462-F464 HW38/HW42 follow-ups
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F465/F466: wider bit28 and stronger bit13 c/g pair beams are negative

## Setup

F465 and F466 tested two immediate follow-ups after the HW38/HW42 panel:

- F465: bit28 HW42, wider HW-ranked c/g beam.
- F466: bit13 HW38, same wider beam but c/g penalty weight raised from 2 to 4.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F465_bit28_hw42_pair_beam_cg_wider.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F466_bit13_hw38_pair_beam_cg_weight4.json`

## Results

| Run | Candidate | Start HW | Pool | Beam | Max pairs | Penalty | Best selected non-seed | Seed stayed best |
|---|---|---:|---:|---:|---:|---|---:|---|
| F465 | bit28_md1acca79 | 42 | 1024 | 1024 | 6 | c,g weight 2 | 44 | yes |
| F466 | bit13_m916a56aa | 38 | 1024 | 1024 | 6 | c,g weight 4 | 40 | yes |

F465 counters:

- expanded: 3,677,528
- skipped duplicate: 1,566,376
- bridge pass: 3,676,193
- HW <= 42: 0
- HW < 42: 0
- wall: 311.94s

F466 counters:

- expanded: 3,467,402
- skipped duplicate: 1,776,502
- bridge pass: 3,467,288
- HW <= 38: 0
- HW < 38: 0
- wall: 294.13s

## Verdict

The immediate pair-beam continuation is now boxed in for the current
settings:

- bit28 HW42 does not improve by simply widening the c/g beam.
- bit13 HW38 does not improve by increasing c/g penalty weight.

The next operator should change coordinates more substantially: alternate
penalty lanes, pair-pool construction, depth schedule, or a beam seeded
from the best non-seed HW40/HW44 intermediates instead of only from the
record seed.
