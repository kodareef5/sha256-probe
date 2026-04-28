# F91: Predictor validation at N=8 ✓ + N=10 retraction of F90's "N-invariance" claim
**2026-04-28 01:35 EDT**

Empirical validation of F90's algebraic predictor on cascade-1
survivor sets. **Confirms at N=8 (2.03× boost as claimed) but
DISCONFIRMS at N=10 (only 1.06× boost).** Honest retraction of F90's
"N-invariant MSB kernel" claim — the bit-position correlation appears
to be a small-N artifact.

This is the **6th honest retraction** in the project's discipline
record (F39, F49, F55, F69, F74, F91 — all caught via fast follow-up
validation as soon as cross-N data was available).

## Tools

`headline_hunt/bets/block2_wang/cascade_searcher/validate_predictor.py`
— stdlib-only. Loads cascade-survivor JSON, applies the F90 3-bit
predicate, splits survivors into PREDICTED vs NOT-PREDICTED, reports
low-HW enrichment ratio.

## Results

### N=8 — predictor VALIDATED

```
Predictor: dm[0].bit7=1 AND dm[9].bit0=1 AND dm[9].bit3=0
Survivors: 260
Low-HW threshold: ≤25 (25th percentile)

ALL survivors:    n=260, low-HW = 67/260 = 25.8%
PREDICTED set:    n=30,  low-HW = 14/30  = 46.7%
NOT predicted:    n=230, low-HW = 53/230 = 23.0%

Low-HW enrichment: 0.467 / 0.230 = 2.03× boost  ← VALIDATED
```

The 3-bit predictor at N=8 gives 2× enrichment for low-HW residuals.
Confirms F90's algebraic prediction.

### N=10 — predictor FAILS (disconfirms F90 N-invariance claim)

```
Predictor: dm[0].bit9=1 AND dm[9].bit0=1 AND dm[9].bit3=0
Survivors: 1,048
Low-HW threshold: ≤32 (25th percentile)

ALL survivors:    n=1048, low-HW = 294/1048 = 28.1%
PREDICTED set:    n=132,  low-HW = 39/132   = 29.5%
NOT predicted:    n=916,  low-HW = 255/916  = 27.8%

Low-HW enrichment: 0.295 / 0.278 = 1.06× boost  ← NOT VALIDATED
```

At N=10, the predictor gives only 1.06× boost — within statistical
noise. The MSB-bit-set + LSB-bit-set + bit3-avoid predicate does NOT
generalize from N=8 to N=10.

### N=10 bit frequencies — all near-uniform

```
Bit | dm[0] | dm[9]
----+-------+-------
  0 | 50.1% | 51.3%
  1 | 48.6% | 48.1%
  ...
  9 | 49.9% | 49.9%   ← MSB at N=10, NO enrichment
```

The MSB at N=10 (bit 9) shows 49.9% frequency in both dm[0] and dm[9]
— exactly the uniform baseline. **No MSB enrichment at N=10.**

### N=10 low-HW correlation — different signals

```
Bit | dm[0] base→low (×ratio) | dm[9] base→low (×ratio)
----+-------------------------+-------------------------
  3 | 48.4% → 53.1% (×1.10)   | 49.9% → 49.3% (×0.99)
  4 | 49.6% → 54.1% (×1.09)   | 49.5% → 50.7% (×1.02)
  5 | 50.1% → 48.0% (×0.96)   | 49.8% → 41.5% (×0.83)  ← depleted
  8 | 51.1% → 53.7% (×1.05)   | 49.9% → 54.1% (×1.08)
  9 | 49.9% → 48.3% (×0.97)   | 49.9% → 51.4% (×1.03)
```

Strongest signal: dm[9].bit-5 DEPLETED ×0.83 — different bit, different
direction from N=8. The N=8 dm[9].bit-3 depletion (×0.78) does NOT
appear at N=10 (×0.99 = no effect).

## Retraction of F90's paper-class claim

F90 claimed:
> The MSB enrichment of dm[0].bit-7 at N=8 EXACTLY matches the
> m17149975 cascade-1 structure at N=32 (kernel bit = 31 = MSB).
> Mini-SHA at N=8 prefers SAME kernel position as full-N=32 collision.
> MSB-kernel preference is N-INVARIANT in shape, not just modular relations.

F91 disconfirms the N-invariance: at N=10, the MSB shows NO
enrichment. The N=8 finding may be:

1. **A genuine small-N artifact**: at N=8, the (m0, m9) restriction
   is so tight (only 65k patterns) that statistical fluctuations
   produce false-positive bit correlations.

2. **A real but N-dependent structure**: the cascade-1 bit-correlation
   pattern may shift with N. F88's per-round HW trajectory finding
   (cascade-1 a-zero structure at round 60) IS N-invariant — that
   claim still stands. But the *which-dm-bits-trigger-it* signal is
   not.

3. **Threshold sensitivity**: low-HW threshold at N=10 (≤32) may be
   too generous. Tighter threshold not tested in this hour's window.

## What still holds (post-retraction)

The F88 + F89 structural findings remain INTACT:
- ✓ N=8 cascade trajectory matches N=32 m17149975 (round-60 a-zero,
  shift-propagation through 61-63)
- ✓ Cascade filter HW_a(60)=0 narrows search 250-1000× at N=8 and N=10
- ✓ Single-register filter is sufficient (multi-register redundant)
- ✓ At N=8 cascade-1 IS the optimum; at N=10 it's near-optimum (1 HW gap)

The F90 bit-correlation claim is the SOLE retraction. The
cascade-filter mechanism remains the right structural tool.

## What this changes for the searcher

- **Drop the F90 bit-position branching heuristic** — no evidence it
  generalizes beyond N=8.
- **Keep the F89 cascade-filter** — empirically robust across N=8 and N=10.
- **Future bit-correlation work**: would need N=12, 14, 16, 32 data to
  see if any bit pattern actually generalizes. At N=12 (16M patterns,
  ~50 min wall) this is the next probe in the searcher's design loop.

## Connection to existing discipline pattern

Project has 5 prior honest retractions today (F39, F49, F55, F69, F74).
F91 is the 6th. The pattern: ship a structural claim with N=K data,
cross-check at N=K+2, retract or refine if it doesn't generalize.
This is healthier than over-claiming and finding out months later.

The retraction itself is signal: it tells us cascade-1 has a robust
**structural** property (a-zero at round 60, F88+F89) but NOT a
robust **algebraic** bit-position predictor. Different layers of the
cascade are differently N-invariant.

## Discipline

- No solver runs (Python compute, no SAT)
- F91 retraction caught via simple cross-N validation (~2 min compute)
- Both N=8 (validated) and N=10 (refuted) results captured

EVIDENCE-level: VERIFIED at N=8, REFUTED at N=10. F90's bit-correlation
claim retracted; F88/F89 structural claims unaffected.

## Reproduce

```bash
# Validate F90 predictor at N=8 (validated):
python3 validate_predictor.py n8_cascade_survivors.json
# Output: 2.03× boost, "VALIDATED"

# Validate at N=10 (refuted):
python3 validate_predictor.py n10_cascade_survivors.json
# Output: 1.06× boost, "weakly validated" (within noise)
```
