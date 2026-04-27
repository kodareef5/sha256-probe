# GPU Sparse-Chamber Scan - 2026-04-27

This pass used the existing OpenCL `off58` scanner on the RTX 4070 Laptop
GPU to look for additional sparse `off58` chambers, then handed the best
GPU-discovered `W57` values back to the CPU `defecthill57` exact-D60
descent.

The goal was not another raw random search. It was to test whether the
singular-chamber mechanism is portable to candidates highlighted by the
message-space and macbook F-series work.

## GPU scan

Each GPU scan used 67,108,864 random `W57` samples.

| idx | candidate | best `W57` | best `off58` | HW |
|---:|---|---:|---:|---:|
| 19 | `bit13_m4e560940_aa` | `0xf0023645` | `0x00002200` | 2 |
| 17 | `bit15_m28c09a5a_ff` | `0x455edff0` | `0x00000402` | 2 |
| 18 | `msb_m189b13c7_80` | `0x84fbdbcb` | `0x00010000` | 1 |
| 1 | `bit19_m51ca0b34_55` | `0x7e55afad` | `0x00010080` | 2 |
| 11 | `bit14_m67043cdd_ff` | `0x2e059c6a` | `0x00008040` | 2 |

The idx 18 hit is the cleanest sparse-offset chamber found so far by this
scan family: a one-bit `off58`.

## Exact-D60 follow-up

For each GPU-discovered chamber, `defecthill57` ran 524,288 CPU starts
with the fixed `W57`.

| idx | exact D60 hits | best exact D61 | HW | checked tail HW | exact point |
|---:|---:|---:|---:|---:|---|
| 17 | 10 | `0x06aa221a` | 11 | 105 | `W58=0x0729a098,W59=0x55747b37` |
| 19 | 13 | `0x52721688` | 12 | 97 | `W58=0xcdd36768,W59=0x1b7784b3` |
| 1 | 10 | `0x2316245c` | 12 | 92 | `W58=0xc2aad5b7,W59=0x650cc1e0` |
| 11 | 5 | `0x67211ec9` | 15 | 99 | `W58=0x64053877,W59=0x9f08da14` |
| 18 | 5 | `0xce14895f` | 16 | 96 | `W58=0xeb5cfd5f,W59=0x20041253` |

All five sparse chambers reached exact D60 at full 32-bit width. None beats
the current exact-D61 HW4 / tail-HW59 frontier.

## Interpretation

The GPU scan strengthens the portability claim: sparse `off58` chambers are
easy to find across multiple candidates, and exact D60 is reachable after
fixing those chambers. The next-wall quality is chamber-specific, though:
even the one-bit idx 18 `off58` chamber only reached D61 HW16 in the first
524k-start pass.

So `off58` sparsity is an entry condition, not the whole explanation. The
better predictor likely includes the round-59 carry chart and the D61
`dh+dCh` image after exact D60 repair. GPU scanning is useful for generating
fresh chambers, but CPU/carry-coordinate follow-up remains necessary to rank
them.
