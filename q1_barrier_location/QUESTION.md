# Q1: Where Is the Collision Barrier?

## The Question
At what round of SHA-256 does collision become impossible, and does
the answer depend on the candidate family or is it fundamental?

## What We Know
- sr=59 (round 59): SAT — collisions exist (Viragh 2026, independently reproduced)
- sr=60 (round 60): UNSAT for 4 known MSB-kernel candidates at N=32
- sr=60 at reduced word widths: SAT at N=8 through N=21 (every non-degenerate N tested)
- Scaling fit: T ≈ 0.87 * 1.47^N (extrapolates to ~21h for N=32, but non-monotonic)

## Open Questions
1. Is there a sharp transition between "SAT word widths" and "UNSAT word widths"?
2. Does the transition depend on the candidate, or does every candidate become UNSAT above some N?
3. Can we reach N=32 SAT with enough compute + the right candidate?

## Strategy
Push the precision homotopy frontier as far as possible. Each new data point
either strengthens the "no fundamental barrier" hypothesis or finds the transition.

Use parallel candidate search (multiple candidates per N, first SAT wins) to
exploit the non-monotonic scaling.

## Key Tools
- `./fast_scan N 10 | python3 89_fast_parallel_solve.py N timeout`
- `python3 82_extract_mini_collision.py` for differential extraction
- `python3 85_scaling_analysis.py` for trend fitting

## See Also
- Issue #1 on GitHub
- `q2_bottleneck_anatomy/` for WHY the barrier exists
