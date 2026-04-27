# F55: cadical HW=47 control — REVERSAL is HW=48-SPECIFIC, not general
**2026-04-27 11:00 EDT**

Tests F54's HW=48 reversal at HW=47: same fill (0xaaaaaaaa), same
kernel_bit (13), only sym differs (bit13_m4e560940 EXACT-sym vs
bit13_m72f21093 NON-sym).

If F54's reversal is HW-general → cadical sym FASTER than non-sym
at HW=47 too.

If F54's reversal is HW=48-specific → cadical agrees with kissat at
HW=47 (sym slower than non-sym).

## Result

```
HW=47, same fill (0xaaaaaaaa), same kernel_bit (13):

cadical bit13_m4e560940 (EXACT-sym): 39.67, 37.63, 35.26, 36.99, 36.15 → median 36.99s
cadical bit13_m72f21093 (NON-sym):   34.29, 36.80, 34.67, 25.97, 25.51 → median 34.29s
```

**At HW=47 cadical: NON-sym is faster by 2.7s.**

For comparison at HW=47 kissat:
- bit13_m4e560940 (EXACT-sym): 32.83s
- bit13_m72f21093 (NON-sym): 28.72s
- gap: 4.1s (NON-sym faster)

For HW=48 cadical (F54):
- bit00_md5508363 (EXACT-sym): 45.20s
- bit18_mafaaaf9e (NON-sym): 65.23s
- gap: 20s (EXACT-sym FASTER — REVERSED vs kissat)

## Cross-solver picture refined

| HW | cand pair | kissat sym | kissat non-sym | cadical sym | cadical non-sym |
|---:|---|---:|---:|---:|---:|
| 47 | bit13_m4e/m72f | 32.83 | 28.72 | 36.99 | 34.29 |
| 48 | bit00/bit18 | 53.42 | 30.39 | 45.20 | 65.23 |

At HW=47: BOTH solvers agree NON-sym is faster (~3-4s gap).
At HW=48: kissat says NON-sym faster (~23s gap), cadical REVERSES
(EXACT-sym faster by 20s).

**The F54 reversal is HW=48-SPECIFIC, not HW-general.**

## What's special about HW=48?

The HW=48 EXACT-sym cands have specific properties:
- bit00_md5508363: a_61=e_61=0x40001004 (HW=3 sym pattern)
- bit17_mb36375a2: a_61=e_61=0x00200040 (HW=2 sym pattern)
- bit2_m67dd2607:  a_61=e_61=0x40403000 (HW=4 sym pattern)
- bit2_mea9df976:  a_61=e_61=0x40000200 (HW=2 sym pattern)

The HW=48 EXACT-sym cands have SPARSER symmetric patterns (HW=2-4)
than HW=47's bit13_m4e560940 (HW=4 sym pattern).

Wait — that's the same range. So the sparseness of the symmetric
pattern alone doesn't explain the cadical-specific HW=48 reversal.

Possibilities:
1. **Total HW threshold**: at HW=48 specifically, cadical's
   preprocessing (vivification, hyper-resolution) finds something
   useful that kissat's doesn't. Below HW=48, less to exploit.
2. **Encoder side-effect**: cascade_aux Mode A CNFs at HW=48 have
   ~13207 vars vs ~13212 at HW=47. Negligible difference.
3. **Coincidence with N=2 cands per cell**: 4 measurements isn't
   strong evidence. Could just be seed variance.

For #3, the cadical bit18 walls (131.46, 51.77, 39.02, 65.23,
68.82 from F54) have HUGE variance. Maybe cadical on bit18
specifically has a pathological case, not a general HW=48 NON-sym
issue.

## Refined story (replaces F54's "reversal" framing)

The honest picture across the cross-solver tests so far:

> "cascade_aux Mode A 1M-conflict walls are SOLVER-DEPENDENT in
> magnitude AND seed variance. kissat is more consistent across
> seeds (range 3-22s). cadical has high seed variance on some cands
> (range up to 92s). At HW=47, both solvers agree EXACT-sym is
> 3-4s slower than NON-sym. At HW=48, the kissat sym/non-sym gap
> is ~23s; cadical's gap depends on which specific cand is tested
> — bit18_mafaaaf9e on cadical has anomalously high variance and
> high median (65s), inverting the typical NON-sym-is-faster
> pattern. Whether this is a bit18-specific quirk or a general
> HW=48 cadical issue requires more cands."

This is more honest than F54's strong "reversal" claim. The
reversal might be a single-cand cadical pathology on bit18.

## What this means for paper Section 4

REVISED again:

> "kissat at 1M conflicts on cascade_aux Mode A sr=60 shows a
> consistent ordering: HW≤47 NON-sym fast cluster (28-32s);
> HW=49+ NON-sym plateau (35-39s); EXACT-sym at HW≥47 5-23s
> slower than NON-sym at same HW. cadical exhibits HIGHER seed
> variance on certain cands (notably bit18_mafaaaf9e at 92s seed
> range) which can invert the kissat ordering on the bit00/bit18
> 2v2 control at HW=48. At HW=47 (bit13_m4e/bit13_m72f control),
> both solvers agree on the NON-sym-faster ordering. The F-series
> cross-solver picture warrants larger N before claiming universal
> ordering reversal."

## Discipline correction

F54 overclaimed "REVERSAL." F55 reveals the reversal is fragile —
HW=48-specific OR bit18-specific. F55 is the honest correction in
the same spirit as F39 catching F37/F38, and F49 catching F48.

**Discipline pattern**: any claim of "X reverses between solvers"
needs cross-validation at MULTIPLE HW levels and MULTIPLE cands per
cell before publication. F54's N=2 was insufficient.

## Discipline

- 10 cadical runs logged via append_run.py
- Both CNFs pre-existing + audited
- Sequential measurement

EVIDENCE-level: VERIFIED. The HW=47 cadical sym/non-sym ordering
matches kissat. F54's HW=48 reversal is now reframed as
HW-specific or bit18-specific (untested distinction).

## Concrete next moves

1. **Test cadical on msb_ma22dc6c7** (HW=48 NON-sym, the OTHER
   HW=48 NON-sym cand). If cadical median ~30s and low variance
   (matching kissat's 31s), then bit18 is a solo cadical pathology,
   not a general HW=48 cadical issue.

2. **Test cadical on bit17_mb36375a2** (HW=48 EXACT-sym, the
   OTHER HW=48 EXACT-sym cand). If cadical median ~42s (matching
   bit17 kissat 42s), then HW=48 EXACT-sym ordering is consistent
   across solvers. If much faster, the EXACT-sym-cadical-friendly
   pattern holds for both HW=48 EXACT-sym cands.

3. **Update F54 with F55 caveat** in the same memo or as a
   prefatory note pointing to F55.

4. **Stop and synthesize**: 5 F-series memos (F50, F52, F53, F54,
   F55) in a row on the same kissat-vs-cadical thread is rapidly
   refining. A consolidation memo at the end of this hour would
   help the fleet (and macbook) keep track of what's actually solid.
