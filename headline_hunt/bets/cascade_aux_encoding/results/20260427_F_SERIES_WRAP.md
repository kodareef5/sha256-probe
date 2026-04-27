# F-series wrap: structural cascade-1 characterization (F1–F16)
**2026-04-26 21:12 EDT**

The F-series ran 14 named experiments + corrections this evening,
plus 6 C tools shipped under `encoders/`. This memo is the synthesis
for future workers.

## Headline structural facts (verified, exhaustive)

1. **Per-chamber de58_size = 1** (F12, full 2^32 enum). At fixed
   (m0, fill, bit, W57), de58 is one specific 32-bit value.

2. **de59 is cand-level invariant** (F4). Across 64 random W57s,
   exactly 1 distinct de59 per cand. Free 32-bit hint, no W57 needed.

3. **de60..de63 are universally 0 under cascade-1 multi-slot** (F14).
   Once cascade-1 holds at slots 57..k, de_k = 0 for k ≥ 60. 12.9
   billion chambers verified across 3 cands.

4. **Cascade-1 7-slot ≡ FULL SHA-256 collision** (F14 corollary).
   Under cascade-1 enforcement at slots 57..63, state at slot 64
   (final hash) FULLY MATCHES between M1 and M2.

5. **0/67 default messages have cascade-1 at slot 57+** (F15). The
   "trivial" message [m0, fill, fill, ..., fill] never extends
   cascade-1 beyond slot 56.

6. **0 cascade-1 alignments in 17.2B M[15] sweeps** (F16). Random
   single-axis perturbation of M is empirically infeasible for finding
   cascade-1-aligned messages.

## Corollaries (theoretical)

7. **sr=61 search reduces to schedule satisfiability** (F14+F15).
   "Find M ∈ {0,1}^448 (with kernel diff) such that schedule's
   dW[57..61] = cw1[57..61] simultaneously" is the actual sr=61
   collision question. 5×32 = 160-bit constraint on 448-bit free
   space. Expected solutions 2^288 in expectation.

8. **sr=63 (full SHA-256 collision via cascade) reduces to**:
   "Find M such that schedule's dW[57..63] = cw1[57..63]." 7×32 =
   224-bit constraint, 2^224 expected solutions.

## Tools shipped (all C, all fast)

| tool | purpose | speed |
|---|---|---|
| `de58_enum.c` | full 2^32 W57 → de58 image enum | 626 M/s |
| `de60_enum.c` | full 2^32 W57 → de60 (always 0!) | 350 M/s |
| `de58_lowhw_set.c` | per-HW distinct de58 values | 600 M/s |
| `cascade_max_slot_search.c` | random msg cascade-1 slot count | 3 M/s |
| `cascade_m15_sweep.c` | 2^32 M[15] sweep + slot count | 5 M/s |
| `dw_xor_kernel.c` | GF(2)-linear XOR diff schedule | instant |

All compile with `gcc -O3 -march=native`. M5 host.

## Empirical residual data (per close cand)

| cand | min HW | min HW de58 | residual structure |
|---|---:|---|---|
| msb_m189b13c7 | 2 | 0x00000108 | 1 distinct value |
| bit13_m4e560940 | 3 | 0x001020[40,4040] | 2 values (1-bit substitution) |
| bit17_m427c281d | 3 | 0x000800[24,21,22] | 6 values (2×3 grid) |
| bit18_m99bf552b | 4 | 0x02160000-class | 4 values (2×2 grid) |
| bit19_m51ca0b34 | 11 | various | 33M chambers at HW=11 |

These residuals are algebraically structured (not random). They
DO NOT directly correspond to sr=61 collision distance, but they
characterize the cascade-1 chamber image's algebraic geometry.

## Honest framing of what F-series did and didn't accomplish

**Did**:
- Characterized cascade-1 chamber dynamics exhaustively (registry-
  wide full 2^32 enumeration).
- Discovered cascade-1 7-slot = full collision (F14 — significant
  framing refinement, not novel content but newly explicit).
- Shipped 6 fast C tools for future cascade-1 work.
- Empirically confirmed kissat-class search is necessary (F16).

**Did NOT**:
- Find an sr=61 SAT or UNSAT.
- Replace kissat as the search tool.
- Probe yale's "Sigma1/Ch/T2 chart-preserving operator" track
  (different mechanism: non-cascade-1 paths).

**Mistakes corrected mid-stream**:
- F13 originally claimed "cascade-1 sr=61 closed" — overreach.
  Caught via verified sr=60 cert sanity check (it has de58 ≠ 0).
  Corrected in commit c38e980; F14 reframed the actual question.

## Cross-bet messages exchanged

- **macbook → yale (singular_chamber_rank)**:
  - 20:07: F10 finds bit=17 m=0x427c281d at min_HW=4 (commit f5e45a5)
  - 20:14: msb_m189b13c7 HW=2 registry champion (commit cbcc5d3)
  - 20:30: F13 DEFINITIVE — 67/67 cascade-1 closed (commit ca7d766)
  - 20:43: F13 correction + F14 update (commit b22ab15)

- **yale → cascade_aux**:
  - 20:40: F12 candidate transfer probe (commit 2e9cf0f). Yale GPU-
    scanned bit17 m=0x427c281d, confirmed F12 residual ≠ singular_
    chamber's off58 coord, got bit17 exact D61 HW6/tail-HW67.

## Discipline ledger

Total runs backfilled: 134 (F1 + F4b + F8 + F9, 50k–10M conflicts).
Audit failure rate: 0%. Dashboard regenerated at commit c90b4c0 +
c59025a. Symlinks at `runs/20260426_f_series_n18/` for audit-pattern
naming.

## What's next for cascade_aux

1. **kissat-driven search for cascade-1 multi-slot alignment** at sr=61
   on the structural champions (msb_m189b13c7 first). Uses standard
   tooling, not new F-series work.

2. **Yale's chart-preserving operator** if/when implemented. F-series
   tools can verify operator output efficiently.

3. **Reading writeups/sr61_impossibility_argument.md** more carefully:
   it claims 47.9% XOR conflict rate makes sr=61 statistically UNSAT.
   F14 result is consistent with this — the "many solutions in
   expectation" count assumes uniform random; the actual constraint
   structure isn't.

EVIDENCE-level (overall): VERIFIED for the structural facts; HYPOTHESIS
for the implication that sr=61 SAT search is intractable at single-
axis perturbation level (F16 confirms within explored space, but
multi-axis kissat-driven search remains open).
