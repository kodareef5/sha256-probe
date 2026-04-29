---
date: 2026-04-28
bet: cascade_aux_encoding
status: SR61_HARDCORE_SELECTOR_ADDED
---

# F311: hard-core JSON and cube seed selector for sr61 bit25 proxy

## Purpose

F310 made the cube stats rankable. F311 adds the structural side: export the
hard-core decomposition as JSON and combine it with observed cube stats to rank
future schedule-bit seeds.

Updated tool:

```
headline_hunt/bets/cascade_aux_encoding/encoders/identify_hard_core.py
```

New tool:

```
headline_hunt/bets/cascade_aux_encoding/encoders/hard_core_cube_seeds.py
```

The selector ranks W1/W2/dW bits by:

- whether the corresponding schedule variable is in the hard core;
- optional observed CaDiCaL stats from `run_schedule_cubes.py --stats`;
- preferred branch value from the observed metric.

## Commands

Hard-core export:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/identify_hard_core.py \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --n-free 3 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F311_auxforce_sr61_bit25_hard_core.json
```

Decision seed ranking:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/hard_core_cube_seeds.py \
  --hard-core-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F311_auxforce_sr61_bit25_hard_core.json \
  --target dw --round 59 --metric decisions \
  --stats-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F306_auxforce_sr61_bit25_dw59_depth1_cadical_50k_stats.jsonl \
  --stats-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cadical_100k_stats.jsonl \
  --stats-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F309_auxforce_sr61_bit25_dw59_depth3_outlier_expansion_cadical_100k_stats.jsonl \
  --top 16 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F311_auxforce_sr61_bit25_dw59_hardcore_decision_seeds.json
```

Propagation seed ranking used the same inputs with `--metric propagations`.

## Hard-Core Result

Target CNF:

```
aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf
```

Decomposition:

| Field | Count |
|---|---:|
| Vars | 13494 |
| Clauses | 56002 |
| Shell vars | 9495 |
| Core vars | 3999 |
| Schedule vars | 192 |
| Schedule vars in core | 151 |
| Schedule vars in shell | 42 |
| Aux vars in core | 3848 |

Shell schedule distribution:

| Word/round | Shell vars |
|---|---:|
| `W1_57` | 18 |
| `W1_58` | 1 |
| `W2_57` | 23 |

No W59 schedule var lands in the shell for this proxy.

## Selector Result

For `dW[59]`, all 32 bit positions are `both_core`: the W1 and W2 variables
for each dW bit are both hard-core variables. This matters because it explains
why the F306-F309 dW59 pilots did not find an easy shell lever.

Top decision-ranked `dW[59]` seeds:

| Bit | Core class | Preferred value | Mean decisions |
|---:|---|---:|---:|
| 29 | both_core | 0 | 653334.846 |
| 19 | both_core | 1 | 637154.500 |
| 1 | both_core | 1 | 605542.500 |
| 3 | both_core | 0 | 599666.417 |
| 31 | both_core | 0 | 591579.500 |
| 27 | both_core | 1 | 554951.500 |

Top propagation-ranked `dW[59]` seeds:

| Bit | Core class | Preferred value | Mean propagations |
|---:|---|---:|---:|
| 29 | both_core | 1 | 17250416.192 |
| 19 | both_core | 1 | 16682002.833 |
| 3 | both_core | 0 | 16532490.083 |
| 1 | both_core | 1 | 15827649.375 |
| 31 | both_core | 0 | 15666430.750 |
| 27 | both_core | 1 | 13729259.500 |

## Interpretation

The structural and statistical stories line up for the already-tested dW59
branch: bits `29,19,1,3,31,27` are not accidental outliers. They are all fully
inside the hard core and are consistently expensive under shallow cubes.

The negative lesson is more important: dW59 is not where the shell is. The shell
schedule variables are concentrated in W57, especially `W1_57` and `W2_57`.
The next useful experiment should compare shell schedule unit cubes against
hard-core dW59 cubes, rather than spending more budget on deeper manual dW59
children.
