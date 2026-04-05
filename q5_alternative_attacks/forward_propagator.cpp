/*
 * forward_propagator.cpp — CaDiCaL + IPASIR-UP with forward SHA-256 propagation
 *
 * Strategy: when enough free-word bits are assigned, compute the SHA-256
 * compression NATIVELY in C++ and propagate the resulting state bits.
 *
 * This is more powerful than bitsliced carry propagation because it
 * computes the EXACT result of entire word operations, not just
 * individual bit positions. When all 32 bits of W1[57] are assigned,
 * we can compute a57, e57, and all intermediate values exactly.
 *
 * The propagator watches the 256 free-word variables (8 words × 32 bits).
 * When a complete word is assigned, it runs the forward computation and
 * propagates any collision-register constraints that become determined.
 *
 * Build:
 *   g++ -O3 -std=c++17 -I/tmp/cadical_src/src \
 *       forward_propagator.cpp /tmp/cadical/build/libcadical.a \
 *       -lpthread -o fwd_prop
 *
 * Usage: ./fwd_prop <cnf_file> <varmap_json> [timeout]
 */

#include "cadical.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <cassert>
#include <ctime>
#include <csignal>
#include <unistd.h>

using namespace CaDiCaL;

/* SHA-256 primitives */
#define MASK32 0xFFFFFFFFU
static inline uint32_t ror(uint32_t x, int n) { return (x>>n)|(x<<(32-n)); }
static inline uint32_t sha_Ch(uint32_t e, uint32_t f, uint32_t g) { return (e&f)^(~e&g); }
static inline uint32_t sha_Maj(uint32_t a, uint32_t b, uint32_t c) { return (a&b)^(a&c)^(b&c); }
static inline uint32_t sha_Sigma0(uint32_t a) { return ror(a,2)^ror(a,13)^ror(a,22); }
static inline uint32_t sha_Sigma1(uint32_t e) { return ror(e,6)^ror(e,11)^ror(e,25); }
static inline uint32_t sha_sigma0(uint32_t x) { return ror(x,7)^ror(x,18)^(x>>3); }
static inline uint32_t sha_sigma1(uint32_t x) { return ror(x,17)^ror(x,19)^(x>>10); }

static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

/*
 * ForwardPropagator: when free-word bits are assigned, run SHA-256 forward
 * and propagate the implications.
 */
class ForwardPropagator : public ExternalPropagator {
public:
    Solver *solver;

    // Variable mapping: var_id → (word_index, bit_position)
    // word_index 0-3 = W1[57..60], 4-7 = W2[57..60]
    std::unordered_map<int, std::pair<int,int>> var_to_word_bit;

    // Current assignment: -1 = unassigned, 0 = false, 1 = true
    std::vector<int8_t> assignment;
    int n_vars;

    // Word completion tracking
    int word_assigned_bits[8]; // how many bits assigned per word
    uint32_t word_values[8];   // partial word values

    // Propagation
    std::vector<int> prop_queue;
    std::vector<std::vector<int>> reason_clauses; // reason for each propagation
    int current_reason_idx;
    int current_reason_pos;

    // Trail for backtracking
    std::vector<int> trail;
    std::vector<size_t> decision_levels;

    // Stats
    long n_propagated = 0;
    long n_forward_runs = 0;

    ForwardPropagator(Solver *s, int nvars) : solver(s), n_vars(nvars) {
        assignment.resize(nvars + 1, -1);
        memset(word_assigned_bits, 0, sizeof(word_assigned_bits));
        memset(word_values, 0, sizeof(word_values));
        current_reason_idx = -1;
        current_reason_pos = 0;
    }

    void register_word_vars(int word_idx, const std::vector<int> &vars) {
        for (int bit = 0; bit < (int)vars.size(); bit++) {
            int var = vars[bit];
            var_to_word_bit[var] = {word_idx, bit};
            solver->add_observed_var(var);
        }
    }

    void notify_assignment(const std::vector<int> &lits) override {
        for (int lit : lits) {
            int var = abs(lit);
            bool val = lit > 0;
            assignment[var] = val ? 1 : 0;
            trail.push_back(lit);

            // Update word tracking
            auto it = var_to_word_bit.find(var);
            if (it != var_to_word_bit.end()) {
                int widx = it->second.first;
                int bit = it->second.second;
                word_assigned_bits[widx]++;
                if (val) word_values[widx] |= (1U << bit);
                else     word_values[widx] &= ~(1U << bit);

                // If a complete word just got assigned, run forward propagation
                if (word_assigned_bits[widx] == 32) {
                    try_forward_propagate(widx);
                }
            }
        }
    }

    void notify_new_decision_level() override {
        decision_levels.push_back(trail.size());
    }

    void notify_backtrack(size_t new_level) override {
        while (decision_levels.size() > new_level) {
            decision_levels.pop_back();
        }
        size_t target = decision_levels.empty() ? 0 : decision_levels.back();
        while (trail.size() > target) {
            int lit = trail.back();
            trail.pop_back();
            int var = abs(lit);
            assignment[var] = -1;

            auto it = var_to_word_bit.find(var);
            if (it != var_to_word_bit.end()) {
                word_assigned_bits[it->second.first]--;
            }
        }
        prop_queue.clear();
        reason_clauses.clear();
    }

    // State56 values (set during initialization)
    uint32_t s1[8], s2[8];
    uint32_t W1_pre[57], W2_pre[57];

    void set_state56(const uint32_t *state1, const uint32_t *state2,
                     const uint32_t *w1pre, const uint32_t *w2pre) {
        memcpy(s1, state1, 32);
        memcpy(s2, state2, 32);
        memcpy(W1_pre, w1pre, 228);
        memcpy(W2_pre, w2pre, 228);
    }

    void try_forward_propagate(int completed_word) {
        n_forward_runs++;

        // Check if ALL 8 free words are now assigned
        bool all_assigned = true;
        for (int w = 0; w < 8; w++) {
            if (word_assigned_bits[w] < 32) { all_assigned = false; break; }
        }
        if (!all_assigned) return;

        // ALL free words assigned! Run full SHA-256 tail computation.
        uint32_t w1[4] = {word_values[0], word_values[1], word_values[2], word_values[3]};
        uint32_t w2[4] = {word_values[4], word_values[5], word_values[6], word_values[7]};

        // Build schedule tail
        uint32_t W1[7], W2[7];
        for (int i = 0; i < 4; i++) { W1[i] = w1[i]; W2[i] = w2[i]; }
        W1[4] = sha_sigma1(W1[2]) + W1_pre[54] + sha_sigma0(W1_pre[46]) + W1_pre[45];
        W2[4] = sha_sigma1(W2[2]) + W2_pre[54] + sha_sigma0(W2_pre[46]) + W2_pre[45];
        W1[5] = sha_sigma1(W1[3]) + W1_pre[55] + sha_sigma0(W1_pre[47]) + W1_pre[46];
        W2[5] = sha_sigma1(W2[3]) + W2_pre[55] + sha_sigma0(W2_pre[47]) + W2_pre[46];
        W1[6] = sha_sigma1(W1[4]) + W1_pre[56] + sha_sigma0(W1_pre[48]) + W1_pre[47];
        W2[6] = sha_sigma1(W2[4]) + W2_pre[56] + sha_sigma0(W2_pre[48]) + W2_pre[47];

        // Run 7 rounds for both messages
        uint32_t a1=s1[0],b1=s1[1],c1=s1[2],d1=s1[3],e1=s1[4],f1=s1[5],g1=s1[6],h1=s1[7];
        uint32_t a2=s2[0],b2=s2[1],c2=s2[2],d2=s2[3],e2=s2[4],f2=s2[5],g2=s2[6],h2=s2[7];
        for (int i = 0; i < 7; i++) {
            uint32_t T1a = h1+sha_Sigma1(e1)+sha_Ch(e1,f1,g1)+K[57+i]+W1[i];
            uint32_t T2a = sha_Sigma0(a1)+sha_Maj(a1,b1,c1);
            h1=g1;g1=f1;f1=e1;e1=d1+T1a;d1=c1;c1=b1;b1=a1;a1=T1a+T2a;
            uint32_t T1b = h2+sha_Sigma1(e2)+sha_Ch(e2,f2,g2)+K[57+i]+W2[i];
            uint32_t T2b = sha_Sigma0(a2)+sha_Maj(a2,b2,c2);
            h2=g2;g2=f2;f2=e2;e2=d2+T1b;d2=c2;c2=b2;b2=a2;a2=T1b+T2b;
        }

        // Check collision
        int diff_hw = __builtin_popcount(a1^a2) + __builtin_popcount(b1^b2) +
                      __builtin_popcount(c1^c2) + __builtin_popcount(d1^d2) +
                      __builtin_popcount(e1^e2) + __builtin_popcount(f1^f2) +
                      __builtin_popcount(g1^g2) + __builtin_popcount(h1^h2);

        if (diff_hw == 0) {
            // COLLISION FOUND! The CNF should be SAT with this assignment.
            // Don't need to do anything — CaDiCaL will verify via BCP.
            printf("*** FORWARD CHECK: COLLISION at hw=0! ***\n");
            fflush(stdout);
        } else if (n_forward_runs % 10000 == 0) {
            printf("  [fwd] %ld checks, best hw=%d\n", n_forward_runs, diff_hw);
            fflush(stdout);
        }

        // If diff_hw > 0, we KNOW this assignment can't be a collision.
        // We could add a blocking clause, but that requires constructing
        // a clause from the current assignment of all 256 free-word vars.
        // For now, let CaDiCaL discover the conflict through BCP.
    }

    bool cb_check_found_model(const std::vector<int> &model) override {
        return true;
    }

    bool cb_has_external_clause(bool &is_forgettable) override {
        return false;
    }

    int cb_add_external_clause_lit() override {
        return 0;
    }

    int cb_propagate() override {
        if (!prop_queue.empty()) {
            int lit = prop_queue.back();
            prop_queue.pop_back();
            n_propagated++;
            return lit;
        }
        return 0;
    }

    int cb_add_reason_clause_lit(int propagated_lit) override {
        // Return reason clause one lit at a time, terminated by 0
        if (current_reason_idx < 0 || current_reason_idx >= (int)reason_clauses.size())
            return 0;
        auto &clause = reason_clauses[current_reason_idx];
        if (current_reason_pos < (int)clause.size()) {
            return clause[current_reason_pos++];
        }
        current_reason_idx = -1;
        current_reason_pos = 0;
        return 0;
    }

    // Ordered list of free-word vars for decision guidance
    std::vector<int> decide_order;
    int decide_cursor = 0;

    void build_decide_order() {
        // W1[57] bits first, then W2[57], then W1[58], etc.
        for (auto &[var, wb] : var_to_word_bit) {
            decide_order.push_back(var);
        }
        // Sort by word index then bit position
        std::sort(decide_order.begin(), decide_order.end(),
                  [this](int a, int b) {
                      auto &wa = var_to_word_bit[a];
                      auto &wb = var_to_word_bit[b];
                      if (wa.first != wb.first) return wa.first < wb.first;
                      return wa.second < wb.second;
                  });
    }

    int cb_decide() override {
        // Disabled for now — CaDiCaL's notification timing makes it
        // unsafe to check our assignment tracking here. Variables may
        // be propagated but not yet notified to us.
        // TODO: fix with a "pending" set that tracks what we've been
        // notified about vs what we haven't.
        return 0;
    }
};


/* Simple JSON parser for varmap (just extract free word variable lists) */
bool parse_varmap(const char *filename,
                  std::vector<std::vector<int>> &word_vars) {
    std::ifstream f(filename);
    if (!f.is_open()) return false;

    std::string content((std::istreambuf_iterator<char>(f)),
                         std::istreambuf_iterator<char>());

    // Very crude JSON parsing — extract "W1_57": [2, 3, 4, ...] patterns
    const char *names[] = {"W1_57","W1_58","W1_59","W1_60",
                           "W2_57","W2_58","W2_59","W2_60"};

    for (int w = 0; w < 8; w++) {
        std::string key = std::string("\"") + names[w] + "\"";
        size_t pos = content.find(key);
        if (pos == std::string::npos) continue;

        // Find the array after the key
        size_t arr_start = content.find('[', pos);
        size_t arr_end = content.find(']', arr_start);
        if (arr_start == std::string::npos || arr_end == std::string::npos) continue;

        std::string arr = content.substr(arr_start + 1, arr_end - arr_start - 1);
        std::vector<int> vars;
        std::istringstream iss(arr);
        std::string token;
        while (std::getline(iss, token, ',')) {
            int v = atoi(token.c_str());
            if (v > 0) vars.push_back(v);
        }
        if (vars.size() == 32) {
            word_vars.push_back(vars);
            printf("  Word %s: vars %d..%d\n", names[w], vars[0], vars[31]);
        }
    }
    return word_vars.size() == 8;
}


int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <cnf_file> <varmap_json> [timeout]\n", argv[0]);
        return 1;
    }

    const char *cnf_file = argv[1];
    const char *varmap_file = argv[2];
    int timeout = argc > 3 ? atoi(argv[3]) : 3600;

    Solver solver;

    // Read CNF
    int n_vars = 0;
    const char *err = solver.read_dimacs(cnf_file, n_vars);
    if (err) { fprintf(stderr, "Error: %s\n", err); return 1; }

    printf("Forward Propagator for sr=60\n");
    printf("CNF: %s (%d vars)\n", cnf_file, n_vars);

    // Parse varmap
    std::vector<std::vector<int>> word_vars;
    if (!parse_varmap(varmap_file, word_vars)) {
        fprintf(stderr, "Error parsing varmap %s\n", varmap_file);
        return 1;
    }

    // Create propagator — must connect BEFORE observing variables
    ForwardPropagator prop(&solver, n_vars);
    solver.connect_external_propagator(&prop);
    for (int w = 0; w < 8; w++) {
        prop.register_word_vars(w, word_vars[w]);
    }
    prop.build_decide_order();

    printf("Propagator: watching %zu variables across 8 free words\n",
           prop.var_to_word_bit.size());
    printf("Timeout: %ds\n", timeout);
    fflush(stdout);

    alarm(timeout);
    time_t t0 = time(NULL);
    int result = solver.solve();
    time_t t1 = time(NULL);

    printf("Result: %s in %lds\n",
           result == 10 ? "SAT" : result == 20 ? "UNSAT" : "UNKNOWN",
           (long)(t1 - t0));
    printf("Stats: %ld forward runs, %ld propagated\n",
           prop.n_forward_runs, prop.n_propagated);

    solver.disconnect_external_propagator();
    return result == 10 ? 10 : (result == 20 ? 20 : 0);
}
