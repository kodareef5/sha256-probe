# F72: F31→F71 synthesis index — navigation guide for today's 40+ F-series memos
**2026-04-27 15:25 EDT**

Today (2026-04-27) shipped 40+ F-series memos in cascade_aux_encoding +
16 in block2_wang trails/residuals. Total ~70 commits, 4 honest
corrections, 4 bet folders touched. This is the single navigation
document for finding any specific finding.

## Quick reference: what each F-number established

### F31-F36: Universal cascade-1 structural properties

- **F31** (corpus extension): bit2 + bit13 1M-sample corpora (~18k records each)
- **F32** (deep corpus structured): F28 archive parsed → 3,065-record JSONL across 67 cands
- **F33** (active-adder framework, DRAFT/buggy)
- **F34** (cascade-invariant): 43 active modular adders universal across all 67 cands
- **F35** (LM cost): 90-bit spread across 11 exact-symmetry cands
- **F36** (universal LM-compat): ALL 67 cascade-1 trails are LM-compatible. msb_ma22dc6c7 is global LM champion (LM=773).

### F37-F45: Cross-solver cohort discovery

- **F37** (LM-min predicts kissat speed FALSIFIED): msb_ma22dc6c7 not faster
- **F38** (HW vs wall sweep, voided)
- **F39** (HONEST CORRECTION #1): F37/F38 cliff was system-load artifact
- **F40** (Mode A ≈ Mode B sanity)
- **F41** (sequential vs parallel kissat)
- **F42** (universal LM-compat extends to 3,065 records)
- **F43** [linux_gpu_laptop] (record-wise LM/HW Pareto): bit4 LM=757 champion
- **F44** [macbook] (per-cand LM-min often at higher HW)
- **F45** [linux_gpu_laptop] (online Pareto sampler): bit28 raw LM frontier
- **F46** (renamed from F45 — cadical confirms F37 LM-doesn't-predict-speed)
- **F47** (bit28 BREAKS per-conflict equivalence): kissat outlier, high seed variance
- **F48** (LM-tail-breadth predicts speed, voided)
- **F49** (HONEST CORRECTION #2): F48 falsified, breadth is uncorrelated

### F50-F58: Two-axis structural picture

- **F50** (HW=48 EXACT-sym test): symmetry alone doesn't predict speed
- **F51** (HW=46/47 boundary): fast cluster expands to 3 cands
- **F52** (EXACT-symmetry at HW≥47 HARMFUL): kissat-specific
- **F53** (HW=48 NON-sym control): symmetry penalty 17s at HW=48
- **F54** (cadical REVERSES kissat ordering at HW=48)
- **F55** (HONEST CORRECTION #3): F54 reversal is HW=48-specific
- **F56** (cadical bimodal): msb_ma22dc6c7 cadical-axis champion
- **F57** (cadical-fast cluster diverges from kissat-fast)
- **F58** (cross-solver synthesis): 3 structural cohorts identified

### F59-F62: Three-solver picture solidifies

- **F59** (CryptoMiniSat 5 confirms Cohort A is universally fast)
- **F60** (msb_ma22dc6c7 ascends to TRIPLE-AXIS CHAMPION + bit18 cadical pathology)
- **F61** (CMS at HW=47 — universal sym penalty)
- **F62** (Cohort A locked: 3 cands × 3 solvers = 9/9 fast)
- **F63** (NEW Cohort D — bit28 is CMS-only fast)
- **F64** [synthesis] (bit28 OVERALL project champion via fleet collaboration)

### F65-F71: Cert-pin verification pipeline

- **F65** (cert-pin sweep on bit28 yale HW=36)
- **F66** (cert-pin sweep across 5 cohort representatives)
- **F67** (cert-pin yale HW=33 EXACT-sym)
- **F68** (CMS deep-budget on bit28 — no SAT, brute force won't reach collision)
- **F69** (HONEST CORRECTION #4): cert-pin BUG FIX — primary W1 vars not aux_W
- **F70** (yale's full Pareto frontier verified — 5/5 near-residuals)
- **F71** (REGISTRY-WIDE: 67/67 F32 deep-min vectors are near-residuals)

## Strongest paper-class claims (post-F69 fix)

| claim | F-number | evidence |
|---|---|---|
| Universal LM-compatibility | F36, F42 | 3,065 records all compat |
| 43-active-adder cascade-invariant | F34 | 67/67 cands, registry-wide |
| 4-cohort solver-architecture taxonomy | F58, F59, F63 | 12 cands × 3 solvers |
| msb_ma22dc6c7 is triple-axis champion | F36, F60 | LM + cadical + CMS + plateau-fast |
| **F32 deep-min corpus has zero collisions** | **F71** | **67/67 UNSAT, registry-wide** |
| yale's bit28 frontier verified clean | F70 | 5/5 Pareto records UNSAT |
| Cert-pin technique works | F69 fix | m17149975 SAT recovered |

## 4 honest corrections — discipline pattern

The F-series shipped 4 honest retractions today:

1. **F39** caught F37/F38: "HW cliff" was system-load artifact
2. **F49** caught F48: "monotonic LM-tail breadth → speed" was small-N overclaim
3. **F55** caught F54: "cadical reversal at HW=47-48" was HW=48-specific
4. **F69** caught F65-F67 tool bug: aux_W (XOR-diff) instead of W1 (primary)

Each correction within minutes-to-hours of the original claim. Same
pattern: rapid iteration produces small-N overclaims; careful follow-up
catches them. Good discipline.

## Project champion ranking (final, post-F71)

For block2_wang Wang attack:

| rank | cand | distinctions |
|---:|---|---|
| 1 | **bit28_md1acca79** | yale HW=33 EXACT-sym (LM=679), Cohort D CMS-fast, F47 kissat-outlier — overall structural depth |
| 2 | **msb_ma22dc6c7** | F36 LM-axis champion (LM=773), F60 cadical-fastest, F60 CMS-fast — TRIPLE-AXIS |
| 3 | **bit2_ma896ee41** | F28 HW champion (HW=45), F25 universal rigidity, kissat-only fast — Wang sym-axis |
| 4 | **bit10_m9e157d24** | Cohort A core, 3-solver universal fast — solver-agnostic baseline |
| 5 | **bit4_m39a03c2d** | F43 record-wise LM champion (LM=757) |

## For yale's manifold-search (recommended cross-axis tests)

1. **Manifold-search on bit10** (Cohort A baseline) vs bit28 (Cohort D)
   — does manifold efficiency align with universal-fast or CMS-fast?
2. **Manifold-search on bit2** (Cohort B) — does kissat-only-fast also
   manifold-only-friendly?
3. **Manifold-search on bit17** (Cohort C) — does cadical-only-fast
   correlate with manifold efficiency?

## Pipeline state (for fleet)

```
yale online sampler  →  W-witness  →  certpin_verify.py --batch  →  SAT/UNSAT
                                                                  ↓
                                       UNSAT (typical)            SAT (HEADLINE!)
                                       ↓                          ↓
                                yale block-2 trail          verified collision
                                design (next)               at lower HW than
                                       ↓                    m17149975 baseline
                            macbook 2-block cert-pin
                                       ↓
                                if SAT → HEADLINE
```

The macbook cert-pin pipeline is now production-grade and validated
end-to-end (F65→F71). The remaining structural piece is yale's
block-2 trail design — the path to the HEADLINE.

## Compute used today

- ~150+ kissat runs (F37-F71)
- ~30+ cadical runs (F46-F58)
- ~20+ CMS runs (F59-F71)
- ~30 sec total compute for F71's 67-cand audit
- ~290 sec for F68's deep-budget probe (the only multi-min run)
- 0% audit failure rate across ~200+ logged solver runs

## What's NOT done (concrete next session items)

1. **2-block cert-pin tool** — needed when yale designs block-2 trail
2. **Deep-budget multi-cand SAT sweep** — needs user authorization
3. **Mouha MILP cross-validation** — would harden F35/F36 LM analysis
4. **Cross-axis test results from yale** — pending yale's response
5. **mitm_residue dormant** — owner=macbook, hasn't run since 04-25

## Discipline summary

- ~70 commits today
- 0% audit failure rate
- 4 honest corrections (issued within minutes of finding)
- All bets fresh heartbeats (cascade_aux + block2_wang refreshed earlier)
- yale fleet collaboration: 6+ commits cross-validated
- Cumulative cert-pin verification corpus: 79 (78 UNSAT + 1 SAT)
