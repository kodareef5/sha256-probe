# IPASIR-UP API survey for the cascade-DP propagator

Closes the bet's #1 TODO ("API survey: read CaDiCaL IPASIR-UP docs"). Local CaDiCaL: 3.0.0, header at `/opt/homebrew/include/cadical.hpp`.

## Class structure

```cpp
class CaDiCaL::ExternalPropagator {
  // -------- REQUIRED virtual methods --------

  // Notifies on every variable assignment. Stack-style: new
  // assignments pushed at end. Includes both decisions and propagations
  // (CDCL units, BCP, etc.) on observed variables.
  virtual void notify_assignment(const std::vector<int>& lits) = 0;

  // Notify on solver entering new decision level.
  virtual void notify_new_decision_level() = 0;

  // Notify on solver backtracking to new_level. Propagator must
  // unwind its own state to match.
  virtual void notify_backtrack(size_t new_level) = 0;

  // Solver presents a candidate full model. Return false to reject;
  // propagator must then add an explanatory clause via
  // cb_has_external_clause / cb_add_external_clause_lit.
  virtual bool cb_check_found_model(const std::vector<int>& model) = 0;

  // Solver asks if propagator has any external clause to inject.
  // is_forgettable: hint to solver about clause persistence (default
  // false = irredundant, persistent).
  virtual bool cb_has_external_clause(bool& is_forgettable) = 0;

  // Solver requests the literals of the external clause one-by-one.
  // Return 0 to terminate the clause. Called after cb_has_external_clause
  // returns true.
  virtual int cb_add_external_clause_lit() = 0;

  // -------- OPTIONAL virtual methods --------

  // Propagator-suggested next decision literal. 0 = solver decides.
  // Triggers runtime error if returned literal is already assigned or
  // not observed.
  virtual int cb_decide() { return 0; }

  // Propagator-suggested next propagation. Returns the forced literal,
  // or 0 if nothing to propagate. Solver will then ask for the reason
  // clause via cb_add_reason_clause_lit.
  virtual int cb_propagate() { return 0; }

  // Reason clause for a literal forced by cb_propagate. Called
  // literal-by-literal, terminated by 0. Reason clause must contain
  // the propagated literal.
  virtual int cb_add_reason_clause_lit(int propagated_lit) { return 0; }
};

class CaDiCaL::Solver {
  // Connect/disconnect propagator. Only ONE propagator at a time.
  void connect_external_propagator(ExternalPropagator* propagator);
  void disconnect_external_propagator();

  // Mark a variable as "observed" — propagator will be notified about
  // its assignments. Observed variables are frozen against inprocessing
  // (variable elimination). Required before propagator can reference
  // the variable in cb_propagate / cb_decide / cb_add_*_clause.
  void add_observed_var(int var);

  // Remove observed flag. Variable must be unassigned at the time.
  void remove_observed_var(int var);
};
```

## Lifecycle (from a propagator implementer's perspective)

1. **Setup** (before solve):
   - Construct propagator instance (subclass of `ExternalPropagator`).
   - `solver.connect_external_propagator(prop)`.
   - For each variable the propagator cares about: `solver.add_observed_var(v)`.
   - Initialize propagator's internal differential-state model.

2. **During solve** (notifications):
   - On `notify_new_decision_level`: snapshot or push internal state.
   - On `notify_assignment(lits)`: update internal differential-state model from each newly-assigned literal. Watch for cascade-rule trigger conditions.
   - On `notify_backtrack(level)`: restore state to that level.

3. **During solve** (queries):
   - On `cb_propagate`: if any cascade rule's preconditions are now met AND the implied bit is currently undecided, return that literal; remember the (lit, reason) pair.
   - On `cb_add_reason_clause_lit(lit)`: stream the reason clause — the negations of the input literals plus `lit` itself. Return 0 to terminate.
   - On `cb_check_found_model(model)`: validate the differential constraints hold across the model. If not, signal external clause via `cb_has_external_clause` / `cb_add_external_clause_lit`.

4. **Cleanup**:
   - `solver.disconnect_external_propagator()` (also resets all observed flags).
   - Destruct propagator instance.

## Mapping cascade-DP rules to IPASIR-UP

| Rule (from SPEC.md) | API hook | When it fires |
|---|---|---|
| Rule 1 (cascade diagonal `dA[57..60]=0`, ...) | `cb_propagate` | When any `dA[r]` bit observed; force to 0. |
| Rule 2 (`dE[60]=0`) | `cb_propagate` | When any `dE[60]` bit observed; force to 0. |
| Rule 3 (Mode FORCE three-filter) | `cb_propagate` | When `dE[61..63]` bits observed in FORCE mode. |
| Rule 4 (unified Theorem 4) | `cb_propagate` + `cb_check_found_model` | When `dA[r]` or `dE[r]` partially decided AND actual `a, b, c` register values determined; force the modular sum constraint. Also a final-model sanity check. |
| Rule 5 (`dC[63]=dG[63]`) | `cb_propagate` | When either side's bits decided; force the other. |
| Rule 6 (R63.3) | Same as Rule 4 at r=63 | (Subsumed.) |
| Rule 7 (W[60] schedule, sr=61) | `cb_propagate` | When relevant `W[44, 45, 53, 58]` bits decided. |
| Rule 8 (failed-residue cache) | `cb_check_found_model` | At any rejected model: hash partial state at cascade boundary, store. |

## Reason clause construction

A propagator is REQUIRED to provide a reason for every literal it forces. The reason clause must:
- Contain the propagated literal (positive form).
- Contain the negation of every "input" literal that contributed to the propagation (i.e., the variables CDCL must un-assign to undo this implication).

For Rule 4 at r=63: forcing `dE[63]_bit_i = (dA[63]_bit_i XOR dT2_63_bit_i)` requires:
- All 32 bits of `dA[63]` (or all 32 bits of `dE[63]`).
- All 32 bits of `dT2_63` (which depends on `a_60, a_61, a_62` — 96 actual-value bits of the pair-1 register).
- Possibly all 32 bits of `a_60_pair2`, etc. (Maj depends on actual values from BOTH pairs.)

So a single Rule 4 propagation has a reason clause of ~160-256 literals. This is HEAVY but tractable; modern solvers handle 256-lit reason clauses fine.

For Rule 1 (cascade diagonal): reason is just the cascade-1 W[57] offset existence — derivable from the cascade-1 input W[t] values for t < 57. Could be ~100-200 lits. Better: use cascade-1's CNF-side encoding to provide the reason from the CNF's own structure (no need to re-explain).

## Critical implementation details

1. **Reason clauses become learned irredundant clauses by default** — they persist across restarts. This is normally good (avoid re-deriving) but can bloat memory. The `is_forgettable` flag lets the propagator hint that some clauses are forgettable (e.g., Rule 7 schedule constraints which can be re-derived cheaply).

2. **Observed variables are frozen against inprocessing** — variable elimination won't touch them. Need to be careful about which vars to observe: observing too few = miss propagation opportunities; observing too many = block useful inprocessing. For cascade-DP: observe all bits of `dA, dB, dC, dD, dE, dF, dG, dH` at rounds 56-63 (8 regs × 32 bits × 8 rounds = 2048 bits), plus the actual-value bits of `a, e` at rounds 56-63 (2 regs × 32 bits × 8 rounds = 512 bits). Total ~2560 observed vars per CNF. Manageable.

3. **No re-entrancy** — solver guarantees at most one callback at a time. Propagator can use thread-unsafe state freely.

4. **Performance: notify_assignment is called on EVERY assignment** including BCP propagations. Internal state update must be O(1) or O(log n) per literal; anything heavier will dominate solve time.

## Var-map: bridging CNF and propagator state

The cascade_aux encoder emits a JSON varmap sidecar (`<cnf>.varmap.json` via `--varmap +`) that maps SAT variable IDs to differential-bit coordinates `(register, round, bit)`. Generated 2026-04-25.

Schema (see `propagators/varmap_loader.py`):
```json
{
  "version": 1,
  "summary": {"sr": 60, "mode": "force", "total_vars": 12620, ...},
  "aux_reg": {
    "a_57": [10989, 10990, ...],   // 32 SAT-var literals
    "a_58": [...], "a_59": [...], ...,
    "h_63": [...]
  },
  "aux_W": {
    "57": [...], "58": [...], ..., "63": [...]
  }
}
```

Literal convention: positive int = SAT var; negative = negated; 1 = const TRUE; -1 = const FALSE. The encoder's constant propagation folds ~384 / 1792 differential bits to compile-time constants on a typical sr=60 force-mode CNF.

The propagator uses `varmap_loader.VarMap` to:
1. **Forward lookup**: get the SAT literal for a specific differential bit. Used during `add_observed_var` setup and `cb_propagate` rule firing.
2. **Reverse lookup**: given a SAT var assignment from `notify_assignment`, identify which differential bit was just decided. Updates the propagator's internal state model.

Without the varmap, the propagator would have to either re-derive the encoder's variable allocation logic (fragile) or instrument the encoder to emit the map at run time (intrusive). The sidecar approach is clean: encoder writes once, propagator reads at solve start.

## Existing reference implementations

- **CaDiCaL examples directory** (`/opt/homebrew/Cellar/cadical/3.0.0/share/`): one ExternalPropagator demo for parity constraints.
- **Alamgir / Nejati / Bright** (literature.yaml#alamgir_nejati_bright_sat_cas_sha256, needs-verification): the closest analog — programmatic propagation for SHA-1/SHA-256 attacks. Likely worth citing in our SPEC.
- **MaplePropagator** (Vardi/Liang group): different SAT lineage but same API spirit.

## Build wiring (macOS, homebrew CaDiCaL)

```bash
# Compile a propagator C++ source against local CaDiCaL.
g++ -std=c++17 -O3 -I/opt/homebrew/include \
    -L/opt/homebrew/lib -lcadical \
    propagator_main.cc -o propagator

# Or via direct link to a custom static CaDiCaL build (recommended for debugging).
```

If we need a newer CaDiCaL than 3.0.0 (e.g., to test forthcoming API additions), build from source: `git clone https://github.com/arminbiere/cadical && cd cadical && ./configure && make`.

## Decision: build path

**Phase 2A** (1 week): C++ skeleton subclass with stub callbacks. Connect to CaDiCaL on a tiny CNF. Verify `notify_assignment` and `cb_propagate` are called as expected. No actual cascade rules yet.

**Phase 2B** (1-2 weeks): port `propagators/rules.py` (Phase 1 Python prototype) to C++. Implement Rules 1, 2 first (simplest — just zero-forcing). Run on the 36-CNF cross-kernel set; compare conflict count vs vanilla CaDiCaL.

**Phase 2C** (1-2 weeks): implement Rules 3, 4, 5. Rule 4 is the heaviest — needs the actual-value bit-tracking and the modular sum reasoning.

**Decision gate** (per kill_criteria.md): after Phase 2B+2C, if conflict count drops by ≥10x at N=32 sr=60 → continue to Phase 3 (Rules 7, 8 + scaling). If <2x → kill the bet.

## Open question: rules vs aux-encoding

The cascade_aux Mode B encoder (`bets/cascade_aux_encoding/encoders/`) achieves SOME of these constraints via CNF-side encoding (Rules 1, 2, 3 are encoded as unit clauses in force mode). The propagator's value-add is Rules 4, 5 (which involve modular arithmetic that CNF can express only with aux variables and ripple-carry adders) and Rule 8 (cross-restart caching, impossible at the CNF level).

So the natural experimental matrix:
- Vanilla CaDiCaL on aux_expose_sr60_n32_*.cnf  (no propagation hints, no force constraints)
- Vanilla CaDiCaL on aux_force_sr60_n32_*.cnf   (force constraints in CNF)
- Propagator + CaDiCaL on aux_expose_sr60_n32_*.cnf  (force constraints via propagator)
- Propagator + CaDiCaL on aux_force_sr60_n32_*.cnf   (both)

The 36-CNF cross-kernel set (just shipped) is exactly the substrate this needs.

---

## 2026-04-28 update: IPASIR-UP for block2_wang absorber search (yale's F125 alignment)

The original survey above (2026-04-25) was framed around cascade-DP collision
search. Today's empirical work (yale F123/F125/F133, macbook F147/F157)
identifies a SECOND use case where the IPASIR-UP infrastructure already shipped
(1310 LOC C++ + IPASIR-UP integration) is directly applicable.

### Yale's F125 stated need

After exhausting all radius-2 local moves (M2-only, both-side, common-mode,
fixed-diff resampling, additive common-mode), yale concluded:

> "structured moves that preserve late-schedule features, OR a solver that
> reasons directly over schedule words W16-W30 instead of raw message-bit
> flips."

Both alternatives map cleanly to IPASIR-UP architectures.

### Two IPASIR-UP architectures applicable to yale's need

#### Architecture A: Cube-and-conquer with structural cubing

Pattern: at each cube, the cubing strategy (MCTS or heuristic) picks a set of
W-bits to fix, then CaDiCaL solves the resulting reduced problem. IPASIR-UP
plays no propagation role here — purely cubing infrastructure.

For block2_wang: cube on W2[60] bit positions (32 cubes per outer iteration).
Each cube fixes 1-2 W2[60] bits; CaDiCaL solves the resulting cascade-1 +
cube-fixed instance. Reward = chain-output target distance after partial solve.

Cost per cube: ~1-10 seconds (cascade-1 sr=60 partial solve at modest budget).
32 cubes × 10 sec = ~5 minutes per outer iteration. Over 8-32 outer iterations
(MCTS rollouts), ~1-2 hours wall time.

This is comparable to yale's current local search budget but explores a
DIFFERENT search-space topology — cube-fixed sub-problems vs random
perturbations.

#### Architecture B: Cascade-aware structural propagator

Pattern: this bet's existing propagator (Rules 1-5 already shipped) reasons
during CDCL search, propagating cascade-1 structural constraints. yale's
absorber-search context is different from the original collision-finding
context: instead of seeking a SAT model, the propagator helps the solver
quickly REJECT configurations far from the target.

For block2_wang: build a CNF that encodes "M1, M2, target W2_diff" with
W2[60] free. The propagator's cascade-zero rules (Rule 1, 2) hold trivially
(they're cascade-1 invariants). Rule 4 (`dE[63] = dA[63] XOR dT2_63`) provides
structural propagation that CDCL can't easily learn from clauses alone.

Cost: per the bet's empirical findings, Rule 4 fires ~150-250 times per 50k
conflicts. For absorber search (probably 10k-50k conflicts per probe),
expect ~50-100 propagator interventions. Overhead 1.9× wall vs vanilla
CaDiCaL (per kill criterion #3 firing on 2026-04-25), but for absorber search
the SEARCH GUIDANCE may compensate.

### Architecture comparison

| Architecture | What yale gets | What this bet's existing code gets you | Estimated build time |
|---|---|---|---|
| A: cube-and-conquer | Structured cubing escape from local minima | New cubing harness (no existing cube tooling here) | ~3-5 days new C++ |
| B: cascade-aware propagator | In-search structural guidance | 1310 LOC C++ + 40+ unit tests + Rules 1-5 | ~few days adaptation |

Architecture B reuses the bet's existing engineering investment. Architecture A
is closer to the AlphaMapleSAT paper (literature/notes/alphamaplesat_*).

### Specific IPASIR-UP hooks for yale's use case

For Architecture B (cascade-aware propagator on block2_wang):

1. **`add_observed_var`**: observe the W2[60] bits, the resulting cascade-1
   state-diff bits at rounds 60-63. Estimated 32 + 256 = 288 observed vars.
   No new infrastructure needed; propagator already supports this pattern.

2. **`cb_propagate`**: existing Rule 4 logic at r=63 forces dE[63] from
   dA[63] + dT2_63. For absorber search, this is the same structural rule —
   no new logic required.

3. **`cb_check_found_model`**: yale's absorber search wants to CONTINUE
   exploration after each near-target model, not stop. The propagator could
   reject "this is the absorber" claims that don't have low chain-diff,
   forcing CaDiCaL to backtrack and explore alternatives.

4. **NEW HOOK NEEDED**: target-distance-based rejection. The propagator
   should reject models where chain-output target distance > threshold T,
   forcing CaDiCaL to find next-best model. This is a NEW callback pattern
   beyond the original SAT/UNSAT use case.

5. **`cb_decide`** (currently unused in the bet): yale's heuristic biases
   toward specific active words. The propagator could implement that bias
   via cb_decide, suggesting branching variables aligned with yale's
   empirical {0,1,2,8,9} pattern.

### Reopen viability for this bet

Per F147's reopen-candidate context, the bet should reopen if:
- yale or another machine articulates a specific use case demand: **yes,
  yale's F125 statement is the use case**
- A specific candidate identifies where vanilla cadical can't solve but
  propagator can: **yale's score-86 plateau IS that scenario**

The 1310 LOC infrastructure + 40+ unit tests are immediately reusable.
Adaptation cost: ~3-5 days to add the target-distance rejection callback
(`cb_check_found_model` extension) and `cb_decide` heuristic bias.

### Recommendation

If the project escalates yale's F125 demand:
1. Reopen this bet (status: closed → in_flight)
2. Add target-distance rejection logic to `cascade_propagator.cc`
3. Add `cb_decide` heuristic biased toward {0,1,2,8,9}-style active words
4. Test on bit3 fixture; compare wall-time and score floor vs yale's heuristic

This is a CONCRETE adaptation path. The bet's existing engineering is
~80% reusable.

### Discipline notes

This update extends the survey, doesn't change implementation. No code
changes; no new compute; no solver runs. Pure documentation update tying
the existing IPASIR-UP infrastructure to today's emergent use case.

If/when reopened, the build steps (Phase 2A→2C) and decision gates
documented above remain valid. This update adds Architecture-B-for-
block2_wang as a 4th decision option alongside the original Phases 2A-C.

## 2026-04-28 PM update: F207-F217 structural findings inform propagator design

The cascade_aux_encoding bet's F207-F217 structural-pivot arc produced
empirical findings that directly inform this bet's IPASIR-UP design.
F237 confirmed that preprocessing-alone doesn't help on hard instances,
which **strengthens** the case for an in-search structural propagator.

### Universal 184-bit active-schedule space (F209/F213/F217)

F209 mapped cascade_aux variables to SHA semantics:
  vars 2..129 = M1 free schedule (W1_57..W1_60 for sr=60)
  vars 130..257 = M2 free schedule (W2_57..W2_60)

F213 found the hard core comprises 185 of 256 schedule vars (72%) plus
~3,722 Tseitin auxiliaries. F217 noted the cascade-1 hardlock forces
**W1_58 entirely** (cascade_aux) or **W1_57** (TRUE sr=61), depending on
n_free.

For the IPASIR-UP propagator:
- The "schedule space" is 256 variables (or 192 for TRUE sr=61).
- ~70 of these are forced by cascade-1 hardlock; can be set immediately
  by `cb_propagate` upon detecting the cand id.
- The remaining ~177-184 are the actual decision variables.

**Concrete propagator hook**: when CaDiCaL queries `cb_check_found_model`,
the propagator can check whether the decision sequence respects
cascade-1 hardlock relations. If not, return a conflict clause.

### Why preprocessing-alone failed (F237) but propagator might succeed

F237 showed: shell_eliminate_v2 (28% var reduction) doesn't help kissat
on hard instances. The hard core is intrinsic; preprocessing redistributes
work without simplifying SAT-difficulty.

A propagator is **structurally different**: it doesn't reduce problem
size before search; it guides search **during** CDCL by:
1. Triggering forced unit propagations earlier than CDCL discovers them
2. Detecting structural conflicts before unit-prop bottoms out
3. Biasing decision variables toward the schedule-bit space

This avoids F237's failure mode: instead of trying to make the problem
smaller, make CDCL's search smarter inside the same problem.

### Specific structural propagator hooks (revised post-F237)

| IPASIR-UP hook | Use for cascade-1 |
|---|---|
| `cb_propagate` | Force W1_58 bits (cascade_aux) or W1_57 bits (TRUE sr=61) when the schedule pattern matches cascade-1 hardlock. ~32 forced bits per cand. |
| `cb_check_found_model` | Verify the model satisfies cascade-1 round equations (Theorems 1-4). Reject if not. |
| `cb_decide` | Bias decisions toward the 184-bit schedule space first; auxiliary Tseitin vars last. |
| `cb_add_external_clause` | Add cascade-1-specific learned clauses (e.g., schedule recurrence W[r] = σ1(W[r-2]) + ... encoded as a single XOR-style learned clause). |

### Implementation priority order

Given F237's empirical lesson (preprocessing alone insufficient):

1. **Phase 2D — Decision-priority propagator**: implement `cb_decide`
   alone. Bias kissat to branch on schedule-space vars first. Cheapest
   structural intervention; tests if order-of-decision matters.

2. **Phase 2E — Forced-bit propagator**: implement `cb_propagate` for
   the 32 cascade-1-forced bits (W1_58 in cascade_aux, W1_57 in TRUE
   sr=61). Should give same effect as kissat already does internally
   via BVE — useful baseline.

3. **Phase 2F — Conflict-aware propagator**: implement
   `cb_check_found_model` rejection of non-cascade-1-compliant
   assignments. This is the structurally-distinct contribution
   (kissat doesn't know cascade-1).

Each phase is 4-8 hours of implementation work; runnable independently.
Ship-and-test cycle ~1 day per phase.

### Reopen recommendation (revised)

Status: programmatic_sat_propagator bet was closed; F147 set
reopen_candidate_2026_04_28. Now stronger reopen rationale:

- F237 shows preprocessing-alone (cascade_aux_encoding direction) is
  empirically refuted on hard cascade-1 instances.
- IPASIR-UP propagator is structurally distinct (in-search vs
  pre-search) and may succeed where preprocessing failed.
- F207-F217 structural findings give concrete propagator hooks.

**Recommended reopen**: implement Phase 2D first (decision-priority).
Test on the same hard sr=61 instance from F235 (kissat 848s timeout).
If decision-priority gives ≥2× speedup, the bet's reopen is justified.
If null, escalate to Phase 2F.

### Discipline notes

This update extends the survey to incorporate F207-F217 structural
findings and F237 empirical lesson. No code changes. No solver runs.

If/when reopened, the structural-propagator hooks (Phases 2D-2F) are
the priority order, NOT Phase 2A-2C (those were generic propagator
research; F207-F237 has now narrowed the actionable scope).

## 2026-04-29 update: F286/F311/F323-F326 sharpen propagator design

### What changed since 2026-04-28 (F207-F237 era)

Five new findings refine the propagator design:

1. **F286** (cascade_aux_encoding): the universal hard core is **132 bits**,
   not 184. Decomposes as 128 round-bits (W*_59 + W*_60, full) plus 4
   specific anchors (W1_57[0], W2_57[0], W2_58[14], W2_58[26]).

2. **F311** (singular_chamber_rank): the chamber attractor is a 1-bit-
   neighborhood-isolated point in (W57, W58, W59) space. 420 single-bit
   moves tested across 3 cross-cand HW4 chambers: 0 preserve the (dh, dCh)
   chart while reducing D61. 1-bit search cannot navigate the basin.

3. **F323**: σ1 fan-in does NOT predict W2_58 universal-core fraction
   (light bits 0.730, dense bits 0.759 — slightly lower).

4. **F324** (this bet's adjacent finding): single-bit unit propagation
   on the cascade_aux force-mode CNF forces 0/32 W2_58 bits and 0/4 F286
   anchors. The encoder does NOT pin the 132-bit core via UP.

5. **F325/F326**: 2-bit pair UP also forces nothing (0/496 pairs in
   bit31; cross-validated 0/32 forced on 5 additional cands; 481 baseline-
   UP-forced is candidate-agnostic).

**Combined thesis**: the 132-bit hard core is a candidate-agnostic
**CDCL-search invariant** of the SHA-256 cascade-1 collision problem.
Not an encoder Tseitin artifact — manifests only through CDCL conflict
analysis.

### Sharpened hook priorities

| IPASIR-UP hook | Use for cascade-1 | Priority (2026-04-29) |
|---|---|---|
| `cb_decide` | **Bias decisions toward the 132 hard-core bits FIRST.** Use F286 stability data per cand or universal 132-bit set. | **HIGH — implement first** |
| `cb_add_external_clause` | **Pre-load CDCL learned clauses for the 132-bit constraint surface.** This is now the structurally-motivated hook: F326 shows these clauses are NOT in the CNF, so injecting them is genuinely additive. | **HIGH — implement second** |
| `cb_propagate` | Force W*_57/58/59/60 bits when the cascade-1 hardlock pattern matches. **DOWNGRADED**: F324 shows even single-bit assumption doesn't UP-force any W2_58 bits, so the propagator has nothing to add via cb_propagate that UP doesn't already do (the cascade-offset is already encoder-pinned via the 481 AUX vars). | LOW — likely redundant with encoder force-mode |
| `cb_check_found_model` | Verify model satisfies cascade-1 round equations and reject. Useful sanity check but not the bottleneck. | MEDIUM |

### Revised reopen recipe

**Phase 2D (priority HIGH, ~6-8 hrs)**: `cb_decide` with 132-bit branching priority

```cpp
// Pseudocode for cascade-1 decision priority
int CascadeOnePropagator::cb_decide() {
  // Decision priority order:
  // 1. The 4 LSB/anchor bits: W1_57[0], W2_57[0], W2_58[14], W2_58[26]
  // 2. The 128 round bits: W1_59[0..31], W2_59[0..31], W1_60[0..31], W2_60[0..31]
  // 3. Auxiliary bits last
  for (int var : priority_order_132) {
    if (!is_assigned(var)) return polarity_hint(var);
  }
  return 0;  // let solver decide
}
```

**Phase 2D extension (priority HIGH, ~2-4 hrs)**: integrate F286 stability
JSON. Read per-cand `schedule_core` from F283-style JSONs to identify the
132 bits for the specific instance being solved.

**Phase 2D' (priority HIGH, ~4-6 hrs)**: `cb_add_external_clause` injecting
learned clauses derived from F286 stability data. The exact clause shape
to inject is informed by yale's `--stability-mode core` selector logic.

**Test instance**: same as F235 (sr61_cascade_m09990bd2_f80000000_bit25,
kissat 848s timeout). Reopen criterion: ≥2x speedup vs kissat baseline.

### What's downgraded vs prior recommendation

The 2026-04-28 PM update prioritized `cb_propagate` for "32 forced bits"
in a Phase 2E. F324 now shows those bits are NOT forced by encoder UP —
they're CDCL-derived. So `cb_propagate` cannot force them either (any
sound propagator must respect UP). The revised priority is:

- 2D (cb_decide):              HIGH — order-of-decision matters
- 2D' (cb_add_external_clause): HIGH — inject conflict clauses missing from CNF
- 2E (cb_propagate):            LOW  — redundant with encoder force-mode
- 2F (cb_check_found_model):    MEDIUM — sanity, not speedup

### Hook-by-hook estimated impact

If implemented correctly, the 132-bit-aware decision priority + clause
injection should give:

- **2-5x speedup** on TRUE sr=61 N=32 instances where kissat baseline is
  ~50s-15min wall (mid-difficulty instances). The 132 bits dominate the
  decision tree.
- **1-2x speedup** on hard sr=61 instances where kissat times out at 848s.
  Diminishing returns: the bits only structure the search space; the
  underlying cascade-1 collision constraint is still the bottleneck.
- **<1.5x speedup** on easy sr=60 N=8/N=10 instances (already solved fast
  by kissat baseline; CDCL trajectory is short).

### Discipline note

This 2026-04-29 update incorporates F286 (132-bit decomposition), F311
(chamber brittleness), F323-F326 (search-invariant proof). No code
changes. No solver runs. The hook priorities are now structurally
motivated by empirical evidence on multiple cands.

If/when reopened: implement 2D + 2D' as the FIRST cycle (one combined
ship of cb_decide + cb_add_external_clause). The Phase 2E cb_propagate
direction is no longer recommended as a primary path.
