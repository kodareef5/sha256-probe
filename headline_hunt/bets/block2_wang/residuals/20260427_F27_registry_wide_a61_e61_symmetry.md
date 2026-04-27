# F27: Registry-wide a_61 = e_61 symmetry — 9/67 cands at 100M
**2026-04-27 04:35 EDT**

Extends F26 (5-cand symmetry analysis) to the full registry of 67
candidates at 100M samples each (~3 min total compute).

## Result

| Property | Count |
|---|---:|
| Total registry cands tested | 67 |
| **Exact a_61 = e_61 (XOR HW = 0)** | **9** (13.4%) |
| Near-symmetry (XOR HW ≤ 1) | 21 (31%) |
| Near-symmetry (XOR HW ≤ 2) | 35 (52%) |

XOR HW distribution:
| XOR HW | cands |
|---:|---:|
| 0 | 9 |
| 1 | 12 |
| 2 | 14 |
| 3 | 11 |
| 4 | 11 |
| 5 | 5 |
| 6 | 4 |
| 8 | 1 |

## The 9 cands with exact symmetry (sorted by min HW)

| cand | min HW | a_61 = e_61 |
|---|---:|---|
| **cand_n32_bit13_m4e560940_fillaaaaaaaa** | **47** | 0x00820042 |
| cand_n32_bit2_mea9df976_fillffffffff | 48 | 0x40000200 |
| cand_n32_bit00_md5508363_fill80000000 | 50 | 0x80400602 |
| cand_n32_bit1_m6fbc8d8e_fillffffffff | 51 | 0x14084000 |
| cand_n32_bit15_m1a49a56a_fillffffffff | 52 | 0x02008010 |
| cand_n32_bit25_m09990bd2_fill80000000 | 52 | 0x00108000 |
| cand_n32_bit00_mf3a909cc_fillaaaaaaaa | 53 | 0x0e008008 |
| cand_n32_bit18_meed512bc_fill00000000 | 54 | 0x01000100 |
| cand_n32_bit3_m33ec77ca_fillffffffff | 54 | 0x500c3904 |

**bit13_m4e560940 has the LOWEST min HW (47) among all 9 exact-symmetry
cands. It is the strongest registry case for Wang-style absorption.**

## Caveat: F27 is at 100M samples

F25 found bit13's HW=47 already at 100M and at 1B. The 9 cands listed
above had their FIRST low-HW residual found at 100M. At 1B samples,
some of these cands' true min-HW residuals may have asymmetry HW >= 1.
F27 should be re-run at 1B samples per cand for definitive symmetry
classification (~25 min compute).

For now, the bit13 finding is robust (matches at 1B and 100M):
**bit13_m4e560940 has min-HW residual a_61 = e_61 = 0x00820042 at
both 100M and 1B sample budgets.**

## What changed from F26 → F27

F26 (5-cand): claimed bit13 was UNIQUE in the distinguished set.
F27 (67-cand): bit13 is unique in MIN HW among 9 exact-symmetry cands.

So bit13's "uniqueness" relative to the 5 distinguished cands was a
sample-set artifact, but its quantitative leadership (lowest HW among
exact-symmetry cands) is robust.

## bit13's distinguishing feature count, updated

| Feature | Rank in registry |
|---|---|
| F12 cascade-1 chamber image min HW | 2 of 67 (HW=3) |
| F25 round-63 residual min HW | 2 of 5 distinguished (HW=47) |
| F27 (this) lowest min-HW exact-symmetry cand | **1 of 9 / 1 of 67 with HW=47 + symmetry** |

Combined: bit13_m4e560940 is the PRIMARY block2_wang target by 3
independent metrics.

## Action item for block2_wang

The existing block2_wang corpus is msb-only. F27 confirms idx8/bit13/9
exact-symmetry cands as more structurally tractable Wang-attack targets.
Extending the corpus to bit13_m4e560940 (residuals/by_candidate/) is
the immediate next concrete move.

EVIDENCE-level: VERIFIED at 100M sample. Definitive 1B-sample
classification across 67 cands is a follow-up (~25 min compute).
