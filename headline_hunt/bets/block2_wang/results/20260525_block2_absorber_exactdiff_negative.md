---
date: 2026-05-25
bet: block2_wang
status: NEGATIVE + integration gap
author: macbook-claude
evidence_level: EVIDENCE (triage; n=40 samples)
---

# Block-2 W2-exact_diff absorption fails on naive bundles; HW35 residual not yet bundled

## What I ran

Probed the Phase-2 block-2 absorber on a sample trail bundle, reusing the existing
tools (`sweep_w2_exactdiff.py`, `beam_w2_exactdiff.py`) on
`trails/sample_trail_bundles/bit28_HW59_naive_blocktwo.json` (block-1 residual HW59).
Log/JSON: `results/runs/20260525_block2_absorb_probe/`.

## Result — FORWARD_BROKEN, pins don't absorb

```
baseline (no pins):  FORWARD_BROKEN  round-63 final HW: min 107, median 131
single W2 exact_diff pins (sweep, 150 cands): FORWARD_BROKEN, best minHW ~102
beam depth-3 (combine up to 3 pins, width 12): FORWARD_BROKEN, best minHW 102
  n_bc_full_collisions = 0 across the top-10
```

Combining pins (depth 3) gives **no improvement** over single pins (both ~102). The
deliberately-small `exact_diff`-pin vocabulary does **not** absorb even a HW59
residual through block-2 rounds 0–24 — it stays FORWARD_BROKEN, and the block-2 tail
actually inflates the round-63 distance (59 → ~102+). Consistent with the recent
F506–F959 "absorber" weights (~82–89) and "reserve triage / closed" verdicts: the
naive block-two is far from clean absorption.

## Integration gap (the actionable finding)

The block-1 residual frontier (bit13 **HW35**, the hard-won c/g pair-beam record) and
the block-2 absorber tooling are **disconnected**: the only trail bundles available
are *naive* (HW55–63), NOT built from the optimized HW35 residuals. So no one has
tested whether the optimized residual absorbs better than the naive one.

**Next concrete step (queued):** build a `2blockcertpin/v1` bundle from the bit13
HW35 record (W1=0x5228ed8d,0x61a1a29c,0x6a7a8409,0xc7d515db) via
`trails/validate_trail_bundle.py`, then run `sweep/beam_w2_exactdiff` on it. If the
HW35 residual still gives FORWARD_BROKEN, the exact-diff-pin absorber is structurally
insufficient and the bet needs the real Wang trail engine (local collisions +
message modification, kill_criteria #1: >18 rounds). If it improves, residual-min
pays off and the pipelines should be wired together.

## INTEGRATION TEST (same day): the HW35 residual does NOT help block-2 absorption

Built the missing bundle from the bit13 HW35 record (encoders/build_bundle_from_record.py,
reuses run_full): `results/runs/20260525_block2_absorb_probe/bit13_HW35_from_record.json`
(validated against the 2blockcertpin/v1 schema). Residual HW=35, and notably
**c63 = g63 = 0x80000000** — at the deep frontier the c/g "lock" is exactly the MSB.

Ran the same block-2 absorber probes on it:

```
HW35 bundle:  baseline FORWARD_BROKEN, dist median 127
  sweep (single pins):   FORWARD_BROKEN, best minD 105
  beam depth-3 (combine): FORWARD_BROKEN, best min final HW 105, 0 bit-condition collisions
vs HW59 naive bundle:    FORWARD_BROKEN, best ~102-109   (essentially identical)
```

**Minimizing the block-1 residual 59 -> 35 does NOT improve block-2 exact_diff
absorption** — both stay FORWARD_BROKEN at ~distance 105. So:
1. The hard-won residual-min work does not pay off for the exact-diff-pin absorber.
2. The exact_diff-pin absorber is structurally insufficient *regardless* of residual HW.
3. The bet's ONLY remaining path is the real **Wang trail engine** (local collisions +
   message modification through block-2 rounds, NOT just exact_diff pins) — kill_criteria #1
   (absorber trail > 18 rounds). That is a major concentrated-design build.

## Decision point (for the owner/user)

block2_wang's two pursued routes are now both characterized as insufficient on this
laptop's autonomous lane: (a) block-1 residual-minimization is deeply-worked/floored
(~HW35) AND doesn't help block-2; (b) the exact_diff-pin block-2 absorber is FORWARD_BROKEN
for both naive (HW59) and optimized (HW35) residuals. The remaining high-value path is the
**Wang trail engine** — a multi-day expert-cryptanalysis build (the bet's original premise,
never started). Recommend: a deliberate decision to commit to that build, or de-prioritize.

## Honest scope

Triage-level (n=40); the tools' own docstrings call this a "design probe, not a
solver." But the integration comparison (HW35 vs HW59, identical FORWARD_BROKEN) is a
clean apples-to-apples result on the same probe, and the c63=g63=MSB observation is exact.
