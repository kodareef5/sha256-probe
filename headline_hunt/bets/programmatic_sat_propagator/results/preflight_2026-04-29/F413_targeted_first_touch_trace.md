---
date: 2026-04-30
bet: programmatic_sat_propagator
status: TARGETED_FIRST_TOUCH_TRACE
parents: F393, F402, F411, F412
---

# F413: targeted first-touch trace

## Summary

Conflict cap: 50000.
Trace vars per candidate: 11.

| Candidate | Return | Wall | Decisions | Backtracks | Trace seen | First dW57_b0 | First low-bit shell key |
|---|---:|---:|---:|---:|---:|---|---|
| `bit2_ma896ee41_fillffffffff` | 2 | 4.058 | 342976 | 57973 | 11/11 | dW57_b0@d0 | w2_57_b1@d10245 |
| `bit24_mdc27e18c_fillffffffff` | 2 | 3.653 | 377616 | 58550 | 11/11 | dW57_b0@d0 | w2_57_b1@d26282 |
| `bit28_md1acca79_fillffffffff` | 2 | 3.368 | 351017 | 57758 | 11/11 | dW57_b0@d0 | w2_57_b1@d35254 |

## First-Touch Events

### bit2_ma896ee41_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12401 | 1 | 481 | 0 | 0 |
| `dW57_b23` | 12424 | 1 | 676 | 512 | 0 |
| `dW57_b22` | 12423 | 1 | 677 | 513 | 0 |
| `w1_57_b0` | 2 | 1 | 3358 | 8679 | 346 |
| `w2_57_b0` | 130 | 0 | 3359 | 8679 | 346 |
| `w2_57_b1` | 131 | 0 | 4980 | 10245 | 420 |
| `w1_57_b22` | 24 | 1 | 14489 | 28566 | 1288 |
| `w1_57_b23` | 25 | 1 | 14490 | 28567 | 1288 |
| `w2_57_b22` | 152 | 1 | 14527 | 28686 | 1288 |
| `w2_57_b23` | 153 | 0 | 14533 | 28687 | 1289 |
| `w2_58_b1` | 163 | 1 | 14543 | 28698 | 1291 |

### bit24_mdc27e18c_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12364 | 1 | 481 | 0 | 0 |
| `dW57_b23` | 12387 | 1 | 676 | 510 | 0 |
| `dW57_b22` | 12386 | 1 | 677 | 511 | 0 |
| `w1_57_b0` | 2 | 0 | 11374 | 24567 | 758 |
| `w2_57_b0` | 130 | 1 | 11375 | 24567 | 758 |
| `w2_57_b1` | 131 | 1 | 12683 | 26282 | 838 |
| `w1_57_b22` | 24 | 1 | 20910 | 33243 | 1321 |
| `w1_57_b23` | 25 | 1 | 20911 | 33244 | 1321 |
| `w2_57_b22` | 152 | 0 | 20944 | 33354 | 1321 |
| `w2_57_b23` | 153 | 0 | 20946 | 33354 | 1321 |
| `w2_58_b1` | 163 | 1 | 20948 | 33367 | 1321 |

### bit28_md1acca79_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12352 | 0 | 481 | 0 | 0 |
| `dW57_b23` | 12375 | 1 | 676 | 512 | 0 |
| `dW57_b22` | 12374 | 1 | 677 | 513 | 0 |
| `w1_57_b0` | 2 | 1 | 18000 | 35253 | 1335 |
| `w2_57_b0` | 130 | 1 | 18001 | 35253 | 1335 |
| `w2_57_b1` | 131 | 1 | 18003 | 35254 | 1335 |
| `w1_57_b22` | 24 | 1 | 18010 | 35275 | 1335 |
| `w1_57_b23` | 25 | 1 | 18011 | 35276 | 1335 |
| `w2_57_b22` | 152 | 1 | 18036 | 35394 | 1335 |
| `w2_57_b23` | 153 | 0 | 18037 | 35394 | 1335 |
| `w2_58_b1` | 163 | 1 | 18040 | 35406 | 1335 |

## Initial Read

This trace records first assignment only. It is a trajectory probe, not a proof of causality.

The useful negative result: bit2 is not failing because CDCL never touches the F343 aux row. `dW57_b0`, `dW57_b22`, and `dW57_b23` are first assigned very early on all three candidates. Bit2 sees them at the same stage as bit24/bit28.

The low-bit shell keys also do not explain the outlier by delayed discovery. Bit2 touches `w2_57_b1` earlier than the helper candidates, not later.

## Verdict

The next mechanism test should not be another generic priority nudge. It should run the same trace with F343 clauses actually injected, and record whether the F343 clause becomes conflict-producing or merely propagating on bit2. F413 shifts the question from "does the solver reach the F343 vars?" to "what happens after it reaches them?"
