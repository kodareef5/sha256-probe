---
date: 2026-05-02
bet: block2_wang
status: ABSORBER_RANKED_PAIR_BEAM_FOLLOWUP
parent: F512 absorber matrix
evidence_level: VERIFIED
author: yale-codex
---

# F513/F515: absorber-ranked pair-beam follow-up

## Setup

F512 showed that the F491 HW35 seed is not the best second-block absorber
launch point under the crude absorber proxy. F513/F515 ask whether the
absorber-ranked residuals are also better starts for the standard block-1
pair-beam operator.

All runs used the same settings as the HW35-producing F487 path:

- candidate: `bit13_m916a56aa`
- slots: W57..W60
- pair pool: 1024
- max pairs: 6
- beam width: 1024
- max radius: 12
- penalty regs: `c,g`
- penalty weight: 2.0

## Results

| Run | F512 rank | Seed HW | Absorber min | Pair-beam best HW | Best score | Verdict |
|---|---:|---:|---:|---:|---:|---|
| F513 | 34 | 42 | 69 | 38 | 77.909 | fresh HW38 side basin |
| F514 | 21 | 41 | 71 | 38 | 83.667 | reconnects to known HW38 basin |
| F515 | 20 | 41 | 73 | 41 | 80.923 | no improvement |

F513 best:

- W=`0x5228ed8d 0x61a1a29c 0xea3a8439 0xf39d5a0b`
- hw63=`[13,6,3,0,10,4,2,0]`
- expanded=3,550,778; bridge_pass=3,550,764

F514 best:

- W=`0x5228ed8d 0x61a1a29c 0xea3a8c29 0x258bfd92`
- hw63=`[13,5,1,0,12,6,1,0]`
- expanded=3,448,278; bridge_pass=3,447,552
- same HW38 basin as earlier F467/F472/F474/F475/F500 artifacts

F515 best:

- seed remained best at HW41
- expanded=3,506,342; bridge_pass=3,505,818

## Interpretation

Absorber ranking is real enough to locate productive side basins, but it is
not enough by itself to beat the block-1 HW35 floor with the old pair-beam
operator.

The important distinction:

- As a **block-1 record-improvement selector**, the absorber ranking is weak.
- As a **two-block launch selector**, the absorber ranking is still live.

That argues against spending the next compute chunk on more direct F491
absorber-ranked pair beams. The old operator keeps mapping promising
two-block starts back to HW38/HW41 block-1 basins.

## Next move

Build a two-block-native profile table:

1. Treat each F491 residual as a block-1 output signature.
2. Treat each absorber matrix result as a block-2 correction signature.
3. Match by lane profile and bit overlap, not by scalar block-1 HW.
4. Use that to select residuals and second-block `M2` masks for a real
   meet/repair search.

## Verdict

Prune absorber-ranked direct pair-beam continuation for now. Continue the
absorber reframe, but change the operator: block-2 correction profiles should
drive the next search, not another scalar pair-beam pass over W57..W60.
