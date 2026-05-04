# F935_f788_top_by_hw5_hw88_shape_reserve_beam Reserve Verdict

Verdict: **weak** - run improved, but not through the calibrated final mixed-low-net channel.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F935_f788_top_by_hw5_hw88_shape_reserve_beam.json` | weak | 88 | 83 d3 | add6/remove0/net+6 | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] | HW89 add8/remove4/net+4 lane[8,12,11,12,8,12,11,15] |
| `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` | pass | 88 | 87 d6 | add7/remove5/net+2 | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |
| `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json` | weak | 87 | 86 d5 | add10/remove0/net+10 | HW87 add5/remove3/net+2 lane[13,10,14,10,13,5,7,15] | HW91 add7/remove3/net+4 lane[13,16,11,12,11,5,10,13] |

## Extracted Mixed Candidates

- Count: 4
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW89 add8_remove4_net+4 depth 6 lane[8,12,11,12,8,12,11,15]

## Next Action

Treat as a weak false-positive unless a short deepen from the best mixed candidate improves.

Suggested next fresh plan row: `20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_combo6.json` top_by_hw[6] HW89 target_l1 9 cg 129.0.

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00001000,0x00100000,0x0008400c,0x00105002,0x00000200,0x10001000,0x00000000,0x00200000,0x08082000,0x20020040,0x09808108,0x00000008,0x00040002,0x10051000,0x12018002,0x02000040 --init-hw 89 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out OUT.json --label LABEL
```
