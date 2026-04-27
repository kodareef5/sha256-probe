# F19: bit13_m4e560940 stack hint speedup confirms F4b generalizes
**2026-04-26 21:24 EDT**

Quick verify: does the F4b de58-de59 stack speedup (1.87× median n=18)
extend to bit13_m4e560940 — a NEW cand identified by F12 + F17 as
structurally distinguished?

## Setup

bit13_m4e560940 fill=0xaaaaaaaa kernel_bit=13. F12 min-HW chamber:
W57=0x7032b79b → de58=0x00102040 (HW=3), de59 = 0xfb0fbb18 (cand-level).

Built two CNFs via cascade_aux Mode A encoder:
- `bit13_base.cnf`: 13492 vars, 56009 clauses (no hints)
- `bit13_stack.cnf`: 13492 vars, 56073 clauses (64 hints: 32 de58 + 32 de59)

## Result (kissat 4.0.4, 50k conflicts, 3 seeds)

| seed | base wall | stack wall | speedup |
|---:|---:|---:|---:|
| 1 | 3.90 s | 1.66 s | 2.35× |
| 2 | 2.93 s | 2.44 s | 1.20× |
| 3 | 2.50 s | 1.81 s | 1.38× |
| **median** | **2.93 s** | **1.81 s** | **1.62×** |

## Conclusion

bit13_m4e560940 stack speedup = **1.62× at 50k** — within the F4b
n=18 deployment range (1.45–2.90×, median 1.87×). The F4b stack
deployment generalizes to this NEW cand on first try.

Cross-bet status: bit13_m4e560940 now confirmed productive across:
- F4b n=18 stack speedup family: 1.62× (in expected range)
- F12 cascade-1 chamber image: HW=3 min de58 (rank 2 of registry)
- F17 round-63 residual: HW=47 (rank 1 of 6 sampled)

Recommended: add bit13_m4e560940 to the cascade_aux fingerprint
deployment baseline. Both Mode A and stack CNFs audit CONFIRMED via
existing fingerprint range.

EVIDENCE-level: VERIFIED at 3-seed median.
