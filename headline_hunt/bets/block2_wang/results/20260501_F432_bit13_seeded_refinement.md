---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_NEW_HW49_RECORD
parent: F378 bridge_score top-1, F431 Hamming-3 isolation of the 4-cand panel
evidence_level: EVIDENCE
compute: 0 solver search; 132.9s pure W-space annealing + 2 audited cert-pin solver checks
author: yale-codex
---

# F432: bit13 seeded refinement turns the F378 surprise lead into a HW=49 near-residual

## Setup

F431 closed the full Hamming-{1,2,3} ball for the four Path C panel
candidates. Its next concrete suggestion was to try the F378 surprise
top-1 control, `bit13_m916a56aa`, which had not received the F427/F428
seeded-refinement treatment.

Seed:

```
bit13_m916a56aa F378 W1[57..60]
0x5228ed8d 0x61a1a29c 0xea7a8c21 0xb6befe82
```

Parameters:

- 12 restarts x 200,000 iterations
- `method=anneal`, `max_flips=3`
- temperature 0.5 -> 0.01
- tabu size 1024
- all restarts initialized from the F378 HW=59 witness

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F432_bit13_seeded_refinement.json`
- `headline_hunt/bets/block2_wang/results/20260501_F432_certpin_validation.json`

## Results

| Seed best HW | Seeds |
|---:|---:|
| 49 | 1 |
| 54 | 2 |
| 55 | 2 |
| 57 | 3 |
| 58 | 3 |
| 59 | 1 |

Best run: seed 5, score 70.667, HW=49, best_iter=85555.

| Cand | F378 HW | F432 HW | Delta | F432 score |
|---|---:|---:|---:|---:|
| bit13_m916a56aa | 59 | 49 | -10 | 70.667 |

## HW=49 witness

```
W1[57..60] = 0x5228ed8d 0x61a1a29c 0xea7a8c21 0x25bfda52
W2[57..60] = 0x1cf531f1 0xb6007fec 0x0af899b2 0x06bd6aa9
hw63       = [11, 6, 2, 0, 17, 11, 2, 0]   (total 49)
diff63     = [0x43985112, 0x27204000, 0x80020000, 0x00000000,
              0xe9317764, 0xb5264210, 0x80020000, 0x00000000]
active_regs = {a,b,c,e,f,g}, da_eq_de=False, c=g=2, d=h=0
```

The improvement keeps W57, W58, and W59 fixed and changes only W1[60]:

```
F378 W1[60] = 0xb6befe82
F432 W1[60] = 0x25bfda52
XOR         = 0x930124d0   bits {4,6,7,10,13,16,24,25,28,31}
```

This is Hamming distance 10 in W1[60], not the Hamming-2/3 behavior
seen in F427/F428. Cascade-1 propagation changes W2[60] from
`0x97bc8ed9` to `0x06bd6aa9`.

## Cert-pin verification

Audited and cross-solver UNSAT:

- audit verdict: CONFIRMED
- cnf_sha256: `b473db6b46a42de2913aff0b60340de7ba40a2ef66d062e658804d552c2a328e`
- kissat 4.0.4: UNSAT in 0.009846s
- cadical 3.0.0: UNSAT in 0.017193s

Both solver runs were appended to `headline_hunt/registry/runs.jsonl`.

## Findings

### Finding 1: bit13 was a real lead, but not a single-block collision

F378's bridge_score top-1 was not noise. A seeded local pass drops the
candidate from HW=59 to HW=49 in 132.9s, putting it in the same residual
quality band as the F408/F427/F428 Path C panel.

Cert-pin still resolves UNSAT in milliseconds. This is a useful
near-residual record, not a headline-class SAT witness.

### Finding 2: the bit13 move is a W1[60]-only, Hamming-10 jump

The four previous Path C panel records emphasized W1[60], but mostly at
small Hamming distance from their seeded records. F432 keeps that
W1[60] dominance while changing the distance scale: all useful movement
again sits in W1[60], but the best bit13 improvement is 10 W-bits away
from the F378 seed.

That makes bit13 a good counterexample to over-reading the F429-F431
Hamming-3 closure. Hamming-3 isolation can be true around a current best
while a better basin remains reachable by annealed multi-step movement
farther out in the same word.

### Finding 3: c/g compression reappears

F378's seed had `hw63=[13,13,3,0,13,13,4,0]`; F432's record has
`[11,6,2,0,17,11,2,0]`. The c/g registers compress from 7 total bits
to 4, while e becomes heavier. This is exactly the kind of structural
asymmetry bridge_score was built to reward, and in this case the score
increase also tracks a real HW decrease.

## Verdict

- Primary objective: achieved for bit13 residual quality, HW 59 -> 49.
- Cert-pin headline-class SAT: not achieved; both solvers UNSAT.
- Structural read: F378's bit13 signal transfers into W-space search.
- New Path C panel state: bit24 HW=43, bit28 HW=45, bit13 HW=49,
  bit3/bit2 HW=51.

## Next

1. Run the F429/F430/F431 Hamming-{1,2,3} closure around the new bit13
   HW=49 record. The existing closure covered only the four original
   panel candidates.
2. Add explicit `best_hw` tracking to `block2_bridge_beam.py`; F427
   already showed bridge_score and HW can diverge, so future artifacts
   should preserve both score-best and HW-best records.
3. Try one direct-HW anneal from the F432 bit13 record, with bridge
   constraints as filters rather than score objective, to test whether
   HW<49 is hiding behind a score-worse move.
