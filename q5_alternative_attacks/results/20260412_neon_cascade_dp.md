# NEON Cascade DP Results — 2026-04-12

## Tool: cascade_dp_neon.c

ARM NEON uint16x8_t vectorized inner loop (8 W1[60] values per vector)
+ OpenMP over W1[57]. Apple Silicon M3 Pro.

## Results

| N | Collisions | Time | Throughput | Verification |
|---|-----------|------|-----------|-------------|
| 8 | **260** | 2.1s | 2.00e9/s | Matches cascade_dp_generic |
| 10 | **946** | 562s (9.4 min) | 1.96e9/s | Matches cascade_dp_generic |

## Scaling

At 2 billion configs/sec with 8 threads:
- N=12: 2^48 / 2e9 = 140,000s = **39 hours** (feasible overnight)
- N=14: 2^56 / 2e9 = 3.6e7s = **415 days** (infeasible without algorithmic improvement)

## Carry-diff Structure (N=8)

Carry-diff matrix: 260 × 343
- Invariant bits: 147/343 (42.9%)
- GF(2) rank: 193
- Real SVD rank: 194
- Matches GPU laptop finding of ~39.4% invariant

## Schedule-diff Pruning: REFUTED

Tested: dW[61]=0 as necessary condition for collision (since g63=e61).
Result: INCORRECT — cascade only zeroes a-path (a,b,c,d). e-path diffs
(f60,g60,h60) persist from state56 and compensate through nonlinear
mixing in rounds 61-63. All 260 collisions have dW[61]≠0.

## Key Insight

After 4 cascade rounds (57-60):
- da=db=dc=dd=de = 0 (fully zeroed)
- df=de59, dg=de58, dh=de57 (NONZERO, from state56 propagation)
- These e-path diffs are resolved by schedule diffs in rounds 61-63
- No intermediate pruning possible (confirms Rotation Frontier)
