---
date: 2026-04-28
bet: block2_wang
fixture: bit19_HW56_51ca0b34_naive_blocktwo
status: BUDGET_KNOWLEDGE_GAINED
---

# F179: bit19 `{0,1,3,8,9}@87` basin is unreachable from random init at 8×50k

## What macbook's F174 batch actually shows

Macbook's F174 took the top-10 radius-1 masks from F172's 3×4000 pass
and reran each at 8 restarts × 50,000 iterations **without F135
initialization** (each restart seeded from a different `--seed` value
4000+i). One of the 10 masks was the known F135 winner `{0,1,3,8,9}`,
included as a sanity-check baseline.

The result is sharper than expected:

```
mask 0,1,3,8,9 — all 8 restart scores at 8×50k from random init:
  restart=3 score=95
  restart=0 score=96
  restart=1 score=96
  restart=7 score=96
  restart=5 score=97
  restart=6 score=97
  restart=2 score=98
  restart=4 score=98
```

**Best across all 8 restarts: 95.** F135's known result on this same
mask: **87.** Gap: 8 points, never closed at 8×50k random init.

## Cross-check vs yale's F173

Yale's F173 (F135-initialized 3×4000 pass) replays `{0,1,3,8,9}@87`
trivially — restart 0 is seeded from the F135 score-87 message pair,
so the local search starts inside the basin and finishes there.

Yale's F174 (separate file, F135-init 8×50k) is the equivalent at
larger budget; same basin-seeded protocol, same 87-class result.

The conjunction of yale's F173/F174 + macbook's F174 batch produces a
stronger empirical claim than either alone:

> The score-87 mask `{0,1,3,8,9}` on bit19_m51ca0b34 is reachable
> only from F135-basin initialization. From random init, even at
> 8 restarts × 50,000 iterations (8× the chunked-scan budget), the
> best random-search score is 95.

## Why this matters

1. **The basin is narrow.** A 5-dimensional active-word mask has
   modest search-space; the fact that 8×50k random restarts cannot
   reach the basin from outside indicates the basin is much smaller
   than the search budget would naively suggest.

2. **Chunked-scan F135 was lucky.** Yale's F135 chunk-1 hit
   `{0,1,3,8,9}@87` with the standard chunk seed schedule. Looking
   back, that may have been a fortunate seed alignment, not a
   reproducible random-search outcome. A re-run of chunk 1 with
   different seeds might *not* find the score-87 basin.

3. **Floor concept is initialization-dependent.** Phrases like
   "bit19 fixture-local floor is 87" should be qualified:
   - F135-basin-init floor: 87
   - Random-init floor at 8×50k: 92-95
   - Random-init floor at 3×4000 (chunked-scan budget): mostly 91-92
     except the lucky F135 hit

4. **Implications for SAT attack.** If a structural-distinction
   mechanism exists, finding the deep basin requires either:
   (a) seeded initialization from a known sub-87 pair (chicken/egg),
   (b) basin-hopping moves that escape the random-init plateau
       (e.g. simulated annealing with restart kicks), or
   (c) global structural method (SAT, BDD) that doesn't rely on
       local search at all.

## Cross-confirms F172's calibration finding

F172 noted the chunked-scan budget (3×4000) was below the per-mask
local-minimum threshold. F179 sharpens this: the per-mask budget
needed to reach the *known* basin is **higher than 8×50k from
random init**. The chunked-scan worked at all because the seed
schedule happened to find the basin in chunk-1.

This means the chunked-scan protocol's effective floor depends on
seed luck. To audit a bit19 chunk's "true" floor, one would need
to either:

- Re-run the chunk with a battery of different seed schedules and
  confirm the same `{0,1,3,8,9}@87` reproducibly emerges. If it
  doesn't, the F135 finding was singular.
- Or seed each restart from a basin-hopping prior (sub-92 random-
  init result) and use that as a launching point.

## Implications for ongoing fixture-local scans

Three concerns for the bit28/bit4/bit25/msb planned scans (F178+):

1. **Their floors at 3×4000 are upper bounds.** Bit28's chunk-0
   floor of 91 (F178) may have a hidden deep basin invisible to
   the chunked-scan budget.

2. **Don't conclude "no fixture-local sub-87 basin exists" from
   chunked-scan alone.** All we'd know is "no basin reachable
   from this seed schedule".

3. **Per-cand basin search needs a different protocol** —
   either F135-style basin propagation (requires a known seed),
   or a global method (SAT / BDD).

## Discipline

- 0 SAT compute (heuristic local search analysis)
- 0 solver runs
- Calibration finding, not a falsification

## What's NOT being claimed

This memo does NOT claim:
- That `{0,1,3,8,9}@87` is wrong (yale's F135 is reproducible from
  F135 init; we can re-verify).
- That the score-87 result is a measurement artifact.
- That fixture-local search is broken.

What's being claimed: the score-87 basin is narrow, and re-finding
it from outside requires either basin-init or a more sophisticated
search protocol than 8×50k random restarts.
