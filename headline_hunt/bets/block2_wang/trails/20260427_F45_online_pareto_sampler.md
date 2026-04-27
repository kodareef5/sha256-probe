# F45: Online Pareto sampler pushes the LM frontier

**2026-04-27 09:35 EDT**

F43 showed that the existing F28/F42 corpus has a nontrivial Pareto
surface over residual HW and Lipmaa-Moriai cost. This pass changes the
sampler objective: instead of keeping only minimum residual HW, the new
`block2_pareto_sampler.c` keeps an online frontier over:

- final residual HW,
- LM cost,
- exact `a61=e61` symmetry.

The point is to test whether F43's LM757/765 records were structural
floors or simply artifacts of min-HW-biased corpus collection.

## Tool

```text
gcc -O3 -march=native -fopenmp -o /tmp/block2_pareto_sampler \
  headline_hunt/bets/block2_wang/trails/block2_pareto_sampler.c
```

Point checks reproduce F43 exactly:

```text
bit2  HW45 LM824 exact-symmetry point: verified
bit13 HW47 LM780 exact-symmetry point: verified
bit4  HW53 LM757 raw-LM point: verified
```

The tool also has a `walk` mode for local LM descent, but the first
smoke test did not beat random Pareto sampling. Random high-throughput
sampling is the stronger instrument so far.

## Matched 1B runs

Four F43 archetypes were sampled at 1B trials each:

| candidate | best HW | best LM | best exact-sym LM |
|---|---:|---:|---:|
| `bit28_md1acca79` | 49 / LM765 | 78 / LM730 | 63 / LM753 |
| `bit4_m39a03c2d` | 49 / LM796 | 82 / LM732 | 59 / LM755 |
| `bit13_m4e560940` | 51 / LM826 | 73 / LM752 | 68 / LM762 |
| `bit2_ma896ee41` | 47 / LM841 | 81 / LM759 | 72 / LM767 |
| `msb_ma22dc6c7` | 49 / LM795 | 72 / LM740 | 70 / LM763 |

This already moved the raw LM frontier from F43's LM757 down to LM730.

## Matched 10B runs

The two live LM leaders, bit28 and bit4, were then run for 10B samples
each.

### bit28 raw LM frontier: LM718

```text
candidate: bit28_md1acca79_fillffffffff
m0 = 0xd1acca79
fill = 0xffffffff
kernel_bit = 28

W57 = 0xa01d8ab7
W58 = 0x38272052
W59 = 0x598cc6c4
W60 = 0xebd0ebae

residual HW = 73
LM cost = 718
active adders = 43
LM incompatibilities = 0
exact a61=e61 = no
```

Per-round LM:

```text
r57 125
r58 109
r59  75
r60  65
r61  89
r62 127
r63 128
```

### bit4 raw LM frontier: LM720

```text
candidate: bit4_m39a03c2d_fillffffffff
m0 = 0x39a03c2d
fill = 0xffffffff
kernel_bit = 4

W57 = 0x68ab9705
W58 = 0x532c7e20
W59 = 0x41ea1ad4
W60 = 0x54a3ea0c

residual HW = 71
LM cost = 720
active adders = 43
LM incompatibilities = 0
exact a61=e61 = no
```

Per-round LM:

```text
r57 132
r58  95
r59  85
r60  73
r61  95
r62 133
r63 107
```

### bit4 exact-symmetry LM frontier: LM743

The best exact `a61=e61` low-LM point also moved:

```text
candidate: bit4_m39a03c2d_fillffffffff
W57 = 0x9edd4906
W58 = 0xc84fcdf8
W59 = 0x0fea7500
W60 = 0x6800e105

residual HW = 64
LM cost = 743
active adders = 43
LM incompatibilities = 0
exact a61=e61 = yes
```

This improves the F43 exact-symmetry LM frontier from LM772 to LM743.

## Updated Pareto interpretation

The new observed target set is:

| axis | candidate | record |
|---|---|---|
| minimum residual | `bit2_ma896ee41` | HW45 / LM824 / exact symmetry |
| balanced exact symmetry | `bit13_m4e560940` | HW47 / LM780 / exact symmetry |
| low HW, low LM | `bit28_md1acca79` | HW49 / LM765 |
| raw LM champion | `bit28_md1acca79` | HW73 / LM718 |
| exact-symmetry LM champion | `bit4_m39a03c2d` | HW64 / LM743 |

The important conclusion is not that LM718 is directly exploitable. Even
LM718 remains far beyond one-block random freedom (`256 - 718 = -462`).
The conclusion is that the first-block residual generator has a much
broader trail-cost surface than the min-HW corpus exposed. Different
objectives select different witnesses and, in some cases, different
candidates.

## Next

- Run deeper on bit28 and bit4 to see whether the raw LM tail keeps
  dropping below 718.
- Add a score-biased sampler or mutation operator if random sampling
  starts showing a stable LM floor.
- Preserve separate target classes for block2 trail design: min-HW,
  exact-symmetry, and raw low-LM.
