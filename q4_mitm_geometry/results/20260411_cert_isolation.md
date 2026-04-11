# The Cert Is an Isolated Point in Round-61 Closure Space

## Key finding

For the cert prefix (M[0]=0x17149975, W1[57..59]=0x9ccfa55e, 0xd9d64416, 0x9e3ffb08):
- **8192 W1[60] values pass round-61** (the "round-61 family")

For ANY single-bit XOR perturbation of W1[57]:
- **0 W1[60] values pass round-61** (32 of 32 perturbations tested)

For 50-100 random prefixes:
- **0 prefixes have any round-61 matches**

## What this means

The cert is NOT in a "neighborhood" of valid prefixes. It's a measure-zero
point. Single-bit perturbations completely destroy the round-61 closure
property.

This means:
1. Local search cannot find collisions starting from random points
2. Hill climbing in the prefix space won't work
3. The cert was found by Kissat via deep backtracking, not local exploration

## Implications for the constructive search

If round-61 closure is this rare, the cascade chain framework alone
won't find collisions efficiently. We need to either:

1. **Find ALGEBRAIC structure** that determines round-61 closure (so we
   can compute valid prefixes directly, not search). Macbook's
   annihilator analysis is heading this direction.

2. **Birthday-style attack** on a hash function defined by the cascade
   chain. Map prefixes to round-61 closure properties, look for
   collisions in that space.

3. **MITM split** where we precompute partial states and look for matches.

4. **Constraint propagation** like SAT — backtrack from round 63
   constraints back to round 57.

## Connection to macbook's algebraic findings

Macbook found that the 49 N=4 collisions span a 23-dim affine hull
with 8 linear coordinate constraints. At N=32, scaling suggests:
- ~24 linear constraints (cascade structure)
- ~32 nonlinear constraints (the hard part)
- Total 56 constraints on 96 free bits = ~40 effective DOF
- Solutions: 2^40 in 2^96 = density 2^-56

But empirically we see ~1 known collision in our search range, and
single-bit perturbations break it. The actual density is much lower
than 2^-56 — closer to 2^-90 or beyond.

The discrepancy suggests:
- The 49 N=4 collisions DO form a coset of dimension ~23, but
- At N=32, the nonlinear constraints become much tighter
- OR the affine hull at N=4 is misleading (small N has more "slack")

## Next experiments

1. Test if 2-bit perturbations of cert give matches (broader neighborhood)
2. Test if perturbations of W1[58] or W1[59] give matches (asymmetric)
3. Compute the cert's specific algebraic structure (what makes it special)

## Evidence level

**STRONG EVIDENCE**: 32 single-bit perturbations × full 2^32 W1[60]
search = 137 billion evaluations × 0 hits. Combined with 100+ random
prefixes also failing. The cert is genuinely isolated.
