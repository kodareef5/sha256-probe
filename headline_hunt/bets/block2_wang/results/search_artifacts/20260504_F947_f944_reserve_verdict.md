# F944_f935_hw83_removal_biased_reserve Reserve Verdict

Verdict: **closed** - no better-than-init mixed low-net repair appeared.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F944_f935_hw83_removal_biased_reserve.json` | closed | 83 | 83 d0 | add0/remove0/net+0 | HW88 add7/remove5/net+2 lane[13,11,11,9,12,13,9,10] | HW88 add7/remove5/net+2 lane[13,11,11,9,12,13,9,10] |
| `20260504_F939_f935_hw83_pure_add_deepen_reserve.json` | closed | 83 | 83 d0 | add0/remove0/net+0 | HW90 add5/remove1/net+4 lane[12,8,14,13,16,9,8,10] | HW92 add6/remove6/net+0 lane[13,11,13,8,16,6,8,17] |
| `20260504_F935_f788_top_by_hw5_hw88_shape_reserve_beam.json` | weak | 88 | 83 d3 | add6/remove0/net+6 | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] |
| `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` | pass | 88 | 87 d6 | add7/remove5/net+2 | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |

## Extracted Mixed Candidates

- Count: 3
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW88 add7_remove5_net+2 depth 6 lane[13,11,11,9,12,13,9,10]

## Next Action

Move to the next fresh reserve-triage target.
