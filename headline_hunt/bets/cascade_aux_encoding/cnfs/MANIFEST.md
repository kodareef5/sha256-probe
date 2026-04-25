# Cross-kernel cascade_aux CNF set

Generated 2026-04-25 (macbook). 36 CNFs total: 9 kernel families × 2 sr-levels × 2 modes.

## Coverage

| kernel-bit | m0 | fill | family |
|---|---|---|---|
| 0  | 0x8299b36f | 0x80000000 | LSB |
| 6  | 0x024723f3 | 0x7fffffff | low-mid |
| 10 | 0x3304caa0 | 0x80000000 | sigma1-aligned |
| 11 | 0x45b0a5f6 | 0x00000000 | sigma1-aligned |
| 13 | 0x4d9f691c | 0x55555555 | mid |
| 17 | 0x427c281d | 0x80000000 | mid |
| 19 | 0x51ca0b34 | 0x55555555 | mid |
| 25 | 0x09990bd2 | 0x80000000 | high |
| 31 | 0x17149975 | 0xffffffff | MSB (priority) |

Each candidate is the first true sr=61 CNF representative from `cnfs_n32/` for that kernel-bit family.

## CNFs

### sr=60 expose mode (9 files)

`aux_expose_sr60_n32_bit{B}_m{M}_fill{F}.cnf` — aux variables + tying clauses on top of standard sr=60 cascade encoding. Solution set unchanged from standard.

### sr=60 force mode (9 files)

`aux_force_sr60_n32_bit{B}_m{M}_fill{F}.cnf` — adds Theorem 1-4 hard constraints (cascade diagonal, dE[60]=0, dA[61]=dE[61], three-filter dE[61..63]=0). Restricts solution set to cascade-DP solutions.

### sr=61 expose mode (9 files)

Same as sr=60 expose but at sr=61 (3 free rounds 57-59).

### sr=61 force mode (9 files)

Same as sr=60 force but at sr=61.

## Audit status

All 36 CNFs audit-CONFIRMED via `infra/audit_cnf.py` against fingerprint buckets (vars, clauses ranges expanded after observation):

```
sr60_n32_cascade_aux_expose: vars [12540, 12620], clauses [52454, 52783]
sr60_n32_cascade_aux_force:  vars [12540, 12620], clauses [52454, 52783]
sr61_n32_cascade_aux_expose: vars [12816, 12888], clauses [53698, 53999]
sr61_n32_cascade_aux_force:  vars [12816, 12888], clauses [53698, 53999]
```

All ranges verified across the 9 kernel families.

## Why

The cascade_aux_encoding bet's prior comparison studies used only the priority MSB candidate. With this cross-kernel set, fleet workers can:
- Run treewidth measurement (FlowCutter) on each variant to test SPEC's prediction of treewidth-drop in force mode.
- Run Kissat/CaDiCaL with multiple seeds to test the ≥10x SAT speedup claim across kernels (currently empirically refuted at 90-min budget on MSB only).
- Compare solver behavior between sr=60 and sr=61 across kernels to isolate kernel-specific effects.

Total disk: ~36 MB. Light artifact.

## Next: who picks up

Any worker with spare CPU-h. Run `python3 headline_hunt/infra/append_run.py --bet cascade_aux_encoding --candidate <id> --cnf <path> --solver kissat --seed <n>` for each comparison run. Append-only run log per CLAUDE.md discipline.
