# F148: bit28_HW59 fixture for yale's absorber search — structurally distinguished cand testbed

**2026-04-28**

## Summary

F146 coordination message recommended yale test bit28_md1acca79
(structurally distinguished per F143: de58_size=2048, hardlock_bits=15)
as a likely-lower-floor target for the F110/F111 absorber search.

This memo PROVIDES the analog fixture so yale can drop it into the
existing search loop without building it from scratch.

## What's shipped

`headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit28_HW59_naive_blocktwo.json`

- Schema: 2blockcertpin/v1 (matches bit3_HW55_naive_blocktwo)
- Cand: bit28_md1acca79_fillffffffff
- Witness: bit28_HW59_naive_blocktwo_test_F148 (lowest HW from F101
  bit28 corpus, 18,633 records)
- residual_hw: 59 (vs bit3's 55, comparable order)
- block2: naive_no_constraints (FORWARD_BROKEN baseline)

## Validator output

```
$ python3 simulate_2block_absorption.py bit28_HW59_naive_blocktwo.json --n-samples 50

Verdict:   FORWARD_BROKEN
Block-1 working-state residual HW: 59 (matches bundle)
Block-2 chain-input diff HW:       69
Block-2 forward simulation:
  Samples:                        50
  Block-2 final chain-diff HW:     107 - 146 (median 130)
  Exact target matches:           0
```

Comparable structure to bit3_HW55 (yale found median 119 baseline,
score 86 after search). The bit28 baseline median is 130 — slightly
higher than bit3's 119, but the structural distinction (hardlock=15)
should give a LOWER floor after search.

## Drop-in commands for yale

Replace `bit3_HW55_naive_blocktwo.json` with the new fixture in any
of yale's F110/F111/F123 commands:

```bash
# F110 dense search
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit28_HW59_naive_blocktwo.json \
  --restarts 16 --iterations 20000 --seed 101 \
  --out-json /tmp/bit28_absorb_search_16x20k.json

# F111 active subset scan
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit28_HW59_naive_blocktwo.json \
  --pool 0,1,5,7,8,9,10,11,12,13,14 --sizes 3-5 \
  --restarts 3 --iterations 4000 --limit 80 \
  --out-json /tmp/bit28_subset_scan.json
```

## Predicted outcomes

If F143's structural-distinction hypothesis is correct:
- bit28 score floor < bit3's 86 (predicted: 70-85 range)
- bit28 active-word distribution might differ from bit3's {0,1,2,8,9}
  (different cand → different W-positions productive)
- The radius-2 local minimum from F123 might NOT hold on bit28 if
  the structural priors are sufficient (lower-energy clusters more
  accessible)

If outcomes match prediction: F143 hypothesis empirically confirmed,
yale's heuristic can be re-targeted at structurally distinguished
cands as a class.

If outcomes contradict prediction: F143 framing is wrong; structural
distinction doesn't transfer to absorber-search yield. Refines the
principles framework.

Either outcome is informative.

## Connection to other shipped today

- **F143** (macbook 2026-04-28): structurally-distinguished cands
  target list. Predicted bit28 advantage.
- **F146** (macbook 2026-04-28): coordination message to yale with
  same suggestion.
- **F148** (this memo): provides the FIXTURE so yale can act on the
  suggestion without setup overhead.

## Files

- Fixture: `bets/block2_wang/trails/sample_trail_bundles/bit28_HW59_naive_blocktwo.json`
- Memo: this file
- Builder: `/tmp/build_bit28_fixture.py` (one-shot, can be re-derived
  from F101 corpus if needed)

## Discipline

- 0 SAT compute (only forward simulation for validation, ~50 samples)
- 0 solver runs to log
- Fixture extends, not replaces, bit3 fixture
- All commands in this memo are for yale's existing scripts
  (no new tooling needed)

## Status

Ready for yale's next iteration. Drop in the bit28 fixture, run F110
or F111, compare score floor to bit3's 86. If yale picks this up
empirically, the F143/F146/F148 chain delivers a concrete cross-bet
empirical experiment.
