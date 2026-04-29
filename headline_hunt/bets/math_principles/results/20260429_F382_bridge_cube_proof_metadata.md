---
date: 2026-04-29
bet: math_principles
status: BRIDGE_CUBE_PROOF_METADATA
---

# F382: bridge cube proof metadata

## Summary

Verdict: `bridge_cube_proofs_extracted`.
Use proof metadata to rank bridge cubes for conflict-clause inspection.

| Cube | Assumptions | Status | Wall | DRAT bytes | Added | Deleted | Fixed | Propagations |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| `F378_D61_floor_guard_explosion::w61` | 32 | `UNSATISFIABLE` | 0.177001 | 1046118 | 50711 | 70224 | 1302 | 47883 |
| `F378_D61_floor_guard_explosion::w57_w60` | 128 | `UNSATISFIABLE` | 0.128742 | 1083438 | 55018 | 71397 | 1446 | 45570 |
| `F375_D61_to_guard_bridge::w61` | 32 | `UNSATISFIABLE` | 0.118771 | 1049917 | 50945 | 70285 | 1300 | 84612 |
| `F375_D61_to_guard_bridge::w57_w60` | 128 | `UNSATISFIABLE` | 0.098552 | 173624 | 12357 | 8675 | 1394 | 1393 |
| `F374_low_guard_corner::w61` | 32 | `UNSATISFIABLE` | 0.10774 | 317853 | 22090 | 17646 | 1286 | 1285 |
| `F374_low_guard_corner::w57_w60` | 128 | `UNSATISFIABLE` | 0.035697 | 1457 | 101 | 128 | 613 | 609 |

## Decision

The fastest/smallest proof cubes are the best first targets for learned-clause inspection. The `w57_w60` full assignment cubes produce tiny proofs, suggesting the contradiction is mostly structural/UP-level rather than deep CDCL search.
