# Phase 2C-Rule4 cross-kernel sweep — firing rate varies 5× across kernels

## Setup

For each of the 9 kernel families, generate a v3 sr=61 force CNF (with modular-diff aux), run the propagator at 50k-conflict budget. Measure how many Rule 4@r=62 fires per run.

## Results

| kernel | Rule 4@r=62 fires | partial-bit samples | max bits forced in 1 sample |
|---|---:|---:|---:|
| bit-0  | **52** | 24 | 9 |
| bit-6  | 86 | 37 | 21 |
| bit-10 | 170 | 47 | 25 |
| bit-11 | 78 | 22 | 24 |
| bit-13 | 110 | 52 | 10 |
| bit-17 | 96 | 45 | 31 |
| bit-19 | **209** | 34 | **32** |
| bit-25 | **249** | 57 | 21 |
| bit-31 | 201 | 79 | 14 |

**Mean: 139 fires per 50k conflicts. Stdev: ~70.**

## Reading

The Rule 4 firing rate varies dramatically across kernels — almost 5× between bit-0 (52) and bit-25 (249). This is the propagator's value-add signal: the more often Rule 4 fires, the more constraint-injection the solver receives that CNF couldn't derive on its own.

**High-firing kernels (likely best propagator targets):**
- bit-25 (249 fires): highest density.
- bit-19 (209 fires): hits 32 bits forced in a single sample — full dE[62] determined.
- bit-31 MSB (201 fires): the priority cert candidate.

**Low-firing kernels (propagator may not help much):**
- bit-0 (52 fires): only 24 partial-bit firing samples.
- bit-11 (78 fires): possibly something kernel-structural about the underlying Sigma0/Maj input distributions.

## Implication for the bet

For a **multi-hour SAT-finding experiment** to validate the bet's ≥10× conflict-count reduction target, **focus on bit-25 and bit-19 first**. Those kernels see ~5× more Rule 4 propagation than bit-0 — if the rule helps anywhere, it helps there most.

For each of bit-25 and bit-19, the experiment design:
- Run at conflict budget 10M (~30-60 min) with propagator ON vs OFF.
- Compare conflicts-to-SAT (or to budget hit) and wall-time.
- ≥10× ratio confirms the bet's value-add.

That's ~2-4 CPU-hours per kernel × 2 kernels = 4-8 CPU-hours total. **Compute-heavy enough that user direction is needed before launch.**

## What this DOESN'T resolve

- Whether the firings ACTUALLY reduce conflicts-to-SAT, or just slow per-conflict throughput.
- Whether sr=61 SAT exists for these candidates at all (most candidates have 0 SAT solutions per the 2^-32 SAT prob structural finding).

## Cross-kernel firing as a propagator-bet diagnostic

This table can be re-run as the propagator evolves (more rules, optimization tweaks). Higher firing rate per kernel = more value-add. Lower = the propagator's logic doesn't apply well there.

Useful for the fleet: a worker who picks up the bet can see immediately which 3-4 kernels are worth running multi-hour comparisons on, instead of brute-forcing all 9.

## Build artifact

The propagator binary and v3 CNFs are gitignored (reproducible). Test logs in this directory.

To re-run:
```bash
g++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
    cascade_propagator.cc -lcadical -o /tmp/cascade_propagator
# For each kernel: regenerate CNF + run propagator at 50k conflicts
```
