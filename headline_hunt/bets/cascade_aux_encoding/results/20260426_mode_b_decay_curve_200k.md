# Mode B decay curve: 200k mid-budget data
**2026-04-26 13:35 EDT** — cascade_aux_encoding bet — daily heartbeat substantive review.

## Question

The predictor work characterized Mode B's value at 50k (peak ~2-9× speedup)
and observed it ~gone at 1M (speedup ≈ 1×). What's the decay curve in
between? Sharp cliff at 50k or gradual ramp?

## Setup

3 cands spanning the 50k speedup range × 3 seeds at 200k conflicts (4×
the training budget). kissat 4.0.4, sr=61.

## Results (3-seed median)

| candidate | 50k speedup | 200k speedup | 50k saving | 200k saving | retained |
|---|---:|---:|---:|---:|---:|
| bit24 m=0xdc27e18c | 3.24× | 1.34× | 2.13s | 1.28s | 60% |
| bit18 m=0x99bf552b | 2.20× | 1.21× | 1.50s | 0.82s | 55% |
| bit4  m=0x39a03c2d | 2.17× | 1.12× | 1.43s | 0.51s | 36% |

**Mode B saving retained 36-60% at 4× budget**. Not a sharp cliff —
gradual decay.

## Decay model emerging

Three points on the curve (per cand average across the 3 cands):
- 50k:  saving ≈ A_50k − 1.20 (avg ~1.7s)
- 200k: saving ≈ ~50% of 50k saving (~0.9s)
- 1M:   saving ≈ 0 (full convergence)

Implied half-life: ~150-300k conflicts. Mode B's preprocessing benefit
decays exponentially-ish, not stepwise.

## Mode B at 200k still helps 12-34%

Even at 4× the training budget, Mode B is faster:
- bit24: 1.34× speedup at 200k (still meaningful)
- bit18: 1.21× speedup at 200k
- bit4:  1.12× speedup at 200k (smallest, but positive)

So the "front-loaded preprocessing" picture is real, but the window of
value is wider than 50k — extends to ~200k with diminishing returns.

## Implications

1. **Practical Mode B targeting**: deploy at budgets <200k for meaningful
   speedup; deploy ≥1M only if the candidate's Mode A is very slow.
2. **The convergence-to-constant model needs refinement**. Mode B
   doesn't converge to ~1.20s at 50k and stay there — it gradually
   approaches Mode A's wall as conflicts increase. The 50k constant
   was a snapshot, not a steady-state.
3. **More precise decay model needed**: 4-budget sweep (50k, 200k,
   500k, 1M) on the same cands would let us fit `saving(t) = sav_50k ×
   exp(-t/τ)` for some half-life τ.

## What would tell us this is wrong

If at higher cands tested, the 200k retention is significantly different
from the 36-60% range here, the gradual-decay model fails. Test by
extending to 5+ cands at 200k.

## Heartbeat scope note

This was a daily heartbeat substantive review (single 30-min substantive
move). Refines the cascade_aux predictor by adding a mid-budget data
point. Full multi-budget sweep (50k, 100k, 200k, 500k, 1M, 2M) on
all 16 cands would be a separate substantive session — see
`bets/cascade_aux_encoding/results/<future>_decay_full_sweep_proposal.md`.

EVIDENCE-level: Mode B saving decay is gradual (36-60% retained at 4×
budget), not a sharp cliff. Window of practical value extends to ~200k,
diminishing to 0 by ~1M.
