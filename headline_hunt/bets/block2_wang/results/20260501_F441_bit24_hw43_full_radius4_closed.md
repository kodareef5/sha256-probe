---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT24_HW43_FULL_RADIUS4_CLOSED
parent: F428 bit24 HW=43, F431 Hamming-3 closure, F434 radius-6 stability
evidence_level: VERIFIED
compute: 11017632 exact forward evaluations; 609.61s wall; 0 solver runs
author: yale-codex
---

# F441: bit24 HW=43 full W57..W60 radius-4 closure

## Setup

F428 established bit24 as the current Path C floor at HW=43. F431 closed
Hamming radius 3, and F434 showed that seeded radius-6 annealing does not
escape the basin. F441 adds the exact missing shell: every Hamming radius
1..4 bit flip over all 128 bits of W1[57..60].

Input witness:

`W1 = 0x4be5074f 0x429efff2 0xe09458af 0xe6560e70`

Artifact:

`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F441_bit24_hw43_full_radius4_enumeration.json`

## Result

| Radius | Total | Cascade-1 pass | Bridge pass | HW <= 43 | HW < 43 |
|---:|---:|---:|---:|---:|---:|
| 1 | 128 | 128 | 128 | 0 | 0 |
| 2 | 8,128 | 8,128 | 8,128 | 0 | 0 |
| 3 | 341,376 | 341,376 | 341,376 | 0 | 0 |
| 4 | 10,668,000 | 10,668,000 | 10,668,000 | 0 | 0 |
| total | 11,017,632 | 11,017,632 | 11,017,632 | 0 | 0 |

Best seen remained the seed itself:

- HW=43
- score=79.073
- `hw63=[14,5,1,0,14,8,1,0]`
- `diff63=[0x78cc01b5,0x0a240001,0x20000000,0x00000000,0xc125d48d,0x06250181,0x20000000,0x00000000]`

## Verdict

The global Path C floor, bit24 HW=43, is exactly closed through radius 4
across W57..W60. Unlike bit13, every radius-4 neighbor also passes the
bridge selector, so the absence of HW <= 43 is purely a residual-quality
failure rather than a selector-filter artifact.

Current exact local picture:

- bit24 HW=43: full W57..W60 radius-4 closed.
- bit13 HW=44: full W57..W60 radius-4 closed.
- bit28 HW=45: Hamming-3 closed and radius-6 seeded stable, but not yet
  exact radius-4 closed.

Next best use of exact enumeration is bit28 HW=45 radius-4 closure, then
switch to nonlocal/carry-chart operators if all top-three records are
radius-4 closed.
