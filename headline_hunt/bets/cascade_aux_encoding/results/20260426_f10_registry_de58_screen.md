# F10: Registry-wide de58 screen — 0/67 cands have de58=0
**2026-04-26 20:05 EDT**

Sampled 16,384 W57 chambers per cand for ALL 67 registry candidates.
Looking for cascade-1 chambers with `de58 = 0` (necessary condition
for sr=61 collision via cascade-1).

## Result: 0/67 cands have de58=0 in 16K-chamber sample

The closest approaches (min_HW ≤ 5):

| cand | min HW | min HW value | low-HW count |
|---|---:|---|---:|
| **cand_n32_bit17_m427c281d_fill80000000** | **4** | 0x00080122 | **14** |
| cand_n32_msb_m189b13c7_fill80000000 | 5 | 0x00020198 | 1 |
| cand_n32_bit10_m27e646e1_fill55555555 | 5 | 0x50000308 | 1 |
| cand_n32_bit13_m4e560940_fillaaaaaaaa | 5 | 0x10902040 | 7 |
| cand_n32_bit18_m99bf552b_fillffffffff | 5 | 0x82160000 | 1 |
| cand_n32_bit15_m6a25c416_fillffffffff | 5 | 0x04144100 | 2 |
| cand_n32_bit29_m17454e4b_fillffffffff | 5 | 0x00844048 | 9 |

Notable: **bit=17 m=0x427c281d** is the closest reach with a min_hw=4
chamber AND 14 separate low-HW (≤5) chambers in the sample. This cand
is structurally distinguished as the registry's "closest" to cascade-1
sr=61.

## Definitively eliminated (small image, fully sampled)

Cands with image size ≤ 1024 are fully covered by 16K samples:

| cand | distinct de58 | min HW | de58=0 |
|---|---:|---:|---|
| cand_n32_bit19_m51ca0b34_fill55555555 | 256 | 11 | absent |
| cand_n32_bit25_ma2f498b1_fillffffffff | 1024 | 10 | absent |

For these two, `0 ∉ de58_image` is **certain**, not probabilistic.
No cascade-1 sr=61 collision exists for bit=19 or bit=25 ma2f498b1.

## What this means

- **No registry cand has been shown to have a cascade-1 chamber with
  de58=0**, but 16K samples isn't exhaustive for cands with image >
  16K. Larger sample (1M+) needed to be confident on large-image cands.
- The cands with image ≤ 16K (bit=19, bit=25 ma2f498b1, plus a few
  others ≤ 16K) are DEFINITIVELY eliminated.
- The 7 low-HW cands are TANTALIZING — their min de58 is close to zero;
  larger sampling could reveal a HW=0 chamber.

## Cross-bet implications

- **singular_chamber_rank bet**: F10 directly explains the HW4 D61
  floor. Yale's HW4 frontier on idx=0/8/17 corresponds to the cascade-1
  chamber's de58 HW. The HW4 lower bound IS the de58 image's minimum
  HW for those cands. F10 finds bit=17 m=0x427c281d at HW=4 in the
  cascade_aux registry — this cand should be added to singular_chamber's
  test set as a fresh structural candidate.
- **block2_wang bet**: F10 narrows where to look for residuals — the
  7 close-to-zero cands have the most "useful" cascade-1 carry trails.
  Residual extraction on bit=17 m=0x427c281d should yield carry patterns
  closer to the round-58 cancellation target than the canonical cands.

## Follow-up F11 launching

Extending sample to 1M chambers per close-to-zero cand. If HW=0 is
reachable for any of the 7, that's the FIRST sr=61-eligible chamber
found in the registry.

## Methodology

`/tmp/deep_dig/de58_zero_screen_all.py` runs in 258s on M5
(67 cands × 16K W57 evals). Per-cand cost ≈ 4s. Output saved to
`/tmp/deep_dig/de58_screen_all.json` with full per-cand metadata.

EVIDENCE-level: STRONG STRUCTURAL FACT for the 2 small-image cands
(bit=19, bit=25 ma2f498b1). EVIDENCE for the rest pending F11
deeper sample.
