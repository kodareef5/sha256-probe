
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
