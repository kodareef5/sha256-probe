# Critical Pair Test at N=32: 2-Bit Relaxation Likely Insufficient

**Date**: 2026-04-11
**Evidence level**: EVIDENCE (5 instances approaching timeout, not yet confirmed)

## Background

Macbook found at N=8: removing bits (4,5) from W[60] schedule enforcement
makes sr=61 SAT in 118s. All other 27 pairs remain UNSAT.

Predicted N=32 critical positions: near sigma1 rotations (17, 19, >>10).

## Test

Encoded sr=60.5: sr=60 with W[60] partially schedule-constrained.
Specific bit pairs left free, rest enforced via message schedule.

5 Kissat instances (seed=5, 1h timeout, nice -19):
- (17,19) — direct sigma1 rotation boundary
- (16,20) — scaled from N=8's (4,5)
- (17,18) — adjacent to rotation
- (18,19) — adjacent to rotation  
- (10,17) — sigma1 shift + rotation

## Result (preliminary — approaching 1h timeout)

All 5 instances running 38+ min wall clock at ~44% CPU = ~17 min effective
solver time. None have terminated. Conflict rate ~16K/s (comparable to
full sr=60). No qualitative difference from the fully free sr=60 problem.

**Expected outcome**: all 5 timeout → 2-bit relaxation NOT sufficient at N=32.

## Also launched

3 instances with more free bits (3, 4, 5 bits near sigma1 boundary):
- (10,17,19), (9,10,17,19), (9,10,16,17,19)
- These have 50+ min remaining of their 1h timeout

2 instances of full sr=60 on bit-2 candidate (M[0]=0x67dd2607, 12h timeout):
- If SAT: second sr=60 collision on a different kernel

## Interpretation

The critical pair phenomenon from N=8 does NOT trivially scale to N=32.
Possible reasons:
1. **N=32 carry chains are much more complex** — 32-bit carries create
   constraints that don't exist at N=8 (which has 8-bit carries)
2. **The critical positions might be DIFFERENT at N=32** — not simply
   scaled from (4,5) at N=8
3. **N=32 might need MORE free bits** — consistent with macbook's finding
   that N=10 already needs more freedom than N=8
4. **The problem is qualitatively harder** — the phase transition K* might
   not follow a simple scaling law

## What this rules out

If confirmed (all 5 timeout): removing 2 bits from W[60] schedule at N=32
is NOT enough to break the sr=61 barrier. The obstruction at N=32 is more
complex than at N=8.

This doesn't rule out:
- Removing 3-5 bits (still testing)
- Different bit positions (496 possible pairs)
- Non-adjacent bit relaxation patterns
- Combined relaxation of W[60] + other schedule equations
