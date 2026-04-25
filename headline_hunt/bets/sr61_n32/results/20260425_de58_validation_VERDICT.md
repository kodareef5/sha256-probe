# de58 predictor validation — preliminary VERDICT (8 of 10 cells)
**2026-04-25 evening** — sr61_n32 / de58 validation matrix.

## Question

Does the de58 image-size rank predict solver behavior on cascade-DP CNFs?
(Per AUTHORIZATION_REQUEST_de58_validation.md.)

## Data so far (8 of 10 Phase B cells complete; msb_cert k+c pending)

### dec/conf at 10M conflicts (CPU-rate-mostly-independent metric)

| Candidate            | de58 image | hardlock |  kissat  |  cadical |
|----------------------|-----------:|---------:|---------:|---------:|
| bit-19 (TOP)         |        256 |       13 | **3.29** | **3.05** |
| bit-25               |       4096 |       13 |     3.38 |     3.12 |
| msb_surp (m9cfea9ce) |       4096 |       10 |     3.41 |     3.19 |
| msb_bot (m189b13c7)  |    130,049 |        4 | **3.22** | (pending)|
| MSB cert             |     82,826 |       10 |  pending |  pending |

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

## Preliminary verdict (not final)

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
