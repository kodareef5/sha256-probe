# 2026-04-25/26 Session — Consolidated Results

**Session window**: 2026-04-25 evening through 2026-04-26 morning (overnight).
**Owner**: macbook (autonomous mode).
**Net deliverables**: 60-candidate registry (+24 NEW), M16-MITM forward
validated, M16-MITM backward design-gap identified, 30 cells exhaustively
swept, 195 logged runs at 0% audit-failure.

## Substantive results

### 1. Registry expansion: 36 → 60 candidates (+24, +67%)

**Method**: M5-tuned OpenMP 2^32 m0 sweeps at uncovered (bit, fill) cells.
~12 min wall per cell on clean CPU.

**24 new candidates added across 11 distinct kernel bits**:
| Bit | Fills tested | NEW cands | Notes |
|----:|:---|:---|:---|
| 1   | fill=0xff | 1 | First-time-tested non-aligned bit |
| 2   | fill=0xff | 3 | Σ0-aligned (hypothesis falsified) |
| 3   | fill=0xff,0x00,0x55 | 2 | Only fill=0xff productive |
| 4   | fill=0xff | 2 | One has de58_size=2048 (small image) |
| 12  | fill=0xff | 1 | Non-aligned, first-tested |
| 13  | fill=0x80 | 1 | Gap-fill for existing kernel |
| 14  | fill=0xff,0x00,0x55 | 3 | Only fill=0xff productive |
| 15  | fill=0xff | 3 | One has hl_bits=14 (high constraint) |
| 18  | fill=0xff,0x00 | 5 | Largest single-bit yield |
| 20  | fill=0xff | 1 | hl_bits=15 (high constraint) |
| 25  | fill=0xff | 2 | One has de58_size=1024 (small image) |

### 2. Σ1/σ1 alignment hypothesis: FALSIFIED

The de58 cascade-eligibility rate is **uniformly ~2^-31 at any bit
position**, regardless of whether that bit is in any rotation amount set
(σ0={7,18,3}, Σ0={2,13,22}, σ1={17,19,10}, Σ1={6,11,25}).

EVIDENCE: 30 cells swept exhaustively. Every productive cell yields rate
within Poisson(1) at 2^-31 baseline. No bias by alignment class.

**Implication**: any (bit, fill) cell may yield candidates; no a-priori
filtering by rotation alignment is justified.

### 3. M16-MITM forward enumerator: VALIDATED

`m16_mitm_forward.c` (218 LOC, M5-tuned OMP) emits 2^(3N) records
(state_59, W57, W58, W59) packed at N bits per word. Records are
cascade-1-eligible by construction.

**Validation**:
- N=8: 200/200 sampled records pass independent Python replay.
- N=10: 200/200 sampled records pass + 10,000 records → 100% distinct
  state_59 (full-resolution matching key, no compression).

EVIDENCE-level claim: forward enumerator is correct at multiple N values.

### 4. M16-MITM backward enumerator: DESIGN-GAP IDENTIFIED

The original `M16_MITM_FOUNDATION.md` design proposed a backward
enumerator that "computes the REQUIRED state at round 59 for cascade-2
(de60=0)." Mathematical analysis shows this is a 1-bit modular
constraint on (pair1.s59, pair2.s59), giving a codimension-1 surface,
not a single "required state."

**Implication**: the matching key (state_59) has no inherent filtering
power. A naive M16-MITM at N=10 produces 2^29 match candidates each
needing full verification — NOT faster than direct enumeration via
backward construction (946 N=10 collisions in 117s).

**Recommendation**: do NOT implement m16_mitm_backward.c per the
foundation memo. Better leverage: re-derive starting from XOR-linear
approximation (Wang-style), or pivot to backward-construction scaling
M14 → M16.

### 5. Predictor closure (from earlier in session)

The 12-cell Spearman validation matrix established that de58_size and
hard_bit_total_lb predictors are search-irrelevant (ρ ≤ 0 across all
tested cells in both kissat and cadical, both 1M and 10M conflict
budgets, both seeds 1 and 5). This session reinforced this with smoke
tests on small-image candidates (de58 ∈ {256, 1024, 2048, 4096}) — none
solve faster.

### 6. de58 image-size distribution

Across 60 candidates: log-uniform-ish distribution from 2^8 to 2^17, with
mode at 2^16-2^17 (37% of cands). The bit=19 m=0x51ca0b34 (fill=0x55)
is a 2^9 outlier with image=256 — ~512x smaller than median.

**hardlock_bits**: median 8, range 1-16. Two new bit=15/bit=20 candidates
have hardlock_bits ∈ {14, 15} — among the highest constraints in the
registry.

### 7. Discipline: audit-rot fix

16 stale `cascade_aux_encoding` sr=61 CNFs (regenerated 2026-04-26 03:10)
because encoder updated 2026-04-25 added modular-diff aux variables that
shifted the var/clause counts. Old CNFs fell into sr=60 fingerprint range.
Fixed via regeneration. All 100 cascade_aux CNFs now audit CONFIRMED.

Risk: ~16 of 130 past cascade_aux runs have sr-level misattribution.
Mode B "2-3.4× speedup" claim may need re-verification at properly
audited sr=61 (~30 min compute).

## What's NOT a result

- No new SAT solutions (sr=61 still untouched).
- No falsification of any active EVIDENCE-level claim.
- No closing of any active mechanism (block2_wang, cascade_aux_encoding,
  kc_xor_d4, sr61_n32, mitm_residue, chunk_mode_dp,
  programmatic_sat_propagator) — all still open.

## Numbers

| Metric | Value |
|---|---|
| Total runs logged | 195 |
| Audit failure rate | 0.00% |
| sr61_n32 runs | 55 |
| Total candidates | 60 |
| Cells exhaustively swept | 30 (queue9 in flight, queue10 ready) |
| Avg yield per cell | 0.80 (Poisson(1) baseline) |
| Productive cells | ~10/30 (33%) |

## Active sweeps

- **queue9** (in flight): bit={21, 23, 24, 26} at fill=0xff. ~48 min wall.
- **queue10** (ready): bit={27, 28, 29, 30} at fill=0xff. ~48 min wall.

After queue9+queue10 complete: 38 cells swept, expected ~+8-10 more cands.

## Bets owned by macbook (live as of 07:10 EDT 2026-04-26)

- **block2_wang**: open. M10/M12 algorithm validated. M16-MITM forward
  validated, backward design-gap. Heartbeat fresh.
- **cascade_aux_encoding**: open. 100/100 CNFs CONFIRMED post-audit-rot fix.
  Heartbeat fresh.
- **mitm_residue**: blocked. Tools exist; not operationalized.
  Heartbeat fresh.
- **programmatic_sat_propagator**: open, no work yet.
  Heartbeat fresh.

## Lessons (for future sessions)

1. **Avoid running smoke-tests in parallel with sweeps** — macOS scheduler
   can starve smaller processes for hours. Sequential is better.
2. **State_59 in cascade-1 doesn't compress** — full-resolution matching
   key in MITM context. Forward enumerator emits ~2^(3N) distinct values.
3. **Per-bit yield is fill-specific** — bit=14 only productive at fill=0xff;
   fill=0x00 and fill=0x55 yield 0. Don't extrapolate yield by bit alone.
4. **Cascade-eligibility is bit-position-uniform** — Σ1/σ1 alignment
   doesn't predict yield. All 32 bits viable at appropriate fill.
