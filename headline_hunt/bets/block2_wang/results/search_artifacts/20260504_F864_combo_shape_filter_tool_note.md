# F864 Combo Shape Filter Tool Note

`m2_target_pair_combo.py` now records M2 transition shape for each combo record:

- `m2_added_bits`
- `m2_removed_bits`
- `m2_net_added_bits`

It also accepts optional pre-evaluation filters:

- `--min-m2-added`
- `--max-m2-added`
- `--min-m2-removed`
- `--max-m2-removed`
- `--min-m2-net-added`
- `--max-m2-net-added`

The filter counter is `skipped_m2_shape_signature`.

Why this matters:

The current portfolio probes show that local continuation and simple transfer
are mostly closed. The next upstream detour selector needs to avoid pure-add
overfill when that is not the intended regime. These flags make it possible to
sample combo detours with explicit M2 shape constraints before spending repair
beam time.

Smoke test:

```text
F851 bit18->bit14 atlas
sample_combos=1000
pair_count=3
min_m2_removed=1
max_m2_net_added=4
evaluated=69
skipped_m2_shape_signature=870
```

The smoke output verified that shaped entries carry the new fields and that the
filter rejects over-additive combinations before SHA evaluation.
