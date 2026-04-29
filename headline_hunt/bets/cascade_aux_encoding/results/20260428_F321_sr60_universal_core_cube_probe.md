---
date: 2026-04-28
bet: cascade_aux_encoding
status: SR60_UNIVERSAL_CORE_CUBE_PROBE
---

# F321: sr60 bit10 universal-core dW59 cube probe

## Purpose

Macbook F270/F271 identified a 128-bit universal sr60 hard core:
`W1_59`, `W1_60`, `W2_59`, and `W2_60` are hard-core across the three sr60
candidates tested so far. F321 turns that structural result into a runnable
Yale-side cube probe on the bit10 sr60 force candidate.

This is a transfer test: use the three-candidate sr60 stability summary plus
the existing sr61 dW59 CaDiCaL decision outliers to pick universal-core dW59
depth-2 cubes for sr60 bit10.

## Setup

Regenerated the ignored base CNF locally:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py \
  --sr 60 --m0 0x3304caa0 --fill 0x80000000 --kernel-bit 10 \
  --mode force \
  --out headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf \
  --varmap + --quiet
```

Audit confirmed it as `sr60_n32_cascade_aux_force`:

```
vars=13168 clauses=54590 VERDICT=CONFIRMED
```

Rebuilt the F271 three-candidate stability JSON from bit10, bit11, and bit13
hard-core exports:

```
stable_core:   150
stable_shell:  46
variable:      60
```

## Selector

Selector inputs:

- hard-core JSON: bit10 sr60 aux-force
- stability JSON: bit10 + bit11 + bit13 sr60 aggregate
- observed stats: F306/F307/F309 sr61 bit25 dW59 CaDiCaL decision stats
- target: `dw[59]`
- mode: `--stability-mode core`, `--stability-weight 1.0`

Top selected bits:

| Rank | Bit | Score | Preferred value | Prior mean decisions |
|---:|---:|---:|---:|---:|
| 1 | 29 | 4.000000 | 0 | 653334.846 |
| 2 | 19 | 3.975234 | 1 | 637154.500 |
| 3 | 1 | 3.926849 | 1 | 605542.500 |
| 4 | 3 | 3.917855 | 0 | 599666.417 |
| 5 | 31 | 3.905477 | 0 | 591579.500 |
| 6 | 27 | 3.849414 | 1 | 554951.500 |

The emitted manifest uses the top four bits `29,19,1,3`, producing 24 depth-2
`dW[59]` cube records.

## 50k CaDiCaL stats run

Command:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F321_sr60_bit10_dw59_universal_core_depth2_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F321_sr60_bit10_dw59_universal_core_depth2_cadical_50k_stats.jsonl \
  --solver cadical --conflicts 50000 --stats
```

All 24 cubes returned `UNKNOWN`.

| Metric | Min | Mean | Max |
|---|---:|---:|---:|
| Wall seconds | 1.455 | 1.634 | 1.826 |
| Decisions | 341028 | 379529 | 424826 |
| Propagations | 5986463 | 6363463 | 6870387 |

Top decision cubes:

| Rank | Cube | Decisions | Status |
|---:|---|---:|---|
| 1 | `dwr59b01v1__dwr59b03v0` | 424826 | UNKNOWN |
| 2 | `dwr59b29v1__dwr59b03v0` | 424815 | UNKNOWN |
| 3 | `dwr59b29v1__dwr59b01v0` | 423965 | UNKNOWN |
| 4 | `dwr59b29v0__dwr59b03v0` | 408203 | UNKNOWN |
| 5 | `dwr59b19v1__dwr59b01v1` | 388740 | UNKNOWN |
| 6 | `dwr59b19v1__dwr59b03v1` | 388523 | UNKNOWN |

Top assignment aggregates by decisions:

| Assignment | Count | Mean decisions | Min | Max |
|---|---:|---:|---:|---:|
| `dw[59].b3=0` | 6 | 394287.333 | 364358 | 424826 |
| `dw[59].b29=1` | 6 | 384107.667 | 341028 | 424815 |
| `dw[59].b1=1` | 6 | 381175.833 | 357587 | 424826 |
| `dw[59].b1=0` | 6 | 378942.333 | 360979 | 423965 |
| `dw[59].b29=0` | 6 | 377886.000 | 360076 | 408203 |
| `dw[59].b19=1` | 6 | 374753.000 | 360076 | 388740 |
| `dw[59].b19=0` | 6 | 373976.333 | 360979 | 383800 |
| `dw[59].b3=1` | 6 | 371105.167 | 341028 | 388523 |

## Interpretation

The universal-core selector transfer is coherent but not a breakthrough at
50k: every cube remains UNKNOWN, and the decision spread is only about 1.25x
from weakest to strongest cube.

Two concrete signals are worth carrying forward:

- `dw[59].b3=0` is the strongest repeated assignment under both decisions and
  propagations.
- The top two-cube continuation target is `dwr59b01v1__dwr59b03v0`; the near-tie
  `dwr59b29v1__dwr59b03v0` independently reinforces `b3=0`.

Next useful continuation is a small 200k or 1M CaDiCaL run on the top 3-4 F321
cubes, plus a matched shell-side control on universal-shell `W1_58` to quantify
whether universal-core targeting is actually better than shell elimination for
this sr60 candidate.
