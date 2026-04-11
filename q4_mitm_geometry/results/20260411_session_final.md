# Session Final Results: 2026-04-11 02:00-07:00 UTC

## Completed Experiments

### Near-Collision Hunt (4096 prefixes)
- **Viable**: 1 / 4096 (0.024%)
- **Best HW**: 52 / 256 (only viable prefix)
- **Runtime**: 13,357 seconds (~3.7 hours)
- Conclusion: round-61 viable prefixes are rare (~0.025%) and give
  HW≈40-52 near-collisions, NOT full collisions

### Multi-Block Absorption Frontier
| Rounds | Result | Process time |
|--------|--------|-------------|
| 16 | **SAT** | <1s |
| 17 | **SAT** | 8s |
| 18 | **SAT** | ~300s |
| 19 | TIMEOUT | 1h |
| 20 | TIMEOUT | 30min |
| 24 | TIMEOUT | 1h |

**Frontier: 18 rounds (28% of SHA-256)**. HW=40 IV diff is absorbable
through 2 schedule-constrained rounds beyond the 16 free-message rounds.

### Critical Pair at N=32
| Free bits | Best tested positions | Result |
|-----------|----------------------|--------|
| 2 | (17,19), (16,20), (17,18), (18,19), (10,17) | ALL TIMEOUT |
| 3 | (10,17,19) | TIMEOUT |
| 4 | (9,10,17,19) | TIMEOUT |
| 5 | (9,10,16,17,19) | TIMEOUT |
| 8 (error-informed) | (5,6,14,17,18,26,27,28) | TIMEOUT |
| 16 (50%) | (5,6,9,10,14,17,18,19,21,23,26,27,28,29,30,31) | **TIMEOUT** |

**N=32 needs >50% of W[60] free** to break sr=61. The critical pair
phenomenon from N=8 does NOT scale with 2 bits at N=32.

### Other Results
- Universal subspace falsified (per-prefix, 27-dim)
- Image sizes have Fermat prime factorization (3, 5, 17, 257)
- Z3 SMT too slow for cascade constraints
- CaDiCaL 6.8x slower than Kissat
- Sigma1 inverse matrix verified (GF(2) bijective)
- Same-message block 2 absorption: ALL timeout (10-16 rounds)

## Still Running
- **Bit-2 sr=60 race**: 2 Kissat, ~8.4h remaining
  M[0]=0x67dd2607, kernel=0x00000004, seeds 5 and 42

## Key Insights

1. **Cascade chain + round-61 closure** gives structured near-collisions
   (HW≈40-52) but NOT full collisions. The cert's HW=0 was found by SAT.

2. **Multi-block is structurally viable**: block 2 absorbs HW=40 through
   18/64 rounds. Wang-style techniques could extend this.

3. **The sr=61 barrier at N=32 is MUCH harder than N=8**: even 50% W[60]
   freedom (16 bits) isn't enough, vs ~50% at N=8.

4. **Near-collision anatomy**: d,h=0 (cascade), c,g≈0, errors in a,b,e,f
   concentrated at sigma1 boundary (bits 17-19 enriched 2x).
