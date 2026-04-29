---
date: 2026-04-28
bet: block2_wang
status: F278_OVERSTATED — F279 retracts; score-87 NOT multi-seed via {1,3} anchoring
---

# F278/F279: forced-{1,3} chunked-scan found a transient 87 from seed 9001 — 8x50k retracts

## Setup

Yale's F339 catalog showed 4 of 5 bit19 seed-7101 narrow basins contain
active words {1,3}. Yale's "next probes" list suggested forced-{1,3}
scans with diverse seeds to test if {1,3} anchoring + multi-seed
discovery reveals more narrow basins.

F278 ran the test: forced-{1,3} size-5 scan (364 masks, all containing
bits {1,3}) at seed 9001 chunked-scan (3×4000).

## F278 chunked-scan result

```
Top 5 by score (seed 9001, chunked-scan):
  score 87 at 1,3,4,7,11  ← striking!
  score 89 at 0,1,2,3,6
  score 90 at 1,3,6,8,10
  score 91 at 1,3,5,6,11  (yale's F335 mask, here at 91)
  score 92 at 1,3,5,8,13
```

The score-87 result on `1,3,4,7,11` from seed 9001 looked like a
breakthrough: score-87 reachable from a NON-7101 seed for the first
time (F135's 87 was seed-7101 only).

## F279 retraction (8x50k verification)

Per F205 protocol, chunked-scan results need 8x50k verification.

```bash
search_block2_absorption.py --restarts 8 --iterations 50000 \
  --seed 9001 --active-words 1,3,4,7,11
```

Result:

```
all 8 restarts:
  restart=7: score=92 msgHW=74
  restart=0: score=95
  restart=1: score=95
  restart=4: score=95
  restart=5: score=96
  restart=6: score=97
  restart=2: score=98
  restart=3: score=100
BEST: 92
```

**F278's score 87 was a TRANSIENT minimum at 3x4000 chunked-scan.**
At 8x50k, seed 9001 reaches only 92. The score-87 result didn't survive
the protocol's verification budget.

## Calibration finding

This is the third occurrence of the F205 transient-minima pattern:
- F201/F205: cross-fixture basin propagation 88-89 results were transient
- F231/F232: shell_eliminate v1 false-SAT was the same class of
  bookkeeping insufficiency
- F278/F279: forced-{1,3} chunked-scan 87 was transient

The pattern keeps holding: **3x4000 chunked-scan can produce sub-91
hits that don't survive 8x50k verification**. F278 was a violation
of the F205 protocol — should have run the 8x50k verification BEFORE
celebrating the score-87 result.

## What F279 sharpens

The yale F339 {1,3} structural pattern observation remains valid:
4 of 5 known seed-7101 narrow basins contain bits {1,3}. But
{1,3} anchoring + non-7101 seed DOES NOT unlock score-87 at the
8x50k verification budget.

Updated picture:
- Score-87 on bit19 is reachable from seed 7101 via F135 chunk-1
  (verified 8x50k by yale F173/F174).
- Score-87 from seed 9001 + {1,3} anchoring at 3x4000 chunked-scan:
  transient (F278/F279).
- Score-87 from seed 9001 at 8x50k: NOT reached (best 92, F279).
- Robust 8x50k floor across non-7101 seeds: 91-95.

The score-87 floor on bit19 fixture appears to be GENUINELY
seed-7101 specific. {1,3} anchoring is a useful structural marker
but doesn't transfer the 87 floor to other seeds.

## Honest update

This is now FOUR retraction-class findings in the session:
- F205: F201's cross-fixture basin propagation overstated
- F232: shell_eliminate v1 had soundness bug
- F237: F211 preprocessing speedup thesis empirically refuted
- F279: F278's forced-{1,3} score-87 was a transient minimum

The discipline holds: ship corrections promptly, don't defend
overstated claims. F278 had ~5 min between announcement and
F279 verification — fast retraction cycle.

## Concrete next probes

(a) **8x50k verification on F278's other top hits**: bit-2 score 89
    `0,1,2,3,6`, score 90 `1,3,6,8,10`. Maybe one of these survives
    8x50k where F278's top didn't.

(b) **Forced-{1,3} scan with seed 5001 or 11001**: third-seed
    coverage.

(c) **Forced-{1,3} 8x50k continuation on top-K**: same protocol
    yale used in F248 — chunked-scan finds candidates, 8x50k
    verifies. Apply this discipline FROM THE START rather than
    retroactively.

## Discipline

- 0 SAT compute (heuristic local search)
- ~3 min wall for F279 verification
- Same retraction discipline as F205/F232/F237/F317
- 73 commits this session

## Coordination with yale

Yale's F339 catalog identified the {1,3} pattern. F278 tested it.
F279 retracts F278. The empirical state:
- {1,3} structural observation: still valid (descriptive)
- {1,3} as universal-floor unlocking key: REFUTED at 8x50k

Worth signaling to yale to avoid building further on the false
F278 claim.
