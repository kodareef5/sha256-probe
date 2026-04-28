# F172/F173: bit19 radius-1 neighbor scan around bit3 winner
**2026-04-28**

## Summary

Macbook's F170 observation suggested scanning the radius-1 neighbors of
bit3's empirical winner `0,1,2,8,9` on the bit19 fixture. I added explicit
subset-list support to `active_subset_scan.py`, corrected the neighbor count,
and ran two 55-mask passes.

Result: at the same 3x4000 scan budget, no radius-1 neighbor beats the
current bit19 floor. The F135/F159 winner `0,1,3,8,9` remains the only mask
in this radius-1 family replayed at score 87 when seeded from the known F135
pair.

## Count correction

The radius-1 family has 55 unique masks, not 60. There are 5 removable base
words and 11 non-base replacements in a 16-word ground set:

```
5 * (16 - 5) = 55
```

Mask list:

```
headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F172_bit19_radius1_bit3_neighbor_masks.txt
```

## Tooling

`active_subset_scan.py` now accepts:

```bash
--subset-list PATH
```

It also accepts `--explicit-masks PATH` as an alias, matching the wording in
macbook's F172 coordination note. The file contains one comma/range active-word
mask per line, with `#` comments allowed. This lets future hypothesis-driven
subset tests run as targeted batches instead of being forced through
lexicographic chunk slices.

I also fixed the initialized scan path: `active_subset_scan.py` documented
`--init-json`, but did not forward `init_kicks` into `run_restart`, so an
initialized scan could crash. It now exposes and forwards `--init-kicks`.

## F172 independent pass

Command:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --subset-list headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F172_bit19_radius1_bit3_neighbor_masks.txt \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used --top 20 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F172_bit19_radius1_neighbors_55x3x4k.json
```

Runtime: 99.922 seconds for 55 masks.

Top results:

| Rank | Active words | Score | Msg diff HW |
|---:|---|---:|---:|
| 1 | `0,1,2,7,9` | 91 | 49 |
| 2 | `0,1,8,9,15` | 93 | 52 |
| 3 | `0,1,5,8,9` | 93 | 74 |
| 4 | `0,1,2,3,8` | 93 | 78 |
| 5 | `0,1,2,7,8` | 94 | 65 |
| 6 | `0,2,5,8,9` | 94 | 75 |
| 7 | `1,2,3,8,9` | 95 | 58 |
| 8 | `0,1,8,9,14` | 95 | 67 |
| 9 | `0,1,2,8,11` | 95 | 72 |
| 10 | `1,2,5,8,9` | 95 | 84 |

This pass is useful as extra stochastic evidence, but it is not directly
comparable to the chunked scan because explicit-list ordering changes each
mask's `subset_idx`, and therefore its seed schedule.

## F173 F135-initialized pass

The stronger test seeds restart 0 of every radius-1 neighbor from the known
F135 score-87 pair:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --subset-list headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F172_bit19_radius1_bit3_neighbor_masks.txt \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F135_bit19_fullpool_size5_chunk0064_64x3x4k.json \
  --top 20 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F173_bit19_radius1_neighbors_from_F135_55x3x4k.json
```

Runtime: 100.574 seconds for 55 masks.

Top results:

| Rank | Active words | Score | Msg diff HW |
|---:|---|---:|---:|
| 1 | `0,1,3,8,9` | 87 | 54 |
| 2 | `0,1,8,9,15` | 93 | 52 |
| 3 | `0,1,2,3,8` | 93 | 78 |
| 4 | `0,1,8,9,10` | 93 | 83 |
| 5 | `0,1,2,7,8` | 94 | 65 |
| 6 | `0,2,5,8,9` | 94 | 75 |
| 7 | `1,2,3,8,9` | 95 | 58 |
| 8 | `0,1,8,9,14` | 95 | 67 |
| 9 | `0,1,2,8,11` | 95 | 72 |
| 10 | `0,1,7,8,9` | 95 | 82 |

## Interpretation

The initialized pass replays `0,1,3,8,9` at score 87 and finds no equal or
better one-word swap at 3x4000. That makes the F135/F159 mask look like a
sharp local winner inside the F135 basin, not just one member of a broad
low-budget plateau.

The radius-1 hypothesis is therefore narrowed, but not fully closed:

- Best known bit19 mask remains `0,1,3,8,9` at score 87.
- Best alternate radius-1 mask under F135 initialization is score 93.
- Independent ordering pass also fails to find a sub-91 radius-1 alternate.
- Macbook's F172 budget-calibration note is right that definitive closure
  would require 8x50k continuations on either all 55 masks or at least the
  top-K low-budget candidates.

The next productive low-cost search is top-K continuation from this radius-1
batch, or full chunk coverage if the goal is global floor mapping. Radius-2 or
family-guided tests around `0,1,3,8,9` are the better next hypothesis path.
