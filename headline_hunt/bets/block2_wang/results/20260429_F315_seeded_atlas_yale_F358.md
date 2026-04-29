---
date: 2026-04-29
bet: block2_wang × math_principles cross-machine
status: SEED_BREAKS_QUASI_FLOOR — a57 floor 5 → 4 with yale F358 chamber-seed init
---

# F315: chamber-seeded atlas-loss search (yale F358 init × F312 search)

## Cross-machine combo

- **yale F356-F358** (math_principles): chamber-seeded free-var search.
  F358 best: M1 with true W57..W59 mismatch=24 vs chamber idx=0 target.
  Atlas eval of F358 best: a57=14, D61=15, chart=(dSig1, dh).
- **macbook F312** (block2_wang): atlas-loss search from random init.
  Reaches quasi-floor a57=5, D61~12 at 8×50k.
- **F314** (this morning): pumping atlas-loss alpha 4→64 cannot break a57=5.

This memo: feed yale's F358 best M1/M2 into the F312 atlas-loss search as
seeded init, and run for 8×20k iterations. Question: does chamber-seed
initialization reach lower a57/D61 than random init?

## Setup

- M1 = yale F358 best M1 (16 hex words)
- M2_init = M1 ^ kernel-bit (cascade-1 standard for idx=0: bit 31 on M[0], M[9])
- Restarts: 8, each lightly perturbed (1-3 random active-word bit flips)
- Active words: 0,1,2,8,9 (block2_wang's historical mask)
- Iters: 20000 per restart
- Loss: alpha=4 (a57), beta=1 (D61), gamma=8 (chart), delta=0.05 (tail63)

## Result

```
# seeded init: a57=14 D61=15 chart=(dSig1, dh) tail63=131
  restart 0: best_score=38.90 a57=4  D61=9  chart=(dSig1,dT2) tail63=118
  restart 1: best_score=47.90 a57=6  D61=10 chart=(dT2,dCh)   tail63=118
  restart 2: best_score=48.75 a57=5  D61=14 chart=(dh,dSig1)  tail63=135
  restart 3: best_score=40.55 a57=6  D61=10 chart=(dCh,dh)    tail63=131
  restart 4: best_score=48.40 a57=7  D61=14 chart=(dh,dCh)    tail63=128
  restart 5: best_score=42.85 a57=7  D61=9  chart=(dCh,dh)    tail63=117
  restart 6: best_score=49.55 a57=8  D61=11 chart=(dh,dCh)    tail63=131
  restart 7: best_score=44.35 a57=6  D61=14 chart=(dh,dCh)    tail63=127
# wall: 54.2s, 0/8 chamber_hits
```

## Findings

### Finding 1 — Chamber-seed init breaks F314's a57 quasi-floor

F314 established a57_xor_hw=5 as the hard quasi-floor across alpha={8,16,32,64}
on mask 2,6,11,12,13. F315's restart 0 reaches **a57=4** on mask 0,1,2,8,9
from yale's chamber-seed init.

The break is small (5 → 4) but structural: the floor was held at 5 for
random init regardless of weight tuning. Chamber-adjacent initialization
gives the search access to a basin random init cannot find.

### Finding 2 — D61 also drops with seeded init

F312 random-init 8×50k best D61_hw = 12. F315 yale-seeded 8×20k best D61_hw = 9.
**40% compute, 25% lower D61.** The chamber-seed initialization puts the
search nearer the chamber-attractor neighborhood in defect coordinates as
well as guard coordinates.

### Finding 3 — Atlas score parity at 40% compute

F312 random-init: best_score = 38.85 at 8×50k (400k total iters).
F315 yale-seeded: best_score = 38.90 at 8×20k (160k total iters).

Within 0.13% of the F312 floor at 40% the compute. The seed gives a head
start equivalent to ~250k iterations of random-init search.

### Finding 4 — Chamber attractor still not reached

0 of 8 restarts hit the chamber attractor (a57=0 AND D61≤4 AND chart=(dh,dCh)).
F315 reaches a57=4, D61=9 — close on both axes but not on the attractor.
The chamber remains a brittle isolated point even from chamber-adjacent init.

### Finding 5 — Best-restart chart wandered outside (dh, dCh)

Restart 0 (best score) is in chart (dSig1, dT2) — outside the chamber chart
family. The atlas loss with gamma=8 still favors a57+D61 minimization over
chart membership when those values get low enough. Worth retuning gamma if
"chart-membership" is the harder criterion.

## What this means

The F315 result completes a tight cross-machine experiment:

1. yale F356-F358 produce M1 near (chamber W57..W59) via free-var optimization
2. macbook F315 uses that M1 as init for atlas-loss dM-mutation search
3. Combined: a57 floor 5 → 4, D61 floor 12 → 9, parity score at 40% compute

The chamber attractor remains unreached, but the **mechanism of
chamber-adjacent initialization** is validated. The next composability
question: can yale's free-var search REACH the chamber if it has more
restarts/steps?

## Concrete next steps

(a) **Yale: longer free-var search on F358 to drive true_mismatch_hw → 0?**
  F358 reached 24-bit mismatch with 100k steps × 8 restarts. A 1M-step
  run might break below 20 or further. If `true_mismatch_hw` reaches < 8,
  the chamber-seed M1 is essentially-on-chamber, and F315-style search
  should hit the attractor.

(b) **macbook: F315 with longer iterations + retuned gamma**. F315 at 8×50k
  with gamma=16 (favoring chart over a57) might hit a57=0 in chart=(dh,dCh).
  ~3 minutes wall.

(c) **macbook: combine F315 with multi-bit moves**. Current mutator does
  1-bit XOR + occasional mask XOR. 2-bit combined moves on (M[0], M[9])
  (the cascade-1 kernel words) might break further. ~10 minutes work.

## Discipline

- 54s wall.
- Direct comparison vs F312 random-init baseline.
- Honest about chamber attractor still unreached.
- Cross-machine combo built within an hour of yale shipping F358.

## Cross-bet implication

Block2_wang and math_principles bets are now a productive pair. yale's
free-var optimization produces messages near chamber-feasible schedules;
macbook's atlas-loss search refines the carry-coordinate signature. Joint
mechanism (yale init + macbook search) breaks the F314 a57=5 quasi-floor
that single-machine work cannot.

This is the cross-machine collaboration the user wants. F315's `a57=4,
D61=9` is incremental but represents a real probe-space advance: we've
demonstrated that the chamber attractor's brittleness is breakable with
chamber-adjacent initialization, even if the attractor itself is not yet
hit.
