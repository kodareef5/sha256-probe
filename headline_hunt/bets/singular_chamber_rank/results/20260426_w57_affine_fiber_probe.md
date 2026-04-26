# W57-Affine Fiber Probe - 2026-04-26

This pass tested whether the repair wall is an artifact of exhausting only the
fixed-W57, 64-bit `(W58,W59)` D60 fiber. The new tool modes are:

- `d60repairfiber96`: sample the local D60-linear affine fiber over all
  96 bits of `(W57,W58,W59)`.
- `d60repairfiber96low`: enumerate low-weight combinations of the 96-bit
  D60-kernel basis.

The target was the idx17 D60-HW7 / D61-HW1 shelf:

```text
idx = 17
W57 = 0xa418c4ae
W58 = 0x46d3f03a
W59 = 0x6cb9eeaa
D60 = 0x14400229 (HW 7)
D61 = 0x10000000 (HW 1)
```

## 96-bit D60 fiber

The 96-bit local D60 map has full rank and a 64-dimensional kernel:

```text
rank60 = 32
kernel_dim = 64
particular_delta_hw = 17
```

A 50M random sample over the 64-dimensional kernel found no nonlinear exact
D60 landing:

```text
samples = 50,000,000
exact60_hits = 0
exact_cap_hits = 0
cap_hits = 1  (the base shelf only)
```

Best sampled point:

```text
W57 = 0x4068e76f
W58 = 0x2e1d0fb5
W59 = 0x83608b68
D60 = 0x00100100 (HW 2)
D61 = 0x1490096c (HW 10)
```

This differs from the fixed-W57 64-bit fiber, where exact D60 landings were
rare but visible after full `2^32` coverage. In the 96-bit fiber, random kernel
sampling is too diffuse: it reaches lower D60, but loses the D61-HW1 chart.

## Low-weight kernel enumeration

The low-weight enumerator checked all kernel-basis combinations through
weight 6:

| max kernel weight | representatives checked | exact D60 | exact cap | best D60 / D61 |
|---:|---:|---:|---:|---:|
| 4 | 679,121 | 0 | 0 | HW3 / HW13 |
| 5 | 8,303,633 | 0 | 0 | HW1 / HW19 |
| 6 | 83,278,001 | 0 | 0 | HW1 / HW19 |

Best low-weight point:

```text
W57 = 0x30f1b805
W58 = 0x46f1f23a
W59 = 0x6d99eeaa
D60 = 0x00000040 (HW 1)
D61 = 0x18ebeaf9 (HW 19)
```

So the 96-bit affine space does contain directions that almost close D60, but
the D61 chart is destroyed even before exact repair.

## Calibrated chart walks

A previous attempt launched oversized 100M `chart61walk` jobs. Those were
stopped as mis-sized. The calibrated replacement used 1M trials, 8 threads,
64 passes, and 32 max flips.

| target | cap | cap hits | exact D60 hits | result |
|---|---:|---:|---:|---|
| idx17 D61-HW1 shelf | 1 | 36,378 | 0 | stayed at D60-HW7/D61-HW1 |
| idx17 D61-HW1 shelf | 4 | 37,900 | 0 | stayed at D60-HW7/D61-HW1 |
| idx8 D61-HW2 shelf | 2 | 35,451 | 0 | stayed at D60-HW7/D61-HW2 |

This says the low-D61 cap chart is broad under chart-preserving moves, but it
does not contain exact-D60 landings at this scale. The chart and exactness are
still separated.

## Interpretation

Freeing W57 and sampling the larger affine repair space does not reveal a
hidden bridge. It creates more ways to reduce D60, but those directions behave
like the earlier terraces: D61 rises sharply as D60 approaches zero.

The current best explanation is now narrower:

- sparse `off58` is not the predictor,
- local pair rank is not the predictor,
- fixed-W57 affine fibers do not hide the repair,
- W57-free affine fibers also do not hide the repair,
- the missing operation must compensate specific carry transitions while
  preserving the mixed Sigma1/Ch/T2 chart.

No exact D61=0, D61 HW3, or tail improvement was found.
