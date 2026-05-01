---
date: 2026-05-01
bet: block2_wang
status: PATH_C_INTERMEDIATE_BASIN_BREAKTHROUGH_HW36
parent: F465/F466 pair-beam negatives
evidence_level: CERTPIN_VERIFIED
compute: two pair-beam runs; kissat+cadical cert-pin verification
author: yale-codex
---

# F467/F468: HW40 intermediate basin drops bit13 to HW=36

## Setup

F465/F466 showed that simply widening the current record seed or increasing
c/g penalty weight did not improve bit13 HW38. F467 changed the seed instead:
it restarted pair beam from the strongest F462 non-record HW40 intermediate.
F468 tested a different lane objective from the HW38 record seed.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F467_bit13_hw40_intermediate_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F468_bit13_hw38_pair_beam_ae.json`
- `headline_hunt/bets/block2_wang/results/20260501_F467_certpin_validation.json`

## F467 New Record: bit13_m916a56aa HW=36

F467 start seed:

- W1 = `0x5228ed8d 0x61a1a29c 0xea3a8429 0xa59e9dfb`
- HW=40
- score=81.842
- hw63=`[16,7,1,0,9,6,1,0]`

New witness:

- W1 = `0x5228ed8d 0x61a1a29c 0x6a3a8409 0x2c9e917b`
- W2 = `0x1cf531f1 0xb6007fec 0x8ab8919a 0xc59c0201`
- HW=36
- score=85.471
- hw63=`[11,3,1,0,13,7,1,0]`
- diff63=`[0xa048446b,0x00844000,0x80000000,0x00000000,0x1624b0d9,0xa088c200,0x80000000,0x00000000]`
- move from HW40 seed: W59 bits 5,31; W60 bits 7,10,11,24,27,31.

F467 counters:

- expanded: 3,446,754
- skipped duplicate: 1,797,150
- bridge pass: 3,446,607
- HW <= 40: 7
- HW < 40: 5
- wall: 288.87s

Depth summary:

| Depth | Kept | Best HW | Best score |
|---:|---:|---:|---:|
| 1 | 1024 | 49 | 73.447 |
| 2 | 1024 | 46 | 76.273 |
| 3 | 1024 | 42 | 80.000 |
| 4 | 1024 | 36 | 85.471 |
| 5 | 1024 | 36 | 85.471 |
| 6 | 1024 | 36 | 85.471 |

Cert-pin:

- CNF: `/tmp/F467/aux_expose_sr60_n32_bit13_m916a56aa_fillffffffff_F467_certpin.cnf`
- sha256: `285ae548c097258a0a5068b6fab6dbb6e8bc5f9e43838b310b93e780edd156dc`
- kissat 4.0.4: UNSAT, ~0.00s
- cadical 3.0.0: UNSAT, ~0.01s

## F468 Negative Control

F468 used the HW38 record seed with penalty registers changed from c,g to
a,e. It did not improve:

- best selected non-seed HW=41
- seed HW=38 stayed best
- expanded: 3,769,528
- bridge pass: 3,769,391
- wall: 321.75s

## Verdict

This is a useful coordinate lesson: the record seed was boxed in under the
same pair beam, but a nearby non-record HW40 basin opened a lower HW36
point. Future search should preserve and reuse strong non-record basins
instead of treating them as failed states.

Current Path C panel:

- bit13 HW=36
- bit28 HW=42
- bit24 HW=43

Next useful work: cert-preserving closure around bit13 HW36, then restart
pair beam from HW36 and from the best F467 non-record intermediates.
