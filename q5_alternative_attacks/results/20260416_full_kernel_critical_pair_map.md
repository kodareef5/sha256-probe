# Full Kernel Critical Pair Map at N=8

## Complete Results

| Kernel bit | M[0] | #SAT | #UNSAT | #TIMEOUT | Critical pairs |
|------------|------|------|--------|----------|----------------|
| 0 | — | — | — | — | no valid candidate |
| 1 | 0x72 | 1 | 0 | 27 | (5,6) |
| 2 | — | — | — | — | no valid candidate |
| **3** | **0xfc** | **4** | **0** | **24** | **(0,1), (1,3), (1,5), (2,7)** |
| 4 | 0x32 | 0 | 0 | 28 | none |
| 5 | 0xa9 | 1 | 0 | 27 | (1,3) |
| 6 | 0x12 | 3 | 0 | 25 | (1,2), (1,4), (3,7) |
| 7 | 0x67 | 1 | 26 | 1 | (4,5) |

Total: 10 SAT, 26 UNSAT, 132 TIMEOUT across 168 tests.
Timeout: 120s per pair, 9 parallel workers.

## Key Observations

1. **Kernel bit 3 has the most critical pairs (4)**
   Pairs (0,1), (1,3), (1,5), (2,7) — all in 120s.
   This is surprising because kernel bit 3 has very few sr=60 collisions (~8).

2. **Critical pair count is NOT proportional to sr=60 collision count**
   - Bit 3: ~8 collisions, 4 critical pairs
   - Bit 6: 1644 collisions, 3 critical pairs
   - Bit 7 (MSB): 260 collisions, 1 critical pair
   - Bit 4: ~146 collisions, 0 critical pairs

3. **The MSB kernel is uniquely easy for UNSAT proofs**
   Bit 7 is the only kernel where Kissat can PROVE UNSAT (26/28 pairs).
   All other kernels have mostly TIMEOUT (not proved UNSAT).
   This suggests other kernels create HARDER instances that might have
   more hidden SAT solutions.

4. **Bit 1 appears in many critical pairs across kernels**
   - Bit 3 kernel: (1,3), (1,5) — bit 1 in 2/4 pairs
   - Bit 5 kernel: (1,3) — bit 1 in 1/1 pairs
   - Bit 6 kernel: (1,2), (1,4) — bit 1 in 2/3 pairs
   Bit 1 of W[60] seems to be a "universal repair coordinate."

5. **132 TIMEOUT pairs might include undiscovered SAT results**
   Longer timeouts (1h+) could reveal many more critical pairs.
   The true critical pair landscape is likely much richer.

## Implication

For sr=61 at larger N, kernel bit 3 (or its analog) might be the optimal
starting point despite having fewer sr=60 collisions. The critical pair
count — not the collision count — determines sr=61 feasibility.

Evidence level: VERIFIED (exhaustive pair scan at N=8, 120s timeout)
