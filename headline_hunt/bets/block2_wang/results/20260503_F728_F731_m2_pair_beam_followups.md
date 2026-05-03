---
date: 2026-05-03
bet: block2_wang
status: ABSORBER_M2_PARALLEL_VERIFY_AND_TOOLING
parent: F535/F536/F537/F538/F539 M2 pair beam sweep; F519 M2 polish roadmap
evidence_level: VERIFIED_JSON_ARTIFACTS
author: yale-codex
---

# F728-F731: parallel M2 pair-beam verification plus tooling hardening

## Context

Pulled Mac's `80cc0f8` push first. The F535 memo showed the M2 pair
beam generalizes across the F518 absorber panel:

- rank 0: 91 -> 86 (F534)
- rank 1: 93 -> 88
- rank 2: 94 -> 86
- rank 3: 95 -> 89
- rank 4: 96 -> 87

That made HW86 look like a possible 24-round absorber floor. This pass tested
three seed indices plus a direct restart from Mac's rank2 HW86 witness.

During the run, Mac pushed `529faab` and `e8ad9c1`:

- F536/F537 found the same rank2 HW85 witness and swept ranks 5-10.
- F538/F539 extended ranks 11-15 and checked the HW85 witness locally closed.

So this memo should be read as independent local verification plus tooling
hardening, not a separate priority claim for the HW85 floor.

## Tooling fixes shipped before rerun

`block2_m2_pair_beam.py` now supports:

- `--init-M2` / `--init-hw` for restarts from known records.
- `--objective {hw,cg,weighted}` and `--pair-rank {hw,cg,weighted}`.
- `--lane-weights` and `--cg-weight` for lane-targeted experiments.
- Correct `best_seen_hw` across initial state, final beam, and earlier-depth
  top records. This fixes the stale-summary issue in the F535 JSONs.
- Bounded record retention: count all improvements but keep only top records,
  so transfer seeds with millions of improving states do not grow memory
  unnecessarily in future runs.

New helper scripts:

- `m2_pair_beam_atlas.py`: summarizes M2 pair-beam JSONs and flags stale
  `best_seen_hw` fields.
- `m2_cross_round_pipe.py`: automates staged 16 -> 20 -> 24 continuation,
  restarting each stage from the previous stage's true best M2.

## Local verification runs

All runs used rounds=24, pair_pool=1024, beam_width=1024, max_pairs=6,
max_radius=12.

| Run | Seed index | Init HW | Best HW | Delta | Depth | Records | Lane HW | Artifact |
|---|---:|---:|---:|---:|---:|---:|---|---|
| F728 | 5 | 96 | 88 | -8 | 4 | 104 | `8,18,9,12,9,10,11,11` | `20260503_F728_seedidx5_m2_pair_beam_r24.json` |
| F729 | 10 | 101 | 89 | -12 | 2 | 1327 | `10,11,10,12,13,8,15,10` | `20260503_F729_seedidx10_m2_pair_beam_r24.json` |
| F730 | 14 | 124 | 86 | -38 | 4 | 1350122 | `12,11,15,12,9,11,5,11` | `20260503_F730_seedidx14_m2_pair_beam_r24.json` |
| F731 | rank2 HW86 restart | 86 | **85** | -1 | 4 | 1 | `11,9,10,9,8,11,13,14` | `20260503_F731_rank2_hw86_deeper_m2_pair_beam.json` |

Important caveat on F730: the JSONL seed's claimed absorber HW is 95, but
evaluating its M2 at 24 rounds gives HW124. This is likely a cross-round-style
seed, not a direct 24-round seed. The run is still valuable: it descends a bad
24-round transfer start into the HW86 basin.

## HW85 witness

F731 started from Mac's F535 rank2 HW86 M2 and reproduced the same depth-4 /
8-bit descendant reported by Mac's F536:

```text
M2 = 0x20100008 0x40000000 0x00000100 0x00100000
     0x40020000 0x10000000 0x08040000 0x00100000
     0x08400000 0x00000008 0x20000000 0x40000800
     0x04010041 0x00000200 0x00010000 0x00000008
```

Flip bits from the HW86 parent:

```text
29, 72, 145, 188, 210, 382, 390, 483
```

Lane HW:

```text
[11, 9, 10, 9, 8, 11, 13, 14] = 85
```

## Atlas observations

`m2_pair_beam_atlas.py` flags Mac's rank1/rank2 F535 JSON summaries as stale:

- rank1 true best is top_records HW88, not reported best_seen HW91.
- rank2 true best is top_records HW86, not reported best_seen HW89.

The markdown memo was correct; only the JSON summary fields were stale.

Pairwise M2 distances among the new records are useful:

- F731 HW85 is distance 8 from its F535 rank2 HW86 parent.
- F730 HW86 is distance 26-36 from the other HW86/HW88/HW89 records.
- F728/F729/F730 are distance 26-32 from each other.

So F731 is a local deepening of one HW86 witness, while F730 is another
independent route into the HW86 basin family.

## Verdict

HW86 is not the 24-round absorber floor. It is a shelf that admits at least
one composed-pair escape to HW85. Mac's F536 established that first in the
shared history; F731 independently reproduced the same witness with the
patched local tool and lane metadata.

The M2 pair beam is now the most productive active path in this bet:

- F535 established broad 5/5 descent across direct seeds.
- F536/F537/F538/F539 established HW85 and 16/16 tested seeds breaking HW91.
- F728/F729/F730 locally reproduced three of the sweep rows with richer lane
  metadata and the fixed summary fields.
- F731 reproduced the HW85 witness from the rank2 HW86 parent.

## Next

1. Run lane-targeted `cg` and weighted objectives from the HW85/HW86 witnesses.
2. Run `m2_cross_round_pipe.py` on seed indices with strong 16/20-round
   profiles, especially the F730-style transfer rows.
3. Continue remaining F518 seed indices after the record-retention fix.
4. Use `m2_pair_beam_atlas.py` to normalize Mac/Yale artifacts where old JSON
   `best_seen_hw` fields are stale.
