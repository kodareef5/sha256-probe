# Q5 Research Notes: Alternative Attack Techniques

## Literature Review (2026-04-05)

### 1. Programmatic SAT (Alamgir et al., 2024)
**Paper:** [SHA-256 Collision Attack with Programmatic SAT](https://arxiv.org/abs/2406.20072)

**Key idea:** Instead of encoding SHA-256 as a black-box CNF, inject domain
knowledge directly into CaDiCaL via the IPASIR-UP interface. Two techniques:
- **Bitsliced propagation:** Propagate SHA-256 operations (Ch, Maj, Sigma)
  at the word level during CDCL search, catching inconsistencies that the
  clause-level propagator misses.
- **Inconsistency blocking:** Use a CAS (computer algebra system) to detect
  algebraic contradictions during search, pruning dead branches early.

**Result:** Plain CaDiCaL: 28 steps max. With programmatic SAT: **38 steps SFS**.
That's a 10-step improvement from solver customization alone.

**Relevance to us:** We use Kissat as a black box. Switching to CaDiCaL with
IPASIR-UP and adding SHA-256-specific propagation could dramatically improve
our sr=60 instances. The constant-folding we do at encode time could instead
be done dynamically during search.

### 2. Li et al. EUROCRYPT 2024 — New Records in SHA-2 Collisions
**Paper:** [New Records in Collision Attacks on SHA-2](https://eprint.iacr.org/2024/349)

**Key idea:** Use MILP-based differential trail search combined with SAT/SMT
for characteristic verification. The breakthrough was finding "local collisions"
in the message expansion — patterns where the schedule words cancel each other
over a few rounds. This is exactly what Viragh's "schedule compliance" approach
does from the opposite direction.

**Result:** 39-step SFS collision (SHA-256), 40-step FS collision (SHA-224).

**Relevance:** Their MILP trail search finds optimal differential paths that
our brute-force approach cannot discover. We should try their trail search
framework on our 7-round tail problem.

### 3. Window Heuristic / Partial Linearization (eprint 2024/1743)
**Paper:** [The Window Heuristic: Automating Differential Trail Search in ARX Ciphers](https://eprint.iacr.org/2024/1743)

**Key idea:** Replace modular addition with XOR (linearization) within
"windows" of W consecutive bit positions. This creates a controllable
trade-off between accuracy and search speed for differential trail finding.

**Relevance:** Our carry homotopy experiment (replacing all additions with XOR)
showed the linearized sr=60 instance ALSO times out. But partial linearization
with windows might reveal structure that full linearization destroys. The
window heuristic could help us understand which bit positions carry the
essential non-linearity.

### 4. CDCL(Crypto) Framework (Nejati et al., 2020+)
**Paper:** [CDCL(Crypto) SAT Solvers for Cryptanalysis](https://arxiv.org/abs/2005.13415)

**Key idea:** Extend CDCL's unit propagation and conflict analysis with
domain-specific "theory propagation" for cryptographic primitives. This is
the theoretical foundation for Programmatic SAT.

**Result:** Improved reduced-round SHA-256 collisions (25 rounds vs 24 with
plain SAT). The CDCL(Crypto) approach catches propagation opportunities that
standard clause-based propagation misses.

### 5. Neural-Guided SAT for Cryptanalysis (NeurIPS 2025)
**Papers:** Multiple from NeurIPS 2024-2025

**Key idea:** Use neural networks to predict critical variable assignments,
then enumerate around those predictions. Up to 5x speedup on cryptographic
SAT instances. SAT4CryptoBench provides standardized benchmarks.

**Relevance:** If our sr=60 CNFs have learnable structure (which backbone
mining suggests they do — 9.6% backbone variables), ML-guided branching
could significantly speed up solving.

### 6. Zhang et al. 2026 — Improved Trail Search to 37 Steps
**Paper:** [Collision Attacks on SHA-256 up to 37 Steps](https://eprint.iacr.org/2026/232)

**Key idea:** Automate the discovery of "local collisions" in the message
expansion. Previously done manually (limiting progress for >10 years).
Their automated tool finds high-quality local collisions efficiently.

**Relevance:** "Local collisions in the message expansion" = schedule
compliance. This is literally what Viragh's approach encodes. Their
automated trail search could identify which schedule patterns are most
favorable for our sr=60 problem.

## High-Priority Ideas for Our Project

### A. Programmatic SAT (HIGHEST PRIORITY)
Switch from Kissat (black-box) to CaDiCaL with IPASIR-UP. Implement:
- Bitsliced word-level propagation for SHA-256 operations
- Inconsistency blocking based on the boomerang contradiction
- Dynamic constant folding during search (instead of at encode time)

The 28→38 step improvement from this technique alone is extraordinary.
Even a fraction of that improvement on our sr=60 instance could break
the timeout barrier.

### B. MILP Trail Search
Use MILP to find optimal differential trails for the 7-round tail.
Our current approach fixes the trail (MSB kernel → specific state56)
and searches for free words that satisfy it. MILP could find entirely
different trails that are more compatible with sr=60 schedule compliance.

### C. Multi-Block Attack
Use Merkle-Damgard: first block achieves near-collision (e.g., our sr=59
result), second block's free IV (= first block's output) corrects the
remaining differential. This has NEVER been tried on this problem.

### D. Partial Linearization Windows
Apply the window heuristic to our sr=60 encoding. Test which bit-window
sizes reveal structure vs destroy it. This could identify which carry
positions are the actual obstruction.

### E. Neural-Guided Branching
Train a neural network on our backbone data and sr=59 solutions to
predict promising branch directions for sr=60 instances.
