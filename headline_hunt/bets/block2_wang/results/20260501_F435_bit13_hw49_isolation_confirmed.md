---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_HW49_HAMMING3_ISOLATED
parent: F432 yale bit13 HW=49, F433 macbook bit13 HW=50 isolation
evidence_level: VERIFIED
compute: 0 solver search; 17.5s deterministic Hamming-ball enumeration; 0 cert-pin runs
author: yale-codex
---

# F435: bit13 HW=49 is Hamming-3 isolated

## Setup

After the rebase, the project had two bit13 results:

- macbook F432/F433: bit13 HW=50, then Hamming-3 isolation around that HW=50 point.
- yale-codex F432: bit13 HW=49 from the original F378 top-1 seed.

That left one direct gap: the new HW=49 basin needed the same
Hamming-{1,2,3} closure that F433 performed for HW=50.

I added a general enumerator:

`headline_hunt/bets/block2_wang/encoders/enumerate_hamming_ball.py`

Then ran it over the full 128-bit `W1[57..60]` ball around:

```
W1[57..60] = 0x5228ed8d 0x61a1a29c 0xea7a8c21 0x25bfda52
HW         = 49
```

Artifact:

`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F435_bit13_hw49_hamming3_enumeration.json`

## Result

| Radius | Total | cascade-1 ok | bridge pass | HW <= 49 | HW < 49 |
|---:|---:|---:|---:|---:|---:|
| 1 | 128 | 128 | 127 | 0 | 0 |
| 2 | 8,128 | 8,128 | 8,003 | 0 | 0 |
| 3 | 341,376 | 341,376 | 333,625 | 0 | 0 |
| **Total** | **349,632** | **349,632** | **341,755** | **0** | **0** |

Best seen remained the seed point itself:

```
HW=49, score=70.667
W1[57..60] = 0x5228ed8d 0x61a1a29c 0xea7a8c21 0x25bfda52
```

## Findings

### Finding 1: the HW=49 bit13 record is a sharp local singleton

The full Hamming-{1,2,3} ball contains no HW-tying and no
HW-improving neighbor. This exactly matches the isolated-peak pattern
from F429/F430/F431 and F433, now applied to the true current bit13
record rather than the superseded HW=50 basin.

### Finding 2: bridge_score is not the binding filter

All 349,632 candidates preserve cascade-1. bridge_score passes
341,755 of them, or 97.7%. Despite that permissive filter, zero
neighbors reach HW <= 49. The local floor is produced by the HW
landscape, not by bridge rejection.

### Finding 3: the current 5-cand Path C panel is now consistently closed at radius 3

Current records:

| Cand | Current HW | Closure |
|---|---:|---|
| bit24_mdc27e18c | 43 | Hamming-3 closed; radius-6 seeded stable |
| bit28_md1acca79 | 45 | Hamming-3 closed; radius-6 seeded stable |
| bit13_m916a56aa | 49 | Hamming-3 closed by F435 |
| bit3_m33ec77ca | 51 | Hamming-3 closed |
| bit2_ma896ee41 | 51 | Hamming-3 closed |

## Verdict

- The new bit13 HW=49 record is Hamming-3 isolated.
- The F433 caveat created by the later HW=49 discovery is now closed.
- Path C has a clean radius-3 characterization across all five current records.
- Headline-class SAT remains uncrossed; this is a verified near-residual structure result.

## Next

1. Run radius-6 seeded confirmation for bit13 HW=49 if we want symmetry
   with F434's bit24/bit28 stability check.
2. Switch from W-cube local closure to geometry relaxation, especially
   lifting or varying the `c=g=1/2` sub-fingerprint.
3. Broaden to new kbits only if the goal is more residual records; the
   current five-record panel is now locally well characterized.
