# F927_f923_hw87_mixed_deepen_reserve Reserve Verdict

Verdict: **closed** - no better-than-init mixed low-net repair appeared.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F927_f923_hw87_mixed_deepen_reserve.json` | closed | 87 | 87 d0 | add0/remove0/net+0 | HW90 add8/remove4/net+4 lane[8,11,12,13,16,13,6,11] | HW90 add8/remove4/net+4 lane[8,11,12,13,16,13,6,11] |
| `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` | pass | 88 | 87 d6 | add7/remove5/net+2 | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |
| `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json` | weak | 87 | 86 d5 | add10/remove0/net+10 | HW87 add5/remove3/net+2 lane[13,10,14,10,13,5,7,15] | HW91 add7/remove3/net+4 lane[13,16,11,12,11,5,10,13] |

## Extracted Mixed Candidates

- Count: 6
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW90 add5_remove1_net+4 depth 3 lane[12,11,8,13,7,11,14,14]

## Next Action

Move to the next fresh reserve-triage target.
