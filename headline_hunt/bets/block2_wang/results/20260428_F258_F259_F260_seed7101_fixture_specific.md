---
date: 2026-04-28
bet: block2_wang
status: F254_HYPOTHESIS_REFINED — seed 7101's luck is FIXTURE-SPECIFIC
---

# F258/F259/F260: seed 7101's narrow-basin access is fixture-specific, not seed-general

## F258: third seed on yale F301 mask

8×50k seed 5001 on bit19 `1,2,3,4,15` (yale's F301 chunk-21 winner).

Three seeds tested on F301 mask:

| Seed | 8×50k best |
|---:|---:|
| 7101 (yale F301) | **90** |
| 9001 (yale F301) | 93 |
| 5001 (F258) | 92 |

Same pattern as F135 (`0,1,3,8,9`) and F248 (`0,7,9,12,14`):
seed 7101 reaches a sub-91 narrow basin; other seeds reach 92-93.

**Confirmed**: F301 score-90 is yet another seed-7101-narrow basin
on bit19. Three such basins now known on bit19 alone.

## F259: seed 7101 on bit3 — does the luck transfer?

Test: does seed 7101 also find a narrow basin on bit3? If yes,
seed-7101 has universal deep-basin access. If no, seed-7101's
luck is bit19-specific.

8×50k seed 7101 on bit3 `0,1,2,8,9`:

```
all 8 restarts:
  restart=1: score=94 msgHW=75
  restart=2: score=95
  restart=0: score=96
  restart=4: score=96
  restart=6: score=96
  restart=3: score=98
  restart=5: score=98
  restart=7: score=99
BEST: 94
```

**Seed 7101 reaches only 94 on bit3, NOT 86.** The seed-7101
"luck" is NOT general.

## F260: refined picture

Combined seed-vs-fixture data:

| Mask | Seed 7101 | Seed 9001 | Seed 9101 | Seed 5001 | Seed 9911 | Other |
|---|---|---|---|---|---|---|
| bit19 `0,1,3,8,9` | 87 (F135 chunk-1) | 91 (F180 chunk-1) | — | — | — | — |
| bit19 `0,7,9,12,14` | 90 (F248) | 92 (F251) | — | 92 (F253) | — | — |
| bit19 `1,2,3,4,15` | 90 (F301) | 93 (F301) | — | 92 (F258) | — | — |
| bit4 `0,1,2,4,8` | 89 (F256) | — | 86 (F188) | — | — | — |
| bit3 `0,1,2,8,9` | 94 (F259) | — | — | — | 95 (F206) | 86 (yale pre-pause) |

### Pattern

**seed 7101 finds narrow basins on bit19 but NOT bit3.** Seed 9101
finds the bit4 deep basin. Other seeds (yale's pre-pause campaign)
found bit3's 86.

Each (seed, fixture) pair has a distinct narrow-basin landscape.
**Seed luckiness is fixture-specific, not seed-general.**

## Implications

### Sharpened structural hypothesis

The cascade-1 fixture × seed space is a fine-grained product. To
fully map narrow basins:

- Each fixture has many narrow-basin masks
- Each seed accesses some subset of those masks
- Different (seed, fixture, mask) triples produce different scores

Multi-seed sweeps on bit3, bit4, bit25, bit28, msb would each find
different narrow basins. The 86 floor may be the asymptotic minimum
across the whole product space.

### What 86 floor means

Robust 86 floor across the (seed, fixture, mask) product space
means: **NO combination tested today reaches strictly below 86**.
This is a strong empirical claim.

The 86 floor is now defended by:
- bit3 multi-seed historical (yale's pre-pause)
- bit3 8×50k seeds 7101 (94) + 9911 (95) [F206/F259]
- bit4 8×50k seeds 9101 (86) + 9501 (94) + 9601-init (86) + 7101 (89)
- bit19 8×50k seeds 7101 (87 in F135 / 90 in F248 / 90 in F301) +
  9001 (91-93) + 5001 (92)

Across all tested (seed, fixture) combinations, sub-86 hasn't appeared.

### For the headline path

Confirms F237/F257: heuristic local search has saturated cascade-1
at 86. No further heuristic variant likely to break this.

The headline path runs through non-heuristic methods:
- IPASIR-UP propagator (F238 Phase 2D-2F)
- Cube-and-conquer
- BDD enumeration
- Or different encoding entirely

## What's NOT being claimed

- That seed 7101 has zero luck on bit3 (only one mask tested; other
  bit3 masks might have seed-7101 narrow basins)
- That bit3's 86 is THE asymptotic floor (multi-seed sweeps might
  find sub-86 at very specific (seed, mask) combos; not yet found)
- That all heuristic methods are equivalent (cube-and-conquer +
  basin-hopping + simulated tempering not yet tested)

## Discipline

- 0 SAT compute (heuristic local search ~7 min total wall across
  F258 + F259)
- F-numbers F258, F259 (macbook F250+ range per yale convention)
- F260 is the synthesis (no compute)

## Coordination

Yale's chunk-21 work (F301) ran multi-seed verification (seed 9001
=93) per my F251 protocol suggestion. Fleet collaboration is
working: yale internalized the multi-seed discipline within hours.
