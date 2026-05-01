---
date: 2026-05-01
bet: block2_wang
status: PATH_C_PAIR_BEAM_BREAKTHROUGH_HW42
parent: F449 Path C locality synthesis
evidence_level: CERTPIN_VERIFIED
compute: pair beam search; kissat+cadical cert-pin verification
author: yale-codex
---

# F450: compensation-aware pair beam breaks Path C floor to HW=42

## Setup

F449 recommended leaving scalar local W-bit ranking and trying
compensation-aware composition. F450 adds:

`headline_hunt/bets/block2_wang/encoders/pair_beam_search.py`

The beam:

- builds a pool of exact two-bit W deltas.
- composes pair moves step by step.
- evaluates the actual W state after every composition.
- ranks beam states by HW plus a c/g compensation penalty.

Main wide run parameters:

- pair pool: 512
- beam width: 512
- max pairs: 5
- max radius: 10
- penalty registers: c,g
- penalty weight: 2

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F450_bit13_hw44_pair_beam_cg_wide.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F450_bit28_hw45_pair_beam_cg_wide.json`
- `headline_hunt/bets/block2_wang/results/20260501_F450_certpin_validation.json`

## New Records

### bit13_m916a56aa: HW=42

Previous bit13 record: HW=44 from F436.

New witness:

- W1 = `0x5228ed8d 0x61a1a29c 0xea6a8429 0x5dbfc83b`
- W2 = `0x1cf531f1 0xb6007fec 0x0ae891ba 0x7e6cf080`
- HW=42
- score=76.684
- hw63=`[12,9,2,0,11,6,2,0]`
- diff63=`[0x124c2b52,0x08c21f00,0x40000800,0x00000000,0xe80608e1,0x39600000,0x40000800,0x00000000]`
- move from F436 HW44: W59 bits 3,11 plus W60 bits 0,3,5,6,12,29,30.

Cert-pin:

- CNF: `/tmp/F450/aux_expose_sr60_n32_bit13_m916a56aa_fillffffffff_F450_certpin.cnf`
- sha256: `623646b6ea0c9c3828cdcf9a63898f8c41096d148b4e922f7530c0788d1af508`
- kissat 4.0.4: UNSAT, ~0.02s
- cadical 3.0.0: UNSAT, ~0.04s

### bit28_md1acca79: HW=44

Previous bit28 record: HW=45 from F408/F427.

New witness:

- W1 = `0x307cf0e7 0x853d504a 0x78f16a5e 0x65f469f2`
- W2 = `0x6fcdf313 0xaa562d8d 0x5713c149 0x0b5cc916`
- HW=44
- score=71.526
- hw63=`[9,10,2,0,14,5,4,0]`
- diff63=`[0xa6003520,0xea241005,0x08000004,0x00000000,0xe50ec099,0x20044024,0x1800000c,0x00000000]`
- move from F408/F427 HW45: W60 bits 1,2,7,8,9,19,26,29.

Cert-pin:

- CNF: `/tmp/F450/aux_expose_sr60_n32_bit28_md1acca79_fillffffffff_F450_certpin.cnf`
- sha256: `cf67615197fc1790ca1f61540b1cc85920aae51baacc04f0716aa42487a0de2d`
- kissat 4.0.4: UNSAT, ~0.02s
- cadical 3.0.0: UNSAT, ~0.03s

## Current Path C Panel

| Candidate | Previous HW | New HW | Status |
|---|---:|---:|---|
| bit13_m916a56aa | 44 | 42 | new global Path C floor |
| bit24_mdc27e18c | 43 | 43 | still second |
| bit28_md1acca79 | 45 | 44 | improved |

## Verdict

F449's pivot was correct: scalar local ranking looked boxed in, but
compensation-aware pair-beam composition found a new floor quickly. These
are still near-residuals, not full collisions, because cert-pin is UNSAT
under both solvers.

Next actions:

1. Hamming-3 / radius-4 exact closure around bit13 HW42.
2. Repeat pair-beam with wider pools and alternate c/g penalties from the
   HW42 seed.
3. Cert-pin any further HW<42 witness immediately.
