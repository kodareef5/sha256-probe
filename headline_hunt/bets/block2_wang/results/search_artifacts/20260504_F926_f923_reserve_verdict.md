# F923_f788_top_by_hw4_hw88_shape_reserve_beam Reserve Verdict

Verdict: **pass** - mixed low-net reserve reached a better-than-init HW.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` | pass | 88 | 87 d6 | add7/remove5/net+2 | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] | HW87 add7/remove5/net+2 lane[8,8,14,13,10,11,14,9] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |
| `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json` | weak | 87 | 86 d5 | add10/remove0/net+10 | HW87 add5/remove3/net+2 lane[13,10,14,10,13,5,7,15] | HW91 add7/remove3/net+4 lane[13,16,11,12,11,5,10,13] |

## Extracted Mixed Candidates

- Count: 8
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW87 add7_remove5_net+2 depth 6 lane[8,8,14,13,10,11,14,9]

## Next Action

Deepen from the best extracted mixed candidate before moving to the next fresh triage target.

Suggested next fresh plan row: `20260504_F799_bit24_f760_hw82_overlap_late_early_pair6_sample5m_combo6.json` top_by_hw[1] HW88 target_l1 22 cg 142.0.

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00001000,0x00100000,0x00004004,0x40105012,0x08000000,0x10001040,0x00220802,0x00200000,0x08000000,0x20020040,0x01848108,0x00000000,0x00000000,0x00050040,0x12018002,0x02000040 --init-hw 88 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out OUT.json --label LABEL
```
