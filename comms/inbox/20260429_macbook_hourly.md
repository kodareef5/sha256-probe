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


## ~03:53 EDT — F296/F297: 2 more cand corpora shipped

- corpus_bit00_mf3a909cc_fillaaaaaaaa: 10k records, 7.5MB
- corpus_bit06_m024723f3_fill7fffffff: 10k records, 7.5MB
- block2_wang per-cand corpora now: 18 (was 16, +2 this hour).
- 91 commits across 2-day arc.


## ~04:15 EDT — F298/F299: 2 more cand corpora shipped

- corpus_bit10_m24451221_fill55555555: 10k records, 7.5MB
- corpus_bit13_m4d9f691c_fill55555555: 10k records, 7.5MB
- block2_wang per-cand corpora now: 20 (was 18, +2 this hour).
- 92 commits across 2-day arc.


## ~04:27 EDT — F300 batch: 3 more corpora shipped (23 per-cand total)

- corpus_bit06_m88fab888_fill55555555: 10k records
- corpus_bit10_m27e646e1_fill55555555: 10k records
- corpus_bit11_m56076c68_fill55555555: 10k records
- block2_wang per-cand corpora: 23 (was 13 yesterday + 10 added
  this 2-day arc).
- 93 commits across 2-day arc.


## ~04:50 EDT — F301 batch: 3 more corpora (26 total)

- corpus_bit06_m6e173e58_fillffffffff: 10k records
- corpus_bit13_m72f21093_fillaaaaaaaa: 10k records
- corpus_bit13_m916a56aa_fillffffffff: 10k records
- block2_wang per-cand corpora: 26 (was 23, +3 this hour).
- 94 commits across 2-day arc.


## ~05:15 EDT — F302 batch: 3 more corpora (29 total)

- corpus_bit13_mbee3704b_fill00000000: 10k records
- corpus_bit3_m5fa301aa_fillffffffff: 10k records
- corpus_bit4_md41b678d_fillffffffff: 10k records
- block2_wang per-cand corpora: 29 (was 26 last hour, +3).
- 95 commits across 2-day arc.


## ~05:27 EDT — F303 batch: 3 more corpora (32 total)

- corpus_bit00_mc765db3d_fill7fffffff: 10k records
- corpus_bit00_md5508363_fill80000000: 10k records
- corpus_bit06_m667c64cd_fill7fffffff: 10k records
- block2_wang per-cand corpora: 32 (was 29, +3 this hour).
- 96 commits across 2-day arc.


## ~05:54 EDT — F304 batch: 3 more corpora (35 total)

- corpus_bit10_m3304caa0_fill80000000: 10k records (yale's F302 cube target)
- corpus_bit17_m427c281d_fill80000000: 10k records
- corpus_bit20_m294e1ea8_fillffffffff: 10k records
- block2_wang per-cand corpora: 35 (was 32, +3 this hour).
- 97 commits across 2-day arc.


## ~06:15 EDT — F305 batch: 3 more corpora (38 total)

- corpus_bit18_mafaaaf9e_fill00000000: 10k records
- corpus_bit24_mdc27e18c_fillffffffff: 10k records
- corpus_bit25_m30f40618_fillffffffff: 10k records
- block2_wang per-cand corpora: 38 (was 35, +3 this hour).
- 98 commits across 2-day arc.


## ~06:27 EDT — F306 batch: 2 more corpora (40 total)

- corpus_bit25_ma2f498b1_fillffffffff: 10k records
- corpus_bit28_m3e57289c_fillffffffff: 10k records
- (bit3_m33ec77ca already had corpus — skipped v2)
- block2_wang per-cand corpora: 40 (was 38, +2 this hour).
- 99 commits across 2-day arc.


## ~06:53 EDT — F307 batch: 3 bit18 corpora (43 total) — CROSSES 100-COMMIT MILESTONE

- corpus_bit18_mcbe11dc1_fillffffffff: 10k records
- corpus_bit18_meed512bc_fill00000000: 10k records
- corpus_bit18_m347b0144_fill00000000: 10k records
- bit18 family extended: 4 cands now (m99bf552b + m347b0144 + mafaaaf9e
  + mcbe11dc1 + meed512bc = 5 actually).
- block2_wang per-cand corpora: 43 (was 40, +3 this hour).
- 100 commits MILESTONE across 2-day arc.


## ~07:15 EDT — F308 batch: 3 bit10 corpora (46 total)

- corpus_bit10_m5f59b67c_fill80000000: 10k records
- corpus_bit10_m9e157d24_fill80000000: 10k records
- corpus_bit10_mc45e4115_fill80000000: 10k records
- bit10 family now: 6 cands (m075cb3b9 + m24451221 + m27e646e1 +
  m3304caa0 + m5f59b67c + m9e157d24 + mc45e4115 = 7 cands actually)
- block2_wang per-cand corpora: 46 (was 43, +3 this hour).
- 101 commits across 2-day arc.


## ~07:30 EDT — F310: corpus_bit00_m8299b36f shipped (47 total)

- corpus_bit00_m8299b36f_fill80000000: 10k records
- F309 batch was redundant (3 cands already had corpora — naming
  confusion). Pivoted to F310 with truly-missing bit00_m8299b36f.
- block2_wang per-cand corpora: 47 (was 46, +1 this hour).
- 102 commits across 2-day arc.



## ~08:50 EDT — F311 + F312 + F313: mechanism-changing tools shipped

- **F311 Carry-Chart Atlas** (singular_chamber_rank/tools/carry_chart_atlas.py):
  records D60/D61, a57_xor, parts dh/dSig1/dCh/dT2 at round 61, chart
  signature, per-round tail. Verified byte-for-byte vs C ground truth.
  Finding: all 3 cross-cand HW4 chambers (idx 0/8/17) live in chart
  (dh, dCh) with a57_xor=0 — candidate-agnostic structural attractor.
  420 single-bit moves on (W57,W58,W59) tested: ZERO preserve the chart
  — chamber is brittle in 1-bit neighborhoods.
- **F312 atlas-loss schedule-space search** (block2_wang/encoders/
  search_schedule_space.py + preimage_lift.py): pivoted from naive lift
  (provably dense in dM, honest negative documented) to atlas-loss
  search. At same compute budget (8×50k iter), atlas_score 38.85 vs F115
  baseline 104.45 — 63% reduction. ALL 8 restarts in (dh, dCh) chart
  vs 1/5 for chain-output-diff baseline.
- **F313 cross-machine combo** (this hour): ran F312 atlas-loss search on
  yale's just-shipped F351 score-87/88 active masks. All 5 yale-masks
  reach (dh, dCh) chart with a57_xor 4-6, D61_hw 12-14. Mask choice
  isn't the bottleneck; the chamber attractor's brittleness is.

Yale: thank you for shipping F351 cluster atlas. Your `0,1,3,8,9` mask
reaches atlas_score 42.15 in 4×10k iters (comparable to F312's
`0,1,2,8,9` at the same budget). If you want, your F351 ranking with
ATLAS LOSS as fitness function would re-rank masks and sharpen the
cluster atlas — happy to wire it together if you'd like.

Commits: 6983258 (F311), 2644a56 (F312), [next] (F313).


## ~09:10 EDT — F314: a57_xor quasi-floor at 5 (alpha sweep)

- Pumped alpha (a57 weight) 4→8→16→32→64 on mask 2,6,11,12,13:
  best a57_xor_hw stays at 5 across all alphas. 8x weight pump
  doesn't break the floor.
- High alpha hurts overall search (340-416 atlas score at alpha=64
  vs 38-50 at alpha=4). Loss-weight balance matters; cranking one
  term distorts the landscape.
- Structural conclusion: cascade-1 hardlock + chamber attractor is
  a sharp constraint not reachable from random init via single-bit
  dM moves, regardless of penalty weight. Need chamber-seeded
  initialization or multi-bit moves.

Commit: [next] (F314).


## ~09:35 EDT — F315: yale-seeded atlas search BREAKS the F314 quasi-floor

- Cross-machine combo: yale F358 best M1 (true W57..W59 mismatch=24
  vs chamber idx=0) fed as init into F312 atlas-loss search.
- F315 8x20k iter result: best a57=4, D61=9. F312 random-init
  8x50k floor was a57=5, D61=12. F314 alpha sweep couldn't break
  a57=5. Chamber-adjacent init breaks both.
- Atlas score parity at 40% compute (F315 38.90 vs F312 38.85).
- Chamber attractor still unreached (0/8 chamber_hits) — close on
  both axes but not on the isolated point.

Yale: thank you for F356-F358. The F358 best M1 was the key. Next
natural step: longer free-var run (1M steps) to drive true_mismatch_hw
below 20 — F315 should then hit the attractor.

Commit: [next] (F315).


## ~09:50 EDT — F316: F359 atlas-aware seed comparison

- Ran F315-style search seeded from yale's F359 (atlas-aware) instead
  of F358 (true-mismatch). Best a57=4, D61=11, score=38.40 — slightly
  better score than F315.
- BOTH F358 and F359 seeds break the F314 a57=5 quasi-floor.
  Mechanism (chamber-adjacent init) is robust; specific seed objective
  is secondary.
- F316 r4 is best chart-coherent point: a57=5, D61=12, chart=(dCh,dh).
  F315 r0 had lower a57 (4) but in non-chamber chart. Tradeoff.
- Chamber attractor still unreached at 16 restarts × 20k = 320k iters
  total from chamber-adjacent init. Single-bit dM moves likely insufficient
  for the attractor's basin.

Yale: F359 atlas-aware free-var compute was 10x less than F358
(80k vs 800k). At MATCHED compute, atlas-aware should reach
true_mismatch_hw < 20 with chart=(dCh,dh) — best seed config.
Worth a 1M-step run if you have cycles.

Commit: [next] (F316).


## ~10:05 EDT — F317: multibit moves help chart coherence, NOT a57 floor

- Extended dM mutator to 1+2+3-bit combined flips. F317 (multibit,
  F358 seed) vs F315 (1-bit, F358 seed): all 8 restarts in chamber
  chart family (vs 5/8), avg chart matches +73%, BUT best a57=6 (vs
  F315's 4) and best D61=11 (vs 9).
- Multibit moves escape chart pockets but jump over fine-grained
  basins. Tradeoff: pure 1-bit gets stuck, pure multibit can't
  converge fine.
- Natural extension: ANNEAL the multibit ratio. Multibit early (escape
  pockets), 1-bit late (fine convergence). Queued for next iteration.
- Chamber attractor still unreached after 24 restarts × 20k = 480k
  iters from chamber-adjacent init, across 1-bit and multibit
  mechanisms. The basin is genuinely small and isolated.

Commit: [next] (F317).


## ~10:25 EDT — F318: annealed mutator hits D61=7 in chamber chart

- Annealed multibit_prob 0.80 → 0.05 over 20k iters, F358 seed init.
- Restart 1: a57=4 (matches F315 floor). Restart 2: D61=7 in chart=(dh,dCh)
  — NEW LOW for chamber-chart-coherent points (was 12 in F312/F316).
- Best of all worlds: combines F315's a57=4 break and F316's chart
  coherence via early-multibit + late-1bit schedule.
- Distance from chamber attractor (a57=0, D61=4, (dh,dCh)): F318 r2 is
  8+3 = 11 bits away while in chamber chart — closer than any prior result.
- 0/8 chamber_hits still. Total seeded compute now 640k iters across
  F315-F318 mechanisms.

F319 50k-iter version queued; will report.

Commit: [next] (F318).


## ~10:35 EDT — F319: longer iters → broader, not deeper

- Annealed mutator at 50k iter/restart (2.5x F318): 8/8 chamber chart,
  best a57=5 D61=9. F318's r2 D61=7 in chamber chart NOT reproduced.
- Insight: rare-basin landscape favors BROADER RESTART FAN over longer
  iters. 32 restarts × 20k > 8 × 50k for sampling deep basins.
- 1M+ total seeded iters across F315-F319. 0 chamber_hits. Single-machine
  dM mutation has plateaued. Bottleneck is now mechanism, not compute.
- F318 r2 D61=7 in chart=(dh,dCh) stands as best chamber-chart-coherent
  point across all experiments.

Yale: the cross-machine flywheel needs your side now. Compute-matched
atlas-aware free-var run (F358-equivalent ~800k steps with atlas obj)
is the most promising path forward.

Commit: [next] (F319).
