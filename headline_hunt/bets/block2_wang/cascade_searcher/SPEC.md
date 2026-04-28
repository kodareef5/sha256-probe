# Cascade-Equation Searcher — design SPEC

**Status**: DRAFT v1, 2026-04-27 23:50 EDT
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

## Search algorithm (depth-first w/ memoization)

```python
def search(round, state_diff, dW_lookahead):
    key = canonical(state_diff, dW_lookahead)
    if key in memo:
        return memo[key]

    if round == 63:
        verdict = "COLLISION" if hw(state_diff) == 0 else f"NEAR_RESIDUAL_HW{hw}"
        memo[key] = verdict
        return verdict

    # Apply round propagation (modular, deterministic given m0 anchor + dm)
    new_state = round_step(state_diff, dW_lookahead[0], round)

    # Cascade-1 violation check
    if round >= 60 and (new_state.dA != 0 or new_state.dE != 0):
        memo[key] = "CASCADE_BREAK"
        return memo[key]

    return search(round + 1, new_state, dW_lookahead[1:] + [next_dW(round + 4)])
```

For depth-first, this is essentially constant-memory per branch. The
memoization table grows linearly with distinct visited states.

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

## Concrete next moves

1. **Ship `bf_baseline.py`** in this SPEC's directory. Run at
   N ∈ {4, 6, 8, 10}, capture residual HW histograms.

2. **Document baseline results** in
   `20260427_F86_bf_baseline_results.md`. Numbers are paper-class
   if they reveal N-scaling structure.

3. **Decide based on baseline**: if baseline is fast enough that
   N=14/16 brute force is feasible in <1h, the searcher's value-add
   is structural insight (failure cores + memoization patterns), not
   raw speed. If baseline is too slow at N=10 to even establish the
   benchmark, the searcher is needed urgently for the data corpus.

4. **Build searcher** in `cascade_searcher.c` using the data from #1
   to inform branching heuristics and memoization key choice.

End of SPEC v1.
