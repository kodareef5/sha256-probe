---
date: 2026-04-30
machine: macbook
status: hourly log (append-only)
---

# 2026-04-30 macbook hourly log

## ~03:30 EDT — close yale F378-F384 acknowledgement loop

Triaged the unanswered yale message
`comms/inbox/20260429_yale_to_macbook_F378_F384_bridge_clause_target.md`
(yale's W57[22:23] bridge-clause target, the seed of macbook's F339-F367
propagator chain). My F343 preflight tool, F347/F348 speedup measurements,
and F366 budget-dependence findings all trace back to that yale discovery
and had not been formally acknowledged. Wrote
`comms/inbox/20260430_macbook_to_yale_F367_chain_thanks_F378_enabled.md`
with: explicit thanks, the F347 → F366 budget-dependence correction
(13.7% single-seed → -8.4% multi-seed at 60s budget), F353 verification
caveat (F349 SAT not reproducible at 4h), F358 polarity-bug retraction
note, and the standing -0.79% number on the F235 basic-cascade CNF.

Concurrent corpus audit: re-ran `audit_cnf.py --json` across all 78 CNFs
in `cnfs_n32/`. All CONFIRMED, observed bounds match the 2026-04-28
fingerprint envelope exactly (no drift). cascade_aux/cnfs/ counts also
unchanged (60/28/32/32 expose-sr60/force-sr60/expose-sr61/force-sr61).
`validate_registry.py`: 0 errors, 0 warnings.

## ~03:55 EDT — F368 multi-seed replication of F348

Ran 5 cands × 2 conditions × 2 new seeds (1, 2) at 60s cadical budget,
4-way parallel (~5 min wall). Combined with F348's seed=0 to get full
3-seed picture. All 20 runs logged via `append_run.py`. Result:

  3-seed grand mean: **−7.44%** (was F348 single-seed: −8.78%)
  σ_across_cands: 4.13% (3.86% excluding bit11)
  per-cand range: −11.13% (bit10) to **+1.63%** worse on bit11

Key finding: **bit11 fill=00000000 and bit13 fill=55555555 (both have
bit-31 of fill CLEAR) show mean ≈ −3% σ ≈ 4-6, while the 3 cands with
fill=80000000 (bit-31 SET) show mean ≈ −10% σ ≈ 1-3**. This is F340's
polarity flip biting back: the 2-clause injection is built from the
bit-31-SET polarity by default, so it targets the WRONG forbidden pair
on bit11/bit13. Per-fill-polarity-aware mining should recover the −10%
envelope on those cands.

bit11 seed 2 actively HURT (+4.81% more conflicts). F368 falsifies a
strong reading of "F343 always helps" — the mechanism is statistical,
not deterministic. Implication for cube-and-conquer: still a net win.
Implication for single deep solve: variance dominates the mean.

Shipped:
  - `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F368_F348_multiseed_replication.{md,json}`
  - 20 entries in `headline_hunt/registry/runs.jsonl`
  - The standing F343-injection number is now **−7.4% at 60s, σ ≈ 4%
    with fill-polarity caveat**, not the F348 −8.78%.

Dashboard refreshed: global audit-failure rate ticked to **0.58%** (10/1716).
This is **NOT** an audit drift — the 10 failures are the injected CNFs
(`/tmp/F348_*_injected.cnf`) which are raw clause-prepended files with no
header / no fingerprint match. They were logged with `--allow-audit-failure`
intentionally. sr61_n32 itself remains 0/83 (kill-criterion threshold is
on sr61_n32, not the global). Below the >1% global flag threshold; safe.

Also: in the future these injected CNFs should either get a synthetic
fingerprint bucket or have header-comment lines preserved by the
mining/injection pipeline so they audit cleanly. Filed as a follow-up
note for the propagator bet.

## ~04:50 EDT — F369: F368 ENCODER-MISMATCH CONFOUND, polarity claim retracted

While prepping the F369 polarity-aware re-mining test, I noticed F348's
injected CNFs (in /tmp) have **13220 vars** while F368's "baselines"
(`cascade_aux/cnfs/aux_force_sr60_n32_bit*.cnf`) have only **12592 vars**.
That's an old vs new cascade_aux_encoder version mismatch — 628-var /
2136-clause structural difference. F368's Δ% was partly measuring that
upgrade, not pure clause injection.

Inspected F348's per-cand prepended unit clauses: bit0/bit10/bit13 use
`-12373/-12317/-12369` (dW57[0]=0), bit11/bit17 use `+12369/+12338`
(dW57[0]=1) — flipped per cand. F348 was already polarity-correct.
**F368's polarity-flip hypothesis is FALSIFIED.** Retracted.

Ran F369 properly: regenerated 5 fresh aux_force sr=60 CNFs with current
encoder (matches F348 injected size), ran cadical 60s × 3 seeds × 5 cands
= 15 baseline runs. Combined with F348+F368's existing injected runs
(those used the new-encoder injected files, so they're valid):

  3-seed grand mean: **−9.10%**
  σ_across_cands: **2.68%**  (vs F368's confounded 4.13%)
  per-cand range: −5.89% (bit13) to −12.03% (bit10)

bit11 seed 2 went from F368's "+4.81% (HURT)" to F369's "−8.26% (HELPS)".
The "harm" was entirely encoder-mismatch artifact.

F347 → F348 → F368 → F369 chain converged: clean **−9.10% σ=2.68%** at
60s budget, validating F348's −8.78% single-seed number retroactively.

Shipped:
  - `F369_consistent_encoder_replication.{md,json}`
  - 15 fresh-baseline runs in `runs.jsonl`
  - F368 memo got a RETRACTION header pointing to F369

Lesson: when baseline and treatment files come from different
script/encoder versions, always cross-check `wc -l` and the `p cnf` line
BEFORE reporting Δ. F368 shipped with this confound undetected; caught
1 hour later. Five retraction lessons in a row from this project, and
the 6th now.

**Dashboard audit-failure rate now 1.44% (25/1731) — flagged as ">1%"**
but the sr61_n32 kill criterion is NOT tripped: sr61_n32 itself has
0/83 audit failures. The 25 flagged entries are all in
`programmatic_sat_propagator`:
  - 10 × `/tmp/F348_*_injected.cnf` (raw clause-prepended, no header
    matches a fingerprint pattern; logged with --allow-audit-failure
    intentionally)
  - 15 × `/tmp/F369_*_force.cnf` (filename doesn't match `aux_force_sr60_*`
    pattern; same intentional --allow-audit-failure flag)
Per CLAUDE.md the kill criterion is per-bet; sr61_n32's audits stay
clean. The dashboard ">1% global" flag is a useful warning but does NOT
require shutdown. Filed as: in the next propagator-bet iteration, either
move /tmp work to `programmatic_sat_propagator/cnfs/F369_*` with proper
naming OR add a `transient` fingerprint bucket so /tmp scratch CNFs
audit cleanly without --allow-audit-failure.

## ~05:05 EDT — IPASIR_UP_API.md envelope updated to F369 numbers

Appended a "2026-04-30 update (F366-F369)" section to the design doc
(`headline_hunt/bets/programmatic_sat_propagator/propagators/IPASIR_UP_API.md`).
Closes the loop F361 (F347-F360 envelope) → F366 (budget dep) →
F368 (confounded) → F369 (clean) by making F369's −9.10% σ=2.68% the
standing envelope for aux_force sr=60 force-mode at 60s budget.

Includes:
  - Full corrected table (F347-F369 chain) with per-probe numbers
  - Per-cand F369 detail (no outliers; bit11 normalized at −7.56%)
  - Two-distinct-effects framing: encoder-mode-dependence × budget-dependence
  - Phase 2D viability matrix per use case (cube-and-conquer vs deep solve)
  - Polarity-awareness as STRUCTURAL design requirement (F343 mining
    must run per-cand at solver init, not hardcoded once)
  - Sixth retraction lesson with concrete protocol
    (`wc -l` + `p cnf` + encoder-version cross-check before measuring Δ)
  - Standing reopen criterion: "≈ −9% conflict reduction at 60s budget,
    σ=2.68%" — neither hyperbolic nor sandbagged.

## ~05:25 EDT — heartbeat refreshes (2 bets, real progress notes)

**programmatic_sat_propagator/BET.yaml**:
  - Removed duplicate `last_heartbeat` field (had stale 2026-04-28T23:15
    AND newer 2026-04-29T15:05 — YAML parser was keeping the second,
    but the dup was a smell).
  - Refreshed to 2026-04-30T05:23Z.
  - Added `recent_progress_2026-04-30_F343_F369_chain` block: full
    F339-F369 chronology (~50 lines), standing F343-injection envelope,
    Phase 2D viability matrix. The BET.yaml `current_progress` field
    remains the older Phase-2 ENGINEERING-COMPLETE narrative; the new
    block captures the empirical chain that didn't fit anywhere else.

**sr61_n32/BET.yaml**:
  - Heartbeat was 4 days stale (2026-04-26, interval=3).
  - Refreshed to 2026-04-30T05:23Z.
  - Added `recent_progress_2026-04-30_F358_F360_cross_bet` block:
    documents that the only sr61_n32 activity since 2026-04-26 was the
    F358 baseline cadical run on F235 (single TIMEOUT, logged), and the
    cross-bet F360 finding that CNF-only F343 injection on basic_cascade
    gives ~−0.79% (near-noise). HONEST: bet has no structural progress
    in 4 days; the work that benefits sr61_n32 is happening in adjacent
    bets, no kill criterion tripped, owner=fleet stays in_flight.

`validate_registry.py`: 0 errors, 0 warnings post-edit.

## ~05:40 EDT — diff_cnf.py: infra fix for F368-class confounds

Wrote `headline_hunt/infra/diff_cnf.py` (~140 LOC). Compares two CNF
files for structural compatibility BEFORE you measure any Δ% across
them. Flags hard-fail confounds (n_vars mismatch >1%, malformed DIMACS,
encoder header DIFFERS) and soft notes (header missing on one side
when n_vars match — common for clause-injected files).

Validated against the actual F368 vs F369 cases:
  - **F368 confound** (old 12592-var baseline vs new 13220-var injected):
    `VERDICT: INCOMPATIBLE`, exit 1, with explicit
    `n_vars MISMATCH: 12592 vs 13220 (Δ=+628, 4.99% > 1.0% threshold)
    — LIKELY ENCODER-VERSION CONFOUND` finding. Would have caught F368
    in 100ms had it existed 1 hour ago.
  - **F369 clean case** (matched 13220-var baseline vs same-encoder
    injected): `VERDICT: compatible`, exit 0, with soft info note about
    the injected file's missing header.
  - **Self-compare**: `compatible (no findings)`, exit 0.

Exit codes: 0 = safe to measure Δ, 1 = confound likely. Use as a
preflight check before any baseline-vs-treatment cadical/kissat run.

Sixth retraction lesson now closed with a tool, not just a memo. The
2026-04-30 IPASIR_UP_API.md update referenced this exact discipline:
"`wc -l` + `p cnf` + encoder-version cross-check before any Δ" —
diff_cnf.py automates exactly that triple-check.

Filed in `headline_hunt/infra/` next to audit_cnf.py and append_run.py;
no integration with audit_cnf.py yet (separate single-file tool keeps
audit clean). Future iteration could add an `--also-diff <baseline>`
flag to audit_cnf.py if usage warrants.

## ~05:55 EDT — negatives.yaml: seed_farming_unchanged_sr61 REOPENED (FIRED trigger)

Reviewed `headline_hunt/registry/negatives.yaml` for any
`would_change_my_mind` triggers that have been empirically fired but
not yet reflected in the registry. Found one:

  **seed_farming_unchanged_sr61** (closed 2026-04-20):
    Trigger: "A new encoding (cascade-aux, XOR preprocessing)
    demonstrably changes solver conflict count or restart pattern."
    Status: **FIRED 2026-04-30** by the F347-F369 chain.

The F343 preflight clause-injection produces a measurable −9.10% σ=2.68%
conflict-count reduction on aux_force sr=60 force-mode at 60s budget
(F369 5 cands × 3 seeds). That's well outside the seed-variance noise
floor (σ ≈ 2-3% per F366) and directly satisfies the would_change_my_mind
condition.

Update: `seed_farming_unchanged_sr61` status → `reopened`, evidence_level
downgraded `VERIFIED → EVIDENCE`, added `reopened_date: 2026-04-30`,
`why_reopened` block referencing F347/F348/F366/F369, FIRED tag inline
on the trigger, and `refined_scope_after_reopen` clarifying the original
"more SEEDS yield no information" claim still stands at deep budgets
(5min+, F366 saturation) but is FALSIFIED at short budgets (60s) when
the encoding is mutated via F343 injection.

Implication: cube-and-conquer pipelines (many short cubes per cand)
gain ~9% × N cumulative speedup. Single-deep-solve pipelines remain
effectively unchanged.

Followed the precedent set by `bdd_marginals_uniform` (reopened
2026-04-26 with refined_scope). Same pattern: original closed claim
was scope-limited; new evidence falsifies a sub-scope without
overturning the whole.

`validate_registry.py` post-edit: 0 errors, 0 warnings (after fixing
mechanism-ID typo `programmatic_sat_propagator` →
`programmatic_sat_cascade_propagator`).

## ~06:15 EDT — literature note + 2 citation corrections (block2_wang relevance)

Two `read_status: todo` entries in `literature.yaml` had unverified
citations referring to "Li, Isobe, Meier, Zhang" (a team that **does
not exist** for the SHA-2 records 2024 paper). Resolved via WebSearch:

  **ePrint 2024/349** = "New Records in Collision Attacks on SHA-2"
    Authors: **Yingxin Li, Fukang Liu, Gaoli Wang** (NOT Li-Isobe-Meier-Zhang)
    EUROCRYPT 2024, Springer LNCS 14651
    Result: first practical SFS 39-step SHA-256 collision (beating
    Mendel-Nad-Schläffer's 38-step SFS from EUROCRYPT 2013)
    Technique: MILP-based differential characteristic search + SAT/SMT
    back-end. Authors explicitly state previous trail-search tools
    (de Cannière-Rechberger automated DC + Mendel-Nad-Schläffer
    extensions) had hit a bottleneck — longer trails not findable by
    heuristic improvement alone.

  **ASIACRYPT 2024 best paper** = "The First Practical Collision for
  31-Step SHA-256"
    Authors: **Yingxin Li, Fukang Liu, Gaoli Wang, Xiaoyang Dong, Siwei Sun**
    Springer LNCS 15494
    Result: first practical FULL (not SFS) 31-step SHA-256 collision,
    1.2h × 64 threads, negligible memory. Improvement on Li-Liu-Wang
    EUROCRYPT 2024 via memory-efficient search.

Wrote a substantive STRUCTURAL_SUMMARY-class note for the EUROCRYPT
paper at `headline_hunt/literature/notes/li_liu_wang_eurocrypt_2024_sha2_records.md`
(~150 LOC) covering: position in the SHA-2 cryptanalysis ladder
(24/27/31/38/39 step records over time), connections to **block2_wang**
(direct methodology reference for the bet's stated dependency
"Implement a bitcondition/trail-search engine"), connections to
programmatic_sat_propagator (MILP front-end + SAT back-end is the
working 2024 pattern; F343 preflight injection is much smaller hint),
project-context framing (Li-Liu-Wang's "trail search has stalled"
empirical claim is the **structural motivation** for the project's
non-trail cascade-1 algebraic absorber direction at sr=60+).

Updated literature.yaml:
  - `li_isobe_meier_zhang_sha2_records` → renamed to
    `li_liu_wang_eurocrypt_2024_sha2_records`. Citation, venue, URL,
    ePrint ID, key_takeaway, action_items, notes_path all corrected.
    confidence: needs_verification → high. read_status: todo → read.
  - `li_asiacrypt_2024_sha256_diff` → renamed to
    `li_liu_wang_dong_sun_asiacrypt_2024_31step_practical`. Same
    treatment: citation, venue, URL, key_takeaway, action_items
    corrected. confidence: needs_verification → high. read_status:
    todo → read.

`validate_registry.py`: 0 errors, 0 warnings after the rename batch
(initially 4 errors from using non-enum values `verified` / `STRUCTURAL_SUMMARY`,
fixed to schema-allowed `high` / `read`).

Methodology takeaway worth quote-citing in any future writeup:

> "The current advanced tool to search for SHA-2 characteristics had
> reached a bottleneck, with longer differential characteristics not
> being found." (Li-Liu-Wang EUROCRYPT 2024 abstract.)

This is the *structural* motivation for the project's cascade-1
algebraic absorber direction at sr=60+ — published trail-search work
explicitly stalls before reaching those rounds, so the project's
direction isn't "doing trail search where the experts can't reach";
it's a fundamentally different attack class operating in a regime
where trail search is documented to be inadequate.

## ~06:30 EDT — finishing the literature triage: Zhang 2026/232 + Alamgir IDs verified

Resolved the 2 remaining `confidence: needs_verification`-class entries
from the previous hour's literature work:

  **ePrint 2026/232** — verified via WebSearch:
    Zhuolong Zhang, Muzhou Li, Lei Gao, Meiqin Wang
    "Collision Attacks on SHA-256 up to 37 Steps with Improved Trail Search"
    Result: extends practical SHA-256 collision frontier from 31 steps
    (Li-Liu-Wang-Dong-Sun ASIACRYPT 2024) to **37 steps** via automated
    discovery of high-quality local collisions in the message expansion.
    The bottleneck previously was that local collisions had to be
    constructed by hand; this paper automates that step.

    Renamed registry ID: `zhang_2026_sha256_round_reduced` →
    `zhang_li_gao_wang_2026_sha256_37step_trail_search`. read_status:
    search_pending → read. Filled key_takeaway, action_items.

  **arXiv:2406.20072** — verified via WebSearch:
    Nahiyan Alamgir, Saeed Nejati, Curtis Bright
    "SHA-256 Collision Attack with Programmatic SAT"
    Submitted 28 June 2024, University of Waterloo.

    Updated `alamgir_nejati_bright_sat_cas_sha256` entry:
    citation set to verified author+title; venue set to "arXiv (28 June 2024)";
    URL set to https://arxiv.org/abs/2406.20072; arxiv_or_eprint =
    arXiv:2406.20072; confidence: needs_verification → high. The previous
    "ePrint 2024/2017 OR arXiv:2406.20072 — verify" ambiguity is resolved.

  **Updated the Li-Liu-Wang note's SHA-2 ladder table** to include the
    new 37-step practical record (Zhang-Li-Gao-Wang 2026). Standing ladder:

      24-step (2008) full → 27-step SFS (2008) → 31-step theoretical
      (Mendel 2013) → 38-step SFS (Mendel 2013) → 39-step SFS
      (Li-Liu-Wang 2024 EUROCRYPT) → 31-step practical
      (Li-Liu-Wang-Dong-Sun 2024 ASIACRYPT best paper) →
      **37-step practical (Zhang-Li-Gao-Wang 2026, NEWEST)** →
      59-step cascade-1 (Viragh 2026, structural-class)

Gap between published trail-search depth (37 steps) and the project's
structural-attack depth (60-step verified, 61-step open) is now
**60 - 37 = 23 steps**. The two methodologies are operating in
entirely different regimes.

`validate_registry.py`: 0 errors, 0 warnings post-edit.
literature.yaml: 17 entries total, all needs_verification entries from
the SHA-2-records cluster now resolved.
