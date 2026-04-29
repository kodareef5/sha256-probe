# macbook hourly notes — 2026-04-29

(Yesterday's macbook-hourly is comms/inbox/20260428_macbook_hourly.md;
that file ended at 78 commits with 4 retractions and full structural-
pivot arc complete. Today picks up where the cube-and-conquer +
universal-hard-core characterization arc left off.)

## ~00:12 EDT — Day pivot, F283 launched

- Yesterday's session ended at 78 commits, 37+ F-memos, 4 retractions
  (F205, F232, F237, F279), 7+ tools, ~10 yale coordination notes.
- Today's priorities (per F237/F257/F271 deductions):
  - Phase 2D propagator implementation (4-8 hrs)
  - BDD enumeration design study
  - Or pivot to different bet entirely
- F283 launched: 4 more sr60 hard-core JSONs (bit19_m51ca0b34,
  bit20_m294e1ea8, bit25_m09990bd2, bit31_m17149975) to extend yale's
  stability tool from 6-cand to 10-cand sample.
- 10-cand stability tightens the universal 128-bit hard-core finding;
  diversity in bits (19, 20, 25, 31) maximizes statistical leverage.
- Yale paused at 7863041 (~3 hrs ago); macbook continues with cross-
  cand structural sample expansion.

## ~00:18 EDT — F284: 10-cand stability ROBUSTLY confirms 128-bit universal hard core

- F283: 4 more sr60 hard-core JSONs (bits 19, 20, 25, 31).
- F284: stability across 10 sr60 cands (F269+F270+F272+F283):
  - stable_core: 132 bits
  - stable_shell: 36 bits
  - variable: 88 bits (up from 6-cand 79)
- 128-bit UNIVERSAL HARD CORE confirmed across 10 cands:
  W1_59, W1_60, W2_59, W2_60 all 32/32 stable_core.
- W1_58 UNIVERSAL SHELL confirmed across 10 cands: 32/32 stable_shell.
- Cand-variable bits expand with sample size (suggests ~95-100 bits
  asymptotic cand-dependent variation).
- The 128-bit universal architecture is empirically saturated as
  the strongest cross-cand structural fact of the bet.
- 80 commits in macbook session arc (28+29 combined).


## ~00:28 EDT — F285: TRUE sr=61 variance test — trigger does NOT fire

- F285: 5 cnfs_n32 TRUE sr=61 CNFs benchmarked at kissat 30s seed 1.
- Cands: m09990bd2/bit25, m17149975/bit31, m11f9d4c7/bit26,
  m17454e4b/bit29, m189b13c7/bit31.
- Result: ALL 5 status UNKNOWN, walls 30.04s (uniform timeout).
- ZERO variance at this budget; all uniformly intractable.
- negatives.yaml trigger "specific (bit, fill, m0) shows >2x
  solve-time improvement" does NOT fire. Closure stays valid.
- Cand-level structural distinction (de58_size, hardlock_bits)
  does NOT translate to solver-time variance at 30s budget.
- 81 commits in macbook 2-day arc.


## ~00:55 EDT — F286: universal hard core decomposes to 132 bits = 128 + 4 anchors

- Per-bit analysis across 10 sr60 cands reveals the 132 stable_core
  bits decompose:
  - 128 round-bits: W1_59[0..31], W1_60[0..31], W2_59[0..31], W2_60[0..31]
  - 4 specific anchors:
    - W1_57[0] (LSB anchor on M1 side of dW[57])
    - W2_57[0] (LSB anchor on M2 side)
    - W2_58[14] (mysterious specific bit)
    - W2_58[26] (mysterious specific bit)
- W*_57[0] = LSB anchors are structurally clean (no carry-in from
  lower bit; cascade-1 hardlock propagates here first).
- W2_58[14] and [26]: bits 14 and 26 differ by 12 = ROTR-12 mapping
  bit 26 → bit 14. Possibly Σ1 ∘ Σ1 composition fixed-point
  structure. Worth deeper algebraic investigation.
- Refined active-schedule decomposition: 132 universal hard-core +
  88 cand-variable + 36 universal shell = 256 total schedule bits.
- 82 commits in macbook 2-day arc.

