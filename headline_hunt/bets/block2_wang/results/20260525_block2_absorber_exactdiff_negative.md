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

## Honest scope

Triage-level (n=40); the tools' own docstrings call this a "design probe, not a
solver." Confirms the naive-blocktwo exact-diff approach is insufficient and pinpoints
the residual<->absorber integration gap; does not by itself close or advance the bet.
