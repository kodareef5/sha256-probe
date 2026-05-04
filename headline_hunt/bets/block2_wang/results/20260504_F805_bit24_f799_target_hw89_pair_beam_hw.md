---
date: 2026-05-04
bet: block2_wang
status: BIT24_F799_TARGET_HW89_PAIR_BEAM_REACHED_HW88
parent: F799 best-target HW89 detour
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F805: bit24 F799 target-shaped HW89 pure-HW repair

## Setup

F805 tests the F799 best-target detour directly. This detour was HW89 with
target L1 13, better target-shaped than the F799 best-HW detour but higher HW.

```text
candidate: bit24_mdc27e18c
seed JSONL: F547_pathC_absorber_seeds.jsonl
seed rank: 1
init HW: 89
init lane: [12, 12, 9, 15, 10, 8, 12, 11]
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
pair-pool HW range: 94..109
depth bests: 94, 91, 90, 91, 90, 88
new records below HW89: 1
best seen HW: 88, source final_beam
wall seconds: 685.41
```

Best HW88 witness:

```text
lane [10, 6, 12, 17, 13, 12, 10, 8]
depth 6
bits [33, 37, 161, 186, 247, 289, 309, 351, 409, 420, 458, 478]
```

Best HW88 M2:

```text
0x00001000,0x00100022,0x00004004,0xc1105202,
0x00010001,0x34001012,0x00000000,0x00a00040,
0x08082000,0x20220042,0x81808108,0x00000400,
0x02100000,0x10050010,0x52018402,0x00000040
```

## Interpretation

F805 found a shallow repair from HW89 to HW88, but it did not produce a
competitive branch. This is weaker than the F799 best-HW -> F800 -> F802 path,
which reached HW85.

Do not spend another pure-HW continuation on this HW88 unless a separate lane
or source comparison identifies it as structurally special.

## Artifact

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F805_bit24_f799_target_hw89_pair_beam_hw.json
```

## Next

Continue the stronger F802 HW85 lane-bridge path. F806 tests target weight 1
toward the F789 HW78 lane.
