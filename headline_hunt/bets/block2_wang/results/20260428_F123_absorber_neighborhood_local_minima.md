# F123: compact absorbers are strict radius-2 local minima
**2026-04-28**

## Summary

F111/F112 found compact block-2 absorber candidates, led by a score-86
candidate on active message words 0,1,2,8,9. Random one-kick continuations
did not improve it and usually failed to return to the score-86 basin.

F123 makes that local statement deterministic: exhaustively probe all
one-bit and two-bit flips over each candidate's active message words.

Result: every tested Pareto candidate is a strict radius-2 local minimum.
No one-bit or two-bit message move improves the target distance.

## New tool

New script:

```
headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py
```

It loads a saved search/subset artifact, fixes M1, then evaluates all
one-bit and two-bit flips in selected M2 message words. It also supports
`--side both`, which probes bit flips in both M1 and M2 while preserving
the chosen active word set. `--mode common` probes paired common-mode flips
in both M1 and M2, preserving the immediate W0..15 message-word XOR diff.

For each move it records:

- final chain-output target distance
- message-diff HW
- active message words
- nonzero schedule words
- final chain diff

## Results

All probes used the F106 bit3 HW55 fixture:

```
headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json
```

Radius-2 summary:

```
active words       base  msgHW  candidates  improving  best neighbor
0,1,2,8,9            86     80       12880          0             95
0,1,8,14             90     75        8256          0             98
0,1,6,10,13          90     67       12880          0             99
0,1,2,10,13          90     70       12880          0             94
0,1,11               91     26        4656          0            102
7,12                 94     29        2080          0             99
```

Archived artifacts:

```
results/search_artifacts/20260428_F123_bit3_active_01289_radius2_probe.json
results/search_artifacts/20260428_F123_bit3_active_01814_radius2_probe.json
results/search_artifacts/20260428_F123_bit3_active_0161013_radius2_probe.json
results/search_artifacts/20260428_F123_bit3_active_0121013_radius2_probe.json
results/search_artifacts/20260428_F123_bit3_active_011_radius2_probe.json
results/search_artifacts/20260428_F123_bit3_active_0712_radius2_probe.json
```

## Score-86 probe

Command:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --active-words 0,1,2,8,9 \
  --radius 2 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F123_bit3_active_01289_radius2_probe.json
```

Result:

```
Base score:          86
Base msg diff HW:    80
Base message words:  5
Base schedule words: 53
Candidates:          12880
Improving moves:     0
Best neighbor score: 95
```

The best two-bit neighbor is still 9 bits worse than the seed:

```
score 95, flips W1b16,W9b30
```

## Two-sided score-86 probe

The first radius-2 pass fixed M1 and perturbed M2. A stronger control also
perturbed M1:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --active-words 0,1,2,8,9 \
  --radius 2 \
  --side both \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F124_bit3_active_01289_radius2_twosided_probe.json
```

Archived artifact:

```
results/search_artifacts/20260428_F124_bit3_active_01289_radius2_twosided_probe.json
```

Result:

```
Base score:          86
Positions:           320
Candidates:          51360
Improving moves:     0
Best neighbor score: 95
```

So the score-86 candidate is not just M2-local. It is also a strict
radius-2 local minimum under two-sided M1/M2 bit moves over its active
message words.

## Common-mode score-86 probe

Blind M2 kicks and raw two-sided moves both failed. A more structured local
move is a common-mode bit flip: flip the same M1 and M2 bit, preserving the
message-word XOR difference in W0..15 while changing the absolute block-2
messages.

Command:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --active-words 0,1,2,8,9 \
  --radius 2 \
  --mode common \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F125_bit3_active_01289_common_radius2_probe.json
```

Archived artifact:

```
results/search_artifacts/20260428_F125_bit3_active_01289_common_radius2_probe.json
```

Result:

```
Base score:          86
Candidates:          12880
Improving moves:     0
Best neighbor score: 100
```

Even common-mode moves that preserve the immediate message XOR difference
do not escape the basin at radius 2.

## Interpretation

The compact absorber candidates are not sitting next to obvious bit-level
improvements. The score-86 point is especially isolated: all one- and
two-bit M2-only moves over its five active message words make it worse,
the same remains true when M1 moves are included, and common-mode paired
moves are worse still.

That changes the next step. More random kicks are low value unless the move
operator is changed. Productive follow-up should use structured moves that
preserve late-schedule features, or a solver that reasons directly over
schedule words W16-W30 instead of raw message-bit flips.
