# bet: singular_chamber_rank — lower-rank sr=61 defect chambers

## The bet

The cascade sr=61 barrier is usually modeled as a uniform 32-bit schedule
defect: the schedule-derived `W60` misses the cascade-required `W60` with
probability `2^-32`.

This bet asks a different question:

> Are there chambers of the SHA-256 Boolean/carry state space where that
> defect map has rank less than 32?

If the local image rank of the defect map drops from 32 to `r`, then the
expected sr=61 compatibility cost drops from `2^32` to about `2^r` inside
that chamber. A rank-20 chamber would be a 4096x structural reduction even
before SAT or GPU search.

## Object being measured

For a cascade-eligible N=32 candidate and free words `(W57,W58,W59)`, build
the normal cascade through rounds 57, 58, and 59:

- choose `W2[r] = W1[r] + cascade_offset(r)` for `r in {57,58,59}`;
- compute the schedule-derived `W1[60]` and `W2[60]` from `W[58]`;
- compute the cascade-required round-60 offset from the round-59 state.

Define:

```text
D(W57,W58,W59) =
    (W2_sched60 - W1_sched60) - cascade_required_offset60  mod 2^32
```

The usual sr=61 cascade compatibility event is `D=0`.

The first tool measures the GF(2) rank of the local Boolean derivative of
`D` with respect to the 96 input bits of `(W57,W58,W59)`.

## Why this is not the same as de58/hardlock

`de58_size` and hardlock bits measure projection structure in the cascade
boundary state. They have already been shown search-irrelevant for CDCL.

This bet measures the actual sr=61 obstruction map. The target is not a
smaller projection; it is a lower-rank obstruction.

## What would be a hit

- Any reproducible N=32 candidate/sample with local defect rank below 32.
- A statistical enrichment of low-rank samples around a recognizable gate
  chamber, such as `f=g` in both paths for `Ch`, or `b=c` in both paths
  for `Maj`.
- A fill/kernel family where the minimum observed rank is consistently
  below the baseline across independent seeds.

## What would kill this first version

If all sampled candidates show rank 32 across broad random and structured
samples, then the simple local-Jacobian form of the singular-chamber idea is
not useful. The broader idea would remain open only through nonlinear
fiber-size measurements, nonzero gate-invisible trails, or block-2 chambers.

## Tools

Compile from repo root:

```bash
gcc -O3 -march=native -fopenmp -I. \
  headline_hunt/bets/singular_chamber_rank/tools/singular_defect_rank.c \
  lib/sha256.c -lm -o /tmp/singular_defect_rank
```

Local-rank probe:

```bash
/tmp/singular_defect_rank 2048 8
```

Boolean-Newton defect-correction probe:

```bash
/tmp/singular_defect_rank newton 1024 8 24
```

Reduced-N exact fiber counter:

```bash
gcc -O3 -march=native -fopenmp -I. \
  headline_hunt/bets/singular_chamber_rank/tools/defect_fiber_counter.c \
  lib/sha256.c -lm -o /tmp/defect_fiber_counter

/tmp/defect_fiber_counter 12 11 0xfff 0
/tmp/defect_fiber_counter single 12 11 0xfff 0x666
/tmp/defect_fiber_counter hits 12 11 0xfff 0x666 0x393
```
