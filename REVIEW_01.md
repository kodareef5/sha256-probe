⏺ All four parallel reviews are complete. Here's the consolidated critical analysis:
                                                                                          
  ---
  SHA-256 sr=60 Campaign: Rigorous Audit Report                                                                         
                                                                                                                        
  Executive Summary                                                                                                     
                                                                                                                        
  This is a substantial body of work (55+ scripts, ~200 CPU-hours, 13 rounds of experimentation) investigating the sr=60
   schedule compliance barrier for SHA-256. The engineering is impressive — particularly the CSA-tree SAT encoder and
  constant-folding discovery. However, the work consistently overstates its results, and several claims require         
  significant qualification or correction.                  

  ---
  1. BUGS FOUND
               
  Critical / High Severity
                                                                                                                        
  1a. UNSAT "Proof" Description Doesn't Match Code                                                                      
                                                                                                                        
  The writeup (THE_THERMODYNAMIC_FLOOR.md Section 3.2) claims: "We fix the top 4 MSBs of both W1[57] and W2[57] at      
  encode time, generating 256 constant-folded sub-instances."
                                                                                                                        
  But 41_unsat_proof_engine.py only fixes W1[57] MSBs (lines 52-63). W2[57] is fully free (line 69: w2_57 =             
  cnf.free_word("W2_57")). The script's own header says: *"Fix the top 8 bits of W1[57]."*
                                                                                                                        
  The "256 = 16x16 pairs" partition described in the paper cannot come from Script 41. Script 43                        
  (43_candidate_validator.py) does fix both, but only at Level 1. The recursive Level 2 and Level 3 partitioning scheme 
  is ambiguously described — the numbers (128 survivors → 64 → 0) only make sense if later levels partition over W1     
  alone, contradicting the claim.                           

  This is the most serious finding. The UNSAT proof's partition scheme must be clarified before the proof can be        
  evaluated.
                                                                                                                        
  1b. No DRAT/DRUP Proof Verification                                                                                   
  
  The "proof" relies solely on Kissat's return code (returncode == 20). No proof certificate was generated (--proof flag
   not used), no proof checker was run. An UNSAT "proof" without independent verification has the same epistemological
  status as a very long timeout. This is standard practice in SAT-based cryptanalysis and its absence is a critical gap.
                                                            
  1c. Single-Solver UNSAT Testing

  All UNSAT partitions were tested only on Kissat 4.0.4. No cross-validation with CaDiCaL, CryptoMiniSat, or any other  
  solver on the constant-folded partitions. A Kissat bug returning false UNSAT would invalidate everything.
                                                                                                                        
  Medium Severity                                                                                                       
  
  1d. Script 05 (z3_sr60_multi.py) — Unimplemented "Analytical Reduction"                                               
                                                            
  Claims "analytical reduction" halving variables, but the actual code has a no-op: s.add(st1[0] == st2[0] if False else
   True) (line 154). Falls back to the full problem. Any "definitive UNSAT" claim from this script is a misinterpreted
  timeout.                                                                                                              
                                                            
  1e. N=9 Rotation Degeneracy in Precision Homotopy                                                                     
  
  At N=9, scale_rot(17,9) == scale_rot(19,9) == 5, making sigma1(x) = SHR(x,3) (two rotations cancel in XOR). This      
  fundamentally breaks schedule diffusion. The N=9 UNSAT result reflects a degenerate function, not SHA-256 structure.
                                                                                                                        
  1f. Script 40 v1 — Fragile W[63] Index                    

  sched[4 + len(sched) - 6] in the v1 function is fragile and may compute incorrect W[63] depending on schedule length. 
  The v2 function is correct.
                                                                                                                        
  1g. Ch_py Operator Precedence Bug (Latent)                                                                            
  
  def Ch_py(e, f, g): return (e & f) ^ ((~e) & g) & 0xFFFFFFFF                                                          
  The mask only applies to the right operand due to precedence. Produces correct results for 32-bit inputs (all current 
  usage) but is fragile. Appears in scripts 01, 02, 03, 05, 06, 10, 11, 13, 72.                                         
                                                                                                                        
  Low Severity                                                                                                          
                                                                                                                        
  - Dead sha256_round method (13_custom_cnf_encoder.py:361) — wrong shift register, never called but should be removed  
  - padding_cooler.c — undefined behavior when no hits found ("ABC"[-1])                                                
  - Genetic scanner — signal starvation (P(da[56]=0) ~ 2^{-31} per evaluation makes GA blind)                           
  - golden_scanner.c — unused W1_pre/W2_pre parameters, n_hits % 1 == 0 always true                                     
                                                                                                                        
  ---                                                                                                                   
  2. QUESTIONABLE CLAIMS                                                                                                
                                                            
  "Ghost Carry Theorem" — Not a Theorem
                                                                                                                        
  This is an experimental observation on ONE candidate (M[0]=0x17149975) with ONE kernel (MSB) and ONE padding          
  (all-ones). Testing: MSB carries of specific rounds, not "any single bit position of any single round" as claimed.    
  Calling it a "theorem" with a "proof" is a serious category error. It should be labeled an experimental finding.      
                                                            
  Boomerang Gap — Listed as "Principal Result" Despite 20% Prediction Accuracy                                          
  
  The paper derives the boomerang gap criterion, validates it against reduced-width instances, and finds it doesn't     
  predict SAT vs UNSAT (accuracy: 1/5). Script 69's own output: "NEGATIVE: The boomerang gap does NOT cleanly separate 
  SAT from UNSAT." Yet the abstract lists it as Principal Result #4, and Section 9.1 says UNSAT is "rooted in" the      
  boomerang gap. This directly contradicts the validation evidence.

  Precision Homotopy — Enormous Extrapolation

  - SAT at N=8-15, UNSAT at N=32. The claim "barrier is scale-dependent, not topological" does not follow — a           
  topological barrier can have a critical dimension
  - Scaling is non-monotonic (N=13 solves faster than N=12; N=15 faster than N=12) — extrapolation to N=32 is unfounded 
  - Mini-SHA-256 with truncated constants and scaled rotations is a different function than SHA-256                     
  - The claim "sr=60 collisions almost certainly exist at 32 bits for some candidate family" is a massive leap from "SAT
   at N≤15"                                                                                                             
                                                                                                                        
  Title Overreach                                                                                                       
                                                            
  "The Thermodynamic Floor of SHA-256" implies a property of SHA-256 itself. The actual result is about one candidate   
  family under one kernel with one padding scheme.          
                                                                                                                        
  ---                                                       
  3. METHODOLOGICAL GAPS
                        
  Standard Cryptanalytic Techniques Never Applied
                                                                                                                        
  ┌──────────────────────────────────┬──────────────┬───────────────────────────────────────────────────────────────┐
  │            Technique             │    Status    │                            Impact                             │   
  ├──────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────────────┤
  │ Wang-style message modification  │ Not          │ The dominant SHA collision technique since 2005. Directly     │
  │                                  │ attempted    │ applicable to 7 rounds with 4 free words                      │
  ├──────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────────────┤   
  │ MILP-based differential trail    │ Not          │ State of the art (Li et al., EUROCRYPT 2024, cited in the     │
  │ optimization                     │ attempted    │ paper). Never used                                            │   
  ├──────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────────────┤
  │ Groebner bases / XL algorithm    │ Not          │ The "full algebraic degree at dim 15" result doesn't preclude │   
  │                                  │ attempted    │  structure at dim 128+                                        │   
  ├──────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────────────┤
  │ Multi-block attacks              │ Not explored │ Merkle-Damgard allows second block to correct residual        │   
  │                                  │              │ differences                                                   │   
  ├──────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────────────┤
  │ Non-contiguous gap placement     │ Barely       │ Script 04 only checks t-2 dependency, not t-7/t-15/t-16       │   
  │                                  │ explored     │                                                               │   
  ├──────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────────────┤
  │ SAT preprocessing (SatELite,     │ Not          │ Could bridge the constant-folding gap without manual          │   
  │ BVE, Vivification)               │ attempted    │ partitioning                                                  │   
  └──────────────────────────────────┴──────────────┴───────────────────────────────────────────────────────────────┘
                                                                                                                        
  Incomplete Explorations                                   

  ┌───────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┐   
  │           Area            │                                         Gap                                         │ 
  ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤   
  │ M[2..15] variation        │ Fixed at all-ones. Only M[1], M[14], M[15] varied. The all-ones choice may be       │ 
  │                           │ structurally unfavorable                                                            │ 
  ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤   
  │ Single-bit kernels        │ Only MSB (bit-31) and bit-30 tested. 30 other bit positions unexplored              │
  ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤   
  │ Script 10 algebraic       │ Tests W1 variation only, ignoring the (W1,W2) joint space                           │
  │ degree                    │                                                                                     │   
  ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤   
  │ UNSAT core atlas          │ Only 5 of 256 partition cells sampled                                               │
  ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤   
  │ Solver diversity          │ Fixed at Kissat 4.0.4. No version variation, no seed variation on UNSAT partitions  │
  ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤   
  │ Comparison with Viragh    │ 2.3x slower than original (220s vs 96s for sr=59). Gap never investigated or closed │
  │ encoder                   │                                                                                     │   
  └───────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
                                                                                                                        
  ---                                                       
  4. STONES LEFT UNTURNED — Comprehensive List
                                                                                                                        
  Tier 1: High-Priority Gaps (likely to yield new information)
                                                                                                                        
  1. DRAT proof verification of the existing UNSAT partitions — required to call it a "proof"                           
  2. Cross-solver validation of constant-folded UNSAT on CaDiCaL + CryptoMiniSat                                        
  3. Wang-style message modification on the 7-round tail with known sr=59 differential                                  
  4. MILP trail search for alternative differential paths (current trail proven incompatible at sr=60)                  
  5. Systematic M[2..15] variation — genetic/MILP-guided, not just M[1] brute force                                     
  6. Run Viragh's original encoder on the constant-folded partitions (may be 2.3x faster)                               
  7. SAT preprocessing (SatELite/Vivification) as alternative to manual constant-folding                                
                                                                                                                        
  Tier 2: Alternative Approaches Not Explored                                                                           
                                                                                                                        
  8. All 32 single-bit kernel positions (only 2 tested)                                                                 
  9. Non-contiguous gap placement with full dependency analysis (t-2, t-7, t-15, t-16)
  10. Multi-block collision construction                                                                                
  11. Groebner basis / algebraic attack on the 7-round tail system                                                      
  12. Coupled (M[0], M[1..8]) candidate generation — joint optimization instead of sequential scan                      
  13. SAT-based schedule gap optimization — find optimal freedom layout, not just contiguous                            
  14. Rotation-symmetric kernel families — kernels invariant under sigma function rotations                             
  15. Structured IV construction preserving MSB kernel properties (current random IV scan failed)                       
                                                                                                                        
  Tier 3: Cross-Disciplinary (Speculative but Identified in Brainstorm)                                                 
                                                                                                                        
  16. Carry-profile genetic search (evolve divergence patterns, not messages)                                           
  17. Belief propagation preconditioning for variable ordering
  18. Differentiable ARX surrogate + gradient descent                                                                   
  19. Replica exchange / parallel tempering across softened instances                                                   
  20. Persistent homology on near-solution space                                                                        
  21. Tensor network contraction view of the round structure                                                            
  22. CEGIS for message modification rule synthesis                                                                     
                                                                                                                        
  Tier 4: Verification & Robustness                                                                                     
                                                                                                                        
  23. Sensitivity to Kissat random seed on UNSAT partitions                                                             
  24. Sensitivity to Kissat version (test 3.x, 4.0.x, 4.1.x)
  25. Timeout sensitivity — are "survivors" at 60s actually UNSAT at 120s?                                              
  26. CSA tree topology alternatives — different decomposition orderings                                                
  27. N=9 controlled experiment — test with corrected rotation amounts to isolate degeneracy                            
  28. Independent verification of the sr=59 collision certificate (not just reproduction)                               
                                                            
  Tier 5: The Round-60 Counting Ambiguity                                                                               
                                                            
  29. C scanners vs SAT solver convention alignment — multiple C scanners compute state after round index 60 (61 total  
  rounds). If the SAT solver's "sr=60" boundary differs, the thermodynamic floor measurements are at the wrong round 
  boundary. This needs explicit verification.                                                                           
                                                            
  ---
  5. OVERALL ASSESSMENT
                                                                                                                        
  What's solid:
  - The CSA-tree encoder is well-engineered and correct (modulo the latent Ch bug)                                      
  - The sr=59 independent reproduction is legitimate                                                                    
  - The constant-folding >> unit-clause discovery is a genuine methodological contribution
  - The experimental coverage within the SAT paradigm is impressively thorough                                          
  - Most conclusions are appropriately scoped when read carefully                                                       
                                                                                                                        
  What needs fixing before any publication:                                                                             
  1. Reconcile Script 41 code with the writeup's UNSAT proof description                                                
  2. Generate and verify DRAT proofs for all UNSAT partition results                                                    
  3. Cross-validate with at least one other solver                                                                      
  4. Rename "Ghost Carry Theorem" to "Ghost Carry Observation"                                                          
  5. Downgrade the boomerang gap from "Principal Result" (or remove the misleading claim that UNSAT is "rooted in" it)  
  6. Add proper caveats to precision homotopy extrapolations                                                            
  7. Fix the Ch operator precedence in all affected scripts                                                             
  8. Fix the title to scope appropriately                                                                               
                                                                                                                        
  The bottom line: The work demonstrates strong engineering and thorough SAT-based exploration, but the claims outrun   
  the evidence in multiple places. The UNSAT "proof" needs verification before it can be called a proof. The most       
  promising unexplored directions are Wang-style message modification, MILP trail optimization, and systematic M[2..15] 
  variation — all standard cryptanalytic techniques that this SAT-focused campaign bypassed entirely. 