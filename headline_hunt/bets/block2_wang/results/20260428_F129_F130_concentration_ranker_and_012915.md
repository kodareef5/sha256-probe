# F129/F130: concentration ranker finds a score-91 neighbor, not a new floor
**2026-04-28**

## Summary

F128 showed that raw expansion-overlap density did not predict better active
word masks. F129 adds a structural ranker that scores concentration, early
fan-in, and feed-channel mixing instead of only total extra feeds.

New tool:

```
headline_hunt/bets/block2_wang/encoders/rank_active_word_subsets.py
```

The ranker generated a top concentration slate. Sixteen high-ranked
previously unobserved masks were scanned at the same strict 3 x 4k budget.
The best new mask was:

```
0,1,2,9,15: score 93, msgHW 80
```

F130 continued that mask for 8 x 50k and improved it to:

```
0,1,2,9,15: score 91, msgHW 83
```

That is live enough to keep, but it still does not challenge the current
score-86 `0,1,2,8,9` lane.

## Ranker

The ranker enumerates message-word subsets and computes one-hop message
expansion structure:

```
W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]
```

Recorded features include:

1. Total extra feeds into overlapped schedule words.
2. Early extra feeds through W24.
3. Max fan-in and early max fan-in.
4. Triple-overlap targets.
5. Mixed identity/nonlinear feed channels.

Command:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/rank_active_word_subsets.py \
  --pool 0-15 --sizes 5 --top 40 --json-limit 120 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F129_active_word_concentration_rank_top120.json \
  --observed-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F11*_active_*.json \
                  headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F12*_bit3_active_*.json \
                  headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F128_overlap_*_3x4k.json
```

Useful ranker sanity checks after adding the new F129/F130 observations:

```
rank  17: 0,1,2,9,15  observed 91/83
rank  21: 1,2,3,11,15 observed 95/73
rank  22: 1,2,6,7,15  observed 96/81
rank 107: 0,1,2,8,9   observed 86/78
```

The ranker is better than pure density at surfacing some near lanes, but it
still does not rank the real score-86 winner near the top.

## F129 scan results

Each mask was scanned as one strict active subset:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool SUBSET --sizes 5 --restarts 3 --iterations 4000 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F129_concentration_SUBSET_3x4k.json
```

| Active words | Best score | Msg diff HW | Schedule words |
|---|---:|---:|---:|
| `0,1,2,9,15` | 93 | 80 | 53 |
| `1,2,3,11,15` | 95 | 73 | 53 |
| `1,2,6,7,15` | 96 | 81 | 53 |
| `0,1,9,10,15` | 99 | 56 | 53 |
| `1,2,3,10,11` | 99 | 63 | 53 |
| `5,6,7,14,15` | 99 | 63 | 53 |
| `0,5,6,9,14` | 100 | 83 | 51 |
| `1,2,9,10,14` | 100 | 86 | 53 |
| `0,1,10,14,15` | 101 | 56 | 53 |
| `1,5,6,9,14` | 101 | 81 | 53 |
| `2,3,4,11,12` | 101 | 78 | 52 |
| `3,4,5,12,13` | 101 | 67 | 51 |
| `4,5,6,13,14` | 101 | 83 | 52 |
| `2,3,10,11,15` | 102 | 68 | 52 |
| `0,1,2,14,15` | 104 | 85 | 53 |
| `1,2,9,14,15` | 104 | 82 | 53 |

The headline result is that concentration ranking found one useful neighbor,
not a better floor.

## F130 continuation

Continuation command:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 4101 \
  --active-words 0,1,2,9,15 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F129_concentration_0_1_2_9_15_3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F130_bit3_active_012915_continue_8x50k.json
```

Result:

```
Best target distance: 91
Best msg diff HW:    83
Nonzero W diffs:     53
Final chain diff:    0x03411d23 0x20022901 0xbce9804f 0x18ca06c2 0x4948f2e1 0xa87995c2 0xa904a890 0x15404881
```

Additive common-mode radius-2 probe:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F130_bit3_active_012915_continue_8x50k.json \
  --active-words 0,1,2,9,15 --mode add_common --radius 2 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F130_bit3_active_012915_addcommon_radius2_probe.json
```

Result:

```
Base score:          91
Candidates:          51200
Skipped no-op moves: 160
Improving moves:     0
Best real move:      score 95
```

The probe tool now skips additive radius-2 no-op pairs such as `+2^b` and
`-2^b` on the same word/bit. Earlier probes were still valid for improvement
counts, but their top neutral move lists could include these cancellations.

## Interpretation

The new score-91 lane shares `0,1,2,9` with the score-86 lane and swaps
word 8 for word 15. That makes the miss more informative than the F128
high-density misses.

What the ranker captures:

1. Early W16/W17 triple-overlap geometry.
2. Mixed identity and nonlinear feed channels.
3. Nearby masks that can reach the low 90s.

What it still misses:

1. The specific `W24` phase created by word 8 in `0,1,2,8,9`.
2. The interaction between active-word geometry and the bit3 trail state.
3. Actual bit-level carry behavior inside the additive schedule.

Next useful direction: add a fixture-conditioned feature to the ranker. Pure
word geometry should be combined with measured early schedule-diff quality
under cheap random samples for each mask, especially around W16, W17, and W24.
