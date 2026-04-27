# F28: Registry-wide 1B-sample residual scan — bit2_ma896ee41 is new champion at HW=45
**2026-04-27 05:30 EDT**

Definitive 1B-sample re-run of F27 (which was at 100M). Refines the
9 → 11 exact-symmetry classification AND identifies a new block2_wang
champion 2 bits below bit13.

## Top 5 by min HW

| Rank | cand | min HW | a_61 = e_61 / asymm |
|---:|---|---:|---|
| 1 | **cand_n32_bit2_ma896ee41_fillffffffff** | **45** | **EXACT** 0x02000004 |
| 2 | cand_n32_bit3_m33ec77ca_fillffffffff (idx8) | 46 | HW=1 (0x18288001 vs 0x08288001) |
| 3 | cand_n32_bit25_m30f40618_fillffffffff | 46 | HW=1 |
| 4 | cand_n32_bit13_m4e560940_fillaaaaaaaa | 47 | **EXACT** 0x00820042 |
| 5 | cand_n32_bit13_m72f21093_fillaaaaaaaa | 47 | HW=1 |

**bit2_ma896ee41 takes the lead** with the lowest registry min HW (45)
AND exact a_61 = e_61 symmetry. This combination wasn't found in any
prior F-series scan.

## Updated EXACT-symmetry list (11 cands at 1B)

Sorted by min HW:

| cand | min HW | a_61 = e_61 |
|---|---:|---|
| **cand_n32_bit2_ma896ee41_fillffffffff** | **45** | 0x02000004 (HW=2) |
| cand_n32_bit13_m4e560940_fillaaaaaaaa | 47 | 0x00820042 (HW=4) |
| cand_n32_bit00_md5508363_fill80000000 | 48 | 0x40001004 (HW=3) |
| cand_n32_bit17_mb36375a2_fill00000000 | 48 | 0x00200040 (HW=2) |
| cand_n32_bit2_m67dd2607_fillffffffff | 48 | 0x40403000 (HW=4) |
| cand_n32_bit2_mea9df976_fillffffffff | 48 | 0x40000200 (HW=2) |
| cand_n32_bit4_md41b678d_fillffffffff | 49 | 0x00048000 (HW=2) |
| cand_n32_msb_m44b49bc3_fill80000000 | 49 | 0x80402400 (HW=4) |
| cand_n32_bit17_m427c281d_fill80000000 | 50 | 0x69000000 (HW=4) |
| cand_n32_bit1_m6fbc8d8e_fillffffffff | 51 | 0x14084000 (HW=4) |
| cand_n32_bit26_m11f9d4c7_fillffffffff | 51 | 0x14040040 (HW=4) |

## Comparison F27 (100M) vs F28 (1B)

F27 had 9 exact-symmetry cands. F28 has 11.

**Lost from F27 list at 1B** (their true min residual has asymmetry,
F27 just hadn't sampled deep enough):
- bit15_m1a49a56a, bit25_m09990bd2, bit00_mf3a909cc, bit18_meed512bc,
  bit3_m33ec77ca (idx8 — at 1B drops to HW=46 with HW=1 asymmetry)

**Added to F28 list** (deeper sampling found exact-symmetry residuals):
- bit2_ma896ee41 (HW=45, NEW LEADER), bit17_mb36375a2 (HW=48),
  bit2_m67dd2607 (HW=48), bit4_md41b678d (HW=49), msb_m44b49bc3 (HW=49),
  bit17_m427c281d (HW=50), bit26_m11f9d4c7 (HW=51)

## bit2_ma896ee41 deep dive

- m0 = 0xa896ee41
- fill = 0xffffffff
- kernel_bit = 2
- min HW residual = 45 (lowest in 67-cand registry at 1B)
- a_61 = e_61 = 0x02000004 — only bits 2 and 25 set (HW=2)

For Wang-style absorption:
- 45 bits total residual to cancel (lowest in registry)
- Of which a_61 + e_61 = 4 bits sharing 2-bit pattern (shared
  cancellation possible)
- Distinct vector count at HW=45: 1 (universal rigidity from F25)

## XOR HW distribution

| XOR HW | cands | cumulative % |
|---:|---:|---:|
| 0 (exact) | 11 | 16% |
| 1 | 18 | 43% |
| 2 | 17 | 69% |
| 3 | 10 | 84% |
| 4 | 7 | 94% |
| 5 | 4 | 100% |

vs F27 (100M) where exact was 9, HW=1 was 12, etc. The shift to deeper
samples reveals more cands have near-symmetry but FEWER are exactly
symmetric at TRUE min HW.

## Implications for block2_wang

**Updated primary target**: `cand_n32_bit2_ma896ee41_fillffffffff`
- m0 = 0xa896ee41, fill = 0xffffffff, kernel_bit = 2
- Beats bit13_m4e560940 (HW=47) by 2 bits
- Same exact-symmetry structural advantage
- Even tighter symmetric pattern: HW(a_61)=HW(e_61)=2 vs bit13's 4

**Secondary targets**: bit13_m4e560940 (HW=47, second-best), idx8
m33ec77ca (HW=46 but HW=1 asymmetric), bit25_m30f40618 (HW=46).

The block2_wang corpus should extend to bit2_ma896ee41 first (best
absorption properties), then bit13_m4e560940 (symmetric backup).

## Cross-bet implication

The "ranking shift" from F25/F26/F27 to F28 demonstrates the
importance of DEEP SAMPLING for accurate cross-cand comparison. F25
at 1B found bit13 best (in 5-cand set); F27 at 100M proposed 9
exact-symmetry cands; F28 at 1B revises both.

bit2_ma896ee41 was NOT in any prior F-series spotlight because:
- F12 cascade-1 chamber min HW: not flagged (registry tier 30+)
- F25 was 5 distinguished cands (not including bit2)
- F27 was 100M (didn't reach HW=45)

F28 1B is the FIRST scan thorough enough to find it. New target.

## Discipline

67 cand × 1B-sample logs at /tmp/deep_dig/F28/. Tool:
encoders/block2_lowhw_set.c. ~25 min total compute.

EVIDENCE-level: VERIFIED at 1B samples. The bit2_ma896ee41 finding
is robust at this sample budget; deeper (10B+) might reveal even
lower min HW for some cands.
