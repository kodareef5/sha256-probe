# F126: fixed-diff resampling does not beat the score-86 absorber
**2026-04-28**

## Summary

F123/F125 showed that the score-86 block-2 absorber is locally isolated
under one/two-bit raw, two-sided, and common-mode moves. F126 tests a
larger structured move: keep the entire saved M1 xor M2 message difference
fixed, but resample the absolute message words.

Result: no improvement.

```
mode    samples  improving  best resampled score
active    20000          0                    96
all       20000          0                    98
```

The saved score-86 point remains better than every fixed-diff resample.

## New tool

New script:

```
headline_hunt/bets/block2_wang/encoders/resample_fixed_diff_absorber.py
```

It loads a saved absorber, extracts the per-word message difference
`D = M1 xor M2`, then samples new absolute M1 words and sets `M2 = M1 xor D`.

Modes:

- `active`: resample only the active difference words.
- `all`: resample all 16 message words.

Both modes preserve the same message-diff HW and active message-word set.

## Commands

Active-word resampling:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/resample_fixed_diff_absorber.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --mode active \
  --samples 20000 --seed 1717 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F126_bit3_active_01289_fixeddiff_active_20k.json
```

All-word resampling:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/resample_fixed_diff_absorber.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --mode all \
  --samples 20000 --seed 1818 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F126_bit3_active_01289_fixeddiff_all_20k.json
```

Archived artifacts:

```
results/search_artifacts/20260428_F126_bit3_active_01289_fixeddiff_active_20k.json
results/search_artifacts/20260428_F126_bit3_active_01289_fixeddiff_all_20k.json
```

## Results

The base candidate:

```
Active words:        0,1,2,8,9
Base score:          86
Message diff HW:     80
Nonzero W diffs:     53
```

Active-word resampling:

```
Samples:             20000
Improving samples:   0
Best resample score: 96
```

All-word resampling:

```
Samples:             20000
Improving samples:   0
Best resample score: 98
```

## Interpretation

The score-86 candidate is not explained by its message XOR pattern alone.
The absolute message words matter. Preserving `M1 xor M2` while changing
the common-mode message content usually destroys the absorber quality.

This pushes the next search away from raw common-mode resampling and toward
schedule-aware moves that preserve specific late schedule behavior, not just
the initial message-word difference.
