---
date: 2026-04-29
bet: math_principles
status: W57_CORE_PAIR_ANALYSIS
---

# F384: W57 core-pair analysis

## Summary

Verdict: `w57_pair_has_single_forbidden_polarity`.
Treat the forbidden W57 pair as a sound two-bit bridge constraint candidate.
Pair: dW57[22], dW57[23].

## Polarity Tests

| dW57[22] | dW57[23] | Literals | Status | Wall |
|---:|---:|---|---|---:|
| 0 | 0 | `[-12419, -12420]` | `UNKNOWN` | 2.004764 |
| 0 | 1 | `[-12419, 12420]` | `UNSATISFIABLE` | 0.251157 |
| 1 | 0 | `[12419, -12420]` | `UNKNOWN` | 2.004102 |
| 1 | 1 | `[12419, 12420]` | `UNKNOWN` | 2.004863 |

## Target Values

| Target | dW57[22] | dW57[23] | Candidate |
|---|---:|---:|---|
| `F378_D61_floor_guard_explosion` | 0 | 1 | a57=19 D61=4 chart=`dCh,dh` |
| `F375_D61_to_guard_bridge` | 1 | 0 | a57=5 D61=13 chart=`dCh,dh` |
| `F374_low_guard_corner` | 0 | 1 | a57=4 D61=11 chart=`dT2,dCh` |
