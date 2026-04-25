# Backward-Construction Scaling Plan: N=8 → N=10 → N=12 → N=16 → N=32

**Author**: macbook 2026-04-25 evening (in response to GPT-5.5 review request for a "concrete backward-construction design with scaling checkpoints").
**Status**: design only, no compute spent. Hand-off artifact for next implementer.
**Foundation**: `q5_alternative_attacks/backward_construct.c` (N=8, 17.12× speedup, 260/260 cross-validated).

This document IS the concrete implementation plan. Each scaling step has a LOC estimate, decision gate, and observable invariant to verify.

## Goal

Find a cascade-DP-compatible (W57, W58, W59, W60) at N=32 such that pairs (M1, M2) with the kernel-difference produce a full state collision at slot 64 — without paying the naïve 2^96 outer-loop cost.

## Why staged

Going N=8 → N=32 directly is the failure mode the bet has already hit (Phase 1 BLOCKED, see BET.yaml). Each intermediate N answers a falsifiable question:

| N  | Question answered                                                                  | Tractable benchmark           |
|---:|------------------------------------------------------------------------------------|-------------------------------|
|  8 | Does bit-by-bit constraint propagation work at all?                                | YES (existing foundation)     |
| 10 | Does the speedup-over-brute-force ratio hold or degrade?                           | exhaustive collision count    |
| 12 | Does it still beat brute force when 2^36 outer loop is the reference?              | exhaustive count + timing     |
| 16 | Where does brute force lose tractability — and does our search still fit?          | partial count + extrapolation |
| 32 | Full target. Authorization & MITM partition required.                              | one positive hit OR clean negative |

A failure to clear the N=10 or N=12 gate is itself a publishable structural finding: "backward construction at SHA-256 cascade-DP scales worse than 2× per bit-of-N."

## Stage 1 — N=10 port (Milestone M10)

**Target effort**: 1 day implementation + 0.5 day measurement.

### Deliverables
- `headline_hunt/bets/block2_wang/trails/backward_construct_n10.c`
  - copy of N=8 source
  - `#define N 10`, `#define MASK ((1U<<N)-1)`
  - rotation values via `scale_rot()` (already parameterized)
  - K, IV unchanged (32-bit constants masked to N bits per the existing pattern)
- Cascade-eligibility scan to find valid (m0, fill) at N=10. The N=8 source hard-codes m0=0x67, fill=0xff. At N=10, run the same a_56 collision search:
  - 2^10 m0 × few fill choices = 4k trials × 56 SHA rounds ≈ ms
  - keep first 5 cascade-eligible candidates
- Reference: brute force over 2^40 = 2^(4N) tuples with cascade-1 forced. Expected per-candidate collision count: scaling argument predicts O(2^(4N) × 2^-N) = O(2^(3N)) per candidate. At N=10: ~2^30 = ~10^9 collisions in the brute-force outer loop, much too many to enumerate. **Reduce the reference**: enumerate only collisions whose final state matches a fixed signature, e.g., bit-0 of de61 = 0 conditional on full residual = 0. That cuts the reference to a tractable size.

### M10 decision gate
Pass if:
- Constructive solver matches brute-force collision count exactly (≥99% with stochastic sampling allowed for tractability). Cross-validation must be byte-identical for at least 1k matched solutions.
- Speedup factor ≥ 8× over brute force (vs 17× at N=8 — half-decay-per-2-bit-N is acceptable).
- No false positives: every BC-found solution verifies against full-state-collision.

If ANY of those fail: **document the regression specifically** (which test, what speedup, what false-positive type). Bet does NOT die — only this specific scaling design is killed; algorithm-level redesign warranted.

### M10 invariants to verify (in addition to collision count)
1. **Theorem 4 hold**: `da_61 ≡ de_61 (mod 2^N)` for all M10 collisions. This was empirically verified at N=32; should hold at N=10.
2. **Hardlock pattern**: each candidate's de58 image at N=10 should produce a hardlock-mask analogous to N=32 results. Confirm pattern emerges (not literally same bits).
3. **R63.1 (dc=dg)** and **R63.3 (da-de=dT2)** modular relations from mitm_residue should hold.

## Stage 2 — N=12 port (Milestone M12)

**Target effort**: 0.5 day (mostly cascade-eligibility scan).

### Deliverables
- `backward_construct_n12.c` — same edits as N=10
- 5 cascade-eligible candidates at N=12
- Brute-force reference at 2^48 outer loop — UNTRACTABLE in full. Use stratified sampling: brute-force enumerate 2^32 random tuples and extrapolate count.

### M12 decision gate
Pass if:
- Speedup ≥ 4× over brute force (decay rate consistent with N=8: 17× → N=10: 8× → N=12: 4× — geometric).
- Algorithm runtime per "valid" tuple is bounded by O(N × constant). If the per-tuple work scales as O(N²) or worse, the path becomes infeasible at N=32 regardless of outer loop reduction.
- The 4-d.o.f. residual variety (R63 constraints) **predicts** the reduced collision count to within 2× factor at N=12.

If pass: this validates the algorithmic scaling. Any further failure at N>12 must come from outer-loop scaling, not constraint-propagation efficiency.

If fail: redirect bet to MITM-only approach (skip backward construction). Backward construction's per-step overhead would dominate.

## Stage 3 — N=16 stress test (Milestone M16) — REVISED 2026-04-25 evening

**REVISION**: original M16 gate said "complete full 2^48 outer loop in ≤ 2 hours wall." Based on real M10 measurements (117s wall on 10 OpenMP threads for 2^30 outer triples), the geometric extrapolation gives N=16 ≈ 117s × 2^18 = ~30M seconds = ~350 days single-machine. **M16 single-machine BC is INFEASIBLE.**

**Revised M16 plan**: M16 must include the MITM partition, not be a pure-BC milestone. Effectively M16 IS the first MITM milestone.

### MITM partition at N=16 (CORRECTED budget)
- Forward path (W57, W58): 2^32 outer × 2^16 inner = 2^48 ops. ~10 minutes wall on 10 threads at M10 rates.
- Storage: 2^32 records × ~16 bytes (state_59 = 8 × 16 bits = 16 bytes) = 64 GB. Tractable on a single NAS-equipped machine.
- Backward path (W59, W60): 2^32 outer × 2^16 inner = 2^48 ops. ~10 min.
- Match phase: hash-join on state_59 signature (16-byte key). Expected matches at N=16 with 4-d.o.f. residual variety: ~2^32 × 2^32 / 2^48 = 2^16 candidate tuples. Verify each (~1ms each = 65 sec).

**Total M16-MITM compute**: ~25 min wall on a single machine with 64 GB storage.

### M16 decision gate (revised)
Pass if:
- MITM forward + backward + match phases complete in budget without OOM.
- Match phase produces verifiable collision tuples that pass Phase 4 (independent SHA re-execution at N=16).
- ≥1 verified collision per candidate at N=16.

If pass: scaling architecture validated; M32-MITM is a (much) bigger version of the same architecture.
If fail: kill memo with the failed phase. Backward construction without MITM doesn't reach N=16; bet moves to graveyard or gets a fundamentally different next-stage design.

## Stage 4 — MITM partitioning at N=32 (Milestone M32-MITM)

**Target effort**: 2-3 days implementation. Compute: bounded by per-candidate kissat-equivalent budget.

### Why MITM
Naïve N=32 backward construction has 2^96 outer loop. Cannot run. The 4-d.o.f. residual variety (mitm_residue bet) reduces effective constraint count to 128 bits (4×32), but that still leaves 2^96 ÷ 2^32 = 2^64 effective per-candidate work — beyond reach.

MITM split:
- Forward path (W57, W58): enumerate 2^64 → cache state_59 keyed by signature. Cost 2^64 SHA-rounds + storage 2^64 entries × ~32 bytes = 0.5 EB. **Storage infeasible.**
- Forward path (W57, W58 with TIGHT-W59-PREFIX): partial enumeration 2^32 × 2^16 = 2^48 with reduced cache. Storage ~10 TB. **Borderline tractable for a fleet machine with NAS.**

### Deliverables (M32-MITM)
- Two binaries:
  - `bc_n32_forward.c` — enumerates forward, emits (state_59, W57, W58, partial_W59) records
  - `bc_n32_backward.c` — enumerates backward from candidate state_64=collision, emits matching (state_59, partial_W59, W60) records
- Match phase: hash-join on `(state_59, partial_W59)` 32+16 = 48-bit signature. Expected matches: 2^48 × 2^48 / 2^48 = 2^48 (need filtering).
- Filter: each match generates a candidate (W57..W60) tuple — verify against full SHA cascade. ~2^48 verifications at ~1µs each = ~80 hours single-thread. Parallelize across fleet.

### M32-MITM decision gate
Pass if **even one verified collision tuple** is found in budget.
Fail: produce kill memo with concrete invariant violated; bet moves to graveyard.

### Authorization required
M32-MITM is a multi-machine multi-day compute. **DO NOT launch without explicit user authorization.** The decision-gate document must include:
- Storage required (precise GB)
- Total fleet-CPU-hours
- Per-machine memory footprint
- Failure-recovery: which intermediate artifacts survive a crash

## Concrete next steps (in order, REVISED 2026-04-25)

1. ✅ **M10 implementation** — DONE 2026-04-25. M10_RESULT.md: 946 collisions, 100% verified, 117s wall, 15.67× speedup VERIFIED via stratified BF.
2. ▶️ **M12 implementation** — IN FLIGHT 2026-04-25 evening. ETA ~2 hr wall on 10 threads (contended with de58 validation matrix). Algorithmic feasibility ladder.
3. **M16 implementation REVISED**: not pure-BC (infeasible single-machine), but M16-MITM. Forward+backward+match architecture. ~25 min wall + 64 GB storage. Single machine sufficient.
4. **M32-MITM design refinement** — write the storage/match-phase architecture (multi-machine, not single).
5. **Authorization request** to user with M16-MITM and M32-MITM concrete budgets.

## What this plan IS

- A handoff artifact: a future worker (any machine) can implement M10 today without further design.
- A falsification ladder: each milestone has a concrete decision gate.
- An honest scope: the multi-week claim is decomposed into per-stage estimates totaling ~5 days of focused implementation pre-N32, plus the N=32 compute step.

## What this plan is NOT

- Not a Wang TRAIL engine. Wang's bit-condition + message-modification machinery is a STAGE-5 extension that subsumes backward construction with probabilistic forward search. Out of scope here.
- Not a guarantee of N=32 success. Each stage can fail; the value is structured falsification.
- Not authorized to launch. Stage 1 (M10) and Stage 2 (M12) are local-only and free; Stage 3 and beyond need user sign-off.

## Tracking

When a worker picks up M10:
- Update BET.yaml: `current_progress` → "M10 in progress"; `last_heartbeat` → today
- Update mechanisms.yaml: `next_action` → "Complete M10 decision gate"
- Append result (PASS/FAIL with specific numbers) to this file as Stage 1 outcome
- If PASS: same for M12. If FAIL: write kill_criteria_M10.md with the specific decision-gate violation.

## Caveat (claim-language tightening per GPT-5.5 review 2026-04-25)

This plan is a DESIGN, not a result. None of the milestones have been executed beyond M0 (N=8 foundation, which is verified). All scaling estimates are extrapolations from N=8 timing data and from theoretical complexity. Decision gates are ranges, not assertions. Treat each gate as EVIDENCE-level outcome at best until exhaustively run.
