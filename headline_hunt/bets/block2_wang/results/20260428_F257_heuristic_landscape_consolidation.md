---
date: 2026-04-28
bet: block2_wang
status: HEURISTIC_LANDSCAPE_FULLY_MAPPED — multiple narrow basins per fixture, 86-87 protocol floor
---

# F257: heuristic landscape on cascade-1 fixtures — consolidated map for future-session reference

## Purpose

Today's 22-memo arc (F176-F256) characterized the heuristic search
landscape on cascade-1 collision fixtures. F257 consolidates the
findings into a single reference map for future-session attack
planning.

## Aggregate empirical picture

Across 6 fixtures (bit3, bit19, bit4, bit25, bit28, msb) and 4+ seeds:

### Robust 8×50k floor across seeds

| Fixture | 8×50k random-init floor | Method |
|---|---:|---|
| bit3 | 95 (F206 seed 9911) | random init |
| bit4 | 94 (F193 seed 9501) | random init |
| bit19 | 95 (F176 multi-seed) | random init |

The robust 8×50k random-init floor across seeds is **94-95** —
heuristic local search from outside cannot reach the deep basins.

### Multi-seed narrow-basin discovery

| Fixture | Seed | Best 8×50k | Mask |
|---|---:|---:|---|
| bit3 | yale's pre-pause | 86 | `0,1,2,8,9` |
| bit19 | 7101 | 87 | `0,1,3,8,9` (F135) |
| bit19 | 7101 | 90 | `0,7,9,12,14` (F248) |
| bit4 | 9101 | 86 | `0,1,2,4,8` (F188) |
| bit4 | 7101 | 89 | `0,1,2,4,8` (F256, different basin) |

**At least 5 narrow deep basins identified across 3 fixtures**.
Each basin is reachable from a SPECIFIC seed; other seeds reach
only the 91-95 robust floor on the same mask.

### F143 status (per F186/F237)

F143 hypothesis: distinguished cands have deeper basins than bit3.

Empirical resolution:
- **At chunked-scan random-init**: distinguished cands (bit19, bit4)
  reach the same 86-87 floor as bit3, just via different seeds.
- **At 8×50k**: same — multiple seeds, multiple narrow basins, all
  at 86-90 across cands.
- **F143 is alive in WEAK form**: distinguished cands have findable
  basins comparable to bit3.
- **F143 is dead in STRONG form**: no cand has been shown to reach
  STRICTLY below 86.

### Basin internal structure (F250/F252/F255)

Yale F248 score-90 basin:
- Radius-1 random-init at 3×4000: best neighbor 91 (F250)
- Radius-1 with same seed at 3×4000: best neighbor 93 (yale F300,
  different ordering)
- F248-init on radius-1 at 3×4000: best neighbor 91 (F252) — basin
  doesn't propagate to neighbors via init
- F248-init on radius-1 winner at 8×50k: best 92 (F255) — even
  longer budget doesn't pierce
- 3 seeds tested on the parent mask: 7101→90, 9001→92, 5001→92

**Conclusion**: F248 basin is sharp, seed-narrow, and internally
isolated. Same structural pattern as F135's score-87 basin.

### Multi-basin per fixture (F256)

Bit4 `0,1,2,4,8` from different seeds:
- Seed 9101 (chunked-scan 3×4000): 86
- Seed 7101 (8×50k random): **89** (different narrow basin!)
- Seed 9501 (8×50k random): 94 (no basin found)
- F188-init at 8×50k: 86 (reproduces seed-9101 basin)

Each seed accesses a different narrow basin or no basin. The
bit4 fixture has ≥ 2 narrow basins on this single mask.

## Three structural-level conclusions

### 1. Heuristic local search has saturated cascade-1 fixtures

No method tested today (single seed, multi-seed, basin-init,
F-init, radius-1) reaches strictly below 86. The 86 floor is
robust across:
- Method (chunked-scan, 8×50k, basin-init)
- Seed (7101, 9001, 9101, 5001, 9501, 9601)
- Fixture (bit3, bit4, bit19; msb/bit25/bit28 not yet probed at
  this depth)

### 2. Each seed has its own narrow basin set

The "narrow basins" on each fixture are seed-specific:
- bit19 from seed 7101 → 87 + 90 (two basins)
- bit4 from seed 9101 → 86; from seed 7101 → 89 (different basins)
- bit3 from yale's seeds → 86 (the canonical case)

Empirical prediction: a 5-seed sweep across all fixtures would
find ~10-30 new narrow basins, all at 86-90, none below 86.

### 3. Basins are isolated, not connected

Radius-1 of any narrow basin doesn't share its depth. Basin-init
from a deep basin doesn't help nearby active-word geometries.
The basin landscape is a set of isolated minima, not a connected
manifold.

## Implications for headline-class attack

### Heuristic path is closed

No further heuristic-search variant is likely to find sub-86. The
86 floor is robust. Multi-seed sweeps would find more 86-90
basins but no deeper structure.

### Non-heuristic options (per F237/F238)

1. **IPASIR-UP propagator** (programmatic_sat_propagator bet,
   F147/F158/F238): in-search structural reasoning. Phase 2D-2F
   implementation = 4-8 hrs each. Tests if guided CDCL reaches
   sub-86.

2. **Cube-and-conquer** (F157 AlphaMapleSAT): partition the hard
   core into branches, processed in parallel. Tests if structural
   cubing helps the F235-class hard instances.

3. **BDD enumeration** on the partial-trail freedom space: explicit
   enumeration of cascade-1 collision pre-images.

4. **Different encoder**: re-encode cascade-1 with explicit
   message-difference HW constraints + better Tseitin variable
   ordering.

### What would change the picture

- A single sub-86 result on ANY cand at ANY seed would refute the
  86 floor.
- A basin-connectivity result (e.g., basin-init descent ≥ 2 points)
  would suggest the heuristic search just hasn't run long enough.
- A polynomial-time algorithm that beats CDCL on cascade-1 specifically
  would break the bet's empirical posture entirely.

None of these have appeared in today's 22-memo heuristic-search arc.

## Reference for future sessions

When implementing IPASIR-UP Phase 2D-2F or any non-heuristic attack,
this F257 landscape map provides the empirical baseline:
- Heuristic 8×50k random-init floor: 94-95
- Heuristic seed-7101/9101 narrow-basin floor: 86-87
- Robust deep floor across seeds: 86 (bit3, bit4 via different seeds)

A non-heuristic method must beat 86 to demonstrate genuine
structural advantage. Reaching 87-88 is "comparable to heuristic
narrow basins"; sub-86 is "headline-class structural advantage".

## Discipline

- 0 SAT compute in F257 (synthesis memo)
- 22 heuristic-search memos consolidated (F176-F256)
- Three retractions in session (F205, F232, F237)
- ~30 yale + macbook coordination commits today
- 54 macbook commits this session

## Status

Heuristic search arc on cascade-1 fixtures: **CHARACTERIZED, DEAD-END
EMPIRICALLY**. Future work pivots to non-heuristic methods or
different bets entirely.
