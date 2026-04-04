# Verification Checklist for sr=60 UNSAT Claims

This checklist tracks the minimum steps needed to treat an UNSAT result as a proof-quality claim.

## Required
- Generate proof certificates for every UNSAT partition (Kissat `--proof` or equivalent).
- Verify proofs with an independent checker (e.g., `drat-trim`, `gratgen`, `veripb` as appropriate).
- Cross-solve a representative subset with another solver (e.g., CaDiCaL, CryptoMiniSat).
- Re-run a sample with varied random seeds and solver versions to detect instability.

## Strongly Recommended
- Store CNF + proof artifact hashes for reproducibility.
- Save solver logs (conflicts, decisions) for regression comparison.
- Confirm round indexing alignment across C scanners and SAT encoders.

## Nice to Have
- Run SAT preprocessing (SatELite, vivification) and compare outcomes.
- Track constant-folding statistics for each partition to detect anomalies.
