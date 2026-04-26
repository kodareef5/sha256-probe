# Mode A vs Mode B on bit=20 NEW candidate — kissat 1M conflicts
**2026-04-26 07:25 EDT** — cascade_aux_encoding bet — fresh evidence.

## Setup

`cand_n32_bit20_m294e1ea8_fillffffffff` is one of the queue8-discovered
candidates (registered 2026-04-26). Notably structurally interesting:
- hardlock_bits = 15 (high — only bit=11 m=0x56076c68 has higher at 16)
- de58_size = 8187
- hw56 = 115

Generated 2 cascade-aux variants this session (post-audit-rot fix):
- `aux_expose_sr61_n32_bit20_m294e1ea8_fillffffffff.cnf` (Mode A)
- `aux_force_sr61_n32_bit20_m294e1ea8_fillffffffff.cnf` (Mode B)

Both 13502 vars / 56072 clauses, audit CONFIRMED in sr61 fingerprint range.

## Result

| Mode | wall | status | run_id |
|---|---|---|---|
| A (expose) | 39.36s | s UNKNOWN | run_20260426_112551_..._8b38e220 |
| B (force)  | 38.10s | s UNKNOWN | run_20260426_112551_..._d97fdd1c |

**Mode B speedup vs Mode A: 1.03×** (negligible).

## Compare to prior characterization

The cascade_aux_encoding bet's prior data (pre-pause, partially audit-rot
affected) showed Mode B 2-3.4× faster than Mode A at 50k conflicts on a
9-kernel sweep. The 500k confirmation showed convergence (Mode B's
front-loaded preprocessing eroded by 500k).

This 2026-04-26 measurement at 1M conflicts on a kernel-bit NOT in the
prior 9-kernel sweep shows **no Mode B advantage**. Consistent with the
500k-convergence pattern: Mode B's preprocessing is fully consumed by 1M
conflicts.

## Implication

Mode B's value-add is **front-loaded preprocessing**, not a steady-state
solver-friendliness improvement. At 1M+ conflicts on cands new to the
prior data, the modes converge.

This is **not** a falsification of the prior 50k Mode B finding — the
50k regime is not represented here. But it does narrow the window where
Mode B helps: the regime where preprocessing-conflict-rate matters.

## Single data point caveat

n=1 candidate, single seed=5, single solver. Adding more (bit=15,
bit=24, bit=26 NEW cands) would tighten the picture. **EVIDENCE-level**
single observation at sr=61, 1M conflicts.

## Reproduce

```bash
kissat --conflicts=1000000 --seed=5 -q \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_expose_sr61_n32_bit20_m294e1ea8_fillffffffff.cnf
kissat --conflicts=1000000 --seed=5 -q \
  headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit20_m294e1ea8_fillffffffff.cnf
```

## What this validates / refutes

- **Validates**: Mode B as written is solver-equivalent to Mode A at 1M+
  conflicts. The structural force constraints don't break solver behavior.
- **Refutes (for sr=61, 1M kissat, this candidate)**: any "steady-state"
  Mode B speedup. Speedup is purely preprocessing window.
- **Does NOT refute**: 50k-window Mode B speedup (not measured here).

## Status

EVIDENCE-level single observation. Cascade_aux bet's "Mode B 2-3.4×
front-loaded preprocessing" claim remains intact for the 50k regime
but should be further qualified: "front-loaded only; converges by ~500k."
