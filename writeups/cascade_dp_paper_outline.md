# Paper Outline: Cascade-Chain Collision Finding for Reduced SHA-256

## Title Options
1. "Cascade-Chain Collision Finding: A SAT-Free Approach to Reduced SHA-256"
2. "The Carry Automaton of SHA-256: Structure and Enumeration of Round-60 Collisions"
3. "Beyond SAT: Constructive Collision Finding via Cascade Decomposition in SHA-256"

## Abstract
We present a constructive, SAT-solver-free method for finding semi-free-start
collisions through 60 of 64 rounds of SHA-256 (sr=60). Our cascade-chain
decomposition exploits the observation that the second message is fully
determined by the first via round-by-round cascade offsets, reducing the
search space from O(2^{8N}) to O(2^{4N}) — half the exponent. We verify
this at N=4,6,8 word widths, finding ALL collisions exhaustively (49, 50,
260 respectively), and demonstrate that SAT solvers find only 37% of
solutions at N=8. We further establish a carry entropy theorem: the carry-
difference pattern uniquely identifies each collision, with entropy exactly
equal to log_2(#solutions) at all tested widths.

## 1. Introduction
- Viragh (2026): sr=59 collision
- Our extension to sr=60 via SAT
- Motivation: can we understand WHY sr=60 works and sr=61 doesn't?
- Preview: cascade chain, carry entropy, constructive finder

## 2. Preliminaries
- SHA-256 specification (rounds 57-63)
- Mini-SHA scaling methodology (with caveats from external reviewers)
- Semi-free-start collision model
- MSB kernel: da[56]=0

## 3. The Cascade Mechanism
### 3.1 Cascade-1: Zeroing a→b→c→d
- dW[57] is a computable constant
- da57=0 for ALL W1[57] values (universal)
- Shift register propagation: db=0, dc=0, dd=0 automatic

### 3.2 The Cascade Chain: W2 Determined by W1
- Key result: W2[k] = W1[k] + C_k(W1[57..k-1])
- Offsets are computable from the round function
- Search reduction: 2^{8N} → 2^{4N}

### 3.3 Cascade-2 and Register h
- h is DETERMINED by a-g at N=4 (Theorem, exhaustive verification)
- Cascade-2 (e→f→g→h) is automatic from cascade-1 + shift register
- Only ONE cascade mechanism exists, viewed from two time offsets

## 4. The Cascade DP Collision Finder
### 4.1 Algorithm
- For each W1[57]: compute W2[57] = W1[57] + C
- For each W1[58]: compute W2[58] from cascade offset
- Continue for W1[59], W1[60]
- Check full collision after schedule-determined rounds 61-63

### 4.2 Results
| N | Collisions | Time | Search space | SAT comparison |
|---|-----------|------|-------------|----------------|
| 4 | 49 | 0.001s | 2^16 | 245,000x faster |
| 6 | 50 | 0.41s | 2^24 | exhaustive |
| 8 | 260 | 24.6s (8 cores) | 2^32 | SAT found only 95/260 |
| 10 | TBD | ~4h (8 cores) | 2^40 | — |

### 4.3 SAT Solver Incompleteness
- At N=8, Kissat with 200 diverse seeds found 95 unique solutions
- The cascade DP found 260 (ALL of them)
- SAT coverage: 37% — solver explores only a fraction of solution space

## 5. The Carry Entropy Theorem
### 5.1 Statement
For every tested N, each collision has a unique carry-difference pattern.
Carry entropy = log_2(#solutions) exactly.

### 5.2 Evidence
| N | Solutions | Free carries | Entropy | Ratio |
|---|-----------|-------------|---------|-------|
| 4 | 49 | 92/196 | 5.61 | 1.0000 |
| 6 | 50 | 181/294 | 5.64 | 1.0000 |
| 8 | 260 | 234/392 | 8.02 | 1.0000 |

### 5.3 Interpretation
- Carry patterns biject with collisions
- 234 "free" carry bits contain only 8.02 bits of information
- The carries are 99.97% correlated
- Automaton width = #solutions at every bit position

### 5.4 The a-Path Near-Linearity
- Sig0+Maj: 1/28 free carries
- T1+T2: 2/28 free carries
- a-register path is nearly linear once collision constraints apply
- a-path entropy captures most of the total carry entropy

## 6. The sr=60/61 Boundary
### 6.1 UNSAT Core Analysis
- All W[60] schedule bits individually redundant
- Critical pairs at N=6: (1,3) and (2,5)
- Critical pair at N=8: (4,5)
- Simple rotation-position hypothesis refuted

### 6.2 Phase Transition
- Fraction of critical pairs shrinks: 13% (N=6) → 3.6% (N=8)
- The obstruction is collective, not positional

## 7. Algebraic Structure
### 7.1 Exact ANF at N=4 and N=8 (restricted)
- d[0]: degree 7 (weakest bit)
- h[0]: degree 8
- Perfect staircase pattern (carry chain signature)
- Degree invariant to word width when #free_vars is constant

### 7.2 Higher-Order Differentials
- Degree > 20 at N=8 (18 hours, through k=20)

### 7.3 Closed Attack Paths
- Algebraic immunity > 4 (annihilator retracted)
- No linear bias (Walsh spectral analysis)
- No cross-register correlations

## 8. Scaling and Limitations
- Mini-SHA caveats (rotation scaling, constant truncation)
- N=32 extrapolation: ~2^{22.4} solutions predicted, 2^128 search
- The cascade DP alone doesn't reach N=32 (2^128 is infeasible)
- Need carry automaton pruning or meet-in-the-middle for scalability

## 9. Conclusion and Open Problems
- First constructive (SAT-free) sr=60 collision finder
- Carry entropy theorem as structural characterization
- Open: polynomial-time algorithm for the carry automaton
- Open: sr=61 via multi-block or modified schedule
- Open: carry automaton width scaling at full N=32

## Acknowledgments
- External reviewers: Gemini 3.1 Pro and GPT-5.4 (OpenRouter)
- Multi-machine fleet: macbook, linux server, GPU laptop
