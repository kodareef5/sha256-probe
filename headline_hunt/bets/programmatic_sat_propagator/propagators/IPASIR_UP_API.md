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
