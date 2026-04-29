---
date: 2026-04-29
bet: block2_wang × math_principles cross-machine
status: SEED_COMPARISON — F358 vs F359 chamber seeds both break a57=5 quasi-floor
---

# F316: atlas-loss search seeded from yale F359 (atlas-aware seed)

## Setup

Same F315 protocol (8 restarts × 20k iters, mask=0,1,2,8,9, alpha=4 beta=1
gamma=8 delta=0.05) but seeded from yale's F359 (atlas-aware free-var
optimization) instead of F358 (true-mismatch-only objective).

| Source | Seed init a57 | Seed init D61 | Seed init chart | Seed mismatch |
|---|---:|---:|---|---:|
| F358 (true-mismatch) | 14 | 15 | (dSig1, dh) | 24 |
| F359 (atlas-aware)   | 17 | 13 | (dCh, dh)   | 29 |

F359's atlas-aware free-var search trades 5 bits of mismatch and 3 a57 bits
for chart membership in the chamber family (dCh, dh) and 2 lower D61 bits.

## Result

```
F316 (F359 init):
  restart 0: score=52.45 a57=8 D61=14 chart=(dCh,dh)
  restart 1: score=46.10 a57=4 D61=15 chart=(dSig1,dT2)
  restart 2: score=47.30 a57=6 D61=17 chart=(dCh,dh)
  restart 3: score=47.75 a57=7 D61=13 chart=(dh,dCh)
  restart 4: score=38.40 a57=5 D61=12 chart=(dCh,dh)   ← chamber-chart best
  restart 5: score=44.95 a57=6 D61=15 chart=(dCh,dh)
  restart 6: score=42.80 a57=4 D61=11 chart=(dT2,dCh)  ← lowest a57
  restart 7: score=45.30 a57=7 D61=11 chart=(dh,dCh)
0/8 chamber_hits
```

## F315 vs F316 head-to-head

| Metric | F315 (F358 seed) | F316 (F359 seed) |
|---|---:|---:|
| Best score              | 38.90  | **38.40** |
| Lowest a57_xor_hw       | 4 (r0) | 4 (r6)    |
| Lowest D61_hw           | 9 (r0) | 11 (r6)   |
| Avg chart matches/restart | 127  | **156**   |
| Best in (dh,dCh) family chart | r6 (a57=8 D61=11) | **r4 (a57=5 D61=12)** |
| Wall                    | 54.2s  | 56.6s     |

## Findings

### Finding 1 — Both yale seeds break the F314 quasi-floor

F314 alpha sweep showed a57=5 was the hard quasi-floor for random-init
8x20k search regardless of weight tuning. Both yale chamber seeds (F358 and
F359) reach a57=4 in the F315/F316 atlas-loss continuation. **The
chamber-adjacent initialization is the mechanism that breaks the floor**;
the specific seed objective (true-mismatch vs atlas-aware) doesn't matter
for breaking the floor.

### Finding 2 — F359 (atlas-aware seed) gives better chart consistency

F316 averages 156 chart matches per restart vs F315's 127 (+23%). The
atlas-aware seed puts the search in chamber-chart-coherent neighborhoods
with more accepting moves per restart.

### Finding 3 — Best chart-coherent point is F316 r4

a57=5, D61=12, chart=(dCh, dh) — best (dh, dCh)-family point across F315 + F316.
F315 r0 has lower a57 (4 vs 5) but in non-chamber chart (dSig1, dT2).
**Tradeoff**: best a57 OR best chart, not both.

### Finding 4 — Chamber attractor still unreached after 16 restarts × 20k

F315 + F316 = 16 restarts × 20k = 320k total iterations from chamber-adjacent
init. 0 chamber_hits. The attractor (a57=0 AND D61≤4 AND chart=(dh,dCh))
remains brittle even with chamber-seeded initialization.

The structural picture: chamber-adjacent init reduces the gradient-descent
gap, but the attractor's basin in dM-mutation space is too small for
single-bit-flip moves to land in it.

## Concrete next moves (ranked)

**(a) Multi-bit dM moves**: extend mutator to do 2-bit and 3-bit combined
flips on (M[0], M[9]) — the cascade-1 kernel words. Currently single-bit
only. ~15 minutes work, possibly the missing piece.

**(b) Yale: 1M-step F358-style run with atlas-aware objective**: F358 had
100k steps × 8 restarts = 800k. F359 had 20k × 4 = 80k (10x less).
Matching F358 compute under atlas-aware objective should reach
true_mismatch_hw < 20 with chart=(dCh, dh) — the BEST seed config.

**(c) Larger active mask + chamber-seed**: F315/F316 used 5-word mask.
Trying all-16 active words + chamber seed might give the search enough
freedom to navigate the chamber attractor's basin.

## What's shipped

- F316 JSON + this memo.
- (F315 was a separate ship.)

## Discipline

- 56.6s wall.
- Direct comparison vs F315.
- 0 chamber_hits — honest.
- Cross-machine collaboration cycle: yale → F358 → F315 → yale → F359 → F316.
