# Charter — guardrails for the Theory Lab

These are non-negotiable. They exist so this lab stays useful and never disturbs the working fleet.

## 1. READ-ONLY toward `../sha256_review/`

The lab **snapshots and cites** the working repo by relative path. It never edits, stages, or
commits anything there. Isolation is verifiable: `git -C ../sha256_review status` must show no
changes caused by this lab, and this lab has its **own** git history (`git log` here is independent).

## 2. Ideation, not grinding

No SAT solver runs live in this lab. The only computation ever contemplated is **cheap, small-N
probes** (reusing `../sha256_review/lib/`) that *falsify or validate a reframing* — and even those
are designed here first (`40_deep_dives/`) and only run on explicit go-ahead. Anything that would
need the solver fleet is marked `probe_cost: heavy` and handed back to the repo as a recommendation.

## 3. Living, not one-shot

The prior one-shot scan (`../sha256_review/april28_explore/`) produced real results but went stale
and sprawled to ~100 terminal files. This lab fixes that:

- `30_register/ideas.yaml` is the single source of truth; `INDEX.md` and `30_register/views/` are
  **generated** from it, never hand-edited.
- Every state change appends a dated line to `50_meta/CHANGELOG.md`. The CHANGELOG growing *is* the
  proof of life.
- Novelty tiers are re-checked against the repo's current HEAD over time (an idea tagged
  `genuinely-new` today can become `repo-established` when a repo bet ships).

## 4. Falsifiability is the entry fee

No idea leaves the `captured` state without a concrete `kill_criterion`. If you can't say what would
kill it, it stays a stub in `20_adjacent_fields/`, not a row in the register. This is the working
repo's *"if you can't say what would close your bet, you don't have a bet"* rule, ported.

## 5. Promotion is a recommendation, never a commit

The only lab state that touches the repo is `promoted` — and only by producing a **ready-to-paste
bet block** for a human to consider adding to `../sha256_review/headline_hunt/registry/mechanisms.yaml`.
The lab never writes there itself.

## 6. No paid external-model spend without a green light

Frontier-model consultations (the repo's Inspiration Engine) cost money and are **off by default**.
Web research + self-synthesis only, unless the user explicitly authorizes a consult.
