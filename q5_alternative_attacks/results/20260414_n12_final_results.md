# N=12 MSB Cascade DP — FINAL RESULTS

Candidate: M[0]=0x22b, fill=0xfff, MSB kernel (bit 11)
Runtime: 43h17m on 8 NEON cores (Apple M3)
Search space: 2^48 = 281 trillion configurations

## Final Count: 3671 collisions (log2 = 11.84)

This is 65% above the MSB scaling prediction of ~2221 (log2=11.12).
Candidate 0x22b is exceptionally collision-rich.

## Carry Automaton Analysis (complete dataset)
- Invariance: 40.0% (235/588 carry-diff bits) — matches universal ~42%
- T1-path freedom: 84.8%
- T2-path freedom: 27.0%
- Branching: 3 at bit 0, deterministic elsewhere
- All structural properties confirmed at N=12

## Scaling Law Update
| N | MSB coll | log2 |
|---|---------|------|
| 4 | 49 | 5.61 |
| 6 | 50 | 5.64 |
| 8 | 260 | 8.02 |
| 10 | 946 | 9.89 |
| **12** | **3671** | **11.84** |

MSB fit: log2(C) = 0.78*N + 2.5 (updated with N=12 data point)

Evidence level: VERIFIED (exhaustive cascade DP, 43h NEON)
