# Structural Analysis of SHA-256 Cascade Collisions:
# From sr=60 to the Polynomial Complexity Boundary

## Abstract

We present a systematic structural analysis of semi-free-start collisions
in reduced-round SHA-256, extending the cascade differential path construction
from round 59 (Viragh 2026) to round 60 (93.75% of 64 rounds). Our analysis
establishes:

(1) An explicit sr=60 collision certificate for full 32-bit SHA-256
    with M[0]=0x17149975, verified via Kissat and cross-checked with
    CaDiCaL and native computation.

(2) A complete structural theory of the cascade collision mechanism,
    comprising six interlocking theorems: the cascade diagonal, the free
    e-path cascade (de60=0), the three-filter equivalence, the da=de
    identity at rounds 61+, the sr=61 cascade break, and the 3x
    algorithmic ceiling for differential approaches.

(3) The collision function's Binary Decision Diagram has polynomial size
    O(N^4.8) in the word width N (verified N=2..12), establishing that
    the collision function has polynomial structural complexity despite
    the exponential search space.

(4) The carry automaton of the collision function exhibits bounded width
    equal to the collision count at every bit position, with deterministic
    transitions (permutation property) verified at N=4,6,8,10,12. However,
    the carry state space for the full input space is nearly injective
    (89-99% of 2^{4N}), ruling out carry-state dynamic programming as a
    search algorithm.

(5) A structural proof that the sr=60/61 boundary arises from schedule
    compatibility: each additional schedule-determined round adds a 2^N
    penalty, exactly cancelling the cascade's computational advantage.

## 1. Introduction

### 1.1 Background
- SHA-256 structure, compression function, message schedule
- Prior work: Wang et al. (SHA-1), Viragh 2026 (sr=59 for SHA-256)
- Semi-free-start collisions and their significance

### 1.2 The Cascade Construction
- Differential path: dM[0]=dM[9]=2^{bit}
- Cascade offset: W2[r] = W1[r] + f(state1, state2)
- Forces da=0 at each round through the free-word region

### 1.3 Contributions
- Enumerate contributions (1)-(5) from abstract
- Mini-SHA-256 parametric framework for systematic study

## 2. Preliminaries

### 2.1 Mini-SHA-256(N)
- Scaled rotations: SR(k) = max(1, round(k*N/32))
- Truncated constants: K_N[i] = K[i] mod 2^N
- Valid for systematic parameterization of word width

### 2.2 The Cascade DP Algorithm
- Precomputation through round 56
- Free message words W[57]..W[60]
- Cascade offset computation per round
- Schedule determination of W[61], W[62], W[63]

## 3. Structural Theory

### 3.1 The Cascade Diagonal (Theorem 1)
- Two zero-waves in the state-diff matrix
- One variable diagonal (de58)

### 3.2 The Free e-path Cascade: de60=0 (Theorem 2)
- Proof via shift register propagation
- Unconditional: holds for ALL message word combinations

### 3.3 Three-Filter Equivalence (Theorem 3)
- de61=de62=de63=0 ⟺ full collision
- Reduces 8-register check to 3 e-register checks

### 3.4 The da=de Identity (Theorem 4)
- da_r = de_r for r ≥ 61
- Proof: dT2=0 from cascade structure

### 3.5 The Cascade Break at sr=61 (Theorem 5)
- P(cascade compatible with schedule) = 2^{-N}
- 16-bit mismatch at N=32

### 3.6 The 3x Algorithmic Ceiling (Theorem 6)
- Cascade permissiveness eliminates all differential constraints
  during free rounds
- Only schedule-determined rounds provide pruning
- Verified across 5 independent implementations

## 4. BDD Polynomial Complexity

### 4.1 Truth-Table BDD Construction
- Interleaved variable ordering
- Bottom-up construction in groups of 4 variables
- Verified at N=2..8 (truth table), N=9 (streaming), N=10,12 (collision-list)

### 4.2 Scaling Analysis
- 10 data points: nodes ≈ 0.38 × N^4.82 (R²=0.93)
- N=12: 92,975 nodes for a 35TB truth table (3B× compression)
- Per-variable node distribution: bell curve reflecting carry chain structure

### 4.3 Construction Complexity Gap
- Incremental BDD (Apply): exponential intermediate blowup
- Streaming BDD: O(2^{3N}) per slice, first construction at N=9
- Collision-list BDD: O(#collisions × N × BDD_size) — practical for any N
- Open: polynomial-time BDD construction

## 5. Carry Automaton Structure

### 5.1 Carry State Extraction
- 49 carry bits per bit position (7 rounds × 7 additions)
- Carry-diff between paths: 49 bits

### 5.2 Bounded Width and Permutation Property
- Width = collision count at every bit position
- Deterministic transitions (branching ≤ 2, typically 1)
- 42% carry-diff invariance (structural, kernel-independent)

### 5.3 Carry-State DP: A Negative Result
- State width for ALL inputs: 89-99% of 2^{4N} (near-injective)
- Root cause: rotation frontier (Sigma functions spread information)
- Carry DP provides zero algorithmic speedup

## 6. The sr=60/61 Boundary

### 6.1 Structural Proof
- Each schedule-determined round: 2^N penalty
- sr=61 via cascade: O(2^{4N}) = same as no cascade

### 6.2 Critical W[60] Pairs
- N=6: pairs (1,3) and (2,5) are critical
- N=8: pair (4,5) is the unique critical pair
- N=10: [scan in progress]
- N=32: 16-bit mismatch, no 2-bit pair can repair

### 6.3 Collision Scaling
- Complete data N=4..12 for MSB and non-MSB kernels
- N mod 4 scaling classes
- Alternating fill amplification at odd N

## 7. Alternative Attack Paths

### 7.1 FACE Algorithm (GF(2) Mode-Branching)
- 128x branch reduction at N=8 (33.4M vs 4.3B)
- 20x GF(2) overhead per branch → net 2.4x slower
- Cascade permissiveness kills symbolic advantage

### 7.2 Multi-Block Attack
- Near-collision residuals: da=de structure
- N=8 minimum HW=7 (out of 64 bits) — too large for block-2 differential

### 7.3 SAT Solver Landscape
- Kissat 4.0.4: 12h for sr=60 at N=32
- CSA-tree vs sequential encoding: ~1.4x difference
- sr=61 at N=32: >50h timeout

## 8. Discussion

### 8.1 The Polynomial Structure Paradox
- The collision function has O(N^4.8) BDD complexity
- But constructing this BDD requires O(2^{4N}) work
- The polynomial structure EXISTS but cannot be efficiently EXPLOITED

### 8.2 Implications for SHA-256 Security
- sr=60 extends the previous best by one round
- The cascade construction has a structural limit at sr=60/61
- Alternative approaches (non-cascade, multi-block) face different barriers

### 8.3 Open Problems
- Polynomial-time BDD construction
- sr=61 via non-cascade methods
- Full SHA-256 (64 rounds) remains secure

## 9. Conclusion

## References

## Appendix A: Collision Certificate
## Appendix B: Mini-SHA-256 Specification
## Appendix C: Complete Collision Count Data (N=2..12)
