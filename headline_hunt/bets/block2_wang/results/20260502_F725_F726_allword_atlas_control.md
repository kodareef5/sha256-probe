---
date: 2026-05-02
bet: block2_wang
status: ALLWORD_ATLAS_CONTROL_AND_KERNEL_VALIDATION
evidence_level: SEARCH_ARTIFACTS
compute: 16 restarts x 50k atlas-loss iterations
author: yale-codex
---

# F725/F726: all-word atlas control vs kernel-preserving validation

## Why this was run

After F717/F724 boxed in two late-W local operators, I revisited the older
atlas-loss thread. F312 suggested trying a larger active mask, but F322 later
retracted the drift-allowed F315/F320 claims because `search_schedule_space.py`
lets M2 drift outside the cascade-1 kernel.

So this pair is deliberately split:

- F725: all-16 active-word drift-allowed control. Informative about the loss
  landscape only, not a cascade-1 claim.
- F726: same 8x50k budget with `M2 = M1 ^ kernel` enforced by
  `search_kernel_preserving.py`.

## F725 drift-allowed control

Artifact:

- `results/search_artifacts/20260502_F725_schedule_space_allwords_8x50k.json`

Best result:

- score 27.60
- a57_xor_hw 3
- D61_hw 10
- chart `(dh, dCh)`

This is the kind of tempting result F322 warned about. It is not cascade-1
valid because the mutator can change the M1/M2 difference outside the fixed
kernel.

## F726 kernel-preserving all-word run

Artifact:

- `results/search_artifacts/20260502_F726_kernel_preserving_allwords_8x50k.json`

Setup:

- init: yale F358 chamber-seed JSON
- active M1 words: all 16
- M2 always derived as `M1 ^ kernel`
- kernel nonzero words: M0 and M9, both `0x80000000`
- 8 restarts x 50k iterations

| Restart | Score | a57 | D61 | Chart | Chamber hits |
|---:|---:|---:|---:|---|---:|
| 0 | 42.90 | 6 | 13 | `(dh, dCh)` | 0 |
| 1 | 44.75 | 4 | 14 | `(dh, dSig1)` | 0 |
| 2 | 43.05 | 7 | 9 | `(dh, dCh)` | 0 |
| 3 | 40.40 | 5 | 14 | `(dCh, dh)` | 0 |
| 4 | 41.80 | 7 | 8 | `(dCh, dh)` | 0 |
| 5 | 45.00 | 7 | 11 | `(dCh, dh)` | 0 |
| 6 | 41.95 | 6 | 12 | `(dh, dCh)` | 0 |
| 7 | 47.00 | 7 | 13 | `(dh, dCh)` | 0 |

## Interpretation

The all-word kernel-preserving search does **not** beat the prior true
cascade-1 baseline:

- F322 random kernel-preserving baseline: score 39.65, a57 floor 5, best
  chamber D61 8.
- F726 all-word seeded run: score 40.40, a57 minimum 4, best chamber D61 8.

The one real new wrinkle is that all-word kernel-preserving mutation can hit
a57=4, but it did so in a non-chamber chart `(dh, dSig1)` and with D61=14.
That supports the same structural read as before: lowering a57 alone is not
the hard part; lowering it while staying in the chamber chart is.

## Verdict

No chamber hit. No true cascade-1 atlas improvement.

Use F725 only as a drift-allowed control. For any future cascade-1 claim, use
kernel-preserving search or an evaluator that rejects non-kernel M1/M2 pairs.
