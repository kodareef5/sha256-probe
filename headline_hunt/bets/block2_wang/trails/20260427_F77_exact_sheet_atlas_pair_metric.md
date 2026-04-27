# F77: Exact Sheet Atlas And Pair-Alignment Metric

**2026-04-27 evening, linux_gpu_laptop**

This pass extended the F45 bit28 Pareto work in two ways:

- add a fourth block-2 target metric, `pair_hw`;
- stop treating W59 as the only useful chart coordinate by running exact
  W60 atlases over W57 and W58 one-bit sheets.

The result is a sharper map of the current bit28 basin. Exact W60 sheet
enumeration continues to be the productive operator; random high-Hamming
walks mostly return to known basins. The current LM frontier remains
LM637, while the local HW frontier inside the LM637 chart moved to HW39.

## Tool changes

`block2_pareto_sampler.c` now records:

```text
pair_hw = HW(a ^ e) + HW(b ^ f) + HW(c ^ g)
max_word_hw = max per-register final difference weight
```

The pair metric is a block-2 absorption hint: raw residual HW can be
large while paired registers are close to each other, which may be a
better shape for a second-block disturbance trail.

New modes:

```text
sweepwordbits m0 fill bit W57 W58 W59 word threads [start] [count]
pairwalk      m0 fill bit W57 W58 W59 W60 restarts steps threads seed max_flips [slack]
```

`sweepwordbits` enumerates exact W60 slices over the base sheet plus all
32 one-bit variants of W57, W58, or W59. Optional chunking lets a sheet
be split by W60 interval.

## LM descent from W59 exact rings

The old bit28 raw-LM record entering this pass was:

```text
W59 = 0xcb04eb44
W60 = 0xc425ef59
HW  = 65
LM  = 652
```

Centered exact W59 rings then descended:

| step | W59 | W60 | HW | LM | exact a61=e61 |
|---:|---:|---:|---:|---:|:---:|
| old raw LM | `0xcb04eb44` | `0xc425ef59` | 65 | 652 | no |
| ring 1 | `0x4b04eb44` | `0x3a355398` | 51 | 647 | no |
| ring 2 | `0x4b04cb44` | `0x458612a5` | 55 | 639 | no |
| ring 3 | `0x4b04cbc4` | `0x0a0627e6` | 45 | 637 | yes |

Current LM champion:

```text
m0   = 0xd1acca79
fill = 0xffffffff
bit  = 28

W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b04cbc4
W60 = 0x0a0627e6

HW       = 45
LM       = 637
pair_hw  = 15
symmetry = exact a61=e61
```

Verification:

```text
active adders: 43
LM incompatibilities: 0
cert-pin: UNSAT under kissat and cadical
```

## Pair-alignment descent

The HW33 champion has `pair_hw=17`, so pair alignment is not identical
to residual HW. Exact W60/W59 sheets found a separate pair frontier:

| step | W59 | W60 | HW | LM | pair_hw |
|---:|---:|---:|---:|---:|---:|
| HW33 champion | `0xc904fbc4` | `0x73b182dd` | 33 | 679 | 17 |
| pair10 | `0xc904fbc4` | `0xfa25159e` | 70 | 738 | 10 |
| pair9 | `0x4b04c344` | `0x5a196d1e` | 93 | 761 | 9 |
| pair8 | `0x4b0ccbc4` | `0x0d9444f8` | 78 | 731 | 8 |

Current pair champion:

```text
W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b0ccbc4
W60 = 0x0d9444f8

HW      = 78
LM      = 731
pair_hw = 8
```

Verification:

```text
active adders: 43
LM incompatibilities: 0
cert-pin: UNSAT under kissat and cadical
```

## W58 exact atlas

Command shape:

```text
sweepwordbits 0xd1acca79 0xffffffff 28 \
  0xce9b8db6 0xb26e4c72 0x4b04cbc4 58 24
```

This enumerated the base W58 sheet plus all 32 one-bit W58 neighbors,
with full 32-bit W60 coverage:

```text
count   = 141,733,920,768 evaluations
threads = 24
wall    = 2670.068 s
rate    = 53.083 M eval/s
```

Global result:

| axis | W58 | W60 | HW | LM | pair_hw | note |
|---|---:|---:|---:|---:|---:|---|
| best HW | `0xb26e4c72` | `0xf59dd823` | 39 | 720 | 25 | new local HW frontier |
| best LM | `0xb26e4c72` | `0x0a0627e6` | 45 | 637 | 15 | unchanged |
| best exact-sym LM | `0xb26e4c72` | `0x0a0627e6` | 45 | 637 | 15 | unchanged |
| best pair | `0xb26e5c72` | `0xbbd3c08c` | 96 | 838 | 10 | worse than pair8 |

The W58 atlas did not find a neighboring W58 sheet that improves LM637
or pair8. The best new HW point was on the base W58 sheet, not a W58
bit flip:

```text
W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b04cbc4
W60 = 0xf59dd823

HW      = 39
LM      = 720
pair_hw = 25
```

Verification:

```text
active adders: 43
LM incompatibilities: 0
cert-pin: UNSAT under kissat and cadical
```

## W57 exact atlas

W57 was chunked into four W60 intervals of size `2^28`; each chunk
covered the base W57 sheet plus all 32 one-bit W57 neighbors.

Combined result:

| W60 range | best HW | best LM | best pair |
|---:|---|---|---|
| `0x00000000..0x0fffffff` | HW43 / LM698 | HW45 / LM637 | pair12 |
| `0x10000000..0x1fffffff` | HW40 / LM681 | HW54 / LM652 | pair12 |
| `0x20000000..0x2fffffff` | HW46 / LM707 | HW71 / LM656 | pair12 |
| `0x30000000..0x3fffffff` | HW44 / LM700 | HW54 / LM654 | pair11 |

The best W57-atlas HW point was:

```text
W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b04cbc4
W60 = 0x1581e5e3

HW      = 40
LM      = 681
pair_hw = 22
symmetry = exact a61=e61
```

The W57 atlas did not beat LM637. The best new point again stayed on
the base W57 sheet rather than a one-bit W57 neighbor.

## Stochastic escape checks

Two 64-flip stochastic walks were run as negative controls:

| start | evals | objective | result |
|---|---:|---|---|
| pair8 | 650M | pairwalk | no pair improvement |
| LM637 | 650M | pointwalk | no LM improvement |

These negatives are useful because they separate the operators:

- exact W60 over structured sheets can move the frontier;
- broad random high-Hamming moves mostly fall back to known basins.

## Cross-candidate exact-W60 scouts

Several older F43/F45 representatives were also checked with exact W60
inside their current sheets. None displaced bit28's global status.

| candidate | best HW | best LM | best pair |
|---|---:|---:|---:|
| `bit2_ma896ee41` | 38 | 730 | 11 |
| `bit13_m4e560940` | 42 | 729 | 10 |
| `bit4_m39a03c2d` | 49 | 731 | 11 |
| `msb_ma22dc6c7` | 45 | 736 | 12 |

These scouts are not the main result here; they show the exact-W60
operator is broadly useful, while bit28 still dominates the combined
HW/LM/pair target set.

## Interpretation

Current bit28 target classes:

| role | W59 | W60 | HW | LM | pair_hw | symmetry |
|---|---:|---:|---:|---:|---:|:---:|
| minimum residual | `0xc904fbc4` | `0x73b182dd` | 33 | 679 | 17 | yes |
| local low-HW in LM637 chart | `0x4b04cbc4` | `0xf59dd823` | 39 | 720 | 25 | no |
| LM champion | `0x4b04cbc4` | `0x0a0627e6` | 45 | 637 | 15 | yes |
| pair champion | `0x4b0ccbc4` | `0x0d9444f8` | 78 | 731 | 8 | no |

The current chart looks locally exhausted for LM under:

- W59 one-bit exact rings,
- W58 one-bit exact atlas,
- W57 one-bit exact atlas over the checked W60 ranges,
- 64-flip stochastic pointwalks.

That does not close the block2_wang bet. It does say the next useful
step should not be another undirected pointwalk in the same coordinates.
Better next operators:

1. use pair-aligned residuals as explicit block-2 trail targets;
2. design an operator that changes W57/W58/W59 jointly while retaining
   exact W60 enumeration as the inner loop;
3. add a true two-block cert-pin / trail-verification harness once a
   candidate absorber exists;
4. if solver verification is required on linux_gpu_laptop, install or
   expose CryptoMiniSat; currently only kissat and cadical are present,
   so F76 `--solver all` cannot run to completion here.

No collision was found. All verified points above are near-residuals.
