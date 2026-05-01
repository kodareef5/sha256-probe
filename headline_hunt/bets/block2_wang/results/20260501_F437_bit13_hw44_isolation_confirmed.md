---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_HW44_HAMMING3_ISOLATED
parent: F436 bit13 HW=44 radius-6 breakthrough
evidence_level: VERIFIED
compute: 0 solver search; 18.1s deterministic Hamming-ball enumeration; 0 cert-pin runs
author: yale-codex
---

# F437: bit13 HW=44 is Hamming-3 isolated

## Setup

F436 found a new bit13 HW=44 record at Hamming distance 4 from the
previous HW=49 point. F437 repeats the deterministic Hamming-ball
closure around the new record.

Witness:

```
W1[57..60] = 0x5228ed8d 0x61a1a29c 0xea6a8c21 0x3dbfd852
HW         = 44
```

Artifact:

`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F437_bit13_hw44_hamming3_enumeration.json`

## Result

| Radius | Total | cascade-1 ok | bridge pass | HW <= 44 | HW < 44 |
|---:|---:|---:|---:|---:|---:|
| 1 | 128 | 128 | 127 | 0 | 0 |
| 2 | 8,128 | 8,128 | 8,003 | 0 | 0 |
| 3 | 341,376 | 341,376 | 333,625 | 0 | 0 |
| **Total** | **349,632** | **349,632** | **341,755** | **0** | **0** |

Best seen stayed the seed:

```
HW=44, score=71.526
```

## Findings

### Finding 1: the new HW=44 basin has the same sharp wall

F435 showed HW=49 was Hamming-3 isolated, then F436 found HW=44 at
distance 4. F437 now shows the new HW=44 point is also Hamming-3
isolated. The bit13 landscape is punctuated: no improvement inside
radius 3, but a deeper point can exist just outside that boundary.

### Finding 2: bridge_score remains permissive

The bridge pass count is identical to F435's HW=49 closure:
341,755/349,632 candidates pass bridge_score. The absence of any
HW <= 44 neighbors is therefore an HW-landscape fact, not a bridge
filter artifact.

## Verdict

- bit13 HW=44 is Hamming-3 isolated.
- Current Path C records remain: bit24 HW=43, bit13 HW=44, bit28 HW=45,
  bit3/bit2 HW=51.
- Further bit13 improvement, if it exists, must be at radius >= 4 or
  require a different geometry/operator.

## Next

1. A second radius-6 seeded pass from HW=44 can test whether F436's
   distance-4 pattern repeats.
2. A focused joint W59/W60 radius-4/5 enumerator would directly cover
   the move class that produced F436.
