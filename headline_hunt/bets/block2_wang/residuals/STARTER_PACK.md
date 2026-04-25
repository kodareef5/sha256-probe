# Top-50 lowest-HW residuals — block2_wang starter pack

`top50_lowest_hw.jsonl` — the 50 lowest-total-HW residuals from `corpus_msb_200k_hw96.jsonl`. HW range: **62 to 69**.

These are the highest-quality residuals available from random sampling at N=32 on the MSB candidate. Active register pattern is universal: `[a, b, c, _, e, f, g, _]` (d63 and h63 always zero by cascade).

## Top 5

| HW | da63 | de63 | W1[57] |
|---:|---|---|---|
| 62 | 0x30a45a81 | 0x7ac504a2 | 0x03005549 |
| 63 | 0x0e88c074 | 0x351f6c90 | 0xf99f0877 |
| 65 | 0xc7027d25 | 0x8071ab0d | 0x353ee9c4 |
| 65 | 0x28d000a4 | 0x5c361243 | 0x3a488c5e |
| 65 | 0xaa602b20 | 0xa4ca1764 | 0xc5f5528a |

Each record (per the build_corpus.py schema) has full (state1_63, state2_63, W[57..60]_pair) so the residual is fully reconstructable.

## Why HW=62 isn't useful for direct Wang

Wang differential trails for SHA-2 typically work with HW ≤ 16-24 active bits in the IV difference. HW=62 is ~3× that — way too dense. The `block2_wang` bet is BLOCKED at this stage.

## What this starter pack is good for (still)

1. **Cluster analysis**: 50 residuals over 6 active registers is enough sample to look for clusters — recurring (da, de) patterns, bit-position concentrations, etc. Could reveal a "shape" the cascade produces that a tailored trail engine could absorb even at higher HW.

2. **Hill-climb seeds**: even though hill-climb on residual HW failed (results/20260424_hillclimb_negative.md, plateau at 82), seeding from these 50 instead of random *might* improve the plateau. Marginal hope, but free to test.

3. **Algebraic structure check**: if all 50 have specific bit patterns at the active positions (e.g., all have da63 with the high bit set), that hints at structural constraints the cascade imposes that could become a trail-engine target.

## Concrete next-action for whoever picks up block2_wang

```python
# Read 50 residuals
with open('top50_lowest_hw.jsonl') as f:
    residuals = [json.loads(l) for l in f]

# Cluster by active-register HW pattern
from collections import Counter
patterns = Counter(tuple(r['hw63']) for r in residuals)
# Look for recurring shapes
```

Or skip to the harder version: extend `build_corpus.py` to enumerate 1M+ samples (5+ min CPU) and capture the lowest 100 — wider net, better statistics.

Until the trail-search engine exists, this starter pack is more "documentation of the residual landscape" than an active research input.

## Files

- `top50_lowest_hw.jsonl` — the 50 residuals
- `corpus_msb_200k_hw96.jsonl` — full 104k-record source corpus
- `build_corpus.py` — generator script
- `20260424_hillclimb_negative.md` — why we can't get below HW=62 with current tools
