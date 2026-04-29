---
date: 2026-04-28
bet: cascade_aux_encoding
status: F262_DEPTH1_DW58_CUBES_INSUFFICIENT_ON_F235
---

# F262: depth-1 dW[58] cube-and-conquer on F235 hard instance — all 16 cubes timeout

## Setup

Yale's F302 shipped `schedule_cube_planner.py` + `run_schedule_cubes.py`
(commit c1952d40, ~20:27 EDT). F262 immediately uses these tools on
the F235 hard instance — the empirically-hardest cascade-1 CNF in the
corpus (kissat 848s timeout per F239, cadical 120s timeout per F239).

If any depth-1 cube on this CNF returns SAT/UNSAT before 30s, that's
the first non-heuristic structural-attack signal: cube-and-conquer
splits beyond what direct CDCL can do.

## Configuration

```bash
# Generate 16 cubes (dW[58] bits 0-7, depth 1)
python3 schedule_cube_planner.py \
  --cnf cnfs_n32/sr61_cascade_m09990bd2_f80000000_bit25.cnf \
  --sr 61 \
  --target dw --round 58 --bits 0-7 --depth 1 \
  --out-jsonl /tmp/F262_dw58_depth1.jsonl \
  --emit-cnf-dir /tmp/F262_cubes

# Run 16 cubes with cadical, 30s each
python3 run_schedule_cubes.py \
  --manifest /tmp/F262_dw58_depth1.jsonl \
  --solver cadical --conflicts 0 --timeout-sec 30 \
  --out-jsonl /tmp/F262_results.jsonl --limit 16 \
  --work-dir /tmp/F262_cubes --keep-cnfs
```

## Result

**ALL 16 cubes TIMEOUT at 30s.**

```
cube=dwr58b00v0  TIMEOUT  30.01s
cube=dwr58b00v1  TIMEOUT  30.01s
cube=dwr58b01v0  TIMEOUT  30.00s
cube=dwr58b01v1  TIMEOUT  30.01s
... all 16 ...
cube=dwr58b07v0  TIMEOUT  30.01s
cube=dwr58b07v1  TIMEOUT  30.01s
```

Total wall: 480s (16 cubes × 30s). Zero cubes solved.

## Interpretation

**Depth-1 dW[58] cubes are insufficient to split F235.** No single
dW[58] bit fixing enables CDCL to solve the resulting subproblem
within 30s.

This is consistent with F237/F239: the F235 instance has
intractability that's not localized to any single dW bit position.
The hardness is structurally distributed across the schedule space.

### Possible explanations

1. **Insufficient depth**: depth-1 fixes only 1 dW bit. Depth-2 (4
   fixed bits per cube) or depth-3 (8 fixed bits per cube) might
   localize the hardness.

2. **Wrong round**: dW[58] might not be the structurally-decisive
   round. dW[59] or dW[60] (closer to the cascade-1 hardlock at
   round 56) might split better.

3. **Wrong target**: W1 unit cubes or W2 unit cubes might split
   better than joint dW cubes.

4. **Genuinely hard instance**: F235 may simply be solver-intractable
   regardless of cube structure. This would push the headline path
   toward BDD enumeration or different encoding entirely.

### What this rules out

- **Cube-and-conquer at depth 1 on dW[58] is NOT the headline path
  on F235.**
- 30s × 16 cubes = 480s wall didn't beat direct kissat's 848s
  timeout meaningfully (kissat had longer single-process budget).

### What this doesn't rule out

- Deeper cubes (depth 2-3, exponentially more cubes).
- Different rounds or targets.
- Cube-and-conquer working on OTHER hard instances (F235 is the
  hardest known; easier hard instances might respond to depth-1).

## Concrete next probes

(a) **Depth-2 dW cubes on F235**: 4 × 16 = 64 cubes, but each cube
    has 2 fixed dW bits. Tests if 4 fixed bits make F235 tractable.
    Total compute: 64 × 60s = 64 min wall worst case.

(b) **Depth-1 cubes on different round**: dW[59] depth-1 = 16 cubes
    at round 59 instead of 58. Cheap (~8 min wall worst case).

(c) **W1-only or W2-only cubes**: target W1[58] bits or W2[58]
    bits separately. If W1-only beats dW (which forces both W1
    and W2 simultaneously), the cascade-1 asymmetry favors
    one-sided cubing.

(d) **Move to a less-hard instance**: F235 may be too hard. Cube
    pilot on a "medium" hard instance (kissat wall 60-300s) might
    show speedup more clearly.

## Discipline

- **1 SAT compute event**: 16 cube runs × 30s timeout each = 480s
  of cadical wall. Not logged via append_run.py since runs
  produced TIMEOUT (UNKNOWN) not SAT/UNSAT verdicts.
- F262 is the first concrete non-heuristic-attack pilot of the
  session. Negative result, but informative.

## Coordination with yale

Yale's F302 tooling worked perfectly. F262 is the natural
complement: yale built the harness, macbook ran the first
adversarial test on the hardest instance.

If yale already plans to run depth-2 or different rounds, signal
which way to coordinate. Otherwise macbook will pick up
(b)/(c)/(d) next.

## Strategic position

F237 closed preprocessing path. F257 mapped heuristic landscape.
F302 shipped cube infrastructure. F262 found cube-and-conquer at
depth-1 on F235 also doesn't break.

The structural attack path is narrowing:
- Depth-1 cubes: F262 negative
- Depth-2 cubes: untested
- IPASIR-UP propagator: not yet implemented (F238 Phase 2D-2F)
- BDD enumeration: not yet implemented
- Different encoder: not yet attempted

Each remaining option is multi-hour future-session implementation
work. The empirical bar for headline-class is "ANY method finds
sub-86 collision pre-image".
