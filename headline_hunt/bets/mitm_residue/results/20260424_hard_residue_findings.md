# Hard-residue empirical findings — bet hypothesis substantially confirmed

**Date**: 2026-04-24
**Machine**: macbook
**Tool**: `bets/mitm_residue/prototypes/hard_residue_analyzer.py`
**Sample size**: 1,000,000 cascade-held W triples on the MSB / 0x17149975 candidate

## Headline finding

**At round 60 under the cascade chain, ~228 of 256 bits are structurally
determined and ~28 are uniform random.** This is empirically very close to the
bet's hypothesized 232/24 split. The hard-residue framing is correct, with
some refinements.

## The breakdown at round 60

| Class | Bit count | Description |
|---|---:|---|
| **Cascade-zero** | 160 | Registers a, b, c, d, e all zero. Forced by cascade chain (cw57 → da57=0 → propagates → cw58 forces da58=0 → ... → cw60 forces de60=0; the algebra cascades to a/b/c/d/e all zero at round 60). |
| **Cascade-determined non-zero** | 68 | Registers f, g, h have specific bit patterns: some forced to 1, some near-zero, some biased. These are *predictable* from cascade structure. |
| **Truly uniform (the hard residue)** | ~28 | Bits whose frequency hovers within ±0.05 of 0.5 — the cascade does NOT determine them. These are the empirical "hard bits" the bet predicted. |

228 + 28 = 256 ✓. Bet's hypothesis (232 free + 24 hard) refined: 228 *constrained* + 28 *truly free*.

## Where the hard residue lives

Concentrated almost entirely in **register g** at round 60:

| Register | Total bits | Uniform bits | Biased bits | Cascade-zero |
|---|---:|---:|---:|---:|
| a | 32 | 0 | 0 | 32 |
| b | 32 | 0 | 0 | 32 |
| c | 32 | 0 | 0 | 32 |
| d | 32 | 0 | 0 | 32 |
| e | 32 | 0 | 0 | 32 |
| f | 32 | ~4 | 28 | 0 |
| **g** | **32** | **~18** | **13** | **0** |
| h | 32 | ~4 | 27 | 0 |

The bet pointed at "g60, h60" as the bottleneck. Empirically: g60 is ~18 uniform
bits, h60 is ~4 uniform bits, f60 is ~4 uniform bits. **g60 is the dominant
hard-residue carrier.**

## Specific hard-residue bits (MSB candidate, 1M samples)

These are the bits where freq(=1) is between 0.45 and 0.55 (effectively uniform):

| Register | Hard bits (positions) |
|---|---|
| f | 1, 6, 15, 21 (4 bits) |
| g | 0, 2, 3, 5, 6, 7, 8, 9, 10, 14, 16, 20, 21, 23, 24, 26, 27, 31 (~18 bits) |
| h | 5, 15, 21, 29 (4 bits) |

Total ≈ 26 hard-residue bits. The other 256 - 26 = 230 bits are predictable from
cascade structure (with high precision at 1M samples — std error per-bit is ~0.0005).

## Why this matters for `mitm_residue`

The bet's MITM strategy relies on the existence of a small set of "hard" bits
where forward and backward freedom must meet. The empirical answer is:
- The hard set has ~26 bits (close to the bet's predicted 24).
- It's localized to a specific register (g) plus a few stragglers.
- Forward-table memory is bounded by 2^26 entries, not 2^32 — that's
  ~67 million entries vs ~4 billion. **At ~256 bytes/entry, ~17 GB instead
  of ~256 GB.** Manageable on commodity hardware.

This dramatically improves the bet's economics. If this finding holds at scale
(more samples + more candidates), the bet becomes **strongly viable**.

## At round 63 (the collision boundary)

For comparison: at round 63, only registers d and h are guaranteed zero (64
bits total). The other 192 bits (a, b, c, e, f, g) are uniform random under
cascade — no structure visible at round 63.

This means:
- The right place to do the MITM split is at **round 60**, not round 63.
- The bet's choice of round 60 as the meeting point is empirically correct.
- A round-63 MITM would face 192 hard bits — economically unworkable.

## What's NOT yet validated

1. **Cross-candidate**: this measurement is on the MSB candidate only. The
   `20260424_cross_candidate_sweep.md` result showed *distributional* similarity
   across 7 candidates at round 63, but the hard-bit *positions* at round 60 may
   differ candidate-to-candidate. Need to re-run hard_residue_analyzer.py on
   non-MSB candidates and check whether the hard bits live in the same g60
   positions.
2. **W[60] anchor sensitivity**: W[60] is fixed to the cert value here. Sweeping
   W[60] within its cascade-2-constrained range may uncover additional hard
   bits that move with W[60].
3. **Backward analysis**: only forward enumeration was tested. The MITM
   requires symmetric backward analysis (round 63 → round 60). The hard bits
   identified here are forward-uniform; the backward direction may identify a
   different (overlapping or disjoint) set.

## Reproduce

```
python3 headline_hunt/bets/mitm_residue/prototypes/hard_residue_analyzer.py \
  --m0 0x17149975 --fill 0xffffffff --kernel-bit 31 \
  --samples 1000000 --threshold 0.05 \
  --out hard_residue_msb_1M.md
```

Throughput: ~16k samples/sec on macbook = ~1 minute for 1M samples.
1M samples gives bit-frequency std error ~0.0005, more than 100× tighter than
the 0.05 threshold — so the structured/uniform classification is robust.

## Recommended next actions (ranked)

1. **Cross-candidate hard-bit positions**: run hard_residue_analyzer on 5 more
   candidates, check whether the ~26 uniform bits are in the same g60 positions.
   If yes: a single forward-table works for all candidates. If no: the bet's
   memory budget multiplies by the number of distinct hard-bit-position sets.
   ~5 minutes CPU. **Highest leverage by far.**
2. **W[60] sweep**: extend forward_table_builder to vary W[60] within cascade-
   2-constrained slack; re-measure hard-residue. Confirms (or refutes) that the
   anchor doesn't bias the result.
3. **Backward analyzer**: implement the symmetric direction (round 63 collision
   target → round 60 requirement) and intersect the hard-bit sets. The actual
   MITM table key is the intersection.

Item 1 is the cleanest win and unblocks a real architectural decision for the bet.
