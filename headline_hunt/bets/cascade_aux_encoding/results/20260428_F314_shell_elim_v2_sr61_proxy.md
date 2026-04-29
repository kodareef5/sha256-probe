---
date: 2026-04-28
bet: cascade_aux_encoding
status: SHELL_ELIM_V2_SR61_PROXY_SLOW
---

# F314: shell_eliminate_v2 on sr61 bit25 proxy

## Purpose

F312 showed shell schedule unit cubes do not split the sr61 bit25 proxy. F314
tests the stronger version of the shell idea: run the sound shell-elimination
preprocessor and compare equal 50k-conflict CaDiCaL probes on the original and
reduced CNFs.

## Commands

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/shell_eliminate_v2.py \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  /tmp/F314_auxforce_sr61_bit25_shell_elim_v2_max0.cnf \
  --max-growth 0
```

Then:

```bash
cadical --stats -c 50000 \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf

cadical --stats -c 50000 \
  /tmp/F314_auxforce_sr61_bit25_shell_elim_v2_max0.cnf
```

## Preprocessing Result

| Field | Original | v2 reduced |
|---|---:|---:|
| Vars | 13494 | 7358 |
| Clauses | 56002 | 41102 |
| Vars eliminated by v2 | 0 | 6136 |
| Elimination pct | 0.0% | 45.5% |
| v2 preprocessing wall | 0.0s | 24.81s |

## CaDiCaL 50k Result

Both probes returned `UNKNOWN`.

| CNF | Conflicts | Decisions | Propagations | CaDiCaL process s | RSS MB |
|---|---:|---:|---:|---:|---:|
| Original | 50001 | 383880 | 8701017 | 2.06 | 26.44 |
| v2 reduced | 50000 | 322467 | 8343545 | 1.94 | 19.85 |

CaDiCaL internal preprocessing after start:

| CNF | Eliminated | Fixed | Substituted |
|---|---:|---:|---:|
| Original | 5490 | 1264 | 2005 |
| v2 reduced | 1188 | 33 | 1218 |

## Interpretation

The reduced CNF is somewhat easier per 50k-conflict probe:

- decisions drop by about 16%;
- propagations drop by about 4%;
- CaDiCaL process time drops by about 6%;
- memory drops by about 25%.

But the full pipeline is much worse:

```
direct CaDiCaL probe:      2.06s
v2 preprocess + probe:    26.75s
```

So `shell_eliminate_v2.py` is structurally valid but operationally too slow for
this path. CaDiCaL's own preprocessing already captures much of the cheap
elimination work. A useful preprocessor would need either a much faster
implementation or a reduction that changes conflict growth, not just a modest
constant-factor improvement in the first 50k conflicts.

## Next Direction

Do not spend more time on Python v2 as-is. The better next options are:

- implement affected-variable priority queues in v2 before further testing;
- use hard-core JSON only for selector/control experiments;
- move toward marginal or learned branching guidance where the solver still
sees the original formula.
