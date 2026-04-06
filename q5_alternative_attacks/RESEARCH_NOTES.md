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

**Code:** https://github.com/Peace9911/sha_2_attack.git

**Key idea:** Multi-phase decomposition using SAT/SMT (not raw MILP).
They model SIGNED DIFFERENCES {=,n,u,0,1} at each bit, not concrete values.
Search space is exponentially smaller than our bit-level value encoding.

**Their 5-phase approach:**
- Phase 1: Fix "local collision" shape (which W[i] have nonzero diffs)
- Phase 2: Minimize total HW of message diffs (SAT optimization)
- Phase 3: Minimize HW of state register diffs (zeros enforced in later rounds)
- Phase 4: Minimize HW of e-register diffs
- Phase 5: Conforming pair search (concrete values) — only 120 seconds!

**Result:** 39-step SFS collision (SHA-256), 40-step FS collision (SHA-224).

**CRITICAL INSIGHT for our project:** We solve a MONOLITHIC problem — one
giant CNF encoding both messages completely. Li et al. decompose into phases
where each constrains the next. Their Phase 5 (conforming pair search) is
what we do as our ONLY step, but they arrive with a much more constrained
problem because Phases 1-4 already determined the differential trail.

**What we're missing:**
1. Signed difference abstraction (2 vars/bit instead of 1 per message)
2. Multi-phase decomposition (trail search THEN conforming pair)
3. Sparsity optimization (minimize HW = maximize probability)
4. Selective model depth (fast filtering before full verification)
5. Their Algorithm 1 with 8 precision-control parameters

**Connection to schedule compliance:** Their "local collision" IS our
"schedule compliance" from the other direction. Same mathematical object,
fundamentally different search strategy.

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

### A. COMBINED: Decomposed Search + Programmatic SAT (HIGHEST PRIORITY)

Combine Li et al.'s multi-phase decomposition with Programmatic SAT:

**Phase 1-4 (Li et al.):** Find sparse differential trail for sr=60
- Model signed differences {=,n,u,0,1} for the 7-round tail
- Optimize for minimum HW (sparsest trail = highest probability)
- Use their Algorithm 1 with selective model depth
- Code: https://github.com/Peace9911/sha_2_attack.git

**Phase 5 (Programmatic SAT):** Conforming pair search with CaDiCaL
- Bitsliced propagation: perfect propagation at each bit position of
  modular addition (3 inputs → 2 outputs per slice). Catches deductions
  that BCP misses. Use LRU cache for repeated patterns.
- Inconsistency blocking: build graph of two-bit equality/inequality
  conditions. BFS to detect odd-length cycles = algebraic contradictions.
  Feed blocking clause to CaDiCaL → immediate backtracking.
- Wordwise propagation: δA + δB = δC (mod 2^32). Split at carry
  boundaries, brute-force subproblems ≤10 variables.
- Auxiliary variable heuristic: assume ? = - for non-primary differentials
  (dramatically improves propagation, critical for >28 steps).
- Use IPASIR-UP interface — no custom solver code needed.

**Expected improvement:** Li et al.'s Phase 5 takes 120s with a good trail.
Programmatic SAT gives 10-step improvement on plain CaDiCaL (28→38).
Combined, this could make sr=60 tractable.

### B. Multi-Block Attack
Use Merkle-Damgard: first block achieves near-collision (our sr=59
result), second block's free IV (= first block's output) corrects the
remaining differential. This has NEVER been tried on this problem.

The second block gets 256 bits of IV freedom + 512 bits of message
freedom. This is FAR more freedom than the 128 bits (4 free schedule
words) we currently have within a single block.

### C. Partial Linearization Windows
Apply the window heuristic (eprint 2024/1743) to our sr=60 encoding.
Test which bit-window sizes reveal structure vs destroy it. The window
heuristic restricts carry propagation to W consecutive bit positions,
trading accuracy for speed. Test W=1,2,4,8,16,32.

### D. Alternative Differential Trails
Use MILP or SAT to search for differential trails compatible with sr=60
that are different from the MSB kernel. Zhang et al. (2026) automated
the discovery of "local collisions" that had been manually constructed
for over a decade.

### E. Neural-Guided Branching
SAT4CryptoBench (NeurIPS 2025) provides framework for ML-guided solving
of cryptographic SAT instances. Our backbone data (9.6% backbone
variables clustering in early rounds) suggests learnable structure.

### 7. Two-Block Collision Conversion (Standard Technique)
**Finding from web search (2026-04-05)**

The two-block method is the STANDARD way to convert SFS collisions to
full collisions in SHA-256 cryptanalysis. The 31-step full SHA-256
collision uses a 2-block approach converting from the 31-step SFS.

Conversion complexity: at most 2^65.5 for 31 steps.

For our sr=59 → sr=60 gap, the residual from sr=59 should be smaller
than a generic 31-step SFS residual, so the conversion overhead could
be much lower.

Source: [The First Practical Collision for 31-Step SHA-256 (ASIACRYPT 2024)](https://dl.acm.org/doi/10.1007/978-981-96-0941-3_8)

### 8. AlphaMapleSAT: MCTS-guided Cube-and-Conquer (2024-2026)
**Paper:** [AlphaMapleSAT](https://arxiv.org/abs/2401.13770)

MCTS-guided cubing gives 1.6-7.6x speedup over March lookahead on
128 cores. But for our problem, we already know the best partition
variables from algebraic analysis (da57=0, W[58] MSBs).

The cryptographic hash inversion paper (JAIR 2024) inverted 19-round
SHA-256 with standard cube-and-conquer. Our problem (7 tail rounds)
is smaller but the collision constraint is harder than inversion.

Source: [Inverting Cryptographic Hash Functions via CnC](https://dl.acm.org/doi/pdf/10.1613/jair.1.15244)
