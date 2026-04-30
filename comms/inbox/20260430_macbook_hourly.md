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

## ~06:50 EDT — F370: 11 unreferenced cnfs_n32/ files attached to candidates

Routine registry hygiene found 11 CNF files in `cnfs_n32/` that were NOT
referenced by any candidate's `artifacts.cnfs` list. These are alternative
encoder variants (TRUE_sr61_*, sr61_cascade_*) of registered cands whose
artifacts only listed the primary `_enf0.cnf` variant.

Pattern of misses:
  - 4 × TRUE_sr61_bit{B}_{m0_prefix}.cnf  (bit10/10/17/19)
  - 7 × sr61_cascade_m{m0}_f{fill}_bit{B}.cnf

All 11 attached via filename → cand-key matching. 7 cands updated:
  - cand_n32_msb_m17149975_fillffffffff (verified-collision; +cascade variant)
  - cand_n32_bit06_m6781a62a_fillaaaaaaaa
  - cand_n32_bit06_m88fab888_fill55555555
  - cand_n32_bit10_m24451221_fill55555555 (+TRUE +cascade)
  - cand_n32_bit10_m3304caa0_fill80000000 (+TRUE +cascade)
  - cand_n32_bit17_m8c752c40_fill00000000 (+TRUE +cascade)
  - cand_n32_bit19_m51ca0b34_fill55555555 (+TRUE +cascade)

Caught one matching bug en route: my `m0_norm("0x00000000")` returned
empty string (lstrip strips '0' and 'x' chars from both directions) —
the fill `0x00000000` collapsed to `''`. Worked around with manual
attachment for the last file. Logged as a note for future similar tools.

Post-edit verification:
  - 78 CNFs in cnfs_n32/ → 78 referenced by some candidate (was 67)
  - validate_registry.py: 0 errors, 0 warnings
  - cnf_fingerprints.yaml audit (re-run): all 78 still CONFIRMED

Diff: ~190 lines because yaml.safe_dump re-flows the entire file with
PyYAML's default formatting (single quotes, different line-wrap width).
Content preserved verbatim — validate_registry confirms. The
re-formatting is a one-time normalization; future edits via the same
tool will produce minimal diffs against this baseline.

## ~07:15 EDT — math_principles bet was UNDOCUMENTED in the registry

While surveying bets for SPEC/kill_criteria coverage, found that
**`headline_hunt/bets/math_principles/`** had:
  - 50+ yale commits
  - 100+ result memos (F340-F384 chain)
  - README.md with full scope description
  - **NO BET.yaml**
  - **NO kill_criteria.md**
  - **NO mechanisms.yaml entry**
  - 0 entries in runs.jsonl

This is yale's bet — directory created 2026-04-29 by yale (commit
ef27a8e: "Implement math principles triage slice"). The F378-F384
chain that seeded macbook's F339-F369 propagator work is also in this
bet's results/ directory. The cross-machine flywheel was real but the
bet itself was invisible to discipline tooling.

Scaffolded the missing files with clear `[SCAFFOLDED 2026-04-30 by
macbook; yale to replace]` markers on every placeholder value:

  - `headline_hunt/bets/math_principles/BET.yaml`: owner=yale,
    in_flight, last_heartbeat=2026-04-29T16:55Z (yale's last commit
    timestamp), heartbeat_interval_days=7, audit_required=false (most
    math_principles tools consume existing artifacts), placeholder
    compute_budget=50 CPU-h, scope summary inferred from README.

  - `headline_hunt/bets/math_principles/kill_criteria.md`: three
    placeholder kill criteria (REM tail-law predictive R²<0.3,
    submodular vs random no-better-than, strict-kernel basin no novel
    SAT) + three reopen triggers. All clearly marked TBD.

  - `headline_hunt/registry/mechanisms.yaml`: added new entry
    `math_principles_calibration`. Required fields populated; placeholder
    kill_criteria/reopen_criteria duplicated from kill_criteria.md.

  - `comms/inbox/20260430_macbook_to_yale_math_principles_BET_scaffolded.md`:
    HEADS_UP message to yale with explicit checklist of placeholders to
    review/replace. Nothing destructive — purely additive scaffolding.

`validate_registry.py`: 0 errors, 0 warnings post-scaffolding. The bet
is now discoverable, the discipline gap is closed, and yale gets a
clear hand-off note. If yale prefers different placeholders or
completely different kill criteria, the markers make it obvious which
fields are macbook's guesses vs yale's content.

## ~07:30 EDT — block2_wang/residuals/extract_top_residuals.py: stub operationalized

The user-suggested move: "operationalize a stub from another bet (e.g.,
write a residual-extraction one-liner for block2_wang)". Surveyed
`bets/block2_wang/residuals/`:

  - 47 per-cand corpora exist in `by_candidate/corpus_*.jsonl`, each
    with full W-witness records (w1_{57..60}, w2_{57..60}, iv1_63,
    iv2_63, diff63, hw63, hw_total, active_regs, da_eq_de).
  - F100_registry_top10_sweep.json aggregates top-10 HWs per cand but
    OMITS the W-witness vectors that produced them.
  - Gap: no tool emits per-cand top-K residuals with full vectors as
    a JSON feed for downstream trail-search consumption.

Wrote `headline_hunt/bets/block2_wang/residuals/extract_top_residuals.py`
(~120 LOC). Walks `by_candidate/corpus_*.jsonl`, sorts by hw_total
(heap-based for memory efficiency on the larger corpora), emits
per-cand top-K records with full W-witness vectors. Supports:

  --cand <suffix>     filter to one cand (substring match)
  --top-k N           per-cand top-K (default 3)
  --hw-max H          filter records hw_total ≤ H (then top-K)
  --out PATH          write to file (default stdout)
  --corpus-dir DIR    override default by_candidate/ location

Smoke-tested:
  - --top-k 1 across all cands → 47 corpora processed in <1s
  - grand_min_hw_total = 55 (cand: bit3_m33ec77ca_fillffffffff)
  - 5 lowest-min cands: bit3 (55), bit19 (56), bit2 (57), bit13 (59), bit28 (59)
  - emits full W vectors + iv1_63/iv2_63/diff63/hw63 ready for
    `simulate_2block_absorption.py` / `build_2block_certpin.py` ingestion

Concrete trail-search lead from the smoke test: **cand
bit3_m33ec77ca_fillffffffff has a HW=55 W-witness already cataloged**
that hasn't been highlighted before. F100 reports this cand had
cert-pin coverage but only top-10 HWs (62-66 range), so the HW=55
record is BELOW the top-10 floor — it's in the corpus but was missed.
This is exactly the kind of artifact the F100 sweep was supposed to
surface but couldn't without W-witness data.

Tool is dependency-free (stdlib only) and reusable for cluster-analysis
follow-ups: feed `extract_top_residuals.py --hw-max 60 --top-k 1000`
into a clustering script to find structural patterns across the
sub-60 residuals.

## ~07:50 EDT — F371: F100 cert-pin sweep had a 13-cand BLIND SPOT

Used `extract_top_residuals.py` (just shipped) to cross-reference 47
per-cand corpora against F100's cert-pin coverage. Findings:

  **F100 covered 54 cands, NOT 67 as documented.** The 13 missing
  cands HAD per-cand corpora at F100 time, but F100 didn't ingest them.
  4 of those 13 cands have W-witnesses BELOW F100's covered min_hw=61
  floor:
    bit3_m33ec77ca_fillffffffff:  HW=55  (lowest in entire dataset)
    bit2_ma896ee41_fillffffffff:  HW=57
    bit28_md1acca79_fillffffffff: HW=59
    bit13_m4e560940_fillaaaaaaaa: HW=61

  These 4 sub-floor W-witnesses have **NOT been cert-pin verified**.
  If single-block sr=60 cascade-1 collisions are reachable at our
  compute scale, they're most likely to materialize at the lowest-HW
  W-witnesses — and 4 such cands were left untested.

The bit3_m33ec77ca HW=55 record is the strongest single lead in the
project's residual corpus:
  w1_57=0x3d7df981  w1_58=0xae13c3a4  w1_59=0x49c834bd  w1_60=0x7619ac16
  w2_57=0x36ed80fa  w2_58=0x8a9db1fa  w2_59=0x5c63c09d  w2_60=0x0a66d006
  hw63=[11,7,8,0,12,8,9,0]   active_regs={a,b,c,e,f,g}   da_eq_de=false

Shipped:
  - `bets/block2_wang/results/20260430_F371_F100_blindspot_13_cands_HW55_lead.md`
  - Updated `negatives.yaml#single_block_cascade1_sat_at_compute_scale`
    with F371 caveat in why_closed (54-cand actual vs 67-cand stated)
    + new would_change_my_mind trigger naming the 4 sub-floor cands
  - Soft-revision: doesn't *invalidate* the F100 conclusion (54 cands
    × ~11 W-witnesses × 3 solvers all UNSAT remains strong evidence),
    but updates the scope statement to match what F100 actually ran

`validate_registry.py` post-edit: 0 errors, 0 warnings.

Recommended next-hour move: cert-pin verify the 4 sub-floor W-witnesses
via `build_2block_certpin.py` + kissat/cadical/CMS at 60s budget.
~10 min compute. Highest-leverage block2_wang move available from
existing data — no new corpus building, no big compute, and the bit3
HW=55 is structurally the lowest known cascade-1 residual in the
project. **Deferring launch to next pulse for explicit go-ahead** since
this crosses the routine-vs-experimental boundary (4 cert-pin builds
+ 12 solver runs). Documented as proposed move (a) in F371 memo.

## ~08:10 EDT — F372: F371 blind spot CLOSED EMPIRICALLY (4/4 UNSAT)

Ran the F371 follow-up cert-pin verification with full discipline.

  Pipeline per cand: cascade_aux_encoder.py (sr=60, expose) → varmap →
    build_certpin.py → kissat 5s + cadical 5s. CNFs persisted to /tmp.

  4 cands × 2 solvers = 8 runs, all logged via append_run.py:
    bit3_m33ec77ca  HW=55  kissat UNSAT 0.01s   cadical UNSAT 0.01s
    bit2_ma896ee41  HW=57  kissat UNSAT 0.01s   cadical UNSAT 0.01s
    bit28_md1acca79 HW=59  kissat UNSAT 0.01s   cadical UNSAT 0.01s
    bit13_m4e560940 HW=61  kissat UNSAT 0.01s   cadical UNSAT 0.01s

  Total wall: ~30s for CNF building, ~0.1s for solver runs.

**All 8 UNSAT — F371's blind-spot lead does NOT contain a single-block
sr=60 collision.** Cert-pin instances are UP-derivable UNSAT in <0.01s,
consistent with F100's pattern. F100's conclusion stands.

**Cert-pin coverage now 58/67 cands directly verified (was 54/67):**
54 from F100 + 4 from F372 = 58. The remaining 9 blind-spot cands
have HW≥62 (within F100's covered HW range) and can be swept in a
future iteration to reach 67/67 if desired.

Shipped:
  - `bets/block2_wang/results/20260430_F372_subfloor_certpin_verification.{md,json}`
  - 8 entries in `runs.jsonl`
  - dashboard.md refreshed

The F371 + F372 pair is a clean closure: F371 surfaced the strongest
single lead the residual corpus had hiding (bit3 HW=55, below F100's
covered floor); F372 verified within minutes that it's a near-residual,
not a collision. Discipline-correct, mechanism-relevant, and
honestly negative.

## ~08:30 EDT — F373: extended F372 to all 9 remaining blind-spot cands → 67/67 = 100% direct coverage

Same pipeline as F372 applied to the remaining 9 blind-spot cands
(HW 61-69, including bit25_m09990bd2 = F235's cand). All 18 runs
(9 cands × 2 solvers) returned UNSAT in 0.01-0.03s.

Cumulative cert-pin coverage (after F373):
  F100 (2026-04-28): 54 cands, ~540 runs, all UNSAT
  F372 (2026-04-30): 4 sub-floor cands, 8 runs, all UNSAT
  F373 (2026-04-30): 9 remaining cands, 18 runs, all UNSAT
  ────────────────────────────────────────────────────────────
  Total direct: **67/67 cands (100%), ~566 runs, 0 SAT.**

negatives.yaml updated: `single_block_cascade1_sat_at_compute_scale`
why_closed now reflects 100% direct coverage (previously characterized
as 54-cand effective per F100 with F32 shared proxy for 13). F371's
would_change_my_mind trigger is **NOT_FIRED 13/13** at all blind-spot
cands; trigger now subsumed by 100% coverage.

Shipped:
  - `bets/block2_wang/results/20260430_F373_remaining_blindspot_certpin.{md,json}`
  - 18 entries in `runs.jsonl`
  - dashboard.md refreshed
  - negatives.yaml soft-revision (100% coverage finding)

Total session F371+F372+F373 chain: ~3 minutes wall, 26 cert-pin runs,
direct registry coverage went 54/67 → 67/67 in three commits. Headline
conclusion (no single-block sr=60 cascade-1 collisions at our compute
scale) now empirically grounded at strict registry-wide verification.

## ~08:50 EDT — F374: cluster analysis on 171 sub-65 cascade-1 residuals (4 strong signatures)

Pure data exploration on the existing 47 corpora — no compute.
Used `extract_top_residuals.py --hw-max 65` to dump 171 records
across 17 cands.

**4 strong structural signatures found:**

1. **Active register set is 100% [a, b, c, e, f, g]** — universal
   cascade-1 hardlock at d=h=0 across the entire deep tail.

2. **`da_63 ≠ de_63` for 100% of sub-65 records.** The Theorem-4
   a_61=e_61 symmetry does NOT extend to round-63 residuals.
   Implication: trail-search heuristics that constrain da=de will
   SKIP all sub-65 W-witnesses. **Don't constrain da=de in any
   sub-65-targeted block2_wang search.**

3. **Per-register HW is non-uniformly distributed.** c and g are
   systematically ~3 HW LIGHTER than a/b/e/f:
     a/b/e/f mean HW ≈ 11.5 (heavier tail)
     c/g     mean HW ≈ 8.6  (lighter tail, 25% lower)
   This is a load-bearing structural asymmetry of cascade-1 round
   dynamics that the existing block2_wang search does not exploit.
   **Concrete heuristic recommendation: prioritize c and g residual
   cancellation in trail-search.**

4. **bit3 / bit2 / bit28 dominate the deep tail.** These 3 cands
   contribute 93/171 = 54% of sub-65 records. If single-block
   sr=60 cascade-1 collisions are reachable at our compute scale,
   bit3/bit2/bit28 are the most likely source. (F372 already
   cert-pin verified each at its lowest-HW W-witness → all UNSAT.)

Cross-bet implication for `programmatic_sat_cascade_propagator` Phase 2D:
the per-register HW asymmetry suggests an additional `cb_decide`
priority — branch on c/g state vars before a/b/e/f at rounds 62-63.
Adds to the F286-bit-prioritized hook without changing soundness.

Shipped:
  - `bets/block2_wang/results/20260430_F374_sub65_residual_cluster_analysis.md`
  - 0 solver runs (pure analysis)
  - 4 concrete predictive findings, 1 cross-bet design recommendation

## ~09:10 EDT — F375 + yale cross-machine message

**F375: 10 missing aux variants generated for F374 deep-tail cands.**
Coverage check found bit2_ma896ee41 (0/4), bit13_m4e560940 (0/4), and
bit28_md1acca79 (2/4 sr=61-only) had aux corpus gaps. Generated the
10 missing CNFs via `cascade_aux_encoder.py`, audited each → all 10
CONFIRMED. Updated `cnf_fingerprints.yaml` for all 4 buckets (sr60_force,
sr60_expose, sr61_force, sr61_expose) with new observed_n_kernels +
last_audited 2026-04-30.

  Aux corpus counts now: sr60_force 31 (was 28), sr60_expose 63 (was 60),
                         sr61_force 34 (was 32), sr61_expose 34 (was 32).
                         Total 162 (was 152, +10).

bit2 + bit13 + bit28 are now first-class participants in cascade_aux.
Future F343-class preflight measurements + F348-class cross-cand
injection sweeps can include them without per-cand encoder gaps.

**Cross-machine message to yale**: wrote
`comms/inbox/20260430_macbook_to_yale_F374_cluster_findings_for_math_principles.md`
explicitly tying F374's 4 signatures into yale's math_principles bet's
stated lines:
  - Signature 2 (`da≠de` 100%) is testable from yale's atlas continuations
  - Signature 3 (c/g 25% lighter) feeds yale's submodular mask selection
    + influence priors + REM/tail-law fitting
  - Signature 4 (bit3/bit2/bit28 dominate deep tail) suggests per-cand
    REM fit + prioritized seed selection in yale's strict-kernel work
  - F375's symmetric-corpus update enables yale to use bit2/bit13/bit28
    aux variants directly without re-encoding

Cumulative session 2026-04-30 commits to date: 31f902f → 7ae2fad → 6cf6a78
→ 4840bfe → 58e14a0 → (F375). 6-7 commits all green discipline.

`validate_registry.py` post-F375: 0 errors, 0 warnings.

## ~09:30 EDT — F376: F374 universality test on full 447k corpus

Aggregated F374's structural signatures across all 447,278 records in
the 47 per-cand corpora, stratified by hw_total band. **0 solver runs.**

Key finding: **F374's c/g asymmetry is HW-band-dependent, NOT universal.**

| HW band  | a/b/e/f vs c/g gap |
|----------|-------------------:|
| 60-64    | **+25.7%** ← peak  |
| 65-69    | +21.5%             |
| 70-79    | +11.4%             |
| 80-89    | +5.7%              |
| **90-99**| **−0.1%** ← crossing |
| 100-109  | −2.3%              |
| ≥110     | −2.6% ← reversed   |

The mode of the natural cascade-1 distribution (HW 90-99 per F101) is
the c/g symmetry crossing point. Below the mode the asymmetry is
positive and grows monotonically toward the deep tail; above the mode
it reverses.

Other 2 of F374's signatures ARE universal at 100% across all 8 HW
bands:
  - active register set [a,b,c,e,f,g] (cascade-1 hardlock)
  - da_63 ≠ de_63 (Theorem-4 a_61=e_61 doesn't extend to round 63)

Refined block2_wang heuristic:
  - HW < 80 (sub-mode): prioritize c/g cancellation
  - HW 90-99 (mode): all 6 registers equivalent
  - HW ≥ 100 (above mode): prioritize a/b/e/f cancellation (reversed)

Refined Phase 2D propagator cb_decide rule: branch on the LIGHTER
cluster, which is HW-dependent — c/g at deep tail, a/b/e/f at high
tail, neither at the mode.

Mechanism-level conjecture: SHA-256 round-function coupling between
Maj/Ch path (a/b/e/f) vs the other registers (c/g) is statistically
washed out at typical HW (mode), but DOMINATES the residual structure
at the deep tail where the constraint "register diff is small" leaves
round-function asymmetry as the dominant feature. At the high tail
the gap reverses, presumably because Maj-coupled registers accumulate
HW more slowly than free-path registers when diffs are large.

Shipped:
  - `bets/block2_wang/results/20260430_F376_universality_test_F374_signatures.md`
  - 0 solver runs (pure analysis)
  - F374 signatures 1+2 confirmed universal; signature 3 refined into
    HW-band-dependent piecewise model; signature 4 explained as
    consistent with band structure

## ~09:50 EDT — F377: F343 preflight on F375 cands FALSIFIES F340 polarity hypothesis

Ran F343 preflight on the 3 F375-generated aux_force_sr60 CNFs
(bit2_ma896ee41, bit13_m4e560940, bit28_md1acca79) to test F340's
"bit-31-of-fill SET → (0,1); CLEAR → (0,0)" rule. ~60s total compute.

All 3 have fill bit-31 SET, so F340 predicts (0,1) for all 3.
Empirical result: **all 3 give forbidden=(0,0).**

Combining F340 (6 cands) + F377 (3 cands) into a 9-cand panel:

  polarity (0,1) ← kbit ∈ {0, 10, 17, 31}
  polarity (0,0) ← kbit ∈ {2, 11, 13, 28}

The polarity is **kbit-dependent, NOT fill-dependent**. F340 saw a
correlation in the original 6-cand sample where kbit set and fill
bit-31 happened to co-vary, but couldn't disambiguate. F377
disambiguates: kbit is load-bearing.

Tentative replacement hypothesis: HW(kbit) parity:
  HW(kbit) ODD  → (0,0)  — perfect match for {2, 11, 13, 28} (HWs 1,3,3,3)
  HW(kbit) EVEN → (0,1)  — matches 3/4 of {0, 10, 17}; kbit=31 (HW=5)
                         is the outlier giving (0,1)

Testable via more F343 preflight runs at unprobed kbits.

Doesn't invalidate F348/F368/F369 conflict-reduction numbers — those
measured per-cand mining + injection on the same cand. F377 only
affects the cross-cand explanatory narrative.

Yale should be told (via the next comms): the F367 acknowledgement
message I sent yesterday cited F340's fill-bit-31 rule; that's now
superseded by F377's kbit-dependent finding.

Shipped:
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F377_polarity_extension_F340_falsified.md`
  - `F377_polarity_extension.json` aggregate
  - 3 preflight JSONs in /tmp
  - 9-cand kbit-polarity table for future cross-reference
  - 1 falsified hypothesis (F340) + 1 tentative replacement (HW-parity)

## ~10:30 EDT — User direction received: bridge-guided block2_wang. Executing.

User direction (verbatim summary):
  1. F349: close as UNREPRODUCED_PENDING_EVIDENCE; no model preserved
  2. Phase 2D propagator: NOT now; gate on bridge-cube harness
  3. MAIN: combine F374 + yale F378-F384 into bridge-guided block2 toolchain
  4. Concrete deliverables (5):
     #1 bridge_score.py: c/g cancellation, abef load, da≠de, D61/guard,
        W57[22:23] bridge polarity
     #2 validate against held-out corpora (rank known sub-65/sub-60 over controls)
     #3 block2_bridge_beam.py: beam over bit3/bit2/bit28 + 1 control
     #4 bridge assumption cubes + identical short solver probes
     #5 cross-cand learned clause clustering
  5. Cleanup: stale shells (none running), dashboard audit-failure split

Shipped this hour:
  - F349 CLOSED (status: UNREPRODUCED_PENDING_EVIDENCE) — no further chase
  - dashboard audit-failure-rate split: real failures 0.00% vs intentional
    --allow-skip 51 (2.90%) — explanation in dashboard.md, summarize_runs.py
    updated to track them separately going forward
  - **F378 deliverable #1: bridge_score.py (~250 LOC, stdlib only)**
    Validated on full 447k corpus:
      Hard rejects: **17.61%** of records (78,745 — the F377 bridge polarity
                    filter is doing real work)
      F371 sub-floor cands rank in top 30 of 368,533 accepted records
        (top 0.01%):
          bit2_ma896ee41:  rank #2  (score 49.59 hw=57)
          bit28_md1acca79: rank #4  (score 48.29 hw=67)
          bit3_m33ec77ca:  rank #11 (score 45.17 hw=63)
          bit13_m4e560940: rank #30 (score 42.41 hw=68)
      **New lead surfaced**: bit13_m916a56aa_fillffffffff scores #1
        (57.92, hw=59) — NOT in F374 dominator set, NOT in F371 sub-floor.
        Score is high because c/g are unusually light relative to a/b/e/f
        at this HW. Worth direct verification.

bridge_score.py is a different signal from extract_top_residuals.py:
the former captures structural asymmetry; the latter ranks by hw_total.
bit3 HW=55 (lowest absolute) ranks #11 because its c/g (HW 8, 9) aren't
the most asymmetric. Correct selector behavior.

Deliverables #2-#5 queued. Progress unit per direction: "a new bridge
selector, a falsified selector, or a generalized learned clause". This
hour shipped a new bridge selector + validated.

## ~10:50 EDT — F379 deliverable #3: bridge-guided hillclimb produces NEW LOWEST HW=56 for bit2

Built `block2_bridge_beam.py` — greedy W-space hillclimb using
forward_table_builder cascade-1 primitives + bridge_score evaluator.
4 cands × 3 seeds × 10k iters = 120k hillclimb steps. Wall: 5.4s.

Result:
  bit2_ma896ee41 NEW HW=56 (corpus floor was 57) ← below empirical floor
  bit2 score 55.96 (very high, beating F378's corpus #1 of 57.92's
  closest comparator on this cand)
  bit3/bit28/bit13_m916a56aa beams plateaued in local optima at
  HW 61-64 (corpus floors 55/59/59) — greedy single-bit-flip can't
  escape without restarts/SA

bit2 HW=56 W-witness:
  W1[57:60] = 0x2264b1ed 0x91b7504a 0xd8f36adf 0xa9603614
  W2[57:60] = 0x51ae863c 0x82f96c37 0xaae18478 0xe6019e05
  hw63 = [10, 11, 5, 0, 14, 11, 5, 0] (c=5, g=5 — strongly asymmetric)

This is a NEW data point not in any corpus. Highest-priority deliverable
#4 target: cert-pin verify it. Sub-30s compute. If UNSAT (likely),
falsified — adds discipline-noted negative. If SAT, **headline-class**.

Shipped:
  - `bets/block2_wang/encoders/block2_bridge_beam.py` (~250 LOC)
  - `bets/block2_wang/results/20260430_F379_bridge_beam_results.md`
  - `bets/block2_wang/results/search_artifacts/20260430_F379_bridge_beam.json`
  - 1 NEW data point below the empirical HW floor for bit2

Deliverables status:
  ✅ #1 (F378): bridge_score.py
  ✅ #2 (F378): hold-out validation, F371 in top 30/368k
  ✅ #3 (F379): block2_bridge_beam.py — bit2 HW=56 below corpus floor
  ⏳ #4: cert-pin probes of beam-discovered + F378 top-K
  ⏳ #5: cross-cand learned-clause clustering
