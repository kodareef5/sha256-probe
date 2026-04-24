# SHA-256 Probe — Agent Operating Guide

## What This Project Is

A systematic exploration of SHA-256 collision resistance limits. We probe
for weaknesses, characterize barriers, and build tools to push further.

This is **not** about proving a single thesis. It is about generating
reliable evidence across multiple angles of attack on SHA-256.

**Background:** Viragh (2026) demonstrated collisions through round 59 of
SHA-256's 64 rounds ("92% broken"). This project investigates whether the
remaining rounds can be attacked. See `reference/paper.pdf`.

## Before You Start

1. **Check `comms/inbox/`** — read messages addressed to you or `all`
2. **Update `comms/status/<your-machine>.md`** — what you're running, capacity
3. Read `CLAIMS.md` — understand what's established vs hypothesized
4. **Read `headline_hunt/TARGETS.md`** — the active hunt direction (post-2026-04-24)
5. **Read `headline_hunt/registry/mechanisms.yaml`** — pick a bet whose owner is `unassigned`
6. **Always import from `lib/`** — never reimplement SHA-256 primitives

The old `q*_` folders' QUESTION.md files are **historical**. The active workspace is
`headline_hunt/`.

## Multi-Machine Coordination

This project runs on multiple machines simultaneously. We coordinate via
git-based messaging in `comms/`. See `comms/README.md`.

**On every `git pull`:** Check `comms/inbox/` for messages addressed to you.
**After significant events:** Update your status board and send messages.
**Before starting new work:** Check what others are doing to avoid duplication.

## Repository Structure

```
headline_hunt/         **ACTIVE WORKSPACE** — post-2026-04-24 second wind
  TARGETS.md           Headline classes we're hunting
  registry/            Living lists: candidates, kernels, mechanisms, negatives, literature, runs
  bets/                One folder per active bet (each with kill criteria)
  datasets/            Canonical artifacts: certificates, BDDs, collision lists, proofs
  infra/               Audit, validation, run-logging, dashboard scripts
  literature/          BibTeX + per-paper notes
  graveyard/           Closed-bet kill memos (prevents reanimation)
  reports/             Decision memos + weekly dashboards
consultations/         External-model consultations (current + archive of prior reviews)
lib/                   Shared library (SHA-256, CNF encoder, solvers)
q1_barrier_location/   FROZEN — historical record (don't extend)
q2_bottleneck_anatomy/ FROZEN
q3_candidate_families/ FROZEN
q4_mitm_geometry/      FROZEN — but tools here feed bets/mitm_residue/
q5_alternative_attacks/ FROZEN — most active pre-pause; tools may feed multiple bets
q6_verification/       FROZEN
reference/             Source paper, prior art, specs (paper.pdf is Viragh 2026)
writeups/              Pre-pause research narratives — read for background, don't extend
cnfs_n32/              Existing TRUE sr=61 CNFs (used by bets/sr61_n32/)
comms/                 Multi-machine coordination (inbox/ for messages)
infra/                 (legacy) Build, batch, orchestration
archive/               Legacy numbered scripts (read-only)
```

## Shared Library (`lib/`)

```python
from lib.sha256 import K, IV, precompute_state, sigma0_py, sigma1_py
from lib.cnf_encoder import CNFBuilder
from lib.mini_sha import MiniSHA256, MiniCNFBuilder
from lib.solver import run_kissat, run_cadical, verify_drat
```

**Never reimplement these.** If you need a variant, extend the library.

## Conventions

### File naming
- No numbered prefixes (multiple agents = name collisions)
- Descriptive names: `padding_freedom_scanner.c` not `77_candidate_mutation.py`
- Results: `results/YYYYMMDD_description/` within each question folder

### Evidence levels
Use these consistently in claims, writeups, and commit messages:
- **VERIFIED**: reproduced, cross-validated, DRAT-checked where applicable
- **EVIDENCE**: consistent from multiple approaches, but gaps remain
- **HYPOTHESIS**: supported by data, not yet tested against alternatives
- **EXTRAPOLATION**: projected from trends, explicitly flagged as uncertain

### Claims
Each testable claim gets its own file in `q*/claims/` with:
- One-sentence statement
- Evidence level
- Supporting scripts/results
- Known caveats
- What would change the assessment

### Commit messages
- State what changed and the evidence level of any new claims
- Reference the bet (post-2nd-wind): `[block2_wang] residual corpus collected, N=...`
- Legacy q*-folder references still acceptable for historical reference: `[q1] ...`

## Running Experiments — Registry Discipline (post-2nd-wind, NON-NEGOTIABLE)

The 2026-04-18 CNF audit cost ~2000 CPU-hours because mislabeled CNFs went
unaudited. These rules exist so that doesn't happen again.

1. **Audit before queuing**: every CNF passes `python3 headline_hunt/infra/audit_cnf.py <file>`.
   Trust the audit verdict, NOT the filename. If it returns CRITICAL_MISMATCH
   or UNKNOWN, do not run.
2. **Log every run**: every solver invocation is recorded via
   `python3 headline_hunt/infra/append_run.py --bet <id> --candidate <id> ...`.
   No exceptions, including exploratory runs. The script auto-captures
   git commit, CNF sha256, machine, audit verdict.
3. **Claim a bet** by editing `headline_hunt/registry/mechanisms.yaml` to set
   `<mechanism>.owner` to your machine name. Update the bet's `BET.yaml` too.
4. **Validate before starting**: `python3 headline_hunt/infra/validate_registry.py`
   should return zero errors. If it warns about staleness on a bet you're about
   to touch, that's a signal to refresh the bet's `last_updated` /
   `last_heartbeat` field in the same commit.
5. **Weekly dashboard**: run `python3 headline_hunt/infra/summarize_runs.py`,
   commit `headline_hunt/reports/dashboard.md`. Watch the audit-failure-rate
   row — if it exceeds 1%, the sr61_n32 bet auto-trips its process kill criterion.
6. **Kill-criteria are real**: when a bet's kill criteria fire, move it to
   `headline_hunt/graveyard/closed_bets/` and write a kill memo using the
   template. Do NOT silently restart a closed bet — meet the reopen criteria first.

## What NOT To Do

- Don't say "proof" without DRAT verification and cross-solver confirmation
- Don't extrapolate mini-SHA results to full SHA-256 without explicit caveats
- Don't add scripts that reimplement `lib/` functions
- Don't modify `lib/` without checking downstream consumers
- Don't frame findings as "properties of SHA-256" when they're properties
  of one candidate family under one kernel with one padding scheme
- Don't use "theorem" for experimental observations

## Macbook-Local Tools (not in repo)

- **Inspiration Engine** (`~/.claude/inspiration/ask_models.py`): Sends research
  briefing to frontier models via OpenRouter for external critique and creative
  ideas. Currently configured for GPT-5.5 at high reasoning (prior pair: Gemini
  3.1 Pro + GPT-5.4, kept commented in MODELS dict). Auto-loads ~400-570K
  tokens of context. DO NOT run without explicit user direction. Useful for
  fresh perspectives, second set of eyes, or when stuck. Budget: ~$2.50-7.50/run
  for GPT-5.5 at high reasoning (reasoning tokens bill as output — actual cost
  ~2× the naive estimate). API key stored locally only. Outputs land in
  `consultations/<date>_<purpose>/` per run.

## Tools Available

- **Kissat 4.0.4** — primary CDCL SAT solver
- **CaDiCaL** — secondary solver for cross-validation
- **CryptoMiniSat 5** — third solver (slow on these instances)
- **drat-trim** — DRAT proof checker (in `infra/drat-trim/`)
- **gcc + OpenMP** — for C tools. Compile flags:
  `gcc -O3 -march=native -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp`

## Current State (post-2026-04-24 second wind)

The pre-pause state (sr=60 SAT verified, sr=61 open, 11 closed mechanisms,
6-theorem boundary proof, BDD O(N^4.8)) is all preserved in `writeups/`.

For **active** state, see:
- `headline_hunt/TARGETS.md` — what we're hunting
- `headline_hunt/registry/candidates.yaml` — all candidates with statuses (replaces
  the inline table that used to live here)
- `headline_hunt/registry/mechanisms.yaml` — what's open/in_flight/blocked/closed
  with kill criteria and reopen triggers
- `headline_hunt/registry/negatives.yaml` — closed doors with would-change-my-mind triggers
- `headline_hunt/reports/dashboard.md` — generated weekly from runs.jsonl
- `consultations/20260424_secondwind/` — GPT-5.5's full meta-consultation that drove this restructure

The principal sr=60 collision certificate is at:
`headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml`
(extracted from `writeups/sr60_collision_anatomy.md`; re-verifiable from the YAML).
