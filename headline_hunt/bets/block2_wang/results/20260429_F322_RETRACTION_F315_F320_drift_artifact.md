---
date: 2026-04-29
bet: block2_wang × math_principles cross-machine
status: RETRACTION — F315-F320 "chamber-seed breaks a57=5 floor" was DRIFT ARTIFACT
---

# F322: RETRACTION of F315-F320 chamber-seed claims

## What was claimed

F315: "yale F358 chamber-seed init breaks the F314 a57=5 quasi-floor"
F316: "Both F358 and F359 seeds break the floor"
F318: "Annealed mutator hits D61=7 in chamber chart" (vs F312's 12)
F319: "Longer iter doesn't help; F318 r2 stands as best"
F320: "Broader fan finds a57=3"

**These claims are NOT valid for cascade-1 collisions.** They overstated
the result by exploring a search space LARGER than cascade-1.

## What went wrong

The F315 search used `mutate_M2(M1, M2, ...)` from `search_schedule_space.py`.
This mutates M2 freely on active words. Under that mutator, M2 drifts away
from `M1 ^ kernel` over the search.

For cascade-1 collisions, the kernel pattern (idx=0: bit-31 on M[0] and M[9]
ONLY) must be preserved. Any M2 with diff at other words is NOT a cascade-1
collision candidate.

Inspecting F318 r2's "best" point:
```
M1[0]^M2[0] = 0x99059227  (HW 13, multiple bits, NOT bit-31 cascade-1 kernel)
M1[1]^M2[1] = 0x0a488242  (HW 8,  spurious word-1 diff)
M1[2]^M2[2] = 0xee202715  (HW 14, spurious)
M1[8]^M2[8] = 0x83ffa725  (HW 19, spurious word-8 diff — should be 0)
M1[9]^M2[9] = 0x40af53c3  (HW 15, NOT bit-31 cascade-1 kernel!)
```

**This is not a cascade-1 collision pair.** It's an arbitrary-diff pair that
happens to land in the chamber chart family of the atlas-loss landscape.

## F321 (kernel-preserving) was the structural fix

F321 implemented the correct cascade-1 search: mutate M1 only, keep
`M2 = M1 ^ kernel` rigid. Result with yale F358 chamber-seed init:
- best_score = 41.20
- best a57 = 5
- best D61 = 10

## F322: random-init kernel-preserving baseline

F322 = same as F321 but with random M1 init (no chamber seed). Result:
- best_score = **39.65** (r5: a57=5, D61=14, chart=(dh,dCh))
- best a57 = 5
- best D61 in chamber chart = **8** (r2: a57=8, D61=8, chart=(dh,dCh))

## True cascade-1 comparison

| Mechanism | Best score | Best a57 | Best D61 in chamber chart | Cascade-1 valid? |
|---|---:|---:|---:|:---:|
| F321 yale-seeded kernel-preserving | 41.20 | 5 | 10 | YES |
| **F322 random-init kernel-preserving** | **39.65** | 5 | **8** | YES |

**Random init beats yale chamber-seed under strict cascade-1.**

## What the cross-machine flywheel actually shows

- yale's F358 produced M1 with `(W57, W58, W59)` close to chamber idx=0
  values (true mismatch=24 bits).
- That M1, plugged into kernel-preserving cascade-1 search, gives WORSE
  atlas scores (41.20) than random M1 (39.65).
- Reason: yale's F358 M1 is constrained near a single chamber neighborhood;
  random M1 explores the full cascade-1 landscape, which includes basins
  that don't overlap with chamber-W57..W59 but still produce low D61 in
  chamber chart (e.g., F322 r2 gets D61=8 with arbitrary M1).

**The chamber-seed init's apparent benefit in F315-F320 came entirely from
allowing M2 to drift outside cascade-1, NOT from cascade-1 search benefit.**

## Retraction-formal

The following claims from prior memos are RETRACTED:

1. F315 memo: "yale-seeded atlas search breaks a57=5 quasi-floor". 
   The break was non-cascade-1.
2. F316 memo: "Both F358 and F359 seeds break the floor". Same artifact.
3. F318 memo: "annealed mutator hits D61=7 in chamber chart, NEW LOW".
   The (M1, M2) pair was not cascade-1.
4. F320 memo: "broader fan finds a57=3". Not cascade-1.

What remains valid:
- F311: Carry-Chart Atlas tool itself (verified vs C ground truth) ✓
- F312: chain-output-diff vs atlas-loss comparison conceptually valid ✓
  but the atlas-loss-search a57=5 D61=12 was drift-allowed; the actual
  cascade-1 floor (F322 random kp) is a57=5 D61=8 (better than what F312
  reported because F312 didn't enforce kernel either).
- F321: chamber-seed kernel-preserving cascade-1 result (a57=5, D61=10) ✓
- F322: random-init kernel-preserving cascade-1 baseline (a57=5, D61=8) ✓

## Updated picture

For TRUE cascade-1 (kernel preserved):
- Random-init annealed search at 8×20k ≈ a57=5, D61=8 in chamber chart
- yale chamber-seed adds NO cascade-1 benefit (worse atlas: 41.20 vs 39.65)
- F314 a57=5 quasi-floor IS the cascade-1 floor (both F312 and F322 hit it)

The chamber attractor (a57=0, D61=4, chart=(dh,dCh)) remains unreached.
For cascade-1 specifically, the attractor distance is now (5 a57-bits, 4
D61-bits) — same as what F312 reported once we re-interpret F312 in the
correct frame.

## Discipline

- Honest retraction of 4 prior claims within an hour of the structural
  discovery.
- The retraction itself is structural information: cascade-1 vs drift-allowed
  search are different problems.
- 5th retraction this 2-day arc (after F205, F232, F237, F279, F288, F309).
  Consistent with the F1 verification protocol's spirit.

## Actionable takeaways

1. **All future atlas-loss search must enforce kernel preservation** for
   cascade-1 claims. Use `search_kernel_preserving.py`, not the F315-F320
   variants.
2. **Yale's chamber-seed work is still valuable** for non-cascade-1
   exploration but does not (yet) help cascade-1 search.
3. **Drift-allowed search is informative about the loss landscape** but
   should not be reported as cascade-1 progress.

## Concrete next moves

(a) Re-run F315-F320 mechanisms under kernel preservation. Compare F321
    (chamber-seed kernel-preserving) vs F322 (random-init kernel-preserving)
    at larger compute (32×20k, 8×50k) to see if either approach wins
    consistently.

(b) Yale: chamber-seed search must be EVALUATED via a kernel-preserving
    atlas score during the free-var optimization. Otherwise yale's
    optimization is also exploring outside cascade-1.

(c) Update F311 atlas to optionally enforce kernel-pair check at evaluation
    time, returning "not_cascade_1" status for non-kernel pairs.

## Cross-bet implication

The block2_wang × math_principles cross-machine flywheel is INFORMATIVE
but has been measuring the wrong thing. Both bets need to retrofit
kernel-preservation discipline. F315-F320 results are valid as
"atlas-loss landscape exploration" but not as "cascade-1 collision
search progress".
