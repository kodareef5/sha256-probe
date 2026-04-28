---
date: 2026-04-28
bet: block2_wang
fixture: bit3_HW55_naive_blocktwo
status: BIT3_BASIN_ALSO_NARROW — universal narrow-basin pattern confirmed
---

# F206/F207: bit3's score-86 basin is also narrow at 8×50k random init

## Critical sanity check after F205

F205 documented that chunked-scan sub-90 results on bit25/bit28/msb
were transient minima at 4000 iter that don't survive 8×50k. The
natural follow-up: **is bit3's score-86 basin itself robust at 8×50k
random init, or also transient?**

Yale's pre-pause campaign reproduced bit3 `{0,1,2,8,9}@86` across
multiple seeds at chunked-scan budget. But that's the chunked-scan
budget. F206 asks: does 8×50k random init also reach 86?

## Result

8×50k random init on bit3 `{0,1,2,8,9}` (8 restarts × 50000 iter):

```
all 8 restarts:
  restart=2: score=95  msgHW=90
  restart=0: score=96  msgHW=79
  restart=1: score=96  msgHW=85
  restart=3: score=97  msgHW=89
  restart=4: score=97  msgHW=79
  restart=6: score=97  msgHW=85
  restart=7: score=98  msgHW=75
  restart=5: score=99  msgHW=87
BEST: 95
```

**No restart reaches 86.** The basin is invisible to 8×50k random
init from outside.

## Universal pattern across all cands

Compare with prior 8×50k random-init results:

| Cand | Mask | 8×50k random-init best |
|---|---|---:|
| bit3 (F206) | `0,1,2,8,9` | **95** |
| bit4 (F193) | `0,1,2,4,8` | **94** |
| bit19 (F176) | `0,1,3,8,9` | **95** |

**All three known sub-90 basins are equally inaccessible from random
8×50k init.** The pattern is universal: chunked-scan finds these
basins via lucky seeds, but 8×50k random init from outside cannot.

## Refined understanding of "robust"

I had been calling bit3's 86 "robust" because yale's chunked-scan
campaign reproduced it across multiple seeds. F206 reveals what
"robust" actually means in this context:

> *Robust at chunked-scan budget* (4000 iter): yale's seed schedule
> happened to land in the basin from multiple seeds, so the result
> is reproducible at that budget.
>
> *Not robust at 8×50k random init*: Even with 12.5× the budget per
> restart, random init cannot find the basin from outside.

The bit3@86 basin is narrow in the same sense as bit4@86 (F188 +
F193) and bit19@87 (F135 + F176). All three are findable only at
chunked-scan budget via specific seed schedules.

## Implication for F143

F143's strong form (distinguished cands have *deeper* basins than
bit3) was dead at 8×50k.

F143's weak form (distinguished cands have *comparable* basins) is
now empirically saturated: bit3's basin is the same narrow type as
bit4's, just with more seeds known to land in it. There is no
structural distinction in basin **geometry** between bit3 and bit4.

The remaining "soft" F143 form would be: *some seeds reproducibly
reach the bit3 basin*, while *other distinguished cands have
basins reachable from fewer seeds*. That's a quantitative not
structural difference.

## Implication for the 86 protocol floor

The 86 protocol floor stands. Every method tested today:
- 4000-iter chunked-scan + lucky seeds: reaches 86 (bit3, bit4) /
  87 (bit19).
- 8×50k random init: reaches 94-95 across cands (basin invisible
  from outside).
- 8×50k basin-init: reaches 86-87 (reproduces seeded basin; no
  descent).
- Cross-fixture basin-init at 4000 iter: gives transient minima
  that don't survive 8×50k.

**No method pierces 86.** The basin landscape on cascade-1
absorber search has 86 as a hard floor at all tested protocols.

## What we now know about the basin landscape

1. Each cand fixture has at least one narrow deep basin findable
   via chunked-scan at lucky seeds.
2. All such basins sit at score 86-87 (with the exception of those
   not yet discovered).
3. None of these basins is reachable from 8×50k random init.
4. Once seeded, basin-init at 8×50k reproduces the basin floor
   without descent.
5. Cross-fixture basin propagation does NOT find sub-86 — it
   reaches the same 86-87 floor, not lower.

This is the **complete empirical picture** at heuristic local
search. Sub-86 requires methods outside this paradigm.

## Honest synthesis of the day's arc

**Confirmed facts**:
- bit3 has a narrow basin at score 86 (yale, multi-seed at 4000 iter).
- bit4 has a narrow basin at score 86 (F188, single seed at 4000 iter;
  reproduced via F188-init at 8×50k in F194).
- bit19 has a narrow basin at score 87 (F135, single seed at 4000 iter;
  reproduced via F135-init at 8×50k in yale's F173/F174).
- All three basins are equally inaccessible from 8×50k random init.
- 86 is the empirical protocol floor.

**Refuted claims**:
- "F135 is dominant universal seed" — partially right but mostly
  reflects F135 init being at restart 0 of chunked scans where
  random restarts also produce transient minima.
- "All 6 distinguished cands have sub-90 basins" — only bit3, bit4,
  bit19 have verified sub-90 at 8×50k. bit25/bit28/msb sub-90 results
  did not survive verification.
- "bit3 has robust deep basin while others don't" — bit3's basin is
  the same narrow type; "robust" applies to chunked-scan-budget
  reproducibility only.

## Headline status

The session has produced calibration findings (F179, F180, F205,
F206) and verified narrow-basin floors at 86-87 across the cand
catalog. **No headline-class result.** The headline path remains
through non-heuristic methods.

## Discipline

- 0 SAT compute
- 0 solver runs
- F206 is a 3-minute, single-experiment sanity check that revealed
  the universal pattern across all cands, retiring the "robust
  deep basin" framing
