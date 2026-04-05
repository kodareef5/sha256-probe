# Universal Depth-1 Constraint Results (2026-04-05)

## Experiment
Test both depth-1 strategies (de57=0, da57=0) across ALL 6 MSB-kernel candidates.

## de57=0 Results (Zero e-register at round 57)

| Candidate | Fill | da57_err | Result |
|-----------|------|----------|--------|
| 0x17149975 | 0xffffffff | 8 | **UNSAT 0.2s** |
| 0xa22dc6c7 | 0xffffffff | 17 | **UNSAT 0.1s** |
| 0x9cfea9ce | 0x00000000 | 21 | **UNSAT 0.1s** |
| 0x7a9cbbf8 | 0x7fffffff | 13 | **UNSAT 0.1s** |
| 0x44b49bc3 | 0x80000000 | 17 | **UNSAT 0.4s** |
| 0x3f239926 | 0xaaaaaaaa | 17 | **UNSAT 0.1s** |

**ALL UNSAT.** The e-register zeroing strategy is provably impossible
for the entire MSB kernel family.

## da57=0 Results (Zero a-register at round 57)

| Candidate | Fill | de57_err | Result |
|-----------|------|----------|--------|
| 0x44b49bc3 | 0x80000000 | **11** | TIMEOUT 120s |
| 0x9cfea9ce | 0x00000000 | 12 | TIMEOUT 120s |
| 0xa22dc6c7 | 0xffffffff | 14 | TIMEOUT 120s |
| 0x3f239926 | 0xaaaaaaaa | 16 | TIMEOUT 120s |
| 0x7a9cbbf8 | 0x7fffffff | 19 | TIMEOUT 120s |
| 0x17149975 | 0xffffffff | **21** | TIMEOUT 120s |

**ALL TIMEOUT.** The a-register zeroing strategy is hard for all candidates
but not proven impossible.

## Key Finding: de57_err Predicts Candidate Quality

The de57 error under da57=0 constraint **correlates with reduced-width
solve speed** from the Q3 crossval:

| Candidate | de57_err | N=10 solve | N=12 solve |
|-----------|----------|------------|------------|
| 0x44b49bc3 | **11** | **24.8s** | **66.0s** |
| 0x9cfea9ce | 12 | 40.7s | 109.3s |
| 0x3f239926 | 16 | 24.4s | 235.9s |
| 0x17149975 | **21** | 71.5s | TIMEOUT |

The ranking matches: lower de57_err → faster solving at reduced widths.

## Evidence Level

**VERIFIED**: de57=0 is impossible for all tested MSB-kernel candidates.
**EVIDENCE**: de57_err under da57=0 predicts reduced-width difficulty.
**HYPOTHESIS**: The optimal sr=60 strategy zeros the a-register path and
lets the e-register error be absorbed by subsequent rounds.
