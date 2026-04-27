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

## 100B follow-up

Matched 100B random Pareto runs on bit28 and bit4 did not improve the
10B frontiers:

| candidate | samples | best HW | best raw LM | best exact-sym LM |
|---|---:|---:|---:|---:|
| `bit28_md1acca79` | 100B | HW47 / LM792 | HW73 / LM718 | HW81 / LM749 |
| `bit4_m39a03c2d` | 100B | HW49 / LM796 | HW71 / LM720 | HW64 / LM743 |

So random online sampling appears to hit a local floor around LM718 on
bit28 and LM720 on bit4 at this budget.

## Seeded point-walk

The sampler's `pointwalk` mode starts from a known witness and applies
small random bit-flip moves, accepting lower-LM moves and occasional
near-neutral moves. This tests whether the low-LM records are isolated
random tail events or sit on a locally navigable carry chart.

Starting from the bit28 LM718 point immediately moved the frontier:

```text
candidate: bit28_md1acca79_fillffffffff
W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b1debc4
W60 = 0x69d0ab84

residual HW = 65
LM cost = 703
exact a61=e61 = yes
```

Starting from that LM703 point moved again:

```text
candidate: bit28_md1acca79_fillffffffff
W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b1debc4
W60 = 0x65d4a9a4

residual HW = 73
LM cost = 687
exact a61=e61 = no
```

The best exact-symmetry point from the same local basin is:

```text
candidate: bit28_md1acca79_fillffffffff
W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b1de3c4
W60 = 0x6dd8ab9d

residual HW = 67
LM cost = 690
exact a61=e61 = yes
```

Independent `active_adder_lm_bound` checks verify all three points with
43 active adders and zero LM incompatibilities.

A further 514M-evaluation point-walk from LM687 did not reduce raw LM
below 687. It did find a bit28 residual-HW improvement:

```text
candidate: bit28_md1acca79_fillffffffff
W57 = 0xe82445f4
W58 = 0xe32e013a
W59 = 0x6816a172
W60 = 0xd9e18932

residual HW = 46
LM cost = 800
exact a61=e61 = no
```

This does not beat the global bit2 HW45 residual, but it moves bit28's
own HW frontier from HW49 to HW46.

## Updated Pareto interpretation

The new observed target set is:

| axis | candidate | record |
|---|---|---|
| minimum residual | `bit2_ma896ee41` | HW45 / LM824 / exact symmetry |
| balanced exact symmetry | `bit13_m4e560940` | HW47 / LM780 / exact symmetry |
| low HW, low LM | `bit28_md1acca79` | HW46 / LM800 and HW49 / LM765 |
| raw LM champion | `bit28_md1acca79` | HW73 / LM687 |
| exact-symmetry LM champion | `bit28_md1acca79` | HW67 / LM690 |

The important conclusion is not that LM687 is directly exploitable. Even
LM687 remains far beyond one-block random freedom (`256 - 687 = -431`).
The conclusion is that the first-block residual generator has a much
broader trail-cost surface than the min-HW corpus exposed. Different
objectives select different witnesses and, in some cases, different
candidates.

## Next

- Continue seeded point-walks from the bit28 LM687/LM690 basin with
  different move radii and acceptance slack.
- Add a score-biased sampler if the point-walk also stabilizes.
- Preserve separate target classes for block2 trail design: min-HW,
  exact-symmetry, and raw low-LM.
