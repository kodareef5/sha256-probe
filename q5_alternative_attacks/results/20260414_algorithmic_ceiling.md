# The 3x Algorithmic Ceiling: Why Symbolic Approaches Can't Beat Concrete

Date: 2026-04-14 23:45 UTC

## The Finding

The cascade construction makes da=0 for ALL message words at ALL
cascade rounds (57-60). This means there are NO differential constraints
to exploit during the free rounds. Symbolic approaches (FACE, BCSDP,
quotient DP) see no pruning opportunities that concrete evaluation misses.

The ONLY collision-discriminating constraints come from the schedule-
determined rounds (61-63), where W[61..63] are fixed by the schedule.
Our de61=0 structural filter already captures this optimally.

## Evidence

| Approach | Branches | Wall-clock | Why limited |
|----------|----------|-----------|-------------|
| NEON brute force | 4.3B | 2.1s | Baseline |
| Structural (de61) | 4.3B filtered | **0.68s** | Rounds 62-63 saved |
| FACE 8-var (round 59 only) | 33.4M | 45s | Only 8 vars in GF(2) |
| FACE 16-var (rounds 59-60) | 33.4M | 44s | Same — no more pruning |
| face_full (all 32 vars) | 33.4M | 44s | **Cascade kills all constraints during r57-60** |
| Quotient transducer | N/A | N/A | 0% dedup (state > input space) |

## The Root Cause

The cascade DP CONSTRUCTS W2 such that da=0 is always satisfied:
  W2[r] = W1[r] + cascade_offset(state_r)

This means: for ANY choice of W1[r], there exists a W2[r] that works.
The differential constraint da=0 is VACUOUS during cascade rounds.
No filter, symbolic or concrete, can prune based on it.

The schedule-determined rounds (61-63) are different: W2[r] is NOT
chosen to satisfy da=0. It's fixed by the schedule. So da[r]=0 becomes
a non-trivial constraint that can discriminate collisions.

## Implication

The 3.08x speedup from de61=0 is the CEILING for register-diff
approaches on the cascade-DP problem structure. Carry-space approaches
can potentially do better by reasoning about WHICH carry patterns at
round 60 lead to dT1_61=0 — but this requires O(2^{0.76N}) enumeration
(the carry automaton width), which at N=8 gives 260 = no savings.

The only way to beat 3x is to change the PROBLEM STRUCTURE:
- Different cascade construction (not da=0 based)
- Multi-block attack (block 2 compensates)
- Direct carry-pattern construction (the FACE mode-branching idea at large N)

## For the Paper

This is a NEGATIVE RESULT that belongs in the paper:
"The cascade construction's permissiveness during free rounds creates
 a fundamental 1/2^N algorithmic ceiling for differential-based filtering."

Evidence level: VERIFIED (exhaustive at N=8, confirmed by 5 independent implementations)
