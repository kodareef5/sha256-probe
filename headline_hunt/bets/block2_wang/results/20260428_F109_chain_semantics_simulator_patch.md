# F109: simulator chain semantics patch - block-2 input diff made explicit
**2026-04-28**

## Summary

Review of F104/F106 found a terminology bug in the 2-block handoff:
`block1.residual_state_diff` is the round-63 working-state XOR diff,
but block 2 starts from the post-feed-forward chaining output. Those
diffs are equal only in special cases.

For the F106 bit3 HW55 fixture:

```
block1 working-state residual HW: 55
block2 chain-input diff HW:       68
block2 final chain-diff HW:       114 - 137, median 132 (5 samples)
```

The FORWARD_BROKEN verdict still holds, but the interpretation changes:
the second block is absorbing the chain-input diff, not the raw
working-state residual.

## Changes

- `simulate_2block_absorption.py` now reports both values:
  - block-1 working-state residual HW
  - block-2 chain-input diff HW
- Final scoring now compares the full final chain-output diff against
  the declared target vector, using Hamming distance to target.
- Unsupported constraints are rejected instead of silently ignored:
  late schedule-word pins at rounds 25..63, `bit_condition`, and
  `modular_relation` now return `UNSUPPORTED_CONSTRAINTS`.
- Early derived schedule constraints are now synthesized for
  `exact`/`exact_diff` at W2 rounds 16..24, using direct additive
  message-word handles and a final schedule verification pass.
- `2BLOCK_CERTPIN_SPEC.md` now states that a full collision target is
  zero final chaining-output diff, not merely zero round-63 working-state
  diff.
- The trail validator now validates optional `block1.W2_57_60` shape.
- `trails/audit_chain_semantics.py` reports the working-state residual
  HW and derived block-2 chain-input HW for one bundle or a directory of
  bundles.
- `encoders/sweep_w2_exactdiff.py` ranks simple one-round W2
  `exact_diff` probes over supported rounds 0..24.

## Verification

```
python3 headline_hunt/bets/block2_wang/trails/validate_trail_bundle.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/m17149975_trivial_v1.json
# VALID

python3 headline_hunt/bets/block2_wang/trails/validate_trail_bundle.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json
# VALID

PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/simulate_2block_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/m17149975_trivial_v1.json \
  --n-samples 5
# Verdict: COLLISIONS_FOUND
# Block-2 chain-input diff HW: 0

PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/simulate_2block_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --n-samples 5
# Verdict: FORWARD_BROKEN
# Block-1 working-state residual HW: 55
# Block-2 chain-input diff HW: 68

python3 headline_hunt/infra/validate_registry.py
# 0 errors, 0 warnings

python3 headline_hunt/bets/block2_wang/trails/audit_chain_semantics.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/
# OK workingHW=0 chainHW=0 for m17149975
# OK workingHW=55 chainHW=68 for bit3_HW55

python3 -c 'from headline_hunt.bets.block2_wang.encoders.simulate_2block_absorption import build_schedule,synthesize_block2_W2; cs=[{"round":16,"type":"exact_diff","diff":"0xffffffff"},{"round":17,"type":"exact_diff","diff":"0x12345678"},{"round":24,"type":"exact_diff","diff":"0x0badc0de"}]; m1,m2=synthesize_block2_W2(cs,seed=7); w1,w2=build_schedule(m1),build_schedule(m2); print(hex(w1[16]^w2[16]), hex(w1[17]^w2[17]), hex(w1[24]^w2[24]))'
# 0xffffffff 0x12345678 0xbadc0de

PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/sweep_w2_exactdiff.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --rounds 0-24 --diff-source chain --n-samples 10 --top-k 3
# baseline median target distance: 132
# best simple probe: round 14, diff chain_e=0x1043708e, median distance 118

PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/sweep_w2_exactdiff.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --rounds 0-24 --diff-source chain --n-samples 100 --top-k 3
# baseline median target distance: 127
# best simple probes: median distance 126, still FORWARD_BROKEN

PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/sweep_w2_exactdiff.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --rounds 0-24 --diff-source both --n-samples 100 --top-k 1
# best both-source probe: round 8, working_g=0x0d1e2020, median distance 125

python3 -c 'import json; from headline_hunt.bets.block2_wang.encoders.simulate_2block_absorption import simulate_bundle; b=json.load(open("headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json")); r=simulate_bundle(b,n_samples=1000); print(r["verdict"], r["min_target_distance"], r["median_target_distance"], r["max_target_distance"])'
# FORWARD_BROKEN 100 128 151

python3 -c 'import json; from headline_hunt.bets.block2_wang.encoders.simulate_2block_absorption import simulate_bundle; b=json.load(open("headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json")); b["block2"]["W2_constraints"]=[{"round":8,"type":"exact_diff","diff":"0x0d1e2020"}]; r=simulate_bundle(b,n_samples=1000); print(r["verdict"], r["min_target_distance"], r["median_target_distance"], r["max_target_distance"])'
# FORWARD_BROKEN 104 128 158
```

## Next

At low sample counts, the best single `exact_diff` chain-word probe looked
like it improved the bit3 fixture's median target distance from 132 to
118. A 100-sample validation showed that effect was mostly sampling noise:
the best one-round probes reached median distance 126 vs baseline 127, all
still FORWARD_BROKEN.

A depth-3 beam search also produced an apparently better 6-sample sequence,
but a 100-sample validation regressed to median distance 129 vs baseline
127. Treat small-sample sweep/beam output as triage only.

The most promising both-source one-round probe also failed a 1000-sample
validation: median target distance tied baseline at 128 and produced zero
near-target samples. Current evidence says single-word exact_diff probing is
not a productive absorber by itself.

Next useful implementation step: late-schedule support. Given a requested
`exact_diff` at W2[r] for r >= 25, search over compatible message words
W2[0..15] instead of rejecting it. That is the first point where a real
local solver becomes more appropriate than the current direct-additive
synthesizer.
