# da61/da62/da63 Are ALL Constant Among Collisions

Date: 2026-04-13 11:45 UTC

## Finding

Among collision solutions at N=4 and N=8, the a-register diffs at
rounds 61, 62, and 63 are each SINGLE-VALUED (constant):

| N | Collisions | |da61| | |da62| | |da63| |
|---|-----------|--------|--------|--------|
| 4 | 49 | **1** | **1** | **1** |
| 8 | 260 | **1** | **1** | **1** |

## Significance

The diagonal analysis showed da61 has ~224 distinct values across ALL
(w57-w60) combinations. But among the 260 COLLISION solutions, da61
takes only ONE value. The collision constraint is so strong that it
forces a UNIQUE state-diff trajectory through rounds 61-63.

## Implication

The collision "hard residue" (rounds 61-63) is NOT a search over many
possible state-diff trajectories. It's a binary test: does a given
(w57,w58,w59,w60) produce the ONE specific da61 value that leads to
collision?

Combined with de60=0 (always) and the cascade diagonal, this means:
- ALL 8 register diffs at rounds 57-63 are either zero, constant, or
  take a single collision-specific value
- The collision is a SINGLE POINT in state-diff space, not a manifold
- The search reduces to: find message words that hit this point

## Connection to Carry Automaton

The carry automaton width = collision count (260 at N=8). Each of these
260 collisions follows the SAME state-diff trajectory but achieves it
via different carry paths. The "width" is entirely in carry space,
not in state-diff space.

This is the strongest evidence yet that the carry automaton framework
is the correct representation: the state-diff problem is trivial
(one target point), while the carry-reachability problem (can the
target be reached via valid carry chains?) is the true hard problem.
