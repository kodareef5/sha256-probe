---
date: 2026-05-03
bet: block2_wang
status: PATHC_BIT24_ABSORBER_CG_HW85
parent: F547 path-C absorber expansion
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F746: bit24 path-C HW86 drops to HW85 under c/g

## Setup

Mac's F547 expanded absorber testing beyond the bit13/F518 panel. The bit24
path-C candidate reached HW86 from a cold M2 start:

```text
candidate: bit24_mdc27e18c
source: F547_pathC_rank1
pure-HW result: 127 -> 86
lane HW: [11, 12, 12, 13, 8, 10, 11, 9]
```

F746 restarts from that HW86 witness with the same c/g objective that found
the bit13 F732 HW82 descent.

```text
objective = total_hw + 2 * (c + g)
pair_rank = cg
rounds = 24
pair_pool = 1024
beam_width = 1024
max_pairs = 6
max_radius = 12
```

## Result

F746 found one sub-HW86 record:

| Run | Candidate | Init HW | Best HW | New records | Depth | Wall seconds |
|---|---|---:|---:|---:|---:|---:|
| F746 | bit24_mdc27e18c | 86 | 85 | 1 | 5 | 677.49 |

Best-HW witness:

```text
HW = 85
objective = 131
lane HW = [9, 10, 10, 13, 13, 12, 13, 5]
bits = [12, 66, 78, 97, 108, 305, 328, 343, 434, 463]
```

M2:

```text
0x00001000 0x00100000 0x00004004 0x00001002
0x00000000 0x00001000 0x00008000 0x00200000
0x00002000 0x20020040 0x01808108 0x00000000
0x00000000 0x00050000 0x02008000 0x00000000
```

The best c/g-objective state was not the best-HW state:

```text
objective = 122
HW = 88
depth = 1
lane HW = [11, 7, 6, 14, 13, 11, 11, 15]
bits = [91, 299]
```

## Verdict

The c/g restart trick is not bit13-specific. It also opens a descent in the
new path-C bit24 absorber basin:

```text
bit24 path-C absorber best: HW86 -> HW85
```

This does not beat the global bit13 HW82 floor, but it strengthens the
cross-candidate picture. The HW82-HW86 absorber family appears reusable across
candidate residuals, and c/g pressure can still expose local descents inside
fresh non-bit13 basins.

## Next

Run the same small c/g restart on the F547 bit3 HW86 witness. If bit3 also
drops, prioritize cross-candidate operator design over further HW82-local
closure.
