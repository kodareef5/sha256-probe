# Q5: What If SAT Isn't the Right Tool?

## The Question
The entire campaign has used SAT solvers. Standard SHA-256 cryptanalysis uses
very different techniques (Wang modification, MILP trails, algebraic attacks).
Do any of these apply here?

## What We Know
- Wang-style message modification: the dominant SHA collision technique since 2005.
  Never applied to this problem. Directly applicable to 7 rounds with 4 free words.
- MILP-based differential trail optimization: state of the art (Li et al., EUROCRYPT 2024).
  Cited in the original work but never used.
- Groebner bases / XL algorithm: "full algebraic degree at dim 15" doesn't preclude
  structure at dim 128+.
- Multi-block attacks: Merkle-Damgard allows a second compression block to correct
  residual differences. Never explored.
- SAT preprocessing (SatELite, BVE, Vivification): could bridge the constant-folding
  gap without manual partitioning.

## Open Questions
1. Can Wang-style modification extend the sr=59 trail to sr=60?
2. Does MILP find alternative differential paths (the current trail is provably
   incompatible at sr=60)?
3. Can a second message block correct the sr=60 residual?
4. What's the algebraic degree of the collision system at full 32-bit width?

## Strategy
These are the highest-information experiments not yet attempted:
1. Wang modification: use sr=59 free words as starting point, apply bit-position
   modification rules to satisfy the additional round constraints
2. MILP: set up a mixed-integer model for the differential trail (requires MILP solver)
3. Multi-block: construct M' where the second block's freedom can absorb the residual
4. Preprocessing: run SatELite/Vivification on the raw sr=60 CNF before Kissat

## Key Tools (to build)
- `78_wang_differential_analysis.py` (archive/) is a starting point for Wang analysis
- MILP model requires a solver (Gurobi, CPLEX, or open-source SCIP/HiGHS)
- Multi-block encoder extends lib/cnf_encoder.py to two compression blocks

## See Also
- Issue #5 on GitHub
- These are standard techniques — any SHA-256 cryptanalysis textbook covers them
