# Cross-Chamber Pooled Surface Walk - 2026-04-26

This pass tested whether the idx 8 HW5/tail-HW67 frontier was a single lucky
chamber or part of a broader sparse-offset phenomenon. The operator was
`frontier61pool`: perturb known exact `defect60=0` seeds, greedily repair back
to exact D60 under mixed policies, and retain the Pareto frontier over D61 and
checked tail.

The batch covered idx 8, idx 3, and idx 0 with matched 50M-trial pooled runs,
plus follow-up 50M/100M runs after new frontiers were found.

## idx 8: tail HW59

Seeds included the HW5 D61 point, the second HW5 basin, HW67/HW68 tail points,
the exact HW6 point, and older HW7/HW8 points.

```text
trials: 50,000,000
exact60 hits: 2,655,492
changed exact60 hits: 114,058

best D61: HW5 (known second HW5 basin)
best tail: HW59
```

New checked-tail frontier:

```text
W57 = 0xaf07f044
W58 = 0xe537c1c7
W59 = 0x598feb25

defect60 = 0
defect61 = 0x6f5fc000 (HW 14)
defect62 = 0xa833c118
defect63 = 0x2f3427d1
tail HW = 59
```

A 100M follow-up including this HW59 point did not improve either objective:

```text
trials: 100,000,000
exact60 hits: 5,439,305
changed exact60 hits: 122,412

best D61: HW5
best tail: HW59
```

The follow-up did find another exact HW5 basin:

```text
W58 = 0x49de26f6
W59 = 0x1f328d74
defect61 = 0x60081002 (HW 5)
tail HW = 74
```

A later 100M mixed-seed pool raised the repair flip cap from 32 to 64 and
included exact HW59/HW60/HW67/HW5 seeds plus non-exact cap-4 and low-D60/D61
terrace seeds. It also did not improve either exact frontier:

```text
trials: 100,000,000
max_flips: 64
exact60 hits: 1,855,242
changed exact60 hits: 37,585
projection failures: 98,144,764

best D61: HW5 (existing seed)
best tail: HW59 (existing seed)
best changed D61: HW7
best changed tail: HW72
```

The wider jump budget mainly made repair harder. None of the mixed-chart
terrace seeds crossed back to exact `D60=0` with a better D61 or tail, which
supports treating the terrace as a different chart rather than merely a distant
part of the same exact surface.

## idx 3: D61 HW7

Seeds included the prior HW11 point, the original exact sr61 point, and a
changed exact basin from earlier greedy repair.

```text
trials: 50,000,000
exact60 hits: 2,504,139
changed exact60 hits: 581,037

best D61: HW7
best tail: HW72
```

New idx 3 D61 frontier:

```text
W57 = 0xe28da599
W58 = 0xdf0770a7
W59 = 0x2ad9ba75

defect60 = 0
defect61 = 0x52802880 (HW 7)
tail HW = 79
```

New idx 3 checked-tail frontier:

```text
W58 = 0x1a09746c
W59 = 0x004b0a03
defect61 = 0x520d7f0e (HW 16)
tail HW = 72
```

A 50M follow-up including both new points did not improve either frontier.

## idx 0: D61 HW6, then M5 HW5

Seeds included the prior HW11 point, the sparse-off59 HW17 point, and a
changed exact HW14 basin.

```text
trials: 50,000,000
exact60 hits: 2,613,188
changed exact60 hits: 455,937

best D61: HW6
best tail: HW67
```

New idx 0 D61 frontier:

```text
W57 = 0x370fef5f
W58 = 0x6e2ca0eb
W59 = 0xe68508a7

defect60 = 0
defect61 = 0x20214084 (HW 6)
tail HW = 82
```

New idx 0 checked-tail frontier:

```text
W58 = 0xca61637d
W59 = 0xf23cfe17
defect61 = 0x9f0fd8ca (HW 18)
tail HW = 67
```

A 50M follow-up including both new points did not improve either frontier.

Macbook then ran a 1B-trial single-candidate walk from an idx 0 HW8 base and
found that idx 0 also reaches the exact D61 HW5 floor:

```text
W57 = 0x370fef5f
W58 = 0x4c4dc123
W59 = 0x9ad3f074

defect60 = 0
defect61 = 0x02081030 (HW 5)
tail HW = 89
```

The same M5 memo reports an idx 0 checked-tail floor of HW64. Macbook later
found exact D61 HW4 on idx 0:

```text
W58 = 0x6ced4182
W59 = 0x9af03606
defect61 = 0x80110200 (HW 4)
tail HW = 77
```

A linux 1B follow-up from that HW4 point found no HW3, but improved idx0's
checked-tail floor to HW66:

```text
W58 = 0x38fd0196
W59 = 0x9372cea1
tail HW = 66
```

These supersede the 50M pooled idx 0 frontier numerically, but not
qualitatively: the D61 and tail optima remain distinct points.

## Interpretation

The low-D61 exact phenomenon is not unique to idx 8:

| candidate | sparse off58 | best exact D61 | best checked tail |
|---:|---:|---:|---:|
| idx 8 | `0x00010002` | HW5 | HW59 |
| idx 0 | `0x00000021` | HW4 | HW66 |
| idx 3 | `0x00000802` | HW7 | HW72 |

This strengthens the collision-difficulty-reduction picture: after sparse
schedule-offset steering, multiple independent full-N chambers reach exact D60
with D61 defects far below random 32-bit weight. The former HW5 D61 floor is
now broken on idx 0, while the best checked tail remains idx 8.

The runs also sharpen the shape question. D61 and tail optimization are
separate objectives: idx 8's tail HW59 point has D61 HW14, while its D61 HW5
points have tails in the 72-78 range. The search should keep a Pareto frontier
rather than collapsing everything into one scalar score.

No exact D61=0 or full tail collision was found.
