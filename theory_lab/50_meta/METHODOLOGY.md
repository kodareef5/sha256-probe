# Methodology — how this lab works (and how it fixes april28)

The lab is the **living, literature-grounded, disciplined** successor to the one-shot
`../sha256_review/april28_explore/` scan. Its own `META_LESSONS.md` diagnosed why that scan
underdelivered; each lesson is fixed here by construction.

| april28 failure (its own words) | fix here |
|---|---|
| one-shot → went stale | living register + `CHANGELOG.md` heartbeat; novelty re-checked vs repo HEAD |
| minutes-per-item, too shallow | hours-per-item *only on promoted angles*; the `40_deep_dives/` gate enforces depth |
| cross-pollination came late | a standing cross-pollination pass (below) |
| literature connections thin | the community scan (`10_community_scan/`) is built **first**, not after |
| speculation without anchor | every row needs `repo_refs` + a falsifiable `kill_criterion` or it can't leave `captured` |

## Sourcing ideas
`source` tags where a row came from: `community-paper` (from `10_community_scan/`), `adjacent-analogy`
(a field mapped onto SHA mechanics), `external-model:<name>` (a frontier-model suggestion),
`generated` / `human`. New rows arrive by (a) sweeping new papers, (b) prospecting an adjacent field
into a `20_adjacent_fields/fields/` stub, then promoting it once a kill-criterion exists.

## Triage
Every row passes `DUPLICATE_POLICY.md` (sets `novelty`) and `SCORING_RUBRIC.md` (sets `plausibility`,
`probe_cost`). The hard gate is the **kill_criterion** — no falsifier, no register row (`LIFECYCLE.md`).

## Cross-pollination (the april28 lesson, operationalized)
Individual single-lens framings tend to be trivial or already in the literature; the genuine novelty
lives in **combining lenses on a shared locus**. Concretely, the current spine is one cross-pollination:
`carries` viewed simultaneously through `number-theory-padic` (the metric), `lattice` (the solver), and
`coding-theory` (the sparsity bound). When adding rows, ask: *which existing row shares my `locus`, and
what does combining our lenses buy?* Record promising combinations as new rows, not just notes.

## Probing
Only `trivial`/`cheap` probes run in-lab, on small N, reusing `../sha256_review/lib/` (never
reimplement primitives — `CHARTER.md` §2). `heavy` probes are designed and handed to the repo. Probe
results are written into the dive's verdict in the april28 `[VERDICT: …]` style and appended to the
row's `notes`.

## Promotion
A surviving angle yields a one-page promotion memo: a ready-to-paste `mechanisms.yaml` bet block
(hypothesis, kill_criteria, reopen_criteria) for a human to add to the repo. The lab recommends; it
never commits to the repo (`CHARTER.md` §1, §5).

## Cadence
Periodically: refresh `00_repo_digest/SNAPSHOT.md` against the repo HEAD; sweep new literature; re-score
rows whose novelty may have drifted; archive rows that have gone stale with a resurrection trigger.
