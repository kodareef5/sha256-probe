---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_RANK18_HW83_CG_NEGATIVE
parent: F738 rank18 HW83; F742 cross-round negative
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F743: rank18 HW83 c/g restart is negative

## Setup

F738 found the best remaining-panel direct seed result:

```text
rank18 direct pair beam: 128 -> 83
lane HW: [10,11,8,11,13,8,12,10]
```

F743 restarts from that HW83 M2 using the same c/g objective that found F732's
HW82 from the rank2 HW85 witness:

```text
objective = total_hw + 2 * (c + g)
pair_rank = cg
rounds = 24
pair_pool = 1024
beam_width = 1024
max_pairs = 6
max_radius = 12
```

## Result

No sub-HW83 records were found.

| Run | Init HW | Best HW | New records | Best objective | Objective-best HW |
|---|---:|---:|---:|---:|---:|
| F743 | 83 | 83 | 0 | 123 | 83 |

The best c/g objective state remained the seed itself.

## Verdict

Rank18's HW83 basin does not have the same immediate c/g-objective escape
that the rank2 HW85 basin had. It remains a useful near-floor witness, but
not the next descent under this radius-12 objective.

Current floor remains HW82 from F732.
