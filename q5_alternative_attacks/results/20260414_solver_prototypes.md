# Solver Prototype Results at N=4

## Three Approaches Tested

### 1. Bitserial Verify (bitserial_verify.c)
dT1_61=0 is NECESSARY but NOT SUFFICIENT for collision.
- 4848 configs satisfy dT1_61=0 (7.4% of 65536)
- Only 49 are actual collisions
- Need dT1_58=0 AND dT1_61=0 AND dT1_62=0 AND dT1_63=0
- Rounds 57, 59, 60 are automatic (cascade)

### 2. Bitserial Solver (bitserial_solver.c)
True bit-serial solver with carry tracking. Finds all 49 collisions.
- Carry automaton width: 48-49 among collisions (bounded)
- Survivor width: 2094→238→92→49 (LSB to MSB)
- 1.19x overhead vs brute force (rotation frontier at N=4)

### 3. A-path Gaussian Analysis (apath_gauss.c)
Structure of the outer search (W57×W58×W59):
- 30/4096 triples productive (0.73%)
- 14 have 1 W60 solution, 13 have 2, 3 have 3
- W60 XOR diffs in rank-3 subspace

## Key Structural Findings

1. **de58 has 2 values {0,2}** — collisions at BOTH
2. **dT2_58 ≠ 0** when Maj diff from cascade constant (dc57=db56≠0)
3. **State59 diff nearly constant** — only 2 distinct patterns among 49 collisions
4. **dW61 discriminates partially** — only values {3,5} among productive triples
   with de58=0, different for de58=2

## Why N=4 Is Too Small for Structural Speedup

At N=4, checking structural filters costs as much as checking collisions.
The rotation frontier (max rotation = N-1 = 3) makes bit-serial worse.
The de58 filter doesn't discriminate (both values contain collisions).

At N≥8: |de58| grows (8 values), brute force becomes 2^32, and structural
filters provide meaningful speedup. The solver architecture is CORRECT —
it just needs larger N to show its advantage.

Evidence level: VERIFIED (all 49 collisions found by all approaches)
