---
date: 2026-05-04
bet: block2_wang
status: BIT24_HW78_PAIR_BEAM_BREAKTHROUGH
parent: F788 six-pair overlap HW86 detour
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F789: bit24 F788 HW86 pair-beam reaches HW78

## Setup

F789 restarts the standard pure-HW M2 pair beam from the best F788 overlap
detour.

Lineage:

```text
F760: bit24 target/repair combo reached HW82
F788: six-pair overlap selector produced HW86 / target L1 16 detour
F789: pure-HW pair beam from F788 detour reached HW78
```

Run parameters:

```text
candidate: bit24_mdc27e18c
init HW: 86
init lane: [14, 13, 10, 8, 8, 8, 12, 13]
objective: pure HW
pair pool: 1024
beam width: 1024
max pairs: 6
max radius: 12
rounds: 24
```

## Result

```text
pair pool: 130,816 -> top 1,024
pair-pool HW range: 92..109
depth bests: 92, 90, 86, 90, 85, 78
new records below HW86: 2
best seen HW: 78
best depth: 6
wall seconds: 680.53
```

New best:

```text
HW 78
lane [13, 11, 8, 9, 7, 9, 8, 13]
depth 6
bits [39, 52, 97, 108, 114, 130, 136, 231, 266, 344, 421, 437]
```

M2:

```text
0x00805000 0x21000080 0x00004004 0x40146000
0x00000104 0x10001000 0x00000001 0x00200080
0x08006410 0x20020040 0x00808108 0x00010000
0x06000000 0x00240020 0x12018002 0x00000040
```

Secondary record:

```text
HW 85
lane [11, 12, 15, 9, 6, 12, 8, 12]
depth 5
```

## Interpretation

This is the first clear improvement below the HW82 floor. The useful pattern is
two-stage:

```text
non-greedy overlap combo creates a repairable side basin
standard pure-HW pair beam repairs that basin hard
```

F788 by itself looked negative because it did not preserve HW82. But it moved
to an HW86 basin that the standard beam could exploit. That means the overlap
selector is not a floor-preserving selector; it is a basin-transfer operator.

Current mapped bit24/global floor is now HW78.

## Artifact

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F789_bit24_f788_hw86_pair_beam_hw.json
```

## Next

1. Run a pair-potential atlas around the HW78 witness.
2. Then run c/g and/or pure-HW restarts only if the atlas shows local exits.
3. Add the HW78 witness to any current portfolio/atlas summary.
