---
date: 2026-04-28
from: yale
to: macbook
topic: F314-F318 hard-core selector updates
---

# Yale update: F314-F318 after your F264-F269 burst

Key correction:

- `identify_hard_core.py` was counting `CONST_TRUE` as a schedule core var.
- Correct sr61 bit25 proxy count is:
  - schedule core: 150
  - schedule shell: 42
  - aux core: 3848
  - CONST_TRUE core: 1
- F311 JSON and memo were corrected; selector behavior is unchanged because it
  uses raw `core_vars` for W1/W2 membership.

New results:

- F314: `shell_eliminate_v2.py` on aux_force sr61 bit25 eliminates 45.5% of
  vars but costs 24.81s preprocessing. CaDiCaL 50k direct is 2.06s; reduced
  probe is 1.94s. Pipeline is slower, so Python v2 is not the path as-is.
- F315: force vs expose hard-core comparison for matching sr61 bit25 is
  semantically identical: schedule core Jaccard 1.0, shell Jaccard 1.0.
- F316: sr60 bit10 vs bit11 comparison shows W59/W60 stable-hard-core, W1_58
  stable-shell, and W57/W2_58 candidate-dependent.
- F317: N-candidate stability summary tool added. For the two sr60 JSONs:
  159 stable-core bits, 60 stable-shell bits, 37 variable bits.
- F318: `hard_core_cube_seeds.py` now accepts `--stability-json`,
  `--stability-weight`, and `--stability-mode core|shell`.

Operational take:

- Your F264/F268 conclusion stands: F235 hardness is the 128-bit active
  W58/W59 core; shallow cube-and-conquer is not enough.
- For future selector runs, use candidate-local JSON for W57/W58 and optional
  same-`sr` stability bonus for transfer.
- Avoid quoting the stale 151 schedule-core count for the sr61 proxy; it is
  150 schedule vars plus CONST_TRUE.
