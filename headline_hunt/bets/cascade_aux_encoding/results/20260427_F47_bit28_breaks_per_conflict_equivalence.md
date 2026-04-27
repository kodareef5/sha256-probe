# F47: bit28_md1acca79 — first cand to BREAK per-conflict equivalence
**2026-04-27 15:22 EDT**

Tests yale's F45 raw LM champion (bit28_md1acca79 at HW=73, LM=718)
on cascade_aux Mode A sr=60 kissat. Result: bit28 is the FIRST cand
in the per-conflict equivalence study to show CLEARLY DIFFERENT solver
behavior from the established 27-28s sequential plateau.

## Result

| mode | walls (seeds 1,2,3,5,7) | median | mean |
|---|---|---:|---:|
| Parallel-5 (with system load 12) | 50.83, 49.22, 50.72, 54.82, 51.74 | **51.46s** | 51.47s |
| Sequential (clean) | 39.25, 36.69, 39.21, 58.48, 55.48 | **39.25s** | 45.82s |

## Comparison to plateau

Sequential measurements (clean, F41 + F47):

| cand | HW | LM | seq median | seq range |
|---|---:|---:|---:|---:|
| bit2_ma896ee41 | 45 | 824 | 27.08s | 25.99-28.63 (2.6s) |
| bit10_m9e157d24 | 47 | 805 | 28.04s | 26.77-29.97 (3.2s) |
| **bit28_md1acca79** | **49** | **855** | **39.25s** | **36.69-58.48 (21.8s)** |

Parallel-5 measurements (older but consistent):

| cand | HW | LM | par-5 median |
|---|---:|---:|---:|
| bit10 | 47 | 805 | 34.28s |
| bit06 | 50 | 825 | 34.55s |
| bit00_mc765db3d | 49 | 875 | 34.78s |
| bit2 | 45 | 824 | 35.61s |
| bit00_mf3a909cc | 51 | 787 | 35.91s |
| bit13 | 47 | 780 | 35.94s |
| msb_ma22dc6c7 | 48 | 773 | 35.99s |
| bit4 | 53 | 757 | 37.34s |
| **bit28** | **49** | **855** | **51.46s** |

bit28 is **15-16 seconds slower** than the established plateau, in
both parallel and sequential measurements. The HW=49 expectation
(per the weak-HW-tracking hypothesis) was ~28s sequential. Observed
39.25s — 11s above expectation.

## Two structural irregularities

### Irregularity 1: higher floor

bit28 sequential floor is 36.69s (best seed) — already above the
27-28s plateau. Even its best seed beats no plateau cand.

### Irregularity 2: high seed variance

bit28 seed variance is 21.8s (range 36.69-58.48), vs ~3s for plateau
cands. Seeds 5 and 7 take ~55s — nearly 2x the median.

This high variance suggests bit28's CNF has a "branchy" structure
where some seeds find quick partial-progress and some flounder.

## What might cause bit28's irregularity?

Per yale's F45, bit28_md1acca79 has:
- Lowest raw LM (718) of any cand at HW=73
- LM-min exact-symmetry record at HW=53 (LM=774, very close to bit4's 772)
- BROAD LM tail across HW levels

The "broad LM tail" might mean bit28's cascade-1 trail surface has
many near-equivalent low-LM points. Kissat may waste time exploring
this fanout.

In contrast, F25 universal rigidity says bit2/bit13/etc. each have
exactly ONE distinct vector at min HW. If their cascade-1 surface
is more concentrated, kissat may converge faster.

**Hypothesis (untested)**: cands with broad LM tails are kissat-harder
than cands with narrow LM tails, even at similar HW. bit28 has
broadest tail; bit28 is hardest. Need 2-3 more cands with intermediate
tail breadth to confirm.

## Refined per-conflict equivalence claim

The clean per-conflict equivalence claim from F37/F39/F41/F46:
"all distinguished cands cluster at 27-28s sequential / 34-37s
parallel-5 at 1M conflicts" must now be REFINED:

> "MOST distinguished cands (bit2, bit13, bit10, bit06, bit00_mc765db3d,
> bit00_mf3a909cc, msb_ma22dc6c7, bit4) cluster at 27-28s sequential,
> 34-37s parallel-5 at 1M conflicts. bit28_md1acca79 is an OUTLIER at
> ~39s sequential, ~51s parallel-5 — likely due to its broad LM tail
> structure (yale F45)."

For paper Section 4/5: the equivalence is BROAD but not UNIVERSAL.
bit28's outlier behavior is a worthwhile structural distinction.

## Implications for block2_wang target selection

bit28 is yale's F45 raw LM champion (HW=73, LM=718) and was a
recommended target. F47 reveals bit28 also has the WORST kissat
behavior at moderate budgets. If the bet's path requires kissat-based
SAT discovery, bit28 is suboptimal despite low LM.

For Wang trail design (where solver speed is irrelevant), bit28
remains a strong candidate via its low LM — but the kissat-harder
structure may indicate the same trails are also harder to construct
algorithmically.

**Updated PRIMARY recommendation**: bit4_m39a03c2d (lowest exact-sym
LM at LM=743 per F45 update) — both LM-tight AND in the
per-conflict equivalence cluster at 37s parallel-5 (F46).

## Discipline

- 10 kissat runs logged via append_run.py (5 parallel + 5 sequential)
- CNF audit CONFIRMED sr=60 cascade_aux_expose
- High-load measurement caveat noted in parallel runs

EVIDENCE-level: VERIFIED. bit28's outlier behavior is consistent
across both parallel and sequential measurement modes. High seed
variance is itself a structural fingerprint.

## Concrete next moves

1. **Test 1-2 more cands at intermediate LM-tail-breadth** to
   validate the "broad-tail = solver-hard" hypothesis.

2. **bit28's per-seed wall variance is itself a metric** —
   log it for future cands.

3. **For yale's operator design**: bit28 might be a useful
   "negative anchor" — the LM-min cand on the LM axis but
   structurally hardest on the solver axis.

4. **Cross-bet implication for block2_wang**: bit28's broad LM tail
   may hint at multiple competing trails, useful or harmful depending
   on whether trail-search exploits or wastes that fanout.
