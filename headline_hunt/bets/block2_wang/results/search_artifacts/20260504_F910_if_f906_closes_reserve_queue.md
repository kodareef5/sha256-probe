# Materialized M2 Reserve Commands

| run | source | group | HW | target L1 | cg | shape | out |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| F911 | `20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_combo6.json` | top_by_hw[2] | 87 | 15 | 131.0 | add11/remove1/net+10 | `20260504_F911_f788_top_by_hw2_hw87_shape_reserve_beam.json` |
| F915 | `20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_combo6.json` | top_by_hw[3] | 87 | 17 | 125.0 | add12/remove0/net+12 | `20260504_F915_f788_top_by_hw3_hw87_shape_reserve_beam.json` |
| F919 | `20260504_F793_bit24_f789_hw78_unfiltered_pair6_sample5m_combo6.json` | top_by_hw[1] | 88 | 20 | 130.0 | add12/remove0/net+12 | `20260504_F919_f793_top_by_hw1_hw88_shape_reserve_beam.json` |
| F923 | `20260504_F788_bit24_f760_hw82_overlap_pair6_sample20m_combo6.json` | top_by_hw[4] | 88 | 22 | 118.0 | add11/remove0/net+11 | `20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json` |
| F927 | `20260504_F799_bit24_f760_hw82_overlap_late_early_pair6_sample5m_combo6.json` | top_by_hw[1] | 88 | 22 | 142.0 | add10/remove1/net+9 | `20260504_F927_f799_top_by_hw1_hw88_shape_reserve_beam.json` |

## Commands

### F911_f788_top_by_hw2_hw87_shape_reserve_beam

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00001040,0x00100000,0x0000400c,0x60105002,0x00000000,0x12001000,0x00800800,0x00200020,0x08000000,0x20024042,0x01808108,0x00000200,0x00000000,0x00050000,0x12018002,0x00001040 --init-hw 87 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F911_f788_top_by_hw2_hw87_shape_reserve_beam.json --label F911_f788_top_by_hw2_hw87_shape_reserve_beam
```

### F915_f788_top_by_hw3_hw87_shape_reserve_beam

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00021240,0x00100000,0x04004004,0x40105002,0x00000000,0x10001000,0x00100000,0x00200000,0x88002000,0x30020040,0x01808108,0x00000000,0x00200000,0x00050000,0x12018122,0x01008040 --init-hw 87 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F915_f788_top_by_hw3_hw87_shape_reserve_beam.json --label F915_f788_top_by_hw3_hw87_shape_reserve_beam
```

### F919_f793_top_by_hw1_hw88_shape_reserve_beam

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00805010,0x21000080,0x00004204,0x60146000,0x00000144,0x10001200,0x00010001,0x00200080,0x08046418,0x60020040,0x00808108,0x00010000,0x06000002,0x06240020,0x12018002,0x00000040 --init-hw 88 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F919_f793_top_by_hw1_hw88_shape_reserve_beam.json --label F919_f793_top_by_hw1_hw88_shape_reserve_beam
```

### F923_f788_top_by_hw4_hw88_shape_reserve_beam

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00001000,0x00102000,0x00004044,0x41105002,0x00000000,0x10041000,0x00041000,0x00200000,0x08002000,0x20020040,0x01808108,0x00028000,0x00001000,0x00050000,0x12018102,0x00010040 --init-hw 88 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F923_f788_top_by_hw4_hw88_shape_reserve_beam.json --label F923_f788_top_by_hw4_hw88_shape_reserve_beam
```

### F927_f799_top_by_hw1_hw88_shape_reserve_beam

```bash
python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260503_F547_pathC_absorber_seeds.jsonl --rank 1 --rounds 24 --init-M2 0x00001000,0x00100000,0x00004004,0x40105012,0x08000000,0x10001040,0x00220802,0x00200000,0x08000000,0x20020040,0x01848108,0x00000000,0x00000000,0x00050040,0x12018002,0x02000040 --init-hw 88 --pair-pool 1024 --beam-width 1024 --reserve-low-net-width 384 --reserve-low-net-max 4 --reserve-low-net-min-removed 1 --reserve-removed-width 128 --reserve-removed-min 2 --max-pairs 6 --max-radius 12 --top-records 30 --out headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F927_f799_top_by_hw1_hw88_shape_reserve_beam.json --label F927_f799_top_by_hw1_hw88_shape_reserve_beam
```
