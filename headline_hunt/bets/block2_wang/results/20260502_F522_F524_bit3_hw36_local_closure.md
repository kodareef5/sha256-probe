---
date: 2026-05-02
bet: block2_wang
status: PATH_C_POST_F521_LOCAL_CLOSURE_AND_RANK_SWEEP
parent: F521 bit3 HW36 breakthrough
evidence_level: VERIFIED
author: yale-codex
---

# F522/F542: bit3 HW36 and bit24 HW40 local closure plus post-floor rank sweep

## Setup

F521 pushed `bit3_m33ec77ca` from HW39 to HW36:

`W1[57..60] = 0xba476635 0x8cf9982c 0x06b9e787 0x2b032ff3`

The F521 synthesis suggested that at the HW36 layer W57..W59 may be fixed
and W60 may be the only live local coordinate. F522/F524 test that directly
with exact bridge-relaxed Hamming enumeration.

## Results

| Run | Slots | Radius | Total | Bridge pass | Bridge reject | HW<=36 | HW<36 |
|---|---|---:|---:|---:|---:|---:|---:|
| F522 | W60 | 1..5 | 242,824 | 241,606 | 1,218 | 0 | 0 |
| F523 | W60 | 1..6 | 1,149,016 | 1,145,714 | 3,302 | 0 | 0 |
| F524 | W59,W60 | 1..4 | 679,120 | 678,753 | 367 | 0 | 0 |
| F525 | W59,W60 | 1..5 | 8,303,632 | 8,302,369 | 1,263 | 0 | 0 |

All runs used `--relax-bridge`, so bridge-rejected cascade-valid neighbors
would still count as ties or improvements.

Best seen remained the seed:

- HW=36
- score=85.471
- hw63=`[13,2,1,0,12,7,1,0]`

## Interpretation

The bit3 HW36 point is locally boxed in under:

- W60-only moves through radius 6;
- W59+W60 joint moves through radius 4.

This strengthens the F521 geometry claim. W57 and W58 are fixed from the
F408/F520/F521 chain, W59 moved once at the HW39 breakthrough, and the HW36
basin is now locally closed against small W59/W60 perturbations.

## Verdict

Do not spend primary effort on small exact W60 tweaks around the bit3 HW36
record. The next bit3 work needs either:

1. manifest-rank restarts from post-HW36 side basins;
2. W59/W60 radius-6+ only if we want a stronger closure certificate;
3. a different coordinate such as pair-beam from a refreshed bit3 manifest.

## F526: bit24 HW40 W59/W60 radius-4 closure

F521 also pushed `bit24_mdc27e18c` from HW43 to HW40:

`W1[57..60] = 0x4be5074f 0x429efff2 0xf09458a7 0xa4fe0078`

F526 ran the matching exact W59/W60 radius-4 bridge-relaxed closure.

| Run | Slots | Radius | Total | Bridge pass | Bridge reject | HW<=40 | HW<40 |
|---|---|---:|---:|---:|---:|---:|---:|
| F526 | W59,W60 | 1..4 | 679,120 | 679,120 | 0 | 0 | 0 |

Best seen remained the seed:

- HW=40
- score=74.412
- hw63=`[6,12,4,0,9,7,2,0]`

Unlike bit3, every W59/W60 radius-4 neighbor bridge-passed, but none tied or
improved the HW40 record.

## F527: refreshed post-F521 manifests

Generated refreshed manifests from F520/F521 pair-beam artifacts:

- bit3 post-HW36 manifest:
  `search_artifacts/20260502_F527_bit3_post_hw36_basin_manifest.json`
  with 118 seeds.
- bit24 post-HW40 manifest:
  `search_artifacts/20260502_F527_bit24_post_hw40_basin_manifest.json`
  with 50 seeds.

Top bit3 seeds:

| Rank | HW | Score | W57..W60 |
|---:|---:|---:|---|
| 1 | 36 | 85.471 | `0xba476635 0x8cf9982c 0x06b9e787 0x2b032ff3` |
| 2 | 38 | 81.857 | `0xba476635 0x8cf9982c 0x06b9e787 0x2b0326e8` |
| 3 | 38 | 75.750 | `0xba476635 0x8cf9982c 0x06b9e787 0xdae32d04` |
| 4 | 39 | 81.000 | `0xba476635 0x8cf9982c 0x06b9e787 0x5882674c` |
| 5 | 39 | 79.143 | `0xba476635 0x8cf9982c 0x06b9e787 0x1aa567f5` |

Top bit24 seeds:

| Rank | HW | Score | W57..W60 |
|---:|---:|---:|---|
| 1 | 40 | 74.412 | `0x4be5074f 0x429efff2 0xf09458a7 0xa4fe0078` |
| 2 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xe09458af 0xe6560e70` |
| 3 | 43 | 74.105 | `0x4be5074f 0x429efff2 0xec9458af 0x360b8e79` |
| 4 | 43 | 72.270 | `0x4be5074f 0x429efff2 0xf09458a7 0x60fe09f0` |
| 5 | 44 | 78.143 | `0x4be5074f 0x429efff2 0xe89458af 0x3a19ebf5` |

## F528/F529: first post-floor manifest-rank continuations

Two first continuation probes tested the next available manifest rank above
the already-consumed F521 seeds.

| Run | Cand | Manifest rank | Init HW | Best HW | Verdict |
|---|---|---:|---:|---:|---|
| F528 | bit3 | 5 | 39 | 39 | reconnects to known F520 HW39 |
| F529 | bit24 | 5 | 44 | 42 | new side basin, not below HW40 |

F528 best:

- W=`0xba476635 0x8cf9982c 0x06b9e787 0x5882674c`
- same as F520 bit3 HW39 witness

F529 best:

- W=`0x4be5074f 0x429efff2 0xe8b458af 0x2a118bfc`
- hw63=`[8,8,2,0,13,6,5,0]`
- HW42, score=71.000

## F530/F542: batched post-floor rank sweep

Ran the controlled rank sweep suggested above with the same wide pair-beam
settings used by F521:

- pair pool 1024
- beam 1024
- max pairs 6
- max radius 12
- c+g penalty 2

This consumed 13 workers in parallel; total worker wall was 5,760.86 seconds,
with slowest single run 525.92 seconds.

### bit3 ranks 6..12

| Run | Rank | Init HW | Best HW | Score | Best W57..W60 |
|---|---:|---:|---:|---:|---|
| F530 | 6 | 39 | 38 | 83.667 | `0xba476635 0x8cf9982c 0x06b9e787 0x1a22af03` |
| F531 | 7 | 40 | 38 | 75.750 | `0xba476635 0x8cf9982c 0x06b9e787 0xdae32d04` |
| F532 | 8 | 40 | 38 | 83.667 | `0xba476635 0x8cf9982c 0x06b9e787 0x08a26aa5` |
| F533 | 9 | 40 | 38 | 75.750 | `0xba476635 0x8cf9982c 0x06b9e787 0xdae32d04` |
| F534 | 10 | 40 | 36 | 85.471 | `0xba476635 0x8cf9982c 0x06b9e787 0x2b032ff3` |
| F535 | 11 | 40 | 38 | 81.857 | `0xba476635 0x8cf9982c 0x06b9e787 0x2b0326e8` |
| F536 | 12 | 40 | 39 | 77.176 | `0xba476635 0x8cf9982c 0x0699e787 0x1b026703` |

No run found HW<36. Rank 10 reconnected to the known HW36 floor; ranks 6
and 8 produced alternate HW38 side basins with score 83.667.

### bit24 ranks 6..10 and 12

| Run | Rank | Init HW | Best HW | Score | Best W57..W60 |
|---|---:|---:|---:|---:|---|
| F537 | 6 | 44 | 41 | 71.647 | `0x4be5074f 0x429efff2 0xf09458af 0x4870f278` |
| F538 | 7 | 44 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xf1b458af 0xa814ef39` |
| F539 | 8 | 44 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xe09458af 0xe6560e70` |
| F540 | 9 | 44 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xf09458a7 0x51f6fdf8` |
| F541 | 10 | 44 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xecb458af 0x2e07ebfa` |
| F542 | 12 | 45 | 43 | 74.105 | `0x4be5074f 0x429efff2 0xec9458af 0x360b8e79` |

No run found HW<40. F537 is the useful new side basin: HW41 from manifest
rank 6, not enough to beat the F521 HW40 floor but closer than F529's HW42.
Ranks 7..10 and 12 all reconnect to HW43 basins.

## Updated Verdict

The post-pull edge is now:

- bit3 HW36 is strongly locally closed in W59/W60 through radius 5.
- bit24 HW40 is locally closed in W59/W60 through radius 4.
- Post-floor manifest continuations through bit3 ranks 5..12 and bit24
  ranks 5..10/12 did not improve the current floors.
- The bit3 basin is highly reconnective: many ranks flow back to the known
  HW36/HW38 W60-only family.
- bit24 still has a live side-basin ladder: F529 found HW42, F537 found
  HW41, but neither crossed the HW40 floor.

The most useful next compute is no longer small-radius closure around the
floor records. Better options:

1. expand bit24 around the F537 HW41 side basin with local W59/W60 closure
   and pair-beam restarts;
2. build a deduplicated bit3 HW38 side-basin manifest from F530/F532/F535;
3. test a different rank objective for bit3 because HW-ranked pair-beam now
   repeatedly returns to the same HW36 attractor.
