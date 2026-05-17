# 2026-05-17: Second-Stage Free-Word Local Refinement

Runner: mac-codex

## Question

The projected-bucket miner found that the best reduced-N witnesses are isolated
inside coarse buckets. Does a local second stage around those witnesses improve
the tail after `D60=0`?

## Implementation

Extended `free_word_mitm_reducedn.c` with an optional refinement stage:

```text
/private/tmp/free_word_mitm_reducedn N [prefix_limit] [refine_budget] [refine_seed_cap]
```

The first-stage scan retains the best `D60=0` witnesses by tail HW and r61 HW.
The second stage then tests neighborhoods around those witnesses:

- all one-bit flips over `W57,W58,W59`,
- all two-bit flips over `W57,W58,W59`,
- an annealed D60-HW walk that can pass through nonzero-D60 states and look for
  better `D60=0` return points.

The refinement stage does not change the schedule model. It still recomputes
`W2[57..59]` from the cascade and accepts only true `D60=0` candidates for tail
comparison.

## Runs

### N=8 exact control

```text
command: /private/tmp/free_word_mitm_reducedn 8 0 100000 64
scan best tail HW: 9
refinement tested: 100,000
refinement D60=0: 528
collisions: 0
seed inserts: 0
best refined tail HW: 9
```

Exact scan control: no improvement, as expected.

### N=10 exact control

```text
command: /private/tmp/free_word_mitm_reducedn 10 0 1000000 128
scan best tail HW: 7
refinement tested: 1,000,000
refinement D60=0: 1,499
collisions: 0
seed inserts: 0
best refined tail HW: 7
```

Exact scan control: no improvement and no false collision. This is a sanity
check that the refinement path is not creating artifacts.

### N=12 sampled

```text
command: /private/tmp/free_word_mitm_reducedn 12 262144 2000000 256
scan best tail HW: 15
refinement tested: 2,000,000
refinement D60=0: 851
collisions: 0
seed inserts: 2
best refined tail HW: 15
```

The walk found new retained seeds but did not improve the best sampled tail.

### N=12 sampled, larger walk budget

```text
command: /private/tmp/free_word_mitm_reducedn 12 262144 50000000 512
scan best tail HW: 15
refinement tested: 50,000,000
refinement D60=0: 18,768
collisions: 0
seed inserts: 24
best refined tail HW: 15
refine elapsed: 2.142s
```

The larger walk generated many valid `D60=0` return points and 24 new retained
seeds, but still did not beat HW15.

## Interpretation

Second-stage local mutation is operationally cheap and correctly finds nearby
`D60=0` return points. The negative part is more important: low-tail witnesses
do not look like local basins under raw bit flips of `W57,W58,W59`.

This means the next refinement should not spend most time on unconstrained local
bit walks. It should use moves that preserve or directly solve the `D60=0`
interface:

```text
mutate W57/W58 projection -> solve or enumerate W59 values with D60=0 -> score tail
```

Practical next build:

1. For a chosen `(W57,W58)` neighborhood, scan all `W59` and retain only
   `D60=0` hits.
2. Rank those hits by tail HW and r61 HW.
3. Use the projected-bucket keys as addresses for which `(W57,W58)` regions to
   resample.

Verdict: projected buckets plus local witnesses are useful addresses, but raw
local mutation is not yet a closing mechanism.
