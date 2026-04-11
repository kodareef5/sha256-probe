# External Review: Gemini 3.1 Pro Preview — 20260410_2134
# Model: google/gemini-3.1-pro-preview
# Reasoning: {'effort': 'high'}

## Reasoning Trace

**Defining the Scope Now**

I'm currently focused on the parameters of the review. We're dealing with a project that's managed to find a semi-free-start collision at round 60 of SHA-256. My primary goal now is determining the scope of the review: what specifically needs examination and the criteria for assessing the team's work.


**Framing the Attack Angles**

I'm now zeroing in on attack vectors. Considering the provided data, I'm leaning toward a focused critique, looking at sigma 1 bridge MITM. The team's research hints at a novel partial schedule compliance, which is interesting. I'm also examining the implications of multi-block attacks, and how to best utilize Wang's techniques within this new context.


**Refining Critique Strategies**

I'm now formulating the critique. I'll begin by acknowledging the significant milestone achieved. I plan to highlight potential issues in their scaling assumptions, and how they approach continuous phase transitions. Furthermore, I'll emphasize the misuse of SAT solvers and address their over-reliance on a single MSB kernel within their methodology.


**Outlining the Structure**

I'm presently building the structure of my review. The introduction will commend the sr=60 achievement while immediately highlighting methodological challenges. I'm planning to separate the critique, new attack ideas, variant approaches, and relevant mathematical frameworks, each in their own section. The team's reliance on particular techniques needs a more careful analysis.


**Expanding on Critique Details**

I'm presently focusing on expanding the critique section. I'm articulating the flaws in their extrapolation techniques and pinpointing the issues with the "homotopy" approach, and I'm further clarifying why the perceived "uniqueness" of the 0x17149975 value might be misleading, highlighting the limitations of CDCL solvers. I'm also elaborating on the futility of brute-force cascade searches given the computational scale.


**Analyzing the Flaws Deeply**

I'm now deeply immersed in the critique, especially the methodology and blind spots. I'm articulating the flawed assumptions in the scaling approaches and the dangers of the "homotopy" approach, including the misinterpretation of sparsity. I am also discussing the implications of the "uniqueness" claim, and why a brute-force approach is futile.


**Expanding the Critique's Base**

I'm presently building upon the existing critique by pinpointing flaws in the team's methodology. Their approach to mini-SHA extrapolation and continuous phase transitions is mathematically unsound. Furthermore, I'm now providing additional details on the misinterpretation of sparsity, including its relation to solving ease and the "uniqueness" of the 0x17149975 value.


**Review Summary Progress**

I'm now outlining a prioritized critique focusing on extrapolation issues, including the "homotopy" approach, and the interpretation of sparsity. The review will address the shortcomings of a brute force cascade search, the "uniqueness" claim, and the mathematical framework's current gaps.


**Review Completion Progress**

I'm now consolidating the review, with a strong focus on practical improvements. The goal is now to propose practical fixes to their SAT encoding and algebraic representation, while simultaneously arguing for a shift toward bit-vector SMT solvers like Z3 or Boolector, and a focus on differential-linear analysis. The structure and content are now complete.




---

This is an exceptional body of research. Pushing a full N=32 SHA-256 collision to round 60 using SAT solvers and analyzing the algebraic tail is serious cryptanalysis. Your identification of the bi-cascade zeroing mechanism is a major structural insight. 

However, your extrapolation methods are scientifically dangerous, you are misinterpreting some of your algebraic results, and you are using the wrong tools for the final mathematical descent.

Here is an unfiltered, expert cryptanalytic review of your ongoing project, broken down as requested.

---

### 1. Honest Critique: Methodology & Blind Spots

**1. The Homotopy / Extrapolation Fallacy**
Your structural scaling (mini-SHA N=4 to N=32) is fundamentally flawed for predicting solve times. You cannot fit an exponential curve `T = 0.87 * 1.47^N` to CDCL solver execution times. SAT solving on cryptographic boolean structures exhibits heavily tailed (often Weibull or Pareto) distributions, not smooth exponentials. Furthermore, changing the modulo word size and scaling rotations (via banker's rounding) fundamentally reshapes the Boolean incidence graph. N=8 and N=32 do not share a continuous homotopy in boolean space; they are discrete Diophantine varieties. 

**2. Misinterpreting the "Uniqueness" of 0x17149975**
You note that 4 candidates failed at 24h, while 0x17149975 succeeded in 12h, and conclude this candidate has special "cascade alignment." While the alignment hypothesis is good, the evidence is statistically empty. CDCL SAT solvers are highly sensitive to variable ordering and random seeds (hence why `seed=5` worked). 24 hours is a microsecond in cryptanalytic SAT time. The other candidates are likely SAT, but Kissat's VSIDS/CHB branching heuristics got stuck in a heavy-tailed restart loop. Do not declare a structure "unique" based on SAT solver timeouts.

**3. Discovering the Obvious in the ANF**
You note that register `h` at round 63 has a low degree (8/32) and missing variables, contrasting it with `a` and `b` (degree 16/32). **This is structurally trivial.** Due to the shift-register nature of SHA-256, `h_63` is just `g_62` = `f_61` = `e_60`. It is literally the `e` register from 3 rounds prior, which means it has bypassed 3 subsequent layers of `Maj` and `Ch` non-linearities. You used brute-force ANF computation to discover SHA-256's literal data-flow graph. The sparsity is physically guaranteed by the specification.

**4. Misusing CDCL SAT for Sparse Algebraic Forms**
Kissat is an aggressive, plain-CNF CDCL solver. It destroys XOR structures by flattening them, severely inflating the search space on sparse algebraic forms. If your tail rounds are dominated by sparse affine structures and XOR cascades (which they are, given the 4.3% XOR closure and low degree), dropping Kissat onto a Tseitin-encoded CNF is like using a hammer on a screw. This explains why CryptoMiniSat timed out: your CNF encoding likely obfuscated the XORs preventing CMS's Gauss-Jordan elimination from triggering.

**5. UNSAT Cores and Scalability**
You used DRAT proofs to verify UNSAT at N=8. But you haven't extracted the **UNSAT Core** (the minimal unsatisfiable subset of clauses). If the UNSAT core for sr=61 at N=8 includes clauses tied to scaled rotation amounts, your "provable impossibility" does not logically scale to N=32.

---

### 2. Creative Ideas You Should Try (Prioritized)

#### A. The Sigma-1 Bridge (Algebraic MITM) via SMT/Bit-Vectors
* **What it is:** Your "Direction 1", but executed correctly. The `W1[60] = sigma1(W1[58]) + C1` bridge is a word-level constraint, NOT a boolean one.
* **Why it works:** You've identified that `W[58]` has "dual duty." Instead of randomly sampling, formalize this dual-duty inside an SMT solver (like Bitwuzla or Z3) using the Theory of Bit-Vectors (`QF_BV`). SMT solvers handle modular arithmetic and XOR bridges natively, unlike SAT. 
* **Implementation First Step:** Write a Z3 script where `W[57]` and `W[59]` are free bit-vectors. Require `W[60]` to force `de60=0`. Add the exact constraint `W[58] = sigma1_inv(W[60] - W[57]...)`. Ask the SMT solver if there exists ANY pair `(W[57], W[59])` that satisfies a valid round 58 state.
* **Timeline/Difficulty:** 1-2 days. Low difficulty. Very high probability of yielding structural insights.

#### B. The "7/8 Near-Collision" Subspace Intersection
* **What it is:** Your "Direction 5", supercharged. Leave `h` (the weakest register) unmatched. Use the SAT solver to find *hundreds* of near-collisions for registers `a-g`. 
* **Why it works:** Finding near-collisions will take minutes/seconds instead of 12 hours. The set of solutions for `a-g` forms an affine variety.
* **Implementation First Step:** Generate 1,000 solutions where `a_63 = b_63 = ... = g_63`. Now evaluate `h_63` on these 1,000 points. Because `h` has a maximum degree of 8 and relies on only 26 variables, you can use these 1000 points to interpolate the residual error space. If the error is affine, you can solve for exactly which constraints flip `h` without breaking `a-g`.
* **Timeline/Difficulty:** 3-5 days. Medium difficulty.

#### C. Multi-block Absorbtion via Wang's Modification (The Nuclear Option)
* **What it is:** Concede that sr=61 semi-free-start is mathematically impossible for a single block. Use two blocks.
* **Why it works:** This is how MD5 and SHA-1 were practically broken. You generate a near-collision at sr=59 or sr=60 where ONLY the `h` register differs (or `h` and `g`). This heavily limits the difference in the IV for Block 2. You then use the massive 512-bit message freedom in Block 2 to architect a collision that specifically cancels that strict, isolated IV difference.
* **Implementation First Step:** Map exactly how an IV difference of `delta` in `h` propagates through the first 16 rounds of SHA-256 (where message words `W[0..15]` are completely free). If you can construct a differential path that zeros that `delta` by step 16, you have defeated SHA-256. 
* **Timeline/Difficulty:** 2-3 weeks. High difficulty. This is PhD-level standard cryptanalysis, but the most likely path to a real-world result.

---

### 3. Variants of Current Approaches

* **Stop using Kissat for everything.** 
  If you are probing algebraic sparse structures, use **Bitwuzla** (for word-level/modular reasoning) or **CryptoMiniSat** (for hybrid SAT/XOR reasoning). 
  *Fixing the CMS issue:* If CMS timed out, your CNF didn't explicitly label XOR clauses. You must write a custom encoder that outputs the DIMACS XOR extension format (e.g., lines starting with `x`) so CMS passes them directly to its Gaussian elimination engine.
* **Phase Transition Precision (sr=60.5):** 
  Instead of restricting "top K bits", compute the algebraic variance of `sigma1`. Enforce constraints on the bits of `W[60]` that have the *lowest non-linear participation* in `W[58]`. By constraining the most linear bits first, you minimize constraint shock to the SAT solver.
* **Candidate Families Definition:** 
  You are defining candidates by `M[0]` and a "kernel." Instead, classify candidate families by their **Round 56 state HW**. Since the entire cascade relies on zeroing registers, the Hamming Weight of the state entering the cascade is the true parameter dictating SAT difficulty.

---

### 4. Mathematical Frameworks You're Missing

**1. Boolean Delay Equations & Data Flow Graphs (DFG)**
Your exact ANF data is crying out for DFG analysis. SHA-256's tail is not a random permutation; it's an Unbalanced Feistel Network. The "absent" variables and degree caps are exactly calculable using Algebraic Degree Bounds (using Möbius transforms over the algebraic normal form). See the literature on *Higher-Order Differentials for SHA-256*. The bound `deg(h_63) = 8` is a mathematical consequence of the Feistel shift, not an arbitrary cryptographic weakness.

**2. Boolean Gröbner Bases without Sage**
You don't need full SageMath to compute Gröbner bases. Download **PolyBoRi** (now part of BRICS/CUDD). It is specifically designed to compute Gröbner bases for boolean rings (where $x^2 = x$). Since `h[0]` is incredibly sparse and you have explicit ANF equations, computing the Boolean Gröbner Basis of the tail rounds with an enforced 0-output might instantly yield the affine constraints on `W[57-59]`. 

**3. MQ (Multivariate Quadratic) Solvers**
Your N=8 exact exact analysis implies you can frame the tail as an MQ system. Look into **Fglm** or **XL (eXtended Linearization)** algorithms. There are standalone C++ libraries (like `libfes`) built for exact solving of boolean polynomial systems over GF(2).

**4. The Reed-Muller / Syndrome Decoding perspective**
Because you have outputs dependent on 26 variables, evaluating an output bit over all $2^{26}$ combinations yields a word in the First-order Reed-Muller code $RM(1, 26)$. Your cascade constraint acts as a puncturing/syndrome condition. Using the Fast Walsh-Hadamard Transform (FWHT) on your algebraic approximations could reveal heavy linear correlations that SAT solvers miss completely.

---

### 5. What To Stop Doing

1. **Stop the 100M/sec C Server Brute Force:** Generating 10 Billion samples to reach HW=47 is algorithmic theater. You are searching a space of $2^{96}$. Generating random `W` words and checking HW is thermodynamically doomed. Shut off this script; use the cores for SMT/Bitwuzla solving or parallel near-collision extraction.
2. **Stop Simulated Annealing (SA):** SA is practically useless for cryptographic hashes. It assumes a gradient in the loss function (Hamming Weight). The strict avalanche criterion (SAC) of SHA-256 ensures that a state with HW=40 is not structurally "closer" to a collision (HW=0) than a state with HW=120. Your data already proved SA fails; don't return to it.
3. **Stop "Scaling" UNSAT Without Cores:** A proof of UNSAT at N=8 means nothing for N=32 unless you extract the logic that caused the contradiction. If the UNSAT derives from a collision between the shift-register tap amounts and the scaled rotation amounts, your N=32 system will be easily satisfiable.
4. **Stop Fixating on sr=61 for Single-Block:** If your phase transition data is correct, sr=61 restricts the system beyond its theoretical capacity. Pivot entirely to the 2-block strategy (Direction 4) for sr>60.

### Next Immediate Action:
Assign one machine to execute the **SMT/Bit-Vector formulation of the Sigma-1 Bridge** (Creative Idea A), and another to map the **Null-Space of the `h` register via Near-Collisions** (Creative Idea B). These two will instantly clarify whether the sr=60 barrier is computational or mathematical.
