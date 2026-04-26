# (0,9) uncovered bit positions at N=32 — 0/942k random scan
**2026-04-25 evening** — registry/notes

## Question

The 36 registered (0,9) candidates cover bit positions
{0, 6, 10, 11, 13, 17, 19, 25, 31} — 9 of 32 bits. The other 23 bits
{1, 2, 3, 4, 5, 7, 8, 9, 12, 14, 15, 16, 18, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30}
have NO registered candidate.

Question: are the uncovered bits **structurally NOT eligible** at N=32, or
just **uncurated** (eligibility exists but random search hasn't found them)?

## Method

Random sample: 23 uncovered bits × 5 fills × 8192 random m0 = 942,080 trials
at N=32. Test cascade-eligibility (a-state collision at slot 56).

## Result

**0 cascade-eligible found in 942,080 trials.** Wall: 211s.

## Interpretation

Expected hits at the cascade-eligibility baseline rate of ~2^-32 per trial:
942080 / 2^32 = **0.000219 expected hits**. Observed 0 is well within
Poisson(0.0002) — does NOT distinguish "rate exactly 0" from "rate ~2^-32".

**This scan does NOT prove uncovered bits are structurally non-eligible.**
It just confirms eligibility is rare enough that 1M-class random sampling
won't find new candidates.

## What this CHANGES for the bet portfolio

- Random m0 sampling at uncovered bit positions is NOT a productive way
  to expand the candidate base.
- To find eligible m0 at uncovered bit positions would require either:
  - Exhaustive 2^32 m0 sweep per (bit, fill): ~5 min in C, ~hours in Python.
  - Theoretical analysis of WHY specific bits {0, 6, 10, 11, 13, 17, 19, 25, 31}
    happened to be sampled in the original curation (perhaps a structural
    bias related to Σ0/Σ1/σ0/σ1 rotation/shift offsets).
- The registry's bit coverage may be ROBUST already; expanding it is not
  cheap.

## Implication for sr61_n32 strategy

Future workers asking "can we find more candidates?" should NOT random-
sample at uncovered bits. Either:
1. Compute-budget a 2^32 sweep at one specific uncovered bit (one-shot
   ~5 min C run).
2. Re-derive from the cascade-eligibility theory why specific bits dominate.
3. Accept the 36-candidate pool as the search space and focus on encoding
   diversity (cascade vs cascade_aux Mode A/B vs derived) rather than
   candidate diversity.

Per validation matrix verdict (predictor null in dec/conf, wall, conf/sec
across 12 cells), the 36-candidate pool is sufficient sample for
candidate-level conclusions; #36 is not the bottleneck.

## Files

- `headline_hunt/registry/notes/20260425_uncovered_bits_scan.md` (this)
- 942k trials in 211s on macbook M5
