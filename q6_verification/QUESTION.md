# Q6: Are Our Results Correct?

## The Question
How confident should we be in our UNSAT claims, collision certificates,
and experimental findings? What's the gap between "solver said so" and
"independently verified proof"?

## What We Know
- sr=59 collision: verified by native computation (VERIFIED)
- sr=60 UNSAT partitions: 29/32 have Kissat UNSAT + DRAT proof + CaDiCaL confirmation
- 3 partitions timeout across all solvers and seeds
- CryptoMiniSat mostly times out (not useful for cross-validation here)
- The encoder has a latent Ch operator precedence bug (fixed in archive scripts)
- Script 41 code doesn't match the writeup's partition description

## Verification Gaps
1. Only 32/1024 partitions sampled — need complete coverage
2. No end-to-end proof chain documented
3. Encoder correctness: no unit test verifying known non-collisions produce UNSAT
4. Round-counting ambiguity between C scanners and SAT encoder not resolved

## Strategy
1. Generate DRAT proofs for ALL UNSAT partition cells (not just sampled)
2. Cross-validate with CaDiCaL on all cells
3. Write encoder unit tests: feed a known sr=59 collision, verify SAT + correct assignment
4. Resolve the round-counting convention: C scanners count from 0, SAT encoder from 57
5. Document the complete proof chain in a claim file

## Key Tools
- `76_partition_verifier.py` (archive/) — cross-solver + DRAT pipeline
- `lib/solver.py` — new unified solver interface
- drat-trim in `infra/drat-trim/` (or `sha256_scripts/tools/drat-trim/`)

## See Also
- Issue #6 on GitHub
- CLAIMS.md for current evidence levels
