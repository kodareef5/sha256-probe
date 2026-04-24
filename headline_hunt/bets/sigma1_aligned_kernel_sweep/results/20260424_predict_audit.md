# sigma1_aligned_kernel_sweep — predict-based audit

**Closed-form (h60+f60 only) prediction across 35 candidates split by kernel-bit type:**

| Group | n | mean total predicted hard bits |
|---|---:|---:|
| Sigma1-aligned bits (6, 11, 17, 19, 25) | 12 | 7.6 |
| Non-sigma1-aligned bits (0, 10, 13, 31) | 23 | 7.4 |

Difference: **0.2 bits — negligible**.

## What this says

The bet's hypothesis: "sigma1-aligned bits (6, 11, 17, 19, 25) are productive for sr=61 but never fully swept with the best fills — sweep them and find optimal candidates."

Empirically (closed-form pre-screen) shows no systematic h60+f60 advantage for sigma1-aligned candidates. Mean is essentially identical to non-aligned.

This is suggestive but not definitive:
- Pre-screen covers only h60+f60 (~9 of 28 bits). g60 (~18 bits) dominates and isn't yet predictable. The 1M-sample full sweep currently running in background will tell us about g60 differences.
- "Productive" might mean something other than "smaller hard-residue" — e.g., easier solver behavior, better differential trail compatibility. Pre-screen doesn't measure those.

## Bet status

The bet stays at priority 7 (lowest). Per the algebraic pre-screen alone, sigma1-aligned offers no clear advantage. The original justification ("never fully swept with the best fills") is unverified — and the few candidates we have at each bit position (6: 6 cands, 11: 2, 17: 3, 19: 1, 25: 1) span 1-2 fills each, mostly 0x00000000 / 0x55555555 / 0xaaaaaaaa / 0xffffffff / 0x80000000 / 0x7fffffff. So 5-6 fills × ~5 bits = at most 30 cells, mostly partially populated.

## Concrete next-action (optional)

If a worker wants to validate or kill this bet:
1. Run full 35-candidate hard_residue_analyzer (currently in flight via background sweep).
2. Compare the empirical TOTAL hard bits (h+f+g) for sigma1-aligned vs others.
3. If still no systematic difference, kill the bet and add to negatives.yaml.

Until that data lands, status remains `open` with low priority. No further work this session.

## Pre-screen detail (top-3 sigma1-aligned)

The smallest predicted-h+f sigma1-aligned candidates:
- bit17 m427c281d: 5 bits (3h + 2f)
- bit17 m8c752c40: 6 bits (3h + 3f)
- bit11 m45b0a5f6: 7 bits (2h + 5f)

Smallest predicted-h+f non-aligned: bit00 mc765db3d (5 bits) and bit10 m27e646e1 (5 bits).

So the global minimum (5 bits) is hit by candidates from BOTH groups. No advantage to sigma1-alignment at this level of analysis.
