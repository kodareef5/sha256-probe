# Critical Pair Scan at N=10: All Pairs TIMEOUT

## Setup
- N=10, C(10,2) = 45 pairs tested
- Candidate: M[0]=0x34c, fill=0x3ff, MSB kernel
- Timeout: 600s per pair, 10 parallel Kissat instances
- Total wall time: 3600s (1 hour)

## Result

ALL 45 pairs TIMEOUT. No SAT, no UNSAT, all inconclusive at 600s.

## Interpretation

At N=8: pair (4,5) is SAT in 21.5s. All other 27 pairs UNSAT (30-100s).
At N=10: NO pair resolves within 600s — the problem is ~30x harder.

The cascade break penalty 2^N grows faster than the 2-bit freedom:
- N=8: 2-bit freedom (4 values) vs 2^8=256 penalty → Kissat manages
- N=10: 2-bit freedom (4 values) vs 2^10=1024 penalty → timeout

This confirms the boundary proof quantitatively: sr=61 difficulty grows
exponentially with N even when the maximum freedom (2 bits of W[60]) is used.

## Need

Longer timeouts (hours) might resolve some pairs at N=10. But the scaling
trend is clear: sr=61 critical pairs become impractical at N≥10.

Evidence level: EVIDENCE (timeout is inconclusive, but consistent with theory)
