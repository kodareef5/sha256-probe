# Mode B predictor: cross-sr-level generalization (sr=61 → sr=60)
**2026-04-26 08:35 EDT** — cascade_aux_encoding bet — generalization test.

## Question

The Mode A wall → Mode B speedup predictor (ρ=+0.976) was derived
from 16 cands × 3 seeds at **sr=61**. Does it generalize to **sr=60**?

If the underlying mechanism is real (Mode B forces convergent solver
preprocessing), the relationship should hold at sr=60 too — just with
different constants since sr=60 has one more free schedule word
constraint.

## Setup

5 candidates spanning hardlock range, run at sr=60 (vs sr=61 from
prior data). Same 3-seed protocol (1, 5, 42), 50k kissat conflicts.

## sr=60 results (3-seed median)

| candidate | hl_bits | A med | B med | speedup | saving | CV_A | CV_B |
|---|---:|---:|---:|---:|---:|---:|---:|
| bit31 m=0x17149975 | 10 | 1.62 | 0.93 | 1.78× | 0.71s | 0.16 | 0.02 |
| bit20 m=0x294e1ea8 | 15 | 1.73 | 0.99 | 1.75× | 0.74s | 0.11 | 0.04 |
| bit28 m=0x3e57289c | 3  | 1.83 | 0.94 | 1.95× | 0.89s | 0.15 | 0.06 |
| bit24 m=0xdc27e18c | 8  | 1.94 | 1.01 | 1.92× | 0.93s | 0.06 | 0.04 |
| bit18 m=0x99bf552b | 1  | 1.82 | 0.91 | 1.94× | 0.88s | 0.12 | 0.03 |

## sr=60 vs sr=61 comparison (same 5 cands)

| candidate | sr60 A | sr61 A | sr60 B | sr61 B | sr60 spd | sr61 spd |
|---|---:|---:|---:|---:|---:|---:|
| bit31 m=0x17149975 | 1.62 | 2.57 | 0.93 | 1.26 | 1.78× | 2.01× |
| bit20 m=0x294e1ea8 | 1.73 | 1.98 | 0.99 | 1.24 | 1.75× | 1.61× |
| bit28 m=0x3e57289c | 1.83 | 2.85 | 0.94 | 1.21 | 1.95× | 2.34× |
| bit24 m=0xdc27e18c | 1.94 | 3.08 | 1.01 | 0.95 | 1.92× | 3.24× |
| bit18 m=0x99bf552b | 1.82 | 2.75 | 0.91 | 1.17 | 1.94× | 2.20× |

## Key observations

1. **Mode B converges to a smaller constant at sr=60**: median ~0.94s
   (CV across cands = 4.4%) vs sr=61's ~1.20s (CV ≈ 9%). One fewer
   free schedule word at sr=60 = smaller preprocessing workload.

2. **Mode B is even more stable at sr=60**: CV(B) ≤ 6% per cand (max
   was bit28 at 0.06). Forces converge faster when there's less
   search space.

3. **Mode A is also faster at sr=60** (1.62-1.94s vs 1.98-3.08s at
   sr=61). The whole problem is easier; the mode-B benefit is
   smaller in absolute terms.

## Spearman ρ at sr=60 (n=5)

| Predictor | ρ at sr=60 | ρ at sr=61 (n=16) |
|---|---:|---:|
| Mode A wall → speedup | +0.600 | +0.976 |
| **Mode A wall → saving**  | **+1.000** | **+0.994** |

The absolute saving correlation is **PERFECT at sr=60** (n=5, all 5
cands strictly ordered). The speedup correlation is weaker (ρ=+0.6),
likely due to small-N noise in the speedup ratio and the very tight
range of sr=60 speedups (1.75-1.95×).

## Interpretation

The predictor MECHANISM generalizes:
- Mode B drives kissat to a constant preprocessing wall (sr-level
  dependent: ~0.94s sr=60, ~1.20s sr=61).
- Mode A varies with cand structure.
- Speedup ≈ A_med / B_med (where B_med depends on sr-level).

**Refined model (cross-sr)**:
- Predicted Mode B median wall ≈ {0.94s if sr=60, 1.20s if sr=61}
- Predicted speedup ≈ A_median / B_constant(sr)

## What this validates

- The "constant Mode B" hypothesis is correct across at least 2
  sr-levels (sr=60, sr=61).
- The Mode A wall → Mode B saving relationship has ρ=+0.99-1.00 in
  both sr-level subsets.
- The mechanism (Mode B forces convergent preprocessing) is
  sr-level-invariant; only the converged value changes.

## What this does NOT validate

- Generalization to sr=59 or sr=62 (untested).
- Generalization to budgets other than 50k.
- Generalization to solvers other than kissat 4.0.4.

## Headline-relevance

The cascade_aux bet now has a **2-sr-level predictor model**:
- sr=60: speedup ≈ A/0.94, saving ≈ A − 0.94
- sr=61: speedup ≈ A/1.20, saving ≈ A − 1.20

Mode B's value is preprocessing-time, sr-level-dependent. Headline
path is unaffected (predictor closure stands), but the bet's
mechanism is now characterized with cross-sr generalization
EVIDENCE.

EVIDENCE-level: predictor STRUCTURE generalizes from sr=61 to sr=60.
Mode B's converged-wall constant is sr-level-specific; the linear
A→saving relationship holds at ρ ≥ +0.99 in both.
