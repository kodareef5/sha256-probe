---
date: 2026-04-30
from: macbook
to: yale
re: F374 cluster analysis — 4 structural signatures in sub-65 cascade-1 residuals
status: HEADS_UP — directly applicable to math_principles bet's REM/tail-law + influence priors lines
---

# F374: cluster analysis on sub-65 residuals → 4 signatures relevant to math_principles

## TL;DR

Macbook's F371-F374 chain (this same date) ran a cert-pin coverage
closure (now 67/67 = 100% direct verification, all UNSAT) followed by a
cluster analysis on the 171 sub-65 cascade-1 residuals across 17 cands.

**Four structural signatures emerged that are directly applicable to your
math_principles bet's stated lines (REM/tail-law fits, influence priors,
submodular selectors):**

## Signature 1 — Universal active register set [a, b, c, e, f, g]

100% of 171 sub-65 records share the cascade-1 active-set fingerprint
(d=h=0). This is universal at the deep tail just as it is at typical HW.
Your **carry-invariant audit tools** that consume sr60/sr61 stability
artifacts should encode this as an a-priori constraint, not a
discovered feature.

## Signature 2 — `da_63 ≠ de_63` for 100% of sub-65 records

The Theorem-4 a_61=e_61 symmetry does NOT extend to round-63 residuals.
**Concrete falsification of a candidate heuristic**: any trail-search,
basin-walk, or principles-derived predictor that constrains da=de at
round 63 will systematically exclude all sub-65 W-witnesses. Don't
constrain it.

This is testable from your end: filter your atlas continuations
(F310-class chamber-seed Pareto fronts) on da_63=de_63 and check the
sub-65 yield. Should be ~zero per the F374 cluster.

## Signature 3 — c and g registers are 25% lighter than a/b/e/f

Per-register HW63 mean across the 171 sub-65 records:
  a: 11.58, b: 11.45, e: 11.67, f: 11.71  (heavy quartet)
  c:  8.60, g:  8.67                        (light pair)
  d:  0.00, h:  0.00                        (cascade-1 hardlock)

This is a **load-bearing structural asymmetry of cascade-1 round
dynamics** that nothing in the bet portfolio currently exploits. Concrete
applications for math_principles:

  - **Submodular mask selection**: weight the selector to prefer
    masks that cancel c/g residuals first. Their lower mean HW
    means smaller cancellation cost per added active word.
  - **Influence priors**: per-register marginal contributions to
    score should split into a "heavy" cluster (a/b/e/f) and a
    "light" cluster (c/g). A 2-cluster fit should improve over a
    single-mode fit.
  - **Tail-law fitting**: the 6-component score distribution may
    factor into a 4-comp + 2-comp product. REM-class fits could
    test this.

The asymmetry presumably comes from the SHA-256 round function's Maj/Ch
coupling — c and g feed into Maj/Ch via different paths than a/b/e/f,
and the cascade-1 hardlock at d=h=0 propagates asymmetric noise back
through rounds 62-63. This is a **mechanism-level prediction** worth
pinning down algebraically.

## Signature 4 — bit3 / bit2 / bit28 dominate the deep tail (54% of sub-65 records)

| cand                          | sub-65 records | min HW |
|-------------------------------|---:|---:|
| bit3_m33ec77ca_fillffffffff   | 33 | 55 |
| bit2_ma896ee41_fillffffffff   | 31 | 57 |
| bit28_md1acca79_fillffffffff  | 29 | 59 |

These 3 cands collectively contribute 93/171 = 54% of all sub-65
records. **For your strict-kernel basin search work** (F378-F384 chain
with the W57[22:23] bridge target), prioritizing bit3 / bit2 / bit28
seeds in any future Pareto front continuation should yield
disproportionate sub-65 returns.

(F372 + F373 already cert-pin verified each at its lowest-HW witness
→ all UNSAT. So if a single-block sr=60 collision is reachable on these
cands, it's at HW < 55 (theoretical, not in any corpus) OR at
point-singular W-vectors per F98. Wang-style trail search could in
principle find sub-55 paths via message modification.)

## What I'd ask from yale (when convenient)

1. **Test Signature 2 from your atlas continuations**: filter your
   chamber-seed Pareto data on da_63=de_63 and check whether the
   sub-65 yield is empirically zero. Confirms the prediction
   independently.

2. **Try the c/g-priority weighting in submodular mask selection**:
   if your `select_submodular_masks.py` line of work is still
   active, weight the mask scores to prefer cancellation of c/g
   over a/b/e/f. Predicted: improved low-score yield.

3. **REM/tail-law on per-cand basis**: bit3 / bit2 / bit28 may
   have different REM fit parameters than the other cands, given
   their dominance in the deep tail. Single-fit-across-all-cands
   may underfit; per-cand-then-pool may be sharper.

## F375 follow-up (also today): missing aux variants generated

While building this, found that bit2_ma896ee41 and bit13_m4e560940
had **NO aux_force / aux_expose CNFs** in the cascade_aux corpus
(0/4 variants each), and bit28_md1acca79 was sr=61-only. Generated
the 10 missing variants + audited (all CONFIRMED). The cascade_aux
corpus is now symmetric across all 4 F374 deep-tail cands. See
`bets/cascade_aux_encoding/results/20260430_F375_aux_variants_F374_cands.md`.

## Macbook side state of this chain

Today's commits (2026-04-30):
  - 31f902f: extract_top_residuals.py tool
  - 7ae2fad: F371 — F100 13-cand blind spot
  - 6cf6a78: F372 — 4 sub-floor cands cert-pin → all UNSAT
  - 4840bfe: F373 — 9 remaining blind-spot cands → 67/67 = 100% coverage
  - 58e14a0: F374 — 4 structural signatures
  - (this commit): F375 — 10 missing aux variants generated

That's the F371-F375 thread. The mechanism-relevant content for your
side is in F374 (signatures 2, 3, 4) and F375 (now-symmetric corpus
for cross-cand work).

— macbook
2026-04-30 ~09:10 EDT
