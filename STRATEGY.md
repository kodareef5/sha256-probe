# SHA-256 Probe: Strategic Direction

*Updated 2026-04-05 based on Q3 findings + Q5 experiments + literature review*

## What We've Learned

### From Q3 (Candidate Family Search)
1. All MSB-kernel candidates are thermodynamically identical at N=32
2. All 2-bit kernels have the same thermodynamic distribution as MSB
3. The ~90-bit thermodynamic floor is a property of the sr=60 PROBLEM
   GEOMETRY (7 tail rounds, 4 free words, schedule coupling), not of
   any kernel or candidate
4. dW[61] constant doesn't predict SAT difficulty
5. Padding freedom doesn't help
6. Crossval speed differences at reduced widths are truncation artifacts

**Bottom line:** Searching for better candidates within any kernel family
is a dead end. The thermodynamic floor cannot be broken by choosing a
different M[0], fill, or kernel.

### From Q5 (Constrained Search Experiments — 53+ CPU-hours)
1. **de57=0 is universally UNSAT** — zeroing the e-register at depth 1
   is provably impossible for ALL MSB-kernel candidates (<0.5s each)
2. **da57=0 is the ONLY viable depth-1 strategy** — all other dW57
   constraints are UNSAT in <1s
3. **Alternative gap placement (free W[58..61]) is UNSAT in 0.1s** —
   W[57] freedom is essential for any chance at sr=60
4. **Single-threaded Kissat with da57=0: TIMEOUT at 7200s** for both
   best and published candidates
5. **Partition solver (5-bit: 32 parts × 3600s): ALL TIMEOUT**
6. **8-bit partition (256 parts × 3600s) running overnight**
7. **de57_err under da57=0 constraint** correlates with reduced-width
   solve speed: best candidate has de57_err=11, published has 21

**Bottom line:** Single-threaded black-box SAT is insufficient even with
algebraic constraints. The problem needs domain-specific solver technology
or fundamentally different attack structure.

### From Literature Review
The standard cryptanalysis community uses fundamentally different
techniques than we've been applying:

| Our approach | Standard approach |
|---|---|
| Monolithic SAT instance | Multi-phase decomposition |
| Concrete bit values | Signed difference abstraction |
| Black-box solver | Domain-specific solver (CDCL(Crypto)) |
| Fixed differential (MSB kernel) | Optimized differential trail |
| Brute-force candidate search | MILP/SAT sparsity optimization |

## The Five Most Promising Directions

### 1. Decomposed Search (Li et al. approach)
**What:** Instead of one giant CNF, decompose into phases:
1. Find the sparsest differential trail compatible with sr=60
2. Optimize the trail for conforming-pair searchability
3. Only then search for concrete message values

**Why:** Li et al.'s Phase 5 (conforming pair, equivalent to our entire
approach) takes 120 seconds. Our monolithic approach times out at 7200s.
The difference is that phases 1-4 constrain the problem enormously.

**How:** Implement signed-difference model for 7-round SHA-256 tail.
Use SAT/SMT to find sparse trails. Then encode conforming pair search
with the trail as additional constraints.

**Code starting point:** https://github.com/Peace9911/sha_2_attack.git

### 2. Programmatic SAT (IPASIR-UP)
**What:** Replace Kissat (black-box) with CaDiCaL + domain-specific
propagation and inconsistency blocking.

**Why:** Plain CaDiCaL: 28-step collision max. With IPASIR-UP: 38 steps.
A 10-step improvement from solver customization alone.

**How:** Implement SHA-256 word-level propagation as an IPASIR-UP user
propagator. The propagator does at search time what our constant-folding
does at encode time, but dynamically adapts to the current partial
assignment.

### 3. Multi-Block Attack
**What:** Use two compression blocks. First block achieves near-collision
(our sr=59 result). Second block's free "IV" (= first block's output)
corrects the residual differential.

**Why:** Never tried on this problem. The Merkle-Damgard structure
gives a completely free 256-bit IV for the second block, which is
far more freedom than the 4 free schedule words we currently have.

**How:** Encode: compress(IV, M1) should be close to compress(IV, M2)
after one block. Then compress(H1, M1') = compress(H2, M2') for some
second-block messages M1', M2'.

### 4. Alternative Differential Trails
**What:** The MSB kernel is one specific differential. Standard
cryptanalysis has found that the CHOICE of differential trail is the
single most important factor. We've been brute-forcing candidates
within a fixed trail.

**Why:** Zhang et al. (2026) automated the discovery of "local
collisions" in the message expansion, breaking through a decade-long
bottleneck of manual trail construction.

**How:** Use MILP or SAT to search for differential trails compatible
with sr=60 schedule compliance. The trail determines which message
words carry differences, and the schedule compliance constraint
determines which words are free.

### 5. Partial Linearization Windows
**What:** Replace modular addition with XOR in "windows" of W
consecutive bit positions. Trade accuracy for speed in trail search.

**Why:** Our full-linearization experiment (XOR-SHA) showed sr=60
also times out when fully linearized. But partial linearization might
reveal which carry positions are the actual obstruction.

**How:** Implement the Window Heuristic from eprint 2024/1743 on
our 7-round tail encoding. Test window sizes W=1,2,4,8,16,32 to
find the critical carry-chain length.

## Priority Order

1. **Decomposed search** — highest expected payoff, most aligned with
   how the community actually makes progress
2. **Programmatic SAT** — can be applied to our existing encoding,
   potentially 10x improvement
3. **Multi-block** — completely new angle, low probability but high
   reward
4. **Alternative trails** — requires new tooling but addresses the
   real bottleneck
5. **Partial linearization** — diagnostic value, helps understand
   the problem structure

## What NOT to Do More Of

- Candidate scanning (Q3 is exhausted)
- Kernel exploration (thermodynamic floor is kernel-independent)
- Black-box SAT solver tuning (marginal returns)
- Thermodynamic scoring (all candidates look the same at N=32)
