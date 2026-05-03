---
date: 2026-05-03
bet: block2_wang
status: BIT24_F760_HW82_PAIR_POTENTIAL_TOP80_REFRESH
parent: F761 pair-potential atlas
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F767: bit24 F760 HW82 pair-potential top-80 refresh

## Setup

F767 refreshes the original F760 bit24 HW82 pair-potential atlas with `top=80`
so it can feed the same broad sampled repair/cg machinery used by F765.

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [9, 10, 11, 10, 10, 13, 13, 6]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 24
init c/g objective: 130
top per bucket: 80
```

## Result

```text
total two-bit M2 pairs: 130,816
HW < 82 pairs: 0
HW <= 82 pairs: 0
c/g-improving pairs: 0
target-L1-improving pairs: 54
wall seconds: 17.29
```

This matches the F761 closure counts, but preserves a wider top-80 menu for
the next sampled combo.

## Interpretation

The F760 HW82 point remains locally closed for HW and c/g, but it is looser
than the F763 HW82 tie in target-lane geometry:

```text
F760/F767 target-improving one-pair moves: 54
F763/F764 target-improving one-pair moves: 5
```

That makes F760 the better parent for one more broad repair/cg sampled pass.
