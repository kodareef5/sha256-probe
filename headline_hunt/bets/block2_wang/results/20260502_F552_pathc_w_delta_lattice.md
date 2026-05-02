---
date: 2026-05-02
bet: block2_wang
status: PATH_C_W_DELTA_LATTICE
parent: F521/F542 post-floor rank sweep
evidence_level: ANALYSIS
author: yale-codex
---

# F552: Path C W Delta Lattice

## Interpretation

This is a cross-run comparison of the actual init-to-record XOR deltas from
the current Path C headline and side-basin pair-beam artifacts.

The useful signal is bit-position recurrence, not full-mask recurrence:

- W57 and W58 remain untouched in all 10 compared records.
- Every real descent changes W60; most also change W59 by only one or two
  bits.
- No complete W60 delta mask repeats across records, so these are not
  reusable templates.
- Several W60 bit positions recur across 3-4 candidate families and are
  useful as sampler priors: b30, b27, b29, b31, b16, b19, b21, b3.
- W59:b21 is the only repeated W59 bit in this slice, shared by bit3 and
  bit24 side basins.

Practical takeaway: future operators should bias toward recurrent W60 bit
positions while still composing candidate-specific masks. Hard-clamping an
entire observed W60 mask would likely overfit.

Artifacts: 10
Records: 10

## Record Deltas

| Artifact | Section | Candidate | HW | Bits | Changed words | Delta masks |
|---|---|---|---:|---:|---|---|
| `20260501_F487_bit13_manifest_rank12_hw41_pair_beam_cg.json` | best_seen | `bit13_m916a56aa` | 41->35 | 12 | 59,60 | `0x00000000 0x00000000 0x00400000 0xe84ba008` |
| `20260502_F521_bit3_rank4_pair_beam_cg.json` | best_seen | `bit3_m33ec77ca` | 42->36 | 9 | 60 | `0x00000000 0x00000000 0x00000000 0x72810038` |
| `20260502_F534_bit3_post_rank10_pair_beam_cg.json` | best_seen | `bit3_m33ec77ca` | 40->36 | 9 | 60 | `0x00000000 0x00000000 0x00000000 0xc381c020` |
| `20260502_F530_bit3_post_rank6_pair_beam_cg.json` | best_seen | `bit3_m33ec77ca` | 39->38 | 6 | 59,60 | `0x00000000 0x00000000 0x00200000 0x0120c800` |
| `20260502_F532_bit3_post_rank8_pair_beam_cg.json` | best_seen | `bit3_m33ec77ca` | 40->38 | 12 | 60 | `0x00000000 0x00000000 0x00000000 0x5220196e` |
| `20260502_F520_bit2_pair_beam_cg.json` | best_seen | `bit2_ma896ee41` | 51->39 | 12 | 59,60 | `0x00000000 0x00000000 0x00006000 0x482821b4` |
| `20260502_F521_bit24_rank3_pair_beam_cg.json` | best_seen | `bit24_mdc27e18c` | 44->40 | 9 | 59,60 | `0x00000000 0x00000000 0x10000008 0x44090a01` |
| `20260502_F537_bit24_post_rank6_pair_beam_cg.json` | best_seen | `bit24_mdc27e18c` | 44->41 | 9 | 60 | `0x00000000 0x00000000 0x00000000 0xbe601000` |
| `20260501_F459_bit28_hw44_pair_beam_cg_followup.json` | best_seen | `bit28_md1acca79` | 44->42 | 9 | 59,60 | `0x00000000 0x00000000 0x00000020 0xa9001046` |
| `20260502_F529_bit24_post_rank5_pair_beam_cg.json` | best_seen | `bit24_mdc27e18c` | 44->42 | 7 | 59,60 | `0x00000000 0x00000000 0x00200000 0x10086009` |

## Shared Bit Positions

| Bit | Count | Candidates |
|---|---:|---|
| `W59:b21` | 2 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b1` | 2 | bit28_md1acca79, bit3_m33ec77ca |
| `W60:b11` | 3 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b12` | 3 | bit24_mdc27e18c, bit28_md1acca79, bit3_m33ec77ca |
| `W60:b13` | 3 | bit13_m916a56aa, bit24_mdc27e18c, bit2_ma896ee41 |
| `W60:b14` | 3 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b15` | 3 | bit13_m916a56aa, bit3_m33ec77ca |
| `W60:b16` | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b19` | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit2_ma896ee41 |
| `W60:b2` | 3 | bit28_md1acca79, bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b21` | 4 | bit24_mdc27e18c, bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b22` | 2 | bit13_m916a56aa, bit24_mdc27e18c |
| `W60:b24` | 3 | bit28_md1acca79, bit3_m33ec77ca |
| `W60:b25` | 4 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b27` | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit28_md1acca79, bit2_ma896ee41 |
| `W60:b28` | 4 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b29` | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit28_md1acca79, bit3_m33ec77ca |
| `W60:b3` | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b30` | 6 | bit13_m916a56aa, bit24_mdc27e18c, bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b31` | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit28_md1acca79, bit3_m33ec77ca |
| `W60:b4` | 2 | bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b5` | 4 | bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b6` | 2 | bit28_md1acca79, bit3_m33ec77ca |
| `W60:b8` | 2 | bit2_ma896ee41, bit3_m33ec77ca |

## Top Bit Positions

| Bit | Count | Candidate count | Candidates |
|---|---:|---:|---|
| `W60:b30` | 6 | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b3` | 4 | 3 | bit13_m916a56aa, bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b16` | 4 | 3 | bit13_m916a56aa, bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b19` | 4 | 3 | bit13_m916a56aa, bit24_mdc27e18c, bit2_ma896ee41 |
| `W60:b27` | 4 | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit28_md1acca79, bit2_ma896ee41 |
| `W60:b29` | 4 | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit28_md1acca79, bit3_m33ec77ca |
| `W60:b31` | 4 | 4 | bit13_m916a56aa, bit24_mdc27e18c, bit28_md1acca79, bit3_m33ec77ca |
| `W60:b5` | 4 | 2 | bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b25` | 4 | 2 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b28` | 4 | 2 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b21` | 4 | 3 | bit24_mdc27e18c, bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b13` | 3 | 3 | bit13_m916a56aa, bit24_mdc27e18c, bit2_ma896ee41 |
| `W60:b15` | 3 | 2 | bit13_m916a56aa, bit3_m33ec77ca |
| `W60:b14` | 3 | 2 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b24` | 3 | 2 | bit28_md1acca79, bit3_m33ec77ca |
| `W60:b11` | 3 | 2 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b2` | 3 | 3 | bit28_md1acca79, bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b12` | 3 | 3 | bit24_mdc27e18c, bit28_md1acca79, bit3_m33ec77ca |
| `W60:b22` | 2 | 2 | bit13_m916a56aa, bit24_mdc27e18c |
| `W60:b4` | 2 | 2 | bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b23` | 2 | 1 | bit3_m33ec77ca |
| `W59:b21` | 2 | 2 | bit24_mdc27e18c, bit3_m33ec77ca |
| `W60:b1` | 2 | 2 | bit28_md1acca79, bit3_m33ec77ca |
| `W60:b6` | 2 | 2 | bit28_md1acca79, bit3_m33ec77ca |
| `W60:b8` | 2 | 2 | bit2_ma896ee41, bit3_m33ec77ca |
| `W60:b0` | 2 | 1 | bit24_mdc27e18c |
| `W60:b26` | 2 | 1 | bit24_mdc27e18c |
| `W59:b22` | 1 | 1 | bit13_m916a56aa |
| `W60:b17` | 1 | 1 | bit13_m916a56aa |
| `W59:b13` | 1 | 1 | bit2_ma896ee41 |
| `W59:b14` | 1 | 1 | bit2_ma896ee41 |
| `W60:b7` | 1 | 1 | bit2_ma896ee41 |

## Top Word Delta Masks

| Word | Mask | Count |
|---:|---|---:|
| W59 | `0x00200000` | 2 |
| W59 | `0x00400000` | 1 |
| W60 | `0xe84ba008` | 1 |
| W60 | `0x72810038` | 1 |
| W60 | `0xc381c020` | 1 |
| W60 | `0x0120c800` | 1 |
| W60 | `0x5220196e` | 1 |
| W59 | `0x00006000` | 1 |
| W60 | `0x482821b4` | 1 |
| W59 | `0x10000008` | 1 |
| W60 | `0x44090a01` | 1 |
| W60 | `0xbe601000` | 1 |
| W59 | `0x00000020` | 1 |
| W60 | `0xa9001046` | 1 |
| W60 | `0x10086009` | 1 |
