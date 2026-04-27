# F25: Cross-cand residual structure on 5 distinguished cands (1B each)
**2026-04-27 04:00 EDT**

Extends F24 (single-cand bit13 lowhw analysis) to all 5 distinguished
candidates. Reveals universal structural rigidity at minimum HW and
identifies idx8_m33ec77ca as the new leader (HW=46).

## Result: minimum HW per cand

| cand | min HW | distinct @ min HW | next-HW gap |
|---|---:|---:|---|
| **idx8_m33ec77ca** (bit=3) | **46** | **1** | 3 (next HW=49) |
| bit13_m4e560940 (bit=13) | 47 | 1 | 4 (next HW=51) |
| msb_m17149975 (bit=31, sr=60 verified) | 49 | 1 | 1 (next HW=50) |
| msb_m189b13c7 (bit=31, F12 chamber champ) | 49 | 1 | 2 (next HW=51) |
| bit18_m99bf552b (bit=18) | 51 | 1 | 1 (next HW=52) |

**All 5 cands: exactly 1 distinct min-HW vector across 1 BILLION samples.**
The structural rigidity F24 found on bit13 is universal across the
distinguished registry.

## New leader: idx8_m33ec77ca

Min HW=46, 1 distinct vector found at:
  W[57..60] = (0xcaf62f78, 0xec3c3674, 0x34a2e2ad, 0x7619ac16)

This cand:
- F18 10B confirmed HW=46 (consistent at 1B too)
- 3-bit gap to next HW level (next found is HW=49) — wider gap than
  bit13's 4-bit gap (HW=47 → HW=51 = 4-bit gap)
- Has a non-MSB kernel (bit=3, less standard than the MSB attacks)

## Per-cand fan-out at higher HW

How many distinct residual vectors at each HW level above min:

| cand | HW+0 | HW+1 | HW+2 | HW+3 | HW+4 | HW+5 |
|---|---:|---:|---:|---:|---:|---:|
| idx8_m33ec77ca | 1 | — | — | 1 | — | — |
| bit13_m4e560940 | 1 | — | — | — | 1 | 3 |
| msb_m17149975 | 1 | 2 | 1 | 4 | 7 | 20 |
| msb_m189b13c7 | 1 | — | 2 | 1 | 3 | 18 |
| bit18_m99bf552b | 1 | 5 | 3 | 13 | 29 | 43 |

(— = no distinct vectors found at that HW level in 1B samples)

**msb_m17149975 has the FASTEST fan-out** (1, 2, 1, 4, 7, 20) — reaches
many distinct residuals quickly above min HW. This is consistent with
its known 12h kissat seed=5 SAT-finding: the residual landscape is
"fluffy" enough that kissat can find HW=0 paths via deep search.

**idx8 and bit13 have the SLOWEST fan-out** — sparse residual landscapes
near minimum, suggesting STRUCTURAL barriers separate the min-HW
vector from the rest.

## Implications for block2_wang

**Updated target ranking** (lower HW = easier Wang-style absorption):

1. **idx8_m33ec77ca**: HW=46 — new primary target. Wide gap before next
   HW level may make absorption easier (fewer "neighboring" residuals
   to manage).
2. **bit13_m4e560940**: HW=47 — secondary target. Demonstrated rigid
   structure (F24) — bit pattern symmetry (a_61 = e_61 = 0x00820042)
   may admit shared cancellation.
3. **msb_m17149975, msb_m189b13c7**: HW=49. Structurally less suitable.
4. **bit18_m99bf552b**: HW=51. Worst of the distinguished cands.

**Novel finding**: the distinguished cands cluster at the cascade-1
chamber image structural minimum. msb_m17149975's "easy SAT" comes from
a fluffy residual landscape, NOT from low minimum residual.

## Tool

`headline_hunt/bets/block2_wang/residuals/block2_lowhw_set.c` — used
identically across cands, ~23 sec per 1B-sample run on M5.

## Cross-bet update for block2_wang

Primary target shifts from msb_m17149975 (the existing block2_wang
corpus has 3787 entries for it) to **idx8_m33ec77ca** for new corpus
work. Or — given block2_wang's existing corpora are msb-focused —
extend to a NEW corpus for idx8 + bit13. Both have rigid HW=46-47
structure that's structurally novel.

EVIDENCE-level: VERIFIED at 1B samples. The "1 distinct vector at min
HW" finding is universal across 5 cands × 1B = 5 billion total samples.
