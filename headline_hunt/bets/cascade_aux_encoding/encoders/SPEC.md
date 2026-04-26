# Cascade-Auxiliary Encoding — Specification

*Version 1, 2026-04-24, macbook.*

## Background (why this encoding is different)

The standard cascade encoding (`lib/cnf_encoder.CNFBuilder` + `encode_collision`) adds
SHA-256 rounds 57-63 for two messages and imposes the full 8-register collision
constraint at round 63. The solver must *implicitly* discover the cascade structure
(Theorems 1-4 of `writeups/sr60_sr61_boundary_proof.md`): that da=db=dc=dd=0 diagonally
through rounds 57-60, that de60=0 automatically, that da=de at r≥61, and that the
full collision reduces to de61=de62=de63=0.

A Kissat or d4 run on the standard encoding reaches these invariants only after many
propagation/conflict cycles, traversing the CSA adder chains. **The cascade structure
is latent in the CNF but not visible to the solver as structural hints.**

The **derived encoding** (full W2 substitution via sigma0/sigma1 at schedule-determined
rounds 61-63) went the other direction — exposing schedule equations explicitly — and
made things worse: treewidth rose from ~110 to 181 at N=8 because the substitution added
long-range edges to the primal graph. See `negatives.yaml#d4_derived_encoding_worse`.

**Cascade-aux takes a third path**: expose the **difference structure** (dA, dB, ..., dH
per round, plus dW per round) as first-class auxiliary variables, tied bitwise to
the underlying state/word variables. These ties are *local* — each aux bit connects
to exactly 2 primary variables at the same round — so they don't inflate treewidth
the way derived does, but they let the solver see the cascade invariants directly.

## Two modes

### Mode A — `--expose-cascade` (default, conservative)

Adds aux variables and tying clauses only. **No semantic constraints added.**
Preserves the solution set of the standard encoding exactly.

Use when: you want to measure whether exposure alone helps the solver (Kissat)
or the compiler (d4) via better component caching / branching heuristics.

### Mode B — `--force-cascade` (aggressive)

Adds the aux variables from Mode A *plus* unit/equality clauses that encode the
cascade invariants from Theorems 1-4 as hard constraints. **Restricts the solution
set to cascade-DP solutions.**

Use when: you want the solver to find cascade solutions faster (sr=60) or prove
there are no cascade solutions at sr=61. Non-cascade solutions — if any exist —
are excluded. For sr=60 this is known to lose nothing (verified cascade SAT at
N=8..32). For sr=61 it's stronger than the base problem.

## Variables added

### Per-round register differences (7 rounds × 8 registers × N bits)

For r ∈ {57, 58, 59, 60, 61, 62, 63} and X ∈ {a, b, c, d, e, f, g, h}:

```
dX[r][i] := X1[r][i] XOR X2[r][i]     for i ∈ [0, N)
```

At N=32: 7 × 8 × 32 = **1792 new variables**.

### Per-round schedule-word differences (7 rounds × N bits)

For r ∈ {57, ..., 63}:

```
dW[r][i] := W1[r][i] XOR W2[r][i]
```

At N=32: 7 × 32 = **224 new variables**.

### Total aux variables

At N=32: **2016 new variables** (+18% over baseline ~11,200 vars).

## Tying clauses (always added, both modes)

Each aux variable is tied to its primary pair via the standard XOR identity. For
`d = a XOR b`, the 4 clauses are:

```
(-a, -b, -d) ∧ (-a, b, d) ∧ (a, -b, d) ∧ (a, b, -d)
```

- **Register ties**: 7 rounds × 8 regs × N bits × 4 clauses = 7168 clauses at N=32.
- **Word ties**: 7 rounds × N bits × 4 clauses = 896 clauses at N=32.
- **Total ties**: **8064 clauses** (+17% over baseline ~46,900).

## Force-cascade clauses (Mode B only)

Grounded in Theorems 1, 2, 3, 4 of the boundary proof. Each rule below encodes a
*known-true* invariant under the cascade-DP construction:

### Theorem 1 — Cascade diagonal (rounds 57-60)

For r ∈ {57, 58, 59, 60} and (X, offset) ∈ {(a,0), (b,1), (c,2), (d,3)}:

```
dX[r][i] = 0   whenever (r - 56) ≥ (offset + 1)
```

Concretely at N=32:
- dA[57..60] = 0 → 128 unit clauses
- dB[58..60] = 0 → 96 unit clauses
- dC[59..60] = 0 → 64 unit clauses
- dD[60]    = 0 → 32 unit clauses

Subtotal: **320 unit clauses**.

### Theorem 2 — de60 = 0 always

```
dE[60][i] = 0   for all i ∈ [0, N)
```

At N=32: **32 unit clauses**.

### Theorem 4 — da = de at r = 61

```
dA[61][i] = dE[61][i]   for all i ∈ [0, N)   →   2N bit-equality clauses
```

At N=32: **64 clauses**.

### Theorem 3 — Three-filter equivalence (rounds 61-63)

In cascade mode, the full 8-register collision is equivalent to `dE[61] = dE[62] = dE[63] = 0`:

```
dE[r][i] = 0   for r ∈ {61, 62, 63}, all i ∈ [0, N)
```

At N=32: **96 unit clauses**.

### Total force-cascade clauses

**512 clauses** at N=32. Negligible vs baseline.

**Important**: when the three-filter is active, the 8-register collision constraint at
round 63 becomes *redundant* — Theorem 3 proves equivalence. Mode B therefore omits
the standard final collision constraint to avoid redundancy. Mode A retains it.

## Expected impact

### On treewidth (for d4)

The register-difference aux vars form a linear "difference spine" running parallel
to the two state trajectories. Each `dX[r][i]` has primal-graph degree 2 (ties to
`X1[r][i]` and `X2[r][i]`). This is *the opposite* of what derived encoding did:
short local edges, not long schedule-spanning ones.

**Prediction (Mode A)**: treewidth at N=8 drops from ~110 to roughly 90-100 as d4's
component-cache finds the difference spine as a natural separator.

**Prediction (Mode B)**: treewidth drops further (~70-85 at N=8) because the
diagonal zero clauses pin ~320 aux vars at N=32, collapsing their contribution to
the primal graph.

Kill criterion #1 fires if Mode A measurement shows no drop AND Mode B shows <20%
drop.

### On SAT solve time (for Kissat)

**Prediction (Mode A)**: comparable to standard. The aux vars give marginal
propagation benefit but the CSA adders still dominate conflict analysis.

**Prediction (Mode B)**: substantially faster on sr=60 (expected ≥10x), because
the search immediately prunes to cascade solutions. For sr=61 TRUE instances,
Mode B is expected to either find a (vanishingly rare) SAT or eventually UNSAT.

**Empirical update (2026-04-24)**: Initial SPEC predicted "fast UNSAT (seconds
to minutes)" for sr=61 Mode B and "≥10x speedup on sr=60 SAT" for Mode B over
standard. Both empirically refuted at modest budgets:

- 600s (10 min) Mode B sr=61 (cand_n32_bit10_m3304caa0): TIMEOUT (run d8aa291).
- 5400s (90 min) Mode B sr=60 MSB cert seed=5: **TIMEOUT** at full 90 min
  budget. Standard takes 12h on same instance/seed; Mode B did NOT find SAT
  in 1/8 of that → Mode B sr=60 speedup is < 8x (and possibly zero).
- 5400s (90 min) Mode A sr=60 MSB cert seed=5: also TIMEOUT.

Both modes' SAT speedup claims are bounded above by what 90-min runs prove
(< 8x). The "≥10x sr=60 speedup" prediction is REFUTED at this budget. To
test for any real speedup, need 4h+ budgets across multiple seeds — that's
the multi-seed sweep documented in `results/20260424_first_solver_run.md`.

The SPEC's *encoding correctness* (audit pipeline, fingerprint, breadth-test
on 35 candidates → 70 CONFIRMED CNFs) is solid. The SPEC's *SAT-speedup
predictions* lack empirical support at these budgets and are RETRACTED until
properly tested.

**Wait — that's important**: a fast UNSAT on Mode B for sr=61 does NOT imply
sr=61 is UNSAT in general! It only means no *cascade-DP* sr=61 solution exists.
Non-cascade sr=61 solutions (Wang-style, etc.) remain out of scope for this
encoder. This aligns with GPT-5.5's separation of bets: sr=61 success is the
headline; block2_wang and programmatic_sat_propagator are how to reach it if
the cascade path is closed.

Kill criterion #2 fires if Mode A shows no SAT robustness improvement on TRUE
sr=61 N=10 AND Mode B doesn't give either the expected 10x sr=60 speedup or a
fast UNSAT signal on sr=61.

## What this SPEC does *not* do

- **No GF(2) differential algebra on dW through sigma1 / sigma0.** At first glance,
  since sigma0 and sigma1 are XOR-linear, one could write
  `dW[61] = sigma1(dW[59]) ⊕ dW_const_61`. This is *wrong* because
  W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45] uses **modular** addition,
  and XOR-differentials are not preserved through modular addition (carries
  corrupt the XOR-linearity). We add `dW[r]` purely as a tied aux variable; we
  do NOT add schedule-differential shortcuts.
- **No cube-and-conquer or soft cascade hints.** Mode B is hard; Mode A is pure
  exposure. A future refinement could try soft hints via Kissat learned-clause
  seeding — out of scope for v1.
- **No non-cascade solutions are searched in Mode B.** If sr=61 turns out to have
  a non-cascade solution, Mode B will miss it. That is intentional and explicit —
  see the explicit comment in the encoder output header.

## Test plan

Dense, testable, and ready for a second machine to pick up:

1. Generate matched-pair CNFs at N ∈ {8, 10, 12, 16} for both sr=60 and sr=61,
   in Mode A and Mode B — 4 × 2 × 2 = 16 CNFs per candidate, ~5 candidates worth
   testing (0x17149975 + 4 TRUE sr=61 picks from cnfs_n32/).
2. Run FlowCutter (d4 decomposition) on every N=8 CNF; report treewidth.
   Target: Mode A tw ≤ standard tw; Mode B tw < standard tw × 0.80.
3. Run Kissat with 10 seeds each on sr=60 N=8 (Modes A, B, standard). Report
   wall time, conflict count, propagations per conflict.
   Target: Mode B median ≤ 0.1× standard median (10x speedup floor).
4. Run Kissat with 10 seeds each on TRUE sr=61 N=10 (Modes A, B, standard),
   timeout 1h per seed. Report SAT/UNSAT/TIMEOUT per seed.
   Target: Mode B fast UNSAT (<10 min median) OR Mode A SAT where standard TIMEOUTS.
5. Log every run via `infra/append_run.py`. Sanity-audit every CNF via
   `infra/audit_cnf.py` first — this encoder's outputs should be added as new
   fingerprints to `infra/cnf_fingerprints.yaml` once a few have been audited.

If Test 2 fails (no treewidth drop) AND Test 3 fails (no sr=60 speedup), kill
criterion #1 fires → close the bet, write a kill memo in `graveyard/`.

## Open design questions for the second worker

- **Variable ordering for d4**: the order in which aux vars are declared may affect
  d4's vtree. Suggest: interleave dX[r][i] immediately after X1[r][i] and X2[r][i]
  in the variable numbering, so tree decomposition sees them as a local cluster.
  Test alternative: declare all aux vars last.
- **Audit fingerprint**: after the encoder is validated on a known-good sr=60 candidate
  that still solves, capture (vars, clauses) for Mode A N=32 and add to
  `cnf_fingerprints.yaml` so future aux CNFs get CONFIRMED verdicts.
- **Symmetry breaking**: the aux vars expose an obvious symmetry `swap(M1, M2)`.
  If this matters for solve time, add a lex-order breaking clause on dW[57][0..7].
  Out of scope for v1 but noted.

## Per-chamber image structure (F-series, 2026-04-26)

Empirical fact: at fixed `(m0, fill, kernel_bit, W57)`, the per-chamber
image of `de58, de59, de60, ..., de63` has size **exactly 1**. That is:
once W57 is fixed, varying the rest of the schedule (W58..W63) in a way
that maintains cascade-1 (`W_k_2 = W_k_1 + cw_k`) yields a **single**
value for each `de_k`. Verified across 7 chambers spanning 4 cands.

Per-slot structure:

| slot | per-chamber size | depends on W57? | implied 32-bit hint |
|---|---:|---|---|
| de58 | 1 | YES (chamber-specific) | 32-bit per-chamber hint |
| de59 | 1 | NO (cand-level invariant) | 32-bit free hint |
| de60 | 1 (= 0) | NO (structurally 0) | hints are redundant w/ Mode B |
| de61 | 1 (= 0) | NO (structurally 0) | hints are redundant |
| de62 | 1 (= 0) | NO | redundant |
| de63 | 1 (= 0) | NO | redundant |

### Structural derivation

Under cascade-1 (`da[k]=0` for k ∈ {57, 58, 59, ...}):

- `de_{k+1} = d_{k} + dT1_{k+1}` (state-vector position 4 update)
- `d_{k} = e_{k-1}` (state shift), so `dd_{k} = de_{k-1}`
- `dT1_{k+1}` after applying `cw_{k+1}` reduces to `dT2_{k+1}`
- `dT2_{k+1} = dSigma0(a_k) + dMaj(a_k, a_{k-1}, a_{k-2})`
- Under cascade-1, `da[k] = da[k-1] = da[k-2] = 0`, so `a` values are
  side-equal — `dSigma0` and `dMaj` arguments collapse:
  - `dSigma0(a_k) = 0`
  - `dMaj(a_k, a_{k-1}, a_{k-2})` depends only on a-side values that
    differ in a-side only when k-1 or k-2 is below the cascade start
- For k = 58: `dMaj(a_57, a_56, a_55)` — a_56, a_55 are pre-cascade,
  carry the original kernel difference. Result: dT2_58 ≠ 0 generally,
  but is fixed by the slot-57 input state (which depends on W57).
  Hence `de58` is W57-determined.
- For k = 59: `dMaj(a_58, a_57, a_56)` — a_57, a_58 are cascade-1
  forced equal. dMaj reduces to a_56-only contribution → cand-level
  constant. Hence `de59` is cand-level invariant.
- For k ≥ 60: cascade-1 has propagated long enough that all dT2/dSigma0
  arguments are side-equal. `de_k = 0` exactly.

### Practical implication

- **de58-at-w57 hint**: 32 unit clauses fixing aux_reg[("e", 58)] to
  the single value computable as `f(m0, fill, bit, W57)`. Useful at
  preprocessing budgets ≤100k.
- **de59 hint**: 32 unit clauses fixing aux_reg[("e", 59)] to a
  cand-level constant. Free (no W57 needed). Stacks with de58.
- **de60..de63 hints**: structurally 0 but Mode B's force clauses
  already encode this; explicit unit clauses interact badly with
  kissat propagation at some cands (F6 negative).

### Caveats

- The chamber-fixed `de58` value is **non-zero** for all observed
  chambers, while sr=61 collision requires `de58 = 0`. So injecting
  `de58 = chamber_value` constrains the search to a chamber that
  contains NO sr=61 collision. The 50k speedup is in chamber-elimination
  triage, not collision-finding.
- This applies to Mode A "expose" CNFs. Mode B "force" CNFs already
  pin de58 = 0 implicitly via cascade clauses; adding chamber-specific
  hints there causes immediate UNSAT propagation (over-restriction).
- Speedup decays past 200k conflicts (F8); regresses 0.85-0.97× at
  500k+. Use only for short-budget triage.

## References

- `writeups/sr60_sr61_boundary_proof.md` — Theorems 1-6, the source of truth for
  the cascade-diagonal, de60=0, da=de, three-filter results.
- `writeups/sr60_collision_anatomy.md` — explains WHY the cascade is what it is
  (sequential register zeroing via shift register + two aligned cascades).
- `lib/cnf_encoder.py` — base encoder whose API this extends.
- `bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py` — implementation.
- `bets/cascade_aux_encoding/results/20260426_de58_de59_stack_n18.md` —
  n=18 deployment of the stack.
- `bets/cascade_aux_encoding/results/20260426_f8_budget_decay.md` —
  budget-dependent regression curve.
