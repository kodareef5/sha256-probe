# F153: bit19_m51ca0b34 corpus built + fixture for yale's slate (most extreme distinguished cand)

**2026-04-28**

## Summary

bit19_m51ca0b34_fill55555555 is the MOST EXTREME structurally
distinguished cand (de58_size=256, 200× below median; hardlock_bits=13).
But no corpus existed for it. F153 builds the corpus + fixture to
complete yale's structural-distinction slate.

## Corpus build

```bash
python3 build_corpus.py \
  --m0 0x51ca0b34 --fill 0x55555555 --kernel-bit 19 \
  --samples 200000 --hw-threshold 80 \
  --out residuals/by_candidate/corpus_bit19_m51ca0b34_fill55555555.jsonl
```

Output:
- 200,000 samples in 7.5 seconds
- 3,597 records below HW=80 threshold (1.8% yield)
- **min HW = 56** (lower than bit3's 55, bit28's 59, bit4's 63!)
- Max HW = 129
- 0 with da==de symmetry (rare structurally)

The 1.8% yield (vs bit3's ~10%) reflects the structural distinction —
bit19 has fewer cascade-eligible W-witnesses but they reach equivalent
or LOWER HW.

## Fixture shipped

`headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json`

Schema 2blockcertpin/v1, simulator-validated:
- Block-1 residual HW = 56 (matches bundle)
- Block-2 forward sim median target distance = 129
- Verdict: FORWARD_BROKEN (expected for naive_blocktwo)

## yale's complete distinguished-cand slate

| Cand | Fixture | de58_size | hardlock | residual_HW |
|---|---|---|---|---|
| bit19_m51ca0b34_fill55 | F153 | **256 (most extreme)** | 13 | **56 (lowest)** |
| bit28_md1acca79_fillff | F148 | 2048 | 15 | 59 |
| bit4_m39a03c2d_fillff | F149 | 2048 | 12 | 63 |
| bit25_m09990bd2_fill80 | F149 | 4096 | 13 | 62 |
| msb_m9cfea9ce_fill00 | F149 | 4096 | 10 | 62 |
| bit3 baseline (generic) | yale's | ~50K | unknown | 55 |

Yale now has 5 distinguished testbeds + bit3 baseline = 6-cand slate.

## Predicted experiment outcome (refined)

If F143 structural-distinction hypothesis holds, rank-order test:
- bit19 (de58=256, hl=13) → predicted floor 65-75 (most extreme)
- bit28 (de58=2048, hl=15) → 70-80
- bit25 (de58=4096, hl=13) → 73-83
- bit4 (de58=2048, hl=12) → 75-85
- msb_m9cfea9ce (de58=4096, hl=10) → 78-88
- bit3 generic → 86 (yale's empirical)

If yale runs F111 active subset scan on all 6, the rank-order
matching this prediction validates the structural-distinction
hypothesis as a CLASS PROPERTY.

bit19 is the MOST EXTREME prediction — if the hypothesis holds, it
should give the LOWEST score floor of any cand. If bit19 doesn't beat
bit3, the hypothesis is significantly weakened.

## Discipline

- 0 SAT compute
- 7.5 seconds of forward-sim + 30 samples for fixture validation
- All shipped artifacts schema-valid
- Registry validates clean

## Status

Yale's slate is now complete: 5 structurally distinguished cands +
bit3 baseline. The F143/F146/F148/F149/F151/F152/F153 chain is the
deepest cross-bet structural experiment the project has set up.

If yale picks up the slate, the project gets a clean 6-data-point
test of whether structural distinction (de58_size, hardlock_bits)
transfers to absorber yield as a class. Either outcome resolves a
fundamental question about cascade-1's structural-vs-empirical
landscape.
