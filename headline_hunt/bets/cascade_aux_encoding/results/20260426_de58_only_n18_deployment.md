# de58-only n=18 deployment chart — 1.43× median, 0% regressions
**2026-04-26 19:21 EDT**

Promotes the per-chamber de58-only finding (commit 3bc3da9) from
n=4 preliminary → n=18 deployment. Strictly better than the 13-bit
marginal-locked variant on every dimension.

## Result

18 cands × 3 seeds × 50k kissat budget × Mode A base.
W57 per cand from yale's GPU off58hill HW4-reaching survey
(`/tmp/deep_dig/off58hill_18cands.json`).

| cand | base_med (s) | de58_med (s) | speedup |
|---|---:|---:|---:|
| msb_cert_m17149975_ff_bit31 | 2.79 | 1.93 | 1.45× |
| bit19_m51ca0b34_55 | 2.55 | 1.94 | 1.32× |
| msb_m9cfea9ce_00 | 2.89 | 1.82 | 1.59× |
| bit20_m294e1ea8_ff | 2.90 | 1.94 | 1.49× |
| bit28_md1acca79_ff | 2.79 | 1.74 | 1.61× |
| bit28_m3e57289c_ff | 2.78 | 1.48 | **1.88×** |
| bit18_m99bf552b_ff | 2.63 | 1.47 | 1.79× |
| bit18_mcbe11dc1_ff | 1.95 | 1.79 | 1.09× |
| bit3_m33ec77ca_ff | 2.77 | 2.09 | 1.33× |
| bit3_m5fa301aa_ff | 2.02 | 1.87 | 1.08× |
| bit1_m6fbc8d8e_ff | 2.99 | 1.92 | 1.55× |
| bit14_m67043cdd_ff | 3.08 | 2.18 | 1.41× |
| bit14_mb5541a6e_ff | 2.86 | 2.20 | 1.30× |
| bit14_m40fde4d2_ff | 2.93 | 2.07 | 1.41× |
| bit25_ma2f498b1_ff | 3.07 | 1.51 | **2.04×** |
| bit4_m39a03c2d_ff | 2.28 | 1.63 | 1.39× |
| bit29_m17454e4b_ff | 3.20 | 1.80 | 1.78× |
| bit15_m28c09a5a_ff | 2.44 | 2.32 | 1.05× |

**Aggregate (n=18)**:
- median: **1.43×**
- mean: 1.48×
- min (floor): 1.05×
- max (ceiling): 2.04×
- **regressions: 0/18 (0%)**

## Comparison to prior cascade_aux variants

| variant | scope | median | floor | regression rate |
|---|---|---:|---:|---:|
| Mode A (baseline) | reference | 1.00× | — | — |
| Mode B (force) | n=18 | ~1.50× | 1.0× | low |
| 13-bit marginal-locked | n=18 (commit a95a267) | 1.16× | 0.7× | ~25% |
| **de58-at-w57 (this memo)** | n=18 (commit pending) | **1.43×** | **1.05×** | **0%** |

de58-at-w57 closes most of the gap to Mode B (which is the strongest
expose-side hint variant we've measured) while keeping Mode A's
solution-set semantics. Critically, the **floor is above 1.0** — no
cand regresses, unlike the 13-bit variant.

## Why the floor moved up

13-bit marginal-locked fixes only the bits whose **aggregate** image
marginal is exactly 0 or 1. That's typically 6-13 bits depending on
the cand. The remaining 19-26 de58 bits are unconstrained, leaving
~2^(19-26) candidate de58 values consistent with the aggregate image.

de58-at-w57 fixes ALL 32 de58 bits to a single chamber-specific
value. The encoded constraint is strictly stronger, AND the implied
W57 set is exactly the chamber that achieves HW4 (the W57 we use
came from yale's GPU survey of HW4-reaching W57s).

The 0% regression rate suggests the "fixing too much" failure mode
that plagued 13-bit (regressions when locked bits weren't the
solver's natural propagation order) doesn't manifest when fixing
all 32 — the solver sees a fully-determined de58 and uses it for
unit propagation cleanly.

## Ceiling cands (1.78×–2.04×)

bit25_ma2f498b1_ff (2.04×), bit28_m3e57289c_ff (1.88×),
bit29_m17454e4b_ff (1.78×), bit18_m99bf552b_ff (1.79×).

These cands have larger Mode A walls (2.78s–3.20s base). The hint
cuts their search drastically. Hypothesis: their Mode A wall is
de58-determined, and the hint short-circuits whatever propagation
path Mode A would have built up.

## Floor cands (1.05–1.09×)

bit15_m28c09a5a_ff (1.05×), bit3_m5fa301aa_ff (1.08×),
bit18_mcbe11dc1_ff (1.09×).

These already have low base walls (1.95s–2.44s). The de58 hint
gives marginal improvement. Hypothesis: the natural Mode A path
is already short, and de58 fixing doesn't speed it up further.

## Deployment status

- Wrapper supports it: `--hint-mode de58-at-w57 --w57 0xHEX` (commit 52390db).
- Per-chamber W57 source: yale's off58hill HW4 survey for the cand,
  or any other HW4-reaching W57. Canonical W57 also valid.
- Recommended default for new cascade_aux runs at sr=61.

## F3 follow-up: Mode A wall predictor on de58-only

Computed Spearman ρ(base_med, de58_speedup) over the n=18 walls above:

| variant | Spearman ρ | Pearson r |
|---|---:|---:|
| Mode B (force) | +0.976 | (very strong) |
| 13-bit marginal-locked | +0.792 | (strong) |
| **de58-at-w57** | **+0.569** | +0.660 |

The Mode A wall predictor IS positive for de58-only — but weaker
than for the other two variants. Hypothesis for why: de58-at-w57 is
more uniformly effective (0% regressions, 1.05× floor) so the
between-cand variance in speedup reflects cand-specific mechanics
more than the gross "how hard is the Mode A search" signal.

The predictor remains a useful coarse filter (cands with high Mode A
walls *will* benefit), but not a fine-grained ranking tool for this
variant. The unified-predictor narrative now reads: Mode A wall
positively correlates with all 3 expose-side hint variants, with the
correlation weakening as the hint gets more comprehensive.

## Other open questions / next steps

1. **F4: de59 free hint**. Per-chamber de59 is ALSO size = 1, AND
   de59 is **cand-level invariant** (verified: 64 random W57s → 1
   distinct de59 per cand). So 32 more "free" hint bits stack with
   de58-at-w57 → 64 bits per chamber. Could push median speedup
   further with no W57 commitment cost.

2. **F5: budget sweep**. The 13-bit hint's sweet spot was 50k. Where
   is de58-at-w57's sweet spot? Could degrade slower (more info
   means more useful at higher budgets).

3. **Open-question: would Mode B + de58-at-w57 stack?** Mode B gives
   ~1.50× via solution-set restriction. If Mode A + de58-at-w57 also
   gives 1.43× via constraint propagation, what does Mode B + de58
   look like? Risk: collide / over-constrain.

EVIDENCE-level: VERIFIED at n=18 × 3 seeds. The per-chamber
de58_size=1 mechanism is structurally derivable (commit 3bc3da9).
The 0% regression rate is a strong empirical signal.
