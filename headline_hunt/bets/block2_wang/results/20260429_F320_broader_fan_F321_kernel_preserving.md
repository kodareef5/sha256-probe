---
date: 2026-04-29
bet: block2_wang × math_principles cross-machine
status: F320_BROADER_FAN_FINDS_a57=3 + F321_KERNEL_PRESERVING_REVEALS_DRIFT_ARTIFACT
---

# F320 + F321: broader fan + kernel-preserving structural fix

## F320: broader restart fan (32 × 20k vs F319's 8 × 50k)

Same total compute (~640k vs 400k iter), 32 restarts instead of 8.

### F320 result

- best_overall_score = **38.90**
- best_overall_a57 = **3** (NEW LOW; restart 29, chart=(dh,dSig1), D61=19)
- best_overall_D61 in chamber chart = 9 (restart 19; a57=7)
- 29/32 (91%) restarts best in chamber chart family
- 0/32 chamber attractor hits

**a57=3 is a new low** but in non-chamber chart (dh, dSig1). The trade-off
between a57 and chart membership persists.

### F320 vs F319 takeaway

Broader fan (32×20k) finds rarer basins than longer iters (8×50k):
- F319 best a57: 5
- F320 best a57: **3**
F319 best D61 in chamber chart: 9
F320 best D61 in chamber chart: 9 (same)

Broader fan helps for hard-floor breakthroughs (a57: 4 → 3); equal for
basin-depth (D61: stuck at 9 in chamber chart unless lucky).

## F321: kernel-preserving search (CRITICAL STRUCTURAL FIX)

### Discovery

While inspecting F318 r2's best (M1, M2) pair, I found:
- M1 ^ M2 = (HW=13, HW=8, HW=14, 0, 0, 0, 0, 0, HW=19, HW=15, 0, ..., 0)
- The cascade-1 kernel for idx=0 is bit-31 ONLY on M[0] and M[9].
- F318 r2's M2 had drifted FAR from M1 ^ kernel.

**F315-F320 search drifts away from cascade-1 kernel pattern**. The atlas
score is achievable, but the resulting (M1, M2) pair is NOT a cascade-1
collision candidate — it's an arbitrary-diff pair that happens to land
in the chamber chart family.

For a TRUE cascade-1 attack, the search structure must be:
- Mutate M1 (any words)
- Keep M2 = M1 ^ kernel rigid (kernel = bit-31 on M[0]+M[9])
- Score the resulting cascade-1 pair

This is what F321 implements.

### F321 result

```
# kernel_diff nonzero words: [(0, '0x80000000'), (9, '0x80000000')]  ← rigid cascade-1 kernel
  restart 0: score=46.60 a57=6 D61=16 chart=(dCh,dh)
  restart 1: score=41.20 a57=5 D61=15 chart=(dCh,dh)   ← best score
  restart 2: score=48.70 a57=8 D61=10 chart=(dh,dCh)
  restart 3: score=49.10 a57=8 D61=11 chart=(dh,dCh)
  restart 4: score=50.10 a57=8 D61=11 chart=(dh,dCh)
  restart 5: score=45.40 a57=6 D61=16 chart=(dCh,dh)
  restart 6: score=47.55 a57=6 D61=17 chart=(dh,dCh)
  restart 7: score=51.60 a57=7 D61=17 chart=(dCh,dh)
8/8 chamber chart, 0 chamber_hits
```

### Cross-mechanism comparison (TRUE cascade-1 vs drift-allowed)

| Mechanism | Best score | Best a57 | Best D61 | Chamber chart% | Cascade-1 valid? |
|---|---:|---:|---:|---:|:---:|
| F312 random-init drift   | 38.85 | 5 | 12 | 100% | NO  |
| F315 F358-seed drift     | 38.90 | 4 | 9  | 63%  | NO  |
| F318 annealed drift      | 40.10 | 4 | 7  | 88%  | NO  |
| F319 annealed 50k drift  | 39.10 | 5 | 9  | 100% | NO  |
| F320 32-fan annealed drift | 38.90 | 3 | 9  | 91%  | NO  |
| **F321 kernel-preserving** | **41.20** | **5** | **10** | **100%** | **YES** ✓ |

**Critical**: F321 is the only TRUE cascade-1 result. F315-F320's lower
metrics came from search-space relaxation (M2 drift), not from finding
better cascade-1 candidates.

### Implications

1. **F315-F320's a57=3,4 results are NOT cascade-1 wins**. They show the
   atlas-loss landscape is reachable in some non-cascade-1 region.

2. **The actual cascade-1 best is F321's a57=5, D61=10 in chamber chart**.
   This is the floor for chamber-seeded annealed kernel-preserving search.

3. **F312 baseline (random-init, drift) atlas=38.85 is NOT a cascade-1
   floor** either — it's the drift-allowed floor. The kernel-preserving
   F312-equivalent (random-init kernel-preserving) is unmeasured.

### Required follow-up

Run F312-equivalent BUT KERNEL-PRESERVING. That gives the random-init
cascade-1 baseline. If F312-kernel-preserving > F321 atlas score, then
chamber-seed init helps EVEN under kernel preservation. If F312-kp ≈ F321,
then chamber-seed init's apparent benefit was mostly from drift.

This is the CRITICAL experiment: it determines whether the cross-machine
flywheel produces a real cascade-1 advance or just a drift-space artifact.

## Discipline

- F320: 285s wall (32×20k).
- F321: 54s wall (8×20k).
- Honest discovery of drift artifact during F318 r2 inspection.
- Honest report that F321 (true cascade-1) shows worse atlas metrics —
  the drift-space results overstated cascade-1 progress.
- Critical follow-up identified: F322 = random-init kernel-preserving.

## What's shipped

- F320 JSON
- `search_kernel_preserving.py` (encoder)
- F321 JSON
- This memo (combined for both F320 and F321 since they're paired findings)

## Next move

**F322: random-init kernel-preserving baseline.** Without yale's
chamber-seed init, with kernel preserved, what's the atlas floor? If
F322 ≈ F321, chamber-seed gave nothing in true cascade-1; if F322 > F321
(worse), chamber-seed gave real cascade-1 benefit.

Wall ~3 minutes. Critical for honest accounting.
