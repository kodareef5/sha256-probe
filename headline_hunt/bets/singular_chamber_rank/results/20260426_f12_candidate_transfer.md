# F12 Candidate Transfer Probe - 2026-04-26

This pass tested whether macbook's `cascade_aux_encoding` F12 residual-grid
champions transfer into the `singular_chamber_rank` D60/D61 surface.

Macbook's F12 result fully enumerated the cascade-aux `de58` residual over
`2^32` W57 chambers and found structured low-HW residual grids:

| candidate | F12 min residual |
|---|---:|
| `msb_m189b13c7_80` | HW2 |
| `bit13_m4e560940_aa` | HW3 |
| `bit17_m427c281d_80` | HW3 |
| `bit18_m99bf552b_ff` | HW4 |

The first question was whether those low residuals are the same object as
this bet's `off58`. They are not. At the F12 min-W57 chambers, this bet's
round-58 cascade offsets are ordinary:

| candidate | F12 min W57 | singular off58 | off58 HW | best exact D61 in 1M |
|---|---:|---:|---:|---:|
| `msb_m189b13c7_80` | `0x303567fc` | `0x98ad226e` | 15 | HW15 |
| `bit13_m4e560940_aa` | `0x7032b79b` | `0xec0abcc1` | 15 | HW14 |
| `bit17_m427c281d_80` | `0x11ffa8d7` | `0xfa18888c` | 13 | HW14 |
| `bit18_m99bf552b_ff` | `0x000accaf` | `0x3337f4ca` | 18 | HW14 |

So the F12 residual is not directly the `singular_chamber_rank` `off58`
coordinate.

## GPU off58 scans

The candidates were added to the OpenCL W57/off58 scanner and scanned for
productive singular charts directly.

| candidate | samples | best W57 | best off58 | HW |
|---|---:|---:|---:|---:|
| `msb_m189b13c7_80` | 67,108,864 | `0xbe156658` | `0x00000200` | 1 |
| `bit13_m4e560940_aa` | 67,108,864 | `0x9fd515c0` | `0x00000282` | 3 |
| `bit17_m427c281d_80` | 67,108,864 | `0x3c438213` | `0x01000000` | 1 |
| `bit18_m99bf552b_ff` | 67,108,864 | `0xacae3c5c` | `0x00002010` | 2 |

The GPU found useful sparse singular charts for the F12 candidates, even
though they were not the same as the F12 min-W57 charts.

## Downstream D60/D61 tests

Initial fixed-W57 exact-hit selection:

| candidate | fixed W57 | trials | exact hits | best exact D61 |
|---|---:|---:|---:|---:|
| `msb_m189b13c7_80` | `0xbe156658` | 1M | 13 | HW9 |
| `bit13_m4e560940_aa` | `0x9fd515c0` | 1M | 20 | HW11 |
| `bit17_m427c281d_80` | `0x3c438213` | 1M | 23 | HW7 |
| `bit18_m99bf552b_ff` | `0xacae3c5c` | 1M | 11 | HW9 |

Larger fixed-W57 passes:

| candidate | trials | exact hits | best exact D61 |
|---|---:|---:|---:|
| `msb_m189b13c7_80` | 16M | 195 | HW8 |
| `bit13_m4e560940_aa` | 8M | 133 | HW10 |
| `bit17_m427c281d_80` | 16M | 314 | HW7 |
| `bit18_m99bf552b_ff` | 8M | 95 | HW9 |

Exact-surface walks on the two strongest new charts:

| candidate | trials | best exact D61 | best checked tail |
|---|---:|---:|---:|
| `msb_m189b13c7_80` | 50M | HW7 | HW72 |
| `msb_m189b13c7_80` | 250M | HW7 | HW71 |
| `bit17_m427c281d_80` | 50M | HW7 | HW72 |
| `bit17_m427c281d_80` | 100M | HW6 | HW67 |

Best points:

```text
msb_m189b13c7_80 D61 frontier
W57 = 0xbe156658
W58 = 0x38c4ec09
W59 = 0xb0b9e93a
D61 = 0x00101dc0 (HW 7)
tail HW = 81

msb_m189b13c7_80 tail frontier
W58 = 0xdc529e78
W59 = 0x0ae0a131
D61 = 0xdb162c00
tail HW = 71

bit17_m427c281d_80 D61 frontier
W57 = 0x3c438213
W58 = 0xf3b64da1
W59 = 0xea123575
D61 = 0xa0240202 (HW 6)
tail HW = 87

bit17_m427c281d_80 tail frontier
W58 = 0x0b3d6f7b
W59 = 0xf9c28114
D61 = 0xff7f0ffe
tail HW = 67
```

## Interpretation

The F12 candidates do transfer into the low-D61 class once the singular
`off58` chart is found directly by GPU scan. They do not currently beat the
known frontiers:

```text
global exact D61 frontier: HW4
global checked tail frontier: HW59

best F12-transfer exact D61: HW6
best F12-transfer checked tail: HW67
```

This separates two objects:

- `cascade_aux_encoding` F12 `de58` residual grids identify a different
  structural surface.
- `singular_chamber_rank` still needs sparse `off58` plus downstream
  carry-chart compatibility.

The F12 result is therefore useful as a candidate source, but not a direct
ranking function for this bet. It produced new second-tier charts, not a new
frontier.

No exact D61=0, D61 HW3, or tail improvement was found.
