# Lifecycle — how an idea moves

A 7-state machine. It mirrors the working repo's bet/kill/graveyard rigor but is lighter: the gate to
advance is **an argument**, not a passing solver run.

```
captured ──▶ triaged ──▶ deep-dive ──▶ probe-designed ──▶ probed ──┬─▶ promoted
   │            │                                                   └─▶ archived
   └────────────┴──────────────────────────────────────────────────────▶ archived
                              (archive from any state, with a reason + resurrection trigger)
```

1. **captured** — a row exists in `ideas.yaml` with at least `lens`, `locus`, `one_liner`, `source`.
   May be rough. Cost to enter: one line.
2. **triaged** — all 9 axes filled, INCLUDING a concrete `kill_criterion` and a `novelty` decided
   against `../00_repo_digest/`. **The hard gate:** if you cannot write the "dead if…" sentence, the
   idea cannot leave `captured` — it is demoted to a `../20_adjacent_fields/fields/` stub. This is the
   repo's *"no kill-criterion, no bet"* rule, ported.
3. **deep-dive** — earns a `../40_deep_dives/dive_<id>.md` (structure → first dismissal → bridges →
   adversarial check → translation → probe-design → verdict). Reserved for `plausibility ≥ 3` OR
   `novelty == genuinely-new`. Gate: a reviewer agrees the bridge is articulable.
4. **probe-designed** — the dive specifies the *smallest decisive experiment* and an **expected-outcome
   table** (what each result would mean), but it has NOT run. `probe_cost` is now firm.
5. **probed** — a `trivial`/`cheap` probe ran in-lab (small-N, reusing `../sha256_review/lib/`). Result
   appended to the dive's verdict and the row's `notes`. `heavy` probes are NOT run here — they exit
   straight to *promoted* as a repo recommendation.
6. **promoted** — survived its probe (or is a clean strong-negative worth importing). **The only state
   that touches the repo, and only as a recommendation:** produce a ready-to-paste `mechanisms.yaml`
   bet block (hypothesis + kill_criteria + reopen_criteria) for a human to consider adding to
   `../sha256_review/headline_hunt/`. The lab still does not commit there.
7. **archived** — parked or killed. Moves to `../graveyard/archived_<id>.md` with: what it was · which
   kill-criterion fired (or "parked, not killed") · what we learned · **resurrection trigger**. The
   `ideas.yaml` row stays (status `archived`) so it is never silently re-proposed.

## Heartbeat (what makes it living, not one-shot)
- Every state change appends a dated line to `CHANGELOG.md`. The CHANGELOG growing IS the proof of life.
- `INDEX.md` + `../30_register/views/` regenerate from `ideas.yaml` on each change.
- Standing cadence: periodically re-pull `../00_repo_digest/SNAPSHOT.md` against the repo's current
  HEAD (novelty tiers drift as repo bets resolve) and sweep new `../10_community_scan/` papers for
  fresh `captured` rows.
