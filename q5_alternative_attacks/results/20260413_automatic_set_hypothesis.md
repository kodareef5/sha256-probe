# The Automatic Set Hypothesis

## Thesis

The set of sr=60 collision-producing carry sequences forms an **automatic set**
over a finite carry alphabet. This implies the collision finder runs in
O(N × C × B) time, where C is the collision count and B the branching factor.

## Evidence

### 1. Bounded Width (Finite Automaton Property)
The carry automaton has width = C at every bit position.
- N=8: width = 260 at all 8 bits
- N=10: width = 946 (±2 at edge bits)
- N=12: width = 610+ (partial)

This is the defining property of a finite automaton: bounded state count.

### 2. Deterministic Transitions
Carry-state transitions from bit k to bit k+1 are deterministic
(branching factor ≤ 2, only at edge bits). The automaton is essentially
a permutation at each level.

### 3. Regular Invariance
42% of carry-diff bits are invariant across ALL collisions, regardless
of N or kernel choice. This regularity is a hallmark of automatic relations.

### 4. GF(2) Affine Structure
The collision variety lies in a 224-dimensional GF(2) affine subspace
(168 carry constraints at N=8). The affine structure is preserved by
the automaton transitions.

### 5. Bounded Cross-Track Dependencies
The rotation frontier creates cross-bit dependencies, but the rotation
amounts are FIXED (2, 6, 7, 11, 13, 17, 18, 19, 22, 25 in full SHA-256).
These create a bounded-width "window" of cross-track coupling.

## Implications

### Complexity
- Brute force: O(2^{4N}) = O(2^{128}) at N=32
- Automatic set approach: O(N × C × B) = O(32 × 2^{28} × 2) = O(2^{34}) at N=32
- Speedup: ~2^{94} ≈ 10^{28}

### Algorithm Sketch
1. Initialize: set carry state at bit 0 from the cascade constraint
2. For each bit k = 0 to N-1:
   a. For each reachable carry state:
     - Enumerate valid input bits (4 message bits, bounded by rotation window)
     - Compute carry transitions
     - Check output-diff constraint at bit k
   b. Merge equivalent carry states (deduplicate)
3. Extract message words from surviving paths

### The Rotation Window
At bit k, the rotation inputs are at positions (k+r) mod N for each rotation
amount r. The maximum look-ahead is max(r) = 25. This creates a "rotation
window" of width 25, within which all cross-bit dependencies are resolved.

For bit-serial processing, we'd need to maintain a 25-bit look-ahead buffer.
At each step, 4 new message bits enter and 4 old bits exit the window.
The buffer state has at most 2^{4×25} = 2^{100} possible values — still
exponential, but much less than 2^{128}.

With the carry automaton's width bound (C ≈ 2^{28} at N=32), the REACHABLE
buffer states are far fewer: at most C × (rotation window combinations).

### What's Needed
1. **Formal proof** that the collision set is automatic (not just evidence)
2. **Efficient automaton construction** that doesn't require knowing all
   collisions first (use structural constraints instead)
3. **Rotation window optimization** to minimize the look-ahead buffer

### Connection to Known Results
- In formal language theory: automatic sets over multi-track alphabets
  are decidable and have polynomial-time membership testing
- The carry propagation is a specific type of FINITE-STATE TRANSDUCER
- The collision constraint is a SYNCHRONOUS relation between input and
  output tracks of the transducer

## Limitations
- The width C grows exponentially with N (C ≈ 2^{0.87N}), so the total
  complexity O(N×C) is sub-exponential but not truly polynomial in N.
- The rotation window creates a constant factor of 2^{~100} in the worst
  case, which may dominate at practical N values.
- Building the automaton incrementally (without full collision enumeration)
  requires the structural constraints to be sufficient — not yet proven.

## Status
HYPOTHESIS — supported by extensive empirical evidence at N=4-12,
consistent with formal automata theory, but not formally proven.
The key open question is whether the rotation window can be handled
without exponential blowup.
