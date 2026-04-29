---
date: 2026-04-28
bet: cascade_aux_encoding
status: TANNER_PAIR_CROSS_MODE_CHECK
---

# F329: high-multiplicity Tanner pair semantics persist on sr60 bit10 force

## Purpose

F328 profiled high-multiplicity Tanner pairs on a regenerated sr60 bit0
aux-expose CNF and found that the dominant pairs are p1/p2 mirrored state
aliases, not direct Σ rotation gaps. F329 checks whether that result survives a
different candidate and mode: sr60 bit10 aux-force.

## Setup

Input:

```
headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf
```

Audit:

```
vars=13168 clauses=54590 VERDICT=CONFIRMED
```

## Command

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/profile_tanner_pairs.py \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf \
  --varmap headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf.varmap.json \
  --n-free 4 --top 24 --min-mult 10 \
  --gap 128 --gap 32 --gap 1 --gap 2 --gap 3 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F329_aux_force_sr60_bit10_tanner_pair_profile.json
```

## Result

Aggregate profile:

| Field | Value |
|---|---:|
| Variables | 13168 |
| Clauses read | 54590 |
| Distinct variable pairs | 40873 |
| 4-cycles | 263904 |

Selected gap pair counts:

| Gap | 4-cycle-forming pairs |
|---:|---:|
| 1 | 4626 |
| 2 | 2674 |
| 3 | 1427 |
| 32 | 1599 |
| 128 | 178 |
| 754 | 32 |

Top semantic pairs:

| Pair | Gap | Mult | Left semantic | Right semantic |
|---|---:|---:|---|---|
| `(2,130)` | 128 | 36 | `p1 W1[57].b0` aliased as `a57/b58/c59/d60/e57/f58/g59/h60` | `p2 W2[57].b0` aliased the same way |
| `(3,131)` | 128 | 36 | `p1 W1[57].b1` aliased as `a57/b58/c59/d60/e57/f58/g59/h60` | `p2 W2[57].b1` aliased the same way |
| `(3228,4445)` | 1217 | 16 | `p1 e59/f60/g61/h62.b1` | `p2 e59/f60/g61/h62.b1` |
| `(3320,4447)` | 1127 | 16 | `p1 e59/f60/g61/h62.b2` | `p2 e59/f60/g61/h62.b2` |
| `(3695,4449)` | 754 | 16 | `p1 e59/f60/g61/h62.b3` | `p2 e59/f60/g61/h62.b3` |

## Comparison to F328

The exact counts differ by candidate/mode, but the top semantic pattern is the
same:

- top pair remains the p1/p2 `W1_57`/`W2_57` mirror at gap 128;
- high multiplicity comes from repeated state aliases, not rotation offsets;
- later high-multiplicity families are again p1/p2 state mirrors at matching
  bit positions.

The force-mode constraints shift the later high-multiplicity family from
F328's `a60/b61/c62/d63` shape toward `e59/f60/g61/h62`, but still inside the
same two-copy shift-register alias mechanism.

## Interpretation

This makes the BP/LDPC target more concrete. The dominant correction family is
stable across at least:

- sr60 bit0 aux-expose
- sr60 bit10 aux-force

The correction should model p1/p2 paired state-bit aliases through the SHA
shift register, especially the W1/W2 free-schedule mirror at round 57. A raw
gap-based correction is too indirect; the semantic object is "same bit,
same shifted state role, opposite copy."
