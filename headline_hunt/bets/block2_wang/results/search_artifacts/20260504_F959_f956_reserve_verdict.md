# F956_f952_hw87_mixed_deepen_reserve Reserve Verdict

Verdict: **closed** - no better-than-init mixed low-net repair appeared.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F956_f952_hw87_mixed_deepen_reserve.json` | closed | 87 | 87 d0 | add0/remove0/net+0 | HW88 add3/remove1/net+2 lane[11,10,10,9,13,9,14,12] | HW89 add8/remove4/net+4 lane[6,6,12,15,9,15,14,12] |
| `20260504_F952_f793_top_by_hw2_hw89_shape_reserve_beam.json` | pass | 89 | 87 d4 | add6/remove2/net+4 | HW87 add6/remove2/net+4 lane[8,15,13,11,7,9,10,14] | HW90 add8/remove4/net+4 lane[8,13,12,9,13,12,14,9] |
| `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` | pass | 88 | 87 d6 | add7/remove5/net+2 | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] |
| `20260504_F935_f788_top_by_hw5_hw88_shape_reserve_beam.json` | weak | 88 | 83 d3 | add6/remove0/net+6 | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |

## Extracted Mixed Candidates

- Count: 5
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW88 add3_remove1_net+2 depth 2 lane[11,10,10,9,13,9,14,12]

## Next Action

Move to the next fresh reserve-triage target.
