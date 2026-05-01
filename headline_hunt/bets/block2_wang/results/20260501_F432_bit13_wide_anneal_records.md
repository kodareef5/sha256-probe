---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_NEW_SUB_FLOOR_HW50
parent: F408 annealed bridge beam (panel: bit2/3/24/28); bit13 was in CANDS but not in F408 panel
evidence_level: EVIDENCE
compute: 0 solver search; 112.7s pure W-space annealing + 4 audited cert-pin solver checks
author: macbook-claude
---

# F432: bit13 wide anneal — new sub-floor records HW=50 (and HW=51)

## Setup

bit13_m916a56aa was F378's "surprise top-1" — it surfaced from the
bridge selector as the highest-scoring cand among non-F374 dominators,
yet it was **not** in F408's wide-anneal panel (codex's F408 ran
bit2/bit3/bit24/bit28 only). bit13's pre-F408 corpus floor was HW=59.

F432 fills that gap: F408-style wide anneal on bit13 only.

Parameters (matching F408):

- 200,000 iter / restart × 12 restarts (random init)
- max_flips = 6
- temp 2.0 → 0.05
- tabu = 512
- 0 SAT solver runs during search

Total wall: 112.7s. 1 cand × 12 seeds × 200k iter = 2.4M evaluations.

Artifact: `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F432_bit13_wide_anneal.json`.

## Results

12 restarts produced a wide HW distribution (in contrast to bit24/bit28
which had narrow basins around their best). Sub-floor results are bold:

| Seed | Score | HW | W1[57..60] |
|---:|---:|---:|---|
| 0  | 60.94 | 57 | … |
| 1  | 63.47 | 57 | … |
| 2  | 65.29 | 55 | 0x55e6c966 0x2159500a 0xaca94730 0x1f22adf7 |
| 3  | 45.55 | 59 | … |
| **4** | **69.78** | **50** | **0x3c2de1c6 0x05e5f5a9 0x1a6a8f8d 0x5ab11fc1** |
| 5  | 53.76 | 59 | … |
| 6  | 60.94 | 57 | … |
| 7  | 57.51 | 56 | … |
| 8  | 46.40 | 62 | … |
| 9  | 42.97 | 63 | … |
| **10** | 66.82 | **50** | 0xa1d4f4df 0x208b7ee1 0x7ded1e58 0xae02509c |
| **11** | **71.55** | 51 | 0x73ef3567 0xbda14907 0x8f4d3a2f 0xd74363fb |

**Two seeds (4 and 10) found HW=50** — the lowest residual on bit13
seen so far. **Seed 11 found HW=51** at the highest bridge_score.

This is a 9-point HW reduction from corpus floor (59 → 50), comparable
to bit24's 14-point and bit28's 14-point F408+F428 reductions.

## Two cert-pin records

Both the HW-best (50) and the score-best (51) witnesses are
distinct W vectors. Cert-pin verified each:

### HW=50 witness (seed 4)

```
W1[57..60] = 0x3c2de1c6 0x05e5f5a9 0x1a6a8f8d 0x5ab11fc1
W2[57..60] = 0x06fa262a 0xef7e298e 0xdcf02ff6 0xe7ef3eba
hw63       = [10, 12, 2, 0, 14, 10, 2, 0]   (total 50)
diff63     = [0x9d041083, 0x7610c40e, 0x00014000, 0x00000000,
              0x78fa8444, 0x3111cc10, 0x00014000, 0x00000000]
active_regs = {a,b,c,e,f,g}, da_eq_de=False, c=2, d=h=0
```

- audit verdict: **CONFIRMED**
- cnf_sha256: `4a8fc4c828050605fd52675db38bcb82d1354735c6f05a2836ca2463451399a6`
- kissat 4.0.4: **UNSAT** in 0.009s
- cadical 3.0.0: **UNSAT** in 0.0149s

### HW=51 witness (seed 11)

```
W1[57..60] = 0x73ef3567 0xbda14907 0x8f4d3a2f 0xd74363fb
hw_total = 51, score = 71.551
```

- audit verdict: **CONFIRMED**
- cnf_sha256: `dca079aafa872829e5a74462d8a65121778c1b0c6015b7dd109846171a49f5ee`
- kissat: **UNSAT** in 0.009s
- cadical: **UNSAT** in 0.016s

All 4 cert-pin runs logged via `append_run.py`.

## Findings

### Finding 1: bit13's residual basin is wider than the F408 panel cands

Looking at HW distribution across 12 seeds:

| Cand | F408/F432 HW range | Best | # seeds at best |
|---|---|---:|---:|
| bit24 (F408) | 49 — 57 | 49 | 1 |
| bit28 (F408) | 45 — 59 | 45 | 1 |
| bit3 (F408) | 51 — 55 | 51 | 1 |
| bit2 (F408) | 51 — 56 | 51 | 1 |
| **bit13 (F432)** | **50 — 63** | **50** | **2** |

bit13 has the largest range AND multiple seeds at its best — suggests
bit13's W-cube has a wider deep-residual region than the F408 panel.

### Finding 2: bit13's HW=50 has c=2 (vs the panel's c=1)

The 4 panel cands (bit2/3/24/28) all reached HW≤45 records with `c=1`
in hw63. bit13's HW=50 records have `c=2`. Different geometry.

This suggests the bit13 records are in a different region of W-cube
than the F408 panel records — possibly with a different cascade-1
fingerprint sub-class. Worth a follow-up (F433) to see whether
bit13's c=2 region has further sub-floor potential at radius > 3.

### Finding 3: score and HW disagree again (matches F427)

Seed 4 (HW=50, score 69.78) and seed 11 (HW=51, score 71.55) sit at
distinct W points. The score-best is HW-worse by 1, mirroring F427's
bit28 finding (different W's optimize different objectives by ±1-2).

This is consistent: bridge_score and HW are not isomorphic; bridge
selector rewards structural features (c/g asymmetry, dominator bits)
that don't perfectly track HW.

### Finding 4: bit13 corpus state after F432

| Cand | Pre-F408 floor | Post-F408 best | Post-F428 best | Post-F432 best |
|---|---:|---:|---:|---:|
| bit3 | 55 | 51 | 51 | (n/a) |
| bit2 | 56 | 51 | 51 | (n/a) |
| bit24 | 57 | 49 | **43** | (n/a) |
| bit28 | 59 | 45 | 45 | (n/a) |
| bit13 | 59 | (skipped) | (skipped) | **50** |

Path C residual records on the 5-cand panel are now:
bit24 43, bit28 45, bit13 50, bit3 51, bit2 51.

## Verdict

- **bit13 HW=50** (and HW=51 score-best) cert-pin verified UNSAT,
  registry-disciplined.
- 9-point HW reduction below pre-F408 corpus floor of 59.
- bit13 joins bit24 and bit28 as deep-residual records (HW ≤ 50).

## Next

1. **F433: seeded refinement on bit13** (max_flips=3 around HW=50
   witness, like F428). Test whether the 2-bit W1[60] perturbation
   pattern reaches HW < 50 on bit13. ~3 min.
2. **F434: bit13 with c=1 constraint** to see whether forcing c=1
   forecloses or enables a deeper sub-floor on bit13.
3. **Other untouched cands**: there are kbits 5, 10, 14, etc. that
   were never in F374-F408's deep-tail dominator panel. Each could
   give an analogous F432-style result. Time-boxed scan.
4. **Move on**: this F432 result might be enough for the day; pivot
   to sr61_n32 or pause for codex's quota reset (13:22 EDT).

The wider basin on bit13 (12 seeds spanning HW 50-63) suggests the
W-cube structure depends meaningfully on kbit. Some kbits have narrow
deep-residual wells; others have wider basins. Knowing which is
which is structural information for future Path C panels.
