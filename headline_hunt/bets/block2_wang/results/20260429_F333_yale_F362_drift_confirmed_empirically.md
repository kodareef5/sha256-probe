---
date: 2026-04-29
bet: block2_wang × math_principles cross-machine
status: F331_DRIFT_CONFIRMED — yale's F362 best pairs all have HW≥9 cross-word diff
---

# F333: F331 drift warning empirically confirmed via yale's F362 JSON

## Setup

F331 (sent 16:00 EDT) warned yale that F366/F367 results likely include
the F322-style drift artifact: probe_atlas_neighborhood's `raw_m1` /
`raw_m2` modes break cascade-1 kernel preservation. F362 is the
upstream Pareto-descendant continuation that all F36x continuations
seed from.

F333 directly inspects yale's F362 JSON to see whether the (M1, M2)
pairs labelled "best" are actually cascade-1 collision pairs.

## Reference: cascade-1 kernel structure (idx=0)

A cascade-1 collision pair (M1, M2) for idx=0 must satisfy:
- M1[0] ^ M2[0] = 0x80000000 (bit 31)
- M1[9] ^ M2[9] = 0x80000000 (bit 31)
- M1[i] ^ M2[i] = 0 for all i ∈ {1,2,3,4,5,6,7,8,10,11,12,13,14,15}

Any (M1, M2) pair that violates this is NOT a cascade-1 collision
candidate, regardless of how good its atlas score is.

## Result

Inspected 5 of 28 (M1, M2) pairs in `20260429_F362_pareto_descendant_continuation.json`.

```
[descendant_runs[0].best]: ✗ DRIFT
  nonzero diff at words 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
  (ALL 16 WORDS have nonzero diff)

[descendant_runs[0].restarts[0].best_a57]: ✗ DRIFT
  nonzero at: w0,w1,w6,w7,w8,w9,w11,w13,w15

[descendant_runs[0].restarts[0].best_chart]: ✗ DRIFT
  same pattern as best_a57

[descendant_runs[0].restarts[0].best_score]: ✗ DRIFT
  same pattern

[descendant_runs[0].restarts[1].best_a57]: ✗ DRIFT
  nonzero at: w0,w1,w2,w3,w4,w6,w7,w8,w9,w10,w11,w13,w14,w15
```

**0 of 5 pairs inspected satisfy the cascade-1 kernel constraint.**

## Forensic detail (descendant_runs[0].best)

| Word | M1^M2 |
|---:|---|
| 0 | 0xc0207014 (HW 7, includes bit 30 + bit 31) |
| 1 | 0x00000015 (HW 3) |
| 2 | 0x1000149c (HW 7) |
| 3 | 0x01210000 (HW 3) |
| 4 | 0x04001000 (HW 2) |
| 5 | 0x00000600 (HW 2) |
| 6 | 0x10218000 (HW 4) |
| 7 | 0x91030000 (HW 5) |
| 8 | 0x00100402 (HW 3) |
| 9 | 0x49060138 (HW 8) |
| 10 | 0x04048000 (HW 3) |
| 11 | 0x00201180 (HW 4) |
| 12 | 0x00280008 (HW 3) |
| 13 | 0x24000020 (HW 3) |
| 14 | 0x00100080 (HW 2) |
| 15 | 0x55020004 (HW 5) |

Total message diff HW = 64 bits across 16 words. The cascade-1 kernel
contributes 2 bits (bit 31 at words 0 and 9). The remaining 62 bits
are pure drift outside the cascade-1 search space.

Word 0 has 0xc0207014 — bit 31 is set ✓ (kernel diff present), but
also bits 30, 13, 12, 4, 2 are set (drift adds 6 more bits at word 0).
Word 9 has 0x49060138 — bit 31 NOT set (the cascade-1 kernel
requirement at word 9 is VIOLATED entirely).

## Implication

Yale's F360-F365 Pareto-descendant continuation reports atlas scores
as low as 35.4 (a57=5 D61=9 chart=(dh,dCh)). These are real measurements
of the drift-allowed atlas-loss landscape but are NOT cascade-1
collision progress.

The TRUE cascade-1 floor at this compute level is what F322 measured:
- F321 yale-seeded kernel-preserving: a57=5 D61=10 score=41.20
- F322 random-init kernel-preserving: a57=5 D61=8  score=39.65

Yale's best 35.4 score (drift-allowed) does NOT translate to a 35.4
cascade-1 floor.

## What stays valid from F360-F365 + F366-F368

- The Pareto-front structure (F360) is a real characterization of the
  drift-allowed landscape's tradeoffs. Useful for understanding the
  multi-objective shape, just not as cascade-1 progress.
- The brittleness extension to pair/triple/quadruple moves (F366/F367/F368)
  in raw count terms (0/2559 pairs etc.) extends F311 brittleness across
  multi-bit moves. This statement is robust to drift status — even the
  larger drift-allowed search space cannot reach the chamber attractor
  with multi-bit moves.

## Concrete recommendation

Yale: re-run F361/F362 (the upstream descendants) with `--modes
common_xor,common_add` only. That eliminates raw_m1 and raw_m2 from
the move set. The Pareto front under kernel-preserving moves is the
cascade-1-valid structural object. Predicted result: smaller front,
higher atlas scores, but each member is a true cascade-1 candidate.

## What's shipped

- F333 empirical confirmation of F331 with yale's own F362 JSON data.
- 5 inspected (M1, M2) pairs from F362 — all drift, 0 cascade-1-valid.

## Discipline

- ~5 min wall (Python forensic scan).
- 0 SAT compute.
- Empirical confirmation of F331's claim with concrete data points.
- This is the cross-machine version of F322's self-retraction: catching
  the drift artifact in another machine's pipeline before it propagates
  further.

## Cross-machine status

This is the 6th cross-machine drift artifact this 2-day arc:
1. F205 retraction (basin transferability, mine)
2. F232 retraction (cross-cand transfer, mine)
3. F237 retraction (preprocessing speedup, mine)
4. F279 retraction (transient minimum, mine)
5. F288/F309 retraction (corpus redundancy, mine)
6. F322 retraction (chamber-seed floor break, mine)
7. **F333 drift confirmation (yale's F362 series)** ← this memo

The discipline pattern holds: catch drift early, document precisely,
distinguish what stays valid from what was overstated. Cross-machine
flywheel needs the same discipline on both sides to produce real
cascade-1 progress.
