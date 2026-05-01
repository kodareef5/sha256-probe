---
date: 2026-05-01
bet: block2_wang
status: PATH_C_MANIFEST_RANK41_BREAKTHROUGH_HW35
parent: F473 basin seed manifest / F484-F485 objective-pool negatives
evidence_level: CERTPIN_VERIFIED
compute: two pair-beam runs; kissat+cadical cert-pin verification
author: yale-codex
---

# F486/F487: manifest HW41 rank 12 drops bit13 to HW=35

## Setup

F486/F487 returned to the F473 basin seed manifest after the objective-ranked
pair-pool variants went negative. Both runs used manifest HW41 seeds with the
standard wider c/g-protected pair beam:

- pair pool: 1024
- pair rank: hw
- beam width: 1024
- max pairs: 6
- max radius: 12
- penalty registers: c,g
- penalty weight: 2

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F486_bit13_manifest_rank11_hw41_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F487_bit13_manifest_rank12_hw41_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/20260501_F487_certpin_validation.json`

## F486 Negative Control

F486 started from manifest rank 11:

- W1 = `0x5228ed8d 0x61a1a29c 0x6a3a8409 0x149e9173`
- HW=41
- score=80.923
- hw63=`[10,9,1,0,11,9,1,0]`

It re-found the previous HW36 record but did not improve it.

F486 counters:

- expanded: 3,494,072
- skipped duplicate: 1,749,832
- bridge pass: 3,493,303
- HW <= 41: 15
- HW < 41: 13
- wall: 298.28s

Depth summary:

| Depth | Kept | Best HW | Best score |
|---:|---:|---:|---:|
| 1 | 1024 | 50 | 72.500 |
| 2 | 1024 | 36 | 85.471 |
| 3 | 1024 | 36 | 85.471 |
| 4 | 1024 | 36 | 85.471 |
| 5 | 1024 | 36 | 85.471 |
| 6 | 1024 | 36 | 85.471 |

## F487 New Record: bit13_m916a56aa HW=35

F487 started from manifest rank 12:

- W1 = `0x5228ed8d 0x61a1a29c 0x6a3a8409 0x2f9eb5d3`
- HW=41
- score=80.923
- hw63=`[13,8,1,0,11,7,1,0]`

New witness:

- W1 = `0x5228ed8d 0x61a1a29c 0x6a7a8409 0xc7d515db`
- W2 = `0x1cf531f1 0xb6007fec 0x8af8919a 0xa0dae661`
- HW=35
- score=86.364
- hw63=`[10,7,1,0,9,7,1,0]`
- diff63=`[0xd8581011,0xa004804c,0x80000000,0x00000000,0x8007828a,0x0001864c,0x80000000,0x00000000]`
- move from HW41 seed: W59 bit 22; W60 bits 3,13,15,16,17,19,22,27,29,30,31.

F487 counters:

- expanded: 3,459,651
- skipped duplicate: 1,784,253
- bridge pass: 3,459,418
- HW <= 41: 29
- HW < 41: 12
- wall: 295.46s

Depth summary:

| Depth | Kept | Best HW | Best score |
|---:|---:|---:|---:|
| 1 | 1024 | 44 | 78.143 |
| 2 | 1024 | 44 | 78.143 |
| 3 | 1024 | 41 | 80.923 |
| 4 | 1024 | 36 | 85.471 |
| 5 | 1024 | 36 | 85.471 |
| 6 | 1024 | 35 | 86.364 |

Cert-pin:

- CNF: `/tmp/F487/aux_expose_sr60_n32_bit13_m916a56aa_fillffffffff_F487_certpin.cnf`
- sha256: `ae7505e9920973b4dbb5638bd1e8e74a4f0fe023e75638cb3733e770d67de8cd`
- kissat 4.0.4: UNSAT, ~0.00s
- cadical 3.0.0: UNSAT, ~0.01s

## Verdict

The manifest tail is still productive. Ranks 6-10 were either connected back
to the HW36 basin or negative, but rank 12 exposed a lower basin and moved the
bit13 panel floor from HW36 to HW35.

Current Path C panel:

- bit13 HW=35
- bit28 HW=42
- bit24 HW=43

Next useful work: exact relaxed Hamming closure around the HW35 witness, then
restart pair beam from the HW35 record and nearby HW36/HW40 intermediates with
new pair-pool construction.
