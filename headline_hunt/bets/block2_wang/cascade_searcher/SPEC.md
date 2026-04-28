# Cascade-Equation Searcher — design SPEC v2

**Status**: REVISED v2, 2026-04-28 02:00 EDT (was DRAFT v1, 2026-04-27 23:50)
**Origin**: User framing — "tiny custom solver around the cascade
equations ... standalone reduced-N searcher over the cascade variables
and schedule residues, with aggressive memoization and explicit failure
explanations. If it beats brute force at N=12/14, then decide whether
to integrate with SAT. The goal is to discover a representation, not
beat Kissat immediately."

This SPEC defines the searcher's variables, propagation rules,
memoization key, and failure-explanation format. It does NOT define
SAT integration — that's a downstream decision after the searcher
exists and performs.

## v2 changelog (after F86–F91 empirical work)

The brute-force baseline (F86) and prototype searcher (F88–F91)
empirically tested several v1 design axes. Some held; some did not.

**VALIDATED at small N**:
- **Cascade-filter mechanism (F89)**: enforcing HW(register a, round 60)=0
  narrows the search space 250× at N=8 and 1000× at N=10. The brute-
  force optimum at N=8 (HW=16) IS in the cascade-filter survivor set.
  At N=10, cascade-filter finds HW=19 vs BF global HW=18 — gap of 1 HW.
- **Single-register sufficiency (F89)**: multi-register filters
  (a:60, b:61, c:62, d:63) yield IDENTICAL survivors as a:60 alone.
  SHA-256's register shift propagates the zero forward automatically.
- **Cascade trajectory N-invariance in shape (F88)**: at N=8, the best
  cascade-1 dm produces the same a-zero-at-round-60 + shift-propagation
  pattern as full-N=32 m17149975. The structural cascade is a faithful
  reduction.

**REFUTED (so dropped from v2)**:
- **Forward HW-bound pruning at intermediate rounds (F88)**: HW
  trajectory peaks at round ~52 (HW≈42 at N=8) before converging.
  Forward pruning cannot distinguish "high HW that will converge" from
  "high HW that won't." All three tested threshold curves prune 100%
  of non-trivial dm at N=8.
- **Bit-position algebraic predictor (F90→F91 retraction)**: F90
  claimed the MSB-position-set + LSB-set + bit3-clear gave 2× boost
  at N=8 and was N-invariant. F91 cross-check at N=10 gave 1.06× boost
  (within noise). The bit-position pattern was a small-N artifact.

**OPEN QUESTIONS (v2 punts to future work)**:
- Memoization on intermediate-round state classes — unlikely to help
  given F88's path-dependent HW trajectory, but not directly tested.
- Backward search from target residuals — likely the right direction
  per M16_FORWARD_VALIDATED.md but not yet implemented in the searcher.
- N-scaling of the cascade-filter optimality gap (BF-min minus
  cascade-filter-min): N=8 gives 0, N=10 gives 1, N=12 unknown
  (~50 min wall budget if measured).

---

## Goal

Discover the **right factorization** of cascade-1 search space at
mini-SHA scales (N ∈ {8, 10, 12, 14}). The output we care about is not
"does it beat kissat" but "what state representation does the search
naturally converge on?" That representation is then a candidate for:

- A bespoke CDCL clause encoding (potential aux variable design)
- A bit-conditioning trail-search algorithm
- An IPASIR-UP propagator (the closed `programmatic_sat_propagator`
  bet's natural successor)
- A hand-written branch heuristic for the existing CNF

---

## Problem reduction

For mini-SHA at N bits:
- 16 message words m[0..15], each N bits → message space M_N = 2^(16N)
- Schedule expansion: W[r] for r ∈ [0,63], same expansion as full SHA-256
  with all arithmetic mod 2^N and rotation amounts unchanged
- 8 working registers a..h, each N bits, evolving 64 rounds
- Cascade-1 trigger: dM such that dW at the bottleneck (rounds 57-60)
  zeroes out specific register positions

A **collision** at sr=60 cascade-1 is a pair (M, M') with:
- dW[r] = W[r] XOR W'[r] for r ∈ [0,60] non-trivial
- State diff dA..dH = 0 at round 63

A **near-residual** is the same with non-zero state diff at round 63.
F71 establishes: across 67 cascade-1 cands at N=32, the F32 deep-min
witnesses are universally near-residuals (single-block UNSAT under
cert-pin).

---

## Variables

The searcher's state space is partitioned into three layers:

### Layer 1: Message-difference variables
- `dm[i]` for i ∈ [0,15], each N-bit modular diff
- Domain: dm[i] ∈ {0, 1, ..., 2^N - 1}
- For cascade-1: dm typically restricted to one or two cascade-driving
  positions (e.g., dm[0] only, or dm[0] + dm[9]); the rest forced to 0
- This is the **search axis** — the searcher enumerates over this layer

### Layer 2: Schedule-residue variables (DERIVED)
- `dW[r]` for r ∈ [0,63], each N-bit modular diff
- For r < 16: `dW[r] = dm[r]` (direct)
- For r ≥ 16: `dW[r] = sigma1_N(dW[r-2]) + dW[r-7] + sigma0_N(dW[r-15]) + dW[r-16]` (mod 2^N)
- These are **derived** from layer 1, not searched
- The searcher should expose them in the propagation log to enable
  failure explanations — "the conflict at round R was caused by
  `dW[R]` having an unsatisfiable carry pattern from `dm[i,j,k]`"

### Layer 3: Cascade-state variables (DERIVED)
- `dA[r]..dH[r]` for r ∈ [0,63], each N-bit modular diff
- Round update: standard SHA-256 round, run twice (once on M, once on
  M'), state diff computed
- These are **derived** from layers 1+2 + the m0 anchor (chosen base message)
- The searcher should track these to detect early failure (residual
  too large at round R < 63)

---

## Propagation rules

```
1. Schedule: dW[r] determined from dm[0..15] for r ∈ [0,15];
             dW[r] = sigma1_N(dW[r-2]) + dW[r-7] + sigma0_N(dW[r-15]) + dW[r-16]
             for r ∈ [16,63]. PURELY MODULAR — no branching.

2. Round propagation: for each round r ∈ [0,63]:
       dT1[r] = dH + dSigma1_N(dE) + dCh(dE, dF, dG) + dW[r]
       dT2[r] = dSigma0_N(dA) + dMaj(dA, dB, dC)
       dE_new = dD + dT1[r]
       dA_new = dT1[r] + dT2[r]
       (state shifts: dH←dG, dG←dF, dF←dE, dE←dE_new, dD←dC, dC←dB, dB←dA, dA←dA_new)

   These are MODULAR additions of values DERIVED from XOR-diffs through
   non-linear functions (Sigma, Ch, Maj). The non-linearity is the
   source of CDCL difficulty — the differential propagation is not
   deterministic in dA-input alone (depends on actual a-value too).

   For the searcher: track BOTH dA and a (modular pair). Failure cores
   come from ranges where the (dA, a) pair forces a contradiction.

3. Cascade-1 trigger: at rounds 57-60, the cascade-zero structure
   should hold:
       dA[60..63] = 0
       dE[60..63] = 0
   These are TARGETS, not constraints. If the search reaches round 60
   with non-zero dA[60] or dE[60], it has failed cascade-1. Failure
   explanation: which round did the cascade break, and which message
   bits propagated the contradiction.

4. Collision target: dA..dH = 0 at round 63. If cascade-1 holds
   (rules 3) and the residual at round 63 is also zero, it's a
   verified collision.
```

---

## Memoization key

The natural memoization key is the **state class** at each round:

```
key(r) = (round, hash(dA[r], dB[r], ..., dH[r], dW[r..r+3]))
```

i.e., two search paths that arrive at round r with the same 8-register
state diff and the same upcoming 4-W diffs propagate identically.
Memoize the verdict (UNSAT, near-residual HW, or full collision).

For r ∈ [50, 63] the key is information-rich (8 registers × N bits + 4
W diffs × N bits = 12N bits). For r small (e.g., r ≤ 5), the state diff
is mostly zero so the key collisions cluster.

**Aggressive memoization**: for round r where dA..dH have low Hamming
weight (cascade structure expected), use bit-pattern + position hash
(not full state). Reduces collisions in the memoization table.

---

## Failure explanations

When the search dead-ends at round R with state-diff HW > threshold,
the explanation is the chain:

```
{
  "round": R,
  "verdict": "near_residual" | "infeasible_carry" | "cascade_break",
  "state_at_R": [dA, dB, ..., dH, dW[R..R+3]],
  "trigger_dm_subset": [bit positions in dm that contributed],
  "first_diverging_round": R0  // smallest round where state diff exceeded zero
}
```

The `trigger_dm_subset` is the explanation: "these N bits of dm
together caused the residual HW to grow at round R0, propagating to a
non-recoverable state by round R."

This is the **structural insight** the searcher should produce. Even
without beating brute force on raw speed, a corpus of failure
explanations across enumerated dm patterns reveals which dm-bit
combinations are structurally infeasible — and that's the
representation we want to discover.

---

## Search algorithm — v2 revised (post-F88 + F89)

The v1 algorithm proposed forward HW-bound pruning + state-class
memoization. F88's empirical trace data refuted forward pruning
(HW peaks mid-rounds; cannot distinguish "will converge" from
"won't"). The v2 algorithm uses cascade-filtering instead:

```python
def search(dm):
    # Forward propagate to round 60, recording register a's diff
    state = simulate_to_round(dm, target_round=60)

    # CASCADE FILTER (F89 validated mechanism)
    if hw(state.a) != 0:
        return "PRUNED_NOT_CASCADE_1"   # 250-1000× narrowing

    # Continue propagation rounds 60-63
    final_state = simulate_to_round(dm, start=state, target_round=63,
                                     start_round=60)

    return ("COLLISION" if hw(final_state) == 0
            else f"NEAR_RESIDUAL_HW={hw(final_state)}")
```

**No memoization in v2.** F88 demonstrates HW trajectories are path-
dependent (peak height + convergence depth depend on full dm history).
Intermediate-round state classes don't naturally cluster.

**No bit-position branching heuristic in v2.** F91 retracted the F90
algebraic predictor — the (MSB-set, LSB-set, bit3-clear) pattern was
a small-N artifact. Default to uniform branching over dm.

**Optional v2 enhancement** (untested): once a dm passes the cascade
filter, optionally run a bit-flip local search on neighborhoods to
find lower-HW residuals. Per F87, full-dm-freedom random sampling at
N=4 dropped min HW from 7 (restricted) to 4 (free). Local search
within cascade-1 might further reduce.

---

## Brute-force baseline (this SPEC's deliverable)

Before building the custom solver, ship a **brute-force enumerator**
at small N to:

1. Establish the benchmark (wall time × N) the custom solver must beat
2. Confirm the cascade-1 trigger pattern works at small N (regression
   test for the eventual searcher)
3. Generate a residual HW distribution at small N (paper-class data
   for cascade structure across N)

The baseline is `bf_baseline.py`, defined here:

- Fix m0 = canonical anchor (e.g., zero or a nontrivial pre-seed)
- Restrict dm to two positions (default: dm[0] and dm[9])
- Enumerate dm[0] × dm[9] over [0, 2^N) × [0, 2^N) (= 2^(2N) patterns)
- For each: compute SHA(m), SHA(m XOR dm) at N-bit width, tally
  residual state-diff HW
- Output: collision count, near-residual HW histogram, wall time

At N=4: 256 patterns. <1s.
At N=6: 4096 patterns. <1s.
At N=8: 65536 patterns. ~1s.
At N=10: 1M patterns. ~10s.
At N=12: 16M patterns. ~3 min.
At N=14: 256M patterns. ~50 min.
At N=16: 4G patterns. ~14 hours (custom solver target).

Custom solver beats brute force at the N where memoization saves more
than enumeration costs — likely N=10..12 transition.

---

## What we learn before writing the searcher

The brute-force baseline at N ∈ {4, 6, 8, 10} answers, for free:

1. **What's the residual HW distribution at small N?** If it's
   long-tailed with a fat zero-mode (full collisions), we know
   cascade-1 is exploitable at small N. If zero-mode is empty,
   N=10 is below the cascade threshold.

2. **Which dm-bit positions are "hot"?** I.e., which positions when
   varied cause the residual to vary most? These are the
   high-information variables for the searcher to branch on first.

3. **Are there modular invariants visible at small N that vanish at
   N=32?** Comparing N=8 vs N=10 vs N=12 collision counts can reveal
   N-dependent vs N-invariant structure.

This is the "discover a representation" goal. The searcher's actual
implementation comes after this data exists.

---

## What this SPEC does NOT specify

- The actual searcher implementation (next-session work; ~300 LOC C
  with memoization hash table, depth-first stack, failure-explanation
  log).
- IPASIR-UP integration (downstream decision per user's framing).
- Full-N=32 application (the searcher is a small-N tool; N=32 is
  where kissat does the work).
- Multi-block extensions (this is single-block + cascade-1; block-2
  absorption is yale's separate domain).

---

## Concrete next moves (v2 — updated post-F86–F91)

**Phase 1 — DONE**:
- ✓ `bf_baseline.py` built and run at N ∈ {4, 6, 8, 10}.
  See F86 + F87 memos for results. HW_min ≈ 1.8N–2.0N at restricted
  (m0, m9). Wall scales 16× per +2 N.
- ✓ `forward_bounded_searcher.py` prototype with search + trace modes.
  See F88 memo. Forward HW-pruning REFUTED; cascade trajectory at
  N=8 confirmed faithful reduction of N=32 m17149975.
- ✓ `--cascade-filter` mode validated (F89). 250-1000× search-space
  narrowing. F89 demonstrated cascade-filter is the right structural
  mechanism.
- ✓ `analyze_cascade_bits.py` + `validate_predictor.py` (F90+F91).
  Bit-position predictor refuted at N>8.

**Phase 2 — open** (sequence proposed):

1. **Cascade-filter optimality gap evolution**: measure at N=12
   (~50 min wall budget). If gap stays at ~1 HW, that's the noise
   floor; if gap GROWS, cascade-1 is N-locally-suboptimal. Awaits
   user authorization for the multi-tens-of-minutes compute.

2. **Backward-search prototype**: implement in Python at N=8, starting
   from target HW=16 residuals at round 63 and propagating back to
   find dm-compatible state-diffs at round 60. Compare to forward
   cascade-filter's coverage.

3. **Modular signature analysis**: F91 ruled out bit-position
   correlation. Test if dm[0] mod K shows enrichment for some small
   K — consistent with F36's universal-LM-compatibility finding.

4. **LM cost extraction at small N**: compute Lipmaa-Moriai bound for
   each cascade-1 survivor at N=8. Compare (HW, LM) Pareto vs
   yale's full-N=32 frontier (HW=33-78). If shape matches,
   N-invariance at the LM level holds.

5. **C port for performance**: only after Phase 2 design is locked.
   Python prototype is fast enough at N≤10; C is needed for N=14, 16.

**Phase 3 — only after Phase 2 produces a representation**:

- IPASIR-UP integration as an optional propagator (the closed
  `programmatic_sat_propagator` bet's natural successor).
- Or: hand-crafted CDCL clause encoding informed by the discovered
  representation.
- Or: structural advice for yale's block-2 trail design.

End of SPEC v2.

## Memos by F-number

- **F85** (this SPEC v1, archived above as v2 changelog)
- **F86** brute-force baseline at N=4, 6, 8 — `bf_baseline.py` shipped
- **F87** random-sample mode + N=10 baseline + full-dm-freedom probe
- **F88** forward-bounded searcher prototype + N=8 cascade trace
- **F89** cascade-filter signature mechanism (validated)
- **F90** bit-correlation analysis at N=8 (later retracted at N>8)
- **F91** predictor cross-N validation + F90 retraction
- **F92+** = v2 next moves (Phase 2 above)
