---
date: 2026-05-02
bet: block2_wang
status: PATH_C_PRIOR_WEIGHTED_W60_W59W60_NEGATIVE
parent: F552 W delta lattice
evidence_level: EVIDENCE
author: yale-codex
---

# F553/F562: Prior-Weighted W60 and W59/W60 Sampler

## Setup

F552 found repeated W60 bit positions across Path C candidates but no repeated
full W60 masks. F553/F562 tested the natural operator:

- keep W57..W59 fixed at each current floor witness;
- sample W60-only flips;
- weight recurrent F552 bits more heavily;
- use flip counts 7..14, outside the exact radius-6 closures already tested;
- run 500k samples per current Path C floor.

The operator is implemented as:

`encoders/prior_weighted_w60_search.py`

Despite the filename, the tool now supports joint W59/W60 sampling through
`--slots 59,60`.

Default prior bits:

`30,27,29,31,16,19,21,3,13,14,15,12,2,25,28`

## F553/F557: W60-only results

| Run | Cand | Init HW | Unique samples | Bridge pass | HW<=init | HW<init | Best HW |
|---|---|---:|---:|---:|---:|---:|---:|
| F553 | bit3 | 36 | 485,755 | 485,585 | 0 | 0 | 36 |
| F554 | bit24 | 40 | 485,804 | 485,804 | 0 | 0 | 40 |
| F555 | bit2 | 39 | 485,702 | 485,702 | 0 | 0 | 39 |
| F556 | bit13 | 35 | 485,685 | 485,685 | 0 | 0 | 35 |
| F557 | bit28 | 42 | 485,910 | 485,909 | 0 | 0 | 42 |

Total: 2,428,856 unique sampled W60 masks, zero ties or improvements.

## F558/F562: W59/W60 joint results

The W60-only negative left one obvious objection: F552 also saw sparse W59
movement, especially W59:b21. F558/F562 reran the prior sampler over the
joint W59/W60 domain, with W59:b21 weighted as a soft prior and all other
W59 bits available at background weight.

| Run | Cand | Init HW | Unique samples | Bridge pass | HW<=init | HW<init | Best HW |
|---|---|---:|---:|---:|---:|---:|---:|
| F558 | bit3 | 36 | 499,926 | 499,923 | 0 | 0 | 36 |
| F559 | bit24 | 40 | 499,906 | 499,906 | 0 | 0 | 40 |
| F560 | bit2 | 39 | 499,928 | 499,928 | 0 | 0 | 39 |
| F561 | bit13 | 35 | 499,921 | 499,921 | 0 | 0 | 35 |
| F562 | bit28 | 42 | 499,932 | 499,932 | 0 | 0 | 42 |

Total: 2,499,613 unique sampled W59/W60 masks, zero ties or improvements.

## Verdict

The F552 recurrent-bit prior is useful descriptively, but W60-only
prior-weighted sampling is not enough to move current floors. The joint
W59/W60 version also failed cleanly. This closes the "just bias recurrent
bit positions harder" angle for the five-candidate panel.

Next operators need either:

1. candidate-specific active masks learned from successful pair pools;
2. cross-candidate transfer from actual pair-pool decompositions, not just
   independent bit frequencies.
3. a state-aware scorer that can distinguish which recurrent bits are useful
   in a given candidate rather than treating them as globally beneficial.
