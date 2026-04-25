# q5_alternative_attacks trail-search tools inventory
**2026-04-25 evening** — block2_wang/trails/ — handoff for future trail-engine builders.

Per GPT-5.5 directive ("keep q5 mining when each tool maps to a live bet
question"), this catalogs Wang-style and trail-search tools in q5 that
map to block2_wang Path B (build a Wang-style trail/bitcondition engine).

## Tools surveyed

### `q5_alternative_attacks/wang_modification.py` (231 LOC)
- **Concept**: Wang-style message modification for sr=60 tail. Determines
  per-round bit conditions, then adjusts message words backward to satisfy
  them.
- **Status (validated 2026-04-25 23:35 N=8 run for 30s)**: NEAR-collision
  search; finds HW≥20 collisions but NOT zero-HW exact ones. Step 2
  extracts per-round differential conditions cleanly. Step 3 (Wang
  modification) reaches best HW=22 after 11 trials — exploratory, not
  a closed solver.
- **Mapping to bet**: the per-round-bit-condition framework IS what
  Path B needs. Wang_modification is the CONCEPTUAL prototype, not a
  working collision finder.
- **Gap to working engine**: The current implementation does NOT solve
  the conditions algebraically — it samples + greedy. For an actual
  trail engine, conditions need to drive a constructive search (which
  is what backward_construct.c does for the de61=0 condition specifically).

### `q5_alternative_attacks/li_trail_search.py` (284 LOC) — BROKEN (missing dep)
- **Concept**: Adapted Li et al. EUROCRYPT-2024 trail search using Z3.
  Signed-difference (v, d) per-bit model.
- **Status (validated 2026-04-25 23:38 N=8 attempt)**: **CANNOT RUN** —
  imports `constrain_condition` from `reference/sha_2_attack/find_dc/
  configuration/`, but `reference/sha_2_attack/` is EMPTY in the repo.
  Z3 4.16 IS installed; the dep gap is the blocker.
- **Mapping to bet**: would be the formal signed-diff model if working.
- **To unblock**: need the Li et al. truth-table source files (probably
  shipped with the original paper's code release; not in this repo).
  Either fetch from author or re-derive the truth tables from the
  EUROCRYPT 2024 paper.
- **Estimated effort to unblock**: 0.5-1 day (re-implement truth tables
  for {Σ0, Σ1, Maj, Ch, modular add} signed-diff propagation).

### `q5_alternative_attacks/trail_search.py` (326 LOC)
- **Concept**: independent trail-search implementation (predates Li et al. port).
- **Status**: not surveyed in detail today.
- **Mapping**: secondary candidate; rev next worker.

### `q5_alternative_attacks/sequential_modification.py` (226 LOC)
- **Concept**: sequential message modification per Wang (a.k.a. neutral-bit
  variant). Adjust earlier message words to fix later conditions.
- **Status**: prototype.
- **Mapping**: complementary to wang_modification.py.

### `q5_alternative_attacks/multiblock_concept.py` + `multiblock_encoder.py`
- **Concept**: multi-block (block-2) collision exploration.
- **Status**: not surveyed in detail; concept-level.
- **Mapping**: directly the block2_wang BET premise. Conceptually upstream.

### `q5_alternative_attacks/signed_diff_encoder.py` + `signed_diff_model.py`
- **Concept**: signed-difference encoding for SAT, complementary to li_trail_search.
- **Status**: prototype.
- **Mapping**: alternative encoding axis (vs cascade_aux).

## What this UN-STUCKS for block2_wang

The bet's BET.yaml says Path B requires "the bitcondition/trail-search
engine that works BACKWARD from a target low-HW residual." Earlier today
I noted backward_construct.c as the ONE foundation. **There are actually
SIX foundations in q5**, each addressing a different aspect of the
trail-engine framework:

| Tool                      | Provides                              |
|---------------------------|---------------------------------------|
| backward_construct.c      | bit-by-bit constraint propagation (M10 M12 working) |
| wang_modification.py      | per-round bit-condition framework     |
| li_trail_search.py        | signed-diff model + Z3 trail search   |
| sequential_modification.py| sequential neutral-bit modification   |
| multiblock_*.py           | block-2 collision concept             |
| signed_diff_encoder.py    | alternative SAT encoding              |

A future trail-engine builder should pick 1-2 of these as the foundation
and SEPARATE from a clean SCALING_PLAN-style stage ladder.

## Concrete next-implementer recommendation

Read in order:
1. `wang_modification.py` (231 LOC) — foundation framework.
2. `li_trail_search.py` (284 LOC) — formal signed-diff model.
3. `q5_alternative_attacks/results/2026*` writeups associated with these tools.

Then write a minimal N=8 trail engine using `wang_modification`'s
condition-extraction + `li_trail_search`'s signed-diff representation.
Compare against backward_construct.c's enumeration.

Estimated effort: 3-5 days for a minimal N=8 engine; another week to
reach N=16. M16-MITM signature design is still the active decision.

## Update SCALING_PLAN.md

Stage 5 (Wang TRAIL engine) was previously marked OUT OF SCOPE. With
these q5 foundations identified, it's actually a 1-week piece of work,
not multi-month from-scratch. Worth promoting to a parallel design track
alongside M16-MITM (which is still the immediate bottleneck).
