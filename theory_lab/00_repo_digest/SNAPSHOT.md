# Repo Digest — Snapshot Header

**This digest reflects:**

| field | value |
|---|---|
| Working repo | `../sha256_review/` |
| Main repo git HEAD | `969ed495abf47d48ed73964a997301378a181121` |
| Branch | `master` |
| HEAD commit dated | 2026-05-26 |
| Digest written | 2026-06-03 |
| Scope | READ-ONLY snapshot for novelty baselining |

## What the working repo is

`../sha256_review/` is a systematic, multi-machine exploration of SHA-256
collision-resistance *limits* — not an attempt to prove a single thesis, but a
campaign to push the schedule-compliance frontier of Viragh (2026) and to
characterize the barriers that stop it. Viragh (2026, `../sha256_review/reference/paper.pdf`)
demonstrated semi-free-start collisions through **sr=59** of SHA-256's 64 rounds
(where `sr` counts how many of the 48 message-schedule expansion equations hold;
sr=59 ≈ 92% "compliant"). This project **independently reproduced sr=59** (custom
CSA-tree SAT encoder, 220.5 s) and then **pushed to sr=60**, producing a verified
**N=32 (full-width) sr=60 semi-free-start collision certificate** (MSB kernel,
M[0]=0x17149975, all-ones padding; Kissat SAT in ~12 h, cross-verified on three
machines by native SHA-256 computation). **sr=61 is the open frontier.** The
campaign's own analysis now concludes single-block sr=61 is *effectively
unreachable*: each additional enforced schedule round costs a factor `2^-2N`
(two independent N-bit conditions — value match `g1=0` AND difference
compatibility `h=0`), i.e. `2^-64` at N=32. ~1800 audited CPU-hours of fleet
search have produced **zero** true-sr=61 SAT. The active work has accordingly
pivoted (post-2026-04-24 "second wind") into a bet registry under
`../sha256_review/headline_hunt/`, with the highest-EV bet being a Wang-style
**multi-block** absorption attack that tries to bypass the single-block cascade
boundary altogether.

The repo is still SAT/CDCL-and-empirical-structure heavy. Its theoretical
content is a set of ~12 interlocking framings (see `established_framings.md`),
several of which are VERIFIED and several of which hit explicit walls. This digest
captures that theory so the lab can judge novelty honestly and never re-propose a
dead angle.

## Maintenance note

**Re-pull these digests when the repo HEAD advances past `969ed495`.** Novelty
tiers are relative to the repo's *current* state: an angle that is "genuinely new"
against this snapshot can become "repo-established" the moment a repo bet ships a
result. In particular, watch `block2_wang` (in flight, paused on a direction
decision), `singular_chamber_rank` (in flight), and `math_principles_calibration`
(in flight) — those three are the live fronts most likely to move the baseline.

## Files in this digest

| file | contents |
|---|---|
| `SNAPSHOT.md` | this header |
| `established_framings.md` | the ~12 interlocking theoretical framings (the core reference) |
| `claims_tiering.md` | CLAIMS.md mirrored by evidence tier |
| `open_bets_digest.md` | active repo bets = the DO-NOT-DUPLICATE list |
| `graveyard_digest.md` | killed angles + their reopen triggers |
| `prior_scan_digest.md` | the april28_explore 36-item one-shot scan + the live unprobed wedges |

All repo citations are relative paths of the form `../sha256_review/...`.
