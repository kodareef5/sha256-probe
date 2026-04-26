# W57-Free Operator Probe - 2026-04-26

This pass tested whether the current wall is an artifact of fixing `W57`.
Previous repair operators moved only `W58/W59` inside a fixed sparse `off58`
chart. Here two operators were widened:

- `chart61beam`: deterministic beam search over bit-flip paths, optionally
  allowing `W57` moves.
- `surface61greedywalk`: greedy exact-D60 repair, optionally allowing `W57`
  perturbations before and during repair.

## Beam Search

The first target was the idx17 D60-HW7 / D61-HW1 shelf:

```text
idx = 17
W57 = 0xa418c4ae
W58 = 0x46d3f03a
W59 = 0x6cb9eeaa
D60 = 0x14400229 (HW 7)
D61 = 0x10000000 (HW 1)
```

Fixed-W57 beam search reproduced the same split as the full D60-fiber
exhaustion:

| mode | depth | beam | best cap state | best exact state |
|---|---:|---:|---|---|
| cap 1, cap-preserving | 24 | 4096 | original D60-HW7/D61-HW1 | none |
| cap 1, closure-first | 24 | 4096 | original D60-HW7/D61-HW1 | D61 HW16 |
| cap 4, mixed score | 40 | 8192 | D60-HW3/D61-HW6 | D61 HW12 |

Allowing `W57` to move created a new nearby cap-4 terrace:

```text
W57 = 0x8458c4ae
W58 = 0x46d3d03a
W59 = 0x34d5dfaa
off58 = 0x9c65f041 (HW 14)
D60 = 0x01c20000 (HW 4)
D61 = 0x00382000 (HW 4)
```

This is a different manifold because `W57` moved, but it leaves the sparse
offset chart. Radius-7 enumeration around it found one exact D60 point, and
that point landed at D61 HW14. The best nearby non-exact points again formed a
staircase:

| D60 HW | best D61 HW |
|---:|---:|
| 1 | 9 |
| 2 | 8 |
| 3 | 7 |
| 4 | 4 |
| 7 | 2 |

The W57-free beam therefore finds new terraces, not an exact low-cap bridge.

## W57-Free Greedy Repair

The widened greedy walker was then run for 100M trials with 24 threads and
`max_flips=64`.

### idx17 HW1 shelf

```text
base: W57=0xa418c4ae, W58=0x46d3f03a, W59=0x6cb9eeaa
exact60 hits: 1,072,656
changed exact60 hits: 1,072,656
best changed D61: HW5
best checked tail: HW66
```

Best D61 point:

```text
W57 = 0xa090e5ee
W58 = 0x42fbf832
W59 = 0x04b3e328
off58 = 0x9c65433b
D61 = 0x04008901 (HW 5)
tail HW = 77
```

Best tail point:

```text
W57 = 0xa90f45ea
W58 = 0x2ed1f018
W59 = 0x49493faa
D61 = 0x01d05000
tail HW = 66
```

### idx8 tail-HW59 frontier

```text
base: W57=0xaf07f044, W58=0xe537c1c7, W59=0x598feb25
exact60 hits: 2,259,089
changed exact60 hits: 1,005,959
best changed D61: HW8
best checked tail: HW59 (unchanged)
best changed tail: HW73
```

The global tail-HW59 point remained the best tail in the run.

### idx0 HW4 frontier

```text
base: W57=0x370fef5f, W58=0x6ced4182, W59=0x9af03606
exact60 hits: 2,261,878
changed exact60 hits: 7,202
best D61: HW4 (unchanged)
best changed D61: HW6
best checked tail: HW66
```

The idx0 run preserved the known HW4/tail-HW66 frontiers but did not improve
either one.

## Interpretation

Freeing `W57` adds real degrees of freedom: exact-D60 landings become common
and the beam finds new low-D60 terraces. But the useful sparse/carry chart is
not preserved. The best W57-free points have high-HW `off58` and worse D61 or
tail than the fixed-chart frontier.

This weakens the hypothesis that the current wall is mainly caused by fixing
`W57`. The more precise obstruction is chart preservation: moving enough to
close D60 or create a new terrace also changes the round-60/61 carry chart
that made D61 small.

No exact D61=0, D61 HW3, or tail improvement was found.
