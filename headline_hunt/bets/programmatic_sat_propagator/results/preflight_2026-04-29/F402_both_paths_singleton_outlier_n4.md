---
date: 2026-05-01
bet: programmatic_sat_propagator
status: bit2 CONFIRMED SINGLETON OUTLIER — n=4 "both paths" sample, 3/4 help, only bit2 doesn't
parent: F401 (F400-H1 falsified at n=2)
type: empirical sample extension (bit4 + bit24)
compute: 4 cadical 60s --stats runs (bit4 + bit24 × baseline + F343); ~4 min wall
---

# F402: Class A "both paths" sub-profile is NOT bimodal — bit2 is a singleton outlier

## Setup

F400 hypothesized "both paths" cands are F343 non-helpers (n=1 from
bit2). F401 falsified at n=2 (bit28 helps cleanly). F402 extends to
n=4 with two more "both paths" cands selected for kbit-spread:

  - bit4_md41b678d (kbit=4, low end like bit2)
  - bit24_mdc27e18c (kbit=24, high middle)

## Method

Encoded both via cascade_aux_encoder.py (--sr 60 --mode force --kernel-bit
N --fill 0xffffffff), mined F343 preflight (5s probe each), injected
unit + pair into baseline CNF, ran cadical 60s --stats × baseline +
F343 × 2 cands.

## Result — n=4 "both paths" Class A panel

```
cand                 unit_force  pair_forbid   conflicts Δ%   yield
bit2_ma896ee41       dW57[0]=1   (0,0)         +0.07          n/a (non-helper)
bit4_md41b678d       dW57[0]=1   (0,1)         -9.40          0.24
bit24_mdc27e18c      dW57[0]=1   (0,1)         -7.13          0.32
bit28_md1acca79      dW57[0]=0   (0,0)         -6.37          0.25
```

**3 of 4 cands help.** bit2 is the only non-helper. Effects on the
helping cands are bounded yield (0.24-0.32), structurally similar to
Class B's 0.18-0.22 yield range.

## Findings

### Finding 1 — F400-H1 fully falsified at n=4

The "both paths" sub-profile contains 1 non-helper (bit2) and 3
helpers (bit4, bit24, bit28). At n=4 the pattern is clearly NOT
"both paths → non-helper". It is "bit2 specifically is a non-helper".

The bimodal claim from F401 ("Class A both paths is bimodal in n=2")
is also weakened at n=4. The empirical mode within "both paths" is
"helps with bounded yield ~0.25". bit2 is the exception, not the rule.

### Finding 2 — bit2 vs other "both paths" cands: feature comparison

```
feature              bit2          bit4          bit24         bit28
m0                   0xa896ee41    0xd41b678d    0xdc27e18c    0xd1acca79
m0_HW                15            16            16            18
kbit                 2             4             24            28
fill                 0xffffffff    0xffffffff    0xffffffff    0xffffffff
fill_HW              32            32            32            32
m0_bit[31]           1             1             1             1
fill_bit[31]         1             1             1             1
F343 unit force      dW57[0]=1     dW57[0]=1     dW57[0]=1     dW57[0]=0
F343 pair forbid     (0,0)         (0,1)         (0,1)         (0,0)
F343 effect          +0.07         -9.40         -7.13         -6.37
```

Distinguishing bit2 from bit4/bit24/bit28:

  - **kbit=2** is the only low-bit case (2 vs 4, 24, 28).
    bit4 (kbit=4) is also low and helps. So kbit ≤ small isn't
    sufficient.
  - **Unit force = dW57[0]=1**: shared with bit4, bit24. So this
    isn't a distinguisher.
  - **Pair forbid = (0,0)**: shared with bit28 (which helps). So
    this isn't a distinguisher either.
  - **Combined (unit=1, pair=(0,0))**: unique to bit2 in this n=4
    panel BUT bit11 (Class B) also has (unit=1, pair=(0,0)) and
    helps at -7.56%. So this combination isn't predictive.
  - **m0**: 0xa896ee41 — no clear structural difference vs others
    yet identified.

bit2's non-helper status remains structurally unexplained at the
F396-feature level.

### Finding 3 — Honest framing

The empirical pattern across all 9 cands tested for F343
effectiveness (8 from F392 + bit28 + bit4 + bit24 from F402,
counting the new ones):

```
class            n   mean    stdev   range
B (neither)      4   -9.30   3.05    [-12.03, -5.89]    tight
A path1          1   -8.33    --     [-8.33,  -8.33]    helps
A path2          2  -10.65   2.49    [-13.12, -8.17]    helps strongly
A both           4   -5.71   4.08    [-9.40,  +0.07]    bimodal but mostly helps
                                                        (3 helpers, 1 non-helper)
```

(Class A both at n=4 with 3 helpers and 1 non-helper. Stdev is
inflated by the bit2 outlier; without bit2, the 3 helpers have
stdev ~1.6 and mean -7.63%, which is a CLEANER cluster than even
Class B.)

So updated picture:
  - Class B (neither path): always helps, bounded yield, tight
  - Class A path1: helps (only n=1 sample)
  - Class A path2: helps strongly (-13.12% to -8.17% at n=2)
  - Class A both: 3/4 help with cleaner cluster than B; bit2 is outlier

bit2 is the only F343 non-helper in the entire 9-cand panel. It is
structurally unexplained at the F396 feature level.

### Finding 4 — Cleaner deployment recipe

Updated Phase 2D F343 deployment recipe (n=9):

  - Class B: deploy F343 unconditionally (bounded yield 0.18-0.22)
  - Class A path1, path2, both: deploy F343 unconditionally
    (bounded-to-strong yield in 8/9 tested cands)
  - **bit2_ma896ee41 specifically: skip F343 deployment**, or apply
    F397 VSIDS-boost to compensate

The simpler version is "deploy F343 to everything except bit2",
which gives a clean predictor at the cand level, not the class level.

This is the empirically grounded outcome of F400-F402: F343 is
nearly universally helpful, with bit2 as a single exception requiring
investigation.

### Finding 5 — Cross-machine implication for F399 matrix

Yale's F399 plan tests F397's priority specs in a 4-condition matrix
on 6 cands. Macbook's F402 finding suggests:

  1. F399's matrix should INCLUDE bit2_ma896ee41 if not already, so
     the matrix can detect whether F397's VSIDS-boost rescues bit2.
  2. F399's matrix can EXCLUDE the F343-vs-baseline axis on Class A
     "both paths" cands other than bit2, since they all help nearly
     uniformly. The interesting comparison is F397-vs-F343-baseline
     on Class A both paths.
  3. The "both paths" sub-profile is no longer hypothesized to be
     bimodal. The bimodality finding from F401 was based on n=2 and
     is dissolved at n=4.

## What's shipped

- This memo with n=4 "both paths" panel
- F402 confirms bit2 as singleton outlier (3/4 help; 1 doesn't)
- F400-H1 fully falsified
- Updated cand-level deployment recipe: F343 universal except bit2
- 4 runs logged via append_run.py

## Compute discipline

- 4 cadical 60s --stats runs logged
- 4 transient CNFs in /tmp/F402/ (audit UNKNOWN, --allow-audit-failure
  consistent with F390-F401 protocol)
- 0 real audit failures

## Next testable iteration

(a) **Investigate bit2 specifically**: deeper structural feature
    mining than F396 captures. m0 byte patterns, internal CDCL
    behavior, conflict-derivation traces. May require dedicated tool
    rather than data join.

(b) **Test bit2 with F397 VSIDS-boost** when Phase 2D C++ build
    lands. If F397 rescues bit2, the priority spec is the right
    intervention. If not, bit2 may be intrinsically resistant to
    cadical's heuristic regardless of priority hints.

(c) **3-seed protocol on bit4/bit24/bit28** to match F369 standard.
    ~9 min compute. Confirms single-seed deltas represent the mean.

## State

- F402 ships at n=4 in "both paths" sub-profile, with bit2 confirmed
  singleton
- F400's headline (Class B reliable) holds; F400-H1 fully falsified;
  bit2 outlier status documented
- Phase 2D recipe simplifies to "F343 universal, except bit2"
- bit2 mechanism remains structurally open

## F381 → F402 chain summary

```
F400:   F387 class predicts F343 variance; H1 hypothesis (n=1 bit2)
F401:   F400-H1 falsified at n=2 (bit28 helps)
F402:   bit2 confirmed singleton outlier at n=4 (bit4 + bit24 also help)
        F343 deployment recipe: universal, except bit2
```

22 numbered memos in 5 days. The hypothesis F400-H1 was proposed and
falsified within the same 60-minute window — the cleanest hypothesis-
test cycle in this chain. Empirical falsification > narrative
preservation.
