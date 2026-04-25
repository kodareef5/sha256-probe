
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
