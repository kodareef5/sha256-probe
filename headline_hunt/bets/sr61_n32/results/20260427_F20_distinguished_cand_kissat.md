# F20: TRUE sr=61 kissat on F12+F17 distinguished cands — all UNKNOWN
**2026-04-26 21:55 EDT**

Per yale's strategic read (commit f2edeed, "test guarded message repair"),
the next concrete moves were:
1. **TRUE sr=61 SAT/Kissat on distinguished candidates** ← this memo
2. Guard-preserving message-space operator (yale's track)
3. Block2/Wang absorption using the relaxed sr=60 cert

This memo executes #1.

## The 6 distinguished cands

Candidates flagged by F12 (cascade-1 chamber min HW) + F17 (block2 round-63
residual min HW) as structurally interesting:

| cand | F12 chamber min HW | F17 residual min HW @100M | F18 @10B |
|---|---:|---:|---:|
| msb_m17149975 (verified sr=60) | 8 | 53 | 44 |
| msb_m189b13c7 | 2 | 51 | 49 |
| bit13_m4e560940 | 3 | 47 | 47 |
| bit17_m427c281d | 3 | 54 | — |
| bit18_m99bf552b | 4 | 54 | — |
| idx8_m33ec77ca | 5 | — | 46 |

## Multi-budget kissat sweep

Each cand × seed=7 × 3 budgets (100k, 1M, 10M conflicts). 10M phase
ran 6 in parallel on M5 cores; hit 300s wall cap before reaching 10M.

| cand | 100k wall | 1M wall | 10M wall (300s cap) | status |
|---|---:|---:|---:|---|
| msb_m17149975 | 2.18 s | 21.30 s | 300.01 s | UNKNOWN |
| msb_m189b13c7 | 2.10 s | 19.58 s | 300.01 s | UNKNOWN |
| bit13_m4e560940 | 3.87 s | 19.34 s | 300.01 s | UNKNOWN |
| bit17_m427c281d | 3.56 s | 18.86 s | 300.01 s | UNKNOWN |
| bit18_m99bf552b | 2.34 s | 21.67 s | 300.01 s | UNKNOWN |
| idx8_m33ec77ca | 2.25 s | 22.42 s | 300.01 s | UNKNOWN |

**0/18 runs returned SAT or UNSAT.** All hit conflict or time limit.

## Interpretation

Per yale's f2edeed finding: "once we add the real message-space guard
a57_xor == 0, the attractive low-defect valleys mostly disappear."
Kissat at TRUE sr=61 (full schedule + cascade-1 + cascade-2) is searching
the GUARDED message space directly. The fact that no SAT emerges at 1M
or even ~3M conflicts (300s wall × cores) is empirical evidence for
yale's structural finding: the guarded valleys aren't in the productive
chart.

The F12+F17 structural distinction (low residual HW in relaxed model)
**does not appear to translate** to faster TRUE sr=61 SAT discovery.
Each distinguished cand performs similarly to non-distinguished cands
in the cascade_aux Mode A registry runs.

## Cross-bet implication

The cascade_aux Mode A speedup work (F4b 1.87× n=18, F19 bit13 1.62×)
is in the schedule-relaxed model. Translating that speedup to TRUE
sr=61 search is non-trivial: the cascade_aux hints encode info about
the relaxed chamber image which doesn't constrain the actual schedule
search directly.

The structural-distinction-to-search-speedup gap is a known issue.

## What this rules in/out

- **Rules out**: "structurally distinguished cands solve TRUE sr=61
  noticeably faster at low budgets." 1M conflicts is already past the
  cascade_aux preprocessing-phase decay (F8); we'd expect any structural
  advantage to have manifested.
- **Doesn't rule out**: "distinguished cands solve TRUE sr=61 at HIGH
  budgets faster." Would need 100M-1B conflicts or longer. Big compute.
- **Reinforces**: yale's "next operator must move within useful guarded
  fiber" framing (f2edeed). Random kissat search at distinguished cands
  is not enough.

## Discipline ledger

18 runs logged via append_run.py. Full TRUE sr=61 cascade_enf0 encoder.
All audit CONFIRMED. Dashboard refreshed (commit pending).

## Next moves (post-F20)

If pursuing #1 from yale's list further: 100M+ conflict budget on the
top 1-2 cands (msb_m17149975 + bit13_m4e560940). Big compute (~20-60
min per run). Requires user authorization per session rules.

Yale's #2 (guard-preserving operator) and #3 (Wang absorption) remain
open and may be higher EV per compute hour.

EVIDENCE-level: VERIFIED at the budgets tested. SAT may exist at higher
budgets but is not within reach of practical compute on this fleet.
