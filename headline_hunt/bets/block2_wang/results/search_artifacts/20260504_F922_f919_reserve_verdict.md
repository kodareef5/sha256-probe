# F919_f793_top_by_hw1_hw88_shape_reserve_beam Reserve Verdict

Verdict: **closed** - no better-than-init mixed low-net repair appeared.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F919_f793_top_by_hw1_hw88_shape_reserve_beam.json` | closed | 88 | 88 d0 | add0/remove0/net+0 | HW90 add7/remove3/net+4 lane[10,10,12,9,14,10,14,11] | HW95 add8/remove4/net+4 lane[14,13,12,14,13,8,12,9] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |
| `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json` | weak | 87 | 86 d5 | add10/remove0/net+10 | HW87 add5/remove3/net+2 lane[13,10,14,10,13,5,7,15] | HW91 add7/remove3/net+4 lane[13,16,11,12,11,5,10,13] |

## Extracted Mixed Candidates

- Count: 5
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW90 add7_remove3_net+4 depth 5 lane[10,10,12,9,14,10,14,11]

## Next Action

Move to the next fresh reserve-triage target.

Suggested next fresh plan row: `20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_combo6.json` top_by_hw[4] HW88 target_l1 22 cg 118.0.

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00001000,0x00102000,0x00004044,0x41105002,0x00000000,0x10041000,0x00041000,0x00200000,0x08002000,0x20020040,0x01808108,0x00028000,0x00001000,0x00050000,0x12018102,0x00010040 --init-hw 88 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out OUT.json --label LABEL
```
