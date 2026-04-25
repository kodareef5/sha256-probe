// cascade_propagator.cc
//
// Phase 2B C++ implementation of cascade-DP propagation rules for CaDiCaL
// via IPASIR-UP ExternalPropagator API.
//
// Port of propagators/rules.py (Phase 1 Python prototype). Currently
// implements RULES 1, 2 (cascade diagonal + dE[60]=0 zero-forcing) with
// reason-clause provision. Future phases add Rules 3-5.
//
// Build:
//   g++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
//       cascade_propagator.cc -lcadical -o cascade_propagator
//
// Usage:
//   ./cascade_propagator <cnf-path> <varmap-path>
//
// The propagator uses the encoder's varmap sidecar to map between SAT
// variable IDs and (register, round, bit) coordinates.

#include <cadical.hpp>
#include <nlohmann/json.hpp>

#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using json = nlohmann::json;

class CascadePropagator : public CaDiCaL::ExternalPropagator {
public:
    // Forced-zero variables (Rules 1+2): their SAT vars must be FALSE.
    // Stored as a map: var_id -> required_value (always 0 for now).
    // (We use map instead of unordered_map for stable iteration order in tests.)
    std::map<int, int> forced_zero_vars;

    // Pending propagations: literals we've decided to force but the solver
    // hasn't requested yet via cb_propagate.
    std::vector<int> pending_propagations;

    // Set of literals already propagated (avoid re-propagating).
    std::unordered_set<int> propagated;

    // Decision-level stack: how many propagations we've made at each level.
    // Used to undo on notify_backtrack.
    std::vector<size_t> level_propagation_counts;

    // Statistics
    long long n_assignments = 0;
    long long n_propagations = 0;
    long long n_decisions = 0;
    long long n_backtracks = 0;

    CascadePropagator() {
        level_propagation_counts.push_back(0);
    }

    // -------- IPASIR-UP API: required virtual methods --------

    void notify_assignment(const std::vector<int>& lits) override {
        n_assignments += lits.size();
        // For Rules 1+2, no need to track assignments — the rules fire
        // unconditionally based on the cascade-DP setup. Future rules
        // (4, 5) will need to update internal modular state here.
    }

    void notify_new_decision_level() override {
        level_propagation_counts.push_back(level_propagation_counts.back());
        n_decisions++;
    }

    void notify_backtrack(size_t new_level) override {
        n_backtracks++;
        // Pop level_propagation_counts back to new_level + 1.
        // The "kept" count is level_propagation_counts[new_level].
        if (new_level + 1 < level_propagation_counts.size()) {
            size_t kept = level_propagation_counts[new_level];
            level_propagation_counts.resize(new_level + 1);
            // Truncate pending_propagations to kept count.
            // (For Rules 1+2, propagations are unconditional axioms — they
            // CAN be re-fired after backtrack. But to avoid double-firing,
            // we trim and let cb_propagate refill.)
            if (pending_propagations.size() > kept) {
                pending_propagations.resize(kept);
            }
        }
    }

    bool cb_check_found_model(const std::vector<int>& /*model*/) override {
        // Rules 1+2 are zero-forcing — if cb_propagate fired correctly,
        // the model already satisfies them. Return true (accept the model).
        return true;
    }

    bool cb_has_external_clause(bool& is_forgettable) override {
        is_forgettable = false;  // cascade structure is invariant; persist clauses
        return false;  // No clauses to add for Rules 1+2 (unit clauses inline)
    }

    int cb_add_external_clause_lit() override {
        return 0;  // No external clauses
    }

    // -------- Optional methods --------

    int cb_propagate() override {
        // Find the next forced-zero variable that hasn't been propagated yet.
        for (auto& [var_id, _] : forced_zero_vars) {
            int neg_lit = -var_id;
            if (propagated.find(neg_lit) == propagated.end()) {
                propagated.insert(neg_lit);
                pending_propagations.push_back(neg_lit);
                level_propagation_counts.back() = pending_propagations.size();
                n_propagations++;
                return neg_lit;
            }
        }
        return 0;  // Nothing to propagate
    }

    int cb_add_reason_clause_lit(int propagated_lit) override {
        // For Rules 1+2 (cascade-DP axioms), the reason is unconditional —
        // the literal is always FALSE under cascade-DP. The minimal valid
        // reason clause is the unit clause [propagated_lit] itself.
        // CaDiCaL expects: the reason clause MUST contain propagated_lit.
        //
        // We implement: emit propagated_lit, then 0 to terminate.
        // This makes the clause [propagated_lit] which is the unit clause
        // that's tautologically valid in cascade-DP context.
        //
        // Note: this is sound IFF the user has committed to cascade-DP
        // search. The propagator is restricting the search space; the
        // unit clause is the formal record of that restriction.
        static int state = 0;
        static int saved_lit = 0;
        if (saved_lit != propagated_lit) {
            saved_lit = propagated_lit;
            state = 0;
        }
        if (state == 0) { state = 1; return propagated_lit; }
        return 0;
    }
};


// -------- Varmap loading --------

// Map (reg, round) -> 32 SAT-var literals
using AuxRegMap = std::map<std::pair<std::string, int>, std::vector<int>>;

bool load_varmap(const std::string& path, AuxRegMap& aux_reg, int& total_vars) {
    std::ifstream f(path);
    if (!f) {
        std::cerr << "ERROR: cannot open varmap " << path << "\n";
        return false;
    }
    json data;
    f >> data;
    if (data["version"] != 1) {
        std::cerr << "ERROR: unknown varmap version " << data["version"] << "\n";
        return false;
    }
    total_vars = data["summary"]["total_vars"];
    for (auto& [key, lits] : data["aux_reg"].items()) {
        // key is "<reg>_<round>"
        auto pos = key.rfind('_');
        std::string reg = key.substr(0, pos);
        int r = std::stoi(key.substr(pos + 1));
        std::vector<int> lit_vec;
        for (auto& l : lits) lit_vec.push_back(l);
        aux_reg[{reg, r}] = lit_vec;
    }
    return true;
}


// -------- DIMACS CNF loader --------

bool load_cnf(const std::string& path, CaDiCaL::Solver& solver) {
    std::ifstream f(path);
    if (!f) {
        std::cerr << "ERROR: cannot open CNF " << path << "\n";
        return false;
    }
    std::string line;
    int n_clauses = 0;
    while (std::getline(f, line)) {
        if (line.empty() || line[0] == 'c') continue;
        if (line[0] == 'p') continue;
        // Parse clause: space-separated ints, ending with 0
        size_t i = 0;
        while (i < line.size()) {
            // Skip whitespace
            while (i < line.size() && std::isspace((unsigned char)line[i])) i++;
            if (i >= line.size()) break;
            // Parse integer
            size_t j = i;
            if (line[j] == '-') j++;
            while (j < line.size() && std::isdigit((unsigned char)line[j])) j++;
            int lit = std::stoi(line.substr(i, j - i));
            solver.add(lit);
            if (lit == 0) n_clauses++;
            i = j;
        }
    }
    std::cerr << "Loaded " << n_clauses << " clauses from " << path << "\n";
    return true;
}


int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: " << argv[0]
                  << " <cnf-path> <varmap-path> [--conflicts=N] [--no-propagator]\n";
        return 1;
    }
    std::string cnf_path = argv[1];
    std::string varmap_path = argv[2];
    long long conflict_limit = 0;  // 0 = no limit
    bool use_propagator = true;
    for (int i = 3; i < argc; i++) {
        std::string arg = argv[i];
        if (arg.rfind("--conflicts=", 0) == 0) {
            conflict_limit = std::stoll(arg.substr(12));
        } else if (arg == "--no-propagator") {
            use_propagator = false;
        }
    }

    // Load varmap
    AuxRegMap aux_reg;
    int total_vars = 0;
    if (!load_varmap(varmap_path, aux_reg, total_vars)) return 1;
    std::cerr << "Loaded varmap: " << aux_reg.size() << " (reg,round) entries, "
              << "total_vars=" << total_vars << "\n";

    // Set up solver
    CaDiCaL::Solver solver;
    solver.set("check", 0);
    solver.set("factor", 0);
    if (conflict_limit > 0) {
        solver.limit("conflicts", conflict_limit);
        std::cerr << "Conflict limit: " << conflict_limit << "\n";
    }

    // Build cascade propagator
    CascadePropagator prop;

    // Rules 1+2: cascade-zero registers under force-mode interpretation:
    //   dA[57..60] = 0  (Theorem 1)
    //   dB[58..60] = 0
    //   dC[59..60] = 0
    //   dD[60] = 0
    //   dE[60] = 0      (Theorem 2)
    std::vector<std::pair<std::string, int>> zero_regs = {
        {"a", 57}, {"a", 58}, {"a", 59}, {"a", 60},
        {"b", 58}, {"b", 59}, {"b", 60},
        {"c", 59}, {"c", 60},
        {"d", 60},
        {"e", 60},
    };
    int n_observed = 0;
    int n_const_already = 0;
    for (auto& [reg, r] : zero_regs) {
        auto it = aux_reg.find({reg, r});
        if (it == aux_reg.end()) {
            std::cerr << "WARN: varmap missing " << reg << "_" << r << "\n";
            continue;
        }
        for (int lit : it->second) {
            if (lit == 1) {
                std::cerr << "WARN: " << reg << "_" << r
                          << " has constant-TRUE bit (cascade-DP infeasible?)\n";
                return 2;
            }
            if (lit == -1) {
                n_const_already++;
                continue;  // already false, no need to force
            }
            // Mark this var as needing to be forced false
            int var = std::abs(lit);
            // If literal is positive: we want bit=0, so var=false (force -var).
            // If literal is negative: we want bit=0, so var=true (force +var).
            // Either way, the FORCED LITERAL is -lit (the negation of the
            // assertion that says "bit is set").
            prop.forced_zero_vars[var] = (lit > 0) ? 0 : 1;
            n_observed++;
        }
    }
    std::cerr << "Cascade-zero targets: " << n_observed << " SAT vars observed, "
              << n_const_already << " bits already const-false\n";

    // Connect propagator (optional — skip with --no-propagator for baseline)
    if (use_propagator) {
        solver.connect_external_propagator(&prop);
        for (auto& [var, _] : prop.forced_zero_vars) {
            solver.add_observed_var(var);
        }
        std::cerr << "Propagator connected with "
                  << prop.forced_zero_vars.size() << " observed cascade-zero vars\n";
    } else {
        std::cerr << "Running WITHOUT propagator (baseline)\n";
    }

    // Load CNF
    if (!load_cnf(cnf_path, solver)) return 1;

    // Solve
    std::cerr << "Solving" << (use_propagator ? " with cascade propagator" : "") << "...\n";
    int result = solver.solve();
    if (use_propagator) {
        solver.disconnect_external_propagator();
    }

    std::cerr << "\nResult: " << result << " (10=SAT, 20=UNSAT, 0=UNKNOWN)\n";
    std::cerr << "Propagator stats:\n"
              << "  notify_assignment events: " << prop.n_assignments << "\n"
              << "  cb_propagate fires:       " << prop.n_propagations << "\n"
              << "  decisions:                " << prop.n_decisions << "\n"
              << "  backtracks:               " << prop.n_backtracks << "\n";

    if (result == 10) std::cout << "s SATISFIABLE\n";
    else if (result == 20) std::cout << "s UNSATISFIABLE\n";
    else std::cout << "s UNKNOWN\n";

    return (result == 10 || result == 20) ? 0 : 2;
}
