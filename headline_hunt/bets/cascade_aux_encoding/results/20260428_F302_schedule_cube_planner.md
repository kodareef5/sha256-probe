---
date: 2026-04-28
bet: cascade_aux_encoding
status: CUBE_HARNESS_SHIPPED
---

# F302: schedule-aware cube planner for cascade_aux

## Purpose

F257 says the heuristic absorber landscape is largely saturated and points
future work toward non-heuristic attacks. F209/F213 identify the active
schedule space as the right primitive for cascade_aux. F302 ships a small
Python cube-and-conquer harness around that primitive.

This is intentionally not a new C/C++ branch. It is a reproducible way to split
existing cascade_aux CNFs along W1/W2 schedule bits or joint dW bits and feed
those cubes to CaDiCaL/Kissat.

## New tools

```
headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py
headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py
```

`schedule_cube_planner.py` uses the documented cascade_aux allocation:

```
var 1: TRUE
sr60 W1_57..W1_60: vars 2..129
sr60 W2_57..W2_60: vars 130..257
```

It can generate:

- unit cubes on `w1` bits
- unit cubes on `w2` bits
- joint differential cubes on `dw`, encoded as two binary XOR clauses for
  `W2[r][b] XOR W1[r][b] = value`

It always writes a JSONL manifest and can optionally materialize augmented CNFs
with the DIMACS clause count repaired.

`run_schedule_cubes.py` reads that JSONL, materializes cube CNFs as needed,
runs `cadical` or `kissat`, and records one JSON result per cube.

## Pilot

Base CNF:

```
headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf
```

Planner command:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf \
  --target dw --round 60 --bits 0-31 --depth 1 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F302_dw60_depth1_cube_manifest.jsonl
```

This produced 64 single-bit cubes. Example for `dW[60][0] = 0`:

```json
{"clauses": [[98, -226], [-98, 226]], "cube_id": "dwr60b00v0"}
```

That matches `W1_60[0] = var 98`, `W2_60[0] = var 226`, and encodes
`W2_60[0] XOR W1_60[0] = 0`.

## Solver smoke

Full 64-cube CaDiCaL smoke:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F302_dw60_depth1_cube_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F302_dw60_depth1_cadical_1k.jsonl \
  --solver cadical --conflicts 1000
```

Result:

```
64 cubes
64 UNKNOWN at 1k conflicts
mean wall:   0.126593s
median wall: 0.105868s
min/max:     0.091362s / 0.252422s
```

The slowest 1k-conflict cubes were mostly high-bit `dW[60]=0` cases:

| Cube | Wall seconds |
|---|---:|
| `dwr60b26v0` | 0.252422 |
| `dwr60b24v0` | 0.235182 |
| `dwr60b28v0` | 0.208031 |
| `dwr60b22v0` | 0.200287 |
| `dwr60b27v0` | 0.198629 |

Follow-up on bits 22..29 at 10k conflicts:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F302_dw60_bits22_29_depth1_cube_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F302_dw60_bits22_29_cadical_10k.jsonl \
  --solver cadical --conflicts 10000
```

Result:

```
16 cubes
16 UNKNOWN at 10k conflicts
mean wall:   0.450396s
median wall: 0.462801s
min/max:     0.324303s / 0.545213s
```

## Interpretation

F302 is primarily an infrastructure commit. The bounded runs do not solve or
refute any cube; they verify that schedule-aware cubes are generated correctly,
are solver-acceptable, and are cheap enough for a modest hardware budget.

The useful distinction from the old shell cube script is semantic targeting:
instead of blindly cubing on vars `2..k`, the planner can split directly on
`W1`, `W2`, or joint `dW` schedule coordinates. That matches the F209/F213
claim that the active schedule space is the algorithmic primitive.

## Next moves

1. Run depth-2 `dw` cubes on a small high-value bit band, e.g. bits 22..29
   at 50k conflicts, and rank by UNSAT/UNKNOWN skew plus wall time.
2. Compare `dw` cubing vs raw `w2` cubing on the same bit band.
3. Feed the hardest/skewed cube family into a deeper CaDiCaL/Kissat run, then
   test whether cube choice predicts hard-core structure from F213.
