# Programmatic SAT for sr=60: Implementation Plan

## Source
Alamgir et al. "SHA-256 Collision Attack with Programmatic SAT" (arXiv 2406.20072)
Code: https://github.com/nahiyan/cadical-sha256

## Result in Paper
- Plain CaDiCaL: 28-step SFS max
- Programmatic CaDiCaL: 38-step SFS (10-step improvement!)

## What It Does
Three IPASIR-UP callbacks inject SHA-256 domain knowledge into CaDiCaL:

1. **Bitsliced propagation**: For each modular addition, derive 2-bit
   XOR conditions from partial assignments. Catches deductions BCP misses.
   Uses LRU cache for repeated patterns.

2. **Inconsistency blocking**: Build graph of 2-bit equality/inequality
   conditions. BFS detects odd-length cycles = algebraic contradictions.
   Feed blocking clause to CaDiCaL → immediate backtracking.

3. **Wordwise propagation**: δA + δB = δC (mod 2^32). Split at carry
   boundaries, brute-force subproblems ≤10 variables.

## Why It Matters for Us
Our sr=60 problem has the SAME structure — differential constraints on
SHA-256 state variables with modular addition. The carry-chain confusion
that makes our instances hard (the "branching points" from DEEP_ANALYSIS.md)
is exactly what bitsliced propagation catches.

## Integration Path

### Option A: Adapt Our Encoding to Nejati's Format (recommended)
The CaDiCaL-SHA256 expects Nejati's collision encoder format with specific
variable naming conventions (A, E, W, sigma0, sigma1, Maj, Ch, carries).
Our CNFBuilder uses a different structure.

Steps:
1. Study Nejati's encoder: https://github.com/nahiyan/cryptanalysis/tree/master/encoders/nejati-collision
2. Build a new encoder in lib/ that produces Nejati-compatible DIMACS
3. Set IS_1BIT=true in types.hpp, enable CUSTOM_PROP and CUSTOM_BLOCKING
4. Build and test on sr=59 first (should be fast)
5. Run on sr=60

Estimated effort: 1-2 days

### Option B: Adapt CaDiCaL-SHA256 to Our Encoding
Modify the state.cpp parser to understand our variable mapping.
Our variables are ordered differently from Nejati's.

Estimated effort: 2-3 days

### Option C: IPASIR-UP from Scratch
Write our own CaDiCaL user propagator using the IPASIR-UP interface.
Already started in q5_alternative_attacks/forward_propagator.cpp.
The Q5 experiment with this approach timed out — likely needs the
2-bit inconsistency detection that we haven't implemented.

Estimated effort: 3-5 days

## Priority
This is the HIGHEST PRIORITY next step after the homotopy results.
A 10-step improvement maps to potentially orders of magnitude speedup
on our instances. At N=32, this could be the difference between
TIMEOUT and SAT.

## Cloned Repository
/tmp/cadical-sha256/ — built CaDiCaL with SHA-256 routines.
Needs IS_1BIT=true in types.hpp to compile with operation definitions.
