# headline_hunt — SHA-256 Probe, Second Wind

This top-level is the active workspace for the project after the 2026-04-20
pause and the 2026-04-24 GPT-5.5 meta-consultation
(`consultations/20260424_secondwind/`).

## What this is

The project pivoted away from "polish a paper on the sr=60 result" and back
to **probing for a headline-worthy finding**. Every active mechanism lives
under `bets/` with a kill criterion. Every artifact is registered. Every
compute run goes through `infra/` audit + logging.

If you can't say what would close your bet, you don't have a bet.

## Where things live

| Path | What |
|---|---|
| `TARGETS.md` | The 3 headline classes we're hunting + clean-stop criteria |
| `registry/candidates.yaml` | All candidate (M[0], fill, kernel) tuples and statuses |
| `registry/kernels.yaml` | Kernel families and sweep coverage |
| `registry/mechanisms.yaml` | Active and proposed attack mechanisms with kill criteria |
| `registry/negatives.yaml` | Closed doors with reopen triggers |
| `registry/literature.yaml` | Papers to read (with confidence flags) |
| `registry/runs.jsonl` | Append-only compute event log |
| `bets/<name>/` | One folder per active hunt, with BET.yaml + kill_criteria |
| `datasets/` | Canonical artifacts: certificates, BDDs, collision lists, proofs |
| `infra/` | Scripts that enforce registry discipline |
| `literature/` | BibTeX + per-paper notes |
| `graveyard/` | Final kill memos for closed bets — prevents reanimation |
| `reports/` | Decision memos + weekly dashboards |

## Where the OLD project lives

`q1_barrier_location/` through `q6_verification/` at the repo root are
**frozen historical record**. Don't extend them. If a bet needs old code,
copy it into the bet's folder with provenance.

`writeups/` contains the cryptanalytic narrative as it stood at pause.
Treat as background reading, not as a place to add new content.

`cnfs_n32/` (at repo root) contains the existing TRUE sr=61 CNFs. The
`bets/sr61_n32/` bet points at them.

## Onboarding (other machines)

1. `git pull`
2. Read `CLAUDE.md`
3. Read `headline_hunt/TARGETS.md`
4. Read `headline_hunt/registry/mechanisms.yaml`
5. Pick a bet whose `owner` is `unassigned`. Set yourself as the owner via PR/commit.
6. Run `python3 headline_hunt/infra/validate_registry.py` — must pass before you start.
7. For every solver/build run: `python3 headline_hunt/infra/append_run.py ...` — no exceptions.

## Why the discipline

April 2026: ~2000 CPU-hours wasted because 38 fleet "sr=61" CNFs were
actually mislabeled sr=60. The audit caught it on day 18.

`infra/audit_cnf.py` exists so this never happens again. Trust the audit
output, not the filename.
