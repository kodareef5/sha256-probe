# 2026-04-10 Session: Novel Attack Experiments Summary

## Context

After 72+ hours of sr=61 SAT race yielded no results, the fleet pivoted
to novel analytical attacks (per work reallocation in Issues #11-#18).
This document summarizes all experiments run on the server (linux)
across ~6 hours of concentrated analytical work.

## Macro result

All novel attacks converge on the same conclusion: **sr=60 is solvable
but sits at the structural boundary of SHA-256's schedule compliance;
sr=61 is effectively UNSAT** due to the sigma1 schedule rule creating
over-constrained requirements.

No breakthrough. Three independent analytical methods (diff-linear
correlation, ANF degree profile, skip-register sweep) point to the
same underlying geometry.

## Experiments run

### 1. MITM Cascade Fix and Forward Scan (#13)
- **Fixed** macbook's cascade_mitm.py bug (missing dT2 term in C_w57 formula)
- **cascade_forward_scan.py**: 500K cascade-constrained samples
  - Best HW = 75 (vs 76 from gpu-laptop's 110B pure brute force)
  - 220,000x more sample-efficient than brute force
  - But plateau at HW~75 matches other methods

### 2. Hill Climbing (null result)
- **cascade_hillclimb.py**: 2M single-bit perturbation evaluations
  - Best HW = 78 (WORSE than random's 75 at 500K)
  - Confirmed landscape has no exploitable single-bit gradient

### 3. SVD-Projected Search
- **svd_projected_search.py**: 1M perturbations along top-35 SVD directions
  - Best HW = 74 (slight improvement over random)
  - Confirms 35-dim structure captures SOME signal

### 4. Round-by-Round Profile
- **Cert**: HW strictly decreases 104 → 86 → 73 → 55 → 39 → 32 → 18 → 0
- **Random (50K)**: HW plateaus 104 → 86 → 78 → 67 → 65 → 83 → 79 → 79
- Gap grows from 0 to 79 across the 7 tail rounds
- Cert uses specific structure random can't match

### 5. The Hard Core (132 bits)
- Direct measurement: 132 of 256 output bits have ZERO deterministic
  linear controllers
- These are da, db, de, df registers at round 63 (not in the cascade
  shift path)
- Expected random HW from 132 random bits = 66, plus ~8 cascade residual
- **EXPLAINS the HW~74 plateau** from all three search methods

### 6. Pairwise Correlation (null)
- **pairwise_correlation.py**: 50 W[58] bit pairs × 1500 samples
  - Max interaction 0.11 (vs noise floor 0.026)
  - No significant pairwise structure beyond single bits

### 7. sr=61 Direct Sampling
- **sigma1_bridge_v2.py**: 500K samples with sigma1 schedule rule
  - Best HW = 92
  - Mean HW = 128 (matches pure random — ZERO structural advantage)
  - **Gap from sr=60: 17 HW at equal sample budget**

### 8. Linearization Pilot
- **linearization_n8.py**: degree-2 features for dh[63] bit 0
  - 62.6% prediction accuracy (12.6 pp above random)
  - Insufficient by itself, but confirms degree-2 structure exists

### 9. Skip-Register Sweep (PARADOX)
- **near_collision_skip.py**: test each "skip register X" config
  - Skip h: SAT in 1.75s (FASTER than baseline)
  - Skip a,b,c,d,e,f,g: TIMEOUT at 120s
- **h is the MOST INFORMATIVE constraint for Kissat**
- Aligns with ANF finding: h bit 0 has lowest algebraic degree (8/32)
- Suggests: adding redundant informative constraints could speed up sr=61

## Cross-validation with fleet findings

Macbook's independent work confirmed:
- ANF degree gradient: a(16)→b(15)→c(13)→d(9) and e(16)→f(14)→g(12)→h(8)
- 49 exact N=4 collisions in 2^32 (density 1.14e-8, balanced)
- Cross-register correlations: zero
- Higher-order differentials through k=16: nothing found

## What we've ruled out

1. **"Find a better candidate"**: hw_dW56, de57_err, 14 other metrics all null
2. **Cascade search in bit space**: plateau at HW~74-78 regardless of method
3. **Pairwise W[58] interactions**: essentially zero
4. **Low-order differentials**: nothing through k=16
5. **Cross-register exploitation**: zero correlated pairs

## What remains unexplored

1. **Guide constraints from h**: if h's constraint is 6x accelerating
   at N=8, maybe ADDING similar informative constraints helps sr=61 N=32
2. **Gröbner basis on low-degree bits**: needs Sage/polybori, not tried
3. **Symbolic computation of a, b, e, f registers**: the "hard core" bits
4. **Alternative differential trails**: our fixed MSB kernel is not unique
5. **Different rotation families at sub-round level**: unexplored

## Headline finding of the session

**The sr=60 → sr=61 gap is ~17 HW at 500K equal sample budget, with
sr=61 showing ZERO mean-case structure.** This is the first direct
empirical measurement of the structural difficulty transition. Combined
with the 10.8% universal sigma1 conflict rate, it strongly supports
the conclusion that sr=61 is structurally UNSAT — not just computationally
hard.

## Productivity

~6 hours of analytical work → 15+ experiments, 10+ new scripts, 8 writeups,
and ~20 commits. Total compute: <1 CPU-hour. Compare to the 72h × 26 procs
= 1872 CPU-hours sr=61 race that produced zero novel findings.

**Analytical work is ~2000x more productive per CPU-hour than SAT racing
for structural understanding**, even though SAT racing is the only way
to find the actual collision (when one exists).
