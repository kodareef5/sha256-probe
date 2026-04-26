# macbook hourly — 2026-04-26

## 02:47 EDT — Hourly comm rolled to today

Per discipline rule (`comms/inbox/<TODAY>_macbook_hourly.md`), creating
today's file. Yesterday's accumulated entries remain in
`20260425_macbook_hourly.md` with chronological history through end of
2026-04-25.

## Live state at session continuation

Background:
- queue4 sweeps running (bit=11 fill=0xff active, bit=25 fill=0xff queued)
- Compute: ~10 more min for bit=11 + ~12 min bit=25 = ~22 min total

Registry: 45 cascade-eligible candidates at N=32 (was 36 at session start).
Validation matrix: 41 sr61_n32 runs logged, 0 SAT/UNSAT, all TIMEOUT.
Audit failure rate: 0.00% across 181 total runs.

## Open headline-related questions (post-sprint)

1. Will bit=11 fill=0xff sweep yield more sigma1-aligned candidates?
2. Will bit=25 fill=0xff sweep similarly?
3. Across all swept (bit, fill) cells: is rate truly uniform 2^-31, or
   does some structural pattern emerge with more data?

## What this morning's session needs

When a fleet machine wakes up, the high-leverage continuation:
- Pick up any uncovered (bit, fill) cell from sweep_coverage.md
- Run cascade_eligibility_sweep <bit> <fill> for ~12 min wall
- Register any eligible m0 with the standard pipeline (encode + audit + yaml + commit)
- Smoke test new cands at 1M kissat (~22s each)

Strategic priority for headline path:
- M16-MITM design (block2_wang) is still the open gate
- Backward-modification design needs implementation (~2-3 days)
- de58/hard_bit predictors confirmed search-irrelevant; new cands add
  search space but not solver-friendliness

## 02:55 EDT — bit=11 fill=0xff: 0 eligible. bit=25 fill=0xff at 6% with 1 ELIGIBLE found

bit=11 fill=0xff full 2^32: 0 eligible (registered cands at this bit are
fill=0x00 and fill=0x55 only).

bit=25 fill=0xff: at least 1 found so far (m=0xa2f498b1, verified eligible
via Python). Sweep 6% done, more may emerge.

Session running total: 14 cells exhaustively swept. Each ~12 min wall.
Registry 36 → 45 (+9 candidates from 4 productive cells; 10 cells found 0).

Pattern emerging: each bit has SPECIFIC fills that produce eligibility.
Random-fill sampling at a bit yields nothing if you miss the productive fills.

Notable structural unique: m=0x99bf552b is the ONLY candidate of 45 whose
hardlock_mask equals exactly 2^kernel_bit (just the kernel bit locked,
31 of 32 de58 bits vary). The "anti-bit-19" structural extreme.

## 03:05 EDT — Launched 4 more strategic sweeps (~48 min wall total)

bit=10 fill=0xff (σ1 shift, registered at 0x00,0x55,0x80 — missing 0xff)
bit=2  fill=0xff (Σ0 amount, FULLY untested)
bit=17 fill=0xff (σ1 amount, registered at 0x00,0x80 — missing 0xff)
bit=13 fill=0x80 (Σ0 amount, registered at 0x00,0x55,0xaa,0xff — missing 0x80)

Targeting gaps in registry coverage. Expected ~6-8 more candidates.
Will register + audit + smoke-test as discovered.

## 03:15 EDT — DISCIPLINE FIX: 16 stale aux sr=61 CNFs regenerated

Audit-sweep of all 100 cascade_aux CNFs found 16 with CRITICAL_MISMATCH
verdicts. Root cause: encoder was updated 2026-04-25 (modular-diff aux
added for Phase 2C); old sr=61 CNFs no longer match new sr=61 fingerprint
range — they fall in sr=60 range.

These 16 had been used in runs.jsonl with sr_audit=CONFIRMED at
generation time but became MISMATCH after fingerprint update.

Fix: regenerated all 16 using current encoder. All 16 now CONFIRMED.
Final audit: 100/100 cascade_aux CNFs CONFIRMED.

Past Mode B speedup characterization may have ~12% sr-level misattribution
(16 of 130 runs hit sr=60 content tagged sr=61). Needs re-verification
before bet's "2-3.4× front-loaded" claim is taken as sr=61 specific.

Memo: bets/cascade_aux_encoding/results/20260426_audit_rot_fix.md

bit=10 sweep also done: 0 eligible. bit=2 starting.

## 03:45 EDT — Queue5 DONE; bit=13 fill=0x80 found 1 NEW (registry 51)

Queue5 final results:
  bit=10 fill=0xff: 0
  bit=2  fill=0xff: 3 NEW (Σ0-aligned hypothesis falsified)
  bit=17 fill=0xff: 0
  bit=13 fill=0x80: 1 NEW (m=0xa23ae799, gap-fill for bit=13)

Total session: 36 → 51 (+15 NEW candidates).
18 cells exhaustively swept. Σ1/σ1 alignment hypothesis closed across all
bit-position alignment types (boundary, σ0, Σ0, σ1, non-aligned).

Plus tonight: discipline fix for 16 stale cascade_aux sr=61 CNFs (audit-rot
post-encoder-update). All 100 aux CNFs now CONFIRMED.

The session's substantive shipped:
- Registry: 36 → 51 (+15)
- New CNFs: 15 cascade + 16 aux = 31 (some already shipped earlier in session)
- Audit-rot fix: 16 stale CNFs regenerated
- 18 (bit, fill) cells exhaustively swept
- 14 new cands smoke-tested (TIMEOUT, normal dec/conf range)

## 03:55 EDT — Queue6: 4 never-tested bits at fill=0xff (~48 min)

bit=1, bit=5, bit=8, bit=14 — never tested at ANY fill.
Expected ~4 new cands at Poisson(1.0) rate. Substantive forward motion.

Session running total (post-queue6 fully populates if it finds ~4):
  Registry: 36 → 51+ (likely 55+)
  Cells swept: 18+ → 22

## 04:00 EDT — Queue6 DONE; bit=14 fill=0xff found 3 NEW (registry 55)

Queue6 (4 never-tested bits at fill=0xff) final tally:
  bit=1  fill=0xff: 1 NEW (m=0x6fbc8d8e)
  bit=5  fill=0xff: 0
  bit=8  fill=0xff: 0
  bit=14 fill=0xff: 3 NEW (m=0x67043cdd, 0xb5541a6e, 0x40fde4d2) ← strongest yield
Total: +4 NEW from queue6.

Session running totals (post-queue6):
  Registry: 36 → **55** (+19, +53% growth)
  Cells exhaustively swept: 22
  All audits CONFIRMED. 0% audit failure rate maintained.

Pattern: 4 first-time-tested non-aligned bits (1, 2, 8, 14) at fill=0xff:
  bit=1  yield 1 (Poisson lower)
  bit=2  yield 3 (high)
  bit=8  yield 0 (Poisson lower)
  bit=14 yield 3 (high)
Bit=5 (non-aligned) and bits 7,10,11,17,19,22 (variously aligned) all
yielded 0 at fill=0xff. **No correlation between rotation alignment and
eligibility yield**, confirming Σ1/σ1-alignment-irrelevant for the
hardlock_mask ≠ 2^kernel_bit case.

Pushed `299f95d`. bit=14 is the productive surprise of queue6.

## 04:15 EDT — M16-MITM forward enumerator VALIDATED at N=10

While queue7 runs in background, validated `m16_mitm_forward.c` at N=10:
- Compiled binary emits 2^30 records / 23.6 GB in ~37s on M5.
- Independent Python validator (200 random samples, seed=42) checks:
  da[57]=da[58]=da[59]=0 modular AND state matches record.
- **200/200 PASS** — EVIDENCE-level validation.

Until tonight m16_mitm_forward.c was source-only. Now it's a working
ground-truth artifact. block2_wang bet's M16_MITM_FOUNDATION step 3
complete; steps 4 (backward) + 5 (match) remain.

Pushed `a021d1e`. M16_FORWARD_VALIDATED.md memo + validator.py committed.

## 04:18 EDT — queue7 partial: bit=14 fill={0,55} both 0 eligible

Queue7 partial (2/4 cells done):
  bit=14 fill=0x00: 0 eligible
  bit=14 fill=0x55: 0 eligible
  bit=2  fill=0x00: running ~6%
  bit=9  fill=0xff: queued

bit=14 candidates clustered at fill=0xff; other fills produce 0. Pattern
matches earlier observation: each (bit, fill) pair has its own
eligibility character; same bit at different fill yields very different
counts. This further reinforces the falsified Σ1/σ1 alignment hypothesis.

Session running totals (post-this-turn):
  Registry: 36 → **55** (+19)
  Cells exhaustively swept: 24 (queue7 +2 done so far)
  Substantive shipped: 5 commits this turn (registry, smoke-tests,
    dashboard, distribution analysis, M16-MITM forward validation)

## 04:20 EDT — Per-pulse summary

Per-turn: 5 commits pushed. Concrete forward motion across:
  - Registry expansion (queue6 finish: bit=14 +3 NEW)
  - Discipline (4 smoke-tests via append_run.py)
  - Visibility (dashboard refresh)
  - Analytic (de58 image-size distribution memo)
  - Implementation (M16-MITM forward enumerator validated)

## 04:25 EDT — queue7 DONE: 0 NEW (4/4 cells empty)

Final queue7 results:
  bit=14 fill=0x00: 0 eligible
  bit=14 fill=0x55: 0 eligible  
  bit=2  fill=0x00: 0 eligible
  bit=9  fill=0xff: 0 eligible (NEW first-time-tested bit)

bit=14 produces eligibles ONLY at fill=0xff. The same pattern observed
at bit=18 and bit=3 — each (bit, fill) cell has its own eligibility
character; cells with high yield at fill=0xff often produce 0 at
fill=0x00 or fill=0x55. The (bit, fill) granularity is fundamental.

bit=9 fill=0xff (newly tested): 0 eligible. Adds another data point
to the falsified Σ1/σ1 alignment hypothesis.

Session totals (final, at this turn):
  Registry: 36 → **55** (+19, +53%)
  Cells exhaustively swept: **26** (up from 22 at start of turn)
  Substantive shipped this turn: 9 commits — registry expansion,
    smoke-tests, dashboard, distribution analysis, M16-MITM forward
    validation (N=8 + N=10), M16-MITM design-gap critique, queue7
    sweep results.

## 04:30 EDT — Strategic update

The queue7 result REINFORCES that follow-up sweeps at non-fill=0xff
cells of productive bits are LOW EV. Each bit's "winning fill" appears
unique. Future sweep effort should target NEW bits at fill=0xff
(remaining: 12, 15, 16, 20, 21, 23, 24, 26, 27, 28, 29, 30) rather
than re-scan productive bits at other fills.

Concrete deliverables this session beyond registry growth:
- M16-MITM forward enumerator validated (200/200 at both N=8 + N=10)
- M16-MITM backward enumerator design-gap identified (NOT viable
  as written — match key saturated)
- de58 image-size distribution documented (2^8 outlier at bit=19)

The block2_wang bet now has CRISP design intel: forward is solid,
backward needs redesign before any further C implementation.

## 07:05 EDT — Morning state. Queue8 still running (overnight contention)

Status as of 2026-04-26 07:05 EDT (morning, ~9h after queue8 launched):

**Queue8 progress (bit=12, 15, 16, 20 at fill=0xff)**:
  bit=12 fill=0xff: 1 NEW (m=0x8cbb392c) — completed 22:24 EDT 2026-04-25
  bit=15 fill=0xff: 3 NEW (m=0x1a49a56a, 0x6a25c416, 0x28c09a5a) — completed 22:31 EDT
  bit=16 fill=0xff: 0 — completed 07:00 EDT 2026-04-26 (took 8.5h overnight)
  bit=20 fill=0xff: ~6% done with 1 eligible (m=0x294e1ea8) — running

**Why bit=16 took 8.5h**: I ran 4 kissat smoke tests (bit=12 + 3×bit=15)
in parallel with bit=16 sweep. The m=0x28c09a5a kissat smoke (de58
small-image cand) was heavily descheduled and ran ~8h wall vs ~45s CPU.
This blocked bit=16 sweep from completing for the same period.

**Lesson**: avoid running CPU-heavy smoke kissat tests parallel with
exhaustive sweeps. Sequential is better for time accounting and
avoiding macOS scheduler starvation.

**Session totals as of 07:05**:
  Registry: 36 → **59** (+23, +64% growth)
  Cells exhaustively swept: **29** + bit=20 in flight
  Substantive shipped: 16+ commits — registry growth, smoke tests,
    M16-MITM forward validation (N=8 + N=10), M16-MITM backward
    design-gap critique, de58 distribution analysis, sweep tracker.
  All audits CONFIRMED. 0% audit failure rate maintained across 194 runs.

## 07:15 EDT — Fingerprint refresh + queue9 mid-stream

**Shipped this pulse**:
- `[infra] cnf_fingerprints` (06540e7): observed_n 13 → 37 across 37 sr61_cascade
  CNFs in cnfs_n32/. Vars/clauses bounds UNCHANGED — encoder output
  structurally stable across queue6/7/8 expansion's new kernel-bits.
- `[sr61_n32] cadical smoke` (37e291a): bit=20 cand 50.12s c UNKNOWN at 1M
  conflicts. cadical 2.4x slower than kissat per conflict here; both UNKNOWN
  consistent with predictor-closure verdict.

**Queue9 partial**:
- bit=21 fill=0xff: 0 eligible
- bit=23 fill=0xff: 0 eligible
- bit=24 fill=0xff: 1 ELIGIBLE found (m=0xdc27e18c) at ~6% sweep — continuing
- bit=26 fill=0xff: queued

**Coordination**: no fleet activity since last pull. Solo pursuit of sweep
coverage continues. queue10 ready to launch when queue9 finishes.

## 07:25 EDT — Queue9 DONE, queue10 launched. Aux variants for bit=20.

**Queue9 final** (bit=21, 23, 24, 26 at fill=0xff): +2 NEW
  bit=21: 0
  bit=23: 0
  bit=24: 1 NEW (m=0xdc27e18c)
  bit=26: 1 NEW (m=0x11f9d4c7)

**Queue10 launched immediately** (bit=27, 28, 29, 30 at fill=0xff). ~48 min.

**Cross-bet shipped this pulse**:
- `[cascade_aux_encoding]` aux-expose + aux-force sr=61 CNFs for bit=20 cand
  (m=0x294e1ea8). 13472 vars / 55967 clauses each, both audit CONFIRMED.
  Adds bit=20 to the cascade_aux solver-comparison surface — Mode B's
  preprocessing-effect can be empirically tested on a high-hardlock kernel
  new to the registry.

**Session totals at 07:25**:
  Registry: 36 → **62** (+26, +72%)
  Cells exhaustively swept: 34 (queue10 in flight, 4 more cells)
  Audit failure rate: **0.00%** across 199 logged runs
  Bets touched this session: registry/sweeps, block2_wang (M16-MITM forward
    validation, backward design-gap critique), cascade_aux_encoding (audit-rot
    fix, +2 new aux CNFs), sr61_n32 (smoke tests across new cands).

## 07:35 EDT — Queue10 DONE. fill=0xff coverage 29/32 bits.

**Queue10 final** (bit=27, 28, 29, 30 at fill=0xff): +5 NEW
  bit=27: 0
  bit=28: 4 NEW (m=0xd1acca79, 0xbcc2e089, 0x3e57289c, 0x5ac592ed) ← highest yield
  bit=29: 1 NEW (m=0x17454e4b)
  bit=30: 0

**MILESTONE**: fill=0xff coverage COMPLETE for 29 of 32 bit positions.
Missing: bits 0, 6, 13 (already covered at other fills).

**Cross-bet shipped this pulse**:
- `[cascade_aux_encoding]` Mode B 2-cand consistency check: bit=20
  AND bit=28 outlier both show ~1.9× speedup at 50k, ~1× at 1M.
  Reproduces "front-loaded preprocessing" claim on fresh data.
  Memo: bets/cascade_aux_encoding/results/20260426_mode_b_2cand_consistency.md

- bit=28 m=0xd1acca79 is structurally distinctive (de58_size=2048 +
  hl_bits=15) — joins the small-image club (bit=4, bit=15, bit=19).

**Session totals at 07:35**:
  Registry: 36 → **67** (+31, +86% growth)
  Cells exhaustively swept: 38
  Total runs logged: 206 (audit failure rate 0.00%)
  Substantive shipped this turn: 40+ commits across registry, smoke
    tests, dashboard refreshes, M16-MITM forward validation, M16-MITM
    backward design-gap critique, de58 distribution analysis,
    cascade_aux Mode A/B 2-cand consistency, fingerprint refresh.
