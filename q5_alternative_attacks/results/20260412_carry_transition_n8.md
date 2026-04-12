# Carry Automaton Transition Structure at N=8

## Finding: The automaton is a PERMUTATION (zero branching)

At every bit position (0-6), there are exactly 260 states with
exactly 1.0 successors per state. The carry automaton has NO branching
and NO merging — it's 260 independent parallel paths.

## Carry vector distances

| Metric | Value |
|--------|-------|
| Min Hamming distance | 100/686 (14.6% differ) |
| Mean distance | 260.4/686 (38.0%) |
| Max distance | 363/686 (52.9%) |
| Pairs within d=50 | 0 |
| Pairs within d=100 | 1 |

The 260 collisions are **isolated points** in 686-dimensional carry space.
No clustering, no local structure. Each collision's carry fingerprint is
at least 100 bits away from every other collision's.

## Implications

1. **MITM speedup via state merging: NOT possible.** States don't merge.
2. **Bitserial DP won't compress:** 260 states at every level = no savings.
3. **The collision set is unstructured in carry space.** Finding collisions
   requires enumerating carry paths, not exploiting local neighborhoods.
4. **Carry vectors ARE the collisions** (bijection confirmed at N=4 and N=8).
   Any algorithm that enumerates valid carry trajectories IS a collision finder.

## The key question for N=32

Does the width grow to 260 × (growth factor)^{24} or stay bounded?
If bounded: polynomial algorithm exists.
If exponential: matches the current O(2^{4N}) cascade DP scaling.

EVIDENCE level: VERIFIED (direct computation on all 260 N=8 collisions).
