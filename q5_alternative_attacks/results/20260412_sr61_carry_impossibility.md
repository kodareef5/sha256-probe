# sr=61 Carry Impossibility: Structurally Disjoint from sr=60

## Result

At N=4: the sr=61 schedule constraint (W[60] = sigma1(W[58]) + const)
is INCOMPATIBLE with ALL 79 carry-diff invariants of sr=60 collisions.

| Test | Result |
|------|--------|
| sr=60 collisions satisfying sr=61 constraint | **0/49** |
| sr=61 random combos satisfying all sr=60 invariants | **0/10,000** |
| Minimum invariant violations per sr=61 combo | **5** (of 79) |
| Mean violations | 19.6 |

## Interpretation

The sr=60 collision set occupies a carry-diff subspace defined by
79 invariant constraints. The sr=61 schedule constraint forces the
collision search into a DIFFERENT region of carry-diff space that
violates at least 5 of these invariants.

**No sr=61 collision can exist that satisfies the sr=60 carry invariants.**
Either:
(a) sr=61 collisions satisfy DIFFERENT invariants (new cascade mechanism)
(b) sr=61 collisions don't exist (the invariants are universal)

Since the invariants come from the T2-path/cascade structure which is
shared between sr=60 and sr=61, option (b) is more likely. The sigma1
schedule constraint breaks the cascade carry alignment.

## Connection to earlier findings

- Server's sigma1 conflict rate (10.8%): measures the SAME incompatibility
  from the linear-algebraic side
- Macbook's critical pair: the rotation positions where the conflict
  concentrates
- Our carry-diff invariants: the SPECIFIC carry bits that are violated

All three perspectives agree: sr=61 breaks the cascade carry structure.

## Evidence level: VERIFIED at N=4 (exhaustive, all 49 collisions)
Needs verification at N=8 (260 collisions) for cross-width confirmation.
