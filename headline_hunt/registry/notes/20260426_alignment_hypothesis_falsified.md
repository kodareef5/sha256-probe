# Σ1/σ1 alignment hypothesis FALSIFIED at bit=18 — 2 NEW candidates discovered
**2026-04-26 ~01:00 EDT** — registry/notes/

## Setup

Tested the hypothesis from `registry/notes/20260425_covered_bits_pattern.md`:
"σ0-aligned bits {3, 7, 18} have 0 cascade-eligible m0 at N=32."

Method: full 2^32 m0 sweep at (0,9) word-pair, fill=0xffffffff, for each
of bits 7, 18, 22 (and bit=31 sanity).

## Results

| Bit | Alignment       | Eligible / 2^32 | Hypothesis | Outcome |
|----:|-----------------|:---------------:|:----------:|---------|
|  31 | boundary (MSB)  | 2 (cert + a22d) |  N/A       | sanity OK |
|   7 | σ0-aligned      | 0               | predicted 0 | HOLDS at bit=7 |
|  18 | σ0-aligned      | **2 NEW**       | predicted 0 | **FALSIFIED at bit=18** |
|  22 | Σ0-aligned      | running         | predicted 0 | TBD |

bit=18 produced TWO new candidates not in the prior 36-candidate registry:
- **m = 0x99bf552b** (hw56=127, de58 image=130086, hardlock_bits=1)
- **m = 0xcbe11dc1** (hw56=146, de58 image=102922, hardlock_bits=9)

Both verified via `lib.sha256.precompute_state` Python implementation
(da_56=0). Both written into `cnfs_n32/` as cascade-augmented sr=61 CNFs,
both audit CONFIRMED.

## What this CHANGES

1. **Hypothesis FALSIFIED**: σ0-alignment is NOT a structural blocker for
   cascade-eligibility. bit=18 produced eligibility at the same 2-per-2^32
   rate as bit=31 (both ~2^-31).

2. **Registry now 38 candidates**: cand_n32_bit18_m99bf552b_fillffffffff,
   cand_n32_bit18_mcbe11dc1_fillffffffff added. Both cascade-eligible,
   both in fresh CNFs.

3. **bit=18 is the FIRST registered σ0-aligned bit position.** The earlier
   covered set {0, 6, 10, 11, 13, 17, 19, 25, 31} was a curation artifact,
   not a structural ceiling. The pattern was OBSERVATION BIAS: the
   curators searched specific bits that happened to be Σ1/σ1-aligned;
   σ0-aligned bits weren't searched, not "non-eligible".

4. **bit=7 result remains 0/2^32** — but this is statistically consistent
   with 2^-31 baseline rate (Poisson(2) variance includes 0). Doesn't
   prove bit=7 is structurally non-eligible; just unlucky in this sweep.

5. **The "registry is exhaustive at fill=0xff" claim** (from bit=31's
   2-per-2^32 result) needs softening: registry was exhaustive at THAT
   (bit, fill) cell. Other (bit, fill) cells may have undiscovered candidates.

## What this gives the bet portfolio

- **Two new candidates for sr61_n32**: bit-18 family. Untested in solver.
  Worth a multi-budget kissat run when fleet has cycles.
- **Candidate-base expansion strategy**: exhaustive sweep at additional
  (bit, fill) cells. Per cell ETA: ~12 min on M5 with 10 OMP threads.
  Cells uncovered: 23 bits × 4 fills = ~92 cells. Total ~18 hr if all
  swept. Expected new candidates: ~92 × 2 = ~180 (assuming uniform 2-per-cell).

- **Updated alignment hypothesis** (still partially supported):
  - Boundary bits 0, 31: covered ✓
  - Σ1 amounts {6, 11, 25}: covered ✓
  - σ1 amounts {17, 19, 10}: covered ✓
  - Σ0 amounts {2, 13, 22}: 1 of 3 covered (13)
  - σ0 amounts {7, 18, 3}: 0 of 3 covered ❌ (FALSIFIED at bit=18)

  Maybe the SET of cascade-eligible bits is broader than initially
  suspected, just under-curated.

## Caveats

- All sweeps at fill=0xffffffff. Other fills not exhaustively swept.
  bit=18 might have very different counts at other fills.
- Confidence in 0-eligibility at bit=7 is statistical — Poisson 0 is
  consistent with rate 2^-31. Need exhaustive sweep at MULTIPLE fills
  for robust closure.
- Registry expansion mechanic: each new candidate requires CNF
  generation, fingerprint check, BET.yaml/mechanisms.yaml update.
  Done for these 2; future bit-18-fill-other discoveries should follow
  same pattern.

## Files

- `headline_hunt/registry/notes/cascade_eligibility_sweep.c`: the sweep tool.
- `cnfs_n32/sr61_cascade_m99bf552b_fffffffff_bit18.cnf`: new CNF #1.
- `cnfs_n32/sr61_cascade_mcbe11dc1_fffffffff_bit18.cnf`: new CNF #2.
- `headline_hunt/registry/candidates.yaml`: 2 new candidate entries.
- `headline_hunt/registry/kernels.yaml`: new kernel_0_9_bit18 entry.
