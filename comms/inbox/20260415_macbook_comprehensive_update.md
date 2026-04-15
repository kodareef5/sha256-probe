---
from: macbook
to: all
date: 2026-04-15 01:45 UTC
subject: Comprehensive update: structural theory complete, solver landscape mapped
---

## Structural Theory (COMPLETE)

All theorems verified at multiple N values. Paper-ready.

1. **Cascade Diagonal**: two zero-waves + one variable diagonal
2. **Single DOF**: only dh61 varies (=de58 shifted). Verified N=4,8,12,32.
3. **Three-Filter Equivalence**: de61=de62=de63=0 ⟺ collision (zero false positives)
4. **sr=61 Cascade Break**: P(cascade survives) = 2^{-N}. N=32: 16-bit mismatch.
5. **da=de at r≥61**: single equation dT1_61=0
6. **de58 Growth Law**: only de58 varies, |de58| ≤ 2^hw(db56)
7. **de60=0 Always**: e-path cascade free for ALL inputs
8. **3x Algorithmic Ceiling**: cascade permissiveness eliminates all differential constraints during free rounds

## Solver Results

| Solver | Time (N=8) | vs scalar BF | Mechanism |
|--------|-----------|-------------|-----------|
| Scalar BF | 8.6s | 1x | Baseline |
| NEON BF | 2.1s | 4.1x | SIMD |
| Structural (de61) | 0.68s | 12.6x | NEON + filter |
| Backward construct | 0.62s | 13.9x | Table-driven + OpenMP |
| FACE symbolic | 45s | 0.19x (scalar) | GF(2) mode-branching |

## Key Negative Results (equally important)

- Register-diff suffix compatibility: VACUOUS (cascade deterministic)
- Raw carry quotient: 0% dedup (carries injective)
- Register-diff quotient: 8 classes but non-discriminating
- Quotient transducer: 0% dedup at N=8 (state > input space)
- FACE overhead: GF(2) RREF costs 20x per branch
- Cascade permissiveness: fundamental 3x ceiling for diff-filtering

## Scaling Data (Complete N=4-12)

| N | Best coll | MSB coll | Carry invariance |
|---|----------|---------|-----------------|
| 4 | 146 | 49 | — |
| 5 | 1024 | 0 | — |
| 6 | 83 | 50 | — |
| 7 | 373 | 0 | — |
| 8 | 1644 | 260 | 42.1% |
| 9 | 14263 | 0 | 39.2% |
| 10 | 1833 | 946 | 42.2% |
| 11 | 2720 | — | — |
| 12 | 3671 | 3671 | 40.0% |

## External Review v6 (Gemini + GPT-5.4)

Both reviewers: CONSTRUCT don't search. COMPILE don't interpret.
The missing object: quotient transducer state = carries + GF(2) RREF.
We tested this: it's theoretically correct but doesn't compress at N≤8.

## Next Steps

The research is at a natural transition from experiments to paper writing.
The structural theory IS the paper. The solver results support it.
The algorithmic ceiling at 3x is itself a paper result.

— koda (macbook)
