# D60 Repair-Fiber Exhaustion - 2026-04-26

This pass tested whether the low-D61 non-exact shelves hide an exact `D60=0`
representative inside the linearized D60 repair fiber. The new tool mode is
`d60repairfiberseq`: solve the linearized D60 equation, then enumerate the
32-dimensional D60 kernel deterministically.

The point of this pass was not another greedy walk. It was a finite chart
question: if the desired low-D61 shelf can be repaired by a representative in
the local D60-linear affine fiber, exhaustive kernel coverage should see it.

## D60-HW7 / D61-HW2 shelf

Base:

```text
idx = 8
W57 = 0xaf07f044
W58 = 0x569a93da
W59 = 0x1f813291
D60 = 0x88400a30 (HW 7)
D61 = 0x00020040 (HW 2)
rank60 = 32
kernel_dim = 32
```

The full `2^32` kernel was covered in five deterministic chunks:

| start | count | exact D60 hits | exact cap-HW2 hits | best exact D61 |
|---:|---:|---:|---:|---:|
| `0x00000000` | 1,000,000,000 | 2 | 0 | HW11 |
| `0x3b9aca00` | 1,000,000,000 | 1 | 0 | HW8 |
| `0x77359400` | 1,000,000,000 | 0 | 0 | none |
| `0xb2d05e00` | 1,000,000,000 | 0 | 0 | none |
| `0xee6b2800` | 294,967,296 | 0 | 0 | none |

Best exact landing:

```text
W58 = 0x443d0254
W59 = 0x46873608
D60 = 0
D61 = 0x30a10015 (HW 8)
tail HW = 83
```

So the D60-linear fiber does contain exact nonlinear D60 representatives, but
the low-D61 terrace does not survive the repair. The best exact D61 found in
the whole fiber was HW8, not HW2.

## D60-HW4 / D61-HW4 terrace

Base:

```text
idx = 8
W57 = 0xaf07f044
W58 = 0xdd55ab86
W59 = 0x1d9ca68f
D60 = 0x04042100 (HW 4)
D61 = 0x00098100 (HW 4)
rank60 = 32
kernel_dim = 32
```

Full-kernel coverage:

| start | count | exact D60 hits | exact cap-HW4 hits | best exact D61 |
|---:|---:|---:|---:|---:|
| `0x00000000` | 1,000,000,000 | 0 | 0 | none |
| `0x3b9aca00` | 1,000,000,000 | 0 | 0 | none |
| `0x77359400` | 1,000,000,000 | 0 | 0 | none |
| `0xb2d05e00` | 1,000,000,000 | 1 | 0 | HW17 |
| `0xee6b2800` | 294,967,296 | 0 | 0 | none |

Best exact landing:

```text
W58 = 0x37d21cd8
W59 = 0xdfe35c75
D60 = 0
D61 = 0xf6af2c22 (HW 17)
tail HW = 95
```

This terrace is even less compatible with exact repair than the HW2 shelf:
only one exact D60 representative appeared across the full kernel, and it lost
the cap by thirteen D61 bits.

## Shelf Around The HW8 Exact Landing

The HW2 shelf's best exact landing was then treated as a new center:

```text
W58 = 0x443d0254
W59 = 0x46873608
D60 = 0
D61 = 0x30a10015 (HW 8)
```

Radius-7 enumeration found nearby non-exact shelves:

```text
D60-HW5 / D61-HW3:
  W58 = 0x663d0a94
  W59 = 0x46c72608
  D60 = 0x04180420
  D61 = 0x80004020

D60-HW4 / D61-HW4:
  W58 = 0x463d8a54
  W59 = 0x4607363c
  D60 = 0x20000007
  D61 = 0x80080060
```

A 200M exact-surface walk from the HW8 landing found:

```text
best exact D61 = HW6
W58 = 0x9639427e
W59 = 0x44a15e0e
tail HW = 77

best checked tail = HW69
W58 = 0x449ed620
W59 = 0x0e590145
```

No new global frontier was found.

## D60-HW5 / D61-HW3 Local Shelf

Base:

```text
W58 = 0x663d0a94
W59 = 0x46c72608
D60 = 0x04180420 (HW 5)
D61 = 0x80004020 (HW 3)
rank60 = 32
kernel_dim = 32
```

Full-kernel coverage:

| start | count | exact D60 hits | exact cap-HW3 hits | best exact D61 |
|---:|---:|---:|---:|---:|
| `0x00000000` | 1,000,000,000 | 0 | 0 | none |
| `0x3b9aca00` | 1,000,000,000 | 0 | 0 | none |
| `0x77359400` | 1,000,000,000 | 0 | 0 | none |
| `0xb2d05e00` | 1,000,000,000 | 1 | 0 | HW14 |
| `0xee6b2800` | 294,967,296 | 0 | 0 | none |

Best cap-preserving point found in the first chunk:

```text
W58 = 0xfd7672e4
W59 = 0x6a4851b2
D60 = 0x00008980 (HW 4)
D61 = 0x01081000 (HW 3)
```

Best exact landing:

```text
W58 = 0x624eba0b
W59 = 0x9e39a0ca
D60 = 0
D61 = 0x84ccdc92 (HW 14)
tail HW = 103
```

Again, the exact repair exists but destroys the low-D61 chart.

## idx17 D60-HW7 / D61-HW1 Shelf

Macbook found exact D61 HW4 on idx17, the sparsest known `off58` chart:

```text
idx = 17
W57 = 0xa418c4ae
off58 = 0x00000001
```

Radius-7 enumeration around that exact point exposed an even lower non-exact
shelf:

```text
W58 = 0x46d3f03a
W59 = 0x6cb9eeaa
D60 = 0x14400229 (HW 7)
D61 = 0x10000000 (HW 1)
```

This is the lowest-D61 shelf seen so far, so it is the cleanest test of the
D60-linear repair hypothesis. The full `2^32` kernel was covered:

| start | count | exact D60 hits | exact cap-HW1 hits | best exact D61 |
|---:|---:|---:|---:|---:|
| `0x00000000` | 1,000,000,000 | 0 | 0 | none |
| `0x3b9aca00` | 1,000,000,000 | 2 | 0 | HW14 |
| `0x77359400` | 1,000,000,000 | 2 | 0 | HW14 |
| `0xb2d05e00` | 1,000,000,000 | 1 | 0 | HW15 |
| `0xee6b2800` | 294,967,296 | 0 | 0 | none |

Best exact landing by checked tail among the HW14 exact repairs:

```text
W58 = 0xdfb14481
W59 = 0xfbf35806
D60 = 0
D61 = 0xfac02e12 (HW 14)
tail HW = 88
```

The full fiber found five exact D60 representatives and zero exact
cap-preserving representatives. Repairing the HW1 shelf through the D60-linear
fiber does not land near the exact HW4 frontier; it jumps all the way back to
double-digit D61.

Local pair/triple/quad descent did not reveal a small combinatorial bridge
either. Strict cap-preserving descent refused to move from the shelf; a
closure-first policy could reduce D60 but lost the chart, ending at D60-HW3 /
D61-HW13.

## New HW1 off58 Charts

The OpenCL W57 scanner was also run across more candidates while the CPU fiber
sweeps were in flight. It found several additional `off58` HW1 charts:

| idx | candidate | W57 | off58 | downstream test |
|---:|---|---:|---:|---|
| 9 | `bit3_m5fa301aa_ff` | `0x84dfb86e` | `0x00040000` | exact D60 found, best D61 HW16 in 262k starts |
| 13 | `bit14_m40fde4d2_ff` | `0x52e8a9a4` | `0x80000000` | exact D60 found, 250M walk reached D61 HW7 and tail HW73 |
| 14 | `bit25_ma2f498b1_ff` | `0x1a4c712e` | `0x00000080` | exact D60 found, best D61 HW13 in 262k starts |
| 15 | `bit4_m39a03c2d_ff` | `0x24aed0bc` | `0x00080000` | exact D60 found, best D61 HW13 in 262k starts |

The idx13 chart was the strongest new one:

```text
W57 = 0x52e8a9a4
W58 = 0x7260a7ef
W59 = 0xb72312aa
off58 = 0x80000000
D60 = 0
D61 = 0x20040631 (HW 7)
tail HW = 85
```

Its best checked-tail point in the same 250M walk was:

```text
W58 = 0x2ba6a6f9
W59 = 0xa64e02fc
D61 = 0x170aa400
tail HW = 73
```

These scans strengthen the negative on simple sparse-offset ranking. `off58`
HW1 is not sufficient: idx17 reaches HW4, while new HW1 charts tested here
only reached HW7/HW13/HW16 under the same family of descent operators.

## Interpretation

The D60-linear fiber is not empty. It contains rare exact nonlinear D60
landings. But across four full 32-dimensional kernel sweeps:

| source chart | base D60/D61 | exact low-cap representatives | best exact D61 |
|---|---:|---:|---:|
| original HW2 shelf | HW7 / HW2 | 0 | HW8 |
| cap-4 terrace | HW4 / HW4 | 0 | HW17 |
| local HW3 shelf | HW5 / HW3 | 0 | HW14 |
| idx17 HW1 shelf | HW7 / HW1 | 0 | HW14 |

This makes the obstruction sharper. The missing bridge is not simply hidden in
the local D60-linear affine fiber. Closing D60 is possible, but the required
representatives leave the mixed Sigma1/Ch/T2 carry chart and re-enter a worse
exact-D60 chart.

The next operator should not be another plain D60 linear repair. It should
target the carry transition itself: preserve the low-D61 mixed chart while
compensating the specific carry bits that make D60 nonzero.
