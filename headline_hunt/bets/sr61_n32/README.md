# bet: sr61_n32 — TRUE sr=61 semi-free-start collision at full N=32

**Priority 4. BUDGET-CAPPED at 10k additional CPU-hours.**

## The bet

Among 29+ audited TRUE sr=61 candidates in `../../../cnfs_n32/`, at least one
has a SAT instance reachable in under 10k additional CPU-hours given encoding
or candidate diversity (NOT seed farming).

## The 1800-CPU-hour scar

- 2026-04-18: CNF audit revealed 38 fleet "sr=61" CNFs were mislabeled sr=60 → ~2000 CPU-h wasted.
- 2026-04-18 to 2026-04-20: 1800 CPU-h on TRUE sr=61, 36 seeds across 8 candidates, zero SAT.
- The pause was triggered partly by this — repeated seed runs on unchanged encodings produced no information.

**Implication**: more seeds on unchanged CNFs is closed (`negatives.yaml#seed_farming_unchanged_sr61`).
Every additional CPU-hour on this bet must change at least one of: encoding, candidate, kernel, predictor question.

## Headline if it works

> "TRUE sr=61 semi-free-start collision at full N=32 SHA-256 (94% of rounds)."

Direct extension of public boundary. Most legibly headline-worthy of all bets.

## Discipline (non-negotiable)

1. Every CNF passes `infra/audit_cnf.py` first. Trust the audit, not the filename.
2. Every run goes through `infra/append_run.py` — no exceptions.
3. Run metadata MUST include encoder commit hash, candidate_id, kernel_id, seed.
4. Seed-only re-runs of an unchanged encoding are forbidden. If you want to retry,
   first change one of: encoder, candidate, kernel.
5. Heartbeat every 3 days (faster than other bets — this one is most prone to drift).

## What's built / TODO

- [x] 29 TRUE sr=61 CNFs in `../../../cnfs_n32/sr61_n32_*.cnf`.
- [x] 8 sr61_cascade variant CNFs in `../../../cnfs_n32/sr61_cascade_*.cnf`.
- [ ] Encoder regeneration with `cascade_aux_encoding` once that bet ships.
- [ ] Predictor experiment: which 5 candidates are most promising? (Need a metric
      better than hw56.)
- [ ] Coordinated seed sweep WITH the new encoding, not without.

## How to join

1. Read `kill_criteria.md` first. Especially the "no measurable improvement" condition.
2. Pick a candidate from `../../registry/candidates.yaml` whose `cpu_hours` is low and
   whose owner is `fleet`.
3. Confirm CNF audit: `python3 ../../infra/audit_cnf.py ../../../cnfs_n32/<file>.cnf`
4. Launch solver (kissat / cadical / cms — already documented in CLAUDE.md tools section).
5. Log via `python3 ../../infra/append_run.py --bet sr61_n32 --candidate <id> --cnf ... --solver kissat --seed N --status TIMEOUT|SAT|UNSAT --wall <s>`.
6. Update candidate's `cpu_hours` in `candidates.yaml` to reflect cumulative spend.

## Related

- Gated by progress on `cascade_aux_encoding` (the only way to "change the encoding").
- Could close `seed_farming_unchanged_sr61` reopen path if encoding actually moves the needle.
- Adjacent in mechanism class to `programmatic_sat_propagator`.
