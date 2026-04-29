---
date: 2026-04-28
bet: cascade_aux_encoding
status: F235_HARDCORE_LOCALIZED_TO_W58_W59
---

# F264/F265: F235 hard-core localized to W*_58 and W*_59 — cube targeting validation

## Setup

Yale extended my F213 identify_hard_core.py with --out-json output
(commit 6160021, ~21:00 EDT). F264 uses the extension to compute
the F235 cand hard-core decomposition for downstream use in yale's
F311 cube-seed selector.

This is concrete fleet-collaboration: macbook's structural-pivot tool
+ yale's extension + macbook's empirical application = sharp data
about which schedule bits are "decisive" for F235.

## F264 result on F235 cand

CNF: `cnfs_n32/sr61_cascade_m09990bd2_f80000000_bit25.cnf`
- 11234 vars, 47530 clauses
- Shell: 7328 vars (65.2%)
- Core: 3906 vars (34.8%)

### Schedule decomposition

| Word | Core | Shell | Comment |
|---|---:|---:|---|
| W1_57 | 1 | **31** | cascade-1 hardlock (per F217) |
| W2_57 | 2 | 30 | mostly forced by W1_57 hardlock + symmetry |
| W1_58 | 30 | 2 | hard-core; structurally decisive |
| W2_58 | 31 | 1 | hard-core |
| W1_59 | 32 | 0 | fully hard-core |
| W2_59 | 32 | 0 | fully hard-core |

**Active hard-core schedule for F235**: 3 bits (W*_57) + 61 bits (W*_58)
+ 64 bits (W*_59) ≈ 128 hard-core schedule bits out of 192 free
schedule total.

## F265: implications for cube targeting

### Cube target validation

Yale's cube experiments (F306-F309) targeted dW[59], my F262 used
dW[58]. Both rounds are HARD-CORE per F264 — correct cube targets.

Cubing on dW[57] (which is mostly shell-eliminable) would be wasted
effort — those bits are forced by cascade-1 hardlock, fixing them
in cubes provides almost no search-tree pruning.

Yale's F311 hard-core selector (using F264's JSON output) will
correctly avoid dW[57] cubes and focus dW[58]/dW[59] cubes — the
right structural choice.

### F262/F306-F309 negatives become structural facts

F262: 16 dW[58] depth-1 cubes all UNKNOWN at 30s.
F306: aux_force sr61_bit25 dW[59] depth-1 pilot.
F307: depth-2 ranked pairs 100k conflicts.
F308: 60s timeout on outlier cube.
F309: depth-3 expansion 100k conflicts → all UNKNOWN.

Combined: the F235 hard core (128-bit active schedule space) is
genuinely intractable to cube-and-conquer at depth-3 with 100k
conflicts. Splitting on 8 bits (depth 3) doesn't sufficiently
constrain the remaining 120-bit search.

To break F235 via cube-and-conquer, would need:
- Depth 4 (16 fixed bits), 100k conflicts: 256 cubes × ~few
  minutes = 1-4 hours wall
- Or depth 3 + 1M conflicts: 8 cubes × ~30 min wall = 4 hours
- Or different round/target: dW[58]+dW[59] joint cubes (depth-3
  spread across 2 rounds) might localize hardness better

### Lower-bound on F235 hardness

Empirical lower-bound from cube experiments:
- 30s cadical: insufficient
- 100k conflicts (~1-30s): insufficient at depth ≤ 3
- 848s kissat: insufficient (full instance)

To break F235 via SAT solving alone, may need >1000 conflicts per
hard-core variable in the worst case = 128 × 1000 = 128k conflicts
minimum, with substantial constants. Not impossible but not cheap.

## F213/F211/F237/F262/F309 unified picture

The cascade-1 collision-search difficulty is structurally
distributed across 128 hard-core bits per F235-class instance.
Whether attacked via:
- Heuristic search (block2_wang): 86 floor saturated (F257)
- Preprocessing (F211/F237): doesn't shrink SAT-difficulty
- Cube-and-conquer (F262/F309): doesn't fragment at modest depth/budget
- IPASIR-UP propagator (F238 unimplemented): TBD

...the 128-bit active-schedule hard core is the persistent intractability
floor.

**A headline-class result requires beating this 128-bit hard core**.
The methods tested today don't manage it. The remaining options are:
- Implement Phase 2D-2F propagator (F238) — adds in-search
  structural reasoning
- BDD enumeration with smart variable ordering
- Different SAT encoding that flattens the hard core

## Discipline

- F264: ~30s wall (yale's --out-json extension to my F213 tool)
- F265: synthesis (no compute)
- 0 SAT solver runs

## Coordination with yale

Yale's F305-F313 burst built the cube-and-conquer infrastructure.
F264 contributes the F235-specific hard-core data that yale's F311
selector consumes. Both tools work together; the empirical answer
they produce on F235 is "depth ≤ 3 cube-and-conquer is insufficient".

Future-session high-leverage moves (per F238/F257):
- Phase 2D propagator implementation (4-8 hrs)
- Or different encoding (cascade_aux variant with explicit hard-core
  forcing)
- Or BDD design study

## What's NOT being claimed

- That cube-and-conquer is dead globally (just on F235 at depth ≤ 3)
- That 128 is the universal hard-core size (varies per cand)
- That F235 is unsolvable (just hard at the budgets tested today)
