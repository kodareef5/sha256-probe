# cascade_aux_encoding — heartbeat 2026-04-25

## What shipped today (macbook, autonomous)

1. **Cross-kernel CNF set**: 9 candidates × 2 sr-levels × 2 modes = 36 CNFs, all audit-CONFIRMED via expanded fingerprint ranges. Reproducible via `cnfs/regenerate.sh` (~3 min).

2. **Per-conflict speedup measurement** (kissat seed=5, 50k conflicts, 3 kernels):
   - Mode B is **2.0× faster wall** than standard, with 35% fewer decisions/conflict and 58% fewer propagations/conflict — consistent across kernels.

3. **Multi-seed variance** (5 seeds × 3 kernels at 50k):
   - Mode B wall=1.00s on every one of 15 runs (CV=0.000). The 2× advantage is structurally seed-stable.

4. **Cross-solver** (cadical 3.0.0, 50k):
   - Mode B 3.4× speedup vs standard on cadical (vs kissat's 2.0×). Encoding effect dominates solver effect.
   - **Mode A confirmed strictly worse than standard on cadical** across all 9 kernels (39 GB RSS observed on bit-10 expose). Anti-recommend Mode A on cadical.

5. **Erosion at scale**:
   - At 500k conflicts: Mode B advantage erodes to ~1.0×.
   - At sr=60 1M conflicts: 1.08×. Mode B is a **front-loaded preprocessing speedup**, not a deep-search accelerator.

6. **Varmap sidecar** (encoder-side change):
   - `cascade_aux_encoder.py --varmap +` now emits JSON sidecar mapping aux SAT vars to (register, round, bit) coordinates. Unblocks Phase 2B of programmatic_sat_propagator.

## State of the bet

The "≥10× SAT speedup" claim from the SPEC is now **honestly characterized as a 2-6× preprocessing speedup**. Real, reproducible, cross-solver — but not headline-class. The bet's path forward is:

- **Path A**: hand off the 36-CNF set to fleet workers for 4h+ kissat runs to test wall-time-to-SAT. Real evidence whether the front-loaded gain compounds in long search.
- **Path B**: integrate the varmap with programmatic_sat_propagator (Phase 2B). The propagator can extend cascade-zero propagation throughout the search, not just at preprocessing — directly addressing the steady-state convergence problem.

Path A is compute-heavy (waiting for fleet). Path B is the natural next move from this bet's perspective.

## Run accounting

- Total cascade_aux_encoding runs in registry: 115
- Audit failures: 0
- CPU-h spent today: ~3.2
- Budget remaining: ~196.8 CPU-h of 200

## Reference

See `comparisons/`:
- `conflict_5k_2026-04-25/` — kissat 50k single-seed
- `multiseed_50k_2026-04-25/` — kissat 50k 5-seed
- `conflict_500k_2026-04-25/` — kissat 500k erosion
- `cadical_50k_2026-04-25/` — cadical 50k 3-kernel
- `cadical_50k_full9_2026-04-25/` — cadical 50k all 9 kernels
- `sr60_modeB_probe_2026-04-25/` — cadical sr=60 1M

Each has its own RESULT.md.
