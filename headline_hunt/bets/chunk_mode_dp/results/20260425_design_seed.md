# chunk_mode_dp design seed — proposed mode-variable set

**Status**: design proposal, no compute. Future workers can either build N=8 prototype or refine the design first.

## The bet's core problem

Raw carry-state DP fails (negatives.yaml#raw_carry_state_dp_near_injective). Each carry state corresponds to ~1 collision; the DP is essentially brute force.

**Hypothesis** (from BET.yaml): a *quotient state* that encodes "what would still need to happen for this partial state to extend to a collision" might be exponentially smaller than raw carries. Mode variables are the additional features that capture this.

## What we now know that we didn't on 2026-04-24 (when the bet was opened)

The mitm_residue structural picture has characterized the cascade-DP residual at r=63 as a **4-modular-d.o.f. variety** (after R63.1 dc=dg and R63.3 da−de=dT2_63). That's strong structural information.

For a chunk-mode DP at the cascade-DP boundary, the natural quotient state at intermediate rounds (r=57, 58, 59, 60) might be:
- Cascade-zero status (binary: has cascade held to round r?)
- Modular signatures of 1-4 register diffs that would propagate to determine the eventual residual variety position.

## Proposed mode-variable set (sketch)

For a DP that walks W's from r=57 to r=63 and tracks "cascade-DP collision feasibility," the state at the END of round r should compactly encode:

```
state[r] = (
    cascade_alive: bool,           # has Theorem 1 held through round r?
    de_60_locked: bool,            # is de[60]=0 known/forced?
    a_register_modular_diff[r],    # modular value of da[r] (or 'free')
    e_register_modular_diff[r],    # modular value of de[r] (or 'free')
    dT2_seed_at_r: int32 or None,  # the dT2_r component from earlier rounds, if computable
)
```

Equivalence: two partial states are equivalent if they have the SAME set of cascade-DP collision extensions. Specifically:
- For r ≤ 60: cascade_alive must be True; remaining state is determined by underlying register values plus dW differences.
- For r > 60: collision feasibility is a function of (da[r], de[r], dT2_r, ...) — exactly the variety dimension our structural picture characterizes.

## How "modes" enter

A "mode" is a discrete tag that classifies the partial state's cascade-DP type. Proposed modes:

- **Mode 0 — pre-cascade**: r < 57, cascade hasn't started yet.
- **Mode 1 — cascade-running**: 57 ≤ r ≤ 60, cascade-1 + cascade-2 enforced.
- **Mode 2 — residual-active-r=61**: r = 61, three-filter dE[61]=0 must hold; da[61]=de[61] modular (Thm 4).
- **Mode 3 — residual-active-r=62**: r = 62, da[62] − de[62] = dT2_62 must hold.
- **Mode 4 — residual-active-r=63**: r = 63, da[63] − de[63] = dT2_63 AND dc[63] = dg[63].

Within each mode, the state is the SHORTEST tuple of moduli whose values determine all extension outcomes. For Mode 4 (the residual variety), our structural picture says this tuple has 4 dimensions × 32 bits = 128 bits.

## Why this might be polynomial

Crucially, the variety has **4 d.o.f. independent of N (the message-bit width)**. As N grows:
- The number of rounds (currently 64) doesn't change.
- The modular d.o.f. is 4 × N bits.
- The W-input search space is (n_free) × N bits.

For sr=61 cascade-DP at full N=32: 96 input bits, 128 d.o.f. → 2^-32 SAT prob.
For sr=61 cascade-DP at scaled N: input would scale linearly, d.o.f. would also scale linearly. 2^(O(N)) overall, NOT 2^(O(N×rounds)).

This is the polynomial structure the bet is hunting. The mode framework EXPOSES it by making the d.o.f. count explicit.

## What the prototype should do

N=8 prototype steps:
1. Implement 5 modes (above) for SHA-256 reduced to N=8 word-bit width.
2. For each mode, define the state tuple (which moduli matter).
3. Build a DP that walks rounds 57-63, transitioning between modes, accumulating mode-state.
4. Count the number of states reached at round 63 in mode 4 — should be ≤ 2^16 (4 mod-N values, 8 bits each = 32 bits, with constraints reducing).
5. Compare against known N=8 collision count (260) — DP should reach ≥260 distinct mode-4 states corresponding to collisions.
6. **Decision gate**: if state count grows < 2^N polynomial when scaling N=4 → N=8 → N=12, the bet works. If exponential, kill.

## Time estimate

- Design refinement: 0.5-1 day (validate the 5 modes against known structural picture)
- N=8 prototype: 2-4 days (Python implementation; ~500-1000 LOC)
- N=12 extrapolation: 1-2 days
- Decision: 1 day

Total: ~1-2 weeks of focused human time.

## Dependencies

- Existing structural picture (mitm_residue results, all locked).
- mini-SHA library at N=8 — currently UNAVAILABLE in lib/. Would need to add `lib/mini_sha.py` (referenced in CLAUDE.md but not present). This is a real blocker for prototype work.
- Knowledge of carry-DP failure modes from earlier work (q5_alternative_attacks/).

## Status of this design seed

This is a SKETCH, not a verified design. To promote to "validated design":
1. Confirm the 5-mode classification covers all reachable partial states.
2. Confirm the mode-4 d.o.f. count matches our 4-d.o.f. structural picture (it does, by construction).
3. Confirm modes 1-3 don't have hidden state that should be modes too.

Future worker who picks up the bet: refine this sketch, then build N=8.
