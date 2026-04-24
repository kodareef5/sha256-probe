# SECOND WIND — repository restructured (2026-04-24)

To: all
From: macbook
Re: project pivot from paper-polishing to headline-hunt

## What changed

The project has pivoted away from "polish a paper on the existing sr=60 result"
and back to **probing for a headline-worthy finding**, after a meta-consultation
with GPT-5.5 (high reasoning, ~570K-token brief, $7.52). The full reasoning is
in `consultations/20260424_secondwind/20260424_1505_gpt55.md` — read it.

User mandate: *"headline-worthy finding or nothing. Until then, we are
investing high-quality tokens in exploring the problem space, probing for
patterns, weakness, new ideas."*

## New top-level: `headline_hunt/`

Active workspace. q1-q6 are now **frozen historical record** — don't extend them.

```
headline_hunt/
  TARGETS.md            <- read this first
  registry/             <- candidates, kernels, mechanisms, negatives, literature, runs.jsonl
  bets/                 <- one folder per active bet, each with BET.yaml + kill_criteria
  datasets/             <- canonical artifacts (sr=60 cert, CNFs, BDDs, proofs)
  infra/                <- audit_cnf.py, append_run.py, validate_registry.py, summarize_runs.py, new_bet.py
  literature/           <- BibTeX + per-paper notes
  graveyard/            <- closed-bet kill memos (so we don't reanimate)
  reports/              <- weekly dashboards
```

## The 7 bets (priority order per GPT-5.5)

1. **block2_wang** — Wang-style block-2 modification from cascade residuals (highest EV)
2. **cascade_aux_encoding** — local-offset auxiliary CNF encoding (cheap, enables others)
3. **kc_xor_d4** — d4 with XOR-preserving preprocessing on standard CNFs
4. **sr61_n32** — TRUE sr=61 at full N=32 (BUDGET-CAPPED at 10k CPU-h)
5. **mitm_residue** — MITM on the 24-bit hard residue (BLOCKED on operationalization)
6. **chunk_mode_dp** — chunk-mode DP with mode variables
7. **programmatic_sat_propagator** — IPASIR-UP custom propagator (newly surfaced by GPT-5.5)

All 7 are `unassigned`. Pick one.

## To pick up a bet (any machine)

1. `git pull`
2. Read `CLAUDE.md` (updated with Registry Discipline section)
3. Read `headline_hunt/TARGETS.md`
4. Read `headline_hunt/bets/<your_pick>/README.md` and `kill_criteria.md`
5. Read `headline_hunt/bets/<your_pick>/BET.yaml`
6. Edit `headline_hunt/registry/mechanisms.yaml` to set
   `<mechanism_id>.owner: <your-machine>`
7. Edit `headline_hunt/bets/<your_pick>/BET.yaml` similarly
8. Run `python3 headline_hunt/infra/validate_registry.py` — must pass before you start
9. Commit + push that ownership claim BEFORE starting compute

## Registry discipline (NON-NEGOTIABLE — process kill if violated)

This is the lesson from the 2026-04-18 CNF audit (~2000 CPU-h wasted on
mislabeled CNFs). Going forward:

- **Every CNF**: `python3 headline_hunt/infra/audit_cnf.py <file>` BEFORE queuing.
  Trust the audit verdict, NOT the filename. Refuses if CRITICAL_MISMATCH.
- **Every solver run**: `python3 headline_hunt/infra/append_run.py ...` to log it.
  Auto-captures git commit, machine, CNF sha256, audit verdict. NO EXCEPTIONS,
  including exploratory runs.
- **Heartbeat**: every 7 days update your bet's `last_heartbeat`. (sr61_n32 is 3
  days — drift-prone bet.)
- **Validate before starting**: `python3 headline_hunt/infra/validate_registry.py`
  must return exit 0.
- **Audit-failure dashboard auto-trips kill criteria**: if `summarize_runs.py`
  shows >1% audit failure rate, sr61_n32 closes pending pipeline fix.

## What didn't change

- `lib/` is unchanged. Still the source of truth for SHA-256 / CNF encoder / solver wrappers.
- `cnfs_n32/` is unchanged. The 42 sr=61 CNFs there remain canonical — they
  were the post-audit good batch. `bets/sr61_n32/` references them by path.
- `writeups/` is unchanged. Read for background, don't extend.
- `comms/` (this folder) is the communication channel as before. No format change.
- `reference/paper.pdf` — Viragh 2026 — unchanged.
- All q1-q6 content unchanged. They're frozen, not deleted.

## What was relocated

- 28 prior inspiration responses moved from `q5_alternative_attacks/results/`
  to `consultations/archive/`. They were misfiled at q5; they're project-wide.

## What was extracted

- The sr=60 collision certificate (M[0]=0x17149975, fill=0xFFFFFFFF, hash
  ba6287f0...) is now structured YAML at
  `headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml`. Source remains
  `writeups/sr60_collision_anatomy.md`.

## Don't

- Don't restart the old fleet pattern of seed-farming on unchanged sr=61 CNFs.
  GPT-5.5 explicitly closed that — see `headline_hunt/registry/negatives.yaml#seed_farming_unchanged_sr61`.
- Don't reanimate a closed mechanism without meeting its `reopen_criteria`.
  All 11 closed doors are documented in `negatives.yaml` with explicit triggers.
- Don't add new content to q1-q6, writeups/, etc. They're frozen historical record.
- Don't skip `audit_cnf.py`. Even if you trust the filename. Especially if you
  trust the filename.

## Questions / coordination

Drop a message in this folder. The macbook is the maintainer of `headline_hunt/`
infra; ping if you find a script bug or want to add a fingerprint to
`infra/cnf_fingerprints.yaml`.

— macbook, 2026-04-24
