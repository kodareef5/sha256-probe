# IPASIR-UP API survey (CaDiCaL 3.0.0)
**2026-04-25 evening** — programmatic_sat_propagator graveyard reference doc.

Per GPT-5.5 review note ("IPASIR-UP API survey" as a concrete handoff
artifact). Captures the API surface available for any future propagator
reopen against the current macbook toolchain.

## Source

`/opt/homebrew/include/cadical.hpp` (CaDiCaL 3.0.0 via Homebrew).

## ExternalPropagator interface — methods available

```cpp
class ExternalPropagator {
public:
    virtual ~ExternalPropagator () {}

    // ============================================================
    // NOTIFICATION callbacks (CaDiCaL → propagator)
    // ============================================================

    // Called when literals are assigned (decision or propagation).
    // The propagator updates its internal state.
    virtual void notify_assignment(const std::vector<int> &lits) = 0;

    // Called when CaDiCaL enters a new decision level.
    virtual void notify_new_decision_level() = 0;

    // Called when CaDiCaL backtracks (the propagator must roll back state).
    virtual void notify_backtrack(size_t new_level) = 0;

    // Called when CaDiCaL has a candidate model. Propagator can reject
    // (return false) to force search continuation.
    virtual bool cb_check_found_model(const std::vector<int> &model) = 0;

    // ============================================================
    // CALLBACK methods (propagator → CaDiCaL)
    // ============================================================

    // Optional: propagator suggests a decision. Return 0 to defer to
    // CaDiCaL's heuristic. Return a literal to override.
    virtual int cb_decide() { return 0; }

    // Optional: propagator wants to propagate a literal. Return 0 to defer.
    // Return a literal that the propagator can justify with a reason clause.
    virtual int cb_propagate() { return 0; }

    // Required: when cb_propagate returns lit, CaDiCaL calls this to
    // assemble the reason clause literal-by-literal (return 0 to terminate).
    virtual int cb_add_reason_clause_lit(int propagated_lit) = 0;

    // Required: signal whether the propagator wants to add a clause.
    // is_forgettable: hint to CaDiCaL whether the clause can be GC'd.
    virtual bool cb_has_external_clause(bool &is_forgettable) = 0;

    // Required: when has_external_clause returns true, this assembles
    // the clause literal-by-literal.
    virtual int cb_add_external_clause_lit() = 0;
};
```

## Connecting to a CaDiCaL solver

```cpp
CaDiCaL::Solver *solver = new CaDiCaL::Solver();
MyPropagator prop;
solver->connect_external_propagator(&prop);
// ... add CNF, set options ...
int result = solver->solve();
solver->disconnect_external_propagator();
```

## Other observer hooks (less commonly used)

- `class Terminator { virtual bool terminate() = 0; };`
  — Allows external code to ask CaDiCaL to terminate (after any conflict).

- `class Learner { virtual bool learning(int size) = 0; virtual void learn(int lit) = 0; };`
  — Receives learned clauses (one literal at a time). Useful for
    snooping/logging but not for propagation.

- `class FixedAssignmentListener { virtual void notify_fixed_assignment(int) = 0; };`
  — Called when a literal becomes top-level fixed (level 0 propagation
    or unit clause). Useful for upstream-fixed-bit tracking.

## What was used in the killed Rule-4 propagator

`bets/programmatic_sat_propagator/propagators/cascade_propagator.cc`
implemented:
- `notify_assignment` → updated internal state per literal
- `notify_backtrack` → rolled back state
- `cb_propagate` + `cb_add_reason_clause_lit` → emitted Rule 4 forced-bit
  propagations
- `cb_check_found_model` → final consistency check
- `cb_decide` → continuous-trigger variant for Phase 2C experiment

What it DID NOT use:
- `Learner` — never observed solver's learned clauses (could have learned
  which diff-aux variables CDCL was deciding, informing trigger choice)
- `FixedAssignmentListener` — never observed top-level fixings (could have
  pre-computed Rule 4 implications when state vars become fixed)

## What forward_propagator.cpp does differently

`q5_alternative_attacks/forward_propagator.cpp`:
- Watches the **256 free-word variables** (W1[57..60] × 32 bits + W2's).
- Triggers `try_forward_propagate(widx)` when a complete free word is
  assigned.
- Computes forward SHA natively in C++ to derive register-value bits.
- Emits collision-register propagations via `cb_propagate`.

This is structurally different from Rule-4 because:
- It observes assignments to FREE WORDS (which CDCL DOES decide).
- It triggers on COMPLETE 32-bit assignments, not partial bits.
- The propagation goes FROM free-word literals TO state-bit consequences,
  matching CDCL's natural decision direction.

## Reopen recipe (for future worker)

If reopening the propagator bet:
1. Read this file + cascade_propagator.cc + forward_propagator.cpp.
2. Choose a propagator design that watches CDCL's natural decision basis
   (free-word literals or diff-aux literals).
3. Build with `g++ -O3 -std=c++17 -I/opt/homebrew/include
   forward_propagator.cpp -lcadical -o fwd_prop`.
4. Bench against `kissat --conflicts=500000` baseline on a current
   sr=61 cascade CNF.
5. Reopen formally if speedup ≥ 2× at 500k+ conflicts.

## Caveat

CaDiCaL 3.0.0 IPASIR-UP API may diverge in future versions. As of 2026-04-25
this is the macbook-installed version; fleet machines should `cadical
--version` to confirm before linking.
