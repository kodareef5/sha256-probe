# F127: additive common-mode move improves score-86 absorber sparsity
**2026-04-28**

## Summary

F123-F126 ruled out several escape routes from the score-86 block-2
absorber basin:

- raw one/two-bit M2 moves
- raw two-sided M1/M2 moves
- common-mode XOR moves
- fixed-diff resampling

F127 tests a more schedule-natural local move: paired modular add/sub
changes to M1 and M2. This does not improve the target distance, but it
does improve the best score-86 candidate's message-diff HW.

New best Pareto point in the score-86 basin:

```
Target distance:     86
Message diff HW:     78
Active words:        0,1,2,8,9
Nonzero W diffs:     53
```

The previous score-86 point had message diff HW 80.

## Tool update

`probe_absorption_neighborhood.py` now supports:

```
--mode add_common
```

This probes paired modular moves:

```
M1[word] += +/- 2^bit
M2[word] += +/- 2^bit
```

That is different from common-mode XOR. It is a better fit for the
additive structure in SHA-256's message schedule.

## Additive common-mode probe

Command:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --active-words 0,1,2,8,9 \
  --radius 2 \
  --mode add_common \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F127_bit3_active_01289_addcommon_radius2_probe.json
```

Archived artifact:

```
results/search_artifacts/20260428_F127_bit3_active_01289_addcommon_radius2_probe.json
```

Result:

```
Base score:          86
Base msg diff HW:    80
Candidates:          51360
Improving moves:     0
Best equal-score HW: 78
```

Best move:

```
ADW1b15+, ADW1b25-
```

That means:

```
M1[1] += 0x00008000
M2[1] += 0x00008000
M1[1] -= 0x02000000
M2[1] -= 0x02000000
```

This keeps the score at 86 and reduces the message-diff HW from 80 to 78.

## Continuation from HW78 seed

`search_block2_absorption.py` now loads `top` candidates from probe/resample
artifacts, sorting ties by message-diff HW. That lets the HW78 candidate
seed the stochastic search directly.

Command:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 1919 \
  --active-words 0,1,2,8,9 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F127_bit3_active_01289_addcommon_radius2_probe.json \
  --init-use all \
  --hw-penalty 0.03 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F127_bit3_active_01289_hw78_continue_8x50k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F127_bit3_active_01289_hw78_continue_8x50k.json
```

Result:

```
Best target distance: 86
Best msg diff HW:    78
Best objective:      88.34
```

No lower objective was found.

## Radius-2 check of HW78 seed

Command:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F127_bit3_active_01289_hw78_continue_8x50k.json \
  --active-words 0,1,2,8,9 \
  --radius 2 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F127_bit3_active_01289_hw78_radius2_probe.json
```

Archived artifact:

```
results/search_artifacts/20260428_F127_bit3_active_01289_hw78_radius2_probe.json
```

Result:

```
Base score:          86
Base msg diff HW:    78
Candidates:          12880
Improving moves:     0
Best neighbor score: 97
```

## Replayable candidate

M1:

```
0xf0268c20 0x32ba7725 0xab2127c5 0x8bbfa559
0xfc1dae5f 0x5b142d31 0x0713f3ca 0xc61c61a8
0x71fe880c 0xb6be8846 0x54cd3828 0x6c2887a1
0xa6c4d1d6 0x75085133 0xadd05863 0x017220f8
```

M2:

```
0x29bb3226 0x029ef889 0x7d80c4e8 0x8bbfa559
0xfc1dae5f 0x5b142d31 0x0713f3ca 0xc61c61a8
0xd9fb2baa 0xf9138d30 0x54cd3828 0x6c2887a1
0xa6c4d1d6 0x75085133 0xadd05863 0x017220f8
```

Final chain diff:

```
0xac302928 0x743c0009 0xae56884b 0xa020a516
0xc681180b 0xc8846151 0xc2c48401 0x20a42a09
```

## Interpretation

Additive common-mode movement is the first local operator to improve the
quality of the score-86 absorber, even though it only improves sparsity and
not target distance. This supports the earlier read: raw random movement is
weak, but schedule-shaped moves can still extract useful refinements.

Next useful step: search additive common-mode neighborhoods with an
objective that explicitly includes message-diff HW, or lift the same idea
from message words to selected late schedule words.
