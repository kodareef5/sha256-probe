# Multi-Paper Plan for SHA-256 Probe Project

## Paper 1: The Collision — CRYPTO/EUROCRYPT submission
**Title**: "Extending SHA-256 Semi-Free-Start Collisions to 60 Rounds"
**Status**: Main result ready, structural theory complete

### Abstract draft
We present a semi-free-start collision for SHA-256 reduced to 60 of 64
rounds, extending the previous best of 59 rounds (Viragh 2026). Our
collision uses a perfect register-zeroing cascade mechanism that propagates
through the SHA-256 shift register. We provide six structural theorems
characterizing the cascade mechanism and proving the sr=60/61 boundary
is a fundamental consequence of the sigma1 schedule constraint. Our analysis
reveals that the collision manifold admits a polynomial O(N^4.8) BDD
representation with a completion quotient exactly equal to the collision count,
yet this compactness is algorithmically inaccessible due to rotation-induced
non-local dependencies (treewidth ~71 at N=4). We experimentally verify all
results across word widths N=4 to N=32 using three independent machines.

### Key sections
1. Introduction + Viragh background
2. The cascade collision mechanism (anatomy)
3. Six structural theorems
4. sr=60/61 boundary proof
5. Precision homotopy (N=8 to N=32 SAT results)
6. Negative results: why sr=61 is hard
7. Implications for SHA-256 security

---

## Paper 2: The BDD Paradox — TCS/ICALP/CCC
**Title**: "Polynomial Knowledge Representation with Exponential Construction
Barriers in Cryptographic Boolean Functions"
**Status**: BDD results complete, quotient verified, compilation experiments ongoing

### Abstract draft
We identify a striking structural phenomenon in the Boolean function
describing cascade collisions in reduced SHA-256: the function admits a
polynomial-size ROBDD (O(N^4.8) nodes) and a completion quotient that
equals the number of satisfying assignments (verified at N=8,10,12), yet
all known construction methods require exponential intermediate work.
Bottom-up symbolic methods (ROBDD Apply, SDD conjunction) produce
exponential intermediates, while bit-serial dynamic programming yields
no state deduplication. Top-down CDCL-based compilation (d4) avoids
intermediate blowup but still requires substantial computation. We relate
this phenomenon to the treewidth of the constraint graph induced by
SHA-256's rotation operations and propose this as a natural example of
the gap between descriptive and constructive complexity in Boolean function
representations.

---

## Paper 3: The Carry Automaton Framework — FSE/ToSC
**Title**: "Carry Automata for Analyzing Modular-Addition Hash Functions"
**Status**: Framework complete, multiple verified results

### Key results for this paper
1. Carry entropy theorem (carry state ↔ collision bijection)
2. 42% carry-diff invariance (universal, kernel-independent)
3. Carry automaton permutation property
4. Cascade tree linearity (branching factor ~1.04)
5. W[59] bottleneck identification
6. Kernel optimization (MSB suboptimal, bit-6 optimal at N=8)
7. Fill-pattern effects (alternating fills for odd N)

---

## Paper 4: Knowledge Compilation Barriers — SAT/CP/AAAI
**Title**: "Knowledge Compilation Meets Cryptanalysis: Why SHA-256
Collisions are Hard to Compile"
**Status**: In progress — d4 experiments running

### Key results
1. Bottom-up compilation (SDD, BDD Apply): exponential intermediates
2. Top-down compilation (d4): avoids blowup, but slow
3. Treewidth analysis: ~71 at N=4, dominated by rotation structure
4. Derived encoding halves free variables, potentially accelerates d4
5. Three bit-serial DP experiments: all brute-force (rotation frontier)
6. BDD completion quotient = constructive automaton width

---

## Paper 5: Experimental SAT for Reduced-Round Hashes — J.Crypto
**Title**: "Empirical Analysis of SAT Solver Performance on SHA-256
Cascade Collision Instances"
**Status**: Extensive data collected

### Key results
1. Seed diversity is essential (single-seed artifacts)
2. Cascade-augmented encoding (+33% robustness)
3. Derived encoding (half free variables)
4. Solver comparison (Kissat >> CaDiCaL >> CryptoMiniSat >> Z3)
5. Scaling analysis (N=8 to N=32, non-monotonic)
6. sr=61 race: 2000+ CPU-hours, zero SAT

---

## Paper 6: Multi-Width Homotopy — Design Codes Crypto
**Title**: "Continuous Homotopy of SHA-256 Collision Attacks Across
Word Widths"
**Status**: Complete data, interesting odd/even effects

### Key results
1. sr=60 SAT at every non-degenerate N from 8 to 32
2. N=9 anomaly (rotation degeneracy at odd N)
3. Fill-pattern dependence (alternating fills rescue odd N)
4. Exotic kernels (non-(0,9) word pairs work)
5. Critical pair landscape varies by kernel
