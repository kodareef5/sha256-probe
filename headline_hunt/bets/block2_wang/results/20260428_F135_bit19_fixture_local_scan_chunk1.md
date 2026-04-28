# F135: second bit19 scan slice finds a score-87 mask
**2026-04-28**

## Summary

F134 made the bit19 size-5 active subset scan resumable and ran the first
64-mask slice, improving bit19 from score 93 to score 90. F135 continues the
fixture-local scan at `--start-index 64`.

The second slice found a much stronger bit19-local mask:

```
Active words: 0,1,3,8,9
Best score:   87
Msg diff HW:  54
```

This is one point above the current bit3 score-86 lane and far stronger than
the transferred-mask bit19 tests from F132. It is the clearest support so far
for F156's fixture-local optimization conclusion.

## Chunk Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 64 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used --top 16 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F135_bit19_fullpool_size5_chunk0064_64x3x4k.json
```

Runtime was 123.147 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,1,3,8,9` | 87 | 54 | 53 |
| 2 | `0,1,3,8,10` | 92 | 77 | 53 |
| 3 | `0,1,3,5,8` | 96 | 55 | 53 |
| 4 | `0,1,3,5,9` | 96 | 67 | 53 |
| 5 | `0,1,2,13,14` | 96 | 70 | 53 |
| 6 | `0,1,3,6,11` | 96 | 70 | 53 |
| 7 | `0,1,3,4,14` | 96 | 80 | 53 |
| 8 | `0,1,3,5,10` | 97 | 51 | 53 |
| 9 | `0,1,2,11,15` | 97 | 63 | 53 |
| 10 | `0,1,3,6,14` | 97 | 65 | 53 |

The chunk's Pareto frontier:

```
score 87, msgHW 54, active 0,1,3,8,9
score 97, msgHW 51, active 0,1,3,5,10
score 100, msgHW 46, active 0,1,3,4,13
score 101, msgHW 55, actual active 1,3,4,5
```

## Continuation

The score-87 mask was continued:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 7301 \
  --active-words 0,1,3,8,9 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F135_bit19_fullpool_size5_chunk0064_64x3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F135_bit19_active_01389_continue_8x50k.json
```

The continuation did not improve:

```
Best target distance: 87
Best msg diff HW:    54
Nonzero W diffs:     53
Final chain diff:    0x0ed01f50 0x842990fc 0x04800154 0x840dc020 0x816fc0b4 0x30da5842 0x40ce8252 0x2218520b
```

## Additive Neighborhood

Additive common-mode radius 2 around the score-87 point:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F135_bit19_active_01389_continue_8x50k.json \
  --active-words 0,1,3,8,9 --mode add_common --radius 2 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F135_bit19_active_01389_addcommon_radius2_probe.json
```

Result:

```
Base score:          87
Candidates:          51200
Skipped no-op moves: 160
Improving moves:     0
Best real move:      score 96
```

## Interpretation

This partially rehabilitates the bit19 fixture after F132. Bit19 did not look
good when evaluated with transferred bit3 masks, but a fixture-local scan found
a mask within one point of bit3's best after only 128 of 4,368 size-5 masks.

The active mask `0,1,3,8,9` is close to bit3's `0,1,2,8,9`, replacing word 2
with word 3. That is a narrower and more useful structural signal than the
failed broad priors: preserve the `0,1,*,8,9` temporal shape, but let the
fixture choose the third early word.

Next useful step: continue the bit19 full-pool scan at `--start-index 128`.
