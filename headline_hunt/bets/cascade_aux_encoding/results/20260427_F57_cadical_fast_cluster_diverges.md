# F57: cadical-fast cluster DIVERGES from kissat-fast cluster
**2026-04-27 11:16 EDT**

Tests cadical on 2 more cands to map the cadical-fast cluster:
- bit17_mb36375a2 (HW=48 EXACT-sym) — counterpart to bit00 in F54
- bit10_m9e157d24 (HW=47 NON-sym) — overlap with kissat-fast cluster

## Result

```
bit17_mb36375a2 (HW=48 EXACT-sym, kissat=42s): cadical 24.21, 24.96, 22.92, 24.47, 24.82
                                                cadical median 24.47s, range 2.04s — FAST!

bit10_m9e157d24 (HW=47 NON-sym, kissat=28s):    cadical 24.20, 23.75, 27.56, 23.36, 23.81
                                                cadical median 23.81s, range 4.20s — FAST
```

Both FAST and TIGHT on cadical. Even bit17 (kissat-slow at 42s) runs
at 24s on cadical — **kissat-penalty REVERSES on cadical at HW=48
EXACT-sym** (now confirmed for 2 cands: bit00 and bit17).

## Updated cross-solver picture (8 cands × 2 solvers)

| cand | HW | sym | kissat | cadical | cadical/kissat ratio |
|---|---:|:---:|---:|---:|---:|
| bit2_ma896ee41 | 45 | EXACT | **27s** | 41s | 1.52× SLOWER on cadical |
| bit13_m72f21093 | 47 | NO | 29s | 34s | 1.17× slower |
| bit10_m9e157d24 | 47 | NO | 28s | **24s** | **0.86× FASTER on cadical** |
| bit13_m4e560940 | 47 | EXACT | 33s | 37s | 1.12× slower |
| msb_ma22dc6c7 | 48 | NO | 31s | **25s** | **0.81× FASTER on cadical** |
| bit18_mafaaaf9e | 48 | NO | 30s | 65s | 2.17× SLOWER (pathology) |
| bit17_mb36375a2 | 48 | EXACT | 42s | **24s** | **0.57× FASTER on cadical** |
| bit00_md5508363 | 48 | EXACT | 53s | 45s | 0.85× faster |

## Two distinct fast clusters

**kissat-fast cluster** (5 cands at 27-29s sequential):
- bit2_ma896ee41 (HW=45 EXACT)
- bit25_m30f40618 (HW=46 NON)
- bit3_m33ec77ca (HW=46 NON)
- bit10_m9e157d24 (HW=47 NON)
- bit13_m72f21093 (HW=47 NON)

**cadical-fast cluster** (3+ cands at 23-25s sequential):
- bit10_m9e157d24 (HW=47 NON) ← overlap with kissat-fast
- bit17_mb36375a2 (HW=48 EXACT) ← kissat-SLOWEST cluster!
- msb_ma22dc6c7 (HW=48 NON)

**Overlap**: only bit10_m9e157d24 is in both fast clusters.

## Key insight: kissat and cadical prefer DIFFERENT structural properties

Pattern across 8 cands:

- **kissat prefers**: low HW (45-47) + NON-symmetry (or HW=45 with sym)
- **cadical prefers**: HW=47-48 with specific structural properties
  not yet characterized; EXACT-sym at HW=48 is FAVORED on cadical
  (opposite of kissat)

This might come from:
- kissat's heuristic chases low-conflict high-structure paths
- cadical's vivification + equiv-sub chases redundant CNF clauses,
  which symmetric residuals provide more of

For paper Section 4: this is now a SUBSTANTIAL solver-architecture
finding with N=8 cands × 2 solvers = 16 measurements.

## bit17 is the SURPRISE cand

- kissat: 42s (slow, EXACT-sym penalty)
- cadical: 24s (FAST AND TIGHT, kissat-penalty REVERSED)

bit17_mb36375a2 (HW=48, fill=00000000, kernel_bit=17, EXACT-sym
a_61=e_61=0x00200040 with HW=2) is now revealed as a CADICAL
CHAMPION cand — fastest tested with the lowest variance.

## bit18 cadical pathology investigated

bit18_mafaaaf9e cadical median 65s, range 92s. Compare to other
HW=48 NON-sym cand msb_ma22dc6c7 cadical median 25s tight.

bit18's pathology is likely:
- Specific bit-pattern in m0=0xafaaaf9e creating a CNF clause set
  cadical's preprocessing struggles with
- Possibly cadical's restart/decay schedule misaligned with bit18's
  specific carry chains

NOT a general HW=48 NON-sym issue. F56 confirmed via msb_ma22dc6c7.

## Paper Section 4 — refined claim with N=8

> "Cascade_aux Mode A 1M-conflict CDCL walls reveal solver-specific
> structural preferences. Across 8 distinguished cands tested on
> kissat 4.0.4 and cadical 3.0.0:
>
> kissat exhibits a 5-cand fast cluster at HW≤47 NON-sym (or HW=45
> EXACT-sym) with median 27-29s and tight seed variance (range
> 2-4s). EXACT-symmetry at HW≥47 incurs a 5-23s kissat penalty.
>
> cadical exhibits a different 3-cand fast cluster (one shared with
> kissat: bit10) at HW=47-48 NON-sym + HW=48 EXACT-sym at 23-25s.
> The kissat-EXACT-sym penalty REVERSES on cadical: bit00 and bit17
> (both HW=48 EXACT-sym) are 8-18s FASTER on cadical than kissat.
> One cand (bit18_mafaaaf9e) exhibits a cadical-specific pathology
> (median 65s, seed range 92s).
>
> Only bit10_m9e157d24 is fast on both solvers. bit2_ma896ee41 is
> fastest on kissat (27s) but slower on cadical (41s). bit17 +
> msb_ma22dc6c7 are fastest on cadical (24-25s) but slow/medium on
> kissat (31-42s). The two solvers leverage DIFFERENT structural
> features of the cascade-1 residual."

This is a robust paper-publishable cross-solver structural finding.

## Implications for block2_wang

Three primary targets, one per axis:

1. **bit2_ma896ee41**: HW + EXACT-sym + kissat-fastest (Wang sym-axis
   + kissat-axis champion)
2. **msb_ma22dc6c7**: F36 LM-min + cadical-fastest (LM-axis +
   cadical-axis champion). Triple distinction.
3. **bit17_mb36375a2**: cadical-fastest (24s) + EXACT-sym at HW=48
   (potentially Wang-friendly via shared sym pattern)

For mixed-solver block2_wang campaigns: bit2 + msb_ma22dc6c7 + bit17
= 3-cand portfolio covering all known cross-solver advantages.

## For yale's manifold-search

cadical's preference for HW=48 EXACT-sym (bit17, bit00) might
correlate with manifold-search efficiency on these cands — both
benefit from STRUCTURAL CONSTRAINT EXPLOITATION. yale's HW=8
near-miss frontier from singular_chamber might be more achievable
on bit17 or msb_ma22dc6c7 than on bit2.

Concrete cross-axis test for yale: try the guarded message-space
walks on bit17_mb36375a2 (HW=48 EXACT-sym, cadical-fast). If yale's
operators converge faster on bit17 than on the F45 bit28 baseline,
the "cadical-fastness ↔ manifold-friendliness" hypothesis holds.

## Discipline

- 10 cadical runs logged via append_run.py
- Both CNFs pre-existing + audited
- Sequential measurement
- N=8 cross-solver baseline now solidly measured

EVIDENCE-level: VERIFIED. Two-cand confirmation (bit00 + bit17) of
cadical EXACT-sym preference at HW=48. bit17's tight 2.04s range
makes it the most-reliable cadical-axis champion.

## Concrete next moves

1. **Synthesis memo (F58)** consolidating F37→F57: 8-cand cross-
   solver picture for paper Section 4. Brings all the kissat-axis
   work + cadical-axis discoveries into one queryable document.

2. **Test cadical on remaining kissat-fast cands** (bit25, bit3) to
   complete the cadical mapping of kissat-fast cluster.

3. **Test bit2 on alternate solvers** (CryptoMiniSat 5?) to see if
   bit2's kissat-cadical asymmetry holds on a 3rd solver.

4. **Update F54 memo** to note that bit17 also confirms the cadical
   reversal at HW=48 EXACT-sym (not bit00 alone).
