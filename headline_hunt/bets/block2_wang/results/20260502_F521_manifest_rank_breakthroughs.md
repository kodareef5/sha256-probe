---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT24_AND_BIT3_NEW_RECORDS_VIA_MANIFEST_RANK
parent: F520 bit2/bit3 HW=39; F487 bit13 manifest-rank breakthrough pattern
evidence_level: EVIDENCE
compute: 9 parallel pair-beam runs (~7 min wall on 10 cores); 6 audited cert-pin solver checks
author: macbook-claude
---

# F521: manifest-rank pair-beam cracks bit24's 9-attempt wall (HW 43→40) and pushes bit3 deeper (HW 39→36)

## Setup

F520 found bit2 and bit3 each broke HW 51 → 39 in single pair-beam runs.
F521 applies the F487 manifest-rank pattern (which took bit13 50 → 35 via
multi-step seeded chains) to extend deeper.

Workflow:
1. Generated basin manifests for bit2, bit3, bit24 by mining their pair-beam
   artifacts via `extract_basin_seeds.py`.
2. Picked top-K manifest seeds at HW *above* current best (rank 2..4).
3. Launched pair-beam from each manifest seed, 9 runs in parallel.
4. Cert-pin verified each new sub-floor record.

Per-cand manifests:
- bit2: 40 seeds spanning HW 39..51 (`20260502_F521_bit2_basin_manifest.json`)
- bit3: 44 seeds spanning HW 39..51 (`20260502_F521_bit3_basin_manifest.json`)
- bit24: 25 seeds spanning HW 43..52 (`20260502_F520_bit24_basin_manifest.json`)
- bit28: 35 seeds (generated for future use, not consumed in F521)

Pair-beam parameters (matching F486/F487):
- pair pool 1024 × beam 1024 × max_pairs 6 × max_radius 12
- pair-rank hw, c+g penalty 2

## Results

| Cand | Seed source | Init HW | F521 best HW | Δ | Score |
|---|---|---:|---:|---:|---:|
| bit24 | manifest rank2 (HW=44) | 44 | 43 | 0 | 79.07 |
| **bit24** | **manifest rank3 (HW=44)** | **44** | **40** | **−3** | **74.41** |
| bit24 | manifest rank4 (HW=45) | 45 | 43 | 0 | 74.10 |
| bit2 | manifest rank2 (HW=43) | 43 | 41 | -2 (vs F520) | 77.51 |
| bit2 | manifest rank3 (HW=43) | 43 | 39 | 0 (vs F520) | 82.76 |
| bit2 | manifest rank4 (HW=44) | 44 | 39 | 0 | 82.76 |
| **bit3** | **manifest rank2 (HW=40)** | **40** | **38** | **−1** | 75.75 |
| **bit3** | **manifest rank3 (HW=40)** | **40** | **38** | **−1** | 81.86 |
| **bit3** | **manifest rank4 (HW=42)** | **42** | **36** | **−3** | **85.47** |

Three cands now have new sub-floor records: bit24 HW=40, bit3 HW=36 + HW=38.
bit2 stayed at F520's HW=39 across 3 manifest seeds.

## Witnesses

### bit24 HW=40 (NEW; was 43)

```
W1[57..60] = 0x4be5074f 0x429efff2 0xf09458a7 0xa4fe0078
hw63 = [6, 12, 4, 0, 9, 7, 2, 0]   total 40
score = 74.412
active_regs = {a,b,c,e,f,g}
```

vs F428's HW=43 W1: `0x4be5074f, 0x429efff2, 0xe09458af, 0xe6560e70`
- W1[57], W1[58]: identical (preserves the W[57]/W[58] fixity pattern)
- W1[59]: 0xe09458af → 0xf09458a7 (3 bits flipped: positions 3, 28; same lane diff)
- W1[60]: 0xe6560e70 → 0xa4fe0078 (multi-bit flip)

### bit3 HW=36 (NEW; was 39)

```
W1[57..60] = 0xba476635 0x8cf9982c 0x06b9e787 0x2b032ff3
hw63 = [13, 2, 1, 0, 12, 7, 1, 0]   total 36
score = 85.471
active_regs = {a,b,c,e,f,g}
```

vs F520's HW=39 W1: `0xba476635, 0x8cf9982c, 0x06b9e787, 0x5882674c`
- W1[57], W1[58], W1[59]: identical (W[57..59] fully fixed at HW≤36)
- W1[60]: 0x5882674c → 0x2b032ff3 (multi-bit flip)

This sharpens F520's pattern: at the HW=36 layer for bit3, the breakthrough
is **purely a W1[60] flip from F520's HW=39**.

### bit3 HW=38 score-best (NEW)

```
W1[57..60] = 0xba476635 0x8cf9982c 0x06b9e787 0x2b0326e8
hw63 = [11, 9, 2, 0, 8, 7, 1, 0]   total 38
score = 81.857
```

Differs from HW=36 only in W1[60] last 8 bits (0x2b032ff3 vs 0x2b0326e8).
Confirms bit3's HW≤38 layer is a tight (W1[60])-only manifold near HW=36.

## Cert-pin verification

All 3 records audited CONFIRMED + cross-solver UNSAT:

| Witness | cnf_sha256 (prefix) | kissat | cadical |
|---|---|---|---|
| bit24 HW=40 | `05214996...` | UNSAT 0.008s | UNSAT 0.015s |
| bit3 HW=36 | `4de86588...` | UNSAT 0.006s | UNSAT 0.011s |
| bit3 HW=38 | `87368321...` | UNSAT 0.006s | UNSAT 0.012s |

6 runs logged via append_run.py.

## Findings

### Finding 1: manifest-rank cracked bit24 after 9 direct attempts failed

Yale ran pair-beam on bit24 from HW=43 init 8 times (F441, F443-F447, F450,
F457, F485) — all stuck at HW=43. F520 (rank-1, this) was the 9th — also
stuck. F521 rank-3 manifest seed (init at HW=44, *not* the current best)
broke through to HW=40.

This is the **same diagnosis F487 made for bit13**: the breakthrough seed
is in a *different basin* than the current best. Direct hill-climbs from
HW=43 cannot escape; restart from HW=44 in a different W-cube neighborhood
descends to HW=40.

The "best next seed is not always the current record" principle (F467/F473
discovery) generalizes from bit13 to bit24.

### Finding 2: rank-K matters; rank-2 and rank-4 differ from rank-3

For bit24, rank-2 and rank-4 manifest seeds did NOT break HW=43, but
rank-3 did. For bit3, rank-2 and rank-3 reached HW=38 (-1 from F520),
but rank-4 reached HW=36 (-3). Specific manifest seeds matter — basin
geometry varies sharply across nearby seeds.

This argues for systematic rank-K sweeps when applying manifest-rank, not
just rank-2/3. F487 itself was rank-12 of bit13's HW=41 manifest.

### Finding 3: W[57..59] becomes more fixed as HW deepens

| HW level | bit3 W1[57] | bit3 W1[58] | bit3 W1[59] | bit3 W1[60] |
|---|---|---|---|---|
| 51 (F408) | 0xba476635 | 0x8cf9982c | 0x0699c787 | 0x8893274d |
| 39 (F520) | 0xba476635 | 0x8cf9982c | 0x06b9e787 | 0x5882674c |
| 38 (F521) | 0xba476635 | 0x8cf9982c | 0x06b9e787 | 0x2b0326e8 |
| 36 (F521) | 0xba476635 | 0x8cf9982c | 0x06b9e787 | 0x2b032ff3 |

W1[57] frozen since F408. W1[58] frozen since F408. W1[59] frozen since F520
(at 0x06b9e787, differs by 1 bit from F408's 0x0699c787). W1[60] is the
only word evolving across HW levels.

This is concrete structural evidence: at the deep layers of bit3's
residual basin, **the entire W-cube reduces to a 32-bit search in W1[60]**
with W[57..59] fixed.

For bit24 HW=40, W1[57] and W1[58] are still frozen, but W1[59] DID flip
(0xe09458af → 0xf09458a7). So bit24's geometry differs from bit3 — it
needs both W1[59] and W1[60] perturbations to break through.

### Finding 4: Path C panel state after F521

| Cand  | Pre-F408 | F408 best | Today's deepest | Δ from pre-F408 |
|---|---:|---:|---:|---:|
| bit3  | 55 | 51 | **36** (F521) | −19 |
| bit2  | 56 | 51 | 39 (F520) | −17 |
| bit24 | 57 | 49 | **40** (F521) | −17 |
| bit28 | 59 | 45 | 42 (Yale F484) | −17 |
| bit13 | 59 | (skipped) | 35 (Yale F487) | −24 |

Sum: 286 → 192 = **−94 HW** across the 5-cand panel. All cert-pin UNSAT.

bit13 still leads at HW=35; bit3 closing fast at HW=36.

## Verdict

- **bit24 HW=40 + bit3 HW=36 + bit3 HW=38**: three new cert-pin'd records.
- Manifest-rank pair-beam **transferred** from bit13 (Yale F487) to bit3
  and bit24. Same workflow, same kind of breakthrough.
- bit2 stayed at HW=39 (3 manifest seeds tried, none beat F520).
- Path C panel total HW reduction since pre-F408: **94 HW**.

## Next

1. **F522 wider rank-K sweep on bit2 and bit24**: try ranks 5-12 of each
   manifest. F487 was rank-12 of HW=41; rank-3 of bit24 HW=44 worked here;
   the right seed may be at higher rank for cands not yet broken.
2. **Generate post-F521 manifests** for bit3 (HW=36) and bit24 (HW=40),
   then run rank-K pair-beam from those to extend further.
3. **Cross-cand W1[60] transfer**: bit3 HW=36 W1[60] = 0x2b032ff3 — does
   that mask flipped from current bests of other cands give improvement?
4. **F523: focused W1[60]-only search** on bit3 from HW=36, exhaustive
   over ~2^32 candidate W1[60] values is infeasible but Hamming-{1..5}
   over 32 bits is 32+496+4960+35960+201376 = ~243K, ~5s. Direct
   confirmation that W1[60] is the only direction.

The F521 result demonstrates the manifest-rank pattern is not bit13-specific
— it transfers. The Path C residual program now has a clear playbook:
generate manifest, pick rank-K above current, pair-beam, iterate.
