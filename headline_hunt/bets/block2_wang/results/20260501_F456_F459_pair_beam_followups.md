---
date: 2026-05-01
bet: block2_wang
status: PATH_C_PAIR_BEAM_FOLLOWUPS_HW38_HW42
parent: F453/F455 bit13 HW41 floor
evidence_level: CERTPIN_VERIFIED
compute: four pair-beam runs; kissat+cadical cert-pin verification
author: yale-codex
---

# F456-F459: wider pair beam drops bit13 to HW=38 and bit28 to HW=42

## Setup

After F454/F455 closed bit13 HW=41 under exact relaxed radius 4, the next
question was whether the pair-beam coordinate still had room. F456-F459 ran
four follow-ups:

| Run | Candidate | Start HW | Pair rank | Pool | Beam | Max pairs | Result |
|---|---|---:|---|---:|---:|---:|---|
| F456 | bit13_m916a56aa | 41 | repair | 512 | 512 | 5 | no improvement |
| F457 | bit24_mdc27e18c | 43 | HW | 512 | 512 | 5 | no improvement |
| F458 | bit13_m916a56aa | 41 | HW | 1024 | 1024 | 6 | HW=38 |
| F459 | bit28_md1acca79 | 44 | HW | 512 | 512 | 5 | HW=42 |

All four used c/g penalty weight 2. F458 also raised max radius from 10 to
12.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F456_bit13_hw41_pair_beam_repair_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F457_bit24_hw43_pair_beam_cg_wide.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F458_bit13_hw41_pair_beam_cg_wider.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F459_bit28_hw44_pair_beam_cg_followup.json`
- `headline_hunt/bets/block2_wang/results/20260501_F456_F459_certpin_validation.json`

## New Records

### bit13_m916a56aa: HW=38

Previous bit13 record: HW=41 from F453.

New witness:

- W1 = `0x5228ed8d 0x61a1a29c 0xea3a8429 0x2d9f1a3b`
- W2 = `0x1cf531f1 0xb6007fec 0x0ab891ba 0x4e9cca80`
- HW=38
- score=83.667
- hw63=`[13,6,1,0,11,6,1,0]`
- diff63=`[0xc3451859,0x1e400400,0x80000000,0x00000000,0x6e050b20,0x1a440200,0x80000000,0x00000000]`
- move from F453 HW41: W59 bits 20,22; W60 bits 3,9,11,12,14,16,21,27,28.

F458 counters:

- expanded: 3,654,541
- skipped duplicate: 1,589,363
- bridge pass: 3,654,333
- HW <= 41: 5
- HW < 41: 1
- wall: 296.64s

Cert-pin:

- CNF: `/tmp/F458/aux_expose_sr60_n32_bit13_m916a56aa_fillffffffff_F458_certpin.cnf`
- sha256: `ebe5fb3a652dbe01396c600bc25826d4e59c68ed9fd61173bda1163fb4ea5976`
- kissat 4.0.4: UNSAT, ~0.02s
- cadical 3.0.0: UNSAT, ~0.04s

### bit28_md1acca79: HW=42

Previous bit28 record: HW=44 from F450.

New witness:

- W1 = `0x307cf0e7 0x853d504a 0x78f16a7e 0xccf479b4`
- W2 = `0x6fcdf313 0xaa562d8d 0x5713c169 0x6a5cb877`
- HW=42
- score=80.000
- hw63=`[9,9,1,0,11,11,1,0]`
- diff63=`[0x610a208a,0x51c24044,0x08000000,0x00000000,0x0a88dc82,0xd246005c,0x08000000,0x00000000]`
- move from F450 HW44: W59 bit 5; W60 bits 1,2,6,12,24,27,29,31.

F459 counters:

- expanded: 710,096
- skipped duplicate: 338,992
- bridge pass: 709,642
- HW <= 44: 4
- HW < 44: 4
- wall: 57.11s

Cert-pin:

- CNF: `/tmp/F459/aux_expose_sr60_n32_bit28_md1acca79_fillffffffff_F459_certpin.cnf`
- sha256: `eaebb36288b248c3bc1631d6114dd36a2cee74be2b2e2b9642c99257c30171cc`
- kissat 4.0.4: UNSAT, ~0.01s
- cadical 3.0.0: UNSAT, ~0.01s

## Negative Controls

F456 shows that repair-ranked pairs are not enough from bit13 HW41: best
selected non-seed state was HW46 and the seed stayed best.

F457 shows that the F453 settings do not move the bit24 HW43 basin: best
selected non-seed state was HW49 and the seed stayed best.

## Current Path C Panel

| Candidate | Prior HW | New HW | Status |
|---|---:|---:|---|
| bit13_m916a56aa | 41 | 38 | new global Path C floor |
| bit28_md1acca79 | 44 | 42 | improved |
| bit24_mdc27e18c | 43 | 43 | unchanged |

## Verdict

The pair-beam coordinate is now the dominant productive tool. The exact
radius-4 closures remain useful as local sanity checks, but they are not
predicting the next basin jump. The best next work is to close bit13 HW38
locally, then restart wider pair-beam from HW38 and from bit28 HW42.
