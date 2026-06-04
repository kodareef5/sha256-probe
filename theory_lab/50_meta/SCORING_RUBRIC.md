# Scoring rubric — plausibility and probe_cost

Two ordinal axes drive triage. Keep them honest; the whole point of the lab is that high-plausibility
+ cheap-to-probe ideas jump the queue, and everything else waits or dies.

## plausibility (1–5) — chance the angle says something real
Anchored, not vibes. "Says something" includes a clean negative (a rigorous *why-the-wall* result counts).

| score | meaning | anchor example |
|---|---|---|
| 1 | numerology / almost certainly dead-for-construction | additive combinatorics constructing one collision; Grover as classical progress |
| 2 | weak analogy, big gaps | survey propagation on a dense structured CNF (may not even converge); Walsh as a *constructive* tool |
| 3 | plausible bridge, real unknowns | 2-adic span of ΔW; expansion-code min distance; carry-lifted lattice on a 1-round residue |
| 4 | strong structural reason to expect signal | (none seeded yet — would need a probe to have already shown partial signal) |
| 5 | near-certain to say something (often = already established) | the repo's own framings (carry automaton, BDD O(N^4.8)) — logged as baseline |

Note the asymmetry: most *fresh* angles cap at 3 pre-probe (an honest bridge with real unknowns). A 4–5
fresh angle should make you suspicious you've under-stated the unknowns. Established repo framings sit at
5 by definition (they're true); that is why they're baseline, not live.

## probe_cost — cost to FALSIFY, not to exploit
The smallest decisive experiment, not the full build-out.

| bucket | meaning | example |
|---|---|---|
| `trivial` | think-only / back-of-envelope, < 1 h | "does this tool construct or only count?" (kills most parked rows) |
| `cheap` | a Python probe on small N, hours, reusing `lib/` | `v2(ΔH)` trend across N∈{8,10,12,16}; low-weight-codeword search on the linearized matrix |
| `moderate` | a real implementation / library spike, ~days | a full PolyBoRi/F4 run; an FCSR-synthesis library integration |
| `heavy` | needs the solver fleet or a new engine | **out of charter to RUN here** — design it and hand it to the repo as a bet |

The triage signal is the **pair**: `plausibility × (1/probe_cost)`. The three spine angles are all
(3, cheap) — that pairing is exactly why they top the shortlist over higher-novelty-but-pricier ideas.
