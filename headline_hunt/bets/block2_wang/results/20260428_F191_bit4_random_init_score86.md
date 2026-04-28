---
date: 2026-04-28
bet: block2_wang
fixture: bit4_HW63_39a03c2d_naive_blocktwo
status: F186_PARTIALLY_FALSIFIED — bit4 reaches 86 at random init
---

# F191: bit4 chunk-0 multi-seed reveals score 86 — first distinguished cand to tie bit3's floor

## Setup

F186 reported all five distinguished cands sit 4-8 points above bit3
at random-init chunked-scan budget. That conclusion was based on
single-seed scans (F183/F184/F185 with seeds 8101/8201/8301). F188-
F190 reran chunk-0 on bit4/bit25/msb with seeds 9101/9201/9301 to
test seed-robustness.

## Single-seed vs multi-seed table

| Cand | Seed 8X01 best | Seed 9X01 best | Floor (min across seeds) | Mask family change? |
|---|---:|---:|---:|---|
| bit4 (F183/F188) | 93 | **86** | **86** | yes — `(8,12)` → `(4,8)` |
| bit25 (F184/F189) | 94 | 92 | 92 | yes — `(6,14)` → `(3,15)` |
| msb (F185/F190) | 91 | 92 | 91 | yes — `(3,4)` → `(6,10)` |
| bit28 (F178/F181) | 91 | 92 | 91 | yes — `(3,14)` → `(6,15)` |
| bit19 (F134/F180-chunk1) | 90 | 91 | 90 | yes |
| bit3 (yale, multi-seed) | 86 | 86 | 86 | stable |

## Headline finding

**bit4 chunk-0 with seed 9101 reaches score 86 at mask `{0,1,2,4,8}`.**

Verified:
```
subset 0,1,2,4,8 — best:
  score=86
  msgHW=66
  M1[:3]=['0x43a5877e', '0xd2f2572a', '0x3155382c']
  all restarts:
    restart=2: score=86  ← this restart hit the basin
    restart=0: score=98
    restart=1: score=103
```

This is the first **distinguished cand** to tie bit3's robust floor of
86 from **random initialization** at chunked-scan budget. F186's
empirical case ("all distinguished cands sit 4-8 above bit3") is
falsified by single counter-example.

## Implications

### 1. F143 alive at random-init level for bit4 specifically

The qualified F143 hypothesis "distinguished cands have at least
basins comparable to bit3 at chunked-scan budget" is now empirically
demonstrated for bit4. Whether the same holds for bit25/msb/bit28
remains open — they may need either lucky seeds, basin-init, or a
longer-budget search.

### 2. Seed noise on bit4 is 7 points

F183 → 93, F188 → 86. **Seven-point gap from seed perturbation alone.**

This is a much wider seed-noise band than bit28 (1pt) or msb (1pt).
The geometry of bit4's chunk-0 must contain a narrow but deep
basin that only some seed schedules navigate to.

This suggests the F143 hypothesis is true for bit4, but the basin
landscape is highly uneven across distinguished cands:
- bit3: shallow-and-wide good basin (86 found from many seeds)
- bit4: narrow-and-deep basin (86 reachable from rare seed 9101)
- bit19: extremely narrow basin (87 reachable only from F135 init)
- bit25/msb/bit28: no sub-91 basin found at chunked-scan random init

### 3. F186's conclusions need revision

F186 stated: "F143 falsified at random-init chunked-scan budget."
This was based on single-seed scans. With multi-seed data:
- F143 falsified for bit25/msb/bit28 at chunked-scan random init.
- F143 *holds* for bit4 at chunked-scan random init.
- bit19 ambiguous (F135-init reaches 87; random-init at 8×50k
  cannot per F176/F179).

The right framing is: **basin landscapes vary by cand. bit4 has a
findable deep basin; bit3 has a robust deep basin; other cands
require basin-init or longer budget.**

### 4. Sub-86 search path

F193 (in flight) runs 8×50k continuation on bit4's `{0,1,2,4,8}@86`
to see if longer budget descends below 86. If yes, **first sub-86
basin would be on bit4, not bit3**, and the cand-level structural-
distinction would have empirical support — distinguished cand
beats bit3 baseline.

This is a potentially headline-class finding. Whether it materializes
depends on F193's outcome.

### 5. Multi-seed protocol pays off

This memo's existence justifies the multi-seed protocol shift
proposed in F180/F186. Bit4's 86 was invisible to F183's single-seed
chunked-scan; only F188's seed-9101 retry revealed it. **Single-seed
chunked-scan campaigns can systematically miss deep basins.**

For ongoing fleet work (yale's bit19 chunks 9-33, macbook's
distinguished-cand scans), 2-3 seeds per chunk is now the
appropriate baseline.

## What's NOT being claimed

- That bit4 has a sub-86 basin (F193 will tell us at 8×50k).
- That bit4 always reaches 86 at random init (only seed 9101 hit it).
- That all distinguished cands have hidden deep basins (only bit4
  demonstrated so far; bit25/msb/bit28 single-counter-example
  budget-doubled and didn't find sub-91).

## Discipline

- 0 SAT compute (heuristic local search)
- 0 solver runs
- Multi-seed reproducibility revealed bit4's deep basin
- 8×50k continuation (F193) launched in parallel; result pending

## Headline-relevance

This is the first finding of the session that points TOWARD a
headline rather than away. Cross-fixture basin propagation (F187)
and bit4's score-86 random-init basin (F191) together suggest the
following narrative is empirically supported:

> SHA-256 cascade-1 absorber search on Wang-2026 cand catalogs has
> a non-trivial basin landscape. Multiple cands have sub-90
> message-pair basins findable via either lucky seeds (bit3, bit4)
> or basin-init from a known seed (bit19, bit28). The basin floor
> on at least one distinguished cand (bit4) ties the default
> baseline (bit3) at score 86. Whether any cand has a sub-86
> basin is the open headline-class question.

The next 30-60 minutes' work focuses on F193's outcome and on
running F187-style basin-init tests on bit4/bit25/msb to map
where else the deep basins live.
