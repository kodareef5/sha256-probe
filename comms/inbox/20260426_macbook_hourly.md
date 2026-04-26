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
