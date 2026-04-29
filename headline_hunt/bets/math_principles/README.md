# math_principles

This bet turns the April 2026 math-principles survey into small, checkable
tools. The first implementation slice focuses on measurement and triage rather
than new solver volume:

- shared manifest over existing artifacts
- REM/tail-law fit for block2 scores
- empirical influence priors for active words/pairs
- hard-core/carry-invariant audit from sr60/sr61 stability artifacts

The scripts are intentionally dependency-free and consume repo artifacts that
already exist.

## Current slice

Run these from the repo root:

```bash
python3 headline_hunt/bets/math_principles/encoders/build_principles_manifest.py
python3 headline_hunt/bets/math_principles/encoders/fit_tail_law.py
python3 headline_hunt/bets/math_principles/encoders/rank_influence_priors.py
python3 headline_hunt/bets/math_principles/encoders/audit_carry_invariants.py
```

Default outputs:

- `data/20260429_principles_manifest.jsonl`
- `results/20260429_manifest_summary.json`
- `results/20260429_F340_tail_law.{json,md}`
- `results/20260429_F341_influence_priors.{json,md}`
- `results/20260429_F342_carry_invariant_audit.{json,md}`

## Readout

F340 says the bit19 active-subset scores are not behaving like a plain REM
tail. Score <= 90 appears far more often than the Gaussian null predicts, so
the next search should treat the low-score masks as structured basins.

F341 gives the first active-word priors from that same corpus. Word 3 ranks
first; pairs `6,11`, `3,8`, `8,9`, and `1,3` are the strongest current pair
signals. The `{1,3}` axis survives as useful but not exclusive.

F342 promotes the late-round carry/core rule: sr60 has all last-two free-round
bits in stable core, and sr61 misses by one bit. First-free-round behavior is
still candidate-specific.

## Next tracks

- feed F341 priors into a submodular active-word selector
- use F342 stable-core coordinates as hard features for BP/matroid audits
- turn F340 low-score masks into explicit multi-seed basin-walk experiments
