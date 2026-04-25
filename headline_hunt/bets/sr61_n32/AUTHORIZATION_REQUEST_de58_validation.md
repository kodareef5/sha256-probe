# Authorization request: de58-rank → solver-behavior validation matrix
**Author**: macbook 2026-04-25 evening (in response to GPT-5.5 review).
**Status**: NOT YET AUTHORIZED. This is a budget-and-matrix request to the user.

## Question to answer

Does the de58 structural rank (image size, hardlock count, low-HW reachability) **predict actual solver behavior** on cascade-DP sr=61 CNFs?

If YES: the de58 family of findings is a real predictor → reallocate sr61_n32 compute toward most-promising candidates → potentially catch the headline faster.

If NO: de58 is structurally interesting but search-irrelevant → mark as "structural-but-not-predictive" in TARGETS.md and stop spending tokens on de58-derived priority arguments.

## Matrix (5 candidates × 2 solvers × 1 seed × 2 conflict budgets)

| Candidate                            | de58 image | hardlock bits | min-HW de58 | Why included                            |
|--------------------------------------|-----------:|--------------:|------------:|-----------------------------------------|
| bit-19_m51ca0b34_fill55555555        |        256 |            13 |          14 | Compression extreme (most-narrow image)  |
| bit-25_m09990bd2_fill80000000        |       4096 |            13 |          ~9 | Compression second-tier                  |
| msb_m9cfea9ce_fill00000000           |       4096 |            22 |           7 | SURPRISE candidate (20-bit compression, MSB family) |
| msb_m189b13c7_fill80000000           |     130049 |            28 |           3 | Low-HW extreme (HW=3 reachable)         |
| msb_m17149975_fillffffffff (cert)    |      82826 |            22 |          10 | Cross-validation against known sr=60 SAT |

**Each cell**: solver run with `--time=<budget>` against the candidate's existing `cnfs_n32/sr61_cascade_*.cnf`.

| solver | seed | budget A     | budget B      |
|--------|-----:|-------------:|--------------:|
| kissat |    5 | 1M conflicts | 10M conflicts |
| cadical|    5 | 1M conflicts | 10M conflicts |

5 cands × 2 solvers × 2 budgets = **20 runs**.

## Estimated wall time per run (from prior cascade_aux runs at sr=59)

- kissat 1M conflicts: 14-16s (per recent runs in runs.jsonl)
- kissat 10M conflicts: ~150s (extrapolated 10×)
- cadical 1M conflicts: 22s
- cadical 10M conflicts: 309s (already observed)

**Total wall time** (sequential, single-machine):
20 runs × ~125s avg = **~42 minutes**, single-threaded. Or ~6 minutes wall on 8 parallel cores.

## Outcomes & their meaning

Possible outcomes for a single (candidate, solver, budget) cell:
- SAT — collision found! Headline. No matter the budget.
- UNSAT — conclusive. Candidate provably has no sr=61 SAT in the encoded space.
- TIMEOUT — inconclusive at this budget.

The matrix is designed to find correlation between de58-rank and TIMEOUT-likelihood.

### Predictive outcomes (de58 IS a predictor)

If de58 rank correlates with conflict count to first-SAT or to UNSAT proof:
- bit-19 (compression extreme) finds SAT/UNSAT first → compression predicts solver-friendliness
- OR msb_m189b13c7 (low-HW extreme) finds SAT/UNSAT first → low-HW predicts
- OR msb_m9cfea9ce (SURPRISE) finds SAT/UNSAT first → high-locked + low-HW predicts

### Null outcomes (de58 is NOT a predictor)

- All 5 candidates × all 4 cells TIMEOUT identically at 10M budget — no predictive signal.
- Cert candidate (mediocre by all de58 metrics) finds SAT first — predictor inverted/wrong.
- Random scatter — no rank-vs-time correlation.

## Decision rule

After running the matrix:
1. **If any SAT found**: stop, report headline, regardless of de58 prediction.
2. **If pattern matches one of the predictive outcomes above**: reallocate next 10k CPU-h budget toward that family of candidates. Update mechanisms.yaml with the new prediction.
3. **If null outcome**: Update TARGETS.md "de58 family" section with EVIDENCE-level conclusion: "de58 rank does not predict cascade-DP-CNF solver behavior at the tested budgets. Structurally interesting but search-irrelevant. Mark as closed."

## What I'm NOT proposing

- NOT proposing multi-day kissat sweeps. 42 wall-minutes single-machine OR 6 wall-minutes with 8 parallel cores.
- NOT proposing FlowCutter, d4, or any tool not currently set up.
- NOT proposing `lib/` or encoder modifications.
- NOT proposing modifications to existing CNFs — just running them with bounded budget.

## Audit/log discipline (will be applied)

- Each CNF passes `headline_hunt/infra/audit_cnf.py` before run; expected verdict CONFIRMED. Run aborts on UNKNOWN/CRITICAL_MISMATCH.
- Each run logged via `headline_hunt/infra/append_run.py` with full metadata (CNF sha256, git commit, solver, seed, budget, status, wall time, conflicts).
- Runs.jsonl auto-rolls into the dashboard. Audit-failure-rate visible on next dashboard regen.

## Authorization questions to user

1. **OK to launch this 20-run matrix at ~42 min single-threaded wall time?**
2. **OK to use 8 parallel cores (would consume ~all macbook compute for ~6 min)?**
3. **OK to interpret SAT result as "publish headline-hunt finding immediately" — or does that need its own re-authorization?**

## What I'll do until authorization

(Per GPT-5.5: keep producing concrete handoff artifacts.)

- M10 backward-construction port for block2_wang (Stage 1 of `SCALING_PLAN.md`). No compute. Local only.
- Continue claim-language audit of writeups (replace overclaims with EVIDENCE-level wording).
- Mine q5 for any additional unmapped tool relevant to active bets.
