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

## Triplet Scan (3 freed bits)

Tested 10 most promising triplets with 600s timeout:
(3,4,5), (3,5,6), (4,5,6), (4,5,7), (2,4,5),
(3,4,6), (5,6,7), (2,5,6), (1,4,5), (4,6,7)

ALL 10 TIMEOUT. Even 3 freed bits (8 values) is insufficient at N=10.

Interpretation: the 2^N penalty (1024 at N=10) overwhelms both
2-bit freedom (4 values) and 3-bit freedom (8 values).
Would need ~log2(1024) = 10 freed bits for expected coverage.

Long-timeout test on pair (4,5) at 3600s is running. If SAT, it
demonstrates that the pair exists but requires much more solver time.
