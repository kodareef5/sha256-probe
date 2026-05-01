---
date: 2026-04-30
machine: macbook-codex
status: active
---

# macbook-codex status

Started from `.codex_session/brief_2026-04-30.md`, then read `CLAUDE.md`,
`CLAIMS.md`, `headline_hunt/TARGETS.md`, registry state, and current inbox
context. Registry validates clean at session start.

Rules of engagement acknowledged:

- Commit as configured `kodareef5`; push is authorized.
- No force-push to master without explicit approval.
- Every solver run must be CNF-audited first and logged through
  `headline_hunt/infra/append_run.py`.
- Claim long-running bet work in `headline_hunt/registry/mechanisms.yaml`
  before launching it.
- Do not reopen closed bets unless reopen criteria are met.
- Do not touch `/tmp/F350` or `/tmp/deep_dig`.
- Do not reimplement `lib/` primitives.
- F-numbered memos for substantive findings, with explicit evidence level.

Ordering decision:

1. Cleanup first: low-risk coordination hygiene before the fleet pulls.
2. Path C next: bounded, no solver, highest EV/CPU-hour among immediately
   executable interventions, and aligned with `block2_wang` priority.
3. Path A after Path C: directly targets the bit2 outlier and F397 priority
   mechanism, but has longer C++/runtime risk and needs registry claiming.
4. Path B last: the F381-F395 chain already mined the learned-clause lead and
   falsified ladder pre-injection as a speedup; remaining value is secondary.

Capacity: using this local Codex session on the Mac workspace. `getconf`
reports 10 online processors; I will keep initial work bounded and avoid
unclaimed long solver jobs.

## 2026-04-30 ~21:10 EDT

Cleanup commit pushed as `b728caf`.

Path C in progress/completed first pass:

- Added annealing/restarts/tabu/candidate controls to `block2_bridge_beam.py`.
- Ran 4-cand annealing sweep, 458s wall, no solver search.
- New residual records: bit3 HW=51, bit2 HW=51, bit24 HW=49, bit28 HW=45.
- Built audited cert-pin CNFs for all 4; audit verdicts `CONFIRMED`.
- Logged 8 cert-pin solver runs; kissat + cadical both UNSAT for all 4.

Next: commit F408 memo/artifacts, then reassess whether to continue Path C
around bit28 or switch to the bit2-specific Path A follow-up left by F407.
