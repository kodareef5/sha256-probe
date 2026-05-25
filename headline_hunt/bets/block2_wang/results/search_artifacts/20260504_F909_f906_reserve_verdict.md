# F906_f788_alt_hw86_cg116_shape_reserve_beam Reserve Verdict

Verdict: **closed** - no better-than-init mixed low-net repair appeared.

| artifact | verdict | init | best | best shape | best mixed | final mixed |
| --- | --- | ---: | ---: | --- | --- | --- |
| `20260504_F906_f788_alt_hw86_cg116_shape_reserve_beam.json` | closed | 86 | 86 d0 | add0/remove0/net+0 | HW89 add4/remove2/net+2 lane[9,10,11,14,13,11,11,10] | HW93 add8/remove4/net+4 lane[13,10,17,9,13,7,12,12] |
| `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json` | pass | 86 | 78 d6 | add8/remove4/net+4 | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] | HW78 add8/remove4/net+4 lane[13,11,8,9,7,9,8,13] |
| `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json` | weak | 87 | 86 d5 | add10/remove0/net+10 | HW87 add5/remove3/net+2 lane[13,10,14,10,13,5,7,15] | HW91 add7/remove3/net+4 lane[13,16,11,12,11,5,10,13] |

## Extracted Mixed Candidates

- Count: 1
- Filter: HW <= 91, removed >= 1, net added <= 4
- Best extracted: HW89 add4_remove2_net+2 depth 3 lane[9,10,11,14,13,11,11,10]

## Next Action

Move to the next fresh reserve-triage target.

Suggested next fresh plan row: `20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_combo6.json` top_by_hw[2] HW87 target_l1 15 cg 131.0.

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00001040,0x00100000,0x0000400c,0x60105002,0x00000000,0x12001000,0x00800800,0x00200020,0x08000000,0x20024042,0x01808108,0x00000200,0x00000000,0x00050000,0x12018002,0x00001040 --init-hw 87 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out OUT.json --label LABEL
```
