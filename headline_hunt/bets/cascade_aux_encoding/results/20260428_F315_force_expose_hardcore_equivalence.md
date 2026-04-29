---
date: 2026-04-28
bet: cascade_aux_encoding
status: FORCE_EXPOSE_HARDCORE_EQUIVALENT
---

# F315: force/expose hard-core equivalence on sr61 bit25 proxy

## Purpose

Mac's F264 note says it is generating hard-core JSON for the F235 candidate.
F315 adds a semantic hard-core comparator and uses it immediately on the local
sr61 bit25 force/expose pair.

This also fixed a bookkeeping bug: `identify_hard_core.py` had counted
`CONST_TRUE` as a schedule core variable. The corrected count is 150 schedule
core vars plus one `CONST_TRUE`, not 151 schedule core vars.

## Tooling

New comparator:

```
headline_hunt/bets/cascade_aux_encoding/encoders/compare_hard_core_jsons.py
```

It compares schedule vars by semantic key:

```
w1[57].b4
w2[59].b31
```

instead of raw SAT var number, so matching encoders can be compared even if aux
numbering differs.

## Commands

Force JSON was regenerated with corrected CONST handling:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/identify_hard_core.py \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --n-free 3 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F311_auxforce_sr61_bit25_hard_core.json
```

Expose JSON:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/identify_hard_core.py \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_expose_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --n-free 3 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F315_auxexpose_sr61_bit25_hard_core.json
```

Comparison:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/compare_hard_core_jsons.py \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F311_auxforce_sr61_bit25_hard_core.json \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F315_auxexpose_sr61_bit25_hard_core.json \
  --left-name force --right-name expose \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F315_force_vs_expose_hard_core_compare.json
```

## Result

Force and expose are identical at the semantic schedule hard-core level.

| Metric | Force | Expose |
|---|---:|---:|
| Vars | 13494 | 13494 |
| Clauses | 56002 | 56002 |
| Shell vars | 9495 | 9495 |
| Core vars | 3999 | 3999 |
| Schedule core vars | 150 | 150 |
| Schedule shell vars | 42 | 42 |
| Aux core vars | 3848 | 3848 |
| CONST_TRUE core vars | 1 | 1 |

Schedule core by word/round:

| Word | Core vars |
|---|---:|
| `w1[57]` | 14 |
| `w1[58]` | 31 |
| `w1[59]` | 32 |
| `w2[57]` | 9 |
| `w2[58]` | 32 |
| `w2[59]` | 32 |

Schedule shell by word/round:

| Word | Shell vars |
|---|---:|
| `w1[57]` | 18 |
| `w1[58]` | 1 |
| `w2[57]` | 23 |

Set comparison:

| Set | Jaccard | Left-only | Right-only |
|---|---:|---:|---:|
| Schedule core | 1.000000 | 0 | 0 |
| Schedule shell | 1.000000 | 0 | 0 |

## Interpretation

For this matching sr61 bit25 candidate, force/expose mode does not change the
semantic hard-core schedule structure. That means the F311/F312 selector
signals are mode-stable for this proxy.

The comparator is now ready for Mac's F264 JSON: if F235 differs, the diff will
be visible as schedule core/shell set movement rather than buried in aux var
numbering.
