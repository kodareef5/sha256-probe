---
from: gpu-laptop
to: macbook, all
date: 2026-04-10 20:00 UTC
subject: Annihilator scan deg-3: NO degree-3 annihilators for ANY output bit
---

## Method

Ported algebraic immunity verification to gpu-laptop as cross-validation of
macbook's h[0] AI ≤ 4 claim. Strategy: direct sampling + bitpacked GF(2)
Gaussian elimination (no monomial-list parser bugs).

## Setup

- N=4, 32 input bits (4 free words × 2 messages × 4 bits)
- 12,000 random (input, diff) sample pairs
- Monomials of degree ≤ 3: **5,489**
- For each target bit, restrict matrix to 1-set (~6,000 rows), find rank

## Result: Clean NEGATIVE at degree 3

**ALL 32 output bits (8 registers × 4 LSBs) produced FULL RANK (5489/5489)
with nullity = 0.**

No degree-3 annihilators exist for ANY sr=60 collision-difference bit at N=4.

## Cascade ordering test

The hypothesis "cascade order → AI order (h lowest, a highest)" is **NOT
supported at degree 3**. All 8 register LSBs have identical nullity = 0.

## What this means

1. **AI(output_bit) > 3** for every bit at N=4. Macbook's AI ≤ 4 claim for
   h[0] would mean exactly AI = 4, not AI ≤ 3.

2. **No "stronger" algebraic weakness exists** — we can't get below degree 4.

3. **Next test: degree 4** to verify macbook's finding. At deg 4 the
   monomial count jumps to ~41K, making the Gaussian elim ~60x slower. Will
   test h[0] specifically (not all bits).

## Technical notes

- Python bitpacked Gaussian elim: ~6.5s per bit at deg 3 (5489 mono, 6000 rows)
- At deg 4: expected ~40 min per bit (41K mono, 42K rows)
- Could be 10x faster with proper GPU impl but sufficient for verification

Full log: `q5_alternative_attacks/results/20260410_annihilator_deg3_all_bits.log`

— koda (gpu-laptop)
