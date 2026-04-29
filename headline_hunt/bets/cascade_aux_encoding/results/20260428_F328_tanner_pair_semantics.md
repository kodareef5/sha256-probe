---
date: 2026-04-28
bet: cascade_aux_encoding
status: TANNER_PAIR_SEMANTICS_PROFILED
---

# F328: high-multiplicity Tanner pairs are p1/p2 mirrored state aliases

## Purpose

F207 falsified the gap-9/11 BP-Bethe correction idea and identified three
actual Tanner 4-cycle structures:

- dense gap-1/2/3 local adjacency
- word-size gap-32 structure
- high-multiplicity gap-128 pairs

F207 left one concrete next probe: profile what the high-multiplicity pairs
actually encode at the SHA-arithmetic level. F328 adds that profiler and runs
it on a regenerated sr60 bit0 aux-expose CNF.

## Tool

New tool:

```
headline_hunt/bets/cascade_aux_encoding/encoders/profile_tanner_pairs.py
```

It counts Tanner variable-pair multiplicities like `tanner_4cycle_count.py`,
then joins the high-multiplicity pairs against the cascade_aux varmap sidecar.

## Setup

The exact F207 CNF artifact was not present in this checkout, so I regenerated
the matching current-encoder CNF:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py \
  --sr 60 --m0 0x8299b36f --fill 0x80000000 --kernel-bit 0 \
  --mode expose \
  --out headline_hunt/bets/cascade_aux_encoding/cnfs/aux_expose_sr60_n32_bit0_m8299b36f_fill80000000.cnf \
  --varmap + --quiet
```

Audit:

```
vars=13224 clauses=54793 VERDICT=CONFIRMED
```

The aggregate count is close to, but not byte-identical with, F207 because the
current regenerated CNF has a different variable/clause count than the archived
F207 memo reported.

## Command

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/profile_tanner_pairs.py \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_expose_sr60_n32_bit0_m8299b36f_fill80000000.cnf \
  --varmap headline_hunt/bets/cascade_aux_encoding/cnfs/aux_expose_sr60_n32_bit0_m8299b36f_fill80000000.cnf.varmap.json \
  --n-free 4 --top 24 --min-mult 10 \
  --gap 128 --gap 32 --gap 1 --gap 2 --gap 3 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F328_aux_expose_sr60_bit0_tanner_pair_profile.json
```

## Result

Aggregate current-encoder profile:

| Field | Value |
|---|---:|
| Variables | 13224 |
| Clauses read | 54793 |
| Distinct variable pairs | 41004 |
| 4-cycles | 270725 |

Selected gap pair counts:

| Gap | 4-cycle-forming pairs |
|---:|---:|
| 1 | 4649 |
| 2 | 2697 |
| 3 | 1418 |
| 32 | 1605 |
| 128 | 148 |
| 754 | 131 |

Top semantic pairs:

| Pair | Gap | Mult | Left semantic | Right semantic |
|---|---:|---:|---|---|
| `(2,130)` | 128 | 36 | `p1 W1[57].b0` aliased as `a57/b58/c59/d60/e57/f58/g59/h60` | `p2 W2[57].b0` aliased the same way |
| `(3,131)` | 128 | 20 | `p1 W1[57].b1` aliased through `e57/f58/g59/h60` | `p2 W2[57].b1` aliased the same way |
| `(5140,5894)` | 754 | 18 | `p1 a60/b61/c62/d63.b0` | `p2 a60/b61/c62/d63.b0` |
| `(5143,5897)` | 754 | 18 | `p1 a60/b61/c62/d63.b1` | `p2 a60/b61/c62/d63.b1` |
| `(5146,5900)` | 754 | 18 | `p1 a60/b61/c62/d63.b2` | `p2 a60/b61/c62/d63.b2` |

Gap-32 top pairs are mostly internal Tseitin auxiliaries not named by the
current varmap; the profiler records them as unmapped rather than inventing
semantics.

## Interpretation

The high-multiplicity structure is not a direct Σ rotation-gap artifact. The
largest pair `(2,130)` is the bit-0 free schedule pair `W1_57`/`W2_57`, and its
high multiplicity comes from repeated p1/p2 state aliases across the first free
round window:

```
a57, b58, c59, d60, e57, f58, g59, h60
```

The gap-754 family has the same shape later in the pipeline: p1 and p2 state
aliases for `a60/b61/c62/d63` at matching bit positions.

BP implication: a better correction target is not "gap-9/11"; it is paired
p1/p2 state-bit marginals at repeated alias points, especially the W1/W2 free
schedule mirror and the later `a/b/c/d` shift-register mirror. That is closer
to a two-copy coupled-state decoder than a raw Tanner-gap decoder.
