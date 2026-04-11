# Claims Registry

All testable claims from this project, ranked by evidence level.
Each claim links to detailed writeup in the relevant `q*/claims/` folder.

## VERIFIED

### sr=60 collision at full SHA-256 (N=32)
**The principal result of this project.** An sr=60 semi-free-start collision
exists for the MSB kernel with M[0]=0x17149975 and all-ones padding.
- **Certificate:**
  ```
  W1[57..60] = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
  W2[57..60] = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]
  ```
- **Hash:** `ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b`
- **Evidence:** Kissat 4.0.4 --seed=5 SAT in ~12h (Mac M5). Independently
  verified on 24-core Linux server and laptop via native SHA-256 computation.
- **Mechanism:** Perfect register-zeroing cascade (see `writeups/sr60_collision_anatomy.md`)
- **Significance:** Extends Viragh (2026) from sr=59 (92.19%) to sr=60 (93.75%)
- **Caveats:** Still semi-free-start (4 free schedule words). NOT a standard collision.
- **Methodological lesson:** The original paper declared this candidate UNSAT.
  The timeout was a single-seed artifact. Seed diversity is essential.

### sr=59 collision independently reproduced
The sr=59 collision certificate from Viragh (2026) has been independently
reproduced using a custom CSA-tree SAT encoder in 220.5 seconds.
- **Evidence:** Kissat returns SAT; extracted assignment verified by native SHA-256 computation
- **Scripts:** `archive/13_custom_cnf_encoder.py` (sr59 mode)
- **Caveats:** None

### sr=60 is SAT at all non-degenerate word widths N=8 through N=32
For every non-degenerate word width from N=8 to N=30 (and N=32), there
exists a candidate producing an sr=60 collision. Continuous homotopy
with no phase transition.
- **Evidence:** Kissat SAT with verified collision at each N=8-25, 27-28, 30, 32
- **Scripts:** `q1_barrier_location/homotopy/`, `results/precision_homotopy_complete.md`
- **Gaps:** N=26, 29, 31 timeout (hard due to prime-width / rotation effects)
- **Caveats:**
  - N=9 excluded (rotation degeneracy)
  - N<32 uses scaled rotations and truncated constants
  - N=26, 29, 31 may need longer runs or different candidates

### SA cannot find sr=60 collisions even where they provably exist
Simulated annealing with 50K restarts and 500K steps per restart fails to
find HW=0 at N=8 (best: HW=8), while Kissat finds SAT in 4.3 seconds.
- **Evidence:** Extensive SA runs at N=8,10; SAT solver succeeds where SA fails
- **Scripts:** `archive/79_sa_collision_search.c`, `archive/80_mini_sa_search.c`
- **Significance:** SA-measured "thermodynamic floor" is meaningless for feasibility.
  Only CDCL SAT solvers with constraint propagation can navigate this landscape.

### Carry entropy = log2(#solutions) exactly at N=4, N=6, N=8
Each sr=60 collision has a unique carry-difference pattern. The carry
pattern IS the collision — perfect bijection (injective projection).
- N=4: 92 free carries, 49 solutions, entropy 5.6 bits, ratio **1.000**
- N=6: 181 free carries, 50 solutions, entropy 5.6 bits, ratio **1.000**
- N=8: 234 free carries, 95 solutions, entropy 6.6 bits, ratio **1.000**
- **Evidence:** Exact computation from all known collision solutions at each N
- **Significance:** The 234 "free" carry bits contain only 6.6 bits of
  independent information — the carries are 99.97% correlated. The carry
  automaton has bounded width equal to #solutions at every bit position.
- **Caveats:** Verified at mini-SHA only. "Bounded width" not yet proven
  formally — observed from the solution set, not from structure alone.

### Register h is determined by registers a-g at N=4
Exhaustive 2^32 enumeration: every input where da=db=dc=dd=de=df=dg=0
also has dh=0. h is NOT independent — cascade-2 is automatic.
- **Evidence:** 49 near-collisions = 49 full collisions. NC/full ratio = 1.000.
- **Significance:** The collision problem has 7 independent register constraints,
  not 8. One equation is redundant.

### d[0] is the algebraically weakest output bit (degree 7, N=8 restricted)
Complete restricted ANF at N=8 (32 cascade variables, exact Moebius transform).
- d[0]: degree 7, 251 monomials. h[0]: degree 8, 266 monomials.
- Perfect staircase: each bit position adds exactly 1 to the degree.
- **Evidence:** 64-bit exact computation, ~12 hours total.

### Critical W[60] schedule pairs exist at N=6 and N=8
Removing specific pairs of W[60] schedule bits makes sr=61 SAT:
- N=8: pair (4,5) SAT. All other 27 pairs UNSAT.
- N=6: pairs (1,3) and (2,5) SAT. All other 13 pairs UNSAT.
- **Evidence:** Exhaustive C(N,2) scan with Kissat at both N values.
- **Caveats:** Simple rotation-position prediction refuted at N=6.

## EVIDENCE

### sr=60 is UNSAT for M[0]=0x17149975 (MSB kernel, all-ones padding)
29 of 32 randomly sampled 5-bit dual partitions are UNSAT with:
- Kissat UNSAT + DRAT proof verified
- CaDiCaL independently confirms UNSAT
- 3 partitions timeout (204, 467, 996) — status unknown
- **Scripts:** `q6_verification/`, `archive/76_partition_verifier.py`
- **Caveats:**
  - Not all 1024 partitions tested (32/1024 sampled)
  - CryptoMiniSat times out on nearly all partitions
  - 3 partitions remain unresolved

### Carry divergence is required for MSB-kernel collisions
Forcing carry-out equality between messages at any tested bit position
produces fast UNSAT at sr=59 (where collisions exist).
- **Evidence:** Ghost carry experiments on one candidate, one kernel, one padding
- **Scripts:** `archive/30_ghost_carries.py`
- **Caveats:** Tested on one candidate only. "Observation" not "theorem."

## HYPOTHESIS

### ~~The sr=60 bottleneck is dW[61] hamming weight~~ RETRACTED
~~All SAT instances (N=8-21) have dW[61] HW in range [3, 8].~~
**Cross-validation by Q3 workstream shows dW[61] constant HW is
anti-correlated with solve speed.** The candidate with dW61_C=18 (worst)
solves fastest at N=10 and N=12, while dW61_C=12 (best) is slowest.
- **Retraction evidence:** `q3_candidate_families/results/20260405_crossval.md`
- **Replacement hypothesis:** min_hw63 and min_gh60 (MITM bottleneck metrics)
  may be better predictors. See Q3 findings.

### The barrier is candidate-dependent, not fundamental
Scaling is highly non-monotonic (N=17 faster than N=16, N=20 faster than N=18).
Different candidates at the same N have very different solve times.
- **Evidence:** Parallel candidate races show 3-5x variance within same N
- **Caveats:** Non-monotonicity could also be solver-specific (Kissat heuristics)

## EXTRAPOLATION

### sr=60 at N=32 may be solvable in ~days of compute
Exponential fit T = 0.87 * 1.47^N gives ~21h for N=32.
- **Evidence:** Fit to 11 data points (N=8 through N=21)
- **Caveats:**
  - Extrapolation from mini-SHA to full SHA-256 is fundamentally unreliable
  - Mini-SHA uses different rotation amounts and truncated constants
  - The fit is dominated by non-monotonic scatter
  - A phase transition could exist between N=21 and N=32
  - Even if solvable, finding the right candidate is a separate challenge

## RETRACTED / DOWNGRADED

### "Ghost Carry Theorem" → Observation
Originally framed as a theorem with proof. Downgraded to observation:
tested on one candidate, one kernel, one padding. Not a general property.

### "Boomerang Algebraic Contradiction" as primary explanation
Script 69 shows 20% prediction accuracy. Does not cleanly separate SAT
from UNSAT. Retained as a family-specific diagnostic, not a principal result.

### "Thermodynamic Floor" as property of SHA-256
The floor is a property of one candidate family under one kernel. Different
families may have very different thermodynamic properties.
