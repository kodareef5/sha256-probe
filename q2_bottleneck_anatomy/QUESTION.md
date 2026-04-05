# Q2: Why Does the Barrier Exist?

## The Question
What structural feature of SHA-256 makes sr=60 hard? Is it the schedule
coupling (W[61] determined by W[59]), the carry chain depth, the algebraic
degree, or something deeper?

## What We Know
- The sr=59 collision zeros one a-register per free round (da, db, dc, dd, de)
- At sr=60, W[61] is schedule-determined and introduces dW[61] with high hamming weight
- dW[61] HW correlates with solvability: 3-8 for SAT instances, 17 for known UNSAT
- The "constant C" (candidate-dependent part of dW[61]) has HW ~15-16 for all known N=32 candidates
- SA cannot navigate this landscape — only CDCL SAT solvers succeed

## Open Questions
1. Is dW[61] HW causal or just a correlate?
2. Can we construct candidates where C (the constant part) is small?
3. Is the carry chain depth the fundamental obstruction, or would a XOR-only SHA also be hard?
4. Does the MITM hard residue (g60/h60) explain the barrier better than dW[61]?

## Strategy
Build testable hypotheses and falsify them:
- Force low dW[61] via W[59] constraints: does it make sr=60 easier?
- Test the XOR-SHA variant: is carry arithmetic the barrier?
- Compare dW[61] vs MITM-anchor metrics as predictors across word widths

## Key Tools
- `78_wang_differential_analysis.py` (round-by-round differential trace)
- `83_dw61_compatibility.py` (constant C analysis)

## See Also
- Issue #2 on GitHub
- `q1_barrier_location/` for empirical data
- `q4_mitm_geometry/` for the alternative bottleneck view
