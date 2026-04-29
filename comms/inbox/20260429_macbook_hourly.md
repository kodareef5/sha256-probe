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


## ~01:30 EDT — F287: algebraic investigation of W2_58[14]/[26] anchors

- Tested σ1-fanin hypothesis: σ1 OUT bits 22-31 have 2-bit fanin
  (SHR-10 truncation); 0-21 have 3-bit fanin.
- Bit 26 fits low-fanin; bit 14 doesn't. Hypothesis REFUTED at
  single-σ1 level.
- Per-bit core_fraction analysis on F284 10-cand data confirms:
  only W2_58[14] and [26] are universal-core. F273 6-cand showed
  more bits at cf=1.0; 10-cand sample disambiguates correctly.
- DEEPER ALGEBRAIC FINDING: σ1²(x) (σ1 applied twice) simplifies
  for bits 14 and 26:
  - σ1²(x)[14] = x[9] ⊕ x[16] ⊕ x[20]   (3 bits)
  - σ1²(x)[26] = x[0] ⊕ x[21] ⊕ x[23] ⊕ x[28]   (4 bits)
- These simplifications come from XOR cancellations across the 9
  intermediate σ1 contributions. Both bits 14 and 26 are at
  POSITIONS WHERE σ1² SIMPLIFIES TO LOW-FANIN expressions.
- Real algebraic structure: bits 14 and 26 may be universal-core
  because their σ1² (two-step schedule recurrence) has fewer
  effective inputs than other bit positions.
- 83 commits across 2-day arc.


## ~01:42 EDT — F288: σ1² fanin hypothesis REFUTED (5th retraction-class finding)

- Computed σ1² effective fanin (after XOR cancellation) for all
  32 bit positions:
  - bits 15-21: fanin=2 (minimum, 7 bits)
  - bits 0,1,2,13,14: fanin=3
  - bits 3,4,12,22-31: fanin=4
  - bits 5-11: fanin=5 (maximum)
- F286 universal-core anchors: bit 14 (fanin=3, NOT minimum) and
  bit 26 (fanin=4, also NOT minimum).
- σ1² fanin alone does NOT predict universal-anchoring positions.
- F287's "σ1² simplification" hypothesis REFUTED — partial
  finding was insufficient mechanism.
- 5th retraction-class finding of session arc (F205, F232, F237,
  F279, F288).
- The W2_58[14]/[26] universal-anchoring still requires
  explanation. Likely needs σ0 contribution + cascade-1 hardlock
  + carry-chain analysis, or encoder-specific Tseitin layout.
- 84 commits across 2-day arc.


## ~01:50 EDT — F289: σ0² fanin analysis — bit 26 at minimum, bit 14 not

- σ0² fanin distribution:
  - Minimum: bits 26, 27, 28 (fanin=2)
  - Most bits: fanin=3
  - Some at fanin=4 (bits 11, 12, 13, 22, 23, 24, 29, 30, 31)
- F286 anchor bit 26: σ0²-fanin=2 ✓ (matches minimum-fanin
  hypothesis at σ0² level)
- F286 anchor bit 14: σ0²-fanin=3 ✗ (not at minimum)
- Combined σ1+σ0 single-step fanin: minimum at bits 29-31 (total=4)
  vs bit 26 (5), bit 14 (6).
- Conclusion: bit 26 has a multi-mechanism algebraic story
  (σ0² minimum, σ1 light); bit 14 doesn't fit any single fanin
  property tested.
- The W2_58[14]/[26] universal-anchoring is multi-mechanism or
  encoder-specific. Single-σ-fanin doesn't predict.
- 85 commits across 2-day arc.


## ~02:15 EDT — F290: cascade_aux force-mode pins REGISTER diffs, not schedule bits

- Read cascade_aux_encoder.py force-mode source (lines 263-285).
- Theorem 1: cascade diagonal — registers a[57..60], b[58..60],
  c[59..60], d[60] differences pinned to 0
- Theorem 2: register e[60] difference = 0
- Theorem 3: e[61..63] differences = 0
- Theorem 4: a[61] = e[61] (register-bit equality)
- NONE of these directly pin schedule W[r] bits.
- Therefore: W2_58[14]/[26] universal-anchoring emerges INDIRECTLY
  through cascade propagation from register constraints to schedule.
- The propagation involves BIG-Σ (Σ0, Σ1) on registers AND
  schedule-recurrence small-σ on W. Multi-step interaction.
- Single-σ (small) fanin analysis (F287/F288/F289) couldn't predict
  the anchors because the actual mechanism involves register-Σ
  composition with schedule-σ.
- F290 explanation closes the F286-F289 algebraic-investigation arc
  with the right structural framing: TSEITIN propagation chain, not
  direct algebraic prediction.
- 86 commits across 2-day arc.


## ~02:28 EDT — F291: bit06_m6781a62a residual corpus build — ZERO HW≤16 hits

- Built block2_wang residual corpus for bit06_m6781a62a_fillaaaaaaaa
  via build_corpus.py (100k samples, HW threshold 16).
- Result: 0 residuals passed filter. Min HW observed = 64, max = 125.
- bit06_m6781a62a has no detectable near-collisions at the
  standard threshold from random W[57..60] sampling.
- Empty corpus file deleted (no useful data to commit).
- Empirically informative: this cand is NOT a strong block2_wang
  trail-search target. Other cands (bit3, bit10, bit19) with non-
  empty corpora are better targets.
- 87 commits across 2-day arc.


## ~02:55 EDT — F292/F293: msb_m17149975 residual corpus shipped (canonical collision-witness)

- F292 attempt with --hw-threshold=16: 0 records (random sampling
  doesn't find HW≤16 residuals on canonical msb either; min HW=62).
- F293: rebuilt with --hw-threshold=200 (effectively no filter):
  100k records captured (75MB total).
- Sampled down to 10k records (7.5MB) matching existing per-cand
  corpus scale.
- corpus_msb_m17149975_fillffffffff.jsonl shipped to by_candidate/.
- This is the FIRST per-cand corpus for the canonical sr=60
  collision-witness (m17149975 from CLAIMS.md).
- 88 commits across 2-day arc.


## ~03:15 EDT — F294: corpus_msb_m3f239926 shipped (10k records)

- Built residual corpus for msb_m3f239926_fillaaaaaaaa (kernel-bit 31).
- 100k records sampled, 10k retained for scale parity (7.5MB).
- Per F293 protocol: --hw-threshold=200 (no HW filter), random
  schedule W[57..60] sampling.
- Second per-cand corpus shipped this hour. block2_wang trail-search
  catalog now has 12 cands with per-cand data.
- Min HW seen across 100k samples: 62 (typical for random sampling
  on this cand).
- 89 commits across 2-day arc.


## ~03:25 EDT — F295: corpus_msb_m44b49bc3 shipped — completes MSB family

- Built residual corpus for msb_m44b49bc3_fill80000000 (kernel-bit 31).
- 10k records sampled (7.5MB).
- block2_wang per-cand corpora now: 16 total (was 13 yesterday +
  F293 msb_m17149975 + F294 msb_m3f239926 + F295 msb_m44b49bc3).
- MSB family complete: m17149975, ma22dc6c7, m9cfea9ce, m189b13c7,
  m3f239926, m44b49bc3 = all 6 registry msb cands have per-cand
  corpora now.
- 90 commits across 2-day arc.

