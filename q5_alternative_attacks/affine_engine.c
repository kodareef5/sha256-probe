/*
 * affine_engine.c — Skeleton for the Affine Bit-Serial Collision Finder
 *
 * ARCHITECTURE NOTES (think before coding):
 *
 * The state is a pool of "worlds." Each world has:
 *   - A GF(2) constraint system (tracks what we know about the 16 variables)
 *   - 8 register values for msg1, each N-bit, each bit an AffineForm
 *   - 8 register values for msg2, same
 *   - 7×7 carry-in bits for msg1 (one per addition per round, for next bit)
 *   - 7×7 carry-in bits for msg2
 *
 * Processing order: bit 0, bit 1, ..., bit N-1.
 * At each bit k, process rounds 0-6 (= SHA rounds 57-63).
 * At each round, process BOTH messages.
 * At each message, the round function at bit k does:
 *
 *   1. sig1_e = Sigma1(e)[k] = e[(k+r0)%N] XOR e[(k+r1)%N] XOR e[(k+r2)%N]
 *      → This is just XOR of three AffineForm values. FREE. No branching.
 *      → The rotated positions may reference bits we haven't "processed" yet,
 *        but those bits are STORED as AffineForm (symbolic). That's fine.
 *
 *   2. ch = Ch(e,f,g)[k]. If e[k] is concrete: ch = e?f:g. No branch.
 *      If e[k] is symbolic: BRANCH (e=0 → ch=g, e=1 → ch=f).
 *      Add constraint to GF2. Prune contradictions.
 *
 *   3. T1 = h[k] + sig1_e + ch + K[rnd][k] + W[rnd][k]
 *      This is a CHAIN of additions. Each addition at bit k:
 *        z[k] = x[k] XOR y[k] XOR carry_in
 *        carry_out = maj(x[k], y[k], carry_in)
 *      If x[k] and y[k] are both concrete: no branch, carry determined.
 *      If either is symbolic: BRANCH on the symbolic operand(s).
 *      IMPORTANT: the intermediate results become concrete after branching.
 *      So each addition in the chain sees the PREVIOUS addition's concrete output.
 *
 *      The T1 chain has 4 additions: (h+sig1), (+ch), (K+W), (prev+KW).
 *      W[rnd][k] for free rounds = variable. For schedule rounds = computed.
 *
 *   4. sig0_a = Sigma0(a)[k]. Same as sig1_e. FREE.
 *
 *   5. maj = Maj(a,b,c)[k]. If b==c (concrete, equal): maj=b. No branch.
 *      If b!=c (concrete, unequal): maj=a. Linear. No branch.
 *      If b or c symbolic: BRANCH.
 *
 *   6. T2 = sig0_a + maj. One addition. May branch.
 *
 *   7. new_e[k] = d[k] + T1. One addition. May branch.
 *
 *   8. new_a[k] = T1 + T2. One addition. May branch.
 *
 *   9. Shift register: h←g, g←f, f←e, e←new_e, d←c, c←b, b←a, a←new_a.
 *      ONLY updates position [k]. Other positions unchanged.
 *
 * After processing both messages at all 7 rounds for bit k:
 *   10. COLLISION CONSTRAINT: for each register r (0-7):
 *       msg1.reg[r][k] XOR msg2.reg[r][k] = 0
 *       This is an AffineForm equation. Add to GF2. Prune contradictions.
 *       THIS IS WHERE THE PRUNING HAPPENS.
 *
 * The collision constraint at each bit gives 8 equations.
 * Over N=4 bits: 32 equations in 16 variables = heavily overdetermined.
 * Expected: massive pruning. 65536 → ~49.
 *
 * IMPLEMENTATION PLAN:
 *
 * Phase 1: Data structures (AF, GF2, State) — DONE in previous files.
 *
 * Phase 2: Helper functions
 *   - af_sigma1_bit(regs_e, bit) → AF         [done]
 *   - af_sigma0_bit(regs_a, bit) → AF         [done]
 *   - af_ch_bit(e,f,g, sys) → expand states   [done]
 *   - af_maj_bit(a,b,c, sys) → expand states  [done]
 *   - af_add_one_bit(x,y,carry_in, sys) → expand states  [done]
 *
 * Phase 3: Round function at one bit
 *   - process_round_bit(states, bit, round, msg) → states
 *   - This calls the helpers in sequence: sigma1, ch, T1 chain, sigma0, maj, T2, new_e, new_a, shift
 *
 * Phase 4: Main loop
 *   - for bit in 0..N-1:
 *       for round in 0..6:
 *         states = process_round_bit(states, bit, round, 0)  // msg1
 *         states = process_round_bit(states, bit, round, 1)  // msg2
 *       states = collision_prune(states, bit)
 *
 * Phase 5: Extract collisions from surviving states
 *
 * KEY INSIGHT I KEEP FORGETTING:
 * The AffineForm for each register bit DOES get updated during round processing.
 * After the shift register update at bit k:
 *   regs[0][k] = new_a[k]  (an AffineForm, possibly symbolic)
 *   regs[4][k] = new_e[k]  (an AffineForm)
 *   regs[1][k] = old regs[0][k]  (shift)
 *   etc.
 * These updated forms are what later rounds and later bits SEE.
 * So when round 58 computes Sigma1(e57)[k], it reads e57[k+r] which
 * was set during round 57's shift register update. If round 57 at
 * bit (k+r) hasn't been processed yet, e57[k+r] is still the INITIAL
 * constant value. If it HAS been processed (bit < k+r at a previous
 * iteration), it's the updated symbolic form.
 *
 * THIS IS WHY THE BIT-SERIAL APPROACH WORKS: the affine forms carry
 * the symbolic information across bit positions and rounds automatically.
 * The rotation "frontier" is handled by the fact that unprocessed bits
 * retain their initial (constant or variable) affine forms.
 *
 * SCHEDULE WORDS (rounds 61-63):
 * W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
 * sigma1(W[59])[k] = W[59][(k+r0)%N] XOR W[59][(k+r1)%N] XOR (k+s < N ? W[59][k+s] : 0)
 * W[59] bits are variables (v_{2*N+0} to v_{2*N+N-1}), possibly resolved by GF2.
 * sigma1 of these is just XOR of AffineForm values — FREE.
 * Then the addition W[61] = sigma1 + const + const + const needs carry branching.
 *
 * So schedule rounds ARE handled by the same affine machinery. Good.
 *
 * MEMORY ESTIMATE at N=4:
 * State size: GF2 system (~NV*5 = 80 bytes) + regs (2*8*4*5 = 320 bytes)
 *           + carries (2*7*7 = 98 bytes) = ~500 bytes per state.
 * At 65536 max states: 32MB. Fits easily.
 * At N=8: same structure, ~1000 bytes per state. At 260 states: 260KB. Trivial.
 * At N=32: ~4000 bytes per state. At ~2^32 states: too much.
 *          But with pruning: at ~830M states: ~3.3TB. Still too much.
 *          HOWEVER: at intermediate bits, state count is much smaller.
 *          And with disk-backed swap: feasible on the server.
 *
 * FOR NOW: implement at N=4, verify 49 collisions, measure state counts per bit.
 */

/* ========== Implementation follows below ========== */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

/* TODO: implement the skeleton above.
 * Start with Phase 1-2 (data structures + helpers).
 * Then Phase 3 (one round at one bit).
 * Then Phase 4 (main loop).
 * Then Phase 5 (extraction).
 *
 * Each phase should be testable independently.
 */

int main() {
    printf("affine_engine.c — skeleton only\n");
    printf("See comments above for the full architecture.\n");
    printf("Implementation in progress.\n");
    return 0;
}
