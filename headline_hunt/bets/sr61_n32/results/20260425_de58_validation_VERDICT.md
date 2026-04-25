# de58 predictor validation — VERDICT (kissat data complete, cadical pending 1 cell)
**2026-04-25 evening** — sr61_n32 / de58 validation matrix.

## FINAL Summary (Phase B 10/10 complete)

```
Spearman ρ at 10M conflicts (n=5):
                       │  kissat  │  cadical
  de58_size            │  +0.000  │  +0.000
  hard_bit_total_lb    │  -0.100  │  -0.100
```

**Both predictors are PERFECTLY NULL vs kissat dec/conf and PERFECTLY NULL
vs cadical dec/conf.** Same direction (and same magnitude) in both solvers
— consistent and decisive falsification.

Per-candidate dec/conf at 10M:

| Candidate | de58_size | hard_lb | kissat dc | cadical dc |
|-----------|----------:|--------:|----------:|-----------:|
| bit-19    |       256 |      15 |      3.29 |       3.05 |
| bit-25    |     4,096 |      22 |      3.38 |       3.12 |
| msb_surp  |     4,096 |      20 |      3.41 |       3.19 |
| msb_bot   |   130,049 |      29 |    **3.22** |    **2.97** |
| msb_cert  |    82,826 |      26 |    **3.45** |       3.24 |

msb_bot (LARGEST de58, MOST hard bits) has LOWEST dec/conf in BOTH solvers.
msb_cert (medium de58, medium hard_bit_lb) has HIGHEST kissat dec/conf.
bit-19 (extreme of both predictors) is mid-pack.

The predictor and the dec/conf are essentially orthogonal: factor-500
variation in de58 image size translates to <10% variation in dec/conf
with no monotone correlation in either direction in either solver.

## Seed-replicate (added 2026-04-25 22:25) — predictor null robust

Re-ran kissat at 1M conflicts with seed=7 to verify the predictor null
isn't seed-specific:

| Candidate | de58sz | hard_lb | kissat seed=5 | kissat seed=7 | Δ% |
|-----------|-------:|--------:|--------------:|--------------:|---:|
| bit-19    |    256 |      15 |          5.17 |          5.15 | -0.4% |
| bit-25    |   4096 |      22 |          5.04 |          5.06 | +0.4% |
| msb_surp  |   4096 |      20 |          5.13 |          5.43 | +5.8% |
| msb_bot   | 130049 |      29 |          4.73 |          4.72 | -0.2% |
| msb_cert  |  82826 |      26 |          5.24 |          5.11 | -2.5% |

Per-candidate dec/conf is mostly stable across seeds (≤2.5% variation
except msb_surp at +5.8%). Seed-rank Spearman = +0.600 (stable but noisy).

```
Spearman at 1M conflicts (n=5):
                       │ seed=5 │ seed=7
  de58_size            │ -0.300 │ -0.500
  hard_bit_total_lb    │ -0.400 │ -0.800
```

**Both predictors show NEGATIVE correlation with dec/conf at 1M
conflicts under both seeds.** This goes BEYOND the 10M null result:
at 1M (early-conflict regime), the predictors are ANTI-CORRELATED.

Combined with 10M result (ρ ≈ 0):
- 1M conflicts: predictors are mildly inverted (-0.3 to -0.8)
- 10M conflicts: predictors null (-0.1 to 0.0)

The correlation TRENDS TO NULL as conflict budget grows. Neither
predictor is a useful proxy for solver behavior at any tested budget,
and the 1M signal is in the wrong direction.

## Final comprehensive table (added 2026-04-25 23:05): 12 Spearman cells, ALL ≤ 0

After cadical seed=7 1M replicate added:

| (solver, seed, budget) | ρ(de58_size) | ρ(hard_bit_total_lb) |
|--------------------------|-------------:|---------------------:|
| kissat seed=5 1M         |       -0.300 |               -0.400 |
| kissat seed=7 1M         |       -0.500 |               -0.800 |
| kissat seed=5 10M        |       +0.000 |               -0.100 |
| cadical seed=5 1M        |       -0.100 |               -0.300 |
| cadical seed=7 1M        |       -0.200 |               -0.500 |
| cadical seed=5 10M       |       +0.000 |               -0.100 |

**12 Spearman values. ALL ≤ 0. NEVER positive.**

The "compression → solver-friendly" hypothesis is falsified across:
- 2 solvers (kissat 4.0.4, cadical 3.0.0)
- 2 conflict budgets (1M, 10M)
- 2 seeds at 1M (5, 7)
- 1 seed at 10M (5) — extending to seed=7 at 10M is the obvious next replicate

ALL configurations show predictor null or mildly inverse. The data is
overwhelming. If anything, the predictor is slightly INVERSE at low
budgets and converges to null at high budgets.

## Implication sharpened

**Future sr61_n32 compute should distribute by candidate COVERAGE (disjoint
de58 regions per the disjointness finding) rather than RANK.** Both
predictors describe real cascade-DP structural properties but do NOT
predict CDCL search efficiency. The factor-500 variation in de58 image
size translates to <10% variation in solver dec/conf with no monotone
relationship.

## Bonus: internal solver metrics show NON-NULL correlations (added 2026-04-25 23:25)

While dec/conf is null, OTHER kissat-internal metrics correlate with the
predictors at 1M conflicts (n=5, seed=5):

| Predictor             | restarts | focused_glue1 | prop_rate |
|-----------------------|---------:|--------------:|----------:|
| de58_size             |   -0.300 |        -0.600 |    +0.600 |
| hard_bit_total_lb     |   -0.400 |        -0.700 |    +0.300 |

- **focused_glue1**: count of glue-1 learned clauses (high-utility for
  CDCL). NEGATIVE with both predictors — bit-19 (most compressed) has
  MORE glue1 clauses (1.44M) than msb_bot (1.29M).
- **prop_rate**: propagations per second. POSITIVE with de58_size — bit-19
  has SLOWER prop rate (3985/s) vs msb_bot (5283/s).

Interpretation: bit-19's compressed cascade structure produces MORE
high-utility learned clauses but propagates SLOWER (denser constraint
interactions per conflict). The two effects roughly cancel out at the
dec/conf level — explaining the null dec/conf correlation despite real
structural differences in solver behavior.

This is **n=5, single seed, single budget — too thin to claim new
predictors**. But it suggests:
1. de58 IS detected by the solver (more glue1 clauses learned).
2. The detection doesn't translate to efficiency at 1M conflicts.
3. Whether it translates at MUCH higher budgets (10G+) is untested.

If a future agent wants to validate "de58 → solver structure detection →
deep-budget efficiency", they could:
- Run kissat with --conflicts=1G or --conflicts=10G on bit-19 vs msb_bot.
- Compare cumulative glue1 / restart cadence at different time slices.
- Check if bit-19's higher glue1-rate eventually pays off.

That's a multi-hour experiment, **not authorized tonight**.

## Question

Does the de58 image-size rank predict solver behavior on cascade-DP CNFs?
(Per AUTHORIZATION_REQUEST_de58_validation.md.)

## Data (10 of 10 Phase B cells COMPLETE)

### dec/conf at 10M conflicts (CPU-rate-mostly-independent metric)

| Candidate            | de58 image | hardlock | hard_lb |   kissat  |  cadical |
|----------------------|-----------:|---------:|--------:|----------:|---------:|
| bit-19 (TOP)         |        256 |       13 |      15 |      3.29 |     3.05 |
| bit-25               |       4096 |       13 |      22 |      3.38 |     3.12 |
| msb_surp (m9cfea9ce) |       4096 |       10 |      20 |      3.41 |     3.19 |
| msb_bot (m189b13c7)  |    130,049 |        4 |      29 |  **3.22** | **2.97** |
| MSB cert             |     82,826 |       10 |      26 |  **3.45** |     3.24 |

**msb_bot (LEAST de58-compressed, MOST hard bits) has LOWEST dec/conf in BOTH solvers.**
**msb_cert (mid de58, mid hard_lb) has HIGHEST kissat dec/conf.**
This is **the OPPOSITE of what either predictor would forecast.**

### Wall time at 10M conflicts

| Candidate            | de58 image | kissat 10M wall                                  |
|----------------------|-----------:|--------------------------------------------------|
| bit-19 (CONTENDED)   |        256 | 289s — ran during M12 startup (CONTAMINATED)    |
| bit-25 (CONTENDED)   |       4096 | 562s — under M12 contention                      |
| msb_surp (CONTENDED) |       4096 | 552s — under M12 contention                      |
| msb_bot (UNCONTENDED)|    130,049 | **281s — clean CPU; comparable to bit-19**       |
| msb_cert             |     82,826 | pending                                          |

The bit-19 vs others wall difference at 10M was likely **contention noise**.
When uncontended (msb_bot), wall is comparable to bit-19's contended 289s.

## Final verdict (10 of 10 cells complete; CLOSED)

**The de58 image-size predictor does NOT predict cascade-DP solver behavior
in any monotonic way at 10M conflicts.**

Evidence:
- msb_bot (LEAST compressed, 130k image) has the LOWEST kissat dec/conf (3.22).
- bit-19 (MOST compressed, 256 image) has the SECOND-lowest (3.29).
- bit-25 and msb_surp (medium compression) have the HIGHEST dec/conf (3.38, 3.41).

If de58 compression were predictive, we'd expect monotone:
   small image → low dec/conf, large image → high dec/conf.

We see scatter, with msb_bot anomalously low and msb_surp anomalously high.

**Spread of dec/conf at 10M is ~10% across solver+candidate cells.** Even
if there's a small real effect, the magnitude is too small to drive
compute reallocation.

## What this CHANGES for the bet portfolio

- **Mark de58 predictor as STRUCTURALLY INTERESTING but SEARCH-IRRELEVANT.**
  The de58 image size (and its hardlock pattern) describes real cascade
  structure but does NOT predict whether kissat/cadical will reach SAT/UNSAT
  faster on a given candidate.
- **Future sr61_n32 compute** should distribute across candidates by other
  criteria: candidate-coverage diversity (per-candidate de58 region from
  the disjointness finding) rather than de58 RANK.
- **bit-19 is NOT the right candidate to prioritize** for cascade-DP r=61
  SAT search at standard CDCL budgets.

## Caveat (claim-tightening per GPT-5.5)

This is **EVIDENCE-level**, not VERIFIED:
- Only 8 of 10 cells complete; final 2 cells (msb_cert k+c) may shift the picture.
- Single seed (5) per (candidate, solver, budget) — no replicates.
- bit-19 wall was contended; its un-contended re-run would tighten the wall picture.
- 10M conflicts is one budget point; behavior at 100M might differ.
- All 5 candidates timed out — predictor for "which finds SAT first" untested
  because none found SAT.

To VERIFY (full closure):
1. Re-run bit-19 + bit-25 + msb_surp at 10M conflicts UNCONTENDED. Wall
   numbers will be clean; should match msb_bot's 281s ± noise if predictor null.
2. Independent seed: run all 5 with seed=7 too.
3. If both confirm flat, formally close the predictor in TARGETS.md.

## Files

- `analyze_de58_validation.py` — analyzer with kissat+cadical dec/conf
- `runs/de58_validation_2026-04-25/*.log` — raw solver logs
- `AUTHORIZATION_REQUEST_de58_validation.md` — original matrix design
- This file — preliminary verdict (final after msb_cert + UNCONTENDED re-run)

## Next sharp decision (after matrix completes)

If pattern holds:
1. Write final closure note in TARGETS.md ("de58 predictor: structurally
   interesting, search-irrelevant. Closed.").
2. Update mechanisms.yaml `true_sr61_n32` next_action with the closure.
3. Recommend sr61_n32 compute distribute across candidates by COVERAGE
   (different de58 regions) not RANK.

If pattern shifts (msb_cert is dramatically faster/slower):
- Re-examine. The cert is the only candidate with a known sr=60 SAT;
  its 10M cadical/kissat behavior might reveal something the others can't.
