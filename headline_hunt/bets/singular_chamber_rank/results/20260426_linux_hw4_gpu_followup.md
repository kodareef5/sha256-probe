# Linux HW4 and GPU Follow-Up - 2026-04-26

This note records the linux follow-up after macbook commit `37b721a` found
the first exact D61 HW4 point on idx 0.

## HW4 verification

The macbook point verifies locally:

```text
candidate idx 0: msb_cert_m17149975_ff_bit31
W57 = 0x370fef5f
W58 = 0x6ced4182
W59 = 0x9af03606

off58 = 0x00000021
off59 = 0x0deeb412

defect60 = 0
defect61 = 0x80110200 (HW 4)
tail HW = 77
```

`manifold61point` reports `rank_pair=64` at this point. The two-wall linear
system is locally full-rank: unlike the rank-63 terrace points, there is no
one-dimensional affine linear representative family to search.

## HW4 local follow-up

A 100M walk from the HW4 point did not find HW3. It did find a separate idx 0
tail point:

```text
W58 = 0x6ceb48b9
W59 = 0xb9143552
defect61 = 0x00010b7b (HW 10)
tail HW = 70
```

A larger 1B walk from the HW4 point also did not find HW3:

```text
trials: 1,000,000,000
exact60 hits: 56,015,090
changed exact60 hits: 371,122

best D61: HW4 (base point)
best changed D61: HW5
```

The same 1B walk improved idx 0's checked-tail frontier:

```text
W58 = 0x38fd0196
W59 = 0x9372cea1
defect61 = 0x12a3fea0 (HW 15)
defect62 = 0xaabbcc8c
defect63 = 0xe4420140
tail HW = 66
```

This is still worse than the global idx 8 tail-HW59 point, but it moves the
idx 0 Pareto frontier.

## Residual-fiber check

`pair61residualfiber` was added to close a loophole in the earlier linear
residual analysis. For rank-deficient pair systems, it enumerates all affine
kernel representatives for low-HW desired D61 residuals, rather than testing
only the one representative returned by the linear solver.

Results:

```text
idx8 cap-4 terrace: rank_pair=63, kernel_dim=1, exact_cap_representatives=0
idx8 HW59 tail:     rank_pair=63, kernel_dim=1, exact_cap_representatives=0
idx8 D61-HW2 shelf: rank_pair=62, kernel_dim=2, exact_cap_representatives=0
idx0 HW4 point:     rank_pair=64, kernel_dim=0, exact_cap_representatives=0
```

So the missing HW3/HW2 path is not hidden in the small affine kernel of the
linearized two-wall map. The obstruction remains arithmetic carry geometry,
not just choice of linear representative.

## GPU access and first scan

The linux laptop's RTX 4070 is not visible inside the default Codex sandbox,
but it is usable with escalated execution. Two access paths were proven:

```text
CUDA driver API + hand-written PTX: ok
OpenCL source JIT via NVIDIA ICD:  ok
device: NVIDIA GeForce RTX 4070 Laptop GPU
```

The first practical GPU tool is `opencl_off58_scan`, a W57/off58 chart scanner.
It is useful for bulk chart discovery, not for the current branch-heavy repair
walker.

Example scans:

```text
idx8, 16,777,216 random W57:
best off58 HW2 at W57=0xa707efce, off58=0x00000120

idx0, 33,554,432 random W57:
best off58 HW2 at W57=0x7976ba1b, off58=0x00000041

idx3, 33,554,432 random W57:
best off58 HW2 at W57=0xc468740a, off58=0x00100200
best low numeric HW3 at W57=0xfe9c0afc, off58=0x00000019
```

## W57 chart tests

The GPU-discovered W57 charts all reached exact D60, but did not beat the
known carry charts.

Initial 1M-start `defecthill57` results:

| candidate | W57 | off58 | exact hits | best exact D61 |
|---:|---:|---:|---:|---:|
| idx0 | `0x7976ba1b` | `0x00000041` | 8 | HW12 |
| idx3 | `0xc468740a` | `0x00100200` | 25 | HW10 |
| idx3 | `0xfe9c0afc` | `0x00000019` | 14 | HW11 |
| idx8 | `0xa707efce` | `0x00000120` | 24 | HW9 |

Deeper walks from the best exact points improved some of those charts but
still did not beat the established frontier:

| candidate/chart | trials | best D61 | best tail |
|---|---:|---:|---:|
| idx8 `off58=0x00000120` | 250M | HW7 | HW71 |
| idx3 `off58=0x00100200` | 100M | HW6 | HW67 |
| idx0 `off58=0x00000041` | 100M | HW7 | HW71 |

This is an important negative result: off58 sparsity by itself is not the
ranking function. The productive charts are selected by downstream carry
geometry, not merely by the Hamming weight or small numeric value of off58.

## Frontier after this follow-up

| objective | candidate | point | value |
|---|---:|---|---:|
| exact D61 | idx0 | `W58=0x6ced4182,W59=0x9af03606` | HW4 |
| checked tail | idx8 | `W58=0xe537c1c7,W59=0x598feb25` | HW59 |
| idx0 checked tail | idx0 | `W58=0x38fd0196,W59=0x9372cea1` | HW66 |

No collision and no exact D61=0 was found.
