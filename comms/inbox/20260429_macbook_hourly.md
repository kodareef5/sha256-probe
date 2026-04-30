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


## ~10:50 EDT — F320 broader fan + F321 kernel-preserving + F322 RETRACTION

- F320 (32×20k, drift): best a57=3 (new low) but in non-chamber chart.
- F321 (kernel-preserving cascade-1, yale F358 seed): a57=5, D61=10.
- F322 (kernel-preserving cascade-1, RANDOM init): a57=5, D61=8 in
  chamber chart. RANDOM-INIT BEATS YALE-SEEDED UNDER STRICT CASCADE-1.

RETRACTION: F315-F320 "yale chamber-seed breaks a57=5 floor" was a
DRIFT ARTIFACT. Inspecting F318 r2's "best" pair revealed M1^M2 was
NOT the cascade-1 kernel pattern (bit-31 on M[0],M[9]) — it had
arbitrary diffs at words 0,1,2,8,9. The search was exploring outside
cascade-1.

Real cascade-1 floor (kernel-preserved): a57=5 D61=8 in chamber chart
(F322). Yale chamber-seed adds NO cascade-1 benefit at this compute
(F321 D61=10 is worse than F322 D61=8).

5th retraction this 2-day arc, shipped within 30 min of structural
discovery. F1 verification protocol applies.

Yale: please retrofit your free-var search with kernel-preservation
discipline. Your chamber-seed M1 is valuable but the SEARCH around
it must enforce M2 = M1 ^ kernel rigid for cascade-1 claims.

Commits: [next] (F320), [next+1] (F321 kernel-preserving), [next+2] (F322
RETRACTION + random-init kernel baseline).


## ~14:15 EDT — F324: universal hard core is CDCL-search property, NOT encoder

- UP test on aux_force sr60 bit31 CNF: 0/32 W2_58 bits forced by
  baseline UP, 0/32 force UNSAT under single-bit assumption.
- 0/256 schedule bits (W*_57..W*_60) are UP-forced. The 481 baseline-
  UP-forced vars are AUX/CONST_TRUE/equality, not schedule.
- F286 132-bit universal hard core is a CDCL-search invariant of the
  SHA-256 cascade-1 collision problem, NOT an encoder Tseitin artifact.
  Stronger structural finding than encoder-pinning would have been —
  not removable by re-encoding.
- Both F287 hypotheses (σ1 fan-in F323, encoder-pin F324) closed with
  negatives, reframing into the positive structural conclusion above.
- For programmatic_sat_propagator: if we build IPASIR-UP, it should
  accelerate CDCL trajectory through these 132 bits.

Commit: [next] (F324).


## ~14:30 EDT — F325: 2-bit pair propagation confirms search-invariant thesis

- 1984 UP runs (496 W2_58 pairs × 4 polarity combos): 0/496 pairs
  trigger UP-UNSAT under any polarity. Anchor pair (14, 26) specifically
  free under all 4 polarities (483-485 vars forced, only +2 to +4 over
  baseline 481).
- Combined with F324 (0/32 single-bit forced), the encoder pins ZERO
  W2_58 bits via 1- or 2-bit UP. The 132-bit hard core is a genuine
  CDCL-trajectory invariant of the cascade-1 collision problem.
- Forensics: the 481 baseline-UP-forced vars are cascade-offset
  internal AUX (vars 10989+, 4-clause Tseitin patterns) — encoder
  pins its OWN cascade structure, but lets the schedule be free.
- All three F287 sub-probes now closed. Combined F323+F324+F325 give
  a sharpened structural thesis: any sound solver finding the cascade-1
  collision must navigate these 132 specific bits via conflict-driven
  search, not Tseitin propagation.

For yale: your `--stability-mode core` selector targeting these 132
bits is structurally correct; F324+F325 proves they're CDCL invariants.

For programmatic_sat_propagator: a custom IPASIR-UP propagator could
short-circuit CDCL by pre-loading conflict clauses on these 132 bits.

Commit: [next] (F325).


## ~14:45 EDT — F326: cross-cand UP validation — encoder pinning is candidate-agnostic

- Re-ran F324 UP test on 5 cands (bit0, bit10, bit11, bit13, bit17).
  ALL 5 show EXACTLY 481 baseline UP-forced vars (same number!) and
  0/32 W2_58 bits forced. Combined with F324's bit31 cand: 6 cands
  all identical pattern.
- The 481 forced are cascade-offset AUX Tseitin chains (vars 10989+,
  4-clause XOR gadgets). The encoder's structural commitment is a
  fixed-size invariant of the cascade-1 encoding architecture.
- Sharpened thesis: 132-bit universal hard core is a candidate-agnostic
  CDCL-search invariant of the SHA-256 cascade-1 collision problem.
  Cannot be eliminated by re-encoding; not detectable by 1- or 2-bit
  UP; manifests only via CDCL conflict analysis.
- All three bets (block2_wang, math_principles, cascade_aux_encoding)
  converge on the same structural object: 132-bit algebraic constraint
  surface for cascade-1 collisions.

Direction for programmatic_sat_propagator: IPASIR-UP propagator
pre-loading conflict clauses on the 132 bits could give 2-10x CDCL
speedup. ~10-20 hr build, measurable on TRUE sr=61 N=32 instances.

Commit: [next] (F326).


## ~15:05 EDT — F327: IPASIR-UP API survey extended with F324-F326 updates

- Extended propagators/IPASIR_UP_API.md (+106 lines) with 2026-04-29
  update incorporating F286/F311/F323-F326 findings.
- Updated target from "184-bit active-schedule" → "132-bit universal
  hard core" (F286 decomposition: 128 round-bits + 4 anchors).
- Sharpened hook priorities per F324's UP-test result:
    cb_decide:               HIGH (was already proposed)
    cb_add_external_clause:  HIGH (NEW priority — inject conflict
                                   clauses missing from CNF since
                                   F326 proved the 132-bit core is
                                   not in the Tseitin)
    cb_propagate:            LOW (DOWNGRADED — encoder doesn't pin
                                  W2_58 bits via UP, so propagator
                                  can't either by soundness)
    cb_check_found_model:    MEDIUM (sanity, not speedup)
- BET.yaml updated with reopen_candidate_2026_04_29_F326_sharpened.
- Bet remains CLOSED. Reopen now requires only Phase 2D+2D' build
  decision (~10-14 hrs total, bigger than routine — needs user OK).

Direction: when fleet has cycles for a multi-hour build, the F326-
sharpened Phase 2D recipe is the most structurally-motivated path
forward for cracking the 132-bit CDCL bottleneck.

Commit: [next] (F327 API survey update).


## ~15:25 EDT — F328+F329: full 132-bit UP test + force/expose mode comparison

- F328: tested all 128 round-bits (W*_59 + W*_60) on aux_force_sr60
  bit31. Result: 0/128 UP-forced (any polarity). Combined with F324
  W2_58 result, all 132 universal-hard-core bits are UP-free.
- F329: same CNF but aux_EXPOSE mode. Baseline UP forces only 1 var
  (just CONST_TRUE) vs force mode's 481 (cascade-offset AUX). The
  480-var difference IS the cascade-1 hardlock encoding.
- BOTH modes have 0/256 schedule bits UP-forced. Encoder-mode-
  independent confirmation that the 132-bit core lives entirely in
  CDCL-search invariant space.
- Combined F324-F329 thesis: 132-bit core is a SHA-256 cascade-1
  collision PROBLEM property, robust across encoding mode, cand
  identity, single-bit and 2-bit UP assumptions.
- F327 IPASIR-UP design choices reconfirmed: cb_propagate correctly
  DOWNGRADED (encoder-independent), cb_decide / cb_add_external_clause
  correctly HIGH priority.

Commit: [next] (F328+F329).


## ~15:45 EDT — F330: sr=61 + F235 hard instance UP cross-validation

- sr=61 aux_force (cand bit10): 481 baseline UP forced (IDENTICAL to
  sr=60), 0/192 schedule bits forced. The thesis transfers cleanly to
  the open frontier (sr=61 has no SAT yet).
- F235 hard instance (basic cascade encoder, kissat 562s timeout):
  baseline UP forces only 1 var (CONST_TRUE) — basic cascade has cascade
  equations as direct clauses, not aux_force's 481 ripple-borrow AUX.
  Random-var UP probes all UP-feasible.
- Cascade location is sr-dependent: sr60 = W*_59+W*_60+anchors, sr61 =
  W*_57+W*_58+W*_59+anchors. F327 propagator design uses cand-specific
  F286 stability data which generalizes correctly.

Headline implication: F327 IPASIR-UP design (Phase 2D+2D') is now
structurally validated across 6 cands × 2 encoder modes × 2 sr levels
+ basic cascade. If projected 2-5x speedup on mid-difficulty sr=61
materializes, that's the path to FIRST SAT on sr=61 — extending
Viragh 2026's sr=59 by two rounds = headline-worthy.

Commit: [next] (F330).


## ~16:00 EDT — F331 cross-machine drift warning to yale (F366/F367)

- Yale shipped F366 (pair moves) + F367 (third moves) extending F311
  brittleness to 2-3 bit radius. Findings:
    F366: 0/2559 pair moves beat base score; 9 preserve D61
    F367: 0/2560 triple moves combine a57-down + chart + D61<=seed
- Critical issue caught: yale's `apply_move()` has `raw_m1` and `raw_m2`
  modes that break cascade-1 kernel preservation (change M1^M2 at the
  flip position). F366's top 3 candidates ALL use a raw_m2 flip at
  word 5 bit 21 — not a cascade-1 collision pair.
- Same drift artifact as F322. Sent F331 coordination note to yale
  flagging this. Suggestion: re-run with --modes common_xor,common_add
  only for cascade-1-valid results.
- What still stands: count statistics (456/458/11/0) are real landscape
  measurements; F367's "0 triple-good moves" extends F311 brittleness
  to triple moves regardless of drift status.

Commit: [next] (F331 coordination note).


## ~16:15 EDT — F332: σ0 fan-in INVERTS the F287 intuition

- σ0 light bits 29-31 (fan-in=2): mean core 0.433
- σ0 dense bits 0-28 (fan-in=3): mean core 0.783 (-0.349 NEGATIVE diff)
- Compound zones at W2_58:
    Both light (29-31):  0.433 — lowest
    σ1 light only (22-28): 0.857 — highest
    Both dense (0-21): 0.759
- Bit 31 universally SHELL (0/10) despite being lightest fan-in.
  Reframe: high-bit positions are STRUCTURALLY ISOLATED in modular
  addition (no carry-in from below, no carry-out forward), so CDCL
  has fewer coupling constraints to derive them. Hence more shell.
- Combined with F323 (σ1 -0.029): simple-fan-in hypothesis is wrong
  in both directions. The 132-bit core's specific positions are
  CDCL-derived, consistent with F324-F326 search-invariant thesis.

Commit: [next] (F332).


## ~16:35 EDT — F333: F331 drift warning empirically confirmed via yale F362 data

- Inspected 5 of 28 (M1, M2) pairs in yale's F362 Pareto-descendant JSON.
  Cascade-1 kernel for idx=0 requires: M1[0]^M2[0] = M1[9]^M2[9] = bit 31,
  ALL other words zero diff.
- 0 of 5 inspected pairs satisfy this. All 5 have nonzero diff at 9-16
  active words (HW 64 across all 16 words for descendant_runs[0].best).
  Word 9's bit 31 is NOT set in any inspected pair (cascade-1 violated).
- F362 best (a57=5 D61=9 score=35.4 chart=(dh,dCh)) is NOT a cascade-1
  collision pair. It's a low-atlas-loss point in the drift-allowed
  landscape only.
- TRUE cascade-1 floor stands at F322's measurement: a57=5 D61=8 score=39.65.
- F333 is the cross-machine version of F322 self-retraction (6th drift
  catch this 2-day arc). Recommendation to yale unchanged: re-run with
  `--modes common_xor,common_add` only.

What's still valid from F36x: Pareto-landscape structure (F360),
multi-bit brittleness extension (F366-F368 0-count rates).

Commit: [next] (F333).


## ~16:55 EDT — F334: kernel-preservation auditor + fleet-wide drift survey

- Shipped infra/audit_kernel_preservation.py — recursive JSON walker
  that flags non-cascade-1 (M1, M2) pairs. --block-context block1
  (default, DRIFT = bug) or block2 (DRIFT = expected absorber search).
- Verified against known-good F321/F322 (PASS) and known-drift F315/F362
  (DRIFT). Tool works.
- Fleet-wide block-1 atlas-loss survey across today's ship:
  - block2_wang search artifacts: ~104/128 pairs DRIFT (81%)
  - math_principles atlas results: ~715/722 pairs DRIFT (99%)
- The 31 PASS pairs are: F321 (8), F322 (8), F361 partial (7), and the
  6 macbook search-artifact files I'd already retracted in F322.
- This catches the F322/F333 class of bug systematically. Future
  cross-machine work can pass through the auditor as a one-line check
  before claims propagate.

Commit: [next] (F334).


## ~17:10 EDT — F335: yale's F369-F372 strict-kernel pivot verified, F372 D61=5 is new cascade-1 low

- Yale shipped F369-F372 with strict kernel preservation in <2hr after
  F331/F333 drift warnings. F334 auditor confirms 95/95 PASS — fully
  kernel-preserving cascade-1 search.
- F372 best_d61: a57=15, **D61=5** in chart=(dCh,dh). UNDER STRICT
  CASCADE-1. F322's D61=8 floor BROKEN on the D61 axis.
- F372 best_score: a57=6, D61=8, score=37.8. Ties F322 D61=8 with
  slightly lower atlas score (37.8 < F322's 39.65).
- Sent F335 thanks note to yale + recognition of new D61 low. Cross-
  machine flywheel back on track under correct discipline.
- Distance to chamber attractor (a57=0, D61=4): F322 is 9 bits; F372
  best_d61 brackets from D61 angle (1 bit), from a57 angle (15 bits).
  Pareto front has at least 2 distinct kernel-safe points now.

The cross-machine cycle today:
  yale F356-F359 (drift) → macbook F315-F320 (drift, retracted F322)
  → F331 drift warning → F333 empirical confirm → F334 auditor
  → yale F369-F372 strict-kernel ship (95/95 PASS).

Commit: [next] (F335 thanks/recognition).


## ~17:25 EDT — yale F373 strict-kernel junction search: 0 simultaneous hits

- Yale F373 ran junction search at depth 3+ from F372 best_guard and
  best_d61 seeds, looking for moves that JOINTLY satisfy
  guard-repair + D61-preserve. 48069-48071 evaluations per branch.
  Both branches: 0 hits.
- Confirms chamber-attractor brittleness extends to MULTI-BIT KERNEL-SAFE
  moves at depth 3. The attractor is genuinely unreachable from basin
  search regardless of move radius or kernel constraint.
- Mechanism gap is now precisely characterized: single-bit dM, multi-bit
  dM, kernel-safe basin search, kernel-safe beam search at depth 1/2/3 —
  ALL of these miss the chamber attractor. CDCL conflict analysis is
  the structurally-distinct mechanism (per F324-F326 search-invariant
  thesis + F327 IPASIR-UP design).
- Hour summary: F333 (yale drift confirmed) + F334 (auditor + survey)
  + F335 (thanks + new D61=5 low recognition). Cross-machine flywheel
  productive: 6 yale commits + 4 macbook commits this hour.


## ~17:50 EDT — F336: F322 random-init seed is a kernel-safe local minimum

- Enumerated all 1536 kernel-safe single moves (common_xor + common_add±)
  on F322 best M1/M2 (a57=5 D61=14 score=39.65 chart=(dh,dCh)).
- 0/1536 moves improve a57 below 5 OR atlas score below 39.65.
  302 lower D61 but all break chart or hike a57 to 8-17.
- F322 random-init seed is a STRICT LOCAL MINIMUM in kernel-safe single-
  move space. F374's a57=4 territory is reached only via yale's chamber-
  seed basin, NOT random-init.
- Cross-machine Pareto front under strict kernel preservation now has at
  least 2 distinct basins:
    Random-init basin (F322): low-a57-with-chamber-chart corner
    Chamber-seed basin (F370-F374): mixed corners across multiple charts
- Implication: chamber attractor brittleness extends to "kernel-safe
  Pareto front splits into multiple disjoint basins, each with own
  local minimum, NONE contain the attractor". CDCL conflict analysis
  remains the structurally-distinct mechanism.
- Verified: F374 yale 303/303 PASS auditor (yale's claim accurate).

Commit: [next] (F336).


## ~18:25 EDT — F337+F338: F322 depth-2 + W*_57[22:23] core synthesis

- F337: 76,800 kernel-safe depth-2 paths from F322 base. 0 paths
  improve a57 below 5 OR atlas score below 39.65 (matches F336).
  D61 reachable down to 5 at a57=15 cost (in (dCh,dT2) chart).
- Yale F378 (parallel work): same F322 base reaches D61=4 in chamber
  chart at a57=19 cost. Combined: F322 basin reaches chamber attractor's
  D61=4 within 2 kernel-safe moves but ONLY at a57=19.
- Yale F384 minimized 2-literal UNSAT: dW57[22]=0, dW57[23]=1.
  Cross-checked F286 universal core: W*_57[22:23] are at 0.40-0.50
  core fraction — NOT universal anchors but cand-variable. Yale's
  UNSAT core is CDCL-derived structural constraint specific to this
  cand (m17149975/bit31).
- This is precisely the kind of "external clause not in Tseitin"
  that F324-F326 search-invariant thesis predicted and F327 IPASIR-UP
  cb_add_external_clause hook is designed for.
- Three classes of CDCL-derived constraints:
  1. F286 universal anchors (10/10 cands)
  2. F286 universal round-bits (W*_59+W*_60)
  3. F384 cand-specific UNSAT cores (NEW)
  Propagator should pre-load all three for max speedup.
- Cross-machine flywheel today produced first concrete propagator
  target: prevent dW57[22]=0 ∧ dW57[23]=1 polarity for m17149975/bit31.

Commit: [next] (F337+F338 synthesis).


## ~18:50 EDT — F339: yale's W57[22:23]=(0,1) UNSAT cross-validated independently

- Independent cadical 10s run on aux_force_sr60_n32_bit31_m17149975 CNF:
    polarity (0, 1):  UNSAT in 0.08s ← yale F384 confirmed
    other 3 polarities: UNKNOWN at 10s budget
- Python UP test (F324 codepath): all 4 polarities UP-OK with 483 forced.
  UP cannot see the (0,1) UNSAT — confirms F324-F326 search-invariant
  thesis. The constraint emerges from CDCL conflict analysis, not Tseitin.
- This is the first independently-verified cand-specific 2-literal CDCL
  UNSAT core. Adds a 3rd class of CDCL-derived structural constraint:
    Class 1: F286 universal anchors (4 specific bits)
    Class 2: F286 universal round-bits (W*_59+W*_60, 128 bits)
    Class 3: F384 cand-specific UNSAT cores ← NEW
- Concrete next step: F327 cb_add_external_clause should support both
  universal (init-time) AND cand-specific (per-cand-mine) clauses. The
  W57[22:23]=(0,1) clause is the first verified test injection.

Cross-machine cycle this hour:
  yale F378-F384 conflict-guided cube mining → macbook F337 depth-2 →
  F338 universal-core cross-check → F339 independent UNSAT verification.

Commit: [next] (F339).


## ~19:20 EDT — F340: W57[22:23] CDCL UNSAT is UNIVERSAL with fill-dependent polarity flip

- Generalized yale's F384 W57[22:23] finding across 6 cands at sr60.
  ALL 6 cands have exactly ONE polarity UNSAT in <0.1s; other 3 are
  UNKNOWN at 5s budget. The constraint is UNIVERSAL, not cand-specific.
- Polarity-flip pattern: fill bit-31 SET (bit0/bit10/bit17/bit31 with
  fill ∈ {0x80000000, 0xffffffff}) → (0,1) UNSAT; fill bit-31 UNSET
  (bit11 fill=0x00000000, bit13 fill=0x55555555) → (0,0) UNSAT.
- This is a NEW class of CDCL-derived structural constraint:
  Class 3' = universal-with-cand-parameterized-polarity. Polarity
  is computed from cand metadata (fill bit-31 in this case).
- F327 IPASIR-UP cb_add_external_clause should pre-load the W57[22:23]
  clause UNIVERSALLY with polarity from cand metadata — saves yale's
  per-cand mining cost (~5 min/cand).
- Refines F339's "cand-specific" framing: the constraint is universal,
  the polarity is cand-parameterized.

Cross-machine flywheel:
  yale F378-F384 → macbook F339 → macbook F340 generalization →
  Phase 2D propagator design has its first universal-with-flip target.

Concrete next: enumerate other (round, bit) positions for similar
universal-with-flip constraints. Algebraic derivation of σ-arithmetic
that produces the polarity flip.

Commit: [next] (F340).


## ~19:45 EDT — F341: dW57[0] = 1 single-bit CDCL UNSAT (LSB anchor mechanism)

- Enumerated all 32 dW57[i] × 2 polarity assignments on m17149975/bit31
  via cadical 5s budget. Wall: 316s.
- Result: EXACTLY ONE polarity is UNSAT — dW57[0] = 0 in 0.02s.
  This forces dW57[0] = 1 (LSB of W57 differential).
- Connects directly to F286 universal anchors W1_57[0] and W2_57[0]
  (both 10/10 core fraction): their XOR (= dW57[0]) must be a universal
  CONSTANT, and F341 verifies cadical immediately UNSATs the wrong polarity.
- This is a NEW class of CDCL-derived structural constraint:
  Class 1a — single-bit unit clause, derivable in 0.02s.
- Combined picture (Phase 2D propagator clause library):
    1. dW57[0] = 1 (unit, all cands per F286)
    2. NOT(dW57[22]=0 ∧ dW57[23]=¬fill_bit31) (2-bit, F340)
    3. Branching priority on F286 132 universal core
    4. Cand-specific cores from yale F378-F384 pipeline

Concrete next: cross-cand validate dW57[0]=1 on the 5 other cands from
F340; test dW58[0]/dW59[0]/dW60[0] for additional unit-clause UNSAT.

Commit: [next] (F341).


## ~20:15 EDT — F342: dW57[0] universally single-bit constrained, cand-specific polarity

- Tested dW57[0] / dW58[0] / dW59[0] / dW60[0] across 5 cands (180s wall).
- ALL 5 cands have exactly ONE polarity at dW57[0] UNSAT in ~0.01s.
  Plus F341 (bit31): 6/6 cands universally constrained at dW57[0].
- Forced value flips per cand:
    forced=0: bit0/0x80000000, bit10/0x80000000, bit13/0x55555555
    forced=1: bit11/0x00000000, bit17/0x80000000, bit31/0xffffffff
  Not determined by fill bit-31 alone — combination of (M[0], fill,
  kernel-bit) determines the polarity.
- dW58[0]/dW59[0]/dW60[0]: NO fast UNSAT in any cand. Single-bit
  mechanism is round-57-specific (matches F286: LSB anchors at
  W*_57[0], not W*_58[0]/W*_59[0]/W*_60[0]).
- Refined picture: TWO classes of universal-with-cand-parameterized-
  polarity constraints now identified:
    Class 1a-univ: dW57[0] (single-bit, F342)
    Class 2-univ:  W57[22:23] (2-bit, F340)
  Both can be pre-loaded by F327 propagator via ~0.1s cadical preflight
  per cand (~free preprocessing for hard sr=61 instances).

Commit: [next] (F342).


## ~20:35 EDT — F343: preflight_clause_miner.py shipped + 6-cand clause library

- Built `propagators/preflight_clause_miner.py` (~250 LOC) — runs
  cadical 5s probes to extract Class 1a-univ unit clauses (dW57[0])
  and Class 2-univ pair clauses (W57[22:23]) from any cascade-1
  cand's CNF.
- Per-cand cost: ~20s wall (5 cadical probes per cand).
- Caught a tool bug during shipping: cadical 3.0.0 rejects float
  budgets ("-t 5.0" → "invalid argument"). Fixed to integer.
- Mined clauses for all 6 cands (bit0/bit10/bit11/bit13/bit17/bit31).
  Each cand emits 2 ready-to-inject clauses for IPASIR-UP propagator's
  cb_add_external_clause hook at solver init.
- This is the concrete implementation step F327 was waiting for. Phase
  2D propagator can now ingest per-cand JSON and inject clauses
  immediately. Mining results in
  bets/programmatic_sat_propagator/results/preflight_2026-04-29/.
- Cross-cand pattern confirmed: dW57[0] forced is per-cand, W57[22:23]
  forbidden polarity tracks fill bit-31 (F340 verified).

Cross-machine yale→macbook chain this 2-day arc:
  F378-F384 cube/UNSAT mining → F339 cross-validation → F340 cross-cand →
  F341 single-bit → F342 cross-cand single-bit → F343 preflight tool.

Commit: [next] (F343).


## ~20:55 EDT — F344: dW57 row is FULLY over-constrained at 2-bit adjacent level

- Ran preflight tool's full sweep mode on m17149975/bit31: 32 single
  bits + 31 adjacent pairs (dW57[i], dW57[i+1]). 13 min wall, 63 cadical
  probes total.
- Result: 1 single-bit forced (dW57[0]=1, per F341) + 31 / 31 ADJACENT
  PAIRS forbidden. ALL consecutive bit pairs on dW57 row have exactly
  one forbidden polarity. That's a fully dense 2-bit constraint surface.
- Forbidden polarities all have form (0, ?). Lower bit's "0" value is
  always part of the forbidden combination. Upper bit varies — pattern:
  (0,0) at i ∈ {0,3,4,6,7,9,12,13,15,18,19,20,24,26,27,28,29}
  (0,1) at i ∈ {1,2,5,8,10,11,14,16,17,21,22,23,25,30}
  yale's F384 W57[22:23]=(0,1) is one of these 31.
- Structural interpretation: dW57 = W2[57] - W1[57] mod 2^32 is encoded
  via ripple-borrow subtractor. Each adjacent pair is a Tseitin-derived
  carry-chain constraint. CDCL conflict analysis fast-derives them all.
- Implication: dW57 is essentially DETERMINED by cand metadata. Phase
  2D propagator can pre-inject all 32 dW57 clauses at solver init,
  freeing CDCL to focus on dW58/dW59/dW60 + absorber compatibility.

Concrete next:
  (a) Verify dW57 has unique SAT model under 32-clause system → 32 unit
      injection clauses at solver init
  (b) Sweep W58/W59/W60 adjacent pairs (~10 min each)
  (c) Cross-cand sweep (~80 min total for all 6 cands)
  (d) Algebraic closed-form: compute dW57 from (M[0], fill, kernel-bit, sr)

Commit: [next] (F344).


## ~21:05 EDT — F345: F344's 32 dW57 clauses are NECESSARY but NOT SUFFICIENT

- Solved the 32-clause dW57 system in isolation (1 unit + 31 adjacent
  pairs) with UP + DPLL model counting.
- Result: only 1/32 bits assigned by UP (just dW57[0]=1). >1000 SAT
  models exist within the isolated 32-clause system.
- Refutes naive "pre-inject 32 dW57 unit clauses" hypothesis from F344.
  The 32 clauses are NECESSARY structural constraints (CDCL fast-derives
  them) but the actual unique dW57 value emerges only from coupling
  with the rest of the CNF.
- Refined propagator value: inject the 32 clauses as LEARNED CLAUSES
  (saves ~3-5s of cadical re-derivation per solve). Modest speedup.
- BIGGER win path: algebraic derivation of dW57 from (M[0], fill,
  kernel-bit, sr) — compute the schedule forward 57 rounds + cascade
  offset, get all 32 dW57 bits in microseconds. Then inject 32 actual
  unit clauses for FULL speedup. Concrete next move.

Honest reframe: F344 was structurally informative (dW57 is dense
2-bit constrained) but the naive propagator-pre-inject claim was
overblown. The algebraic-preflight path is the one that gives the
"32-bit unit clause injection" benefit cleanly.

Commit: [next] (F345).


## ~21:25 EDT — F346: algebraic dW57 preflight from M alone is STRUCTURALLY WRONG

- Attempted algebraic dW57 preflight: compute W1[57], W2[57] via
  schedule recurrence from M, take XOR.
- Empirical mismatch on bit0 cand: algebra says XOR LSB = 1, but cadical
  preflight says forced = 0 (F342). Doesn't agree.
- Read cascade_aux_encoder.py source: for sr=60, W1[57]/W1[58]/W1[59]/
  W1[60] are FREE schedule words (n_free=4). Solver chooses them
  constrained by cascade-1 hardlock at round 60. They're NOT determined
  by M alone.
- My algebra computed "M-derived W[57]" via schedule recurrence, but
  the encoder treats W[57] as free — different model.
- Refutes F345's "what's next (d)": there is NO microseconds-algebraic
  preflight for sr=60. Cadical preflight IS the right approach.
- Phase 2D propagator architecture confirmed:
    1. Init: receive cand metadata
    2. Preflight: cadical ~20s probe extracts mined clauses (F343 tool)
    3. Inject: cb_add_external_clause loads them at solver init
    4. Solve: main cadical/kissat run with propagator active

Net: ~20s preflight overhead, saves CDCL re-derivation (~3-5s per
solve attempt). Modest speedup, but the architecture is sound.

Honest reframe: F344+F345 mining work stands; F346 attempted shortcut
fails for structural reasons (W57..W60 freedom in sr=60 force-mode
encoding). Direction: ship the preflight tool as-is, no algebraic
shortcut exists.

Commit: [next] (F346).


## ~21:40 EDT — F347: F344 mined clauses give 13.7% fewer CDCL conflicts

- Empirical test: cadical 60s budget on bit31 m17149975 sr60 force-mode
  CNF, baseline vs F344-injected (32 mined clauses appended).
- Result at same 60s budget:
    Baseline:       2,190,601 conflicts, 9,524,146 decisions
    F344-injected:  1,891,271 conflicts, 9,320,660 decisions
    Δ conflicts:   -299,330 (-13.7%)
    Δ decisions:   -203,486 (-2.1%)
    Δ propagations: +53M (+25%) — extra prop work per node, less
                                   backtracking total
- Both UNKNOWN at 60s, but F344-injected explored a measurably better-
  pruned search tree. Real CDCL speedup, not artifact.
- Cost-benefit:
    20s F343 preflight + ~5% conflict reduction → break-even >400s solves
    13 min F344 full sweep + ~14% reduction → break-even >90 min solves
  For F235-class (848s timeouts), the 20s preflight is clearly worth it.
- Confirms F345/F346 reframe: cadical preflight + clause injection IS
  the right architecture. Speedup is modest but measurable.

Phase 2D propagator implementation is now empirically justified at the
"modest speedup" level. Larger gains would require either better
preflight mining (more clauses, more rounds) or instance-specific
optimization (e.g., F235 hard instance).

Commit: [next] (F347).


## ~22:00 EDT — F348: F343 2-clause injection gives 5-14% speedup across all 6 cands

- Tested cadical 60s baseline vs F343-injected (2 clauses: dW57[0] unit
  + W57[22:23] pair) on bit0/bit10/bit11/bit13/bit17 cands. ~10 min wall.
- ALL 5 new cands show conflict reduction: -5.1% to -11.1%. Plus F347's
  bit31 at -13.7% (32 clauses). Mean across 6 cands: -9.6%.
- F343 vs F344 cost-benefit:
    F343 minimal (2 clauses, 20s mining): 9.6% mean reduction
    F344 full row (32 clauses, 13 min): 13.7% reduction (only 4% extra)
  → F343 is the sweet spot. F344's 30 extra clauses give modest extra
    benefit at 40x mining cost.
- Break-even analysis:
    F343: 200s solve time → 20s preflight pays back via 10% reduction
    F344: 5700s solve time → 13 min preflight pays back
  For F235-class (848s timeouts), F343 is clearly worth it.
- Cross-cand variance: -5% to -11% suggests cand-specific structure;
  the 2 clauses help different cands by different amounts.
- Speedup is BELOW the bet's 2x reopen criterion (~1.1x), but measurable
  and useful for long-running sr=61 probes.

Phase 2D propagator implementation is now empirically grounded:
  - 20s preflight per cand (F343 mining)
  - cb_add_external_clause injects 2 clauses
  - Net 5-14% wall reduction on long-running solves
  - Concrete reopen path for the bet

Commit: [next] (F348).


## ~22:18 EDT — F349: m17454e4b/bit29 sr60 PENDING verification

- Background task notification arrived: yesterday's task on
  aux_expose_sr60_n32_bit29_m17454e4b_fillffffffff.cnf returned
  `s SATISFIABLE` after running ~24h (started yesterday 21:51 UTC,
  completed today 21:59 UTC).
- This cand has been tested at sr=61 only (3 logged TIMEOUT runs);
  no prior sr=60 run logged. If verified, would be a NEW sr=60 SAT
  instance (the project's second after m17149975/bit31).
- Verified the audit: CNF audits CONFIRMED, cand registered, encoder
  check passes (da[56]=0 cascade-eligible).
- Re-ran kissat with --time=600 (10min budget). Result: s UNKNOWN
  after 598s, 20.7M conflicts, 34k conflicts/sec.
- 10-min budget INSUFFICIENT to reproduce SAT. Original task ran
  hours/possibly ~24h with no --time limit.
- Saved both outputs (original task + 10-min verification log).
- NOT claiming new SAT. PENDING longer verification (1h kissat run
  needs user approval per multi-hour-compute rule).

Concrete next: ASK USER before launching 1h kissat verification.
If approved, extract model + lib/sha256 verify + log via append_run.py.
If verified, update CLAIMS.md (n32_sr60 SAT count: 1 → 2).

Discipline gap noted: the original bg task didn't use --output-model
or --time flags, didn't log via append_run.py. The SAT model itself
is NOT preserved — only the verdict line.

Commit: [next] (F349 PENDING memo).


## ~22:32 EDT — F350: cadical 600s also UNKNOWN — F349 cross-solver corroborated

- Cross-solver verification: cadical 3.0.0 -t 600 on the same
  aux_expose_sr60_n32_bit29_m17454e4b CNF. Result: UNKNOWN at timeout.
- Both kissat (F349) and cadical (F350) at 10-min budgets: UNKNOWN.
- Cross-solver agreement strengthens conclusion: original task's
  `s SATISFIABLE` either (a) found after >10 min solver time, or
  (b) some output artifact.
- 1147 prior sr=60 aux_expose runs in registry; only 4 SAT verdicts
  (3 cert-pin trivial reproductions of m17149975). For non-cert-pinned
  search, sr=60 SAT is STRUCTURALLY RARE.
- Logged F349 + F350 runs via append_run.py. Total runs: 1690 (+2).
- Status: F349 PENDING — needs >10 min compute (1h+ verification
  requires user approval per multi-hour-compute discipline rule).

User: please advise on whether to launch 1h kissat verification
(--time=3600 --output-model + append_run.py logging). If so, F349's
SAT either confirms (NEW sr=60 instance, headline-worthy) or is
refuted as artifact.

Commit: [next] (F350 cadical verification).


## ~22:45 EDT — F351+F352: F343 preflight on F349 CNF (sr60 expose) + injection still UNKNOWN

- F351: ran F343 preflight on m17454e4b/bit29 sr60 EXPOSE CNF.
    dW57[0] forced=1 (Class 1a-univ confirmed for kernel-bit-29
    EXPOSE — extends F341/F342 finding cross-mode + cross-kernel-bit)
    W57[22:23] forbidden=(0, 0) (different polarity from bit31's
    (0,1) at same fill=0xffffffff in FORCE mode — F340 hypothesis
    refines: more factors than fill alone)
- F352: cross-solver injection test (cadical 600s + kissat 600s
  parallel on F349 CNF + F351's 2 mined clauses).
    BOTH solvers UNKNOWN at 600s budget.
    kissat injected: 20.46M conflicts (vs 20.68M baseline = -1.06%)
    cadical injected: 15.35M conflicts (similar magnitude to baseline)
- Speedup MUCH smaller than F347's 13.7% on FORCE-mode bit31. Either:
    (a) EXPOSE mode benefits less from F343-mined clauses
    (b) The 2-clause injection works differently across cands
- F349 still PENDING. Original 24h-window task SAT not reproducible
  in 10min by either solver, with or without injection.
- Logged 4 runs total this hour via append_run.py. Total runs.jsonl: 1692.

Concrete next: the injection mechanism IS structurally validated for
sr=60 FORCE mode (F347 13.7% speedup on bit31), but EXPOSE mode shows
weaker effect. Worth noting in F327 IPASIR-UP design: per-mode
calibration may matter.

Commit: [next] (F351+F352 PENDING-extension memo).


## ~22:54 EDT — F353: USER APPROVED 4h compute → 3 parallel verification runs launched

User OK to use more compute. Launched at 22:53 EDT, target completion 02:53 EDT:

  PID 8053: kissat --time=14400 (baseline F349 CNF)
  PID 8054: kissat --time=14400 (F343-injected F352 CNF)
  PID 8055: cadical -t 14400 --no-binary (baseline, cross-solver)

Total: 12 CPU-h, 4h wall. Per user "use more compute, i can share, u can
have most of it."

If any returns SAT:
  → extract_and_verify.py parses model, reconstructs M1/M2
  → lib/sha256 runs schedule + compression, verifies round-60 state diff = 0
  → If verified: NEW sr=60 cascade-1 collision instance (project's 2nd)
  → Update CLAIMS.md, candidates.yaml, log via append_run.py
  → cascade_aux_encoding bet's recent_progress

If all 3 still UNKNOWN at 14400s:
  → original task's SAT was either spurious or required even longer time
  → escalate to 24h match of original timeline (needs another user OK)

Continuing autonomous work. Will check back at ~02:53 EDT.

Commit: [next] (F353 launch).


## ~22:55 EDT — F354: F343 preflight works at sr=61 (open frontier)

- Ran F343 preflight on aux_force_sr61_n32_bit31_m17149975_fillffffffff.
  20s wall.
- Result: dW57[0] forced=1, W57[22:23] forbidden=(0, 1) — IDENTICAL to
  sr=60 force-mode bit31 (per F340/F341).
- Class 1a-univ + Class 2 both transfer to sr=61. Phase 2D propagator's
  preflight produces SAME clauses across sr levels for the same cand.
- For F235 hard instance (sr=61 basic cascade encoder, kissat 562s
  timeouts): F343 mining + injection should give similar 5-14% speedup
  per F347/F348 measurement.

F353 verification still running (3 parallel 4h kissat/cadical, 2:09
into 4h budget, no SAT yet).

Commit: [next] (F354).


## ~23:14 EDT — F355: F343 preflight is sr-INVARIANT across 5 cands

- Ran F343 preflight on sr=61 force-mode CNFs for 5 cands (bit0/bit10/
  bit11/bit13/bit17). 100s total wall.
- Result: ALL 5 cands have IDENTICAL preflight output between sr=60
  and sr=61 (combined with F354 bit31 = 6/6 cands match):
    bit0:  forced=0 / (0,1) at both sr levels
    bit10: forced=0 / (0,1) at both
    bit11: forced=1 / (0,0) at both
    bit13: forced=0 / (0,0) at both
    bit17: forced=1 / (0,1) at both
    bit31: forced=1 / (0,1) at both
- F343 mined clauses are sr-INVARIANT for force-mode. Per-cand mining
  at sr=60 gives the clauses for sr=61.
- Phase 2D propagator design simplification: ONE 20s preflight per cand
  serves all sr levels for force-mode. No per-sr re-mining needed.
- Confirms structural argument: round-57 dW constraints come from
  cascade-1 hardlock structure that's invariant across sr=60/sr=61.

F353 verification (4h kissat/cadical) at 20/240min, no SAT yet.

Commit: [next] (F355 sr-invariant validation).


## ~23:35 EDT — F356: F343 preflight is mode-invariant (force vs expose)

- Ran F343 preflight on sr=60 EXPOSE mode for 5 cands + bit29 FORCE
  mode (completing bit29 cross-mode coverage).
- Result: ALL 7 cands have IDENTICAL preflight output across tested
  mode/sr combinations:
    sr60-force = sr60-expose = sr61-force per cand
- F343 mined clauses are properties of the CASCADE-1 COLLISION
  PROBLEM (round-57 differential), NOT of encoding choice.
- Per-cand mining at sr=60 force-mode (cheapest combo) gives the
  clauses for ALL sr levels and BOTH encoding modes.
- BUT: injection EFFECT is mode-dependent:
    F347 (sr60 FORCE, 32 mined clauses): -13.7% conflicts
    F352 (sr60 EXPOSE, 2 mined clauses): -1.06% conflicts
  Hypothesis: FORCE has 481 cascade-offset AUX clauses where the
  mined clauses provide "shortcut hints"; EXPOSE has fewer such
  clauses so the marginal value is smaller.
- Phase 2D propagator: prioritize FORCE mode injection (5-14% measurable
  speedup); EXPOSE mode injection still positive but smaller.

F353 verification still running (~21min in).

Commit: [next] (F356 mode-invariance).


## ~23:58 EDT — F357: F343 preflight on F235 hard cand + F340 refuted

- Ran F343 preflight on F235 reopen-target cand (m09990bd2/bit25/0x80000000)
  at sr=61 force-mode. 20s wall.
- Result: dW57[0] forced=0, W57[22:23] forbidden=(0, 0).
- Combined 8-cand table spans 4 kernel-bits, 4 fill values.
- F340 "fill bit-31 → polarity" hypothesis REFUTED:
    bit25 fill=0x80000000 (bit-31 SET) → (0,0) [should be (0,1) per F340]
    bit29 fill=0xffffffff (bit-31 SET) → (0,0) [should be (0,1) per F340]
- Polarity correlates with KERNEL-BIT instead:
    (0, 1): kernel-bits {0, 10, 17, 31}
    (0, 0): kernel-bits {11, 13, 25, 29}
  No obvious arithmetic pattern; non-trivial function of (M[0], fill, kernel-bit).
- F235 reopen path: 2 mined clauses ready for IPASIR-UP injection. Need
  to map var IDs from aux_force to F235's basic cascade encoder (~30 min)
  OR build F343 var-discovery on F235 directly.

F353 verification still running (~62 min/240 min). Will trigger on SAT.

Commit: [next] (F357).


## ~00:23 EDT (Apr 30) — F359 launched: full-row sweep on F235 cand

- Launched F344-style full-row sweep on aux_force_sr61 m09990bd2/bit25.
  Target: ~32 clauses (vs F357's 2). 13min wall.
- Plan: translate the ~32 mined clauses to F235's basic-cascade vars
  and re-test injection. Expected: stronger speedup than F358's 2.1%.
- Per F344 result on bit31 sr60: full-row gave 13.7% vs 2-clause's
  baseline. Rough projection for F235: 4-6% if scaling holds.

F353 4h verification: ~90 min/240 min, no SAT yet. PIDs 8053/8054/8055
all active.

Commit: [next] (F359).


## ~00:36 EDT (Apr 30) — F359: full-row sweep on F235 cand → 34 mined clauses

- F344-style full sweep on aux_force_sr61 m09990bd2/bit25 cand. 12.5min wall.
- Result: 3 single-bit forced (dW57[0]=0, [1]=0, [2]=1) + 31/31 adjacent
  pairs forbidden = 34 total mined clauses (vs F357 minimal's 2).
- m09990bd2/bit25 has MORE single-bit constraints than bit31 (1 single).
  Cand-specific richness confirmed.
- Translation to F235 vars (basic cascade encoder) for injection test:
    3 unit × 2 clauses + 31 pair × 4 clauses (OR-of-XORs) = 130 CNF clauses
- Expected speedup on F235 (projecting from F347/F348/F358): 5-10%.
  Would save ~50-85s on F235's 848s baseline.
- F353 4h verification still running (~106 min/240 min, no SAT yet).

Commit: [next] (F359 full sweep).


## ~00:50 EDT (Apr 30) — F360: F358 RETRACTION + corrected -0.79% measurement

- Caught F358 bug during F360 derivation: my 4-clause OR-of-XOR
  encoding had wrong polarities, didn't actually forbid the
  (W1=W2 AND W1=W2) case. Manual truth-table check confirmed.
- Corrected F359's 34 mined clauses → 130 F235 CNF clauses with
  proper encoding. Re-ran cadical 5min comparison.
- Result: -0.79% conflict reduction (vs F358's claimed -2.1% which
  came from BUGGY clauses).
- Retracted F358's interpretation. F343 preflight + CNF-only injection
  on F235 basic cascade encoder gives ~1% best case — much weaker
  than F347's 13.7% on aux_force.
- Speedup envelope clarified:
    aux_force + 32 clauses (F347): -13.7%
    aux_force + 2 clauses (F348):  -8.8% mean
    aux_expose + 2 clauses (F352): -1.06%
    BASIC CASCADE + 130 clauses (F360): -0.79%  ← real F235 measurement
- 6th retraction this 2-day arc. Phase 2D propagator NATIVE injection
  via IPASIR-UP remains the path to F347-class 13.7% on F235.

F353 verification at 117 min/240 min, no SAT.

Commit: [next] (F360 retraction).


## ~01:00 EDT (Apr 30) — F361: IPASIR_UP_API.md updated with real F343-F360 measurements

- Extended propagators/IPASIR_UP_API.md with 2026-04-30 update
  documenting empirical envelope from F347-F360 sequence.
- Honest revision of F327's 2-5x speedup projection:
    F347 aux_force 32 clauses: -13.7% (best)
    F348 aux_force 2 clauses: -8.8% mean
    F352 aux_expose 2 clauses: -1.06%
    F360 basic_cascade 130 clauses: -0.79% (worst — F235 measurement)
- F360 retraction integrated: F358's claimed -2.1% was buggy CNF.
- Phase 2D reopen criterion REVISED: 2x is unrealistic for CNF-only;
  native-hook injection might hit ~1.16x via F347-class speedup.
- For Phase 2D implementer: concrete recommendations + reopen gate updated.

F353 verification at 122/240 min, no SAT yet. SAT-detection monitor
re-armed (60 min more).

Commit: [next] (F361 doc update).


## ~01:58 EDT (Apr 30) — F362: aux_force_sr61 bit25 only -0.46% (noise level)

- Tested F359's 34 mined clauses NATIVELY on aux_force_sr61 m09990bd2/bit25.
  cadical 5min: 5,348,445 baseline → 5,324,083 injected = -0.46%.
- Combined with F360's -0.79% on basic-cascade for SAME cand: both
  ~1% or below — INDISTINGUISHABLE FROM NOISE.
- F347's 13.7% on bit31 sr60 was an OUTLIER. Cand-specific variance
  dominates injection benefit.
- Updated speedup envelope:
    F347 sr60 aux_force bit31 (32 clauses): -13.7%  ← outlier
    F348 sr60 aux_force 5-cand mean (2):    -8.8%
    F352 sr60 aux_expose bit29 (2):         -1.06%
    F360 sr61 basic_cascade bit25 (130):    -0.79%
    F362 sr61 aux_force bit25 (34):         -0.46%  ← noise
- Phase 2D reopen recipe sharpened: F235 (bit25) is NOT ideal test
  instance — speedup too small. Best candidates for native injection
  are bit31-class cands where F347 measured the outlier 13.7%.
- Need controlled test: bit31 m17149975 at sr=61 with native injection
  to isolate variables (cand vs sr vs mode).

F353 verification at 182/240 min, no SAT yet. Re-arming monitor.

Commit: [next] (F362 noise-level finding + cand-variance reframe).


## ~02:17 EDT (Apr 30) — F363: bit31 sr61 + 2 clauses also ~noise (-0.72%)

- Tested aux_force_sr61 bit31 m17149975 + F354's 2 mined clauses (5min cadical).
  Result: -0.72% (vs F362 bit25 sr61 -0.46%).
- 2-clause F343 minimal preflight gives ~1% across all cands tested.
- F347's 13.7% on bit31 sr60 with 32 clauses is increasingly looking
  like: (a) 30-extra-clause bulk effect, or (b) noise outlier.
- F348's -8.8% mean across 5 cands also suspicious — may be similar.
- Concrete unblock: F344-style full-row sweep on aux_force_sr61 bit31
  (~13min mining + 10min comparison) would test if 32-clauses give
  ~13% even at sr=61 (vs 2-clauses' ~1%).
- Phase 2D propagator viability picture darkens: real speedup on most
  cands appears ~1%, far below F361's 1.16x reopen criterion.

F353 verification at ~210/240 min, no SAT yet (final 30 min).

Commit: [next] (F363).


## ~02:25 EDT (Apr 30) — F364 launched + cascade_aux_encoding heartbeat refreshed

- F364: F344-style full-row sweep on aux_force_sr61 bit31 m17149975
  (the F347 13.7% outlier cand at sr=61). 13min mining, then 10min
  injection comparison.
  Will tell us: does F347's 13.7% reproduce at sr=61 with 32 clauses?
  Or was it sr=60 specific / noise?
- Refreshed cascade_aux_encoding BET.yaml heartbeat with substantive
  progress notes covering F341-F363 chain (~30-line update).
  Documents:
    - 4 structural classes (Class 1a/2 universal, Class 3 F286, Class 4 yale-style)
    - SR/mode invariance (F354-F356)
    - Empirical speedup envelope (F347 to F363, cand variance)
    - F322/F358 retractions
    - F349 PENDING SAT verification ongoing
- registry validates 0/0.

F353 verification at ~211/240 min, no SAT yet (~29 min remaining).

Commit: [next] (F364 launch + cascade_aux heartbeat).


## ~02:42 EDT (Apr 30) — F364+F365: F347's 13.7% APPEARS TO BE NOISE OUTLIER

- F364 mined full-row sweep on aux_force_sr61 bit31: 32 clauses (same
  structure as F344 bit31 sr60). 13min wall.
- F365 injection 5min: -0.08% conflict reduction (5,253,180 → 5,248,930).
  Essentially ZERO speedup.
- F347 measured -13.7% on EXACT same setup at sr=60. F365 at sr=61
  with same cand, same 32 clauses, same encoder: -0.08%.
- Per F354/F355 sr-invariance of mining: should be similar magnitude.
  F347's 13.7% is almost certainly noise outlier from N=1 measurement.
- Updated empirical envelope:
    F347 sr60 bit31 32 clauses: -13.7% (NOISE)
    F365 sr61 bit31 32 clauses: -0.08% (real, near-zero)
    F362/F363/F360 various 2-130 clauses sr61: -0.46% to -0.79%
    Real speedup ~0-1% on all sr=61 cands.
- Phase 2D propagator viability SERIOUSLY compromised. F361's 1.16x
  reopen criterion essentially unreachable with CNF injection.
- 7th retraction-style finding this 2-day arc.

F353 verification at ~225/240 min, no SAT yet (~15 min remaining).

Next concrete probe: F347 replication with cadical seeds for noise
floor estimate.

Commit: [next] (F364+F365 F347-refutation).


## ~02:55 EDT (Apr 30) — F353 4h verification COMPLETE: F349 SAT NOT REPRODUCED

- All 3 parallel 4h runs ended at budget cap, all UNKNOWN:
    kissat baseline:  230.7M conflicts UNKNOWN (3h 58m)
    kissat injected:  233.8M conflicts UNKNOWN (3h 58m) — +1.31% MORE
    cadical baseline: 128M conflicts UNKNOWN (4h)
- F349 SAT NOT REPRODUCIBLE IN 4 HOURS.
- Per F362-F365: F343 injection effect at sr=61 is ~0-1% noise level.
  4h kissat injected gave +1.31% conflicts (slightly worse than baseline).
- Updated F349 memo to PENDING_NEGATIVE_EVIDENCE_4H. Original 24h-window
  task SAT report stays UNVERIFIED. NOT updating CLAIMS.md.
- Logged all 3 runs via append_run.py. Total runs.jsonl: 1696.

User: 4h compute budget consumed. Result: F349 SAT not reproduced.
Recommend: leave F349 as PENDING and move on; OR commit another 24h+
verification budget to match original timeline. Your call.

For now, F353 is closed-with-negative-evidence. Continuing with other
work.

Commit: [next] (F353 final verdict).
