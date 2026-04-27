# F18: 10B residual scan reorders the picture — msb_m17149975 reaches HW=44
**2026-04-26 21:25 EDT**

Followup to F17 (100M scan, commit dfbb1ed). Extending to 10B samples
per cand reveals different scaling behavior across cands.

## Result

10 BILLION random (W1[57..60]) tuples per cand under cascade-1 +
cascade-2 + schedule extension to slot 64. ~190 sec wall per cand
(53 M/s with 4 in parallel sharing cores).

| cand | HW @ 100M (F17) | HW @ 10B (F18) | drop |
|---|---:|---:|---:|
| **msb_m17149975 (verified sr=60)** | 53 | **44** | -9 |
| idx=8 (m=0x33ec77ca) | not in F17 | 46 | — |
| bit13_m4e560940 (F17 leader) | 47 | 47 | 0 |
| msb_m189b13c7 (F12 chamber champ) | 51 | 49 | -2 |

## Reordered ranking @ 10B

1. **msb_m17149975** — HW=44 (best, with deep headroom to explore)
2. idx=8 m33ec77ca bit=3 — HW=46
3. bit13_m4e560940 — HW=47 (rigid: no improvement from 100M to 10B)
4. msb_m189b13c7 — HW=49

## Min-HW witness (W1[57..60]) per cand

| cand | min-HW (W1[57..60]) |
|---|---|
| msb_m17149975 | (0x22a23004, 0xf0f2c8f5, 0x946bbc63, 0x9f121f90) |
| idx=8 m33ec77ca | (0xcaf62f78, 0xec3c3674, 0x34a2e2ad, 0x7619ac16) |
| bit13_m4e560940 | (0xaffb9373, 0x6f262a99, 0xe4deabc3, 0x057cb110) |
| msb_m189b13c7 | (0xea373209, 0x82b49272, 0x0fa19bef, 0xa750d5a1) |

## Why msb_m17149975 dropped most

The verified sr=60 cand has the deepest residual structure to explore.
Its known sr=60 collision exists at SOME (W1[57..60]) point — implies
HW=0 is reachable at the actual collision. Random search is sampling
the residual surface; with 10B samples we found HW=44 (still 44 bits
short of 0).

bit13_m4e560940's stagnation at HW=47 from 100M to 10B is interesting
— it suggests the cand's residual surface has a "shelf" near HW=47
that random search hits quickly but doesn't penetrate. This is more
consistent with a STRUCTURAL minimum than headroom.

## Honest correction to F17

F17 named bit13_m4e560940 as block2_wang's primary target based on
100M-sample HW=47. F18 reveals msb_m17149975 has deeper headroom
(HW=44 already at 10B, more potential at 100B+).

Updated recommendation:
- **msb_m17149975**: primary target for extended search (1T-10T samples)
  to push residual HW lower. Known sr=60 cand; may admit absorption.
- **bit13_m4e560940**: structurally distinguished but may not improve
  with more samples.

## Sub-finding: bit=13 family comparison @ 100M

Of 7 bit=13 cands in registry:
- m4e560940 (fill=0xaa): HW=47 (best)
- m916a56aa (fill=0xff): HW=50
- ma23ae799 (fill=0x80): HW=50
- mbee3704b (fill=0x00): HW=51
- me01ff7c0 (fill=0xaa): HW=52
- m4d9f691c (fill=0x55): HW=53
- m72f21093 (fill=0xaa): HW=53

m4e560940 is 3 bits below next-best bit=13 cand. Structurally
distinguished within the bit=13 family (independent of cross-family
ranking).

EVIDENCE-level: VERIFIED at 10B samples. Future workers extending
to 100B+ should prioritize msb_m17149975 (deepest headroom) and
re-test bit13_m4e560940 ridigity hypothesis.
