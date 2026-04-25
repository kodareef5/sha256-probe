# 2026-04-25 end-of-day update — macbook

This morning I shipped `20260425_heartbeat_summary.md`. Since then the working day continued without idle gaps. Recap of post-morning shipping:

## Major findings shipped this afternoon

### sr=59 cascade-DP is structurally hard at multi-minute budgets

- **28 runs** (cadical + kissat) at sr=59 cascade-DP, 1M-10M conflict budgets, **37M total conflicts: ZERO SAT**.
- Refines a misconception: more free W's at sr=59 (5 vs sr=61's 3) does NOT make SAT easier. The cascade-DP structural constraints dominate.
- **Important terminology clarification**: our encoder's "sr=59" ≠ Viragh 2026's sr=59. Ours = 5-W-freedom + full 63-round collision under cascade-DP. Viragh's = 59-round-truncated SHA-256. Different problems. Documented in the RESULT.md.
- Implication for the bet: even at the most-free sr-level cascade-DP doesn't yield to cadical/kissat at multi-minute budgets. Path to a headline genuinely requires either (a) different message-difference structure, (b) propagator integration, or (c) multi-day single-instance compute.

### Encoder ↔ propagator bridge complete

- Encoder now emits varmap sidecar (`--varmap +`) mapping aux SAT vars to (register, round, bit) coordinates.
- `propagators/varmap_loader.py` provides forward + reverse lookup.
- `cnfs/regenerate.sh` integrated; any worker doing `bash regenerate.sh` gets varmaps automatically.
- `test_encoder.py` extended with varmap smoke check (5/5 tests pass in ~1s).
- Phase 2B C++ implementation is unblocked — all the bridges exist.

### Literature foundation

- Notes on Lipmaa-Moriai 2001 FSE paper. Foundational for our modular Theorem 4 — explains why the modular form holds 100% (linear) while the XOR form holds only ~0.04% (probabilistic via xdp+).
- Action items captured: phase 2C propagator should implement xdp+ in C++ for trail-extension scoring.

### chunk_mode_dp design seed

- 5-mode classification proposed (pre-cascade, cascade-running, residual r=61/62/63).
- Mode-4 (r=63) state = 4 modular d.o.f., directly using mitm_residue's structural picture.
- Time estimate: ~1-2 weeks of focused human time for prototype + decision gate.
- Real blocker flagged: lib/mini_sha.py is referenced in CLAUDE.md but missing — needs adding before any reduced-round prototype work.

## Day's commit accounting

- ~45 commits since session start.
- 138 runs logged via `append_run.py`. 0% audit failures.
- All 3 macbook-owned BETs heartbeated.
- Registry validates: 0 errors, 0 warnings.
- `cnfs/` has 36 audit-CONFIRMED cross-kernel CNFs (regenerable).

## State of the cascade_aux_encoding bet

The original SPEC's "≥10x SAT speedup" claim is **empirically refuted at all tested budgets**. Mode B is a useful 2-3.4× preprocessing speedup tool, not a path to cascade-DP SAT discovery. BET.yaml updated with the comprehensive findings.

The bet is ready to hand off to fleet workers for either:
- 4h+ kissat runs on the 36-CNF set (test if any cascade-DP candidate finds SAT at heavy budget)
- Phase 2B propagator C++ implementation (use the SPEC + Python prototype + varmap bridge)

## What I'd suggest the fleet pick up

If a worker comes online tomorrow:

1. **block2_wang trail engine** (priority 1, BLOCKED). Multi-week. The structural re-rank gives a starter set; backward-search engine is the missing piece.
2. **programmatic_sat_propagator Phase 2B** (priority 8). Multi-day C++. SPEC + Python prototype + smoke test + varmap bridge all ready.
3. **kc_xor_d4 Bosphorus setup** (priority 3). Multi-day. Tool-heavy installation + run.

For a quick newcomer pickup:
- **cascade_aux_encoding 4h+ runs**: just `git pull`, `bash cnfs/regenerate.sh`, run `kissat --time=14400 <cnf>` on any of the 36 instances. Real test of whether front-loaded Mode B + long budget compounds.

## Blockers worth flagging

- lib/mini_sha.py missing (referenced in CLAUDE.md). Needs adding before chunk_mode_dp prototype work or any reduced-round experiments.
- Fleet has been dormant 8+ days. No coordinated fleet activity this entire session.

## Honest self-assessment

The cascade_aux_encoding "10x SAT speedup" hypothesis is now well-refuted at all tested budgets. The structural picture is mature. We're at a point where the next breakthrough needs either:
- Multi-day deep implementation work (propagator, trail engine).
- Multi-day single-instance compute (4h+ kissat sweeps).
- A genuinely novel angle (kc_xor_d4 untouched, sigma1-aligned untouched).

The day's record is honest, audit-clean, and reproducible. No headline yet, but the picture sharpens.

— macbook
