# F948_f788_top_by_hw6_hw89_shape_reserve_beam Reserve Verdict

Verdict: **closed** - no better-than-init mixed low-net repair appeared.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F948_f788_top_by_hw6_hw89_shape_reserve_beam.json` | closed | 89 | 89 d0 | add0/remove0/net+0 | HW90 add6/remove2/net+4 lane[14,11,9,9,11,15,9,12] | HW93 add8/remove4/net+4 lane[11,12,16,12,7,11,14,10] |
| `20260504_F935_f788_top_by_hw5_hw88_shape_reserve_beam.json` | weak | 88 | 83 d3 | add6/remove0/net+6 | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] |
| `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` | pass | 88 | 87 d6 | add7/remove5/net+2 | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |
| `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json` | weak | 87 | 86 d5 | add10/remove0/net+10 | HW87 add5/remove3/net+2 lane[13,10,14,10,13,5,7,15] | HW91 add7/remove3/net+4 lane[13,16,11,12,11,5,10,13] |

## Extracted Mixed Candidates

- Count: 4
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW90 add5_remove1_net+4 depth 3 lane[4,8,11,13,13,10,15,16]

## Next Action

Move to the next fresh reserve-triage target.

Suggested next fresh plan row: `20260504_F793_bit24_f789_hw78_unfiltered_pair6_sample5m_combo6.json` top_by_hw[2] HW89 target_l1 15 cg 125.0.

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00805000,0x21000080,0x00004004,0x44146000,0xa0010104,0x10001000,0x08030001,0x00200088,0x08006418,0x20020040,0x00008108,0x00010000,0x06080000,0x00240020,0x12018002,0x02000040 --init-hw 89 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out OUT.json --label LABEL
```
