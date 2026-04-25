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
    // Forced-zero variables (Rules 1+2+3): their SAT vars must be FALSE.
    // Stored as a map: var_id -> required_value (always 0 for now).
    // (We use map instead of unordered_map for stable iteration order in tests.)
    std::map<int, int> forced_zero_vars;

    // Rule 5 (R63.1: dc_63 = dg_63 bit-equality):
    // Each pair (cv, gv) is the SAT var for bit i of dc_63 / dg_63 respectively.
    // When one is assigned, the other must take the same value (modulo polarity
    // signs from the encoder's literal-as-XOR-aux representation).
    // dc_polarity / dg_polarity reflect whether the encoder's aux literal has
    // positive (=+1) or negative (=-1) polarity at this bit.
    struct EqPair {
        int cv;        // dc_63 bit-i SAT var (or 0 if constant)
        int dc_pol;    // +1 or -1 (sign of literal in encoder)
        int gv;        // dg_63 bit-i SAT var (or 0 if constant)
        int dg_pol;
    };
    // Indexed first by pair-GROUP (e.g., 0=dc_63↔dg_63 (R63.1),
    // 1=dA[61]↔dE[61] (R61.1 / Rule 4 specialization)), then by bit (0..31).
    // We store a flat vector and use stride 32.
    std::vector<EqPair> r63_eq_pairs;  // size = 32 * n_groups

    // For reverse lookup: SAT var -> (flat eq-pair index, side: 0 or 1).
    struct EqVarSide { int pair_idx; int side; }; // side: 0=c, 1=g
    std::unordered_map<int, EqVarSide> r63_eq_lookup;

    // Current value of each eq-pair side: -1=unassigned, 0=false, 1=true.
    struct AssignEvent { int pair_idx; int side; int prev; };
    std::vector<std::vector<AssignEvent>> level_eq_assignments;
    std::vector<std::pair<int, int>> r63_eq_state;  // [pair_idx] -> (c_val, g_val)

    // Pending propagations: literals we've decided to force but the solver
    // hasn't requested yet via cb_propagate.
    std::vector<int> pending_propagations;

    // For each pending propagation, remember the reason: a list of literals
    // that forced this propagation (negations form the reason clause body).
    std::vector<std::vector<int>> pending_reasons;

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
    long long n_rule5_fires = 0;
    long long n_rule4r61_fires = 0;

    CascadePropagator() {
        level_propagation_counts.push_back(0);
        level_eq_assignments.push_back({});
    }

    // Helper: queue a forced literal with its reason (input literals).
    // Reason convention: the reason clause is [propagated_lit] OR [neg(input)
    // for input in reason_lits], asserting "if all reason inputs hold then
    // propagated_lit holds." For unconditional axioms, reason_lits is empty.
    void queue_propagation(int lit, std::vector<int> reason_lits) {
        if (propagated.find(lit) != propagated.end()) return;  // already done
        propagated.insert(lit);
        pending_propagations.push_back(lit);
        pending_reasons.push_back(std::move(reason_lits));
        level_propagation_counts.back() = pending_propagations.size();
        n_propagations++;
    }

    // -------- IPASIR-UP API: required virtual methods --------

    void notify_assignment(const std::vector<int>& lits) override {
        n_assignments += lits.size();
        // Rule 5 (R63.1) — track dc_63 and dg_63 bit assignments.
        for (int lit : lits) {
            int var = std::abs(lit);
            auto it = r63_eq_lookup.find(var);
            if (it == r63_eq_lookup.end()) continue;

            int pair_idx = it->second.pair_idx;
            int side = it->second.side;
            // sat-value: true if lit > 0, false if lit < 0
            int sat_val = (lit > 0) ? 1 : 0;
            // Convert to differential-bit value via the encoder's polarity.
            // bit_val = sat_val XOR (pol < 0)
            const EqPair& pair = r63_eq_pairs[pair_idx];
            int pol = (side == 0) ? pair.dc_pol : pair.dg_pol;
            int bit_val = (pol > 0) ? sat_val : (1 - sat_val);

            // Record for backtrack
            int prev = (side == 0) ? r63_eq_state[pair_idx].first
                                   : r63_eq_state[pair_idx].second;
            level_eq_assignments.back().push_back({pair_idx, side, prev});

            if (side == 0) r63_eq_state[pair_idx].first = bit_val;
            else r63_eq_state[pair_idx].second = bit_val;

            // Check if the partner side is now forceable.
            int other_side = 1 - side;
            int other_var = (other_side == 0) ? pair.cv : pair.gv;
            if (other_var == 0) continue;  // partner is constant
            int other_pol = (other_side == 0) ? pair.dc_pol : pair.dg_pol;
            int other_state = (other_side == 0) ? r63_eq_state[pair_idx].first
                                                 : r63_eq_state[pair_idx].second;
            if (other_state == -1) {
                // Force partner to bit_val. Convert bit_val back to sat-val
                // using other_pol.
                int forced_sat_val = (other_pol > 0) ? bit_val : (1 - bit_val);
                int forced_lit = (forced_sat_val == 1) ? other_var : -other_var;
                // Reason: the negation of the input (`-lit`) and the
                // propagated literal forming the binary clause:
                //   [forced_lit, -lit]  meaning "lit → forced_lit"
                queue_propagation(forced_lit, {lit});
                if (pair_idx < 32) n_rule5_fires++;
                else n_rule4r61_fires++;
            }
        }
    }

    void notify_new_decision_level() override {
        level_propagation_counts.push_back(level_propagation_counts.back());
        level_eq_assignments.push_back({});
        n_decisions++;
    }

    void notify_backtrack(size_t new_level) override {
        n_backtracks++;
        if (new_level + 1 < level_propagation_counts.size()) {
            size_t kept = level_propagation_counts[new_level];
            level_propagation_counts.resize(new_level + 1);
            // Truncate pending_propagations + reasons. Also drop from
            // `propagated` set so they can re-fire.
            if (pending_propagations.size() > kept) {
                for (size_t i = kept; i < pending_propagations.size(); i++) {
                    propagated.erase(pending_propagations[i]);
                }
                pending_propagations.resize(kept);
                pending_reasons.resize(kept);
            }
        }
        // Undo Rule 5 state changes back to new_level.
        while (level_eq_assignments.size() > new_level + 1) {
            for (auto it = level_eq_assignments.back().rbegin();
                 it != level_eq_assignments.back().rend(); ++it) {
                if (it->side == 0) r63_eq_state[it->pair_idx].first = it->prev;
                else r63_eq_state[it->pair_idx].second = it->prev;
            }
            level_eq_assignments.pop_back();
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
        // First: drain the pending queue from notify_assignment-driven Rule 5.
        // pending_propagations holds literals queued but not yet returned.
        // We use a "next unsent" marker: scan for the next entry that the
        // solver hasn't seen yet (we mark "sent" by inserting into a set).
        for (size_t i = 0; i < pending_propagations.size(); i++) {
            int lit = pending_propagations[i];
            if (sent_to_solver.find(lit) == sent_to_solver.end()) {
                sent_to_solver.insert(lit);
                return lit;
            }
        }

        // Then: zero-forcing for Rules 1+2 (cascade-DP axioms).
        for (auto& [var_id, _] : forced_zero_vars) {
            int neg_lit = -var_id;
            if (propagated.find(neg_lit) == propagated.end()) {
                queue_propagation(neg_lit, {});  // unconditional axiom, no reason inputs
                sent_to_solver.insert(neg_lit);
                return neg_lit;
            }
        }
        return 0;  // Nothing to propagate
    }

    std::unordered_set<int> sent_to_solver;  // propagations the solver has consumed

    int cb_add_reason_clause_lit(int propagated_lit) override {
        // Reason clause format: [propagated_lit, -input_1, -input_2, ...]
        // i.e., "propagated_lit OR not(input_1) OR not(input_2)" which is
        // logically "input_1 AND input_2 → propagated_lit".
        //
        // For unconditional rules (1, 2): inputs is empty, clause is
        // just [propagated_lit] — a unit clause encoding the axiom.
        //
        // For Rule 5: inputs has one literal (the partner-side decision),
        // clause is [propagated_lit, -input] — a binary clause encoding
        // the bit-equality.
        static int reason_idx = -1;
        static int reason_state = 0;
        static const std::vector<int>* current_reason = nullptr;
        static int saved_lit = 0;

        if (saved_lit != propagated_lit) {
            // New reason clause requested. Find the index in pending_propagations.
            saved_lit = propagated_lit;
            reason_state = 0;
            reason_idx = -1;
            for (size_t i = 0; i < pending_propagations.size(); i++) {
                if (pending_propagations[i] == propagated_lit) {
                    reason_idx = (int)i;
                    current_reason = &pending_reasons[i];
                    break;
                }
            }
            if (reason_idx < 0) {
                // Shouldn't happen — propagated_lit must be in pending list.
                return 0;
            }
        }

        if (reason_state == 0) {
            reason_state = 1;
            return propagated_lit;
        }
        // State 1+: emit -input_k for each input.
        int input_idx = reason_state - 1;
        if (current_reason && input_idx < (int)current_reason->size()) {
            reason_state++;
            return -((*current_reason)[input_idx]);
        }
        return 0;  // terminate clause
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
    int ver = data["version"];
    if (ver != 1 && ver != 2) {
        std::cerr << "ERROR: unknown varmap version " << ver << "\n";
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
    // Rules 1+2: cascade diagonal + dE[60]=0 (Theorems 1+2).
    // Rule 3 (Mode FORCE three-filter): dE[61..63] = 0.
    // All four enforce zero-diff on specific (reg,round) cells.
    std::vector<std::pair<std::string, int>> zero_regs = {
        // Rule 1: cascade diagonal
        {"a", 57}, {"a", 58}, {"a", 59}, {"a", 60},
        {"b", 58}, {"b", 59}, {"b", 60},
        {"c", 59}, {"c", 60},
        {"d", 60},
        // Rule 2: dE[60] = 0
        {"e", 60},
        // Rule 3: dE[61..63] = 0 (three-filter — equivalent to full r=63 collision
        // under cascade-DP per Theorem 3).
        {"e", 61}, {"e", 62}, {"e", 63},
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

    // ---- Bit-equality groups ----
    // Group 0 (indices 0..31):  Rule 5  — dc_63 = dg_63        (R63.1)
    // Group 1 (indices 32..63): Rule 4 specialization at r=61 — dA[61] = dE[61]
    //   (since dT2_61 = 0 under cascade, the modular form da_61 = de_61 reduces
    //    to bit-equality identical in form to Rule 5).
    struct EqGroup {
        std::string left_reg; int left_round;
        std::string right_reg; int right_round;
        const char* label;
    };
    std::vector<EqGroup> eq_groups = {
        {"c", 63, "g", 63, "Rule 5  (dc_63 = dg_63)"},
        {"a", 61, "e", 61, "Rule 4@r=61 (dA[61] = dE[61])"},
    };
    int total_pairs = 32 * eq_groups.size();
    prop.r63_eq_pairs.resize(total_pairs);
    prop.r63_eq_state.assign(total_pairs, {-1, -1});

    for (size_t g = 0; g < eq_groups.size(); g++) {
        const auto& grp = eq_groups[g];
        auto left_it = aux_reg.find({grp.left_reg, grp.left_round});
        auto right_it = aux_reg.find({grp.right_reg, grp.right_round});
        if (left_it == aux_reg.end() || right_it == aux_reg.end()) {
            std::cerr << "WARN: " << grp.label << " — missing varmap; skipping\n";
            continue;
        }
        int n_registered = 0;
        for (int b = 0; b < 32; b++) {
            int left_lit = left_it->second[b];
            int right_lit = right_it->second[b];
            int flat_idx = (int)g * 32 + b;
            CascadePropagator::EqPair p;
            p.cv = (std::abs(left_lit) > 1) ? std::abs(left_lit) : 0;
            p.dc_pol = (left_lit > 0) ? 1 : -1;
            p.gv = (std::abs(right_lit) > 1) ? std::abs(right_lit) : 0;
            p.dg_pol = (right_lit > 0) ? 1 : -1;
            prop.r63_eq_pairs[flat_idx] = p;
            if (p.cv && p.gv) {
                prop.r63_eq_lookup[p.cv] = {flat_idx, 0};
                prop.r63_eq_lookup[p.gv] = {flat_idx, 1};
                n_registered++;
            }
        }
        std::cerr << grp.label << ": " << n_registered << " bit-pairs registered\n";
    }

    // Connect propagator (optional — skip with --no-propagator for baseline)
    if (use_propagator) {
        solver.connect_external_propagator(&prop);
        for (auto& [var, _] : prop.forced_zero_vars) {
            solver.add_observed_var(var);
        }
        // Also observe the Rule 5 vars
        for (auto& [var, _] : prop.r63_eq_lookup) {
            solver.add_observed_var(var);
        }
        std::cerr << "Propagator connected: " << prop.forced_zero_vars.size()
                  << " cascade-zero vars + " << prop.r63_eq_lookup.size()
                  << " Rule-5 vars observed\n";
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
              << "    of which Rule 5 fires:  " << prop.n_rule5_fires << "\n"
              << "    of which Rule 4@r=61:   " << prop.n_rule4r61_fires << "\n"
              << "  decisions:                " << prop.n_decisions << "\n"
              << "  backtracks:               " << prop.n_backtracks << "\n";

    if (result == 10) std::cout << "s SATISFIABLE\n";
    else if (result == 20) std::cout << "s UNSATISFIABLE\n";
    else std::cout << "s UNKNOWN\n";

    return (result == 10 || result == 20) ? 0 : 2;
}
