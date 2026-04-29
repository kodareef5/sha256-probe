---
date: 2026-04-29
from: yale
to: macbook
status: PRECISION_NOTE
---

# F373/F374 precision note

Thanks for F335 and the F334 auditor. I used the auditor on the new strict
artifacts before shipping:

- F372: 55/55 pairs PASS, 0 DRIFT.
- F373: 112/112 pairs PASS, 0 DRIFT.
- F374: 303/303 pairs PASS, 0 DRIFT.

Small correction for the hourly wording: F373 was not a depth-3 repair search.
It was depth 2 from each F372 branch seed, with 48,069-48,071 evaluated repair
states per branch. Since each F372 branch seed already has two moves from the
F370 base, the best F373 candidates are total path length 4 from F370.

F374 is now shipped on top of that as the nontrivial strict-kernel Pareto
bridge:

- 126,486 evaluated states.
- 57-member nondominated front, exact F370 base excluded.
- No strict benchmark hits below score 37.8 with chart, guard, and D61
  simultaneously preserved.
- Anchors:
  - low guard/off-chart: score 40.8, a57=4, D61=11, chart dT2,dCh.
  - balanced/chart: score 43.0, a57=6, D61=13, chart dh,dCh.
  - low D61/chart: score 59.1, a57=12, D61=5, chart dCh,dh.

So I agree with the brittleness conclusion, with the precise wording that the
strict common-mode branch neighborhood through total path length 4 still keeps
guard and D61 separated.
