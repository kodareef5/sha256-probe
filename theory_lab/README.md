# SHA-256 Theory Lab

A standalone **idea-prospecting workspace** for the SHA-256 collision-resistance question.
Its job is to find a *new theoretical foothold* — a reframing of the number space and SHA-256
mechanics that opens a fresh angle — by mining the cryptanalysis community and adjacent math
fields and **classifying** the results into a living register.

It is a **study + ideation** companion to the working repo at `../sha256_review/`. It does **not**
grind SAT solvers and it does **not** touch that repo.

## What this is

- A **living, classified register** of attack angles (`30_register/ideas.yaml`), each tagged on 9
  axes and gated by a falsifiable kill-criterion.
- A **read-only digest** of the working repo's current theory + prior art (`00_repo_digest/`), so
  novelty is judged honestly and dead angles aren't re-proposed.
- A **community + adjacent-field scan** (`10_community_scan/`, `20_adjacent_fields/`).
- **Designed probes** for the most promising footholds (`40_deep_dives/`) — designs, not runs.

## What this is NOT

- Not a participant in `../sha256_review/` (see `CHARTER.md` — read-only toward the repo).
- Not a SAT-grinding effort. No solver runs live here.
- Not a one-shot scan. The prior one-shot (`../sha256_review/april28_explore/`) went stale; this
  one accumulates (`50_meta/CHANGELOG.md` is the heartbeat).

## How to add an idea (the 30-second version)

1. Add a row to `30_register/ideas.yaml` (copy the schema in `30_register/SCHEMA.md`).
2. You **must** write its `kill_criterion` ("this angle is dead if ___") or it can't leave `captured`.
3. Run `python3 30_register/infra/validate_ideas.py` then `python3 30_register/infra/rebuild_views.py`.
4. Commit. The CHANGELOG and views update; `INDEX.md` shows it in the whole-lab table.

## Layout

```
00_repo_digest/     read-only snapshot of ../sha256_review + april28 prior art
10_community_scan/  what the cryptanalysis community is doing (2026 frontier)
20_adjacent_fields/ catalog of adjacent-math lenses + stubs
30_register/        THE classified idea register (ideas.yaml = source of truth) + generated views
40_deep_dives/      per-angle dives with designed probes
50_meta/            methodology, lifecycle, scoring, changelog
graveyard/          archived ideas with resurrection triggers
```

Start with `INDEX.md` (90-second whole-lab scan) and `50_meta/shortlist.md` (the live footholds).
