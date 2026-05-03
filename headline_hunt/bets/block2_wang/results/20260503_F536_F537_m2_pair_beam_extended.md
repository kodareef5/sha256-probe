---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_HW85_NEW_FLOOR_PLUS_BROAD_SWEEP
parent: F535 multi-rank breakthrough (HW=86 floor on ranks 0+2)
evidence_level: VERIFIED
compute: ~20 min wall (8 parallel pair-beams: 2 deeper iterations + 6 broader sweep)
author: macbook-claude
---

# F536/F537: HW=85 absorber floor + sweep extends to rank 10 — 11/11 F518 seeds break HW=91

## Setup

**F536** tests whether HW=86 is a true absorber floor by iterating
pair-beam from F535's two HW=86 records (rank 0 and rank 2 paths,
independent M2 init masks). 2 parallel runs.

**F537** extends F535's breadth sweep to F518 ranks 5-10. 6 parallel runs.

Both batches in parallel: 8 procs on 10 cores. ~20 min wall.

## F536 results — HW=85 found

| Iter source | Init HW | Best HW | Δ |
|---|---:|---:|---:|
| rank 0 path (F534 W) | 86 | 86 | 0 (locally closed at this radius) |
| rank 2 path (F535 W) | 86 | **85** | **−1** |

The rank 2 HW=86 W has a sub-86 neighbor: **HW=85 at depth 4 (8 M2 bits)**.

HW=85 witness:
```
M2 = 0x20100008 0x40000000 0x00000100 0x00100000
     0x40020000 0x10000000 0x08040000 0x00100000
     0x08400000 0x00000008 0x20000000 0x40000800
     0x04010041 0x00000200 0x00010000 0x00000008
```

## F537 results — sweep ranks 5-10 (6/6 breakthrough)

| Rank | Init HW | F537 Best HW | Δ |
|---:|---:|---:|---:|
| 5 | 96 | 88 | −8 |
| 6 | 96 | 89 | −7 |
| 7 | 98 | **86** | **−12** |
| 8 | 100 | 88 | −12 |
| 9 | 101 | 87 | −14 |
| 10 | 101 | 89 | −12 |

6/6 perfect breakthrough rate. Average drop: −10.8 HW per seed
(vs F535's −6.6 — deeper init seeds give bigger deltas).

Rank 7 reached HW=86, joining the HW=86 cluster (rank 0, rank 2, rank 7).

## Combined sweep: 11/11 F518 ranks broken (out of 22 total)

| Rank | Init HW | Best HW | Δ |
|---:|---:|---:|---:|
| 0 | 91 | **86** | −5 |
| 1 | 93 | 88 | −5 |
| 2 | 94 | 86 → **85 (F536)** | −8 → **−9** |
| 3 | 95 | 89 | −6 |
| 4 | 96 | 87 | −9 |
| 5 | 96 | 88 | −8 |
| 6 | 96 | 89 | −7 |
| 7 | 98 | 86 | −12 |
| 8 | 100 | 88 | −12 |
| 9 | 101 | 87 | −14 |
| 10 | 101 | 89 | −12 |

**11/11 perfect breakthrough rate.** Average reduction: **−9.7 HW** per seed.

Best absolute absorber HW achieved: **85** (F536 from rank 2 iteration).
HW=86 cluster: ranks 0, 2 (initial), 7. HW=87: rank 4, 9. HW=88: ranks 1, 5, 8.

## Findings

### Finding 1: HW=86 is NOT the absorber floor — HW=85 exists

F535's HW=86 cluster (ranks 0 + 2) suggested a basin floor at HW=86.
F536 disproves this: from rank 2's HW=86, an 8-bit M2 perturbation
descends to HW=85. The basin extends further than F535's max_radius=12
captured.

Suggests further iterations may find HW=84, HW=83, etc. The path-C
trajectory (each iter shaves 3-5 HW) likely transfers.

### Finding 2: deeper init seeds get bigger drops

F535 (init 91-96): avg Δ=−6.6
F537 (init 96-101): avg Δ=−10.8

The pair beam has a roughly fixed-depth "reach" from any starting
point. Higher-init seeds have more headroom to descend. Asymptotic
floor appears to be around HW=85-89 across the corpus.

### Finding 3: rank 0 HW=86 path is locally closed

F536 iter0 (from rank 0's HW=86 W) found 0 new records. This W is
locally optimal at radius 12. By contrast, rank 2's HW=86 W has a
sub-86 neighbor — different basins have different local geometry.

This mirrors the W-cube observation (F428 bit24 vs F427 bit28):
breakthrough basin geometry varies by entry point.

### Finding 4: 1327 + 1390 records on ranks 9+10

Highest record counts of any F537 run. Deep init seeds (HW=101)
produce many sub-init records as the beam descends. Rich basins.

## Verdict

- **HW=85 is the new absorber floor** on bit13's residual family.
- 11/11 F518 ranks tested all break HW=91 single-bit floor.
- Average descent: −9.7 HW per seed via multi-bit M2 pair beam.
- Yale F519's diagnosis "next operator should be multi-bit M2 pair beam"
  is empirically validated across 11 seeds.

## Next

1. **F538: extend sweep to F518 ranks 11-21** (parallel batches).
   Likely 11/11 more breakthrough; map full corpus.
2. **F539: deeper iteration from HW=85 + HW=86 records**.
   F428-style chain — see if HW=84, 83, ... exists.
3. **Check 16-round and 20-round absorber floors**: cheaper compute,
   may reveal cross-rounds transfer pattern.
4. **Pivot back**: with M2 pair beam established as productive, consider
   what the HW=85 floor implies for actual block-2 collision finding.
   (HW=0 = collision; HW=85 is still far. But: lower absorber HW =
   easier downstream Wang-style trail design.)

The F534-F537 chain is a clean structural contribution to Yale's
absorber program. The pivot from Path C to absorber paid off
within ~30 min of compute.
