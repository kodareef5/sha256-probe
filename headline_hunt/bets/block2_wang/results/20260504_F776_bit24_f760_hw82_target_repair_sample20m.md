---
date: 2026-05-04
bet: block2_wang
status: BIT24_F760_HW82_TARGET_REPAIR_SAMPLE20M_NEGATIVE
parent: F767 top-80 pair-potential atlas
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F776: bit24 F760 HW82 broad target/repair 20M sample

## Setup

F776 is the broad target+repair counterpart to F768. It starts from the original
F760 HW82 point, uses the F767 top-80 atlas, and enables target pairs instead
of disabling them.

```text
candidate: bit24_mdc27e18c
init HW: 82
init lane HW: [9, 10, 11, 10, 10, 13, 13, 6]
target lane: bit13 HW82 lane [10, 11, 9, 12, 9, 7, 10, 14]
init target L1: 24
init c/g objective: 130
```

Selection:

```text
target pairs = 80
repair pairs = 80
HW pairs = 20
c/g pairs = 40
per-register repair pairs = 10
selected pairs = 236
pair_count = 5
radius = 8..10
sampled combos = 20,000,000
rng seed = 776
```

## Result

```text
candidate combos: 20,000,000
evaluated: 19,965,138
skipped duplicate: 34,356
HW < 82: 0
HW <= 82: 0
c/g-improving: 40
target-L1-improving: 10,546
wall seconds: 2874.33
```

Best raw-HW sample:

```text
HW 85
target L1 19
c/g objective 133
lane [13, 9, 12, 10, 12, 6, 12, 11]
bits [75, 79, 124, 142, 178, 207, 367, 396, 496]
```

Best target-L1 sample:

```text
HW 92
target L1 10
c/g objective 134
lane [10, 11, 10, 13, 11, 12, 11, 14]
```

Best c/g sample:

```text
HW 87
c/g objective 113, delta -17
target L1 23
lane [10, 14, 8, 16, 11, 12, 5, 11]
```

## Interpretation

F776 is negative on the HW82 floor. Broadening the selected pool from the exact
F763-style set did not reproduce an HW82 tie:

```text
F763 exact, 76 selected pairs: one HW82 tie in 18.47M final states
F776 sampled, 236 selected pairs: zero HW82 ties in 19.97M final states
```

This supports the read that F763's exact selected set was unusually well
conditioned. Simply adding more target and repair pairs dilutes the useful
repair composition rather than making floor ties more common.

F776 still finds plenty of geometry: 10,546 target-improving states and a
strong c/g detour at HW87/objective 113. But those are detours, not floor
preserving moves. The next useful operator should be more structured than
random five-pair sampling from a larger pool.

## Next

Stop direct broad five-pair sampling around F760/F763 unless a new selection
rule is added. A better direction is a two-stage atlas beam that expands only
target-improving moves and then adds repair moves with explicit damage-balance
constraints.
