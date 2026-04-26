# Local Rank Probe — 2026-04-26

Host: linux GPU laptop role, CPU-only. `nvidia-smi` could not communicate
with the NVIDIA driver, so the first pass used the i9 CPU with 8 OpenMP
threads.

## Commands

```bash
gcc -O3 -march=native -fopenmp -I. \
  headline_hunt/bets/singular_chamber_rank/tools/singular_defect_rank.c \
  lib/sha256.c -lm -o /tmp/singular_defect_rank

/tmp/singular_defect_rank 2048 8
/tmp/singular_defect_rank newton 1024 8 24
```

## Local derivative-rank result

Sampled 18 representative N=32 cascade-eligible candidates:

- 36,864 total local points (`18 * 2048`).
- 0 points with full 96-bit derivative rank below 32.
- Every candidate had `rank32 = 2048/2048`.

So the simplest version of the singular-chamber hypothesis is negative:
the sr=61 defect map does not show obvious local rank collapse in the full
`(W57,W58,W59)` space.

## Separated word ranks

The separated ranks are more interesting:

- single-word ranks are not full:
  - `W57`: minimum 28-30 depending on candidate,
  - `W58`: minimum 28-30,
  - `W59`: minimum 24-28.
- any two-word slice is usually full rank 32.
- a few candidates showed `rank(W58,W59 | fixed W57) = 31` at some sampled
  points, including bit19, bit28, bit18, and one bit14 candidate.

Interpretation: no single word controls the defect alone. Pairs usually do.
`W59` is the weakest individual coordinate. That argues against a naive
rank-collapse search, but it leaves open an implicit-solve or nonlinear
fiber-size approach.

## Low-defect observations

Random/local-rank samples saw defect Hamming weights as low as:

- HW 4: `bit28_m3e57289c_ff`
- HW 5: `bit20_m294e1ea8_ff`, `bit3_m5fa301aa_ff`
- HW 6: several fill=0xff candidates including bit14 and MSB cert

These low-HW defects still had full local rank. Low defect weight is not
the same thing as low rank.

## Boolean-Newton probe

The Newton mode fixes `W57` and iteratively solves the local 32x64 Boolean
derivative system over `(W58,W59)` to try to force `D=0`.

Run: 18 candidates, 1024 starts each, 24 iterations.

Result:

- 0 exact `D=0` successes.
- Most derivative systems were full rank; rank failure was rare.
- Best final defects landed around HW 5-9 depending on candidate.

Interpretation: local linear correction alone is not a constructive solver
for the full 32-bit defect. It can move onto low-defect shelves, but the
remaining bits appear nonlinear/carry-chamber locked.

## What changed in the mental model

The direct "find rank < 32" version is probably too naive because the
schedule path injects high-rank dependence through `sigma1(W58)`.

The useful next question is nonlinear:

> For fixed `W57`, what is the actual fiber size of `D(W58,W59)=0`, and
> are some candidates/fills/chambers enriched above the random `2^-32`
> baseline?

If fibers are larger than random even with full local rank, the reduction
will not appear in the Jacobian. It will appear as a global chamber/fiber
effect.

## Next steps

1. Build a reduced-N exact fiber counter for this same `D` map.
2. At N=8/10/12, measure `# {(W58,W59): D=0}` for fixed `W57` across
   candidates and fills.
3. If the fiber distribution is heavy-tailed, search for the gate/carry
   chamber features that predict fat fibers.
4. Only then scale a targeted full-N probe.

