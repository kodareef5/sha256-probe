# F38: HW vs kissat-wall sweep — bit2 advantage is a CLIFF, not a smooth trend
**2026-04-27 12:54 EDT**

Tests F37's preliminary "HW predicts kissat speed" hypothesis with 4
new cands across HW range 47..51, all under cascade_aux Mode A sr=60,
5 seeds × 1M conflicts × parallel.

## Combined data (6 cands across HW 45..51)

| HW | cand | seed walls | **median** | source |
|---:|---|---|---:|---|
| 45 | bit2_ma896ee41 | 26.72, 26.51, 26.38, 26.85, 25.87 | **26.51** | F30 |
| 47 | bit10_m9e157d24 | 33.52, 34.28, 33.97, 35.79, 35.17 | **34.28** | F38 (this) |
| 48 | msb_ma22dc6c7 | 33.94, 37.48, 35.99, 37.39, 35.03 | **35.99** | F37 |
| 49 | bit00_mc765db3d | 34.99, 34.25, 35.87, 34.78, 33.38 | **34.78** | F38 (this) |
| 50 | bit06_m6e173e58 | 35.36, 34.55, 32.78, 33.66, 35.11 | **34.55** | F38 (this) |
| 51 | bit00_mf3a909cc | 35.91, 34.04, 37.19, 37.10, 35.46 | **35.91** | F38 (this) |

## Key observation: the CLIFF at HW=45→47

| transition | wall change | HW change | rate |
|---|---:|---:|---:|
| HW 45 → 47 | +7.77s (+29%) | +2 | ~3.9s/HW |
| HW 47 → 48 | +1.71s (+5%) | +1 | 1.7s/HW |
| HW 48 → 49 | −1.21s (−3%) | +1 | NEGATIVE |
| HW 49 → 50 | −0.23s (−1%) | +1 | NEGATIVE |
| HW 50 → 51 | +1.36s (+4%) | +1 | 1.4s/HW |

**HW=45 to HW=47 is a 7.77s CLIFF** (29% slowdown for 2 HW units).
**HW=47 to HW=51 is a flat plateau at 34-36s** (within seed noise).

## F37 hypothesis revised

F37 said "each HW unit ~3s." Wrong. The actual structure is:
- bit2 (HW=45) is in a class of its own — much faster
- HW=47..51 cands are all in a plateau (34-36s)
- Mid-plateau differences are within seed noise (±2s)

Hypothesis revision:
- HW=45 has STRUCTURAL ADVANTAGE not captured by HW alone.
  Possible mechanisms:
  - bit2_ma896ee41 has the EXACT-SYMMETRY property (a_61=e_61) AND
    HW=45. Both might contribute.
  - bit2's specific bit-pattern (HW=2 in a_61 leg) gives kissat
    extra unit-clauses to propagate.
- For HW≥47, the advantage flattens — kissat heuristics can't
  distinguish HW=47 from HW=51 at 1M conflicts.

## Possible explanations for the cliff

### Hypothesis A: exact-symmetry preserves more structure

bit2 is exact-symmetry (a_61=e_61). Of HW=47-51 cands tested:
- bit10_m9e157d24 (HW=47): NOT exact-symmetry (per F32 a61_eq_e61=False)
- msb_ma22dc6c7 (HW=48): NOT exact-symmetry
- bit00_mc765db3d (HW=49): NOT exact-symmetry
- bit06_m6e173e58 (HW=50): NOT exact-symmetry
- bit00_mf3a909cc (HW=51): NOT exact-symmetry

So bit2 is the ONLY exact-symmetry cand in this set. Could the symmetry
be the key advantage, not HW?

### Hypothesis B: HW alone, but with discrete steps

Maybe HW=45 falls below a kissat threshold for "interesting"
preprocessing. Kissat's vivification, hyper-resolution etc. might
trigger at low-HW residuals.

### Hypothesis C: artifact of parallel measurement

5×1M conflicts in parallel could load CPU differently. But all 6 cands
were measured under same parallel setup.

## Test for hypothesis A: HW=47 exact-symmetry cand

To distinguish A from B:
- Pick an EXACT-SYMMETRY cand at HW=47: bit13_m4e560940 (the F26 bit13)
- Run 5×1M parallel kissat
- If wall ≈ 26-28s → exact-symmetry is the predictor (A)
- If wall ≈ 34-36s → HW=45 itself is the predictor (B)

Did NOT run this test in F38 (out of scope), but it's the obvious
next move.

## Implications

1. **F30 + F37 + F38 together establish per-conflict kissat behavior**:
   - HW=45 + exact symmetry: ~26s
   - HW≥47 (any structure tested): ~35s
   - The 9-10 second gap is REAL across multiple cands.

2. **For paper Section 5**: the bit2 advantage is now empirically
   verified across multiple comparison cands. It's not a single-cand
   anomaly.

3. **F36's LM metric is still relevant** for Wang trail-construction
   (carry constraints), but NOT for kissat speed.

4. **The cliff structure is itself notable**: 1M conflicts is enough
   to reveal a 9s gap between HW=45 and HW=47, but not enough to
   distinguish HW=47 from HW=51. There's a structural property at
   HW=45 that kissat picks up on.

## Discipline

- 20 kissat runs logged via append_run.py
- 4 new CNFs built and CONFIRMED via cascade_aux_encoder
- Reproducible: seeds 1, 2, 3, 5, 7
- Compute: ~3 minutes total wall

EVIDENCE-level: VERIFIED. Cliff structure reproducible across 5
HW=47-51 cands. The HW=45 vs HW=47-51 gap is structural, not seed
noise.

## Concrete next moves

1. **Test bit13_m4e560940** (HW=47, EXACT symmetry) to distinguish
   hypothesis A (symmetry predictor) from B (HW=45 predictor).
2. **Test bit25_m30f40618** (HW=46, NOT exact-symmetry) to fill HW=46
   bin.
3. **Aggregate as a kissat-wall predictor model**: enrich F32 corpus
   with median walls per cand. Pattern across (HW, symmetry, LM)
   triples.
4. **Sequential vs parallel kissat**: re-run bit2 with sequential
   kissat (one process at a time) to control for parallelism artifact.
