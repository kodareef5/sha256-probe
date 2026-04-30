---
date: 2026-04-30
bet: cascade_aux_encoding
status: CORPUS_HYGIENE — 10 missing aux variants generated for F374 deep-tail cands; all CONFIRMED
parent: F374 sub-65 cluster analysis
---

# F375: aux variants for F374 deep-tail cands (bit2, bit13, bit28)

## Setup

F374 identified bit3/bit2/bit28 as the 3 cands that dominate the deep
tail of the cascade-1 residual distribution (54% of all sub-65 records).
F371-F373 used aux_expose sr=60 cert-pin to verify the lowest-HW
witness for each → all UNSAT.

A coverage check found that the cascade_aux corpus had:
  - bit3_m33ec77ca:  4/4 aux variants present
  - bit2_ma896ee41:  **0/4 aux variants** (all missing)
  - bit13_m4e560940: **0/4 aux variants** (all missing)
  - bit28_md1acca79: 2/4 (sr=61 force + expose only; sr=60 missing)

bit13_m4e560940 is structurally interesting because it's the F374
fourth-place deep-tail cand AND the F371 fourth sub-floor cand
(HW=61 minimum). Without aux variants, it can't participate in any
F343-class preflight or aux_force/expose-mode comparison work.

F375 closes the gap.

## What was generated

Ran `cascade_aux_encoder.py` for each missing combination:

| cand           | sr=60 force | sr=60 expose | sr=61 force | sr=61 expose |
|----------------|:-----------:|:------------:|:-----------:|:------------:|
| bit2_ma896ee41 | NEW         | NEW          | NEW         | NEW          |
| bit13_m4e560940| NEW         | NEW          | NEW         | NEW          |
| bit28_md1acca79| NEW         | NEW          | (existed)   | (existed)    |

10 new CNFs + 10 varmap sidecars. All in
`headline_hunt/bets/cascade_aux_encoding/cnfs/`.

## Audit

Each ran through `audit_cnf.py --json`. **10/10 CONFIRMED.**

| CNF                                            | bucket                       | vars   | clauses |
|------------------------------------------------|------------------------------|-------:|--------:|
| aux_force_sr60_*_bit2_ma896ee41_*              | sr60_n32_cascade_aux_force   | 13252  | 54947   |
| aux_expose_sr60_*_bit2_ma896ee41_*             | sr60_n32_cascade_aux_expose  | 13252  | 54947   |
| aux_force_sr61_*_bit2_ma896ee41_*              | sr61_n32_cascade_aux_force   | 13526  | 56184   |
| aux_expose_sr61_*_bit2_ma896ee41_*             | sr61_n32_cascade_aux_expose  | 13526  | 56184   |
| aux_force_sr60_*_bit13_m4e560940_*             | sr60_n32_cascade_aux_force   | 13208  | 54737   |
| aux_expose_sr60_*_bit13_m4e560940_*            | sr60_n32_cascade_aux_expose  | 13208  | 54737   |
| aux_force_sr61_*_bit13_m4e560940_*             | sr61_n32_cascade_aux_force   | 13492  | 56009   |
| aux_expose_sr61_*_bit13_m4e560940_*            | sr61_n32_cascade_aux_expose  | 13492  | 56009   |
| aux_force_sr60_*_bit28_md1acca79_*             | sr60_n32_cascade_aux_force   | 13203  | 54737   |
| aux_expose_sr60_*_bit28_md1acca79_*            | sr60_n32_cascade_aux_expose  | 13203  | 54737   |

All 10 land within the existing fingerprint envelope. No range widening
needed.

## cnf_fingerprints.yaml updates

  - sr60_n32_cascade_aux_expose: observed_n_kernels 24 → 25, n_files 60 → 63
  - sr60_n32_cascade_aux_force:  observed_n_kernels 15 → 16, n_files 28 → 31
  - sr61_n32_cascade_aux_expose: observed_n_kernels 18 → 19, n_files 32 → 34
  - sr61_n32_cascade_aux_force:  observed_n_kernels 18 → 19, n_files 32 → 34
  - All buckets last_audited: 2026-04-30

`validate_registry.py`: 0 errors, 0 warnings post-edit.

## Implications

bit2_ma896ee41 and bit13_m4e560940 are now first-class participants in
the cascade_aux family. Future F343-class preflight clause mining,
F347-F369 conflict-reduction measurements, and any cross-cand sweep
will include them automatically.

bit28_md1acca79's sr=60 force/expose variants enable the F348-class
single-seed cross-cand injection test to extend to a 4th sub-floor cand
without hitting the F368 encoder-version mismatch (since these 10 CNFs
are all freshly built with the current encoder).

## Compute

- 10 × ~5s encoding = ~50s wall
- 10 × ~0.3s audit = ~3s wall
- Total: ~1 min routine
- 0 solver runs, 0 runs.jsonl entries (corpus generation only)

## What's shipped

- 10 new aux CNFs + varmaps in `bets/cascade_aux_encoding/cnfs/`
- `cnf_fingerprints.yaml` updated for 4 buckets (last_audited 2026-04-30)
- `20260430_F375_aux_variants_F374_cands.json` raw audit results
- This memo

## Cross-bet implications

- block2_wang: F374's bit3 cand had aux variants; bit2 + bit13 + bit28
  did not. With F375 the corpus is symmetrical across all 4 deep-tail
  cands. Future cluster/structural studies can use any of them
  interchangeably without "wait, I have to encode that one first".

- programmatic_sat_cascade_propagator: F343 preflight + F348 cross-cand
  measurements can now extend to bit2/bit13/bit28 at sr=60 force-mode
  without per-cand encoder gaps. If/when Phase 2D is built, the bit2
  + bit13 + bit28 cands give 3 fresh data points in addition to F348's
  5 existing cands.
