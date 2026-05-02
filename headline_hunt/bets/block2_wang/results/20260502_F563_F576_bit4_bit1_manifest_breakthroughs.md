---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT1_HW35_BIT4_HW36_PANEL_BREAKTHROUGH
parent: F525 panel expansion
evidence_level: VERIFIED
author: yale-codex
---

# F563/F576: bit4 and bit1 manifest-rank breakthroughs

## Setup

Pulled macbook's F525 panel expansion and followed its top two new cands:

- `bit4_m39a03c2d`, F525 wide-anneal floor HW43
- `bit1_m6fbc8d8e`, F525 wide-anneal floor HW45

All pair-beam runs used the F521 settings:

- pair pool 1024
- beam 1024
- max pairs 6
- max radius 12
- c/g penalty weight 2

## First pair-beam descents

| Run | Cand | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F563 | bit4 | 43 | 36 | 85.471 | `0x726ca5c7 0x6db409f8 0x12f025f7 0x778d3357` |
| F564 | bit1 | 45 | 40 | 78.333 | `0x7f74bd45 0x65649ab9 0xb0e869c9 0xae49bf68` |

F563 immediately makes bit4 competitive with bit3 HW36. F564 makes bit1
competitive with bit24 HW40 before manifest-rank restarts.

## Manifest-rank follow-ups

F565 extracted first manifests:

- bit4 post-HW36: 53 seeds
- bit1 post-HW40: 31 seeds

Then F566/F571 tested ranks 2..4 for each.

| Run | Cand | Manifest rank | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---:|---|
| F566 | bit4 | 2 | 37 | 37 | 84.571 | `0x726ca5c7 0x6db409f8 0x12f025f7 0xf6ed309b` |
| F567 | bit4 | 3 | 38 | 36 | 85.471 | `0x726ca5c7 0x6db409f8 0x12f135f1 0x05493417` |
| F568 | bit4 | 4 | 39 | 39 | 82.757 | `0x726ca5c7 0x6db409f8 0x12f025f7 0x2dc92e39` |
| F569 | bit1 | 2 | 41 | 40 | 78.333 | `0x7f74bd45 0x65649ab9 0xb0e869c9 0xae49bf68` |
| F570 | bit1 | 3 | 41 | 40 | 78.333 | `0x7f74bd45 0x65649ab9 0xb0e869c9 0xae49bf68` |
| F571 | bit1 | 4 | 42 | 35 | 86.364 | `0x7f74bd45 0x65649ab9 0xb0e869c5 0x9ea93f2b` |

F571 is the new headline: bit1 drops from F525 HW45 to HW35, tying bit13's
current Path C best.

## Cert-pin validation

`--solver all` is not usable on this host because `cryptominisat5` is
missing. Each headline record was rerun with kissat and cadical separately.

| Witness | kissat | cadical |
|---|---|---|
| F563 bit4 HW36 | UNSAT, 0.008s | UNSAT, 0.019s |
| F564 bit1 HW40 | UNSAT, 0.008s | UNSAT, 0.015s |
| F571 bit1 HW35 | UNSAT, 0.022s | UNSAT, 0.043s |
| F567 bit4 alternate HW36 | UNSAT, 0.022s | UNSAT, 0.041s |
| F580 bit4 HW35 | UNSAT, 0.012s | UNSAT, 0.018s |

All are confirmed near-residuals, not full collisions.

## Local closure

Exact bridge-relaxed closures around the headline floors:

| Run | Cand | Floor | Slots | Radius | Total at max radius | Bridge pass | Bridge reject | HW<=floor | HW<floor |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| F572 | bit1 | 35 | W60 | 6 | 906,192 | 906,053 | 139 | 0 | 0 |
| F573 | bit1 | 35 | W59,W60 | 4 | 635,376 | 635,328 | 48 | 0 | 0 |
| F574 | bit4 | 36 | W60 | 6 | 906,192 | 891,714 | 14,478 | 0 | 0 |
| F575 | bit4 | 36 | W59,W60 | 4 | 635,376 | 633,405 | 1,971 | 0 | 0 |
| F582 | bit4 | 35 | W60 | 6 | 906,192 | 906,192 | 0 | 0 | 0 |
| F583 | bit4 | 35 | W59,W60 | 4 | 635,376 | 635,359 | 17 | 0 | 0 |

Both new floors are locally closed in the same small neighborhoods that closed
the older panel floors. F582/F583 additionally close the later F580 bit4 HW35
record.

## F577/F583 continuation

After the first checkpoint, ran a focused continuation from the F576 manifests:

- bit1 ranks 6..8
- bit4 ranks 4..5

| Run | Cand | Manifest rank | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---:|---|
| F577 | bit1 | 6 | 42 | 36 | 85.471 | `0x7f74bd45 0x65649ab9 0xb0e869e9 0x41e72f68` |
| F578 | bit1 | 7 | 42 | 40 | 78.333 | `0x7f74bd45 0x65649ab9 0xb0e869c9 0xae49bf68` |
| F579 | bit1 | 8 | 43 | 41 | 80.923 | `0x7f74bd45 0x65649ab9 0x30e869f1 0xe735a7b8` |
| F580 | bit4 | 4 | 38 | 35 | 86.364 | `0x726ca5c7 0x6db409f8 0x12f335f5 0xdfec32d3` |
| F581 | bit4 | 5 | 38 | 38 | 81.857 | `0x726ca5c7 0x6db409f8 0x12f135f5 0x5ccb3615` |

F580 upgrades bit4 from HW36 to HW35, tying bit13 and bit1 as co-best Path C
cands. It is cert-pin verified and locally closed by F582/F583.

## Refreshed manifests

F576 regenerated post-breakthrough manifests from the F563/F571 chain:

- `search_artifacts/20260502_F576_bit1_post_hw35_basin_manifest.json`
  with 94 seeds.
- `search_artifacts/20260502_F576_bit4_post_hw36_basin_manifest.json`
  with 146 seeds.

F584 refreshed those manifests again after F577/F583:

- `search_artifacts/20260502_F584_bit1_post_hw35_basin_manifest.json`
  with 171 seeds.
- `search_artifacts/20260502_F584_bit4_post_hw35_basin_manifest.json`
  with 179 seeds.

Top bit1 seeds:

| Rank | HW | Score | W57..W60 |
|---:|---:|---:|---|
| 1 | 35 | 86.364 | `0x7f74bd45 0x65649ab9 0xb0e869c5 0x9ea93f2b` |
| 2 | 40 | 78.333 | `0x7f74bd45 0x65649ab9 0xb0e869c9 0xae49bf68` |
| 3 | 41 | 80.923 | `0x7f74bd45 0x65649ab9 0xb0e869c9 0xcea33b2b` |
| 4 | 41 | 75.667 | `0x7f74bd45 0x65649ab9 0xb0e869c1 0xcf21bf68` |
| 5 | 42 | 80.000 | `0x7f74bd45 0x65649ab9 0xb0e869c5 0x1f23bb2b` |

Top bit4 seeds:

| Rank | HW | Score | W57..W60 |
|---:|---:|---:|---|
| 1 | 35 | 86.364 | `0x726ca5c7 0x6db409f8 0x12f335f5 0xdfec32d3` |
| 2 | 36 | 85.471 | `0x726ca5c7 0x6db409f8 0x12f025f7 0x778d3357` |
| 3 | 36 | 85.471 | `0x726ca5c7 0x6db409f8 0x12f135f1 0x05493417` |
| 4 | 37 | 84.571 | `0x726ca5c7 0x6db409f8 0x12f025f7 0xf6ed309b` |
| 5 | 37 | 84.571 | `0x726ca5c7 0x6db409f8 0x12f135f5 0x4f27b01b` |

## Updated panel

| Cand | Prior floor | New floor | Status |
|---|---:|---:|---|
| bit13 | 35 | 35 | unchanged best |
| bit1 | 45 | 35 | new co-best |
| bit3 | 36 | 36 | unchanged |
| bit4 | 43 | 35 | new co-best |
| bit2 | 39 | 39 | unchanged |
| bit24 | 40 | 40 | unchanged |
| bit28 | 42 | 42 | unchanged |

F525's panel expansion paid off immediately: bit1 and bit4 are not merely
extra corpus rows; they are deep Path C cands.

## Next

1. Continue bit1 F584 ranks 9..16 and bit4 F584 ranks 6..12.
2. Apply the same F563/F571 workflow to F525 bit20 and bit18 next, since
   they are the next strongest new cands after bit4/bit1.
