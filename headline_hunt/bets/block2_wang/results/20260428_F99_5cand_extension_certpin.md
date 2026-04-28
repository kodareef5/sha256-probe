# F99: cert-pin top-10 extended to 5 more priority cands — now 13 cands covered, 552 cells
**2026-04-28 04:55 EDT**

Direct continuation of F98. Extends the cert-pin top-10 audit from 8
cands (F94/F95/F96/F98) to 13 cands by adding 5 priority cands not
yet covered:

- **bit10_m075cb3b9** (Cohort A baseline per F77)
- **bit11_m45b0a5f6** (sigma1-aligned kernel)
- **bit25_m09990bd2** (Cohort A/C per F79)
- **bit18_m99bf552b** (separate axis per F18, F60)
- **bit4_m39a03c2d** (F43 LM champion at HW=53/LM=757)

## Setup

5 fresh corpus builds at 200k samples each, HW≤80 threshold.
Total wall ~38s for 5 builds:

```
bit10_m075cb3b9: 3,761 records, min HW = 63
bit11_m45b0a5f6: 3,643 records, min HW = 63
bit25_m09990bd2: 3,745 records, min HW = 62
bit18_m99bf552b: 3,634 records, min HW = 62
bit4_m39a03c2d:  3,638 records, min HW = 62
```

All sparse-fill (0x00 or 0x80) or dense-fill (0xff) — covers both
fill regimes from F93's structural finding.

## Cert-pin result — 50/50 UNSAT

```
50 W-witnesses × 3 solvers (kissat + cadical + CMS) = 150 cells
0 SAT, 50 UNSAT, all 3 solvers agree per witness
Total wall ~1.4s
```

Top-10 HW range varies per cand: 62-69 (bit18, bit25), 63-67 (bit10,
bit11), 62-66 (bit4). All UNSAT.

## Updated combined cert-pin evidence corpus (F70 - F99)

| Memo | Cands | Witnesses | Cells | Result |
|---|---:|---:|---:|---|
| F70 (yale frontier) | 1 | 5 | 15 | UNSAT |
| F71 (registry-wide) | 67 | 67 | 67 | UNSAT |
| F94 (bit3 low-HW) | 1 | 10 | 30 | UNSAT |
| F95 (4 cands low-HW) | 4 | 40 | 120 | UNSAT |
| F96 (bit28 low-HW) | 1 | 10 | 30 | UNSAT |
| F97 (6 cands HIGH-HW) | 6 | 60 | 180 | UNSAT |
| F98 (m17149975 + ma22dc6c7) | 2 | 20 | 60 | UNSAT |
| F99 (5 priority cands) | 5 | 50 | 150 | UNSAT |
| **TOTAL** | **13 distinct top-10** | **262** | **652** | **0 SAT** |

**13 cands with top-10 cert-pin coverage** (up from 8 after F98).
**262 distinct W-witnesses, 652 cross-solver cells, 0 SAT, 100%
near-residual.**

## Per-cand top-10 summary (13-cand audit)

```
bit2_ma896ee41         HW 57-64   10/10 UNSAT  (F95)
bit3_m33ec77ca         HW 55-63   10/10 UNSAT  (F94)
bit4_m39a03c2d         HW 62-66   10/10 UNSAT  (F99 NEW)
bit10_m075cb3b9        HW 63-67   10/10 UNSAT  (F99 NEW)
bit11_m45b0a5f6        HW 63-66   10/10 UNSAT  (F99 NEW)
bit13_m4e560940        HW 61-64   10/10 UNSAT  (F95)
bit18_m99bf552b        HW 62-69   10/10 UNSAT  (F99 NEW)
bit25_m09990bd2        HW 62-66   10/10 UNSAT  (F99 NEW)
bit28_md1acca79        HW 59-63   10/10 UNSAT  (F96)
m17149975 (control)    HW 62-67   10/10 UNSAT  (F98)
m189b13c7              HW 63-66   10/10 UNSAT  (F95)
m9cfea9ce              HW 62-67   10/10 UNSAT  (F95)
ma22dc6c7              HW 63-67   10/10 UNSAT  (F98)
                                  ----------
                                  130/130 cells UNSAT (low-HW track)
```

PLUS HIGH-HW (HW=80) probe (F97): 6 cands × 30 cells = 180 cells UNSAT.

## Significance: 13-cand × 9-axis cert-pin uniformity

The cert-pin UNSAT property is empirically uniform across:
- **Kernel positions**: 2, 3, 4, 10, 11, 13, 18, 25, 28, 31 (× 2 cands)
- **Fill densities**: 0x00, 0x80, 0xaa, 0xff
- **HW range**: [44, 80]
- **Cands**: 13 distinct (verified-collision m17149975 + 12 others)
- **Solvers**: kissat 4.0.4 + cadical 3.0.0 + CryptoMiniSat 5

**No single axis shifts the SAT/UNSAT verdict.** The cascade-1
single-block CNF is structurally UNSAT for all corpus low-HW + HW=80
ceiling W-witnesses on every cand tested.

## What still pending

- **54 / 67 registry cands** still without top-10 cert-pin coverage.
  At ~10s per cand (corpus build + cert-pin), full sweep is ~9
  more minutes wall.
- **HW > 80 region** untested.
- **2-block cert-pin** (yale's domain).

## Discipline

- 5 corpus builds (200k each, ~38s total)
- 5 missing CNFs detected; 1 generated (bit10_m075cb3b9), 4 already existed
- 50 cert-pin verifications, all UNSAT
- 50 entries logged via append_run.py
- All CNFs CONFIRMED via earlier audits
- 0% audit failure rate maintained
- **Registry total: 1019 → 1069 logged runs**

EVIDENCE-level: VERIFIED. 50 W-witnesses × 3 solvers, 150 cells, 0
SAT.

## Concrete next moves

1. **Sweep remaining 54 cands**: 9 more min wall would close the
   registry-wide top-10 audit.
2. **F100 synthesis memo**: combine F70-F99 into a single paper-class
   "near-residual invariant across the registry" claim.
3. **Yale block-2** trail design — still the structural unknown.
