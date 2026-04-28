---
date: 2026-04-28
bet: cascade_aux_encoding
status: F208_UNIVERSALITY_QUALIFIED — Tanner structure is encoder-specific
---

# F210: TRUE sr=61 CNFs have substantially different Tanner-graph structure than cascade_aux

## Setup

F208 found that cascade_aux Tanner-graph 4-cycle structure is
universal across 8 cascade_aux instances. F209 grounded this with
the encoder semantic mapping. The natural next probe (F209-c):
test whether the same structure appears in TRUE sr=61 CNFs
(`cnfs_n32/`), which use a different encoder.

## Result

Ran tanner_4cycle_count.py on
`cnfs_n32/sr61_cascade_m17149975_fffffffff_bit31.cnf` (the
canonical sr=60 collision-witness candidate, m17149975).

| Property | cascade_aux (F207/F208) | TRUE sr=61 (F210) |
|---|---|---|
| Vars × clauses | 12596 × 52657 | 11256 × 47663 |
| 4-cycle count | 270K | **201K** |
| Multiplicity-4 pairs | 27,752 | 24,884 |
| Max single multiplicity | **36** | **10** |
| Highest-mult pair | (var 2, var 130) gap=128 mult=36 | (var 11, var 1584) gap=1573 mult=10 |
| Gap=128 prominent? | yes (high-mult outliers) | no (not in top 20) |
| Gap=32 prominent? | yes (1605 pairs) | no (not in top 20; gap=22 has 68) |
| High-mult cluster | mult=18 family at gap=754 | scattered at gaps 1571-1723 |

The two encoders produce **substantially different Tanner-graph
shapes**:

1. **Maximum coupling differs by 3.6×.** cascade_aux has a single
   var-pair coupled by 36 clauses; TRUE sr=61's max is 10.
   cascade_aux's encoding concentrates clauses on specific var-pairs.

2. **High-mult pair gaps differ by an order of magnitude.**
   cascade_aux peaks at gap=128 (4× word size). TRUE sr=61 peaks
   at gap=1573-1723. These differ in the underlying variable layout.

3. **Word-aligned (gap=32) structure is absent in TRUE sr=61.**
   Cascade_aux had 1605 pairs at gap=32; TRUE sr=61 doesn't show
   gap=32 in top-20 buckets.

4. **TRUE sr=61's high-mult pairs cluster around var indices
   ~11-125 paired with var indices ~1574-1853.** A consistent
   "small + medium" pairing pattern, not the "small + small + 128"
   pattern of cascade_aux.

## Interpretation

The TRUE sr=61 encoder lays out variables in a different order than
cascade_aux. cascade_aux groups M1 schedule words first then M2
schedule words (per F209), giving the gap=128 = 4×32 cross-message
pattern. TRUE sr=61 likely groups by ROUND first (with M1 and M2
adjacent within each round), giving a different gap pattern.

Without reading the TRUE sr=61 encoder source (likely in
`q1_barrier_location/` or `archive/`), the exact semantic mapping
isn't known. But the empirical conclusion is sharp:

> **The cascade_aux-specific quasi-cyclic gap-32 structure does
> NOT generalize to TRUE sr=61.** Tanner-graph shape is encoder-
> specific.

## Consequences for F207/F208/F209 conclusions

### F207 holds (within cascade_aux)
The four-peak structure (gap-1-3, gap-32, gap-128) is real for
cascade_aux N=32. Still falsifies the principles framework's
gap-9/11 prediction within that encoder.

### F208 holds (within cascade_aux family)
8 cascade_aux CNFs share the same shape. But the "universal"
descriptor must be qualified: **universal within cascade_aux**,
NOT across encoders.

### F209 holds (semantic mapping for cascade_aux)
The (var 2, var 130) = W1_57[0] / W2_57[0] mapping is correct
for cascade_aux. For TRUE sr=61, the variable layout is different;
F209's mapping doesn't apply.

### F209's hybrid algorithm proposal — qualified scope
The proposed "BP marginal on 128-bit (M1, M2) joint schedule +
heuristic on hardlock space" was specifically for **cascade_aux's
encoding**. For TRUE sr=61, a similar BP-marginal approach would
need a different variable-clustering scheme matching that
encoder's layout.

## What this means for the bet

cascade_aux_encoding bet's algorithm direction is now sharper:
**design BP-marginal decoder for cascade_aux specifically**, since
its quasi-cyclic structure is favorable. The decoder can then be
benchmarked against cascade_aux CDCL+hints to test if BP improves
on the existing 2-3× preprocessing speedup.

For TRUE sr=61, a separate analysis would be needed to design an
encoder-specific decoder. That's beyond cascade_aux_encoding bet's
scope.

## Concrete next probes

(a) **Read the TRUE sr=61 encoder** to map its variable layout
    semantically. Likely in `archive/` or `q1_barrier_location/`.
    Confirms whether the gap=1573 cluster encodes round-coupling
    or some other pattern.

(b) **Compare an `aux_force_*.cnf` (mode=force) to the same-cand
    `aux_expose_*.cnf` (mode=expose)**. Both use cascade_aux
    encoder. If structure differs, mode-specific Tseitin auxiliaries
    matter; if same, the bet can target either mode.

(c) **Run F207 on a smaller cnf** (mini-SHA, N=8 or N=10) to test
    whether the quasi-cyclic gap-32 structure is N-dependent. F134
    suggested N=8 mini-SHA work as the BP-Bethe baseline target.

(d) **Treewidth bound** on cascade_aux's bipartite graph. If
    treewidth is small (≤50), exact DP decoding is feasible.

## Discipline

- 0 SAT compute (single TRUE sr=61 CNF analysis, ~0.04s)
- 0 solver runs
- F210 corrective: F208's "universal" claim qualified to within
  cascade_aux family
- Strategic implication: cascade_aux is the right target for the
  QC-LDPC-style decoder; TRUE sr=61 needs separate analysis
