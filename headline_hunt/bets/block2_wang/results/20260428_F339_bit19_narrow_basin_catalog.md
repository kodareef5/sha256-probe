# F339: bit19 narrow-basin catalog after F335/F337
**2026-04-28**

## Summary

F276/F277 add independent seed-5001 checks for the new Yale basins:

- F335 `1,3,5,6,11`: seed5001 reaches 92, while seed7101/chunk-init holds 88.
- F337 `1,3,6,8,12`: seed5001 reaches 92, while seed7101/chunk-init holds 90.

That confirms the same pattern seen in F248/F301: chunk-discovered low scores
are real enough to preserve under init continuation, but they are not robust
random-init floors.

Machine-readable catalog:

`headline_hunt/bets/block2_wang/results/20260428_F339_bit19_narrow_basin_catalog.json`

## Catalog

| ID | Chunk | Active words | Best score | Contains `{1,3}` | Seed notes |
|---|---:|---|---:|---|---|
| F135 | 1 | `0,1,3,8,9` | 87 | yes | seed-7101 narrow-basin floor |
| F335 | 26 | `1,3,5,6,11` | 88 | yes | seed7101/chunk-init=88, seed9001=95, seed5001=92 |
| F248 | 19 | `0,7,9,12,14` | 90 | no | seed7101/chunk-init=90 |
| F301 | 21 | `1,2,3,4,15` | 90 | yes | seed7101/chunk-init=90, seed9001=93 |
| F337 | 27 | `1,3,6,8,12` | 90 | yes | seed7101/chunk-init=90, seed9001=92, seed5001=92 |

## Interpretation

Four of five bit19 narrow basins contain active words `{1,3}`. That is a useful
lead, not a theorem: F248 is a genuine outlier, and the non-7101 checks still
land in the 92-95 range rather than reproducing the sub-90 points.

The practical conclusion is to stop treating every size-5 chunk hit as equally
informative. The next targeted probes should separate:

- `{1,3}`-anchored search behavior,
- F248-style outlier behavior,
- seed-7101/init artifacts versus robust multi-seed floors.

## Next probes

- Run a forced-`{1,3}` size-5/6 scan with diverse seeds instead of seed7101 only.
- Run radius-1/radius-2 mask neighborhoods around F335 and F337 under seed5001/9001.
- Keep F248 as an outlier control when testing any `{1,3}` structural explanation.
