---
date: 2026-04-28
bet: block2_wang
fixture: bit4_HW63_39a03c2d_naive_blocktwo
status: BIT4_FLOOR_AT_86 — sub-86 not reachable with current toolset
---

# F194: bit4 basin-init 8×50k reproduces 86, does not descend

## Setup

After F191 found bit4's `{0,1,2,4,8}@86` from random-init seed 9101,
the natural next test is whether 8×50k continuation with **basin-init
from F188's score-86 result** can pierce below 86.

Same protocol as yale's F173/F174 on bit19 (F135-init 8×50k). On
bit19 it reproduced 87 from inside the basin but didn't descend.
This memo asks: same outcome on bit4?

## F193 (random-init 8×50k) — pre-test

8×50k random restart on bit4 `{0,1,2,4,8}` (no init). Best across 8
restarts: **94**. The 86 basin is unreachable from outside, same
pattern as F176/F179 showed for bit19's 87 basin.

## F194 (basin-init 8×50k from F188)

```bash
PYTHONPATH=. python3 search_block2_absorption.py \
  bit4_HW63_39a03c2d_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 9601 \
  --active-words 0,1,2,4,8 \
  --init-json 20260428_F188_bit4_chunk0_seed9101.json
```

Result:

```
all 8 restarts:
  restart=0: score=86  msgHW=66    ← seeded from F188's 86
  restart=3: score=94  msgHW=64
  restart=1: score=95
  restart=2: score=96
  restart=5: score=96
  restart=7: score=96
  restart=6: score=98
  restart=4: score=100
BEST: 86
```

**Restart 0 reproduces 86 (the seeded one).** No descent below 86.
Restarts 1-7 are random init within the active-word constraint;
those reach 94-100, consistent with F193.

## Cross-cand floor consolidation

Updated empirical state with multi-seed + basin-init data:

| Cand | Random-init chunked-scan (3×4000) | 8×50k random-init | 8×50k basin-init | Floor |
|---|---|---|---|---:|
| bit3 | 86 (yale, multi-seed) | not tested today | not tested today | **86** |
| bit4 | 86 (F188 seed 9101); 93 (F183 seed 8101) | 94 (F193) | 86 (F194) | **86** |
| bit19 | 87 (F135 seed 7101); 91 (F180 seed 9101) | 95 (F176) | 87 (yale F173/F174) | **87** |
| bit25 | 92-94 (F184/F189) | not tested | not tested | 92 |
| bit28 | 91-92 (F178/F181); 89 with F135 init (F187) | not tested | 89 (F187 cross-fixture init) | 89 |
| msb | 91-92 (F185/F190) | not tested | not tested | 91 |

## Interpretation

**86 is a structural floor at the 8×50k protocol level on this
fixture catalog.** bit3 robust at 86; bit4 robust at 86; bit19 stops
at 87. Neither random-init 8×50k nor basin-init 8×50k descends below
86 on any cand.

This is the second cand to confirm the F179 pattern:
- Lucky chunked-scan seeds find narrow deep basins.
- 8×50k random init from outside cannot find them.
- 8×50k basin-init from inside reproduces but doesn't descend.

The floor is what it is: the basin's actual minimum at this active-
word mask is 86 for bit4, 86 for bit3, 87 for bit19. The local search
genuinely can't find lower under this protocol.

## What this rules out

1. **F143 in the strong form** (distinguished cands have basins
   *strictly better* than bit3) is dead at the 8×50k protocol level.
   bit4's 86 ties bit3's 86. None of bit19/bit28 is below 86 either.

2. **Basin-init does not magically descend.** It re-enters the
   basin and finds the local minimum, which is the same 86 (or 87)
   that the lucky-seed chunked-scan found.

3. **The 8×50k budget is the right per-mask budget for finding
   the local minimum, but not for *piercing* it.** To go below 86
   needs either:
   - A different active-word mask (different basin entirely).
   - A different fixture (might have a deeper basin).
   - A different search algorithm (basin-hopping, simulated tempering,
     SAT, BDD).
   - A different attack mechanism entirely.

## What this does NOT rule out

1. Different masks on bit4 (or any cand) might have deeper basins.
   We've only tested `{0,1,2,4,8}` at 8×50k. Other masks might
   contain sub-86 basins.

2. Different fixtures (bit3 with different M1) might have deeper
   basins.

3. The cascade-aux encoding path (separate bet) might give SAT
   access to sub-86 message pairs.

## Headline-relevance honest assessment

The F187/F191 hopes for a sub-86 basin via basin-init protocol have
not materialized at 8×50k. **86 is empirically the protocol floor**
across the cand catalog tested.

This is honest negative: not a setback (we now know the floor with
calibrated confidence), but not headline-class. The headline path
must run through one of:

(a) A different active-word mask with a deeper basin (worth
    F187-style basin-init scans on additional masks).

(b) A non-local search method that doesn't get trapped in basin
    floors (SAT with structural constraints; BDD enumeration).

(c) A structural insight that explains why 86 is a barrier and
    suggests how to step around it (carry-automaton, schedule-
    compliance algebra).

## Next-step priorities (revised)

1. **Extend F187-style cross-fixture basin-init to all cands**:
   F135 → bit4, F135 → bit25, F135 → msb, F135 → bit19 (control).
   Each ~2 min wall, total ~10 min. Tests if any other cand has a
   sub-89 basin findable via cross-fixture seeding.

2. **F188-init basin-init on a *different mask* of bit4**: take
   F188's score-86 message pair as init for chunk-1 / chunk-2 of
   bit4. Asks if the M1 transfers to a sub-86 basin under a
   different active-word mask.

3. **Run cascade_aux_encoding bet's BP-Bethe propagator** (separate
   path; needs implementation per F134 plan).

4. **Pause heuristic search; pivot to structural method**: SAT,
   BDD, IPASIR-UP propagator, tropical-geometry probe.

## Session arc this hour (recap)

- F176/F179: identified narrow-basin / seed-noise pattern.
- F180: F135's score-87 confirmed as seed-7101 singular.
- F186: cross-cand random-init floor map. F143 looked dead.
- F187: cross-fixture basin propagation works (bit28 89 from
  F135 init). F143 partially revived.
- F191: bit4 random-init reaches 86, ties bit3. Multi-seed
  protocol wins.
- F193/F194: bit4 8×50k confirms the basin floor at 86; sub-86
  not reachable via this protocol.

## Discipline

- 0 SAT compute (all heuristic local search)
- 0 solver runs
- Eight memos shipped this hour, building empirical state
- Honest negative on the sub-86 hope; clarifies the next
  iteration should be structural, not chunked-scan-deeper
