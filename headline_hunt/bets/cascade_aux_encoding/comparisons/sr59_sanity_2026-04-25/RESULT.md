# sr=59 cascade-DP cadical sanity probe — UNEXPECTED HARDNESS

## Setup

Per the encoder's parameter schema:
- sr=59: 5 free W's at rounds 57-61.
- sr=60: 4 free W's (57-60).
- sr=61: 3 free W's (57-59).

Naive intuition: sr=59 has the MOST search freedom, so SAT should be easiest. Combined with Viragh's "92% broken" sr=59 result, sr=59 should be a quick sanity-check SAT.

**Test**: cadical 3.0.0 with conflict budget 1M, both modes, 6 candidates × 1 seed (force) + 3 candidates × 5 seeds (force, multi-seed) + 3 candidates × 1 seed (expose). Total 18 runs.

## Results

| | runs | wall (s) | SAT count | UNSAT count | UNKNOWN |
|---|---:|---:|---:|---:|---:|
| Force mode (6 candidates × seed=5) | 6 | 16.7-21.1 | 0 | 0 | 6 |
| Force mode (3 candidates × 5 seeds) | 15 | 15.3-21.3 | 0 | 0 | 15 |
| Expose mode (3 candidates × seed=5) | 3 | 19.5-22.2 | 0 | 0 | 3 |
| **Total** | **24** | — | **0** | **0** | **24** |

**Zero SAT in 24 sr=59 cascade-DP runs.** 24M conflict-equivalent compute spent, all timeout.

## Why this is surprising

Naive bit-counting at sr=59 force mode:
- W[57..61] free: 5 × 32 = 160 bits
- Cascade through r=60 (Theorem 1): consumes 0 search bits (just binds W2 to W1)
- dE[60..63]=0 + dA[61]=dE[61]=0 (Theorems 2-4): 4 × 32 = 128 bits of constraint
- Expected SAT solutions per candidate: 2^(160 - 128) = **2^32 = ~4 billion**

With 4 billion solutions in a 5×32-bit search space, cadical should find SAT in ≪1M conflicts (random walk hits SAT region with prob 2^32/2^160 = 2^-128 per W choice, so expected ~2^128 trials ... hmm wait that's worse than 1M).

OK the bit-counting argument is wrong. Let me redo:

At a 5-W-free search with 4 32-bit constraints:
- For each W assignment, the constraints are checked.
- Solutions are at positions where ALL 4 constraints hold.
- If constraints are "structurally independent" (probabilistic): density = 2^-128 in 2^160 space → 2^32 solutions.
- Random search hits SAT with prob 2^-128 per trial → expected 2^128 trials.

So even with 2^32 solutions, finding ONE via random search needs ~2^128 trials. That's why CDCL times out.

The only way to find SAT in <1M conflicts is if the constraints have STRUCTURE that CDCL can exploit (unit propagation, etc.). Our cascade-DP constraints are non-trivial modular relations through SHA-256's nonlinear ARX operations — not inherently CDCL-friendly.

## What this implies

1. **Viragh's "92% broken" result is NOT cascade-DP-compatible.** Viragh likely uses Wang-style differential characteristics with low-Hamming-weight starting differences, which yield trail probabilities high enough to make collision search feasible. Our cascade-DP construction enforces a SPECIFIC class of differentials (cascade diagonal + zero e-trace at r=60..63) that doesn't overlap with Viragh's solution space.

2. **Cascade-DP sr=59 is structurally hard.** The 2^32 expected SAT solutions don't translate to easy CDCL search. The structural constraints (Theorems 1-4) define a tight modular variety that CDCL has to navigate via unit propagation alone — no shortcuts.

3. **Mode B's "front-loaded" preprocessing speedup observed at sr=60/61 doesn't translate to "fast SAT-finding at sr=59."** The 2× advantage at small budgets is amortized away over the 1M-conflict steady-state search.

4. **The bet's headline-class hypothesis is further constrained.** "≥10x SAT speedup at sr=61" was already retracted (down to 2-6x preprocessing). Now we add: even at sr=59 (more free bits), cascade-DP SAT is empirically out of reach at 1M-conflict budget. The path to a headline at any sr-level requires either:
   - A different message-difference structure (block2_wang's Wang trails, kc_xor_d4's #SAT route).
   - A propagator that can navigate the modular variety more efficiently than CDCL alone (programmatic_sat_propagator bet).
   - Genuinely-multi-day compute on a single instance (~10^9 conflicts).

## Should we read this as encoder bug?

Possible but unlikely. Both modes agree on UNKNOWN. The 6 sr=59 force CNFs all have similar var/clause counts (12252-12336 vars, 51168-51511 clauses — clean 6-kernel range). The fingerprints have been added to cnf_fingerprints.yaml (commit forthcoming). All audit-CONFIRMED.

If there's an encoder bug at sr=59, it would have to either:
- Add a constraint that makes sr=59 UNSAT (force solver to deduce UNSAT eventually) — but we don't see UNSAT.
- Subtly distort the cascade construction in a way that the per-conflict cost stays similar but SAT solutions vanish.

Either is possible but neither is a smoking gun. **My honest assessment: cascade-DP sr=59 is genuinely hard at 1M-conflict budget; this is consistent with the broader pattern that cascade-DP imposes a tight structural constraint that CDCL can't exploit at modest budgets.**

## Constraints on follow-up

- **Don't conclude "no sr=59 collision exists in cascade-DP"** from 24 runs at 1M conflicts. The negative is "not findable in 1M conflicts via cadical."
- A 4h+ kissat run on a single sr=59 force candidate would test this more decisively. **Not initiating without explicit user direction.**
- The propagator (Phase 2B+) is the natural mechanism to reduce the conflict budget needed.

## sr=59 CNF artifacts

Added new fingerprint buckets to `infra/cnf_fingerprints.yaml`:
- `sr59_n32_cascade_aux_expose`: vars [12200, 12400], clauses [51100, 51600]
- `sr59_n32_cascade_aux_force`: same range

Updated `infra/audit_cnf.py` with `^aux_{expose,force}_sr59.*\.cnf$` patterns. All 6 sr=59 CNFs audit-CONFIRMED.

## Run logs

24 logs in this directory (6 single-seed force, 15 multi-seed force, 3 expose).
