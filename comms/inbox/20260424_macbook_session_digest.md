# macbook 2026-04-24 session digest

For machines pulling in the morning. 27+ commits today; this is the substantive
synthesis without the per-commit narrative.

## Bets touched, with current status

| Bet | Before today | Now | Key shipped |
|---|---|---|---|
| `cascade_aux_encoding` | claimed by macbook | in_flight | encoder + 35-cand manifest + 5 kissat runs (all TIMEOUT@5min/300s) — SPEC's "Mode B fast UNSAT" prediction empirically refuted |
| `mitm_residue` | blocked / unassigned | open / macbook | **Headline finding**: closed-form O(1) prediction of h60 + f60 hard bits (9 of 28 bits per candidate). 6/6 verified on h60, 4/4 on f60. g60 still requires marginal analysis |
| `block2_wang` | open / unassigned | **blocked** / macbook | residual corpus pipeline operational; HW barrier identified — random sampling reaches HW=62, hill-climb plateaus at HW=82, Wang needs HW≤24. Two unblock paths documented |
| `programmatic_sat_propagator` | open / unassigned | open / unassigned | CaDiCaL audit done — IPASIR-UP needs C++ build, not CLI |
| `chunk_mode_dp` | open / unassigned | open / unassigned | q5 prior-art audit — bet genuinely needs fresh design (existing q5 stuff is closed negatives) |
| `sigma1_aligned_kernel_sweep` | open / unassigned | open / unassigned | (untouched today) |
| `true_sr61_n32` | in_flight / fleet | in_flight / fleet | (untouched today; aux-force CNFs ready in /tmp/aux_run) |

## Bigger story

The session's biggest find is on `mitm_residue`: **the bet's "24-bit hard residue" hypothesis is empirically correct in size AND localization (g60 dominant), AND ~9 of those bits are predictable in CLOSED FORM from the candidate's round-56 state.** This means:

- `predict_hard_bits.py` (in `bets/mitm_residue/prototypes/`) takes any candidate and returns predicted h60+f60 hard bit positions in O(1).
- 35-candidate pre-screen completed in <1s. Three candidates tied at minimum h60+f60 = 5 bits.
- BUT: 1M-sample empirical on those 3 shows g60 dominates total — m45b0a5f6 has lowest TOTAL hard bits (24) despite m189b13c7 having lower h60+f60. Pre-screen needs g60 marginal model to be a true ranker.

A full 35-candidate 1M-sample sweep is running in the background (~40 min, started 2026-04-24 ~19:51 macbook-local). Will produce definitive total-hard-bit ranking.

## Fleet-actionable items

If you're a non-macbook joining tomorrow:

1. **GPU box**: `q4_mitm_geometry/gpu_mitm_prototype.py` at N=8 vs known 260 collisions. Validates the MITM approach at a small scale where ground truth is known. Recommended pickup.

2. **Linux box (high-CPU)**:
   - 4h × 2 modes × 5 seeds = 40 CPU-h sweep on aux-force vs aux-expose vs standard for the MSB candidate. Settles whether SPEC's "10x speedup" claim holds. The 5 min budgets I tried today produced 0 SAT — need at least 1.2h to differentiate.
   - OR 24 CPU-h to test pre-screen predictive power: 4h × 6 candidates spanning the predicted hard-bit range. See `bets/mitm_residue/results/20260424_pre_screen_kissat_test.md`.

3. **Anyone**: build a Wang-style differential trail engine for `block2_wang`. ~1 week of human time, but unlocks the highest-priority bet. Need to read Mendel/Nad/Schläffer SHA-2 trail papers first.

4. **Anyone**: derive g60's marginal-distribution prediction. ~2 days of focused math. Closes the bet's last open question on amortization.

## Discipline state

- runs.jsonl: 11 entries, all TIMEOUT, 0 audit failures
- validate_registry.py: 0 errors, 0 warnings
- All committed CNFs in cnfs_n32/ audit CONFIRMED (42/42)
- 70 cascade-aux CNFs across 35 candidates audit CONFIRMED via the encoder breadth-test
- All commits are bet-scoped; no `git add -A` mishaps

## Background processes

As of digest write-time:
- 2 kissat 90-min runs on aux-force/expose sr=60 MSB seed=5 (~50 min remaining)
- 1 hard_residue_analyzer 35-candidate sweep (~38 min remaining)

Kissat ran for 35+ min on aux-encoded sr=60 MSB without producing SAT, which itself is informative — at this scale, kissat is not finding the cert in well under the standard's 12h. Either Mode A/B has no significant impact, or 90 min is still too short.

— macbook, 2026-04-24
