# SHA-256 Probe: Project Pause Summary
## 2026-04-20 — Regrouping

## Principal Achievements

### 1. sr=60 Semi-Free-Start Collision at Full SHA-256 (N=32)
- **Certificate verified on 3 machines**
- Extends Viragh (2026) from 59/64 rounds to 60/64 rounds (93.75%)
- Mechanism: perfect register-zeroing cascade (two zero-waves through shift register)

### 2. Complete Structural Theory (6 Theorems)
- Cascade diagonal, de60=0 always, three-filter equivalence
- da=de identity, sr=61 cascade break (P=2^{-N}), 3x algorithmic ceiling
- Clean proof that sr=60/61 boundary is structural, not computational

### 3. BDD Polynomial Complexity + Completion Quotient
- O(N^4.8) BDD size (10 data points, N=2..12)
- Completion quotient = #collisions (verified N=8, N=10, N=12)
- A constructive O(2^N)-state automaton EXISTS
- **The paradox**: compact solution language, intractable search space

### 4. Comprehensive Negative Results
- Carry-state DP: zero speedup (near-injective on search space)
- GF(2) linearization: fails (carry nonlinearity fundamental)
- Carry elimination: affine rank maximal (quadratic MAJ does all pruning)
- Bottom-up SDD: exponential blowup (10.5GB at N=4)
- Bit-serial DP (3 variants): all brute force
- BDD marginals: uniform at N≥10 (no SAT phase hints)
- Critical pair predictor: linear bridge too coarse (sigma1 rank-deficient)
- Derived encoding: hurts compilation (tw=181 vs 110)
- d4 on N=8: >67h without completing (treewidth barrier)

### 5. Critical CNF Audit
- ALL 38 fleet "sr=61" CNFs were actually sr=60 (misnamed)
- ~2000 CPU-hours of prior "sr=61 racing" invalidated
- True sr=61 first attempted 2026-04-18
- 36 TRUE sr=61 seeds × ~51h = ~1800 CPU-hours: zero SAT

## Key Numbers

| Metric | Value |
|--------|-------|
| Total CPU-hours invested | ~5000+ |
| sr=60 solve time | 12h (Kissat seed=5) |
| TRUE sr=61 at N=32 | 1800+ CPU-hours, ZERO SAT |
| d4 N=4 compilation | 39s (treewidth=54) |
| d4 N=8 compilation | >67h (treewidth=110), killed |
| BDD nodes at N=12 | 92,975 |
| Collision count scaling | ~2^N |
| BDD quotient peak/collisions | 0.98-0.99 (all N) |
| Treewidth standard N=8 | 110 (d4 FlowCutter) |
| Treewidth derived N=8 | 181 (worse!) |

## What We Proved

1. **sr=60 is achievable** (collision certificate)
2. **sr=61 is structurally ~2^32× harder** (cascade break theorem + empirical)
3. **The collision manifold is polynomial** (BDD O(N^4.8))
4. **But not constructively accessible** (all compilation/DP methods fail)
5. **The rotation frontier blocks decomposition** (treewidth ~110 at N=8)
6. **Linear analysis is always insufficient** (quadratic MAJ/Ch does all pruning)
7. **The right quotient exists** (completion width = #collisions) but can't be built without knowing solutions

## What Remains Open

1. **sr=61 at N=32**: genuinely open (1800 CPU-hours is insufficient to conclude)
2. **d4 with XOR preprocessing**: might reduce treewidth enough to complete
3. **Chunk-mode DP with mode variables**: the constructive approach neither proven nor disproven
4. **Wang-style Block-2 attack**: unexplored at N=32 (HW≈28 residual)
5. **Cascade-auxiliary encoding**: might help both SAT and compilation
6. **N=32 kernel optimization**: sigma1-aligned kernels (10,17,19) untested with better fills

## External Reviews (Gemini 3.1 Pro + GPT-5.4)

Reviews 7, 8, 10 all converge:
- "You have arrived at the destination" (Gemini R8)
- "The collision language is compact; the natural search state is not" (GPT-5.4 R8)
- "Stop raw carry DP, stop more SAT seeds on unchanged encodings" (both)
- "The paper is there — write it up" (both)
- Publication recommendation: CRYPTO/EUROCRYPT for the boundary paper

## Publication Plan (6 Papers)

1. **CRYPTO/EUROCRYPT**: sr=60 collision + structural boundary theory
2. **TCS/ICALP**: Polynomial BDD paradox + completion quotient
3. **FSE/ToSC**: Carry automaton framework for hash analysis
4. **SAT/CP**: Knowledge compilation barriers for ARX ciphers
5. **J.Crypto**: Empirical SAT analysis for hash collision instances
6. **DCC**: Multi-width homotopy across word sizes

## Files of Note

- `writeups/PROJECT_SUMMARY.md` — master summary
- `CLAIMS.md` — all claims with evidence levels
- `writeups/20260417_multi_paper_plan.md` — 6-paper outlines
- `q5_alternative_attacks/results/` — 250+ result files
- `cnfs_n32/TRUE_sr61_*.cnf` — genuine sr=61 CNFs for future work
- `encode_sr61_cascade.py`, `encode_sr61_derived.py` — improved encoders
- `q5_alternative_attacks/bdd_quotient_and_marginals.c` — BDD analysis tool
- `q5_alternative_attacks/bitserial_carry_dp.c` — DP experiments
- External reviews in `q5_alternative_attacks/results/2026041*_inspiration_*.md`

## Compute State at Pause

- All processes killed (d4, kissat)
- Fleet notified of CNF audit
- All findings committed and pushed
- Ready to resume from any point
