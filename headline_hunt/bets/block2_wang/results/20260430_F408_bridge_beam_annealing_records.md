---
date: 2026-04-30
bet: block2_wang
status: PATH_C_RECORDS_FOUND_AND_CERTPIN_NEGATIVE
parent: F379 bridge-guided greedy beam
evidence_level: EVIDENCE
compute: 0 solver search; 458s pure W-space annealing + 8 audited cert-pin solver checks
---

# F408: annealed bridge beam lowers residual records to HW=45, all cert-pin UNSAT

## Setup

Path C extended `block2_bridge_beam.py` from greedy-only hillclimb to
support simulated annealing over the same `(W57, W58, W59, W60)` W-space:

- geometric cooling `T=2.0 -> 0.05`
- 12 independent restarts per candidate
- 200,000 iterations per restart
- mutation radius 1..6 bit flips
- recent-state tabu size 512

Run panel: `bit3_m33ec77ca`, `bit2_ma896ee41`, `bit24_mdc27e18c`,
`bit28_md1acca79`. Total wall: 458s. No SAT solver was used during search.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260430_F408_bridge_beam_anneal.json`
- `headline_hunt/bets/block2_wang/results/20260430_F408_certpin_validation.json`

## Result

| Candidate | Prior known floor | F408 best HW | Delta | Best score | Cert-pin |
|---|---:|---:|---:|---:|---|
| bit3_m33ec77ca | 55 | 51 | -4 | 71.551 | kissat UNSAT, cadical UNSAT |
| bit2_ma896ee41 | 56 | 51 | -5 | 71.551 | kissat UNSAT, cadical UNSAT |
| bit24_mdc27e18c | 57 | 49 | -8 | 73.447 | kissat UNSAT, cadical UNSAT |
| bit28_md1acca79 | 59 | 45 | -14 | 74.146 | kissat UNSAT, cadical UNSAT |

All four pinned CNFs audited `CONFIRMED` before solver invocation. All eight
cert-pin runs are logged in `headline_hunt/registry/runs.jsonl`.

## Witnesses

```
bit3_m33ec77ca  HW=51  hw63=[15,10,1,0,13,11,1,0]
W1[57..60] = 0xba476635 0x8cf9982c 0x0699c787 0x8893274d
W2[57..60] = 0xb3b6edae 0xcbcc8ef2 0xa6862188 0xa55c6f58

bit2_ma896ee41  HW=51  hw63=[17,6,1,0,14,12,1,0]
W1[57..60] = 0x504e056e 0x3e435e29 0xda594ea2 0xe37c8fe1
W2[57..60] = 0x7f97d9bd 0x3e28be83 0xf7685723 0xa1f0c7a3

bit24_mdc27e18c  HW=49  hw63=[15,12,1,0,12,8,1,0]
W1[57..60] = 0x4be5074f 0x429efff2 0xe09458af 0xd6560e70
W2[57..60] = 0x8b1bab38 0x9adf28be 0xa95e0159 0xce6759f9

bit28_md1acca79  HW=45  hw63=[12,6,3,0,12,11,1,0]
W1[57..60] = 0x307cf0e7 0x853d504a 0x78f16a5e 0x41fc6a74
W2[57..60] = 0x6fcdf313 0xaa562d8d 0x5713c149 0xe764c998
```

All four preserve the F374/F376 cascade-1 fingerprint:
active registers are `{a,b,c,e,f,g}`, `d=h=0`, and `da != de`.

## Findings

### Finding 1: annealing fixes the F379 local-optimum failure

F379's greedy hillclimb beat the corpus only on bit2 and plateaued above the
known corpus floor on the other candidates. F408's annealing run beats the
known floor on all four tested candidates, including a large bit28 improvement
from HW=59 to HW=45.

The main structural shift is extreme `c/g` collapse: three records have
`c=g=1`, and bit28 has `g=1`. The bridge-score asymmetry term is therefore
doing useful work once the search is allowed to leave greedy basins.

### Finding 2: lower residuals are still cert-pin near-residuals

The new records are substantially closer to zero diff than the F371/F379
records, but the single-block cert-pin verdict remains unchanged:

```
4 witnesses x 2 solvers = 8 runs
kissat:  4/4 UNSAT, 0 SAT
cadical: 4/4 UNSAT, 0 SAT
```

This is not a collision. It is a better residual source for block-2 absorption
or bridge-cube design.

### Finding 3: Path C succeeded on its residual objective, not on SAT

Success criterion split:

- New HW < 56 record: achieved on all four candidates.
- Cert-pin validation: all four are audited and cross-solver UNSAT.
- Headline-class SAT: not achieved.

## Next

1. Feed the HW=45 bit28 witness into block-2 absorption tooling as the new
   best residual seed.
2. Run a narrower second annealing panel around bit28 with more restarts or
   seed-from-best perturbations if the immediate goal is another residual
   record.
3. Keep cert-pin as a fast negative screen, but do not expect it to learn
   useful clauses; F380 already showed these instances are UP-trivial.
