---
date: 2026-05-01
bet: programmatic_sat_propagator
status: ACTUAL_REGISTER_PRIORITY_GEOMETRY_VERDICT
parents: F421, F422, F423, F424, F425
---

# F426: actual-register priority geometry verdict

## Question

F421 found an actual-register learned-neighborhood signal, but the priority arm only helped bit24. F422-F425 asked whether that signal could be refined into a deployable operator or whether it was a bit24-specific artifact.

## Verdict

Actual-register learned-neighborhood priority is not a general rule. The deployable form is narrower: bit24's contiguous high `actual_p1_a_57` cluster `21-25` supports pure bounded priority. Sparse low-bit clusters on bit2 and bit28 oversteer even at lower caps, while F343 remains the better operator.

## Candidate Boundary

| Candidate | Geometry | Best F343 Result | Best Priority Result | Decision |
|---|---|---:|---:|---|
| `bit24_mdc27e18c_fillffffffff` | high contiguous `a_57[21:25]` | F422 F343: -0.51% | F424 cap96: -13.20%; cap64-cap112 all -12.30% to -13.20% | Use pure high-cluster priority; cap96 default, cap64-cap112 viable |
| `bit2_ma896ee41_fillffffffff` | sparse low `a_57` bits 3/7/8 | F425 F343: -3.38% | F425 cap64: +35.07%; cap96: +14.83% | Use F343; stop priority |
| `bit28_md1acca79_fillffffffff` | sparse low `a_57` bits 2/5/6 | F425 F343: -17.05% | F425 cap64: +23.45%; cap96: +8.98% | Use F343; stop priority |

## Mechanism Read

The bit24 result is robust across two seed panels: F422 cap64 improved by 11.37% on seeds 0-2, and F424 cap64-cap112 all improved by 12.30-13.20% on seeds 3-7. The exact cap is not the important part; the contiguous high cluster is.

Bit2 and bit28 are the opposite. Smaller caps did not convert the signal into a weak positive. They still increased decisions and backtracks, and they drove much higher `cb_propagate` activity. That makes the priority behavior look like search oversteer on sparse low clusters.

## Operating Rule

- For bit24-like geometry: try pure high-cluster `actual_p1_a_57` priority with cap64/cap96.
- For sparse low-bit hotspots: keep F343 and do not apply direct priority.
- Do not compose F343 with bit24 high-cluster priority by default; F423 showed interference.

## Next Gate

Scan future learned-neighborhood candidates for contiguous high actual-register clusters before spending solver budget on priority transfer. If no such candidate exists, keep the operator as bit24-specific and move effort back to F343/default CDCL or a new feature family.
