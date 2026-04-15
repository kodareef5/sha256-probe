# The Unified Mathematical Object: A Cascade Transducer

## What We Know

| Finding | Mathematical Form |
|---------|------------------|
| BDD polynomial O(N^4.8) | Collision function has compact canonical representation |
| Carry automaton bounded width | Collision states form permutation at each bit position |
| 42% carry-diff invariance | 42% of the transducer's output tape is deterministic |
| da=de identity | The a-path and e-path are algebraically coupled |
| de60=0 always | The e-path cascade is unconditionally free |
| 3x algorithmic ceiling | Cascade permissiveness prevents differential pruning |
| Carry DP = brute force | The transducer's state space is near-full for non-solutions |

## The Object

The collision function is a **finite-state transducer** T that maps:

  Input tape: (W57[0..N-1], W58[0..N-1], W59[0..N-1], W60[0..N-1])
  → Read one 4-bit symbol per bit position (interleaved)
  
  State: carry vector from all 49 additions (per path)
  
  Output: collision bit (0 or 1) after processing all N symbols

Properties of T:
1. **Polynomial BDD**: T's output function has O(N^4.8) BDD complexity
2. **Bounded width for accepting runs**: the set of accepting computations
   forms a width-K automaton where K = #collisions ≈ O(N)
3. **Near-full width for ALL runs**: the set of all computations fills
   the state space to ~90% capacity (near-injective)
4. **Rotation coupling**: T is NOT a standard finite automaton because
   the transition function at position b reads register values at
   positions b ± {rotations}, creating non-local dependencies

## Why It Can't Be a Standard Automaton

Standard finite automata process input symbols sequentially with a fixed
state transition function. T's transitions at position b depend on
register values at rotated positions (b+2, b+6, etc.) — future positions
that haven't been processed yet.

This makes T a **dependent transducer**: the transition at position b
requires information from positions b+1..b+max_rot. This is equivalent
to a sliding-window automaton with window size = max_rotation.

For N=8: window size = 6 (from Sigma1 rotation 6).
For N=32: window size = 25 (from Sigma1 rotation 25).

## The Window Automaton Formulation

Reformulate T as a window automaton:
- State at position b: (carry vector, register bits at positions b..b+w-1)
  where w = max_rotation
- State size: 49 carry bits + 8×2×w register bits
- For N=8: 49 + 96 = 145 bits → 2^145 potential states
- Actual width for collisions: ~260 (permutation)
- Actual width for all inputs: ~2^32 (near-full)

The exponential gap (2^32 actual vs 260 for collisions) is why
brute force dominates. The collision automaton has bounded width
but is EMBEDDED in a much larger automaton for all inputs.

## The Polynomial Paradox

The BDD of T's output is polynomial (O(N^4.8) nodes) because the
FUNCTION has polynomial complexity — the collision condition can be
compactly represented.

But COMPUTING the function requires enumerating the full input space
(or equivalent) because the INDIVIDUAL PATHS through the automaton
are near-injective. No carry-state DP, MITM, or bit-serial approach
can avoid the exponential search.

The only known efficient evaluator is the BDD itself — once constructed,
it can enumerate all accepting runs in O(N^4.8 + K) time. But constructing
the BDD requires finding all accepting runs first (circular).

## Where Could a Breakthrough Come?

1. **Direct BDD construction via composition**: if the per-round BDD
   operations could be composed without exponential blowup, the BDD
   could be built in polynomial time. The rotation frontier prevents
   standard Apply from working (exponential intermediates).

2. **Algebraic attack on the window automaton**: the window creates
   a system of equations that could be solved algebraically. The
   cascade's dT2=0 property linearizes much of the system. Could
   the remaining nonlinearities (Ch function) be handled by small
   case analysis?

3. **Topological constraint**: the collision set has a specific
   algebraic variety structure (intersection of N polynomial equations).
   If this variety has polynomial degree, it can be enumerated efficiently.

4. **Random self-reducibility**: if the collision function has the
   property that finding ONE collision is as hard as finding ALL,
   then the BDD polynomial complexity implies collision finding
   is polynomial. But SHA-256 likely lacks this property.

## The Bottom Line

The collision function is a dependent transducer with polynomial output
complexity and bounded accepting-path width, embedded in an exponential-
width computation. This is the unified object. Breaking through requires
either:
- A composition method that preserves polynomial BDD size (algorithmic)
- An algebraic attack on the window automaton equations (algebraic)
- Or accepting that the polynomial structure is a property of the
  solution set, not an algorithmic lever (complexity-theoretic)
