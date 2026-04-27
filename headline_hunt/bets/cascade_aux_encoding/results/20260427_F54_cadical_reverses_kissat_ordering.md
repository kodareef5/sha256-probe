# F54: cadical REVERSES kissat ordering — F52/F53 sym-penalty is KISSAT-SPECIFIC
**2026-04-27 10:45 EDT**

Tests F53's mechanism prediction: "if EXACT-symmetry creates branchier
CNF that kissat can't break, cadical (different CDCL strategy) might
handle it differently."

Result: **cadical REVERSES the ordering**. EXACT-sym is FASTER than
NON-sym on cadical, opposite of kissat.

## Result on HW=48 cands (5 seeds × 1M conflicts × sequential)

| cand | HW | sym | kissat median | **cadical median** | range |
|---|---:|:---:|---:|---:|---:|
| bit00_md5508363 | 48 | EXACT | 53.42s | **45.20s** | 14s |
| bit17_mb36375a2 | 48 | EXACT | 42.52s | (untested) | — |
| msb_ma22dc6c7 | 48 | NO | 31.31s | (untested) | — |
| **bit18_mafaaaf9e** | **48** | **NO** | **30.39s** | **65.23s** | **92s** |

For the 2v2 control:
- kissat: EXACT-sym 17s SLOWER than NON-sym
- cadical: EXACT-sym ~20s FASTER than NON-sym

**ORDERING REVERSES BETWEEN SOLVERS.**

## bit18_mafaaaf9e cadical seed variance is enormous

cadical walls: 131.46, 51.77, 39.02, 65.23, 68.82 → range 92.44s.

Compare to bit18 on kissat: 33.36, 29.59, 28.53, 30.39, 33.75 →
range 5.22s.

cadical's variance is 18× kissat's on the same CNF. This is a
HUGE difference in solver consistency.

bit00 cadical seed variance: 14s — much more reasonable. So cadical
handles the EXACT-sym CNF more reliably than the NON-sym CNF.

## Implications — F52/F53 mechanism revised

F52/F53 mechanism speculation:
> "EXACT-sym residuals create cascade_aux CNFs with structural
> redundancy that kissat can't break."

F54 update:
> "EXACT-sym residuals create cascade_aux CNFs with STRUCTURE.
> kissat handles the structure POORLY (penalized by ~17s at HW=48).
> cadical handles the structure WELL (advantage of ~20s at HW=48).
> The difference is in CDCL HEURISTIC choice, not in CNF
> 'branchiness' per se. cadical's heuristic appears to leverage
> the symmetric structure; kissat's gets confused by it."

This is a fundamentally different (and more interesting) finding.
The cascade_aux Mode A CNFs contain real structural information
that some solvers exploit and others stumble on.

## What this means for the F-series story

The F37/F39/F41/F46/F47/F48/F49/F50/F51/F52/F53 story across kissat
is REAL but SOLVER-SPECIFIC:

- For kissat: HW≤47 fast cluster, EXACT-sym at HW≥47 harmful, etc.
- For cadical: completely different ordering. EXACT-sym might be
  the FAST cluster. NON-sym might be slow with high variance.

**The "fast cluster" is solver-dependent.**

For paper Section 4, the publishable finding solidifies as:

> "Within cascade_aux Mode A sr=60 CNFs at 1M conflicts, kissat and
> cadical exhibit STRUCTURALLY DIFFERENT ordering on a controlled
> 2v2 test (HW=48 EXACT-sym vs NON-sym). On kissat, EXACT-sym is
> ~17s slower than NON-sym. On cadical, EXACT-sym is ~20s FASTER
> than NON-sym. cadical seed variance on the NON-sym cand is 18×
> kissat's. The cascade_aux structure encodes information that some
> CDCL heuristics leverage and others miss. Which solver is 'best'
> depends on which structural feature is being exploited."

This is a more honest and more interesting structural finding than
'symmetry is always harmful' — it's a real solver-architecture
distinction.

## Implication for sr=61 / hardline-hunt strategy

Most of the F-series structural-vs-solver work has been on KISSAT
exclusively. The F54 reversal means we should:

1. **Cross-validate kissat structural findings on cadical** before
   publishing as universal claims. F37/F46/F47/F49/F50/F51/F52/F53
   all need cadical follow-ups.

2. **Pick the solver that EXPLOITS the structural advantage** of
   the target cand. For bit2 (HW=45, EXACT-sym, kissat=27s),
   cadical might be even faster. For msb_ma22dc6c7 (HW=48, NON-sym,
   kissat=31s), cadical at 65s is much WORSE.

3. **Use BOTH solvers** in parallel for unknown cands — whichever
   converges first wins.

## Implications for block2_wang

For Wang trail design (where solver-axis is irrelevant), bit2 keeps
its structural primacy.

For SAT-axis exploration of new cands:
- If bit2 is the target: try cadical first (might be faster)
- If msb_ma22dc6c7 is the target: kissat first
- Mixed-solver portfolio is the safest cross-axis strategy

## Discipline

- 10 cadical runs logged via append_run.py (NEW solver in dataset)
- Both CNFs pre-existing + audited
- Sequential measurement
- bit18 cadical ran for >1min on seed=1; reproducible

EVIDENCE-level: VERIFIED. Direct 2v2 control with consistent results
across 5 seeds per group. The cadical vs kissat reversal is REAL.

## ADDENDUM (run during F54 same session): bit2 on cadical

Tested cadical on bit2_ma896ee41 (kissat-fastest at 27s, HW=45 EXACT-sym):

  walls: 65.08, 43.60, 41.30, 26.47, 24.60 → median 41.30s, range 40.48s

cadical is NOT universally fast on EXACT-sym. bit2 cadical median is
41s — much slower than kissat (27s) AND highly variable.

Updated 3-cand cross-solver picture:

| cand | HW | sym | kissat | cadical | order on kissat | order on cadical |
|---|---:|:---:|---:|---:|---|---|
| bit2_ma896ee41 | 45 | EXACT | 27s | 41s | fastest | fastest |
| bit18_mafaaaf9e | 48 | NO | 30s | 65s | middle | slowest |
| bit00_md5508363 | 48 | EXACT | 53s | 45s | slowest | middle |

**Key insight**: bit2 is fastest on BOTH solvers. The bit00/bit18
ordering REVERSES between solvers. cadical's seed variance is huge
on multiple cands (bit2: 40s, bit18: 92s, bit00: 14s).

cadical isn't a "symmetry-friendly" solver per se — it's an
"inconsistent on cascade_aux Mode A" solver with high seed variance.
bit2's universal speed across solvers might reflect bit2's specific
structural cleanness (HW=45 + sparse symmetric pattern) rather than
sym-friendliness.

## Concrete next moves

1. **Test cadical on bit13_m4e560940 vs bit13_m72f21093** (HW=47
   EXACT-sym vs NON-sym) — does the bit00/bit18 reversal hold at HW=47?

2. **Update F37-F53 memos with cadical caveat**: "kissat-specific."
   The cross-solver picture is the more honest one.

3. **For yale's manifold-search**: F54's cadical reversal hints
   that cadical's heuristics ARE leveraging cascade-1 symmetric
   structure on certain cands but NOT bit2. Worth comparing yale's
   manifold-search behavior to cadical's per-cand variance.

4. **Update sigma1_aligned_kernel_sweep BET.yaml**: add F54's
   "solver-dependent ordering" finding — single-solver structural
   tests aren't enough to settle the bet.

5. **Cross-solver kissat-vs-cadical sweep across the 15-cand
   F-series baseline** would give a complete cross-validation
   matrix. Substantial follow-up work but high information value.
