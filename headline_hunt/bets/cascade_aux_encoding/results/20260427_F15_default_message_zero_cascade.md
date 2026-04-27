# F15: 0/67 default messages have natural cascade-1 at slot 57+
**2026-04-26 20:55 EDT**

Followup to F14. Confirms the cascade-1 multi-slot search is non-trivial:
no registry cand's "trivial" message [m0, fill, fill, ..., fill] satisfies
cascade-1 beyond slot 56.

## Setup

For each registry cand, take the default message:
```
M = [m0, fill, fill, fill, fill, fill, fill, fill, fill, fill,
     fill, fill, fill, fill, fill, fill]
```
(M[0] = m0, M[1..15] = fill). Compute the SHA-256 schedule W[0..63]. Run
SHA-256 forward through round 56 to get state. Then check at each slot k
in {57..63} whether the schedule's dW[k] = cw1[k] (the cascade-1
condition).

## Result

**0 of 67 cands** have cascade-1 at slot 57 with the default message.
Same at slots 58, 59, 60, 61, 62, 63.

This means: cascade-1 at slot 57+ requires a NON-TRIVIAL M. The kissat
search problem at sr=61 is real — it's finding those 14 free message
words (M[1..8], M[10..15]) such that the schedule's dW[57..61] all
align with cw1[57..61].

## Connection to F14

F14 showed: under cascade-1 enforcement at slots 57..63, the final
SHA-256 output state matches between M1 and M2. So cascade-1 at 7 slots
= FULL COLLISION.

F15 shows: the default registry messages don't naturally satisfy this
at any slot beyond 56. The collision is hidden in the message-space
search.

## What this means for the project

For each cand, the "is sr=63 collision reachable via cascade-1?"
question reduces to:
  Does there exist M[1..8, 10..15] ∈ (Z/2^32)^14 such that the
  schedule's dW[57..63] are all cascade-1-aligned?

Each slot's cascade-1 condition is a 32-bit equation on the schedule.
7 slots × 32 = 224-bit constraint on 14 × 32 = 448 free bits.
Expected solutions: 2^(448-224) = 2^224.

But: the constraints are nonlinear via sigma0/sigma1 and via the
state's dependence on M. The "impossibility" question is whether the
constraint system is genuinely solvable.

For sr=61 specifically (5 slots cascade-1): 5 × 32 = 160-bit constraint.
Expected solutions: 2^288 — many in principle.

For full sr=63 collision: 7 × 32 = 224-bit constraint. Expected
solutions: 2^224 — still many.

So sr=63 collisions via cascade-1 have a HUGE expected count if the
constraints were random. They aren't found because:
1. The constraints are highly structured (nonlinear schedule)
2. kissat hasn't searched long enough
3. OR: the structure makes the constraint system fundamentally
   inconsistent (impossibility)

## What's next

1. **F16**: pick the best-positioned cand (e.g., msb_m17149975 or one
   with low default-cascade misalignment) and quantify HOW FAR the
   default schedule's dW deviates from cw1[k] at each slot. Small
   deviations might be reachable by minor M-perturbations.

2. **F17**: search over message-space (14-dim) for cascade-1 alignment
   at slots 57, 58. With the C tool's speed (350M evals/sec for de-
   computation), we could check 100M random messages in ~1 sec.
   Looking for ones with cascade-1 at slot 57 (32-bit constraint
   = 1 hit per 2^32 = 4.3B random messages = ~13s).

3. **Chart-preserving operator (yale)**: instead of perturbing W57
   space (which ignores schedule constraints), perturb M-space and
   check what cascade-1 alignment looks like.

## Honest framing summary

The F-series this session characterized cascade-1 chamber dynamics
in a hypothetical free-W57 model. F14+F15 connect that to the actual
collision-search problem (schedule-constrained M-space search).
Neither directly solved sr=61, but they clarify what the right
question is.

EVIDENCE-level: VERIFIED. Default-message check is exhaustive for
the 67 registry cands.
