# Structurally-aware hill-climb does NOT break the HW plateau

## What I tried

The mitm_residue structural picture (4 modular d.o.f. at r=63, R63.1 and R63.3 constraints) suggested a potentially smarter scoring function for hill-climb on W[57..60]:

- **raw**: HW(da) + HW(db) + HW(dc) + HW(de) + HW(df) + HW(dg) — sum over all 6 active registers (modular). Naive.
- **free4**: HW(da) + HW(db) + HW(dc) + HW(df) — sum over the 4 free moduli only.
- **hybrid**: HW(da) + HW(db) + 2·HW(dc) + HW(de) + HW(df) — raw with 2× weight on dc since it pins dg=dc by R63.1.

Hypothesis: hill-climb under `free4` or `hybrid` might find lower-HW residuals because the metric correctly accounts for the 4-d.o.f. structure of the residual variety.

## Results (priority candidate, 200k steps × 5 restarts each)

| metric | restart-best (under metric) | raw-equivalent HW | best raw HW | elapsed |
|---|---|---|---:|---:|
| raw     | [65, 73, 72, 68, 70] | [65, 73, 72, 68, 70] | **65** | 40s |
| free4   | [46, 45, 49, 47, 49] | [83, 71, 75, 74, 77] | 71 | 41s |
| hybrid  | [65, 73, 72, 68, 70] | [65, 73, 72, 68, 70] | **65** | 41s |

**Best raw HW across all modes and restarts: 65** (vs random sampling's 58-62 minimum from build_corpus.py).

Hill-climb under structural-aware metrics does NOT outperform random sampling under the raw metric. The plateau persists.

## Why hybrid doesn't help

The hybrid metric weights HW(dc) at 2× to account for dc=dg coupling. In principle, this should bias the search toward states with lower dc HW, which would automatically reduce dg HW. Empirically, the search trajectory under hybrid is IDENTICAL to raw — the 2× weighting doesn't break ties differently because the local moves around the plateau already optimize HW(dc) implicitly through the raw metric.

## Why free4 makes raw HW worse

free4 optimizes HW(da) + HW(db) + HW(dc) + HW(df) only — it IGNORES HW(de) and HW(dg). The hill-climb finds W's where the 4 free moduli have low HW (median 47), but those W's happen to have HIGH HW(de) and HW(dg) (raw HW 71-83). The structurally-derived registers can compensate badly.

This confirms a subtle point: even though dg is fully determined by dc (R63.1) and de is determined by da and dT2_63 (R63.3), their HW DEPENDS on the actual values, not just on dc and da's HW. Low-HW dc doesn't guarantee low-HW dg through the modular subtraction (which involves carry propagation).

## What this confirms (and refutes)

**Confirmed**: the bet's prior `20260424_hillclimb_negative.md` — local search on residual HW plateaus around HW=65-82, well above the Wang threshold (≤24).

**Refuted**: my hypothesis that structural-aware scoring would break the plateau. The 4-d.o.f. structural picture doesn't help local search.

## Why neither helps

The residual variety is **uniform on the 4-d.o.f. modular space** (per the empirical uniformity check from mitm_residue 20260425_sat_prob_derivation.md). For a uniform 4 × 32 = 128-bit variety, the HW distribution is binomial(128, 0.5):
- mean: 64
- min in 1M samples: ~50-52 (5σ tail)

The corpus's min HW=58-62 from random sampling is in this expected range. Hill-climb on a flat (uniform) variety can't beat random — every move is equally good in expectation.

The ONLY way to find sub-50 HW residuals is via STRUCTURED CONSTRUCTION (path B in BET.yaml: backward-search from a target low-HW residual), not via local search on the W-input space.

## Implication for the bet

The hill-climb path (forward-sample-then-improve) is **firmly closed** for HW reduction below the random-sampling floor. The structural picture, while empirically locked, does not translate to local-search advantage.

Path forward to a sub-24-HW corpus:
- (B) Backward-search engine — multi-week.
- (A) Cascade-aux force-mode extension that constructively limits residual HW algebraically — multi-day, requires encoder modification.
- New idea: SAT-based residual-HW-bounded search (encode "HW_residual ≤ K" as cardinality constraint, search for satisfying W). Kissat with cardinality constraints is feasible but slow at large K.

## Run logs

`structural_hillclimb.py` — single-file Python script, 200 lines, ~120s total runtime per full sweep.

## Status of negatives.yaml

This result REFUTES one possible avenue ("structural-aware hill-climb breaks the plateau") and is consistent with the existing closed claim about local search.

It does NOT close the broader negative ("naive multi-block strategy fails — residual too large") — that requires path B success.
