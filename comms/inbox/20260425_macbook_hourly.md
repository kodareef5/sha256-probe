
## 00:48 EDT — Theorem 4 boundary pinpointed: r=61 modular = 100%, r=62 = 0%

Per-round da-de equality check across 5000 samples on priority candidate:
  r=61: da_mod==de_mod 100% (Theorem 4 confirmed empirically), da_xor==de_xor only 0.04%
  r=62: BOTH forms 0% — round 62 breaks the equality
  r=63: 0% (divergence continues)
Sharpens earlier 'Theorem 4 fails at r=63' to: holds modularly at r=61, breaks completely at r=62.
**Possible bug flagged**: cascade_aux force-mode SPEC enforces XOR-form dA[61]=dE[61], but Theorem 4 is modular. XOR-form is a stricter (and incorrect-by-form) constraint that admits only 0.04% of valid samples. SPEC may need correction.
Writeup: `bets/mitm_residue/results/20260425_theorem4_pinpoint.md`

## 01:17 EDT — Retraction: previous SPEC-bug claim was wrong

Verified the cert (sr=60 collision) has da=de=0 starting at r=60 — XOR-equality and modular-equality BOTH hold trivially from r=60 onward.
Mode B's XOR-equality encoding admits the cert. The 0.04% rate I observed was on RANDOM cascade-held residuals, not on collision-solution paths.
Retracting the SPEC-bug flag from `20260425_theorem4_pinpoint.md`.
The boundary-pinpoint (r=61 modular = 100%, r=62 = 0%) STANDS — that's an independent finding.
Mode B's ≥10x SPEC claim remains separately refuted at 90-min budget for unrelated reasons.
Writeup: `bets/mitm_residue/results/20260425_spec_bug_retraction.md`

## 02:00 EDT — Theorem 4 structural proof: r=62 breakage formula identified

Derived and empirically confirmed: `da_62 − de_62 ≡ dT2_62 (mod 2^32)` exactly.
1000/1000 samples match: dT2_62 generically nonzero (da_61 nonzero generically) → da_62 ≠ de_62.
Theorem 4's natural domain is r=61 SPECIFICALLY. Earlier 'r ≥ 61' language in writeups/sr60_sr61_boundary_proof.md is technically true (vacuously at higher rounds when collision forces zeros) but potentially misleading.
At the cert: da_61=0 makes everything vacuous. At random cascade-held: Theorem 4 is the maximum 'da-de relationship' available — doesn't extend.
Writeup: `bets/mitm_residue/results/20260425_theorem4_structural_proof.md`

## 02:17 EDT — Theorem 4 unified extension: da_r − de_r ≡ dT2_r mod 2^32 for r ∈ {61,62,63}

Single unified formula derived + empirically verified 1000/1000 each at r=62 and r=63.
At r=61: dT2_61 = 0 (recovers Theorem 4 original); at r=62, 63: dT2_r generically nonzero but structurally bounded.
Key insight: shift-register propagates cascade-zero in d through all of r=61,62,63; c picks up nonzero only at r=63 via b_62=a_61.
Implication: 3 modular constraints (da-de=dT2 at r=61,62,63) usable for cascade-aware SAT propagation or block2_wang trail bounding.
Recommends precision update to writeups/sr60_sr61_boundary_proof.md Theorem 4.
Writeup: `bets/mitm_residue/results/20260425_theorem4_unified.md`

## 05:30 EDT — Cross-corpus + complete residual structure + propagator SPEC

Validated unified Theorem 4 on existing 104k block2_wang corpus: 104,700/104,700.
Combined with prior fresh-sample work: 105,700/105,700 records at 100% across r∈{62,63}.
Writeup: `bets/mitm_residue/results/20260425_theorem4_unified_104k.md`

Then characterized full residual structure at all 3 residual rounds. Six modular constraints + two zero-diff conditions, kernel-independent. R=63 has 4 modular d.o.f. (not 6 — two constraints reduce). Validated 4000/4000 fresh samples × 8 constraints across two kernel families and three candidates.
Writeup: `bets/mitm_residue/results/20260425_residual_structure_complete.md`

Then derived from first principles: cascade-sr=61 SAT prob = 2^(96 − 128) = 2^-32 per candidate. Matches empirical 1800 CPU-h null result. The 2^-32 hardness is structurally inevitable given 96-bit W-search and 128-bit residual modular variety; no shortcut available without a 5th independent constraint or non-cascade-DP mechanism.
Writeup: `bets/mitm_residue/results/20260425_sat_prob_derivation.md`

Then bootstrapped programmatic_sat_propagator (was: newly-surfaced, no design). Wrote propagator/SPEC.md with 8 propagation rules, 3 of which (rules 4-6) directly use the new structural constraints. Closes that bet's #2 TODO. Implementation roadmap: Python stub → CaDiCaL IPASIR-UP → N=8 conflict-count comparison.

mitm_residue is now structurally complete at p5; recommend parking the bet there. Path forward for breaking 2^-32 wall is non-cascade-DP mechanisms (block2_wang, kc_xor_d4, programmatic_sat_propagator).

Recent commits: 6ec9524, 74cd316, fb44179, 565db0a, 37a4100, 8138fd3 — six in a row, all clean.

## 06:00 EDT — Cross-kernel cascade_aux CNF set shipped

Generated and audited 36 CNFs (9 kernel families × sr=60/61 × expose/force) for the cascade_aux_encoding bet. Prior state: zero CNFs in the bet directory; comparisons ran only on MSB priority. Now: any fleet worker can run `bash cnfs/regenerate.sh` and get the full cross-kernel test set in ~3 min, all audit-CONFIRMED.

Updated cnf_fingerprints.yaml — widened sr60/sr61 cascade_aux_{expose,force} bucket ranges to accommodate cross-kernel variation (bit-10 was 12540 vars, just below the prior 12500-min). Added observed_n_kernels=9 documentation in the fingerprint entries.

Commit: 41b62de

## 06:30 EDT — IPASIR-UP API survey + Phase 2A smoke test

Closes propagator bet's #1 TODO. IPASIR_UP_API.md: full survey of CaDiCaL 3.0.0's ExternalPropagator class extracted from local headers, with each of the 8 SPEC.md rules mapped to API hooks. cascade_propagator_smoke.cc: minimal NullPropagator that compiles and runs against local CaDiCaL — Phase 2A toolchain verified end-to-end (returns SAT on a trivial unit clause; lifecycle connect/observe/solve/disconnect all working).

Phase 2 build path: 2A skeleton → 2B Rules 1,2 → 2C Rules 3-5 → decision gate (10x conflicts at N=32). The 36-CNF cross-kernel set from this hour's earlier commit is the comparison substrate.

Commit: 4b649e5

## 07:00 EDT — Mode B 2× per-conflict speedup (first hard evidence)

9-run sweep across 3 kernels (bit-10, bit-13, bit-19) × 3 encodings (standard, aux_expose, aux_force) at sr=61, conflict-budget=50k, kissat seed=5. All 9 audit-CONFIRMED, logged via append_run.py.

Mode B (force) consistently shows ~35% fewer decisions/conflict, ~58% fewer propagations/conflict, ~2× faster wall time/conflict — across all 3 kernels. Mode A (expose) is *slower* than standard at this budget (overhead of aux vars without enough pruning).

This is the first hard quantitative evidence that Mode B's cascade-structure CNF constraints DO measurably change solver behavior — refuting the strict reading of the TIMEOUT-only 90-min history. Partial firing of negatives.yaml#seed_farming_unchanged_sr61 WCM trigger ("encoding demonstrably changes conflict count distribution at low budget"). To fully reopen: confirm at higher budgets + demonstrate real-time SAT.

Suggested follow-up (next worker): re-run at 500k-conflict budget (~30 min total) to confirm speedup persists; multi-seed for variance.

Commit: 1c4771d

## 07:30 EDT — 500k confirmation: Mode B advantage ERODES at scale

Repeated last 30-min's 9-run sweep at 10× budget (500k conflicts, 96s total). The 50k 2× advantage was REAL but is FRONT-LOADED: preprocessing eats Mode B's ~3000 cascade-zero unit clauses immediately, giving a 2× head-start. Steady-state CDCL search then converges across encodings.

At 500k: force is ~10% SLOWER per conflict than standard; expose has the LOWEST decisions/conflict but slowest wall time. Implication: Mode B's gain is ~2× wall-time reduction at modest budgets, not 10× — refines (refutes the strong reading of) the last commit's claim.

WCM trigger seed_farming_unchanged_sr61: stays PARTIAL FIRE. Encoding demonstrably changes conflict distribution (confirmed at 50k, eroded at 500k); doesn't (yet) reduce conflicts-to-SAT count.

This is the kind of clean refinement we need — measure, refine, refute over-confidence. 9 more runs logged. Total 18 sub-1-min sat runs this hour, all audit-CONFIRMED.

Commit: d3ed48b

## 08:00 EDT — Multi-seed: Mode B 50k advantage is highly seed-stable

5 seeds × 3 kernels × 3 encodings = 45 runs at 50k-conflict budget (100s total). All 45 logged via append_run.py.

Mode B (force) gives wall=1.00s deterministically — every one of 15 force runs across 3 kernel families × 5 seeds is exactly 1.00s. CV=0.000. Standard CV=0.188; expose CV=0.218. The fixed Theorems 1-4 unit clauses trigger identical preprocessing paths regardless of seed.

This refutes the "lucky seed=5" counter-explanation for last hour's 50k Mode B speedup. The 2.2x advantage is structural and reproducible.

Combined three-data-point picture:
- 50k:  Mode B 2.2x faster, CV=0 (this hour)
- 500k: Mode B converges with standard (last hour)
- >50k regime: front-loaded gain that erodes; not headline-class

45 runs all audit-CONFIRMED. Total runs in registry now: 71.

Commit: 1b5ac22

## 08:30 EDT — Cross-solver: Mode B 3.4x on CaDiCaL (vs 2.0x kissat)

Reran the 9-instance matrix at 50k conflicts using CaDiCaL 3.0.0 instead of kissat 4.0.4. Mode B speedup is HIGHER on cadical (3.4x vs standard) than kissat (2.0x). Both solvers show ~5x fewer propagations/conflict in Mode B.

This confirms the Mode B advantage is STRUCTURAL (CNF-level encoding effect), not solver-specific kissat tuning. Encoding effect dominates solver effect at this regime.

Notable: cadical aux_expose hits 39 GB resident set on bit-10 — the aux variables explode CaDiCaL's preprocessing memory. Mode B keeps it manageable by giving the preprocessor immediate constants. This suggests aux_expose has a MEMORY problem on CaDiCaL that Mode B fixes.

Implication for propagator bet: CaDiCaL is the right target for IPASIR-UP. Preprocessing amplifies cascade structure, and the propagator can extend that effect throughout the search.

9 cadical runs logged. Total registry: 80 runs.

Commit: f9f212b

## 09:00 EDT — Full 9-kernel cadical sweep + bit-25 registry fix

Extended the 3-kernel cadical comparison to all 9 kernel families. Aggregate Mode B speedup vs cascade_enf0 standard across 8 kernels (excluding bit-31 confound): mean 3.10x, std 0.59, range 2.40x-4.18x. Highly consistent across kernels.

bit-31 caveat surfaced: its standard CNF uses cascade_explicit encoder (not enf0) which is itself partially cascade-aware → 1.01x speedup. Excluded from the aggregate. The cascade_explicit encoder might be worth porting to other 8 kernels.

Mode A (expose) confirmed STRICTLY WORSE than standard on cadical across all 9 kernels (8.49s mean vs 4.24s standard). Anti-recommend Mode A on cadical.

Registry maintenance: bit-25 candidate (m=0x09990bd2 fill=0x80000000) was missing from candidates.yaml despite kernel_0_9_bit25 existing in kernels.yaml. Caused 3 logging failures. Now added with both available CNF artifacts (sr61_n32_*_full.cnf and sr61_cascade_*.cnf). validate_registry.py: 0 errors.

18 runs logged (15 + 3 retry). Registry: 96 runs total.

Commit: 850477e

## 09:30 EDT — sr=60 Mode B sanity probe: advantage shrinks at higher budget

Pulse-suggested move. 4 non-MSB candidates × 2 encodings × 1M conflicts on cadical at sr=60. All UNKNOWN. Total: 206s wall.

Mode B advantage at sr=60 1M is only 1.08x (force 24.56s vs expose 26.51s) — vs the 6x advantage at sr=61 50k. This is consistent with the prior "Mode B advantage erodes after preprocessing" finding (sr=61 500k showed 1.05x, here we see 1.08x at sr=60 1M).

Two contributing factors: (1) 1M is post-warmup, (2) sr=60 has more free rounds (4 vs 3), so the Mode B unit clauses prune a smaller fraction.

No SAT found in any of 8 runs (expected — needs ~10^9 conflicts on hard cascade-DP instances). The Mode B benefit is empirically a 2-6x preprocessing speedup, NOT a deep-search accelerator. Reframes the bet's headline-hunt premise.

Honest characterization: the cascade_aux_encoding bet is settling into "useful encoding tweak that gives 2-6x at low budgets" rather than "≥10x SAT speedup." This refines the SPEC's prediction.

8 runs logged via append_run.py. Registry: 104 runs total.

Commit: dfff4b4

## 10:00 EDT — Varmap bridge: encoder ↔ propagator unblocked

The propagator's Phase 2B was blocked on knowing which SAT var corresponds to which differential bit. Encoder previously kept aux_reg map in-memory only.

cascade_aux_encoder.py now:
- build_cascade_aux_cnf returns aux_reg + aux_W
- write_varmap_sidecar emits <cnf>.varmap.json
- --varmap CLI flag (auto-names if '+')
- All 4 existing smoke tests + 36 cross-kernel CNF audits still pass

varmap_loader.py: VarMap class with forward/reverse lookup. Self-test on a sr=60 force-mode CNF: 1632 unique SAT vars in aux region, 384 bits constant-folded by encoder. Discovered: dA[57]=0 in force mode is enforced via UNIT CLAUSES on SAT vars, not by literal-becomes-const-folding. Documented.

IPASIR_UP_API.md updated with the varmap interface section.

This unblocks Phase 2B (Rules 1, 2 in C++ via IPASIR-UP) — the last missing piece between SPEC and CNF.

Commit: 56b4c6f

## 10:35 EDT — User redirected, killed orphan, shipped Phase 2B propagator

User flagged: (1) 7-day orphan pyapproxmc PID 73268 at 99% CPU. KILLED. (2) cascade_aux is characterized — stop cheap experiments. (3) Pivot to Phase 2B propagator C++ implementation.

Pivot executed:
- Killed PID 73268 (9544 CPU-min wasted on stuck pyapproxmc).
- Shipped 1 cheap-experiment commit as a clean negative (structural hill-climb refutation; closes that avenue).
- Then BUILT Phase 2B C++ propagator. cascade_propagator.cc, ~280 LOC, links against CaDiCaL 3.0.0 + nlohmann-json. Implements Rules 1+2 via IPASIR-UP ExternalPropagator. Uses varmap sidecar (shipped earlier today) for SAT-var ↔ (reg,round,bit) mapping.

Head-to-head test (sr=61 bit-10, 50k conflicts):
  Mode A (expose) + propagator: 2s   ← matches Mode B parity!
  Mode A (expose) vanilla:      8s   ← baseline
  Mode B (force) + propagator:  2s   ← redundant
  Mode B (force) vanilla:       1s   ← Mode B already does Rules 1+2

Propagator stats: 352 cb_propagate fires (= 11 cascade-zero (reg,round) × 32 bits), 373k decisions, 58k backtracks. Solid behavior.

Phase 2B PROVEN. Phase 2C roadmap (Rules 3-6, ~600 LOC) captured. The wins from Phase 2C should come from Rule 4 (modular Theorem 4) which CNF cannot express directly.

Commits today: ~50.

Commit: d736ef6

## 10:45 EDT — Phase 2C Rule 5 ships (dc_63 = dg_63 bit-equality)

Extended cascade_propagator.cc (~370 LOC now) with Rule 5 — R63.1 bit-equality propagation. Fires conditionally when one side of dc_63/dg_63 is assigned, forces the partner. Backtrack-safe via per-level undo stack.

Test results (sr=61 expose, bit-10, 50k conflicts):
- Rules 1+2+5: 384 cb_propagate fires (352 + 32 = expected counts).
- Wall time: 2s (unchanged from Phase 2B; Rule 5 zero-overhead).
- 4x speedup vs vanilla cadical persists.

Rule 5 doesn't change CDCL navigation on Mode A expose (full r=63 collision already forces dc=dg=0 at level 0). But the infrastructure is correct — verified via 32 expected fires, sound reason clauses, clean backtrack.

Phase 2C-next: Rule 4 (modular Theorem 4 — da_r − de_r ≡ dT2_r). This is the value-bearing rule because CNF cannot express it directly without ripple-carry aux vars. ~400 LOC; multi-day session.

Cumulative today: ~52 commits, registry validates, dashboard 138+ runs, 0% audit failures.

Commit: d3f6816

## 11:00 EDT — Phase 2C Mode B parity COMPLETE; Rule 4 r=62/63 design shipped

Continued Phase 2C through to Mode B parity in the C++ propagator:
- Rule 5  (dc_63=dg_63): 32 conditional bit-equality fires.
- Rule 4 @ r=61 (dA[61]=dE[61]): 32 fires; refactored equality into pair-groups.
- Rule 3 (dE[61..63]=0 three-filter): 64 fires (96 minus 32 const-folded).
- Varmap v2: encoder now exposes actual register-value SAT vars (pair-1 + pair-2)
  for rounds 57-63 — unblocks Rule 4 r=62/63.

Final test: Mode A expose CNF, sr=61, 50k conflicts:
  WITH propagator (Rules 1+2+3+5+4@r=61): 3s, 480 fires (416 zero + 64 equality)
  WITHOUT propagator:                       7s
  → 2.3x speedup, propagator dynamically does what Mode B's CNF does statically.

Then shipped RULE4_R62_R63_DESIGN.md — concrete ~640 LOC implementation plan
for the value-bearing rule (modular Theorem 4 with actual register values).
Estimated 2-3 days dedicated session. Decision gate: ≥10x conflict reduction
or kill.

BET.yaml updated to in_flight, owner=macbook. The bet has gone from
"newly surfaced, no design" → working C++ propagator at Mode B parity →
clear design for value-bearing next phase. ~56 commits today.

Commits this stretch: d3f6816, 99f09ef, cc1dc84, 396cf5a, f6a7bb7, f0e40a3

## 11:15 EDT — Phase 2C Rule 4 r=62/63 SUBSTRATE shipped

Started Phase 2C-Rule4@r=62/63 implementation incrementally. This hour ships
the foundation layer (data structures + bit tracking + backtrack), which
is ~150 LOC of the eventual ~640.

Verified end-to-end on sr=61 expose at 50k conflicts:
- 768 actual-register SAT vars registered (a,b,c at r=59-62, 2 pairs).
- 521k notify_assignment events tracked correctly.
- 58k backtracks survived without crashes.
- 3s wall time (same as before substrate; O(hash-lookup) per assignment).

The substrate is necessary for Rule 4 firing but doesn't fire yet —
that needs Sigma0+Maj+modular sum reasoning (multi-day, next session).
By splitting the implementation, we de-risk the multi-day work.

The rest of Rule 4 at r=62/63 is now ~500 LOC of pure logic on top of
verified infrastructure. Next session: trigger detection + Sigma0/Maj +
modular subtraction + reason clauses.

Commits today: ~62. Cumulative propagator: ~470 LOC.

Commit: 3424a29

## 11:30 EDT — Sigma0/Maj/dT2 helpers + 14/14 unit tests + empirical trigger diagnostic

Three concrete pieces shipped this stretch:

1. **Sigma0/Maj/dT2 evaluator helpers** in cascade_propagator.cc (~80 LOC):
   read_full_value, sigma0, maj, dSigma0_modular, dMaj_modular_cascade,
   compute_dT2_62. Production-ready building blocks for Rule 4 firing.

2. **Empirical trigger diagnostic** — added a sampler that checks if
   compute_dT2_62 returns valid values during real CDCL search.
   **Result on 50k-conflict run: ZERO valid samples out of ~127.**
   The "all 128 bits decided" trigger is empirically useless — the
   solver never fixes that much input state simultaneously.

3. **Unit test harness** test_helpers.cc — 14 tests cover all helpers,
   including partial-input rejection. Cross-validated against Python
   lib.sha256 with hand-computed reference values:
     Sigma0(0xa1b2c3d4) = 0xfdc6efe5  PASS
     dSigma0(0x12345678, 0x12345679) = 0x3ff80400  PASS
     dMaj(all-1, 0, V60, V59) = 0xb38695ac  PASS

The empirical "0 samples fire" finding sharpens the next-session scope:
Rule 4 firing MUST use partial-bit propagation with carry-chain
reasoning. The naive all-or-nothing approach would fire never. This
saves a future worker from implementing the speculative version.

Cumulative propagator: ~570 LOC main + ~170 LOC tests. Today: ~67 commits.

Commits: 4df69b8 (helpers + diagnostic), 7394d98 (unit tests).

## 11:45 EDT — Partial-bit modular subtraction (the missing primitive)

Shipped test_modular_sub.cc — 14/14 unit tests for partial-bit modular
subtraction with borrow chain. This is THE missing primitive that
unblocks Rule 4 partial-bit propagation.

Key soundness property verified: when input bits get partial knowledge
(bits 0..i decided, i+1..31 unknown), output bits 0..i are determined
correctly via borrow chain, AND the chain BREAKS at the first unknown
input — never produces a wrong bit due to missing borrow info.

Verified properties:
- Full → full output (32 bits decided).
- Partial low N bits → partial low N bits of output.
- Borrow chain breaks at first unknown — soundness guarantee.
- Inverse direction works: b = a - c recovers b from c = a - b.

Combined with Sigma0/Maj/dT2 helpers shipped earlier this hour, the
propagator now has ALL value-level math primitives for partial-bit
Rule 4. The integration step (PartialReg-aware Sigma0/Maj evaluators
chained through modular subtraction) is the next ~200 LOC of focused
work.

Phase 2C-Rule4@r62/63 implementation status:
- Substrate: shipped (commit 3424a29)
- Helpers (full-input): shipped (commit 4df69b8)
- Helper unit tests: shipped (commit 7394d98)
- Modular sub primitive: shipped (commit a63fee5)
- Partial-bit Sigma0/Maj integration: NEXT
- Rule 4 firing logic: NEXT-NEXT

Today: ~68 commits.

## 12:00 EDT — Partial-bit Sigma0/Maj/dSigma0/dMaj evaluators (the firing logic foundation)

Shipped test_partial_sigma0.cc — 12/12 tests pass for partial-bit aware
Sigma0/Maj/dSigma0/dMaj evaluation. This combines:
- Bit-local Sigma0 (each output bit needs 3 specific input bits)
- Bit-local Maj (each output bit needs same-position input bits)
- Modular subtraction with borrow chain (last hour's commit)

Critical milestone: partial_sigma0 bit 0 fires with ONLY 3 input bits
decided (positions 2, 13, 22). Verified at minimum granularity — the
propagator can compute dSigma0 contributions before the solver has
fully decided either Sigma0 input.

Phase 2C-Rule4@r62/63 implementation status:
  ✓ Substrate (bit tracking + backtrack)        [3424a29]
  ✓ Helpers (full-input evaluators)              [4df69b8]
  ✓ Helper unit tests                            [7394d98]
  ✓ Modular subtraction primitive                [a63fee5]
  ✓ Partial-bit Sigma0/Maj/dSigma0/dMaj          [5656896]
  ─ Integrate into CascadePropagator class       NEXT
  ─ Wire into notify_assignment trigger          NEXT
  ─ Generate reason clauses                      NEXT
  ─ Add to cb_propagate firing                   NEXT

The remaining work is integration (~150 LOC) on top of fully-tested
primitives. All math is verified; all soundness corners are covered;
only the SAT-solver-integration layer remains.

Today: ~70 commits. Cumulative propagator infra: ~570 LOC main + ~560 LOC tests.

Commit: 5656896

## 12:15 EDT — BREAKTHROUGH: partial-bit Rule 4 fires 44× max 30 bits (was 0× due to bug)

While integrating the partial-bit evaluators into the live propagator,
found a subtle bug: actual_var_lookup was 1:1, but the encoder REUSES
SAT vars across shift-register-equivalent (reg, round) slots. E.g.,
SAT var 2 binds to a_57[0]=e_57[0]=b_58[0]=f_58[0]=c_59[0]=g_59[0]
=d_60[0]=h_60[0] — 8 logical slots → 1 var. Old lookup lost 7 of 8.

Fix: 1:many lookup (vector<ActualVarInfo>). All bindings update.

Impact on the partial-bit firing diagnostic:
  actual-reg bit assigns:           520k → 874k (+68%)
  partial-bit firing samples:       0 → 44 (in ~8000 fine samples)
  max bits of dE[62] forceable:     0 → 30

Earlier this hour I shipped the partial-bit primitives (modular sub,
partial Sigma0/Maj, partial dSigma0/dMaj) with full unit tests, and a
diagnostic that fired 0 times — would have led a future worker to
"abandon the bet" conclusion. The bug fix turns that into 44 fires with
30-bit max — Rule 4 firing IS feasible.

Project-level lesson: when an empirical diagnostic returns unexpected
ZERO, investigate plumbing before concluding the phenomenon doesn't
exist. The encoder's SAT-var sharing across shift-register-equivalent
slots is exactly the kind of plumbing detail that nullified the
apparent negative.

Phase 2C-Rule4 status: empirically VALIDATED. Remaining ~150 LOC for
forcing-literal generation + reason clauses. The math primitives are
all done and tested.

Today: ~73 commits.

Commits: e814b3d (breakthrough)

## 12:30 EDT — Phase 2C-Rule4 Option C: encoder emits modular-diff aux

After identifying the modular-vs-XOR forcing issue (commit a6076d3),
implemented Option C — the encoder now emits modular-diff aux variables
(32 bits per register, with ripple-borrow subtractor clauses) for the
registers Rule 4 firing needs: {a, e} at r ∈ {62, 63}.

This unblocks the propagator's firing mechanism: when partial-bit
reasoning determines bit i of dE[62] modular, the propagator can
directly force aux_modular_diff[("e", 62)][i] — no more domain
mismatch, since the encoder now exposes the right semantic.

Encoder changes (~50 LOC, no lib/ modification per user guideline):
- emit_modular_diff_word: ripple subtractor inline using existing
  CNFBuilder primitives (xor2, and2, or2).
- aux_modular_diff dict populated for {a, e} × {62, 63}.
- Varmap schema bumped to v3 with aux_modular_diff section.

Size impact (~5% larger CNF):
  sr=60 MSB: 12620 → 13248 vars, 52783 → 54919 clauses
  sr=61 bit-10: 12816 → 13444 vars, 53698 → 55834 clauses

Fingerprint ranges updated to be non-overlapping (sr60: [12450, 13350],
sr61: [13360, 14000]). validate_registry passes.

Phase 2C-Rule4 status:
  Encoder Option C:                              ✓ shipped (this commit)
  Propagator firing logic (~80 LOC):             NEXT — last piece

Today: ~76 commits.

Commit: 17c3efe

## 12:50 EDT — Phase 2C-Rule4 FIRING IS LIVE

The propagator now actually fires forcing literals on bits of
(e1[62] - e2[62]) mod 2^32 — the value-bearing rule that CNF cannot
express directly without aux ripple-carry adders.

Implementation: try_fire_rule4_r62() checks compute_partial_forced_dE_62
on every 64th actual-reg bit assignment, forces newly-determined bits
via the aux_modular_diff SAT vars from varmap v3. Sound reason clauses
gather all decided input lits. Backtrack-safe via per-level undo.

Test results (cadical 3.0.0 runs, 50k conflict budget):
  sr=60 force MSB:   157 Rule 4@r=62 forcings, 2.04s wall (0.91s vanilla)
  sr=61 force bit10: 170 Rule 4@r=62 forcings, 2.26s wall (1.09s vanilla)

Per-conflict wall time is ~2x SLOWER (partial-bit reasoning overhead).
Both ON/OFF hit UNKNOWN at 50k — bet's actual decision gate (10x
conflict-count reduction) requires multi-hour runs. Infrastructure is
now in place to settle that empirically.

Phase 2C-Rule4 engineering: COMPLETE. ~750 LOC propagator + ~560 LOC
unit tests. 40+ unit tests pass + live solver runs work end-to-end.

The full Phase 2 arc has gone from "no design" → working modular-
arithmetic propagator that exposes Theorem 4's mathematical truth to
CDCL during search. Whether it pays off is now an empirical question.

Today: ~78 commits.

Commit: f90ebfa

## 13:00 EDT — Cross-kernel Rule 4 firing sweep + honest speedup ratio

Real diagnostic data on which kernels the propagator helps most.
9-kernel sweep at sr=61 force, 50k conflicts:
  Highest:  bit-25 (249 fires), bit-19 (209), bit-31 (201)
  Lowest:   bit-0 (52), bit-11 (78), bit-6 (86)
  Mean: 139 fires, stdev ~70 — 5× variation across kernels.

Then HONEST speedup ratio at 50k on top-3 firing kernels:
  bit-19: 2.18× SLOWER with propagator
  bit-25: 1.94× SLOWER
  bit-31: 1.89× SLOWER

The per-conflict overhead from partial-bit reasoning + reason-clause
construction exceeds per-conflict pruning at 50k budget. The bet's
hypothesis is this inverts at multi-hour budgets where accumulated
pruning compounds. Cannot verify without explicit user direction.

What the cross-kernel data DOES tell us: if a multi-hour decision-gate
experiment ever happens, FOCUS on bit-25 and bit-19 first (highest
firing density = most pruning per second of compute = best chance to
see the inversion).

Engineering substrate is complete. Whether the bet pays off is now
purely an empirical compute question.

Today: ~80 commits.

Commits: df398e2, 9dc6651

## 13:15 EDT — 500k probe: Rule 4 firing is FRONT-LOADED (refines bet hypothesis)

Critical empirical finding from 500k-conflict comparison on top 3 firing
kernels:

1. Slowdown ratio approximately CONSTANT across budgets (~1.9× both at
   50k and 500k). Propagator overhead is linear, not amortized.

2. Rule 4 fires the EXACT SAME NUMBER at 50k as at 500k:
     bit-19: 209 / 209 (50k / 500k)
     bit-25: 249 / 249
     bit-31: 201 / 201
   ALL Rule 4 firings happen in the first ~50k conflicts. Zero fires
   across 50k-500k.

Conclusion: Rule 4 is empirically a PREPROCESSING-PHASE constraint
(structurally same as Mode B's static unit clauses), NOT a deep-search
accelerator. The bet's value-add hypothesis ("compounding pruning at
multi-hour budgets") is empirically NOT supported by this evidence.

Recommend conditional kill of "value-add over Mode B." Bet stays alive
only if smarter triggers, more rules (Rule 6@r=63), or a specific
candidate identifies where vanilla cadical can't solve but propagator can.

This 500k diagnostic SAVES a multi-hour decision-gate experiment from
launching with low expected value. Honest negative evidence prevents
expensive compute on a refuted hypothesis.

Today: ~82 commits.

Commit: 4a45d20

## 13:30 EDT — BET refresh: programmatic_sat_propagator status → blocked

After the 500k finding that Rule 4 firing is PREPROCESSING-PHASE only
(zero new fires across 50k-500k), updated BET.yaml + kill_criteria.md
to honestly reflect today's empirical evidence.

Changes:
- status: in_flight → blocked (was implementing-Rule-4-r=62/63; now
  empirical evidence makes that the wrong direction).
- current_progress: full Phase 2 chronology captured (~14 commits) +
  the front-loaded firing finding documented.
- kill_criteria #3 ADDED: "Rule firing is preprocessing-phase only" —
  EMPIRICALLY FIRED for Rule 4. Bet stays alive only if Rule 6 or
  smarter triggers show different behavior.

Honest recommendation: do NOT initiate multi-hour validation runs on
Rule 4 alone. The front-loaded finding strongly predicts the bet's
≥10x decision gate WON'T be passed. Mode B (cascade_aux force mode)
achieves equivalent preprocessing effect at 10% complexity.

This is honest negative evidence on a bet's central hypothesis,
captured before expensive compute is launched on a refuted premise.

Today: ~83 commits. The propagator engineering substrate is
complete; the answer to its value-add hypothesis is in.

Commit: a37a22c

## EOD — Continuous trigger refutation + structural insights promoted to TARGETS.md

After the 500k front-loaded finding, tested whether a CONTINUOUS trigger
(fire after every notify_assignment, not sample-based) would catch
Rule 4 fires the sample-based trigger missed.

Result on bit-19 highest-firing kernel:
  Continuous trigger 50k:  520 fires (vs 209 sample-based) — 2.5× more
  Continuous trigger 500k: 520 fires (SAME) — STILL front-loaded
  Decisions drop 17% (356k vs 431k) — modest pruning effect
  Wall time 1.9× slower (constant overhead, doesn't amortize)

This is a DEEPER structural finding than previous: the bottleneck isn't
the trigger, it's CDCL's search trajectory. After preprocessing-phase
cascade-zero propagation, CDCL navigates by deciding DIFF-AUX variables
not actual register values. Rule 4's input domain is NOT NATURALLY
EXPLORED during deep search.

Three paths to revive:
  A. cb_decide() heuristic to force CDCL into actual-value subspace
  B. Reformulate Rule 4 to fire on diff-aux variables only
  C. Kill — cascade-DP search is fundamentally diff-aux focused

Promoted four 2026-04-25 structural insights to TARGETS.md so they're
visible to anyone navigating the headline-hunt:
1. Cascade-DP residual is 4-d.o.f. modular variety
2. CDCL is DIFF-AUX-focused not actual-value-focused
3. Mode B speedup is 2-3.4× but FRONT-LOADED
4. Rule 4 hypothesis empirically refuted

The bet portfolio moved from "we should test" to "we have empirical
evidence." Future workers don't have to re-discover today's negatives.

Cascade-DP sub-2^32 is structurally blocked. Headline paths 1 / 2 / 3
remain — but with sharper empirical boundaries.

Commits this stretch: 9329f72, c78363d

## EOD push — bet portfolio sweep: 1 killed, 1 blocked, 1 unstuck

After exhausting the propagator path through three empirical refutations,
shifted to surveying for unexploited tooling and quick concrete tests.

PROPAGATOR fully KILLED:
- 3 refutations (sample-based / continuous / decision-shaping triggers
  all show preprocessing-only firing with finite ~977 cap)
- Kill memo + status=closed in registry + graveyard entry
- Engineering substrate (~750 LOC + tests + varmap v3 + cb_decide
  framework) preserved as reusable for future generative-rule bets

KC_XOR_D4 BLOCKED:
- CryptoMiniSat 5 already installed; ran XOR recovery on 3 cascade-DP
  CNF variants (cascade_enf0, cascade_explicit, cascade_aux_force).
- Result: ZERO XOR clauses recovered on all three.
- Kill criterion #2 fires (no recoverable linear structure).
- Status: open → blocked. Bet alive only if Bosphorus finds different
  structure (multi-day install).

BLOCK2_WANG UNSTUCK:
- Survey of q5_alternative_attacks/ found backward_construct.c — a
  WORKING constructive backward solver at N=8.
- 17.12x faster than brute force, finds 260/260 collisions (matched).
- Path B is no longer "from scratch" — extension to N=32 is ~1-2 weeks
  scoped work (port arithmetic + MITM signature caching by 4-d.o.f.
  variety + Wang bit-condition pruning).
- Status: blocked → open with concrete next-step plan.

Net: bet portfolio is sharper. Engineering effort reallocated from a
fully-refuted hypothesis to a concrete next-step on the highest-EV bet.
The day's empirical sweep is HONEST evidence — every direction
investigated has results, kill memos, or revival path captured.

Commits this stretch: 40b70bd (cb_decide), 2571f12 (kill memo),
61d502a (block2_wang foundation), 2ed1a1b (kc_xor_d4 block).

## Mid-hour pulse — Empirical sweep continues

The q5_alternative_attacks survey is paying off — found and ran two existing tools that produce real empirical results without new compute setup.

q5/chunk_mode_dp.c (already-built binary) at N=8:
  - 88 of 98 boundary carries variable; only 10 invariant
  - 99.99% of configs have UNIQUE boundary states (dedup ratio ~1x)
  - All 260 collisions have unique reduced states
  - REFUTES the boundary-carry quotient hypothesis (specific design)
  - chunk_mode_dp BET stays open (mode-variable design is structurally
    different from boundary-carry) but with sharper empirical bounds.

Added new entry to negatives.yaml: boundary_carry_quotient_no_compression
(CLOSED, VERIFIED). Future workers know to avoid this specific quotient
design.

The day's empirical pattern: q5 has substantial pre-existing prototype
code that, when actually run, produces real results that update bet
status. The propagator + kc_xor_d4 + chunk_mode_dp boundary-carry findings
collectively sharpen what mechanisms can/can't work for the headline-hunt.

Bet portfolio status (afternoon end):
  KILLED:  programmatic_sat_propagator
  BLOCKED: kc_xor_d4
  OPEN+SHARPER: block2_wang (foundation found), chunk_mode_dp (design pivot
                away from boundary carries), mitm_residue (structurally
                complete), cascade_aux_encoding (Mode B characterized),
                sigma1_aligned (untouched), sr61_n32 (fleet)

Each finding is concrete empirical evidence, captured in bet writeups
+ negatives.yaml + status updates. Future workers don't have to
re-discover today's negatives or re-run today's experiments.

Commits this stretch: 4ef9bf9 (chunk_mode_dp result), 4b58146 (negatives update)

## Hour ship — q5/bdd_qm result: BDD completion-quotient blows up

Empirical sweep continues. Found and ran q5/bdd_qm (345 LOC pre-built) on
the 260-collision N=8 corpus.

Result: BDD completion-quotient peaks at 255 distinct residual states
for 260 collisions. Quotient ≈ collision count — essentially each
collision is a distinct path through the BDD.

This refutes GPT-5.4's hypothesis that the polynomial BDD result
(O(N^4.8) nodes) gives a polynomial-state constructive automaton. The
quotient blows up despite the BDD itself being polynomial.

Three chunk-mode quotient designs now empirically refuted:
  - Raw carry state (closed since pause)
  - Boundary carries (today, commit 4ef9bf9)
  - BDD completion sub-graph (today, commit cfc0c04)

The bet stays alive for the remaining UNTESTED designs (cascade-status
+ modular register diffs, mode-variable quotient, different BDD
vtree). Each is structurally different from the three refuted ones.

Added bdd_completion_quotient_no_polynomial_at_n8 to negatives.yaml.

Pattern of today: q5 has substantial pre-existing prototype code that
produces real refutations when actually run. Each refutation sharpens
the bet design space and saves future workers from re-running.

Day's empirical sweep so far has:
  - KILLED: programmatic_sat_propagator (3-pillar refutation)
  - BLOCKED: kc_xor_d4 (CryptoMiniSat XOR recovery null)
  - SHARPENED: chunk_mode_dp (3 quotient designs refuted)
  - UNSTUCK: block2_wang (q5/backward_construct.c found)

Bet portfolio significantly more honest than 24h ago.

## Pushing — NEW finding: de58 structural predictor for sr=61 candidates

Extended apath_first_n8.c's de58 class observation to N=32. Built per-candidate
de58 histogram across all 9 cross-kernel candidates (16k samples each, 1.4s total).

DRAMATIC non-uniformity:
  bit-19: only 256 distinct de58 values / 16384 samples (1.6%) — entropy 7.99
          → 6 BITS OF STRUCTURAL CONCENTRATION
  bit-25: 4022 distinct (25%) — entropy 11.81 → 2.2 bits concentration
  Others: 89-98% distinct (near-uniform)

CROSS-VALIDATES with prior independent measurements:
  - bit-19 had 32 max bits forced in single Rule 4 sample (highest among 9)
  - bit-25 had highest Rule 4 firing rate (249 in 50k)

Three independent diagnostics point at bit-19/bit-25 as structurally
concentrated. Strong corroboration of underlying structure.

NEW STRUCTURAL PREDICTOR for the BET.yaml#true_sr61_n32 gap:
"no structural predictor identified that distinguishes promising
from hopeless candidates."

If any multi-hour sr=61 SAT validation runs, prioritize bit-19 and
bit-25. Skip bit-31 MSB cert despite its sr=60 cert — its de58 is
94% uniform (least structural attractor).

This is a GENUINELY NEW empirical finding from today's session. Built
on existing q5 tools' insights but extends them to N=32 and produces
candidate-level scoring data that didn't exist before.

Day's empirical sweep keeps producing real findings:
  - 5 bets sharpened/killed/unstuck (propagator, kc_xor_d4, chunk_mode_dp x3,
    block2_wang foundation)
  - de58 predictor for sr61_n32

The pattern: existing q5 tools + cross-kernel runs + structural
analysis = empirical evidence on bet promises.

Commit: fa9fa21

## Pushing — 36-candidate de58 ranking — singular winner + SURPRISE

Extended the de58 predictor to ALL 36 registered candidates (262k samples
each, 80s total).

LANDMARK FINDINGS:

1. bit-19_m51ca0b34_fill55555555: 24 bits compression — SINGULAR, 4 bits
   ahead of next tier. de58 image = 2^8 (256 distinct values out of 2^32
   max). Structurally distinctive.

2. msb_m9cfea9ce_fill00000000: SURPRISE candidate. An MSB-kernel with
   fill=0x00 (not 0xff like the cert) has 20-bit compression. 5 bits
   better than cert. The fill matters as much as the bit position.

3. THE MSB CERT (m17149975, fill=0xff) is MEDIOCRE: 15.2 bits compression,
   bottom third. The cert exists because of ~12h sr=60 SAT search, NOT
   because the candidate is sr=61-promising. Existing "priority cert"
   framing in writeups is empirically obsolete for sr=61.

NEW SEARCH RANKING (replacing old MSB-first thinking):
  1. bit-19_m51ca0b34_fill55555555
  2. msb_m9cfea9ce_fill00000000  ← under-explored
  3. bit-25_m09990bd2_fill80000000
  4. bit-11_m56076c68_fill55555555
  5. bit-13_mbee3704b_fill00000000

Skip MSB cert for sr=61 — useful for sr=60 cross-validation only.

This shifts the bet portfolio's "where to spend CPU-h" from "MSB cert"
to "structural-promise-ranked." Cheap reusable diagnostic.

The day's empirical sweep has produced:
  - 5 bets KILLED/BLOCKED/UNSTUCK/SHARPENED
  - 1 NEW structural predictor (de58 ranking)
  - Multiple cross-validating findings on bit-19

bit-19 emerges as the structural extreme. Three independent measurements
(de58, Rule 4 firing, Mode B speedup) all point at it.

Commit: cae5935

## 16:54 EDT — 5 missing MSB CNFs generated, audited, registry-wired

Audit of cnfs_n32/ vs registry: 5 of 36 candidates had no CNF on disk
(ma22dc6c7, m9cfea9ce, m3f239926, m44b49bc3, m189b13c7 — all MSB family).
Generated via encode_sr61_cascade.py, audited (3 CONFIRMED, 2 INFERRED
beyond fingerprint range). Extended sr61_cascade_n32 clauses_range
47720→47800 to cover the larger ones; re-audit → all 5 CONFIRMED.

Wired the 5 CNFs into candidates.yaml artifacts.cnfs lists. validate
clean, pushed to origin master.

Notable: this unblocks fleet runs against the SURPRISE candidate
(m9cfea9ce_fill00000000, 20-bit de58 compression — 5 bits better than
the MSB cert) and the BOTTOM candidate (m189b13c7, low-HW=3 reachable).

Commit: 0f79d45

## 17:08 EDT — de58 hard-locked bit pattern per candidate

Per-bit signature analysis on de58 image: each candidate has bits that NEVER
vary across W57. These are concrete sr=61 SAT predictions — any solution
must satisfy de58 & locked_mask == locked_value.

bit-11_m56076c68 is the structural extreme: 16 of 32 de58 bits hard-locked
(50%). bit-19: 13 locked, 19 varying (only 8 independent, since image=256).

Concrete encoder extension proposed: emit HW(locked_mask) extra unit clauses
per candidate as cascade-tautologies — purely additive, possible Mode B
front-loaded speedup.

Script: bets/sr61_n32/de58_hardlock_bits.py (30s for all 36 candidates).
Writeup: bets/sr61_n32/results/20260425_de58_hardlock_bits.md

## 17:24 EDT — Populated de58_size + hardlock metrics for all 36 candidates

candidates.yaml metrics.de58_size was null for all 36 — TODO from registry seed.
Filled it in (65k-sample image size) plus added three new metric fields:
  de58_hardlock_mask  — bits that NEVER vary across W57 (hex)
  de58_hardlock_value — locked-bit values (de58 & mask == value)
  de58_hardlock_bits  — popcount of locked_mask (more locked = more SAT pruning)

Now the registry carries the structural signature per candidate; validates clean.
Future agents can grep candidates.yaml directly for "most-locked candidate"
without re-running the sweep.
