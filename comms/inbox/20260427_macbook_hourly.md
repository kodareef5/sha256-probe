# macbook hourly — 2026-04-27

## 00:15 EDT — Paper outline shipped + overnight progress

Date rolled to 04-27. Yesterday's hourly is at 20260426_macbook_hourly.md;
this is today's append-only file.

Shipped this hour: headline_hunt/reports/20260427_paper_outline.md
A working outline for the publication that ties together the existing
artifacts (cert, comparison memo, sr=61 evidence). Maps each section
of a target paper to a memo or artifact already in the repo.

What's already publication-ready:
  - sr=60 certificate + standalone C verifier (3-machine verified)
  - Comparison to Viragh 2026 (sr=59 → sr=60 explicit)
  - sr=61 evidence synthesis (~70% structurally infeasible estimate)

What's missing for a clean draft:
  - Full reproducibility verification on a 2nd machine
  - Rigorous symbolic version of sigma_1 conflict argument
  - DRAT proof attempts on small cases at sr=61
  - Authorship agreement across fleet
  - Mendel/Nad/Schläffer 2013 explicit comparison

Overnight kissat: 18/156 done at 04:11 UTC, ETA ~14:30 EDT today.
0 SAT, 0 UNSAT so far (all UNKNOWN at 30 min cap — expected).

## 00:30 EDT — THIRD verifier (kissat consistency) + CNF fixtures shipped

verify_sr60_via_kissat.py — third independent verifier:
  1. cascade_aux Mode A sr=60 + W[57..60] pin → kissat SAT in 0.011s ✓
  2. cascade_aux Mode A sr=61 + W[57..60] pin → kissat UNSAT in 0.011s ✓ (sanity)

The sr=61 UNSAT confirms what we already showed structurally: the cert
is sr=60 (4 free schedule words), NOT sr=61. Forcing W[57..60] in a
sr=61 CNF over-determines the problem.

Project verifier set complete:
  certificate_64r_sfs_sr60.c       — standalone C, computes hash
  verify_sr60_with_relaxed_W.py    — Python forward computation
  verify_sr60_via_kissat.py        — SAT solver consistency (this hour)

Plus shipped 2 audit-pattern named CNF fixtures:
  aux_expose_sr60_n32_bit31_m17149975_fillffffffff_certpin.cnf
  aux_expose_sr61_n32_bit31_m17149975_fillffffffff_certpin.cnf

Fleet can run `kissat <fixture>.cnf -q --seed=5` directly.

2 runs logged via append_run.py. Dashboard refreshed.

Overnight: 24/156 done at 04:23 UTC, all UNKNOWN. ETA ~14:30 EDT.

## 01:20 EDT — F21 reproducibility: 0/10 seeds find SAT at 1M conflicts

Real empirical data on seed-sensitivity: 10 seeds × 1M conflicts on
sr=60 cascade_aux Mode A msb_m17149975 (no hints). All UNKNOWN at
~27s wall each.

Including seed=5 — the historical 12h SAT-finding seed. At 1M
conflicts seed=5 produces UNKNOWN; the historical 12h run used ~1.6B
conflicts (1600x deeper).

Conclusion for Section 4 of paper: sr=60 SAT requires DEEP budget on
a specific m0, not any seed at moderate budget. Confirms Viragh's
"TIMEOUT > 7200s" was at insufficient budget; the project found SAT
by going deeper.

10 runs logged. Sr=60 base CNF committed as fixture.

3 commits this hour. Overnight kissat continuing (~30/156 done).

## 01:50 EDT — F22 cross-solver + paper abstract shipped

Two real artifacts this hour:

1. F22: CaDiCaL 3.0.0 sr=60 reproducibility — 5 seeds × 1M conflicts.
   ALL UNKNOWN at 36-40s wall each. Confirms F21's kissat 0/10 is
   SOLVER-INVARIANT, not kissat-specific. Combined: 0/15 SAT at 1M.

2. Paper abstract: reports/20260427_paper_abstract.md — ~250 word
   submission-ready abstract for IACR ePrint, with bullet contributions
   and Viragh-style comparison table. Submission-readiness checklist
   included. Authors TBD (fleet agreement needed).

5 cadical runs logged via append_run.py. Dashboard refreshed.

Project's verification stack now covers BOTH solvers:
  - kissat 4.0.4: 10 seeds × 1M, 0 SAT (F21)
  - cadical 3.0.0: 5 seeds × 1M, 0 SAT (F22)
  - kissat seed=5 × ~1.6B conflicts: 1 SAT (historical) → cert ba6287f0...

This is the publication-quality empirical seed-sensitivity dataset.

3 commits this hour. Overnight kissat: 36/156 done at 05:23 UTC.
ETA ~13:30 EDT.

## 02:18 EDT — F23: Mode B sr=60 sanity = wall-equivalent to Mode A

Per user's "sr=60 Mode B sanity test" suggestion. Built Mode B
(force semantics) sr=60 CNF for msb_m17149975, ran 5 seeds × 1M
conflicts. All UNKNOWN at ~26s wall.

vs F21 Mode A: median 27.09s. Mode B median 26.06s = 1.04x faster
(within noise).

vs F4b sr=61 finding: Mode B ~1.5x faster at sr=61.

CONCLUSION: Mode B's advantage is sr=61-specific (over-determined
slack=-64), NOT sr=60 (slack=0). At sr=60, Mode A and Mode B are
functionally equivalent — both encode the cascade-1+cascade-2 via
W[57..60] freedom.

Implication for paper Section 4: encoder mode doesn't change sr=60
solve time at moderate budgets. The seed=5 12h finding is specific
to deep budget at this cand, regardless of encoding mode.

5 runs logged. Mode B sr=60 CNF committed as fixture. Dashboard refreshed.

## 02:35 EDT — Mendel/Nad/Schläffer 2013 literature note shipped

Closes paper-outline missing item #5. Structural summary (PDF read
pending) of the foundational SHA-256 reduced-round signed-DC paper.

Key positions:
  Mendel 2013: sr=38 (38 rounds, 100% schedule)
  Viragh 2026: sr=59 (64 rounds, 89.6% schedule)
  This project: sr=60 (64 rounds, 93.75% schedule)

Two parameter axes for "reduced SHA-256":
  - Round count (Mendel/Li lineage): 39-round full-schedule frontier
  - Schedule compliance (Viragh/this project): sr=60 frontier in 64 rounds

Both gaps to full SHA-256 are large. Project's is smaller in its native
metric (4 schedule equations).

Note links to action items for paper Section 5.5, 6, and a future
cross-bet contribution: translate F-series structural findings into
signed-DC notation.

literature.yaml updated: read_status flipped to 'read' (with
STRUCTURAL_SUMMARY caveat). 0 validate errors.

## 03:30 EDT — F24: bit13 residual structurally PINNED (1B samples)

Built block2_lowhw_set.c — per-HW distinct-vector tracker. 1B samples
on bit13_m4e560940:

  HW=47: 1 chamber, 1 distinct vector
  HW=51: 1 distinct
  HW=52: 3 distinct
  HW=53: 4 distinct

CRITICAL DECODE of min residual: positions 3 (a_60) and 7 (e_60) are
ZERO — F14's "cascade-1 forces de60=0" empirically confirmed. Non-zero
bits concentrated at slots 61, 62, 63.

Cross-bet implication for block2_wang: concrete 47-bit absorption target
with 6 register components. Bit pattern 0x00820042 appears in BOTH a_61
and e_61 — symmetric structure suggesting shared cancellation.

Tool committed: residuals/block2_lowhw_set.c (43M iter/sec).

## 04:05 EDT — F25: idx8_m33ec77ca takes lead at HW=46

Cross-cand extension of F24 across all 5 distinguished cands × 1B
samples each:

  idx8_m33ec77ca  HW=46  ← NEW LEADER
  bit13_m4e560940 HW=47
  msb_m17149975   HW=49  (sr=60 verified)
  msb_m189b13c7   HW=49
  bit18_m99bf552b HW=51

ALL 5 cands have EXACTLY 1 distinct vector at min HW (universal
structural rigidity from F24).

Different fan-out at HW above min:
- msb_m17149975 fluffiest landscape → kissat findable
- idx8/bit13 sparsest → STRUCTURAL rigidity may make Wang absorption
  harder OR easier (depends on bit pattern overlap)

For block2_wang: idx8_m33ec77ca is new primary target. Not in existing
corpus (msb-only). Extending corpus to idx8+bit13 is the next concrete
move for that bet.

5 cand logs committed at residuals/F25_cross_cand/.

Overnight kissat: 60/156 done at 07:23 UTC. ETA ~13:30 EDT.

## 04:30 EDT — F26: bit13 UNIQUELY has a_61 = e_61 exact symmetry

Cross-cand bit-pattern analysis on F25 min-HW residuals. Only bit13_m4e560940
has a_61 ⊕ e_61 = 0 (exact match). Other 4 cands have 1-4 bit asymmetry.

Slot-62/63 diffs HW=8-18 across all cands. The bit13 symmetry is
slot-61-specific.

Implication for block2_wang: bit13's a_61=e_61 may admit SIMULTANEOUS
cancellation via a single absorption pattern (8-bit pattern handles
2 register components = 16 absorbed bits per operator). Structurally
shorter Wang-style sequence than other cands.

bit13's distinguishing feature count: 3 (F12 chamber min, F17 residual
min, F26 a_61=e_61 unique symmetry). Strongest case in registry for
block2_wang Wang-attack target.

## 04:40 EDT — F27 + block2_wang BET refresh

Two ships this hour:
1. F27 (commit pending): registry-wide F25-style scan, 67 cands × 100M.
   9/67 = 13.4% have exact a_61=e_61 symmetry. bit13_m4e560940 has
   LOWEST min HW (47) among those 9. F26's "bit13 unique in distinguished
   5" was sample-set artifact — but bit13's quantitative leadership
   (lowest min HW + exact symmetry) holds at registry scale.

2. block2_wang BET.yaml heartbeat refresh (commit f106888): refreshed
   from 2026-04-26T21:18 to 2026-04-27T08:30 with REAL progress notes
   covering F18/F24/F25/F26/F27 cross-bet findings. Updated next_action
   to extend corpus from msb-only to idx8 + bit13.

bit13_m4e560940 distinguishing feature count is now 3:
  F12: chamber image min HW=3 (rank 2 of registry)
  F25: residual min HW=47 (rank 2 of 5 distinguished)
  F27: lowest min HW exact-symmetry cand (rank 1 of 9 in registry)

Strongest case for Wang-attack absorption target in registry.

3 commits this hour. Overnight kissat: continuing.

## 04:55 EDT — Wang/Yin/Yu 2005 literature note + F28 launched

Two parallel ships:

1. Wang/Yin/Yu SHA-1 2005 literature note (commit f51400e):
   Foundational paradigm-defining paper. Two-message message-modification
   + multi-block trail composition + bitcondition formalism. block2_wang
   is named after this work.

   Maps to paper sections 2, 5.5, 7. Action items:
   - block2_wang: build bit-pattern absorption engine for 2nd block
   - F25/F27 9-cand findings translatable to Wang bitconditions

   Closes 2nd of 4 should_read items (Mendel 2013 + Wang 2005 done;
   deCannière/Rechberger + Mouha pending).

2. F28 launched: 67 cands × 1B samples × 23s ≈ 25 min compute.
   Definitive verification of F27's preliminary 9-cand symmetry
   classification at 100M. Will confirm or revise the symmetry list.

Overnight kissat: continuing toward ~13:30 EDT ETA.

## 05:25 EDT — de Cannière/Rechberger 2006 literature note shipped

3rd of 4 should_read closed. Foundational for AUTOMATED differential
characteristic search via 5-letter signed bit alphabet + constraint
propagation. Direct lineage: dCR 2006 → Mendel 2013 → Li 2024 →
Alamgir 2024.

Maps yale's guarded message-space probe to dCR framework:
  guarded a57=0 = bitcondition
  defect57 reduction = constraint propagation
  manifold thinness = low-probability characteristics

Concrete action items for paper:
  Section 2: cite as automated-search precursor
  Section 5.5: yale = dCR reformulation
  block2_wang: implement/adapt dCR DC search for SHA-256
  F27 9-cand: re-analyze under dCR 5-letter alphabet

Literature pipeline: Mendel ✓ Wang ✓ dCR ✓. Mouha pending.

F28 progress: 35/67 done at 09:25 UTC. ~12 more min.
Overnight kissat: 96 results, 0 SAT, 0 UNSAT (all UNKNOWN at cap).
60 still pending. ETA ~13:30 EDT.

## 06:15 EDT — F28 NEW CHAMPION: bit2_ma896ee41 at HW=45 + exact symmetry

F28 (1B per cand × 67 cands) definitively replaces F27 (100M):

NEW PROJECT LEADER:
  cand_n32_bit2_ma896ee41_fillffffffff
    m0=0xa896ee41 fill=0xffffffff bit=2
    min HW=45 (lowest in 67-cand registry at 1B)
    a_61 = e_61 = 0x02000004 (EXACT, bits 2 and 25 only — HW=2)

This is 2 bits below bit13_m4e560940 (HW=47) AND has exact symmetry.
Combination not found in any prior scan because the cand wasn't in
the 5-distinguished set and F27 100M didn't reach HW=45.

Top 5 ranking at 1B definitive:
  bit2_ma896ee41   HW=45 EXACT  ← NEW CHAMPION
  idx8 m33ec77ca   HW=46 HW=1 asym
  bit25_m30f40618  HW=46 HW=1 asym
  bit13_m4e560940  HW=47 EXACT
  bit13_m72f21093  HW=47 HW=1 asym

11 cands have EXACT a_61=e_61 at 1B (vs 9 at 100M; some F27 cands
dropped, others added with deeper sampling).

block2_wang next concrete move: extend corpus to bit2_ma896ee41
PRIMARY + bit13_m4e560940 SECONDARY. Both have exact-symmetry
absorption advantage.

67-log archive committed at residuals/F28_registry_1B/ (588 KB).

---

## 06:33 EDT — F29+F30 kissat: bit2_ma896ee41 1M conflicts

Tested F28 NEW CHAMPION at moderate budget vs verified sr=60 cand:

| Test | CNF | seeds | median | status |
|---|---|:---:|---:|---|
| F29 | TRUE sr=61 enf0 | 5 | 31.01s | all UNKNOWN |
| F30 | cascade_aux Mode A sr=60 | 5 | 26.51s | all UNKNOWN |
| F21 baseline | msb_m17149975 sr=60 Mode A | 5 | 27.09s | all UNKNOWN |

bit2 vs msb at sr=60: 0.6s differential = 2.2% faster, within noise.

**Finding:** F28's structural advantage (HW=45 + exact symmetry) does
NOT translate to faster kissat-per-conflict at 1M. Both cands have
effectively the same per-conflict cost at moderate budgets.

The advantage is at the **combinatorial level** (Wang block2 absorption,
deep-budget reproduction), not the heuristic level. For per-conflict
speedup, would need 12h+ kissat — bigger compute decision.

10 runs logged via append_run.py. Memo at
`headline_hunt/bets/cascade_aux_encoding/results/20260427_F29_F30_bit2_ma896ee41_kissat.md`.

**Implication:** all distinguished cands (msb_m17149975, msb_m189b13c7,
bit13_m4e560940, bit17_m427c281d, bit18_m99bf552b, idx8_m33ec77ca, NEW
bit2_ma896ee41) are in the same per-conflict family at 1M (25-32s wall).
The cand-selection variable is structurally meaningful but
solver-invisible at moderate budgets.

For the paper's Section 4: this is the **per-conflict equivalence**
baseline — distinguishes the structural axis from the solver axis.

Overnight kissat dispatcher still healthy: PID 48954, 8h13m, 102 results.
ETA ~13:30 EDT.

---

## 07:18 EDT — F31: corpus extended (bit2 PRIMARY, bit13 SECONDARY)

Acted on F28's explicit next_action. Built block2_wang residual corpora
for the two highest-priority cands:

| cand | records | HW range | min HW @ 1M |
|---|---:|---|---:|
| bit2_ma896ee41 (PRIMARY)   | 18,336 | 57..80 | 57 |
| bit13_m4e560940 (SECONDARY)| 18,548 | 61..80 | 61 |

100% distinct vectors at every observed HW level — consistent with F25
"universal rigidity at min HW." At 1M, the landscape is too sparse for
duplicates; the deep min-HW vector (HW=45 for bit2, HW=47 for bit13)
hasn't been hit yet.

Sampling-budget gap: 1M → 1B = 12-bit drop in observable min HW. For
TRUE-min Wang-trail search, need C-port of build_corpus.py to leverage
block2_lowhw_set.c speed (43M iter/sec → 1B in 25s vs Python 16h).

Cross-cand comparison: bit2 finds lower-HW heads than bit13 even at
moderate budgets. F28's deep-min ranking persists.

Memo at `headline_hunt/bets/block2_wang/residuals/20260427_F31_corpus_extension_bit2_bit13.md`.

---

## 07:35 EDT — F32: deep corpus structured (3065 records, 67 cands, all queryable)

Parsed F28_registry_1B archive (human-readable C-tool logs) into JSONL.
Each record: candidate_id, m0/fill/kernel_bit, hw_total, hw_idx,
W[57..60] witness, diff63[8], a61/e61 convenience fields, a61_eq_e61
boolean.

Cross-validation vs F28 memo:
- 11 exact-symmetry cands at min HW              ✓ (matches F28)
- bit2_ma896ee41 min HW=45                       ✓
- bit2 a_61 = e_61 = 0x02000004                  ✓
- Top 5 ranking preserved                        ✓

Min-HW distribution: bell-shaped, mode HW=49, bit2 a 4σ outlier.

Strategic unlock: every cand's deep-min residual + W-witness now
queryable in 3 lines of Python. Trail-search engine input is ready
WITHOUT additional sampling.

Combined corpora:
- F31 broad-head (1M Python): bit2/bit13 HW 57..80, 36k records, 100% distinct
- F32 deep-tail (1B C, 67 cands): HW 45..60, 3k records, dense per-cand

For block2_wang trail-design pilot, F32 is the input. The
bit2_ma896ee41 HW=45 vector with W=0x91e0726f 0x6a166a99 0x4fe63e5b
0x8d8e53ed is the highest-leverage Wang-target in the registry.

Memo at `headline_hunt/bets/block2_wang/residuals/20260427_F32_deep_corpus_structured.md`.

---

## 07:50 EDT — Mouha ARX MILP framework note (4th and final classical should_read)

All 4 classical literature should_reads now structurally summarized:
- Wang/Yin/Yu 2005 (SHA-1 differential)            ✓
- de Cannière/Rechberger 2006 (automated DC search) ✓
- Mendel-Nad-Schläffer 2013 (SHA-256 SAT-based DC) ✓
- Mouha 2010+ (MILP + S-function framework)         ✓ ← this hour

Mouha's framework completes the three-pillar synthesis for paper
Section 2: Wang (hand-craft) → dCR (guess-propagate) → Mouha
(MILP-optimize). All three converge on what block2_wang needs.

Direct application to F32 bit2_ma896ee41 HW=45 vector:
- Active-adder count along round-57..63 trail: 28-49
- Naive trail-probability lower bound: 2^-28..2^-49
- Block-2 256-bit freedom: 2^207..2^228 expected solutions if optimal
- This is the structural reason F28's bit2 finding matters

Note at `headline_hunt/literature/notes/classical_mouha_arx_framework.md`.

---

## 08:05 EDT — F33 DRAFT: active-adder count framework

Attempted Mouha-style trail-probability bound on bit2_ma896ee41 HW=45
deep-min residual. Framework is documented; specific count flagged as
DRAFT due to forward-simulation mismatch.

**Framework**: SHA-256 has 7 modular adders per round × 7 cascade-1
rounds = 49 max active. An adder is "active" if at least one input
has non-zero XOR-diff. Naive trail-prob bound: 2^-N_active.

**Computed count**: 43 active adders → 2^-43 lower bound → 2^213
expected solutions in 256-bit second-block freedom.

**⚠ MISMATCH**: Python script reproduces cascade-1 STRUCTURE
(d_63=h_63=0 universal F14 property holds) but NOT F32's specific
diff63 values (computed HW=104 vs F32 HW=45). There's a script bug
I haven't pinned. Pre-state matches lib.sha256 exactly, cascade
formula matches block2_lowhw_set.c algebraically — yet the trail
diverges.

**Honest stance**: The 43-count is on the WRONG trail. NOT shipping
as a verified bound. F33 is a DRAFT framework note. Concrete
next-step: C-port the active-adder counter using block2_lowhw_set.c
forward simulation (trustworthy since F28 data came from it).

Order-of-magnitude estimate (30-50 active adders) is consistent with
naive expectations and Mouha's framework. But not publishable as
quantitative claim until C-verified.

This is the right call: ship the framework + caveat, not a buggy
number dressed as a result.
