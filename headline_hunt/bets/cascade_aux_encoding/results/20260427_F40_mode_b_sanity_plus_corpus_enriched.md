# F40: Mode B sanity test + F32 corpus LM-enrichment
**2026-04-27 13:13 EDT**

Two-part hour: (1) sanity-check that Mode B (force) doesn't differ
meaningfully from Mode A (expose) for the F28 NEW CHAMPION at 1M
conflicts; (2) enrich F32 deep corpus with structural metrics for
future use.

## Part 1: Mode A vs Mode B on bit2_ma896ee41

| Mode | encoder | seed walls | median |
|---|---|---|---:|
| Mode A (expose) | cascade_aux_mode_a | 36.18, 35.41, 36.25, 35.61, 35.50 | **35.61s** (F39) |
| Mode B (force)  | cascade_aux_mode_b_force | 36.25, 31.96, 35.78, 35.00, 36.92 | **35.78s** (F40) |

**Difference: 0.17s (0.5%). Within seed noise.**

Mode B's "force" encoding (which directly enforces cascade-zeros via
clauses) does not give measurable speedup over Mode A's "expose"
encoding (which leaves them as derived constraints) on bit2 at 1M
conflicts.

This is consistent with the established per-conflict equivalence
(F30, F37, F38, F39 reaffirmed): cand-level structural variations
are invisible to kissat at moderate budgets, AND so are
encoder-level variations.

## Part 2: F32 corpus enriched with LM cost

Built `F28_deep_corpus_enriched.jsonl` from F32. Added per-(cand
min-HW record) fields:
- `cand_min_active_adders` (always 43 — F34 invariant)
- `cand_min_lm_cost` (varies 773-890 — F36 metric)
- `cand_min_max_hw_sum` (loose ceiling)
- `cand_min_lm_incompat` (always 0 — F36 universal compatibility)

Distribution across 67 cands:
- min LM: 773 (msb_ma22dc6c7)
- q1: 822
- median: 835
- q3: 852
- max: 890

All cands: 43 active adders ✓ universal (F34)
All cands: 0 LM-violators ✓ universal (F36)

The enriched corpus makes future cross-cand work (Wang trail design,
LM-vs-solver correlation studies, MILP cross-validation) trivial:

```python
import json
recs = [json.loads(l) for l in open('F28_deep_corpus_enriched.jsonl')]
mins = [r for r in recs if 'cand_min_lm_cost' in r]
# Sort by LM
mins.sort(key=lambda x: x['cand_min_lm_cost'])
# Top 5 LM-min cands
for r in mins[:5]:
    print(r['candidate_id'], r['hw_total'], r['cand_min_lm_cost'])
```

## Discipline

- 5 kissat runs logged via append_run.py (Mode B sanity)
- Mode B CNF audit: CONFIRMED sr60_n32_cascade_aux_force
- Compute: ~3 minutes total (parallel kissat + corpus enrichment)
- Idempotent: same input → same output

EVIDENCE-level: VERIFIED. Mode A ≈ Mode B at 1M conflicts (within
0.5% wall difference). Corpus enrichment is deterministic and
reproducible.

## What's solidified vs what remains hypothesis

**Solidified by F30-F40 series (verified)**:
- ✓ F34: 43-active-adder cascade-1 invariant across all 67 cands
- ✓ F36: Universal LM-compatibility (zero violators per cand)
- ✓ Per-conflict kissat equivalence (~35-36s) at 1M conflicts
  - Across cands (F37, F38, F39 reaffirmed)
  - Across encoder modes A vs B (F40 this run)
  - Across exact-symmetry vs not (F39 bit2 vs F38 plateau)
- ✓ F35/F36: LM cost varies meaningfully (90-117 bit spread)

**Hypothesis only / deferred**:
- bit2's STRUCTURAL advantage (HW=45 + symmetry) might show at DEEP
  budgets (12h+ kissat). Untested.
- Wang second-block trail feasibility (LM-min cand wins on
  carry-constraint count). Untested without trail design pilot.

## Concrete next moves

1. **DEEP-budget kissat on bit2** (4 cores × 12 hours = 48 CPU-h).
   Tests the structural-advantage-at-depth hypothesis. Needs user
   authorization for compute.
2. **Wang trail-design pilot**: pick LM-min cand (msb_ma22dc6c7),
   construct a candidate second-block trail, compute its LM cost.
   This is the actual feasibility argument for block2_wang.
3. **Cross-validate enriched corpus consumers**: build a
   `cand_select.py` script that takes (HW-weight, LM-weight) and
   returns ranked cand list. Useful for fleet coordination.
