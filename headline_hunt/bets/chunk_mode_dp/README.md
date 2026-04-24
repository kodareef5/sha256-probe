# bet: chunk_mode_dp — Chunk-mode DP with mode variables

**Priority 6** per GPT-5.5 (medium-low EV).

## The bet

Raw carry-state DP failed because the carry state is near-injective on the search
space (89-99% of 2^{4N}). But the BDD has O(N^4.8) size — so a *compact* state
must exist for the collision quotient. The bet: find that quotient via
**future-completion mode variables**.

## Hypothesis

A DP state that tracks "what would still need to happen for this partial state to
extend to a collision" — boundary modes plus canonical residual context — is
compact even though the raw carry state is not.

The completion quotient = #collisions equivalence (verified N=8, 10, 12) is
direct evidence such a quotient exists; we just don't know its representation.

## Headline if it works

> "First constructive DP for cascade collisions — invalidates carry-state-injectivity
> as a barrier to algorithmic search."

Settles the polynomial-BDD-paradox in a different direction than `kc_xor_d4`.

## What's built / TODO

- [ ] **Design the mode-variable set.** What does "future completion" mean concretely?
- [ ] **N=8 prototype.** Must recover the known 260 N=8 collisions with a state count
  that grows polynomially (or at least sub-exponentially) in N.
- [ ] **N=12 extrapolation.** If N=8 works, push to N=12 (where exhaustive collision
  counts are known).

## Related

- Tests `raw_carry_state_dp_near_injective` reopen criterion ("a quotient state not
  based on raw carries gives >10x reduction at N=8 from scratch").
- Tests `bit_serial_dp_brute_force` reopen criterion ("decomposition that respects
  the rotation frontier").
