// cascade_propagator_smoke.cc
//
// Phase 2A smoke test: minimal CaDiCaL::ExternalPropagator subclass that does
// nothing, just verifies the IPASIR-UP API compiles and links against local
// CaDiCaL and that the lifecycle (connect, add_observed_var, solve, disconnect)
// works end-to-end.
//
// Build:
//   g++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
//       cascade_propagator_smoke.cc -lcadical -o cascade_propagator_smoke
//
// Verified 2026-04-25 against CaDiCaL 3.0.0 (homebrew). Returned 10 (SAT) as expected.

#include <cadical.hpp>
#include <vector>
#include <cstdio>

class NullPropagator : public CaDiCaL::ExternalPropagator {
public:
  void notify_assignment(const std::vector<int>& /*lits*/) override {}
  void notify_new_decision_level() override {}
  void notify_backtrack(size_t /*new_level*/) override {}
  bool cb_check_found_model(const std::vector<int>& /*model*/) override { return true; }
  bool cb_has_external_clause(bool& is_forgettable) override {
    is_forgettable = false;
    return false;
  }
  int cb_add_external_clause_lit() override { return 0; }
  // cb_propagate, cb_decide, cb_add_reason_clause_lit use default no-op impls.
};

int main() {
  CaDiCaL::Solver solver;

  // Disable factor checks so we can add literals without manual variable
  // declarations (purely for this smoke test).
  solver.set("check", 0);
  solver.set("factor", 0);

  NullPropagator prop;
  solver.connect_external_propagator(&prop);
  solver.add_observed_var(1);

  // Trivial CNF: (1) — single positive unit clause.
  solver.add(1); solver.add(0);

  int result = solver.solve();
  solver.disconnect_external_propagator();

  printf("smoke: solver.solve() returned %d (expected 10 = SAT)\n", result);
  return result == 10 ? 0 : 1;
}
