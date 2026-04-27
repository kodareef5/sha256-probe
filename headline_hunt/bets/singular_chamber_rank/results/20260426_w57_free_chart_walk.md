# W57-Free Chart Walk - 2026-04-26

This pass tested whether the HW4 exact-D60 floor survives when the
chart-preserving walker is allowed to move all three active words
`(W57,W58,W59)`, not just `(W58,W59)`.

The motivation was the same failure pattern seen in the affine repair
fiber and macbook pair-flip probe: low-D61 shelves are reachable, but
ordinary repair loses the chart that made them low. The new local tool
change adds `free_w57=1` to `chart61walk`, so random starts and one-bit
repair steps range over 96 bits.

## idx 17 D61-HW1 shelf

Base:

```text
idx = 17
W57 = 0xa418c4ae
W58 = 0x46d3f03a
W59 = 0x6cb9eeaa
D60 = 0x14400229 (HW 7)
D61 = 0x10000000 (HW 1)
```

Two 10M W57-free chart walks and one deterministic W57-free beam were run.

| run | cap | exact-D60 hits | exact low-cap hits | best exact D61 | best cap |
|---|---:|---:|---:|---:|---|
| walk, 10M | 1 | 281 | 0 | HW9 | D60 HW6 / D61 HW1 |
| walk, 10M | 4 | 281 | 0 | HW9 | D60 HW3 / D61 HW4 |
| beam, depth 32, width 8192 | 1 | found exact | 0 | HW11 | unchanged base |

Best exact point from the 10M walks:

```text
W57 = 0x341080e6
W58 = 0x52d1c223
W59 = 0xa138ed32
D60 = 0
D61 = 0x516a4080 (HW 9)
tail HW = 84
```

So W57 freedom can close D60 from the HW1 shelf, but the D61 chart breaks
before exactness is reached.

## Exact HW4 floors

The stronger test starts from exact-D60 HW4 points and asks for any exact
D61 HW3-or-better landing.

### idx 0

Base:

```text
W57 = 0x370fef5f
W58 = 0x6ced4182
W59 = 0x9af03606
D60 = 0
D61 = 0x80110200 (HW 4)
tail HW = 77
```

Runs:

| run | trials/evals | exact-D60 hits | exact HW<=3 hits | best exact | best cap |
|---|---:|---:|---:|---:|---|
| walk | 20M | 246,470 | 0 | base HW4 | D60 HW7 / D61 HW3 |
| beam | 23,253,697 | base only | 0 | base HW4 | D60 HW12 / D61 HW3 |
| walk | 100M | 1,226,734 | 0 | base HW4 | D60 HW5 / D61 HW3 |

Best 100M non-exact cap point:

```text
W57 = 0x370fcb1f
W58 = 0x2ded4986
W59 = 0x9e523680
D60 = 0x10004460 (HW 5)
D61 = 0x18080000 (HW 3)
```

### idx 8

Base:

```text
W57 = 0xaf07f044
W58 = 0x63f723cf
W59 = 0x10990224
D60 = 0
D61 = 0x41200001 (HW 4)
tail HW = 79
```

Runs:

| run | trials/evals | exact-D60 hits | exact HW<=3 hits | best exact | best cap |
|---|---:|---:|---:|---:|---|
| walk | 20M | 253,698 | 0 | base HW4 | D60 HW5 / D61 HW3 |
| beam | 23,253,697 | base only | 0 | base HW4 | D60 HW14 / D61 HW3 |
| walk | 100M | 1,265,760 | 0 | base HW4 | D60 HW4 / D61 HW3 |

Best 100M non-exact cap point:

```text
W57 = 0x27d1b95e
W58 = 0x62b5977e
W59 = 0x318aef12
D60 = 0x00220104 (HW 4)
D61 = 0x00442000 (HW 3)
```

## Carry comparison

The HW3 cap points are not close chart-preserving repairs of the exact
HW4 points.

For idx 0, the best HW3 cap point changes:

```text
off58 xor HW = 19
off59 xor HW = 18
round61 part xor HW = [0, 12, 16, 14]
round61 carry xor HW = [19, 18, 8]
```

For idx 8:

```text
off58 xor HW = 13
off59 xor HW = 12
round61 part xor HW = [0, 19, 14, 14]
round61 carry xor HW = [18, 15, 13]
```

Pair-residual repair from the HW3 shelves does not preserve the cap:

| candidate | shelf | rank pair | best linear repair |
|---:|---|---:|---|
| idx 0 | D60 HW5 / D61 HW3 | 62 | D60 HW19 / D61 HW5 |
| idx 8 | D60 HW4 / D61 HW3 | 63 | D60 HW13 / D61 HW7 |

## Interpretation

Freeing W57 does not unlock an exact sub-HW4 D61 point under the current
chart-walk operator. The high-volume exact populations are especially
informative:

```text
idx0 100M walk: 1,226,734 exact-D60 hits, all D61 HW4
idx8 100M walk: 1,265,760 exact-D60 hits, all D61 HW4
```

The operator can find D61 HW3 shelves, and it can find exact-D60 points,
but not both at once. The HW3 shelves move into different `off58/off59`
and round-61 Sigma1/Ch/T2 carry charts.

This strengthens the current diagnosis: the next useful operator is not
more W57 freedom by itself. It must actively compensate the specific
round-60 carry transitions while preserving the mixed round-61 chart.

No exact D61=0, D61 HW3, or tail improvement was found.
