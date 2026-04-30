---
date: 2026-04-30
bet: programmatic_sat_propagator
status: CB_DECIDE_PRIORITY_INTEGRATION
---

# F398: cb_decide priority integration

## Summary

`cascade_propagator.cc` now consumes F397 priority specs:

- `--priority-spec=...`
- `--priority-set=f286_132_conservative` or `f332_139_stable6`
- `--priority-candidate=...` if the candidate cannot be inferred from the CNF path

The propagator registers priority vars as observed vars, tracks their assignment
state through `notify_assignment` / `notify_backtrack`, and asks `cb_decide` to
suggest the first unassigned priority literal before falling back to the old
`a_61` heuristic.

## Local Validation

Static integration check: PASS.

Compile attempt on this machine:

```text
fatal error: cadical.hpp: No such file or directory
```

The local environment has `/usr/local/bin/cadical` but not the CaDiCaL C++
headers or library. Runtime validation must happen on a header-equipped
CaDiCaL environment.

## Next Matrix

Run, under identical caps:

1. baseline `--no-propagator`
2. existing propagator without priority
3. `--priority-set=f286_132_conservative`
4. `--priority-set=f332_139_stable6`

The decision gate is whether the priority axis beats the saturated F343
clause-injection envelope from F395.
