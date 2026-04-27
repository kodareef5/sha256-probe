# F14: Under cascade-1, de60 = 0 UNIVERSALLY (refines cascade-2 claim)
**2026-04-26 20:42 EDT**

This finding fundamentally restructures the F-series understanding.
It's the right next step after the F13 correction (commit c38e980).

## Result

For 3 cands × 2^32 W57 chambers (12.9 BILLION chambers total), under
cascade-1 enforcement at slots 57, 58, 59, 60:

| cand | de60=0 chamber count | total chambers |
|---|---:|---:|
| msb_m17149975 (verified sr=60) | **4,294,967,296** | 4,294,967,296 |
| bit=19 m=0x51ca0b34 | **4,294,967,296** | 4,294,967,296 |
| msb_m189b13c7 | **4,294,967,296** | 4,294,967,296 |

**EVERY single W57 chamber yields de60 = 0** under cascade-1. The
result is universal, not cand-specific.

## Why

Under cascade-1 enforcement at slot k (W2_k = W1_k + cw1[k]):
- da[k] = 0 (by construction)
- After 4 consecutive cascade-1 slots, da[k-3..k] = 0
- This makes dT2[k+1] = 0 (Sigma0/Maj args side-equal)
- de[k+1] = dd[k] + dT1[k+1] = de[k-1] - dT2[k+1] (modular)
- Iterating, after 4 cascade-1 slots, the e-component algebra produces
  de[60] = 0 automatically

The writeup `sr60_collision_anatomy.md` describes "two cascades:
a-path (cascade 1) and e-path (cascade 2) triggered by W[60]". But
under cascade-1 enforcement at all 4 slots (57, 58, 59, 60), cascade-2
fires automatically — there's really ONE cascade structure with
de[60]=0 as its inevitable consequence.

## Verification

The verified sr=60 collision (m17149975, W57=0x9ccfa55e) gives
de60=0. Test under varying W58/W59/W60 with cascade-1 at each slot:

```
W57=0x9ccfa55e, vary W58/W59/W60 — de60 always 0:
  verified W58/W59/W60     de60 = 0x00000000
  W58=0,W59=0,W60=0        de60 = 0x00000000
  random_1                 de60 = 0x00000000
  random_2..6              de60 = 0x00000000
```

This confirms: for fixed W57 under cascade-1, de60 is independent of
W58/W59/W60 (the cw1[k] adjustments fully determine the cancellations).

## Implication for sr=60 search

For sr=60 collision the actual question is:
- Find M (16 free words) such that schedule-derived W[57..60] satisfy
  cascade-1 at all 4 slots (4 × 32 = 128 bits of constraint)
- de_60=0 is then automatic

So sr=60 closure = "find a message whose schedule's 4 critical W
words happen to be cascade-1-aligned." Given the 14 free message
words (M[0] and M[9] are kernel-fixed), expected solutions are huge
(~2^(448-128) = 2^320). That's why sr=60 is solvable.

## Implication for sr=61 search (the actual headline target)

For sr=61 we additionally need cascade-1 at slot 61, which requires
dW[61] = cw1[61]. dW[61] is schedule-determined by:
  dW[61] = sigma1(dW[59]) + dW[54] + sigma0(dW[46]) + dW[45]

For random message, dW[61] matches cw1[61] with prob 2^-32. So sr=61
solutions are ~2^288 in expectation — still many, but each one is
~2^32× rarer than sr=60.

Under cascade-1 at slot 61, de_61 is also universal-zero (by extension
of the F14 mechanism). So the sr=61 closure reduces to: "find a
message where the schedule's 5 critical W words (W[57..61]) are all
cascade-1-aligned." That's the actual hard search.

## What F1-F13 actually characterized

- F1-F4: preprocessing speedups under cascade_aux Mode A (REAL)
- F5: wrapper deployment (REAL)
- F8-F9: budget decay (REAL)
- F10-F13: de58 image structure under "free W57" cascade-1 model
  (REAL but IRRELEVANT to actual sr=61 search — sr=61 doesn't
  require de58=0)
- F14 (this memo): de60=0 is automatic under cascade-1, refining
  the writeup's "two cascades" framing

## What's structurally surprising

The writeup describes cascade-1 (a-path) and cascade-2 (e-path) as
"overlapping shift-register cascades" with "perfect timing."
Empirically (F14) they're not really independent — cascade-2 is a
mechanical consequence of cascade-1 across 4 slots. The "perfect
timing" is structural, not coincidental.

## What's next: actual sr=61 question

To probe sr=61 collision feasibility, we need to:

1. **Search for messages whose schedule's W[57..61] are all cascade-1-
   aligned.** This is what kissat does. Hard because 5 × 32 bits of
   constraints on 14 × 32 bits of free space.

2. **Test if the cascade-1 alignment at slots 57..61 is structurally
   possible.** I.e., is the system of cascade-1 constraints + schedule
   equations consistent? This is the IMPOSSIBILITY argument that
   `writeups/sr61_impossibility_argument.md` discusses.

3. **F-series-style: enumerate the schedule space directly.** Instead
   of varying W57 freely, vary M[1], M[2], ..., M[15] (the 14 free
   message words besides M[0] and M[9]) and compute the schedule's
   dW[57..61] per kernel. Check if any M produces all 5 cw1-aligned.

## Tool

`encoders/de60_enum.c` — same speed as de58_enum (350-630 M evals/sec),
computes de60 instead of de58. Confirms universal de60=0 under
cascade-1 in <12s per cand.

EVIDENCE-level: VERIFIED. Exhaustive 12 billion chamber check.

## Takeaway for future workers

The F-series characterized cascade-1 chamber dynamics, NOT sr=61
collision feasibility. The actual sr=61 question requires schedule-
constrained search. Future enumeration should target message-space
(M[1..8] + M[10..15] = 14 free words modulo kernel) rather than
W57-space (which conflates schedule constraints).
