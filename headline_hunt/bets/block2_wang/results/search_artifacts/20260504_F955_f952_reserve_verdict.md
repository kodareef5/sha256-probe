# F952_f793_top_by_hw2_hw89_shape_reserve_beam Reserve Verdict

Verdict: **pass** - mixed low-net reserve reached a better-than-init HW.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F952_f793_top_by_hw2_hw89_shape_reserve_beam.json` | pass | 89 | 87 d4 | add6/remove2/net+4 | HW87 add6/remove2/net+4 lane[8,15,13,11,7,9,10,14] | HW90 add8/remove4/net+4 lane[8,13,12,9,13,12,14,9] |
| `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` | pass | 88 | 87 d6 | add7/remove5/net+2 | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] |
| `20260504_F935_f788_top_by_hw5_hw88_shape_reserve_beam.json` | weak | 88 | 83 d3 | add6/remove0/net+6 | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |
| `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json` | weak | 87 | 86 d5 | add10/remove0/net+10 | HW87 add5/remove3/net+2 lane[13,10,14,10,13,5,7,15] | HW91 add7/remove3/net+4 lane[13,16,11,12,11,5,10,13] |

## Extracted Mixed Candidates

- Count: 6
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW87 add6_remove2_net+4 depth 4 lane[8,15,13,11,7,9,10,14]

## Next Action

Deepen from the best extracted mixed candidate before moving to the next fresh triage target.
