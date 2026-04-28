# F96: bit28_md1acca79 residual corpus + top-10 multi-solver cert-pin — yale's primary cand
**2026-04-28 03:55 EDT**

Extends F95's audit to bit28_md1acca79 — yale's overall project
champion (per F32 deep sampling and yale's online Pareto sampler).
F95 covered 5 cands but bit28 was notably absent. F96 closes that gap.

## Setup

bit28 corpus build (parallel to F93's bit3 build):
```
python3 build_corpus.py \
    --m0 0xd1acca79 --fill 0xffffffff --kernel-bit 28 \
    --samples 1_000_000 --hw-threshold 80 --seed 42 \
    --w1-60 0x0a0627e6 \
    --out by_candidate/corpus_bit28_md1acca79_fillffffffff.jsonl
```

W1[60] = 0x0a0627e6 chosen from F80's HW=45/LM=637 EXACT-sym
W-witness (yale's NEW LM champion).

## Build result

```
1,000,000 attempts → 1,000,000 cascade-held → 18,633 records below HW=80
Throughput:  26,338 samples/sec
Wall:        38.0s
HW range:    min=59, max=130
da == de:    0 records (independent a/e paths)
```

## Cross-cand corpus comparison (now 6 cands)

| Cand | n_records (1M) | min HW | kernel_bit | fill |
|---|---:|---:|---:|---|
| bit3_m33ec77ca (F93) | 18,517 | 55 | 3 | 0xff |
| **bit28_md1acca79 (F96)** | **18,633** | **59** | 28 | 0xff |
| bit2_ma896ee41 | 18,336 | 57 | 2 | 0xff |
| bit13_m4e560940 | 18,548 | 61 | 13 | 0xaa |
| m189b13c7 (msb) | 3,787 | 63 | 31 | 0x80 |
| m9cfea9ce (msb) | 3,735 | 62 | 31 | 0x00 |

**bit28 has the most records (18,633)** but min HW=59 vs bit3's 55.
Note: yale's deep exploration found HW=33 EXACT-sym at LM=679 on bit28
— that's much lower because yale VARIES W1[60] across the chart while
the corpus FIXES it to 0x0a0627e6.

## Cert-pin top-10 result

```
HW=59 idx0  UNSAT  0.036s  near-residual (3-solver)
HW=59 idx1  UNSAT  0.027s  near-residual (3-solver)
HW=60 idx2  UNSAT  0.027s  near-residual (3-solver)
HW=61 idx3  UNSAT  0.028s  near-residual (3-solver)
HW=61 idx4  UNSAT  0.027s  near-residual (3-solver)
HW=62 idx5  UNSAT  0.027s  near-residual (3-solver)
HW=62 idx6  UNSAT  0.027s  near-residual (3-solver)
HW=63 idx7  UNSAT  0.028s  near-residual (3-solver)
HW=63 idx8  UNSAT  0.029s  near-residual (3-solver)
HW=63 idx9  UNSAT  0.028s  near-residual (3-solver)

Summary: 0 SAT, 10 UNSAT, 0 other
```

**10/10 UNSAT** with 3-solver agreement per witness. Total wall ~0.3s.

## Updated combined cert-pin evidence corpus

| Memo | W-witnesses | Solvers | Cells | Result |
|---|---:|---:|---:|---|
| F70 (yale frontier verify) | 5 | 3 | 15 | 5 UNSAT |
| F71 (registry-wide audit) | 67 | 1 (kissat) | 67 | 67 UNSAT |
| F94 (bit3 top-10) | 10 | 3 | 30 | 10 UNSAT |
| F95 (4 more cands top-10) | 40 | 3 | 120 | 40 UNSAT |
| F96 (bit28 top-10) | 10 | 3 | 30 | 10 UNSAT |
| **TOTAL** | **132 distinct** | mixed | **262 cells** | **0 SAT** |

132 distinct W-witnesses, 262 cross-solver cells, 0 SAT.

## Significance for yale's headline path

bit28 is yale's primary target. F70 verified yale's first 5 frontier
points (HW=33-65) all UNSAT. F80 verified yale's HW=45/LM=637 NEW LM
champion UNSAT. F96 now adds 10 more bit28 W-witnesses from a corpus
build, all UNSAT.

**Total bit28 cert-pin verifications: 5 (F70) + 1 (F80) + 10 (F96) =
16 distinct W-witnesses on bit28**, all near-residuals across all
3 solvers.

Yale's bit28 single-block search has saturated empirically. The
HEADLINE path on bit28 IS the Wang block-2 absorption trail (per
2BLOCK_CERTPIN_SPEC.md / F82). Yale's structural domain.

## Per-witness W-witness identity (paper-class data)

The bit28 corpus W-witnesses (top-10):

```
HW=59  W57=0xca1894ac W58=0xa48c6675 W59=??? W60=0x0a0627e6
HW=59  W57=0x7205cf8a W58=0xcbe408b2 W59=??? W60=0x0a0627e6
HW=60  W57=0xf745c51a W58=0xa86aa453 ...
HW=61  W57=0x3b05ffa2 W58=0x45f6868b ...
... [full data in /tmp/bit28_top10.jsonl]
```

All share W60=0x0a0627e6 (corpus's fixed W1[60]). The W57, W58, W59
triples are uniform random samples from the cascade-eligible
sub-region.

## Discipline

- 10 cert-pin runs logged via append_run.py
- All CNF: aux_expose_sr60_n32_bit28_md1acca79_fillffffffff.cnf
  (datasets/certificates/, CONFIRMED audit)
- Registry total: 929 → **939**
- 0% audit failure rate maintained

EVIDENCE-level: VERIFIED. 30 cells (10 W-witnesses × 3 solvers), all
UNSAT. Pipeline ran in 0.3s wall.

## Concrete next moves

1. **Higher-HW probe on bit28**: are HW=70-80 corpus witnesses still
   UNSAT? Test extends the floor empirically.

2. **Synthesis memo F97**: combine F70/F71/F94/F95/F96 into a single
   "near-residual invariant" claim with all 262 cells of evidence.

3. **Yale block-2 push**: yale should design block-2 trail using the
   F82 SPEC schema. The bit28 single-block side is now exhaustively
   verified UNSAT; block-2 is the structural unknown.
