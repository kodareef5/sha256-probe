# Moonshot Test: bits (17,19) at N=32 — TIMEOUT

**Date**: 2026-04-11
**Evidence level**: EVIDENCE (negative — inconclusive between UNSAT and slow-SAT)

## Result

Predicted critical pair (17,19) — sigma1 rotation positions at N=32:
**TIMEOUT at 7200s (3 parallel seeds)**

This is NOT definitive UNSAT. Possibilities:
1. (17,19) is UNSAT at N=32 → prediction wrong (consistent with N=6 refutation)
2. (17,19) is SAT but takes >2h → needs longer timeout or CaDiCaL
3. The critical pair at N=32 is at different positions entirely

## Context

At N=8: critical pair (4,5) was found SAT in 118s
At N=6: critical pairs (1,3) and (2,5), NOT the predicted (3,4)

The simple "critical pair = sigma1 rotations" hypothesis was already
refuted at N=6. This N=32 timeout is consistent with that refutation.

## What this tells us

Finding the critical pair at N=32 requires either:
1. Full C(32,2)=496 pair scan (infeasible — each takes hours)
2. Better theory for predicting critical positions
3. Alternative approach (e.g., encode with 3-bit freedom instead of 2)

## Next steps

- Try 3-bit removal at N=32 (C(32,3)=4960 triples, but test only predicted)
- Try the carry-automaton DP approach to find sr=61 solutions directly
- Focus on the carry linearization framework which doesn't need the critical pair
