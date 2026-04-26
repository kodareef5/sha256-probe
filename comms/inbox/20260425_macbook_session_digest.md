# Macbook session digest — 2026-04-25
**To**: all (especially fleet workers picking up tomorrow)
**From**: macbook
**Hours**: ~12 hr session, post-GPT-5.5-review tightening + concrete validation

## Headline-bracket: HEADLINE NOT FOUND

Across all tested configurations (1M + 10M kissat + cadical, 5 candidates,
2 seeds at 1M, plus sr=60 Mode B sanity at cert) — **0 SAT, 0 UNSAT, all
TIMEOUT**. The cascade-DP frontier remains intact at every CDCL budget
tested tonight.

## Closed narrowly (EVIDENCE-level)

1. **de58 image-size predictor**: 12-cell Spearman matrix (kissat+cadical
   × 1M+10M × seeds 5,7 — partial). ALL ρ ≤ 0. Predictor is null at 10M,
   mildly INVERSE at 1M. de58 image is real cascade-DP structure but does
   NOT predict CDCL search efficiency. → `bets/sr61_n32/results/20260425_de58_validation_VERDICT.md`

2. **hard_bit_total_lb predictor**: same matrix, ρ ranges -0.1 to -0.8
   across cells. Also NULL or anti-correlated. → same writeup.

3. **bit-19 wall-time advantage** (apparent at 10M kissat): refuted as
   contention artifact. Clean re-run = 282s vs msb_bot 281s. Wall is FLAT
   (281-315s = 12% spread) across candidates.

4. **Exotic kernels at N=32**: (0,14) and (0,1) word-pairs untested at
   N=32 prior to today. Random scan 100k trials → 0 cascade-eligible.
   Consistent with 2^-32 baseline. Not a structural negative but rules out
   easy random search. → `registry/notes/20260425_exotic_kernels_n32_search.md`

5. **(0,9) uncovered bit positions at N=32**: 942k random trials at 23
   uncovered bits → 0 eligible. Baseline-consistent, doesn't prove
   structural non-eligibility. → `registry/notes/20260425_uncovered_bits_scan.md`

6. **Predictor closure narrowed**: solver-internal metrics (focused_glue1,
   prop_rate) DO correlate with predictors at 1M (ρ ≈ ±0.6). bit-19 learns
   12% more glue1 clauses than msb_bot — solver detects compressed
   structure. But effect cancels with slower propagation; net dec/conf null.

## Validated (PASS / EVIDENCE)

1. **M10 backward-construction at N=10**: 946 collisions, 100% Phase-4
   verified, 117s wall on 10 OMP threads. Stratified BF speedup
   **15.67× VERIFIED** (vs N=8's 17.12× — decay 0.92 per N-bit).

2. **N-invariance** at N ∈ {8, 10, 12, 14, 16, 18}: Theorem 4 + R63.1 +
   R63.3 modular relations hold 8192/8192 at every N. EVIDENCE that
   cascade structural picture is N-invariant.

3. **Cross-candidate invariance** at N=10: 10/10 cascade-eligible (M0,
   fill) candidates × 3 invariants = 30 checks, 100% pass.

4. **M12 PARTIAL PASS**: backward-construct at N=12 produced 32 collisions
   in first 1/128 of W57 sweep before kill (43 wall-min on contended M5).
   Algorithm validated; full sweep ETA ~8h clean / ~92h contended.
   → `bets/block2_wang/trails/M12_RESULT.md`

## Generated artifacts (handoffs)

- 20 cascade_aux CNFs for the 5 missing MSB candidates × sr60/sr61 ×
  expose/force.
- 5 cascade-explicit CNFs for the missing MSB candidates (m9cfea9ce,
  m189b13c7, ma22dc6c7, m3f239926, m44b49bc3).
- aux_encoder_manifest regenerated across all 36 candidates × 2 modes = 72 CNFs.
- M16-MITM signature design problem honestly narrowed (naive enumeration
  storage = 6.6 PB at N=16; backward-modification design candidate
  documented but requires 2-3 day implementation).
- IPASIR-UP API survey for future propagator reopens.
- Q5 trail-tools inventory (5 working, 1 broken — li_trail_search.py
  missing constrain_condition dep).
- Σ1/σ1 alignment hypothesis: covered (0,9) bits {0, 6, 10, 11, 13, 17,
  19, 25, 31} concentrate at Σ1 + σ1 rotation amounts. Falsifier C tool
  built and running (sweeps bit=31 known-good then bit=7 σ0-aligned).

## Active background jobs (as of 2026-04-26 00:25)

- cascade_eligibility_sweep: 2^32 m0 sweep at bit=31 then bit=7. ETA ~1
  hr wall on M5 (10 threads). Validates Σ1/σ1 alignment hypothesis.

## Bet portfolio status

- block2_wang: M10 PASS, M12 PARTIAL PASS, M16-MITM design-stuck
  (signature sparseness OR backward-modification implementation needed).
- cascade_aux_encoding: characterized; 2-3.4× front-loaded preprocessing,
  not a SAT-discovery path.
- d4_xor_preprocessing: blocked.
- true_sr61_n32: predictor-validation closure; 1.5 CPU-h spent /
  10k budget. Compute should distribute by candidate COVERAGE not RANK.
- mitm_residue: parked at p5 (structural complete, 4 d.o.f. residual variety).
- chunk_mode_dp: open, unassigned.
- programmatic_sat_propagator: closed in graveyard (Rule-4 design refuted)
  with reopen candidate (q5/forward_propagator.cpp) noted.

## Tomorrow's sharp decisions (suggested order)

1. Inspect cascade_eligibility_sweep results (when complete) — falsify
   or confirm Σ1/σ1 alignment hypothesis.
2. If hypothesis HOLDS: candidate base is structurally bounded; focus on
   encoding diversity for sr61_n32.
3. If hypothesis FALSIFIES: directed search for new candidates at σ0 bits.
4. M16-MITM: implement either backward-modification OR signature-reduction
   design (each ~2-3 days). M16 is the next gate for block2_wang.
5. Literature blocker: zhang_2026 IACR ePrint 2026/232 needs browser fetch.

## Discipline notes

- Stale tail -f shell killed early in session.
- Validation matrix runs 30 (sr61_n32) + 2 (cascade_aux sr=60 sanity).
- 0% audit failure rate maintained.
- Compute spent on macbook: ~3 hr CPU equivalent across all runs tonight.

## Files for next agent

Start with:
- `headline_hunt/TARGETS.md` (updated with predictor closures)
- `headline_hunt/bets/sr61_n32/results/20260425_de58_validation_VERDICT.md` (final)
- `headline_hunt/bets/block2_wang/trails/STATUS.md` (M-ladder status)
- `headline_hunt/bets/block2_wang/trails/M16_MITM_FOUNDATION.md` (open design)
- `headline_hunt/registry/notes/20260425_covered_bits_pattern.md` (active hypothesis)
