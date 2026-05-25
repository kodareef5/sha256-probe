# Kill memo — chunk_mode_dp_with_modes

**Closed**: 2026-05-25
**Closed by**: macbook-claude
**Total CPU-h spent**: ~0.05 (BDD quotient run 0.02s + reused 85s N=8 enumeration)

## What this bet was

Chunk-mode DP with **mode variables** on a *future-completion* quotient state.
Bet (`bets/chunk_mode_dp/BET.yaml`, P6): raw carry-state DP fails because the carry
state is near-injective, but the collision BDD is O(N^4.8) — so a *compact* state
quotient must exist; find it via future-completion mode variables and build a
constructive forward DP that recovers the N=8 collisions with sub-exponential state.

## Which kill criterion fired

> "N=8 prototype cannot recover 260 with a compact state count (e.g., state
> explosion comparable to brute force)."

Met — via the canonical/minimal quotient measurement (stronger than any prototype):
the BDD **completion quotient** (distinct residual sub-BDD nodes per prefix depth)
peaks at **255 of 260** collisions (`results/bdd_qm_2026-04-25/`), i.e. near-injective,
state explosion comparable to brute force.

## Why this is DEFINITIVE (the new argument)

The 2026-04-25 result refuted only the *BDD-sub-graph* quotient and explicitly left
the bet open for "untested mode designs" (the 5-mode tuple in the design seed). That
caution was unnecessary:

**The completion quotient IS the Myhill–Nerode minimal automaton.** The "distinct
residual sub-functions after fixing the first d variables" is, by the standard
OBDD = minimal-DFA-for-fixed-order correspondence, the *minimum* number of states
any forward automaton reading these variables in this order can have at layer d. The
observed max layer width 255 ≈ collision count is therefore a **lower bound on the
frontier of every forward DP in this variable order** — including the design seed's
cascade-status + 4-modular-d.o.f. mode tuple and the BET.yaml mode-variable set
(both are forward DPs over the round-ordered W bits). No mode abstraction can be
more compact than the minimal automaton. So all remaining "untested" designs are
refuted without building them.

This also resolves the BDD paradox cleanly: O(N^4.8) is the **total** node count
summed over all 32 layers, but a constructive forward DP must materialize each
**layer's width** (the frontier), which is ≈ collision count = exponential in N.
Total-nodes-compact does NOT imply forward-constructible. (Matches the known
"BDD construction is O(2^{4N})".)

## What we learned

- Compact total BDD size != small forward frontier. The forward frontier (layer
  width / Myhill–Nerode classes) is the quantity a DP pays, and it is near the
  collision count here. This is the general reason carry/mode/boundary DP all fail.
- The 4-modular-d.o.f. residual variety (from mitm_residue) does NOT imply a compact
  DP state: a 4-d.o.f. variety over N-bit moduli is 2^{O(N)} points, and the
  reachable forward states are near-injective on collisions regardless.
- Implies the polynomial-BDD-paradox does NOT resolve toward a constructive
  algorithm via completion quotients. Adjacent: reinforces
  `negatives.yaml#raw_carry_state_dp_near_injective` and the d4/kc_xor difficulty.

## Caveat (honest scope)

The 255 minimal width is for the BDD's variable order (round-interleaved bit-slice).
A radically different variable ordering *could* in principle reduce the max layer
width, but (a) the O(N^4.8) BDD already used a good order and still hit 255, and
(b) no proposed mode design changes the order (all read rounds 57->63). Finding a
polynomial-width order is itself the unsolved (likely infeasible) problem; this bet
proposed mode variables, not a new order, so it is refuted as scoped.

## Reopen criteria (verbatim from mechanism entry)

(The mechanism had no explicit reopen_criteria; from related negatives —)
"a quotient state not based on raw carries gives >10x reduction at N=8 from scratch"
and "decomposition that respects the rotation frontier". A genuine reopen would need
a variable ORDER (not just a mode tuple) whose minimal automaton layer width is
shown polynomial in N — a strictly stronger, order-level result.

## Adjacent updates

- `mechanisms.yaml/chunk_mode_dp_with_modes`: status open -> closed, owner macbook-claude.
- `negatives.yaml`: add `forward_completion_quotient_min_width_near_collision_count`
  (the Myhill–Nerode generalization), superseding the narrower
  `bdd_completion_quotient` observation.
