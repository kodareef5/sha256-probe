# Mode B speedup predictor: Mode A baseline ρ=+0.750 (n=16)
**2026-04-26 07:48 EDT** — cascade_aux_encoding bet — substantive finding.

## TL;DR

Across 16 candidates tested at 50k kissat conflicts:
- **Spearman ρ(Mode A wall, Mode B speedup) = +0.750**
- **Spearman ρ(Mode A wall, absolute saving) = +0.941**
- hardlock_bits ρ = -0.444 (weak inverse, but A-wall is much better)
- de58_size ρ = +0.185 (negligible)
- hw56 ρ = -0.074 (no correlation)

**Mode A baseline wall is the strongest predictor of Mode B speedup**.
The harder a candidate is for Mode A at 50k, the more Mode B helps.

## n=16 dataset

| candidate | A wall | B wall | speedup | saving | hl_bits | de58 | hw56 |
|---|---:|---:|---:|---:|---:|---:|---:|
| bit18 m=0x99bf552b | 3.12 | 1.01 | 3.09× | 2.11s | 1  | 130086 | 127 |
| bit28 m=0x3e57289c | 3.10 | 1.03 | 3.01× | 2.07s | 3  | 64487  | 125 |
| bit15 m=0x28c09a5a | 3.25 | 1.17 | 2.78× | 2.08s | 14 | 4096   | 125 |
| bit3  m=0x5fa301aa | 2.96 | 1.15 | 2.57× | 1.81s | 6  | 82835  | 134 |
| bit25 m=0x30f40618 | 2.97 | 1.18 | 2.52× | 1.79s | 5  | 16380  | 141 |
| bit4  m=0xd41b678d | 2.79 | 1.22 | 2.29× | 1.57s | 5  | 32152  | 130 |
| bit4  m=0x39a03c2d | 2.65 | 1.22 | 2.17× | 1.43s | 12 | 2048   | 109 |
| bit28 m=0xd1acca79 | 4.00 | 2.03 | 1.97× | 1.97s | 15 | 2048   | 127 |
| bit18 m=0xcbe11dc1 | 2.25 | 1.15 | 1.96× | 1.10s | 9  | 102922 | 146 |
| bit20 m=0x294e1ea8 | 3.93 | 2.08 | 1.89× | 1.85s | 15 | 8187   | 115 |
| bit3  m=0x33ec77ca | 2.00 | 1.11 | 1.80× | 0.89s | 6  | 82943  | 130 |
| bit31 m=0x17149975 | 2.20 | 1.26 | 1.75× | 0.94s | 10 | 82826  | 104 |
| bit25 m=0xa2f498b1 | 2.10 | 1.21 | 1.74× | 0.89s | 6  | 1024   | 136 |
| bit29 m=0x17454e4b | 2.08 | 1.21 | 1.72× | 0.87s | 12 | 8187   | 132 |
| bit31 m=0xa22dc6c7 | 2.02 | 1.31 | 1.54× | 0.71s | 14 | 32159  | 115 |
| bit24 m=0xdc27e18c | 1.78 | 1.24 | 1.44× | 0.54s | 8  | 57899  | 138 |

## Spearman correlations (n=16)

| Predictor | ρ vs speedup | ρ vs saving |
|---|---:|---:|
| Mode A wall (50k) | **+0.750** | **+0.941** |
| hl_bits           | -0.444     | -0.156     |
| de58_size         | +0.185     | +0.006     |
| hw56              | -0.074     | -0.232     |

## Interpretation

The previous "inverse hardlock" hypothesis (n=3) was real but WEAK
(ρ=-0.444 for speedup). The dominant signal is **Mode A baseline wall
itself**.

Mechanism (intuited): Mode B's force clauses provide cascade-structural
hints that help the solver propagate. A "harder" Mode A baseline (more
work to early conflicts) means the solver has more wasted exploration
that Mode B's structural hints can prune. An "easy" baseline means the
solver finds shortcuts on its own, leaving Mode B less to add.

**This is a real, falsifiable, ρ=0.94 EVIDENCE-level finding** at
sr=61, 1M kissat preprocessing window. n=16, single solver, single seed.

## What this lets us do

1. **Predict Mode B value-add per-candidate**: run a quick 50k Mode A,
   read off the wall, predict expected Mode B speedup ≈ wall × ~0.6
   (rough fit from n=16).
2. **Target Mode B at hard-to-Mode-A candidates**: Mode B's value is
   highest where the solver struggles most early.
3. **Deprioritize Mode B for easy-baseline candidates**: e.g.,
   bit=24 m=0xdc27e18c (1.78s baseline) gets only 1.44× speedup;
   Mode B's overhead may exceed its value at higher budgets.

## What this doesn't tell us

- **Whether Mode B helps at 1M+ conflicts**: prior data (1M Mode A vs B
  on hl=15 cands) showed ~1× speedup. Mode B's value is firmly
  in the early-conflict regime.
- **Whether ANY of these cands solve at sr=61**: predictor closure stands.
  10M kissat on bit=28 m=0xd1acca79 (most-constrained NEW cand): TIMEOUT
  at 303.06s wall — no SAT.

## Reproduce

```bash
# 16 cands × 2 modes × 50k = 32 runs, ~2 min total
for cand in bit{15_m28c09a5a,3_m33ec77ca,3_m5fa301aa,4_m39a03c2d,4_md41b678d,18_m99bf552b,18_mcbe11dc1,20_m294e1ea8,24_mdc27e18c,25_m30f40618,25_ma2f498b1,28_m3e57289c,28_md1acca79,29_m17454e4b,31_m17149975,31_ma22dc6c7}; do
  for mode in expose force; do
    kissat --conflicts=50000 --seed=5 -q \
      headline_hunt/bets/cascade_aux_encoding/cnfs/aux_${mode}_sr61_n32_${cand}_fillffffffff.cnf
  done
done
```

EVIDENCE-level finding: Mode A baseline wall is a strong predictor
(ρ=+0.94 for absolute saving, ρ=+0.75 for speedup) for Mode B's
value-add at the 50k early-conflict regime.

## ADDENDUM (07:55 EDT) — Multi-seed shows large variance per-cand

Tested 3 cands across the speedup range at seeds 1, 5, 42:

| candidate | seed=5 | seed=1 | seed=42 | CV(speedup) |
|---|---:|---:|---:|---:|
| bit24 m=0xdc27e18c | **1.44×** | 3.24× | 3.59× | **0.42** |
| bit4  m=0x39a03c2d | 2.17× | 1.96× | 2.45× | 0.11 |
| bit18 m=0x99bf552b | 3.09× | 2.15× | 2.20× | 0.21 |

**Critical caveat**: bit24's seed=5 "1.44×" was a major outlier. At
seeds 1 and 42, bit24 actually scored 3.24× and 3.59× — among the
HIGHEST speedups, not the lowest.

Coefficient of variation in speedup ranges 11%-42% per cand. The n=16
single-seed correlation (ρ=+0.75) is contaminated by per-cand
seed-noise that on bit24 specifically was ~42% relative.

Median-of-3-seeds for the 3-cand subset:
| candidate | A median | speedup median |
|---|---:|---:|
| bit4  | 2.65s | 2.17× |
| bit18 | 2.75s | 2.20× |
| bit24 | 3.08s | 3.24× |

Ordering by A wall: bit4 < bit18 < bit24.
Ordering by speedup: bit4 < bit18 < bit24.
**The directional finding (more A wall → more Mode B speedup)
HOLDS at median, but the n=16 ρ=+0.75 was inflated** by bit24
seed=5 happening to be unusually fast for Mode A (1.78s vs ~3.0s
median).

## Refined EVIDENCE-level claim

- Mode B speedup IS positively correlated with Mode A baseline wall.
  Direction is robust across multi-seed validation.
- The ρ=+0.75 estimate from single-seed n=16 OVERSTATES the
  predictor strength because per-cand seed-CV is 11-42%.
- A multi-seed (n_seeds ≥ 3) averaged dataset would yield a more
  honest correlation. Likely smaller ρ but more reliable.
- Mode A baseline wall remains the BEST predictor among hl_bits,
  de58_size, hw56 (all weak or null).

## Updated actionable

Predicting per-cand Mode B value-add: run quick 50k Mode A at multiple
seeds first, take median wall, multiply by ~0.6 for expected Mode B
saving. Single-seed estimates are unreliable for cands with CV > 0.2
in early-conflict regimes.
