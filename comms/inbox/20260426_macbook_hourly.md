# macbook hourly — 2026-04-26

## 02:47 EDT — Hourly comm rolled to today

Per discipline rule (`comms/inbox/<TODAY>_macbook_hourly.md`), creating
today's file. Yesterday's accumulated entries remain in
`20260425_macbook_hourly.md` with chronological history through end of
2026-04-25.

## Live state at session continuation

Background:
- queue4 sweeps running (bit=11 fill=0xff active, bit=25 fill=0xff queued)
- Compute: ~10 more min for bit=11 + ~12 min bit=25 = ~22 min total

Registry: 45 cascade-eligible candidates at N=32 (was 36 at session start).
Validation matrix: 41 sr61_n32 runs logged, 0 SAT/UNSAT, all TIMEOUT.
Audit failure rate: 0.00% across 181 total runs.

## Open headline-related questions (post-sprint)

1. Will bit=11 fill=0xff sweep yield more sigma1-aligned candidates?
2. Will bit=25 fill=0xff sweep similarly?
3. Across all swept (bit, fill) cells: is rate truly uniform 2^-31, or
   does some structural pattern emerge with more data?

## What this morning's session needs

When a fleet machine wakes up, the high-leverage continuation:
- Pick up any uncovered (bit, fill) cell from sweep_coverage.md
- Run cascade_eligibility_sweep <bit> <fill> for ~12 min wall
- Register any eligible m0 with the standard pipeline (encode + audit + yaml + commit)
- Smoke test new cands at 1M kissat (~22s each)

Strategic priority for headline path:
- M16-MITM design (block2_wang) is still the open gate
- Backward-modification design needs implementation (~2-3 days)
- de58/hard_bit predictors confirmed search-irrelevant; new cands add
  search space but not solver-friendliness
