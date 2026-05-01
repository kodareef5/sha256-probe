---
date: 2026-04-30
bet: programmatic_sat_propagator
status: F343_PHASE_HINT_TRACE
parents: F411, F414, F415
---

# F416: F343 forbidden-pair phase hint trace

## Summary

Conflict cap: 50000. F343 clauses are appended as in F414. The runner also calls `solver.phase(lit)` for `dW57[0]` at its forced value and for `dW57[22:23]` at the forbidden pair polarity.

| Candidate | Audit | Return | Wall | Decisions | Δ vs F413 | Δ vs F414 append | Backtracks | Δ backtracks vs F414 | Trace seen | Phase hints |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `bit2_ma896ee41_fillffffffff` | CONFIRMED | 2 | 3.773 | 381782 | +38806 (+11.31%) | +6178 (+1.64%) | 58623 | +449 (+0.77%) | 11/11 | `dW57_b0_forced_phase:12401` `dW57_b22_forbidden_phase:-12423` `dW57_b23_forbidden_phase:-12424` |
| `bit24_mdc27e18c_fillffffffff` | CONFIRMED | 2 | 4.063 | 389532 | +11916 (+3.16%) | +5020 (+1.31%) | 58828 | +95 (+0.16%) | 11/11 | `dW57_b0_forced_phase:12364` `dW57_b22_forbidden_phase:-12386` `dW57_b23_forbidden_phase:12387` |
| `bit28_md1acca79_fillffffffff` | CONFIRMED | 2 | 3.306 | 364794 | +13777 (+3.92%) | +11534 (+3.27%) | 58199 | +149 (+0.26%) | 11/11 | `dW57_b0_forced_phase:-12352` `dW57_b22_forbidden_phase:-12374` `dW57_b23_forbidden_phase:-12375` |

## First-Touch Events

### bit2_ma896ee41_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12401 | 1 | 481 | 0 | 0 |
| `dW57_b23` | 12424 | 0 | 676 | 512 | 0 |
| `dW57_b22` | 12423 | 1 | 677 | 512 | 0 |
| `w1_57_b0` | 2 | 1 | 3358 | 8677 | 346 |
| `w2_57_b0` | 130 | 0 | 3359 | 8677 | 346 |
| `w2_57_b1` | 131 | 0 | 4980 | 10243 | 420 |
| `w1_57_b22` | 24 | 1 | 14489 | 28557 | 1288 |
| `w1_57_b23` | 25 | 1 | 14490 | 28558 | 1288 |
| `w2_57_b22` | 152 | 1 | 14527 | 28677 | 1288 |
| `w2_57_b23` | 153 | 0 | 14531 | 28677 | 1288 |
| `w2_58_b1` | 163 | 1 | 14535 | 28687 | 1288 |

### bit24_mdc27e18c_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12364 | 1 | 481 | 0 | 0 |
| `dW57_b23` | 12387 | 1 | 676 | 510 | 0 |
| `dW57_b22` | 12386 | 1 | 677 | 510 | 0 |
| `w1_57_b0` | 2 | 0 | 11374 | 24559 | 758 |
| `w2_57_b0` | 130 | 1 | 11375 | 24559 | 758 |
| `w2_57_b1` | 131 | 1 | 12683 | 26274 | 838 |
| `w1_57_b22` | 24 | 1 | 20910 | 33235 | 1321 |
| `w1_57_b23` | 25 | 1 | 20911 | 33236 | 1321 |
| `w2_57_b22` | 152 | 0 | 20944 | 33346 | 1321 |
| `w2_57_b23` | 153 | 0 | 20946 | 33346 | 1321 |
| `w2_58_b1` | 163 | 1 | 20948 | 33359 | 1321 |

### bit28_md1acca79_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12352 | 0 | 481 | 0 | 0 |
| `dW57_b23` | 12375 | 0 | 676 | 512 | 0 |
| `dW57_b22` | 12374 | 1 | 677 | 512 | 0 |
| `w1_57_b0` | 2 | 1 | 18000 | 35240 | 1335 |
| `w2_57_b0` | 130 | 1 | 18001 | 35240 | 1335 |
| `w2_57_b1` | 131 | 1 | 18003 | 35241 | 1335 |
| `w1_57_b22` | 24 | 1 | 18010 | 35262 | 1335 |
| `w1_57_b23` | 25 | 1 | 18011 | 35263 | 1335 |
| `w2_57_b22` | 152 | 1 | 18036 | 35381 | 1335 |
| `w2_57_b23` | 153 | 0 | 18037 | 35381 | 1335 |
| `w2_58_b1` | 163 | 1 | 18040 | 35393 | 1335 |

## Initial Read

This tests a lighter decision primitive than `cb_decide`: polarity bias without variable-selection takeover. If bit2 were mostly failing because selected F343 vars get the wrong saved/default phase, this should move the trajectory once those vars are selected.

The phase hints do affect the early aux values on bit2 and bit28 (`dW57_b23` follows the hinted forbidden polarity while `dW57_b22` satisfies the pair clause), but the search counters move the wrong way. Decisions increase versus F414 on all three candidates: +1.64% for bit2, +1.31% for bit24, and +3.27% for bit28. That is a useful negative: bit2 is not rescued by clause placement or polarity bias, and forbidden-pair phase bias is actively harmful in this trace.

## Verdict

The remaining decision-priority problem is not solved by phase. The next implementation path should either instrument conflict involvement directly or test an activity-bump/score primitive; `cb_decide` takeover and `phase()` polarity hints have both failed to rescue bit2.

## Compute Discipline

- 3 phase-hinted injected CNFs audited before solver launch; all audited CONFIRMED.
- 3 solver runs appended with `append_run.py`.
- Logs: `/tmp/F416/*.stderr.log` and `/tmp/F416/*.stdout.log`.
