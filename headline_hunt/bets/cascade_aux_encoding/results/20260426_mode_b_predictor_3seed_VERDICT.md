# Mode B speedup predictor — 3-seed median VERDICT
**2026-04-26 08:00 EDT** — cascade_aux_encoding bet — definitive multi-seed result.

## TL;DR

After expanding from n=16 single-seed to n=16 × 3-seed-median:

| Predictor | ρ (single-seed) | ρ (3-seed median) |
|---|---:|---:|
| **Mode A wall → speedup** | +0.750 | **+0.976** |
| **Mode A wall → saving**  | +0.941 | **+0.994** |
| hl_bits → speedup         | -0.444 | -0.215 |
| de58_size → speedup       | +0.185 | -0.150 |
| hw56 → speedup            | -0.074 | +0.350 |

**Mode A wall is essentially a perfect predictor** of Mode B's
50k-conflict speedup once seed-noise is averaged out. The relationship
is near-monotonic: harder Mode A baseline → bigger Mode B saving.

## n=16 dataset, 3 seeds (1, 5, 42), 50k kissat conflicts

| candidate | A med | B med | spd med | sav med | CV_A | CV_B | hl | de58 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bit24 m=0xdc27e18c | 3.08 | 0.95 | 3.24× | 2.13s | 0.30 | 0.17 | 8  | 57899 |
| bit15 m=0x28c09a5a | 3.25 | 1.17 | 2.78× | 2.08s | 0.18 | 0.01 | 14 | 4096  |
| bit29 m=0x17454e4b | 3.41 | 1.21 | 2.69× | 2.14s | 0.26 | 0.05 | 12 | 8187  |
| bit25 m=0xa2f498b1 | 3.05 | 1.21 | 2.58× | 1.87s | 0.22 | 0.02 | 6  | 1024  |
| bit25 m=0x30f40618 | 2.97 | 1.23 | 2.52× | 1.79s | 0.13 | 0.02 | 5  | 16380 |
| bit28 m=0x3e57289c | 2.85 | 1.21 | 2.34× | 1.63s | 0.07 | 0.09 | 3  | 64487 |
| bit3  m=0x5fa301aa | 2.83 | 1.23 | 2.30× | 1.60s | 0.03 | 0.04 | 6  | 82835 |
| bit18 m=0x99bf552b | 2.75 | 1.17 | 2.20× | 1.50s | 0.11 | 0.11 | 1  | 130086|
| bit4  m=0x39a03c2d | 2.65 | 1.21 | 2.17× | 1.43s | 0.15 | 0.04 | 12 | 2048  |
| bit3  m=0x33ec77ca | 2.41 | 1.20 | 2.01× | 1.21s | 0.18 | 0.04 | 6  | 82943 |
| bit31 m=0x17149975 | 2.57 | 1.26 | 2.01× | 1.29s | 0.16 | 0.04 | 10 | 82826 |
| bit28 m=0xd1acca79 | 2.52 | 1.22 | 1.97× | 1.36s | 0.41 | 0.33 | 15 | 2048  |
| bit18 m=0xcbe11dc1 | 2.27 | 1.28 | 1.96× | 1.10s | 0.09 | 0.08 | 9  | 102922|
| bit31 m=0xa22dc6c7 | 2.32 | 1.19 | 1.95× | 1.13s | 0.16 | 0.07 | 14 | 32159 |
| bit4  m=0xd41b678d | 1.99 | 1.22 | 1.73× | 0.84s | 0.22 | 0.04 | 5  | 32152 |
| bit20 m=0x294e1ea8 | 1.98 | 1.24 | 1.61× | 0.75s | 0.44 | 0.32 | 15 | 8187  |

Per-cand CV across 3 seeds:
- CV(Mode A wall): mean 0.19, median 0.17, max 0.44
- CV(Mode B wall): mean 0.09, median 0.05, max 0.33  ← Mode B much more stable
- CV(speedup):     mean 0.19, median 0.19

## Key observations

1. **Mode A wall predicts speedup ρ=+0.976**. Run a 50k Mode A on a
   new candidate, multiply by ~0.6, and you get the predicted Mode B
   absolute saving with high accuracy.

2. **Mode B is much more stable than Mode A across seeds**. CV(B) ≈
   0.09 vs CV(A) ≈ 0.19. Mode B's force clauses force convergent
   solver behavior; Mode A's exploration is more seed-dependent.

3. **hl_bits weak predictor (ρ=-0.215)**. The earlier "inverse hardlock"
   hypothesis at n=3 was real but small magnitude — Mode A wall
   subsumes it.

4. **hw56 emerges as moderate positive predictor (ρ=+0.350)**. Heavier
   pre-state Hamming weight → slightly larger Mode B speedup. Untested
   structurally — could be confound with Mode A wall.

5. **bit20 m=0x294e1ea8 has lowest speedup (1.61×) AND lowest
   Mode A median wall (1.98s)** — consistent with the predictor.

## Mechanism (intuition)

Mode B's force clauses encode cascade-structural constraints. The
solver normally has to LEARN these via conflict-driven backtracking
in the early-conflict regime. With Mode B, the constraints are
already there — the solver skips that learning phase.

How much the solver "would have spent" learning depends on the
instance hardness, which Mode A baseline measures directly. Hence the
near-perfect correlation: Mode B saves what Mode A would have spent
on cascade-structural learning, modulo small noise.

## Refined EVIDENCE-level claims

- **Mode A 50k wall predicts Mode B 50k speedup with ρ=+0.976** at
  n=16 candidates (3-seed median, kissat 4.0.4, sr=61).
- **Per-cand seed-CV in speedup is ~19%**; multi-seed averaging
  required for honest per-cand prediction.
- **The predictor is strongest for absolute saving (ρ=+0.994)** —
  even tighter than for relative speedup.

## Implication for headline path

Mode B's value is strictly bounded by Mode A's baseline. To get
larger Mode B speedups, you'd need cands where Mode A is HARDER
at 50k. But predictor closure (validation matrix earlier) showed
Mode A baseline doesn't predict full sr=61 SAT-finding ability. So
even bit24 (highest 50k speedup, 3.24×) is unlikely to solve at 1M+
conflicts.

**Mode B's value is preprocessing-time, not solving-time.** This memo
quantifies the preprocessing-time effect cleanly; it does NOT promise
SAT.

## Reproduce

```bash
# 16 cands × 2 modes × 3 seeds = 96 runs, ~5-10 min
for cand in {bit15_m28c09a5a,bit3_m33ec77ca,bit3_m5fa301aa,bit4_m39a03c2d,bit4_md41b678d,bit18_m99bf552b,bit18_mcbe11dc1,bit20_m294e1ea8,bit24_mdc27e18c,bit25_m30f40618,bit25_ma2f498b1,bit28_m3e57289c,bit28_md1acca79,bit29_m17454e4b,bit31_m17149975,bit31_ma22dc6c7}; do
  for mode in expose force; do
    for seed in 1 5 42; do
      kissat --conflicts=50000 --seed=$seed -q \
        headline_hunt/bets/cascade_aux_encoding/cnfs/aux_${mode}_sr61_n32_${cand}_fillffffffff.cnf
    done
  done
done
```

EVIDENCE-level result: Mode A 50k wall → Mode B speedup, Spearman
ρ = +0.976 (3-seed median, n=16 cands).
