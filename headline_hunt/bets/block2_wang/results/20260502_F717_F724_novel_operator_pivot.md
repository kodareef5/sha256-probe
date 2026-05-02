---
date: 2026-05-02
bet: block2_wang
status: PATH_C_NOVEL_OPERATOR_PIVOT_NEGATIVE
evidence_level: SEARCH_ARTIFACTS
compute: 8,435,441 multi-objective pair-beam expansions; 131,584 additive-W move candidates
author: yale-codex
---

# F717/F724: novel operator pivot

## Why this was run

After the selector-ranked tail pass started turning into rank consumption,
we pivoted away from "next manifest seed, same operator" and tested two
different coordinate changes:

1. `multi_objective_pair_beam.py` - keeps several beam objectives alive at
   once instead of ranking every state by one scalar.
2. `additive_w_move_probe.py` - probes modular `W +=/-= 2^bit` moves, not
   XOR bit flips, inspired by the additive common-mode absorber result in
   F127.

## New tools

- `headline_hunt/bets/block2_wang/encoders/multi_objective_pair_beam.py`
- `headline_hunt/bets/block2_wang/encoders/additive_w_move_probe.py`

The multi-objective beam preserves frontiers for total HW, c/g pressure,
lane balance, target-shape distance, bridge score, and explicit repair. The
additive probe tests whether carry-aware modular movement gives a better
local neighborhood than XOR flips.

## F717/F720 multi-objective pair beam

All runs used:

- pair pool: 768
- beam width: 768
- max composed pairs: 6
- max radius: 12
- objectives: `hw,cg,balance,target,score,repair`

| F | Candidate | Init | Best seen | Best non-seed band | Result |
|---|---|---:|---:|---|---|
| F717 | bit24_mdc27e18c | 40 | 40 | HW43, score 72.270 | no tie/improvement |
| F718 | bit24_mdc27e18c alt | 40 | 40 | HW44, score 75.000 | no tie/improvement |
| F719 | bit26_m11f9d4c7 | 39 | 39 | HW41, score 80.923 | no tie/improvement |
| F720 | bit28_md1acca79 | 39 | 39 | HW41, score 77.514 | no tie/improvement |

Artifacts:

- `results/search_artifacts/20260502_F717_bit24_hw40_multiobj_pair_beam.json`
- `results/search_artifacts/20260502_F718_bit24_alt_hw40_multiobj_pair_beam.json`
- `results/search_artifacts/20260502_F719_bit26_hw39_multiobj_pair_beam.json`
- `results/search_artifacts/20260502_F720_bit28_hw39_multiobj_pair_beam.json`

Interpretation: diversified beam retention did change the explored states,
but it did not reopen the current floor witnesses. The useful positive signal
is shape separation: for bit26 the beam found HW41 states with lower c/g
pressure than the seed, but the total-HW cost stayed too high. That suggests
the issue is not simply "we pruned the right c/g-repair path too early."

## F721/F724 additive W radius-2

All four additive probes used max_terms=2 over W57..W60.

| F | Candidate | Init | Candidates | Bridge pass | HW<=init | Best non-seed |
|---|---|---:|---:|---:|---:|---:|
| F721 | bit24_mdc27e18c | 40 | 32,896 | 31,265 | 0 | HW54 |
| F722 | bit24_mdc27e18c alt | 40 | 32,896 | 31,266 | 0 | HW51 |
| F723 | bit26_m11f9d4c7 | 39 | 32,896 | 31,266 | 0 | HW44 |
| F724 | bit28_md1acca79 | 39 | 32,896 | 31,266 | 0 | HW50 |

Artifacts:

- `results/search_artifacts/20260502_F721_bit24_hw40_additive_w_radius2.json`
- `results/search_artifacts/20260502_F722_bit24_alt_hw40_additive_w_radius2.json`
- `results/search_artifacts/20260502_F723_bit26_hw39_additive_w_radius2.json`
- `results/search_artifacts/20260502_F724_bit28_hw39_additive_w_radius2.json`

Interpretation: late-W modular add/sub moves are not a promising local
operator at radius 2 around these floor witnesses. They can make sparse XOR
word changes, but the residual HW jumps sharply.

## Verdict

No new Path C floor. Active tail remains:

- HW39: bit2, bit12, bit26, bit28
- HW40: bit24

This pivot still usefully prunes two novel ideas:

1. Multi-objective retention alone is not enough to unlock the current floor
   basins.
2. Additive local movement helps absorber sparsity in message space, but does
   not transfer directly to late W57..W60 residual polishing.

Next genuinely different work should move farther from local W-neighborhoods:
state-aware construction/backward constraints, absorber-seeded block-2 tests,
or a schedule-space operator that changes early message words while scoring
against the late carry chart.
