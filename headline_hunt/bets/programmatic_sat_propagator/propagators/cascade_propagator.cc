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

    // ---- Rule 4 @ r=62, r=63: actual register-value bit tracking ----
    // For each (reg, round, pair) we track 32 bits. Each bit ∈ {-1, 0, 1}
    // (unassigned / false / true). Supports the eventual modular sum
    // reasoning at r=62 and r=63 (RULE4_R62_R63_DESIGN.md).
    //
    // Indexed by a flat register key: reg_key = reg_idx * 64 + round, where
    // reg_idx ∈ [0..7] for 'a'..'h'. We track rounds 57..63 (full residual
    // window) for both pair-1 and pair-2.
    static constexpr int N_REG_KEYS = 8 * 64;  // sparse; only some used
    struct PartialReg {
        std::array<int, 32> bits;  // -1, 0, 1
        int n_decided;
        PartialReg() : n_decided(0) { bits.fill(-1); }
    };
    std::map<int, PartialReg> actual_p1;  // reg_key -> partial value (pair-1)
    std::map<int, PartialReg> actual_p2;  // pair-2

    // Reverse: SAT var -> list of (reg_key, pair, bit_idx, polarity).
    // The encoder REUSES SAT vars across (reg, round) pairs that share the
    // same underlying value via SHA-256's shift register (e.g., a_57 = b_58
    // = c_59 = d_60, all share their bit-0 SAT var). When such a var is
    // assigned, ALL bindings are updated.
    struct ActualVarInfo { int reg_key; int pair; int bit; int polarity; };
    std::unordered_map<int, std::vector<ActualVarInfo>> actual_var_lookup;

    // Backtrack support: per-level undo stack of bit assignments.
    struct ActualUndo { int reg_key; int pair; int bit; int prev; };
    std::vector<std::vector<ActualUndo>> level_actual_undo;

    static int reg_key_for(const std::string& reg, int round) {
        int reg_idx = (reg.size() == 1 && reg[0] >= 'a' && reg[0] <= 'h')
                      ? (reg[0] - 'a') : -1;
        if (reg_idx < 0) return -1;
        return reg_idx * 64 + round;
    }
    static std::string reg_key_str(int reg_key) {
        char reg_c = 'a' + (reg_key / 64);
        int round = reg_key % 64;
        return std::string(1, reg_c) + "_" + std::to_string(round);
    }

    long long n_actual_assignments = 0;
    long long n_dT2_62_computable = 0;  // # times all 96 inputs decided
    long long n_partial_bits_decided_max = 0;  // max # bits of partial dT2_62 ever determined
    long long n_partial_dT2_62_fires = 0;  // # samples where partial-bit logic would force ≥1 dE[62] bit

    // ---- Phase 2C-Rule4 Option C: modular-diff aux for direct forcing ----
    // varmap_v3+ exposes aux_modular_diff[(reg, round)] — SAT vars representing
    // bit i of (w1 - w2) mod 2^32 with ripple-borrow ties to actual w1, w2 bits.
    // The propagator can force these directly when partial-bit logic determines
    // the modular bit value.
    std::map<std::pair<std::string, int>, std::vector<int>> aux_modular_diff;
    // Track which (reg_round, bit) we've already forced this level (to avoid re-fires)
    std::set<std::pair<int, int>> rule4_forced;  // (encoded reg_round, bit)
    std::vector<std::vector<std::pair<int, int>>> level_rule4_undo;
    long long n_rule4_r62_fires = 0;

    // ---- Helper utilities for Rule 4 r=62/63 firing logic ----

    // Read a 32-bit unsigned value from a PartialReg if all 32 bits are decided.
    // Returns -1 if any bit is undecided.
    static long long read_full_value(const PartialReg& preg) {
        if (preg.n_decided < 32) return -1;
        unsigned int v = 0;
        for (int b = 0; b < 32; b++) {
            if (preg.bits[b] == -1) return -1;  // belt-and-suspenders
            if (preg.bits[b] == 1) v |= (1u << b);
        }
        return (long long)v;
    }

    // Sigma0(x) = ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22).
    static unsigned int sigma0(unsigned int x) {
        auto rotr = [](unsigned int v, int n) {
            return (v >> n) | (v << (32 - n));
        };
        return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
    }

    // Maj(x, y, z) = (x & y) ^ (x & z) ^ (y & z).
    static unsigned int maj(unsigned int x, unsigned int y, unsigned int z) {
        return (x & y) ^ (x & z) ^ (y & z);
    }

    // Modular dSigma0 = (Sigma0(a1) - Sigma0(a2)) mod 2^32.
    // Returns -1 if either a1 or a2 isn't fully decided.
    static long long dSigma0_modular(const PartialReg& a1, const PartialReg& a2) {
        long long va1 = read_full_value(a1);
        long long va2 = read_full_value(a2);
        if (va1 < 0 || va2 < 0) return -1;
        unsigned int s1 = sigma0((unsigned int)va1);
        unsigned int s2 = sigma0((unsigned int)va2);
        return (long long)((s1 - s2) & 0xFFFFFFFFu);
    }

    // Modular dMaj = (Maj(a1_{r-1}, V60, V59) - Maj(a2_{r-1}, V60, V59)) mod 2^32
    // where V60 = a_60 (cascade-zero, value common between pairs) and similarly V59.
    // Caller passes V60 and V59 as the cascade-equal common values.
    static long long dMaj_modular_cascade(const PartialReg& a1_rm1,
                                          const PartialReg& a2_rm1,
                                          unsigned int V60, unsigned int V59) {
        long long va1 = read_full_value(a1_rm1);
        long long va2 = read_full_value(a2_rm1);
        if (va1 < 0 || va2 < 0) return -1;
        unsigned int m1 = maj((unsigned int)va1, V60, V59);
        unsigned int m2 = maj((unsigned int)va2, V60, V59);
        return (long long)((m1 - m2) & 0xFFFFFFFFu);
    }

    // Compute dT2_r when all required inputs are fully decided.
    // For r=62: dT2_62 = dSigma0(a_61) + dMaj(a_61, a_60, a_59) mod 2^32
    //   inputs: a1_61, a2_61 (varying), a_60 (cascade-zero), a_59 (cascade-zero)
    // Returns -1 if any input isn't fully decided.
    long long compute_dT2_62() {
        int key_a1_61 = reg_key_for("a", 61);
        int key_a_60 = reg_key_for("a", 60);
        int key_a_59 = reg_key_for("a", 59);
        auto p1_61_it = actual_p1.find(key_a1_61);
        auto p2_61_it = actual_p2.find(key_a1_61);
        auto p1_60_it = actual_p1.find(key_a_60);
        auto p1_59_it = actual_p1.find(key_a_59);
        if (p1_61_it == actual_p1.end() || p2_61_it == actual_p2.end()
            || p1_60_it == actual_p1.end() || p1_59_it == actual_p1.end())
            return -1;  // varmap doesn't expose these
        long long V60 = read_full_value(p1_60_it->second);
        long long V59 = read_full_value(p1_59_it->second);
        if (V60 < 0 || V59 < 0) return -1;
        long long ds0 = dSigma0_modular(p1_61_it->second, p2_61_it->second);
        if (ds0 < 0) return -1;
        long long dmaj = dMaj_modular_cascade(p1_61_it->second, p2_61_it->second,
                                              (unsigned int)V60, (unsigned int)V59);
        if (dmaj < 0) return -1;
        return (long long)(((unsigned int)ds0 + (unsigned int)dmaj) & 0xFFFFFFFFu);
    }

    // ---- Partial-bit primitives (from test_partial_sigma0.cc) ----

    static PartialReg partial_sigma0(const PartialReg& a) {
        PartialReg r;
        for (int i = 0; i < 32; i++) {
            int b1 = a.bits[(i + 2) % 32];
            int b2 = a.bits[(i + 13) % 32];
            int b3 = a.bits[(i + 22) % 32];
            if (b1 == -1 || b2 == -1 || b3 == -1) continue;
            r.bits[i] = b1 ^ b2 ^ b3;
            r.n_decided++;
        }
        return r;
    }

    static PartialReg partial_maj(const PartialReg& a, const PartialReg& b,
                                   const PartialReg& c) {
        PartialReg r;
        for (int i = 0; i < 32; i++) {
            int ai = a.bits[i], bi = b.bits[i], ci = c.bits[i];
            if (ai == -1 || bi == -1 || ci == -1) continue;
            r.bits[i] = (ai & bi) ^ (ai & ci) ^ (bi & ci);
            r.n_decided++;
        }
        return r;
    }

    static PartialReg partial_modular_sub(const PartialReg& a, const PartialReg& b) {
        PartialReg r;
        int borrow = 0;
        for (int i = 0; i < 32; i++) {
            if (a.bits[i] == -1 || b.bits[i] == -1) break;
            int diff = a.bits[i] - b.bits[i] - borrow;
            if (diff < 0) { r.bits[i] = diff + 2; borrow = 1; }
            else          { r.bits[i] = diff;     borrow = 0; }
            r.n_decided++;
        }
        return r;
    }

    static PartialReg partial_modular_add(const PartialReg& a, const PartialReg& b) {
        PartialReg r;
        int carry = 0;
        for (int i = 0; i < 32; i++) {
            if (a.bits[i] == -1 || b.bits[i] == -1) break;
            int sum = a.bits[i] + b.bits[i] + carry;
            r.bits[i] = sum & 1;
            carry = (sum >> 1) & 1;
            r.n_decided++;
        }
        return r;
    }

    // Compute partial dT2_62 = dSigma0(a_61) + dMaj(a_61, a_60, a_59) bit-by-bit.
    // Bit i is determined iff:
    //   - bits 0..i of dSigma0 are determined (via partial_sigma0 + modular_sub)
    //   - bits 0..i of dMaj are determined (similar)
    //   - bits 0..i of their sum (modular add) are determined
    // Returns a PartialReg; n_decided tells how many low bits are determined.
    PartialReg compute_partial_dT2_62() {
        PartialReg empty;
        int key_a1_61 = reg_key_for("a", 61);
        int key_a_60 = reg_key_for("a", 60);
        int key_a_59 = reg_key_for("a", 59);
        auto p1_61_it = actual_p1.find(key_a1_61);
        auto p2_61_it = actual_p2.find(key_a1_61);
        auto p1_60_it = actual_p1.find(key_a_60);
        auto p1_59_it = actual_p1.find(key_a_59);
        if (p1_61_it == actual_p1.end() || p2_61_it == actual_p2.end()
            || p1_60_it == actual_p1.end() || p1_59_it == actual_p1.end())
            return empty;
        // dSigma0 = Sigma0(a1_61) - Sigma0(a2_61) modular
        PartialReg ds0 = partial_modular_sub(
            partial_sigma0(p1_61_it->second),
            partial_sigma0(p2_61_it->second));
        // dMaj cascade: V60, V59 fully decided in pair-1 (cascade-equal in pair-2)
        // Use the cascade-zero common values (which are stored in actual_p1).
        PartialReg dmaj = partial_modular_sub(
            partial_maj(p1_61_it->second, p1_60_it->second, p1_59_it->second),
            partial_maj(p2_61_it->second, p1_60_it->second, p1_59_it->second));
        // dT2 = dSigma0 + dMaj modular
        return partial_modular_add(ds0, dmaj);
    }

    // For Rule 4 firing: would force bits of dE[r] = dA[r] - dT2_r modular.
    // Returns the partial dE[62] that would be implied by current state.
    // (Diagnostic only — does not yet generate forcing literals.)
    PartialReg compute_partial_forced_dE_62() {
        PartialReg empty;
        // Look up dA[62] aux register (the dE we want to force)
        // We need access to aux_reg from main; instead we use the actual values.
        // dA[62] = a1_62 - a2_62 modular (computed from actual values).
        int key_a_62 = reg_key_for("a", 62);
        auto p1_62_it = actual_p1.find(key_a_62);
        auto p2_62_it = actual_p2.find(key_a_62);
        if (p1_62_it == actual_p1.end() || p2_62_it == actual_p2.end())
            return empty;
        PartialReg dA62 = partial_modular_sub(p1_62_it->second, p2_62_it->second);
        PartialReg dT2_62 = compute_partial_dT2_62();
        // dE[62] = dA[62] - dT2_62 modular
        return partial_modular_sub(dA62, dT2_62);
    }

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
        level_actual_undo.push_back({});
        level_rule4_undo.push_back({});
    }

    // Try firing Rule 4 at r=62: force bits of aux_modular_diff[("e", 62)]
    // based on partial-bit reasoning.
    // Returns # of newly-forced bits.
    int try_fire_rule4_r62() {
        auto it = aux_modular_diff.find({"e", 62});
        if (it == aux_modular_diff.end()) return 0;
        const std::vector<int>& mod_diff_e62 = it->second;
        if (mod_diff_e62.size() < 32) return 0;

        PartialReg forced_dE62 = compute_partial_forced_dE_62();
        if (forced_dE62.n_decided == 0) return 0;

        int reg_key_e62 = reg_key_for("e", 62);
        int n_new = 0;
        for (int b = 0; b < 32; b++) {
            if (forced_dE62.bits[b] == -1) continue;
            // Already forced this bit at current state?
            std::pair<int, int> key{reg_key_e62, b};
            if (rule4_forced.find(key) != rule4_forced.end()) continue;

            int aux_lit = mod_diff_e62[b];
            if (std::abs(aux_lit) <= 1) continue;  // already constant
            int sat_var = std::abs(aux_lit);
            int aux_pol = (aux_lit > 0) ? 1 : -1;
            int target_bit = forced_dE62.bits[b];
            int target_sat_val = (aux_pol > 0) ? target_bit : (1 - target_bit);
            int forced_lit = (target_sat_val == 1) ? sat_var : -sat_var;

            // Build a minimal-but-sound reason clause: list ALL the relevant
            // currently-decided input literals that contribute to bit b's
            // determination. For now (sound but heavy): include all decided
            // bits of a_61, a_60, a_59 in both pairs, plus a_62 in both pairs.
            std::vector<int> reason_inputs;
            auto collect_decided = [&](int rk, int pair) {
                auto& m = (pair == 1) ? actual_p1 : actual_p2;
                auto pit = m.find(rk);
                if (pit == m.end()) return;
                const PartialReg& pr = pit->second;
                // Find the actual SAT var for each decided bit (reverse lookup).
                // Since SAT vars alias, we record them as positive lits matching
                // each bit's current value (so the reason is "if bit was the
                // value it currently is, then...").
                for (int bi = 0; bi < 32; bi++) {
                    if (pr.bits[bi] == -1) continue;
                    // Find ANY SAT var bound to (rk, pair, bi).
                    // We don't have a direct fwd index; we scan the bindings.
                    for (auto& [var_id, bindings] : actual_var_lookup) {
                        for (const auto& info : bindings) {
                            if (info.reg_key == rk && info.pair == pair && info.bit == bi) {
                                int sat_lit_value = (info.polarity > 0) ? pr.bits[bi]
                                                                        : (1 - pr.bits[bi]);
                                int input_lit = (sat_lit_value == 1) ? var_id : -var_id;
                                reason_inputs.push_back(input_lit);
                                goto next_bit;
                            }
                        }
                    }
                    next_bit:;
                }
            };
            collect_decided(reg_key_for("a", 61), 1);
            collect_decided(reg_key_for("a", 61), 2);
            collect_decided(reg_key_for("a", 60), 1);  // cascade-zero (V60)
            collect_decided(reg_key_for("a", 59), 1);  // cascade-zero (V59)
            collect_decided(reg_key_for("a", 62), 1);
            collect_decided(reg_key_for("a", 62), 2);

            // Reason inputs collected. Queue propagation.
            queue_propagation(forced_lit, std::move(reason_inputs));
            rule4_forced.insert(key);
            level_rule4_undo.back().push_back(key);
            n_new++;
            n_rule4_r62_fires++;
        }
        return n_new;
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

        // Rule 4 r=62/63 substrate: track actual register-value bits.
        // SAT vars are reused across (reg, round) pairs via shift register —
        // update ALL bindings when one is assigned.
        for (int lit : lits) {
            int var = std::abs(lit);
            auto av_it = actual_var_lookup.find(var);
            if (av_it == actual_var_lookup.end()) continue;
            int sat_val = (lit > 0) ? 1 : 0;
            for (const ActualVarInfo& info : av_it->second) {
                int bit_val = (info.polarity > 0) ? sat_val : (1 - sat_val);
                auto& reg_map = (info.pair == 1) ? actual_p1 : actual_p2;
                PartialReg& preg = reg_map[info.reg_key];
                int prev = preg.bits[info.bit];
                preg.bits[info.bit] = bit_val;
                if (prev == -1) preg.n_decided++;
                level_actual_undo.back().push_back(
                    {info.reg_key, info.pair, info.bit, prev});
                n_actual_assignments++;
            }
        }

        // Diagnostic: track how often the dT2_62 input set is fully decided.
        // Also: PARTIAL-BIT diagnostic — how often would partial-bit Rule 4
        // r=62 firing have determined ≥1 bit of dE[62]?
        // Sample at TWO rates: coarse (every 4096) for full-decided check,
        // fine (every 64) for partial-bit check (where firing is rarer).
        if (n_actual_assignments > 0 && (n_actual_assignments & 0xFFF) == 0) {
            if (compute_dT2_62() >= 0) n_dT2_62_computable++;
        }
        // Aggressive trigger: fire Rule 4 after EVERY notify_assignment
        // (not sampled). This is the smarter-trigger experiment per the
        // 500k-front-loaded finding — sample-based was missing fleeting
        // states where Rule 4 could have fired between backtracks.
        // Diagnostic: track partial-bit reasoning every 64 events, but
        // ALSO try to fire continuously.
        if (n_actual_assignments > 0 && (n_actual_assignments & 0x3F) == 0) {
            PartialReg forced_dE62 = compute_partial_forced_dE_62();
            if (forced_dE62.n_decided > 0) n_partial_dT2_62_fires++;
            if (forced_dE62.n_decided > n_partial_bits_decided_max) {
                n_partial_bits_decided_max = forced_dE62.n_decided;
            }
        }
        // Continuous trigger (smarter-trigger experiment, 2026-04-25).
        // Cost: O(32 * 32) = 1024 ops per call vs sampling. With 521k events,
        // worst case ~533M ops. Should still be fast on modern HW.
        if (!aux_modular_diff.empty()) {
            try_fire_rule4_r62();
        }

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
        level_actual_undo.push_back({});
        level_rule4_undo.push_back({});
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
        // Undo actual-register state changes back to new_level.
        while (level_actual_undo.size() > new_level + 1) {
            for (auto it = level_actual_undo.back().rbegin();
                 it != level_actual_undo.back().rend(); ++it) {
                auto& reg_map = (it->pair == 1) ? actual_p1 : actual_p2;
                PartialReg& preg = reg_map[it->reg_key];
                int cur = preg.bits[it->bit];
                if (cur != -1 && it->prev == -1) preg.n_decided--;
                preg.bits[it->bit] = it->prev;
            }
            level_actual_undo.pop_back();
        }
        // Undo Rule 4 forcings — let them re-fire if conditions still hold.
        while (level_rule4_undo.size() > new_level + 1) {
            for (auto& key : level_rule4_undo.back()) {
                rule4_forced.erase(key);
            }
            level_rule4_undo.pop_back();
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

bool load_varmap(const std::string& path, AuxRegMap& aux_reg,
                 AuxRegMap& actual_p1, AuxRegMap& actual_p2,
                 AuxRegMap& aux_modular_diff,
                 int& total_vars, int& version) {
    std::ifstream f(path);
    if (!f) {
        std::cerr << "ERROR: cannot open varmap " << path << "\n";
        return false;
    }
    json data;
    f >> data;
    version = data["version"];
    if (version != 1 && version != 2 && version != 3) {
        std::cerr << "ERROR: unknown varmap version " << version << "\n";
        return false;
    }
    total_vars = data["summary"]["total_vars"];
    for (auto& [key, lits] : data["aux_reg"].items()) {
        auto pos = key.rfind('_');
        std::string reg = key.substr(0, pos);
        int r = std::stoi(key.substr(pos + 1));
        std::vector<int> lit_vec;
        for (auto& l : lits) lit_vec.push_back(l);
        aux_reg[{reg, r}] = lit_vec;
    }
    if (version >= 2) {
        if (data.contains("actual_p1")) {
            for (auto& [key, lits] : data["actual_p1"].items()) {
                auto pos = key.rfind('_');
                std::string reg = key.substr(0, pos);
                int r = std::stoi(key.substr(pos + 1));
                std::vector<int> lit_vec;
                for (auto& l : lits) lit_vec.push_back(l);
                actual_p1[{reg, r}] = lit_vec;
            }
        }
        if (data.contains("actual_p2")) {
            for (auto& [key, lits] : data["actual_p2"].items()) {
                auto pos = key.rfind('_');
                std::string reg = key.substr(0, pos);
                int r = std::stoi(key.substr(pos + 1));
                std::vector<int> lit_vec;
                for (auto& l : lits) lit_vec.push_back(l);
                actual_p2[{reg, r}] = lit_vec;
            }
        }
    }
    if (version >= 3) {
        if (data.contains("aux_modular_diff")) {
            for (auto& [key, lits] : data["aux_modular_diff"].items()) {
                auto pos = key.rfind('_');
                std::string reg = key.substr(0, pos);
                int r = std::stoi(key.substr(pos + 1));
                std::vector<int> lit_vec;
                for (auto& l : lits) lit_vec.push_back(l);
                aux_modular_diff[{reg, r}] = lit_vec;
            }
        }
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
    AuxRegMap actual_p1_map, actual_p2_map, aux_modular_diff_map;
    int total_vars = 0;
    int varmap_version = 0;
    if (!load_varmap(varmap_path, aux_reg, actual_p1_map, actual_p2_map,
                     aux_modular_diff_map, total_vars, varmap_version)) return 1;
    std::cerr << "Loaded varmap v" << varmap_version << ": "
              << aux_reg.size() << " (reg,round) entries, "
              << "total_vars=" << total_vars << "\n";
    if (varmap_version >= 2) {
        std::cerr << "  actual_p1: " << actual_p1_map.size()
                  << " entries; actual_p2: " << actual_p2_map.size() << " entries\n";
    }
    if (varmap_version >= 3) {
        std::cerr << "  aux_modular_diff: " << aux_modular_diff_map.size()
                  << " entries (Rule 4 firing targets)\n";
    }

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

    // ---- Rule 4 r=62/63 substrate: register actual-value vars from varmap v2 ----
    // For now we just track them; the actual modular sum reasoning is the
    // dedicated next phase (RULE4_R62_R63_DESIGN.md). Tracking them here
    // exercises the data structures and validates backtrack safety.
    int n_actual_registered = 0;
    auto register_actuals = [&](const AuxRegMap& src, int pair) {
        for (auto& [key, lits] : src) {
            const auto& [reg, r] = key;
            // Track the rounds and registers that Rule 4 r=62/63 will need:
            // a, b, c at r ∈ {59, 60, 61, 62}.
            if (r < 59 || r > 62) continue;
            if (reg != "a" && reg != "b" && reg != "c") continue;
            int reg_key = CascadePropagator::reg_key_for(reg, r);
            for (int b = 0; b < 32; b++) {
                int lit = lits[b];
                if (std::abs(lit) <= 1) continue;
                int var = std::abs(lit);
                int pol = (lit > 0) ? 1 : -1;
                // 1:many lookup — append, don't overwrite.
                prop.actual_var_lookup[var].push_back(
                    {reg_key, pair, b, pol});
                n_actual_registered++;
            }
        }
    };
    if (varmap_version >= 2) {
        register_actuals(actual_p1_map, 1);
        register_actuals(actual_p2_map, 2);
        std::cerr << "Rule 4 r=62/63 substrate: " << n_actual_registered
                  << " actual-register SAT vars registered (a,b,c at r=59..62)\n";
    }

    // Copy aux_modular_diff into the propagator for Rule 4 firing.
    int n_modular_diff_vars = 0;
    if (varmap_version >= 3) {
        for (auto& [key, lits] : aux_modular_diff_map) {
            prop.aux_modular_diff[key] = lits;
            for (int lit : lits) {
                if (std::abs(lit) > 1) n_modular_diff_vars++;
            }
        }
        std::cerr << "Rule 4 firing targets: " << n_modular_diff_vars
                  << " modular-diff aux SAT vars across "
                  << prop.aux_modular_diff.size() << " (reg,round) entries\n";
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
        // And the Rule 4 r=62/63 substrate vars
        for (auto& [var, _] : prop.actual_var_lookup) {
            solver.add_observed_var(var);
        }
        // And the Rule 4 firing target vars (aux_modular_diff)
        for (auto& [key, lits] : prop.aux_modular_diff) {
            for (int lit : lits) {
                if (std::abs(lit) > 1) {
                    solver.add_observed_var(std::abs(lit));
                }
            }
        }
        std::cerr << "Propagator connected: " << prop.forced_zero_vars.size()
                  << " cascade-zero vars + " << prop.r63_eq_lookup.size()
                  << " Rule-5 vars + " << prop.actual_var_lookup.size()
                  << " actual-register vars observed\n";
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
              << "    of which Rule 4@r=62 forcings: " << prop.n_rule4_r62_fires << "\n"
              << "  actual-reg bit assigns:   " << prop.n_actual_assignments << "\n"
              << "  dT2_62 computable (sample, full): " << prop.n_dT2_62_computable
              << " (out of ~" << (prop.n_actual_assignments / 4096) << " samples)\n"
              << "  dT2_62 partial-bit firing samples: "
              << prop.n_partial_dT2_62_fires << " ("
              << "max bits forced in any sample: "
              << prop.n_partial_bits_decided_max << ")\n"
              << "  decisions:                " << prop.n_decisions << "\n"
              << "  backtracks:               " << prop.n_backtracks << "\n";

    if (result == 10) std::cout << "s SATISFIABLE\n";
    else if (result == 20) std::cout << "s UNSATISFIABLE\n";
    else std::cout << "s UNKNOWN\n";

    return (result == 10 || result == 20) ? 0 : 2;
}
