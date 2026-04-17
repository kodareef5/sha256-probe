# The Transducer Framework: Unified View of Cascade Collisions

**Date**: 2026-04-16
**Status**: HYPOTHESIS — theoretical framework connecting empirical findings

## The Unified Object

The SHA-256 cascade collision problem can be formulated as:

> Find all input strings accepted by a **finite-state transducer** T
> that processes N-bit words bit-by-bit (LSB→MSB).

Specifically:
- **Input alphabet**: Σ = {0,1}^8 (4 words × 2 messages × 1 bit per position)
- **State space**: C = carry states from all 49 additions (7 rounds × 7 adds)
- **Transition**: T(C[k], σ[k]) → C[k+1] (deterministic)
- **Accept**: collision predicate on final state C[N-1]

## How Each Finding Maps to the Transducer

| Finding | Transducer interpretation |
|---------|--------------------------|
| **Carry entropy theorem** (rank ≈ N) | The accepting paths of T number ~2^N |
| **BDD polynomial scaling** (N^4.94) | The accepting language of T has an OBDD of polynomial size |
| **Cascade tree linearity** (ratio 1.04) | The forward search tree of T has branching factor ~1 |
| **42% carry-diff invariance** | 42% of the state bits in T are redundant (determined by structure) |
| **Carry DP negative result** | The full state space of T is O(2^{4N}) (exponential) |
| **Permutation property** | T is a **permutation transducer** on the accepting set: each accepting path has a unique state sequence |

## The Central Question

T has **exponential state space** (2^{4N}) but **polynomial-size accepting language** (N^4.94 OBDD nodes).

In formal language theory: DFA minimization can reduce the state count to
the language's syntactic monoid size. For our language, this might be polynomial.

> **Open Question**: Does the minimal DFA for the cascade collision language
> have polynomial or exponential state count?

If **polynomial**: cascade collision finding is in P (via DFA minimization + enumeration).
If **exponential**: the polynomial BDD is an accident of OBDD variable ordering, not structural.

## Why the State Space Explodes: The Rotation Frontier

Without Sigma rotations, the transducer would process each bit position
independently — carry bits at position k depend only on positions 0..k-1.
The state space would be bounded by the carry width (~49 carries × 2 messages ≈ 98 bits).

Sigma rotations (ROTR by 2, 6, 7, 10, 11, 13, 17, 18, 19, 22, 25)
create CIRCULAR DEPENDENCIES:
- Bit k of Sigma1(e) = e[k+6] XOR e[k+11] XOR e[k+25] (mod N)
- Processing bit k requires knowing bits k+6, k+11, k+25
- These bits haven't been computed yet in the LSB→MSB pass

The transducer resolves this by storing the FULL register values in the
state (not just carries), inflating the state space from 2^98 to 2^{8N+98}.

## Three Paths to Polynomial Time

### Path 1: Variable Ordering
Find an OBDD variable ordering where the rotated bits are adjacent.
The current interleaved bit-first ordering achieves N^4.94 nodes.
An ordering aligned with rotation orbits might reduce this further.

### Path 2: Symbolic Carry Propagation
Express the carry transitions symbolically (ANF/polynomial). If the
symbolic transition function has bounded degree in carry variables,
Gaussian elimination solves each bit position in polynomial time.

**Obstacle**: The ANF is degree-N in message variables (from the
polynomial analysis). Carry variables have narrower support but
the rotations couple all positions.

### Path 3: Direct Minimal DFA Construction
Build the minimal DFA without first constructing the full transducer.
Myhill-Nerode equivalence classes can sometimes be computed from the
STRUCTURE of the transition function, not the full state table.

For SHA-256: the Sigma/Ch/Maj/addition operations are all "algebraically
nice" (bitwise Boolean or modular arithmetic). The composition of
algebraically nice functions might yield algebraically nice equivalence
classes.

**Obstacle**: The composition of rotations with modular addition is
the core of SHA-256's diffusion. If the minimal DFA were easily
constructable, SHA-256 would be weak.

## Connection to SAT Solving

The 11 Kissat seeds racing on N=32 sr=61 are exploring the transducer's
state space via CDCL search. The cascade-augmented encoding (192 extra
clauses) provides the solver with information about the transducer's
structure (da=0 at intermediate rounds).

The carry-conditioned SAT approach would expose the transducer's carry
states as branching variables, aligning VSIDS heuristics with the
transducer's transition structure.

## What This Means for sr=61

The sr=61 constraint adds: W[60] = sigma1(W[58]) + const.
In transducer terms: the input alphabet at the W[60] position is
REDUCED from {0,1} to a function of earlier inputs.

This constraint reduces the language to a SUB-LANGUAGE. The sub-language
may have:
(a) Zero accepting paths (sr=61 is UNSAT for this candidate)
(b) A few accepting paths (sr=61 is SAT but hard to find)
(c) Many accepting paths (sr=61 is SAT and the solver should find one)

From the carry impossibility result (N=4): 0/49 sr=60 collisions satisfy
sr=61. This suggests the sub-language is MUCH smaller than the sr=60 language.
The cascade break probability 2^{-N} gives ~1 expected accepting path at N=32.

## Evidence Level

This framework is a HYPOTHESIS — it unifies empirical findings but makes
no new testable predictions beyond what the individual results already imply.

The key open question (polynomial vs exponential minimal DFA) is a
THEORETICAL problem that may not be resolvable empirically at feasible N.
