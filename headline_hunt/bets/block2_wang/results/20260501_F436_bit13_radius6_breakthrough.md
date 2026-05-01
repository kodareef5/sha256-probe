---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_NEW_HW44_RECORD
parent: F435 bit13 HW=49 Hamming-3 isolation; F434 radius-6 confirmation pattern
evidence_level: EVIDENCE
compute: 0 solver search; 137.4s W-space annealing + 2 audited cert-pin solver checks
author: yale-codex
---

# F436: radius-6 seeded anneal breaks bit13 from HW=49 to HW=44

## Setup

F435 proved the new bit13 HW=49 record has no Hamming-{1,2,3}
neighbor at HW <= 49. The natural symmetry check was F434-style
seeded anneal at a wider mutation radius.

Parameters:

- candidate: `bit13_m916a56aa`
- init W1[57..60]: `0x5228ed8d, 0x61a1a29c, 0xea7a8c21, 0x25bfda52`
- 12 restarts x 200,000 iterations
- `method=anneal`, `max_flips=6`
- temperature 0.5 -> 0.01
- tabu size 1024

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F436_bit13_hw49_radius6_seeded.json`
- `headline_hunt/bets/block2_wang/results/20260501_F436_certpin_validation.json`

## Results

| Outcome | Seeds | Best score | Best HW |
|---|---:|---:|---:|
| Stayed at HW=49 seed | 11 | 70.667 | 49 |
| Escaped to new record | 1 | 71.526 | 44 |

The new record came from seed 2 at iteration 126,898.

## HW=44 witness

```
W1[57..60] = 0x5228ed8d 0x61a1a29c 0xea6a8c21 0x3dbfd852
W2[57..60] = 0x1cf531f1 0xb6007fec 0x0ae899b2 0xde7500a9
hw63       = [13, 8, 3, 0, 10, 7, 3, 0]   (total 44)
diff63     = [0x30af3824, 0x15254400, 0x80020800, 0x00000000,
              0x0325b082, 0x0d024410, 0x80020800, 0x00000000]
active_regs = {a,b,c,e,f,g}, da_eq_de=False, c=g=3, d=h=0
```

Delta from F435 HW=49:

```
W59 XOR = 0x00100000   bit {20}
W60 XOR = 0x18000200   bits {9,27,28}
total Hamming distance = 4
```

This is exactly outside F435's closed Hamming-3 ball.

## Cert-pin verification

Audited and cross-solver UNSAT:

- audit verdict: CONFIRMED
- cnf_sha256: `2ebafe056476d78d0b0406c318926b59f6ed8aed51dce7ad5b12fa22f485a3aa`
- kissat 4.0.4: UNSAT in 0.022060s
- cadical 3.0.0: UNSAT in 0.046806s

Both solver runs were appended to `headline_hunt/registry/runs.jsonl`.

## Findings

### Finding 1: bit13 is now the second-deepest Path C record

Current Path C records:

| Cand | Current HW | Source |
|---|---:|---|
| bit24_mdc27e18c | 43 | F428 |
| bit13_m916a56aa | 44 | F436 |
| bit28_md1acca79 | 45 | F408/F427/F434 |
| bit3_m33ec77ca | 51 | F408 |
| bit2_ma896ee41 | 51 | F408 |

The bit13 path went from F378 HW=59 to F432/F435 HW=49, then to F436
HW=44. That is a 15-point reduction from the original corpus lead.

### Finding 2: Hamming-3 isolation was real, but not enough

F435's deterministic closure remains valid: no neighbor at radius <= 3
ties or beats HW=49. F436 found the next basin at Hamming distance 4.
So the local landscape has a hard radius threshold rather than a
smooth basin around the HW=49 point.

### Finding 3: the improvement changes W59 and W60, not just W60

Earlier breakthroughs often concentrated entirely in W60. F436 keeps
W57 and W58 fixed, but uses one W59 bit plus three W60 bits. That
suggests the next layer of Path C movement may require joint
late-schedule moves rather than W60-only enumeration.

## Verdict

- Primary objective: achieved, bit13 HW 49 -> 44.
- Cert-pin headline-class SAT: not achieved; both solvers UNSAT.
- Structural result: radius 4 breaks the Hamming-3 isolated HW=49 basin.
- Current best panel is now bit24 HW=43, bit13 HW=44, bit28 HW=45,
  bit3/bit2 HW=51.

## Next

1. Run Hamming-{1,2,3} closure around the new bit13 HW=44 record.
2. Run radius-6 seeded confirmation from HW=44; if it breaks again,
   bit13 is not at its local floor.
3. Try a focused joint W59/W60 operator, since F436's improvement was
   one W59 bit plus three W60 bits.
