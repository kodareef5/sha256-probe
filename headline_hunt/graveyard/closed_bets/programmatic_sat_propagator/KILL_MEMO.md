# Kill memo — programmatic_sat_propagator

**Closed**: 2026-04-25
**Closed by**: macbook (autonomous session)
**Total CPU-h spent**: ~0.5 (engineering-side experiments only)

## What this bet was

GPT-5.5's 2026-04-24 meta-consultation surfaced the idea: a CaDiCaL `ExternalPropagator` (IPASIR-UP) that injects cascade-DP-aware reasoning rules into CDCL search. The hypothesis was that programmatic propagation could enforce constraints CNF cannot express directly — modular Theorem 4 (`da_r − de_r ≡ dT2_r mod 2^32`) on actual register values, with Sigma0/Maj computation — and that this extra pruning would compound during long search to give ≥10× conflict-count reduction at multi-hour budgets.

BET.yaml preserved at original path: `bets/programmatic_sat_propagator/BET.yaml`.

## Which kill criterion fired

From `kill_criteria.md` criterion #3 (added 2026-04-25 in response to early empirical evidence):

> **Trigger**: Propagator's main rules fire ONLY in the early-CDCL phase (e.g., during preprocessing or first ~50k conflicts) and fall silent during deep search.

**Empirical confirmation across 3 trigger strategies:**

| Trigger | Conflicts | Rule 4 fires | Verdict |
|---|---:|---:|---|
| Sample-based (every 64) | 50k → 500k | 209 → **209** (same) | front-loaded |
| Continuous (every event) | 50k → 500k | 520 → **520** (same) | front-loaded |
| + cb_decide() decision-shaping | 50k → 500k | 977 → **977** (same) | front-loaded |

In all three, Rule 4@r=62 fires only during the first ~50k conflicts; ZERO new fires across 50k–500k.

## Evidence

Result writeups (chronological):
- `bets/programmatic_sat_propagator/results/phase2b_smoke_2026-04-25/RESULT.md` — Phase 2B Mode B parity at 4×
- `bets/programmatic_sat_propagator/results/phase2c_partial_breakthrough_2026-04-25/RESULT.md` — 1:many SAT-var lookup fix; partial-bit firing 0 → 44
- `bets/programmatic_sat_propagator/results/phase2c_rule4_firing_2026-04-25/RESULT.md` — Rule 4 firing live, 157 fires at 50k
- `bets/programmatic_sat_propagator/results/phase2c_rule4_kernel_sweep_2026-04-25/RESULT.md` — Rule 4 firing varies 5× across kernels (52–249)
- `bets/programmatic_sat_propagator/results/phase2c_rule4_500k_2026-04-25/RESULT.md` — front-loaded firing at 500k (kill criterion #3 fired)
- `bets/programmatic_sat_propagator/results/phase2c_continuous_trigger_2026-04-25/RESULT.md` — continuous trigger refutation
- `bets/programmatic_sat_propagator/results/phase2c_cb_decide_2026-04-25/RESULT.md` — decision-shaping refutation (the killer)

Code artifacts (preserved):
- `propagators/cascade_propagator.cc` — ~750 LOC, builds against CaDiCaL 3.0.0
- `propagators/test_helpers.cc`, `test_modular_sub.cc`, `test_partial_sigma0.cc` — ~560 LOC unit tests, 40+ tests pass
- `propagators/SPEC.md`, `IPASIR_UP_API.md`, `RULE4_R62_R63_DESIGN.md`, `MODULAR_VS_XOR_FORCING_ISSUE.md`

Encoder artifacts (preserved, kept active for any future propagator):
- `bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py` — varmap v3 with `aux_modular_diff` (modular-diff aux variables for {a, e} × {62, 63})
- 36-CNF cross-kernel set + regenerate.sh

Run log entries: not appended (these were sub-second engineering experiments, not solver-budget runs).

## What we learned

This kill is INFORMATION. Three durable findings:

### 1. CDCL on cascade-DP CNF is DIFF-AUX-FOCUSED
CDCL navigates by deciding XOR-diff aux variables (dE[r], dA[r]). Actual register values are decided IMPLICITLY via unit propagation, rarely as primary decisions. Rules that require actual register values fire heavily during preprocessing (when cascade-zero unit clauses propagate massively) and fall silent during deep search.

### 2. Rule 4-style modular reasoning is CONSTANT-pruning, not GENERATIVE
The relation `dA[62] − dE[62] = dT2_62` is a single algebraic equation. Across all possible partial states CDCL might visit, the equation has a FINITE set of implied literals. For bit-19 it's ~977. Once all are forced, no further pruning possible regardless of trigger strategy or decision shaping.

### 3. Mode B and propagator are NOT additive — they're alternatives
Mode B's static unit clauses + the propagator's Rule 4 fires achieve the SAME constant-pruning effect. The propagator's complexity (~750 LOC + IPASIR-UP) is unjustified when Mode B does the equivalent at zero propagator overhead.

### Implication for headline-hunt portfolio

**Cascade-DP search cannot be sub-2^32 via propagation-style mechanisms.** Future bets in this category need either:
- Actively exploit the diff-aux variable subspace (which CDCL DOES decide on)
- Be GENERATIVE pruning rules (e.g., learning new constraints from conflict analysis, not just deriving implied literals from existing ones)
- Pivot to a different mechanism class entirely (block2_wang trail engine, kc_xor_d4 #SAT)

This insight propagated to `headline_hunt/TARGETS.md` so future workers see it.

## Reopen criteria

(Verbatim from `kill_criteria.md`'s "Reopen triggers")

- New IPASIR-UP-compatible solver advance with significantly different decision strategy (e.g., one that backtracks deeply enough to re-decide the cascade-input bits).
- New cascade theory gives propagation rules with formal soundness proofs AND empirical evidence of continuous firing during long CDCL search.
- A specific cascade-DP candidate is identified where vanilla cadical cannot find SAT in 100M+ conflicts, but the propagator can. (The only path to a true headline result — and would be earned only by finding the candidate, not by improving the propagator alone.)

## Adjacent updates

- `headline_hunt/registry/mechanisms.yaml` — `programmatic_sat_cascade_propagator` entry will be marked `status: closed` (next-pass registry edit).
- `headline_hunt/TARGETS.md` — already updated 2026-04-25 with structural insights from this kill (commit `c78363d`).

The cascade_aux_encoding bet is now the canonical preprocessing-phase cascade-structure injection mechanism. block2_wang remains the highest-EV unexplored path per GPT-5.5's meta-consultation.

## What survives in code

The propagator engineering substrate is NOT deleted — it stays at `bets/programmatic_sat_propagator/propagators/` as a reference implementation. Future workers who want to try a different rule (Rule 6 at r=63, a generative learning rule, or a diff-aux-targeted rule) can build on the same:
- IPASIR-UP integration framework
- Varmap v3 schema (encoder ↔ propagator bridge)
- Partial-bit modular arithmetic primitives (sigma0, maj, modular sub with borrow chain)
- cb_decide() decision-shaping framework
- Backtrack-safe per-level undo stacks

What's killed is the SPECIFIC HYPOTHESIS that Rule 4-style modular Theorem 4 propagation gives ≥10× conflict reduction. Future hypotheses can reuse this infrastructure.
