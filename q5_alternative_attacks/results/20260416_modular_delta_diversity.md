# Modular Delta Diversity Across the Cascade (N=8)

**Date**: 2026-04-16  
**Status**: VERIFIED at N=8 (260 collisions)

## Finding

The **modular difference** ΔW[r] = (W2[r] - W1[r]) mod 2^N evolves from
fully constant at round 57 to nearly maximal diversity at round 60:

| Round | Unique (ΔW mod 2^N) | Fraction of 256 |
|-------|--------------------:|----------------:|
| 57    | **1** (= 0x2d)      | 0.4%            |
| 58    | 103                 | 40.2%           |
| 59    | 74                  | 28.9%           |
| 60    | 146                 | 57.0%           |

ΔW[57] = 0x2d for EVERY collision — the cascade's pre-round-57 state
is fixed (precomputed from M[0..15]), so da[57] = 0 forces a single
modular difference for W[57] per candidate.

At rounds 58-60, the modular delta depends on the choice of W1[57..r-1],
creating diversity. Round 60 is maximally diverse (ΔW[60] ∈ 146 of 256
values).

## Tuple Signatures

Each of 260 collisions has a near-unique (ΔW[58], ΔW[59], ΔW[60]) tuple:
- 251 distinct tuples
- 9 tuples repeat with multiplicity 2

The cascade structure **compresses** the 4-word collision problem into
a 3-word modular-delta signature, with ΔW[57] fixed by construction.

## Interpretation

The cascade construction reduces the "differential freedom" of sr=60
collisions:
- 1 word (W[57]): forced differential by initial state
- 3 words (W[58..60]): progressively varying differentials

This is the MODULAR view of the cascade. The XOR view (differentials
in GF(2)) shows less structure because XOR and modular arithmetic
are nonlinearly related.

## Implication

The "256 cascade collisions per candidate" phenomenon (hw56-predicted
and verified at N=8 with 260) is equivalent to saying:
**the 3-tuple (ΔW[58], ΔW[59], ΔW[60]) has ~250-260 reachable values**.

If we could characterize WHICH tuples are reachable, we'd have a
compact description of the collision set.

The unique tuples form a subset of 2^{3N} = 16M values at N=8.
260/16M = 0.0015% density. Enumerating this subset is the hard part.

## Relation to Cascade Tree Linearity

Earlier finding: cascade tree has branching factor 1.04 (250 pairs →
260 collisions).

This finding: 251 unique modular-delta tuples.

Both are facets of the same observation: collisions occupy a
near-bijective subset of ~260 ≈ 2^N coordinates.

## Open Question

Why does ΔW[59] have LESS modular diversity (74) than ΔW[58] (103)
or ΔW[60] (146)? One would naively expect monotonic growth as cascade
state accumulates complexity. The reduction at W[59] suggests the
cascade's mid-round structure constraints apply MORE at W[59] than
at the boundaries.

This matches the W1[59] cardinality reduction (42 unique W1[59]
values — also the most constrained word). **W[59] is the cascade's
internal bottleneck in both direct and differential form.**
