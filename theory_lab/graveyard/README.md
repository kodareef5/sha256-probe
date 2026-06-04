# Graveyard — archived ideas

When a register row reaches `archived` (killed or parked), it gets a memo here:
`archived_<idea_id>.md` with:

- **What it was** — the one-liner.
- **Which kill-criterion fired** (or "parked, not killed" with the reason).
- **What we learned** — the residue worth keeping.
- **Resurrection trigger** — the specific observation that would re-open it (the
  `would_change_my_mind` discipline, ported from the repo's `negatives.yaml`).

The `ideas.yaml` row **stays** (status `archived`) so an archived angle is never silently
re-proposed — it shows up in views with its kill reason attached.

## Pass-1 note
The four **parked** rows seeded on 2026-06-03 (`algebraic-geometry-variety`,
`additive-combinatorics-sumset`, `tropical-carry-maxchain`, `quantum-grover-residual`) carry their
one-line dead-for-construction reasons inline in `ideas.yaml`; they were catalogued-dead, never live,
so they have no standalone memo yet. The two **repo-killed** carry/tensor rows point to the repo's own
probed verdicts. Standalone memos get written the first time a *live* row is archived after a probe.
