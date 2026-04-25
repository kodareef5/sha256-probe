# de58 class non-uniformity — structural pruning for block2_wang backward search

## What I found

Ran `q5/apath_first_n8` (already-built binary). It implements a 3-level filter chain for N=8 cascade-DP:
- Level 0: classify W57 by de58 (a-path structure groups W57 into 8 classes of 32 W57 values each)
- Level 1: de61=0 early-exit after round 61
- Level 2: full collision check at r=63

Result at N=8:
```
*** ALL 260 COLLISIONS FOUND AND VERIFIED ***
Throughput: 6.17e+09 configs/sec
Speedup vs NEON baseline: 3.0x
Speedup vs scalar: 13.2x
```

## The interesting empirical bit: de58 classes are NON-UNIFORM

| de58 class | Collisions | per-W57 rate | Spread |
|---|---:|---:|---|
| 0x34 | 39 | 1.2 | mid-high |
| 0x42 | 17 | 0.5 | LOW |
| 0x44 | **59** | **1.8** | HIGHEST |
| 0xb2 | 23 | 0.7 | low |
| 0xb4 | 42 | 1.3 | mid-high |
| 0xc2 | **15** | **0.5** | LOWEST |
| 0xc4 | 44 | 1.4 | mid-high |
| (one missing) | — | — | — |

Mean: 32.5 collisions/class.
Range: 15 to 59 (4× variation).
Stdev: ~17.

**The de58 value of W57 deterministically partitions the (W57, W58, W59, W60) search space, and some partitions yield 4× more collisions than others.** Empirically structural — not random.

## Implication for block2_wang's backward search

The block2_wang bet's path B (backward-search engine for N=32) currently considers all (W57, W58, W59) triples uniformly. The 4× variation in de58 class collision density at N=8 suggests:

1. **Pre-filter by de58 class**: at N=32, the de58 value is 32 bits → up to 2^32 classes. If similar non-uniformity holds, focusing search on the top-quartile classes saves ~4× compute on average.

2. **Combine with mitm_residue's 4-d.o.f. residual variety**: the 4 d.o.f. at r=63 are downstream of the de58 class. The de58 class essentially CONSTRAINS where the residual lands in the 4-d.o.f. variety.

3. **Adaptive search**: start with the top-density de58 class, expand to others only if needed. This reduces expected search depth.

## Why this works (structural reason)

Per the a-path-first analysis (Gemini 3.1 Pro + GPT-5.4 review):
- de58 depends ONLY on W57 (not W58, W59, W60). de58 has 8 distinct values at N=8 (one per W57 class).
- Each de58 class corresponds to a different downstream "geometry" — different number of compatible W58/W59/W60 combinations.

At N=32: de58 will have some discrete number of structural classes (maybe in low thousands, not 2^32 — the cascade's a-path constraints limit the count). Similar non-uniformity expected.

## Combined with block2_wang's other foundations

The block2_wang bet's path B foundations now include:

| Foundation | What it gives |
|---|---|
| `q5/backward_construct.c` (17× speedup at N=8) | Bit-by-bit constraint inversion algorithm |
| `q5/apath_first_n8.c` (13× scalar speedup) | de58 class partitioning + structural pre-filter |
| `mitm_residue` 4-d.o.f. variety (this session) | Residual signature for MITM caching |
| Wang bit-condition algebra (TODO) | Probabilistic xdp+ trail extension scoring |

A future N=32 backward-search engine would COMBINE these:
1. Outer loop iterates de58 classes, ordered by collision density (apath_first_n8 idea).
2. Per-class: bit-by-bit W60 inversion (backward_construct.c idea).
3. Match against 4-d.o.f. residual variety signature for MITM-style cache hits (mitm_residue).
4. Score trail extensions by xdp+ (Wang/Lipmaa-Moriai literature).

## Compute spent

~1 second on macbook (apath_first_n8 already built, runs in 0.7s for full N=8 enumeration).

## Not chasing further

The de58 class structure at N=32 is the kind of thing that needs ACTUAL N=32 computation to verify. The structural ARGUMENT (similar non-uniformity expected) is plausible but not proven.

This finding adds a third empirical pillar to block2_wang's path B (after backward_construct.c and the structural variety). It doesn't kill the bet or directly advance it; it sharpens the design space for a future implementer.

## Updated next-action for block2_wang BET.yaml

Currently:
> Extension to N=32 is now ~1-2 weeks of focused implementation (port arithmetic + add MITM signature caching + Wang-style bit-condition pruning).

Should become:
> Extension to N=32 combines: (a) bit-by-bit W60 inversion from q5/backward_construct.c, (b) de58 class pre-filtering from q5/apath_first_n8.c, (c) MITM signature caching keyed by mitm_residue's 4-d.o.f. residual variety, (d) optional xdp+ trail-extension scoring per Lipmaa-Moriai. ~2-3 weeks focused implementation.
