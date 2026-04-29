---
date: 2026-04-28
bet: cascade_aux_encoding
status: CUBE_STATS_RANKER_ADDED
---

# F310: cube stats ranker for sr61 bit25 proxy

## Purpose

F306-F309 showed a consistent negative result for hand-picked shallow cubing on
the sr61 bit25 aux-force proxy. F310 adds a small aggregation tool so future cube
batches can be selected from observed CaDiCaL stats instead of by manual
inspection.

New tool:

```
headline_hunt/bets/cascade_aux_encoding/encoders/rank_cube_stats.py
```

It loads one or more `run_schedule_cubes.py --stats` JSONL outputs and ranks:

- individual cubes by a chosen metric;
- individual assignments by aggregate metric values;
- assignment pairs by aggregate metric values.

The pair ranking supports `--min-pair-count` so one-off depth-3 children do not
hide repeated signals.

## Commands

Decision-ranked summary:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/rank_cube_stats.py \
  --metric decisions --top 12 --min-pair-count 2 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F310_sr61_bit25_cube_decision_rank_summary.json \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F306_auxforce_sr61_bit25_dw59_depth1_cadical_50k_stats.jsonl \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cadical_100k_stats.jsonl \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F309_auxforce_sr61_bit25_dw59_depth3_outlier_expansion_cadical_100k_stats.jsonl
```

Propagation-ranked summary:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/rank_cube_stats.py \
  --metric propagations --top 8 --min-pair-count 2 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F310_sr61_bit25_cube_propagation_rank_summary.json \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F306_auxforce_sr61_bit25_dw59_depth1_cadical_50k_stats.jsonl \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cadical_100k_stats.jsonl \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F309_auxforce_sr61_bit25_dw59_depth3_outlier_expansion_cadical_100k_stats.jsonl
```

## Inputs

The combined ranking uses 92 rows:

- F306: depth-1 `dW[59]` stats at 50k conflicts.
- F307: targeted depth-2 `dW[59]` stats at 100k conflicts.
- F309: targeted depth-3 children under `19=1,29=0` at 100k conflicts.

All rows remained `UNKNOWN`; this is a prioritization signal, not evidence that
the cubes are close to solving.

## Result

Top repeated assignment aggregates by decisions:

| Assignment | Count | Mean decisions | Median | Max |
|---|---:|---:|---:|---:|
| `dw[59].b29=0` | 17 | 661501.529 | 652873 | 936107 |
| `dw[59].b19=1` | 13 | 659344.923 | 647116 | 936107 |
| `dw[59].b29=1` | 9 | 637908.889 | 634825 | 713126 |
| `dw[59].b3=0` | 6 | 608631.000 | 637125.5 | 713126 |

Top repeated assignment pairs by decisions:

| Pair | Count | Mean decisions | Median | Max |
|---|---:|---:|---:|---:|
| `dw[59].b19=1 & dw[59].b29=0` | 9 | 705705.667 | 654842 | 936107 |
| `dw[59].b1=0 & dw[59].b29=0` | 2 | 675339.500 | 675339.5 | 739243 |
| `dw[59].b1=1 & dw[59].b29=0` | 2 | 667535.500 | 667535.5 | 680229 |
| `dw[59].b29=0 & dw[59].b3=0` | 2 | 659821.000 | 659821 | 670601 |

Top repeated assignment aggregates by propagations:

| Assignment | Count | Mean propagations | Median | Max |
|---|---:|---:|---:|---:|
| `dw[59].b29=1` | 9 | 17298272.222 | 18025093 | 19213056 |
| `dw[59].b29=0` | 17 | 17225080.647 | 17821093 | 19395538 |
| `dw[59].b19=1` | 13 | 16968313.231 | 17651560 | 19395538 |
| `dw[59].b3=0` | 6 | 16581632.833 | 17811648 | 19213056 |

Top repeated assignment pairs by propagations:

| Pair | Count | Mean propagations | Median | Max |
|---|---:|---:|---:|---:|
| `dw[59].b29=0 & dw[59].b3=0` | 2 | 18384103.500 | 18384103.5 | 18619844 |
| `dw[59].b29=0 & dw[59].b3=1` | 2 | 18177339.500 | 18177339.5 | 18533586 |
| `dw[59].b1=1 & dw[59].b29=0` | 2 | 17977268.000 | 17977268 | 18207287 |
| `dw[59].b19=1 & dw[59].b29=0` | 9 | 17724848.000 | 17747249 | 19395538 |

The strongest repeated decision signal is still:

```
dW[59] bits 19=1, 29=0
```

The strongest single observed propagation cube is still the F309 depth-3 child:

```
dW[59] bits 19=1, 29=0, 27=1
```

## Interpretation

Bit 29 is the central local discriminator in this proxy corpus. The specific
pair `19=1,29=0` is the best repeated decision-heavy branch, and it remains
visible after filtering out single-observation pairs.

This does not rescue shallow cube-and-conquer. The useful outcome is tooling:
future pilots should generate broader candidate batches, rank them mechanically,
and then spend larger budgets only on repeated signals. The next selector should
add hard-core variable scores or BP/BDD marginal information before launching
more depth-3 or depth-4 cube runs.
