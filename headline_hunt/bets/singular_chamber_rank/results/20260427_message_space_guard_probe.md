# Message-Space Guarded Cascade Probe - 2026-04-27

This pass rechecked the singular-chamber search after macbook's F14/F15
correction: the collision-relevant object is not a free `W57,W58,W59`
tail chart, but actual message-space assignments whose schedule-derived
`dW[57..61]` match the cascade-1 required offsets.

The important correction is the slot-57 guard. A schedule match
`dW[57] == cw1[57]` is not meaningful unless the round-56 output already
has `a1 == a2` at slot 57. The message-space scorer now reports:

```text
a57_xor = state1[0] ^ state2[0] after rounds 0..56
defect[k] = dW[57+k] - cw1[57+k]
prefix_zero = number of consecutive guarded cascade-1 slots from 57
```

## Rank

At the registry default messages, the guarded local map has full rank for
tested candidates:

| idx | candidate | schedule rank | guarded rank | guarded kernel |
|---:|---|---:|---:|---:|
| 0 | `msb_cert_m17149975_ff_bit31` | 160 | 192 | 256 |
| 8 | `bit3_m33ec77ca_ff` | 160 | 192 | 256 |
| 18 | `msb_m189b13c7_80` | 160 | 192 | 256 |

So the 448 message bits linearly span the 32-bit `a57` guard plus the
five 32-bit schedule/cascade defects. The obstruction is nonlinear carry
landing, not a missing local dimension.

## Unguarded false positive

Before adding `a57_xor`, an idx18 walk found:

```text
W-free words:
80052400 80000000 84002148 a4018092 20008811 80200520 b0000011
80042004 88461100 80c09100 98800508 11000000 80923080 82008910

defect57 = 0
```

With the guard included, this is not a valid slot-57 cascade hit:

```text
a57_xor = 0x61d94a81
a57_hw  = 13
defect57 = 0x00000000
prefix_zero = 0
```

This quarantines the earlier unguarded D57 result. It was a schedule
alignment in the wrong pre-state chart.

## Guarded walks

Corrected multi-axis walks over the 14 free message words used the
objective:

```text
score(prefix 1) = HW(a57_xor) + HW(defect57)
```

Matched 3M-trial, 16-thread runs over four candidates found:

| idx | candidate | best guarded prefix HW | a57 HW | defect57 HW |
|---:|---|---:|---:|---:|
| 0 | `msb_cert_m17149975_ff_bit31` | 9 | 4 | 5 |
| 8 | `bit3_m33ec77ca_ff` | 9 | 5 | 4 |
| 17 | `bit15_m28c09a5a_ff` | 9 | 3 | 6 |
| 18 | `msb_m189b13c7_80` | 10 | 5 | 5 |

A seeded 5M-trial run from the idx8 HW9 point improved the guarded prefix
to HW8:

```text
idx 8
free words:
ffffffff ffffffef ffffefff afff771c fffffefe ffffffff f7dd77ff
f4dbfeab fbf5e7e7 fff96fdf fbbdfeff fefffffd f3bffbff b6fe6bff

a57_xor = 0x00401001  HW 3
defect57 = 0x28220800  HW 5
guarded prefix HW = 8
prefix_zero = 0
```

The idx0 seeded 5M-trial run did not improve its HW9 point.

## Exact-guard neighborhoods

The next check enumerated all message-bit perturbations through radius 3
around the default messages while retaining only exact `a57_xor=0` guard
points. Each radius-3 enumeration checks 14,986,272 neighbors.

| idx | seed | guard hits through radius 3 | slot-57 hits | best exact-guard prefix |
|---:|---|---:|---:|---:|
| 0 | default | 1 | 0 | HW19 (default) |
| 8 | default | 1 | 0 | HW15 (default) |
| 19 | default | 1 | 0 | HW14 (default) |

For idx0 and idx8, the only exact-guard point within radius 3 of the
default message is the default message itself. The best low-HW neighbors
all leave the guard manifold:

```text
idx0 best any radius<=3: guarded prefix HW10, a57 HW5, defect57 HW5
idx8 best any radius<=3: guarded prefix HW12, a57 HW6, defect57 HW6
idx19 best any radius<=3: guarded prefix HW12, a57 HW6, defect57 HW6
```

Radius-3 enumeration around the seeded idx8 HW8 and idx0 HW9 near-miss
points found no exact-guard point at all. These near-miss valleys are
off the cascade manifold, not broad neighborhoods around hidden guarded
solutions.

## F17 bit13 target

Macbook's F17 round-63 residual work distinguished `bit13_m4e560940_aa`
as the lowest round-63 residual candidate in that metric. Adding it to
the guarded probe:

```text
idx 19: bit13_m4e560940_aa
rank_guarded = 192
base guarded prefix HW = 14
3M guarded walk best prefix HW = 9

best walk:
a57_xor = 0x1681000a  HW 7
defect57 = 0x00001100  HW 2
```

This does not beat idx8's HW8 guarded-prefix frontier. It does show a
different split: bit13 can make `defect57` very small while failing to
repair the `a57` guard.

## A57 guard repair

The next operator separated the tasks:

1. randomly perturb the 14 free message words,
2. use a local 32-bit Boolean-Newton repair only for `a57_xor`,
3. keep only repaired `a57_xor=0` points when scoring `defect57`.

This tests whether the exact guard manifold is accessible, even if the
low-HW valleys are off-manifold.

Each 500k-trial run used 16 threads, up to 8 guard-repair iterations,
and up to 96 initial random flips:

| idx | candidate | repaired guard hits | best exact-guard prefix | exact slot-57 hits |
|---:|---|---:|---:|---:|
| 0 | `msb_cert_m17149975_ff_bit31` | 400 | HW19 (default) | 0 |
| 8 | `bit3_m33ec77ca_ff` | 391 | HW15 (default) | 0 |
| 18 | `msb_m189b13c7_80` | 434 | HW13 (default) | 0 |
| 19 | `bit13_m4e560940_aa` | 347 | HW14 (default) | 0 |

The repair step is effective at recovering `a57_xor=0` from off-manifold
starts, but every best exact-guard representative stayed at the default
message's `defect57` value. The operator repairs the guard by returning
to the same unproductive guard chart; it does not find a lower-D57 guard
fiber.

## Guarded Newton

Boolean-Newton projection was updated to solve the guarded prefix
`(a57_xor, defect57)`. The map has rank 64 for that prefix, but the
linear corrections have average Hamming weight about 32 and performed
worse than stochastic small-step repair. This repeats the earlier
tail-coordinate pattern: linear solvability exists, but the linear jump
crosses nonlinear carry charts.

## Interpretation

The old free-tail chart remains useful for understanding carry geometry,
but it is a relaxation. In real message space, preserving `a57_xor=0`
is a first-class constraint. The current guarded message-space frontier is
only a low-HW near miss at slot 57, not a cascade hit:

```text
best guarded slot-57 prefix: HW8
exact guarded slot-57 hits: 0
exact sr61 hits: 0
```

This aligns with macbook's F16 result: single-axis message sweeps behave
like brute force. Multi-axis heuristic walks can reduce the guarded
slot-57 residual, but so far do not cross it. Radius-3 exact-guard
enumeration shows the local guard manifold is extremely thin near the
default messages and absent near the best near-miss valleys. The next
useful operator must do more than repair `a57` after the fact: it needs
to move within a productive exact-guard fiber while steering `defect57`,
rather than repairing back to the default guard chart or optimizing
unguarded schedule defects.
