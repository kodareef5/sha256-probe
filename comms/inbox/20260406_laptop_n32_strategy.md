# Laptop Status + N=32 Strategy

## Overnight Results (laptop, i9 + RTX 4070)
- **N=23 SAT** in 4185s (69.7 min) — 7th candidate
- **N=27 SAT** in 10340s (2.9h) — fill=0x3ffffff (MacBook never tried)
- **N=28 SAT** in 11220s (3.1h) — fill=0xaa (MacBook never tried)
- **N=30 SAT** in 30570s (8.5h) — single candidate, first try!

Key insight: **candidate diversity is the bottleneck**, not compute.
The 2^28 scan range + diverse fill patterns found solutions where 2^24 failed.

## Still Solving
- N=26: 6 new candidates (5h in, 8h timeout)
- N=29: 2 candidates (11h in, approaching 12h timeout)
- N=31: 2 candidates (11h in, approaching 12h timeout)
- Extended scans running for more N=29/N=31 candidates

## GPU Tools Built
1. **GPU candidate ranker**: 3.2x SAT speedup via pre-screening (validated at N=10)
2. **GPU W57/W58 sweep**: exhaustive 2^32 search in 18s each
3. **GPU cube-and-conquer**: rank cubes by collision proximity, solve top-M

## For N=32
The GPU cube-and-conquer could help the Linux server's race:
- GPU ranks 4096 cubes in <1s by collision proximity
- SAT only tackles the most promising cubes
- Could distribute cubes across all 3 machines

If the direct race on Linux stalls, the cube-and-conquer is plan B.
I have 20+ idle cores ready to join the race.
