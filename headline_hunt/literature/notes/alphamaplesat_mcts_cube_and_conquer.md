# alphamaplesat_2024 — AlphaMapleSAT: MCTS-based cube-and-conquer

**Authors**: Piyush Jha, Zhengyu Li, Zhengyang Lu, Raymond Zeng, Curtis Bright, Vijay Ganesh
**Venue**: arXiv:2401.13770 (2024)
**Read status**: TL;DR captured, not yet deep-read.

## TL;DR (3 lines)

MCTS replaces shallow lookahead in cube-and-conquer cubing. Deductive feedback from SAT solvers guides MCTS rollouts. 1.61x–7.57x wall-clock improvement on 128-core systems vs March on benchmark instances.

## Most relevant findings to this project

- **Technique**: MCTS-driven cube selection, with rollouts evaluated by partial SAT solving. Key insight is replacing depth-limited heuristic lookahead with stochastic-search-with-feedback.
- **Solver substrate**: CaDiCaL (matches our local install at version 3.0.0). SAT Modulo Symmetries and SAT+CAS variants tested as the "conquer" stage.
- **Parallelism**: scales 32 → 64 → 128 cores; consistent speedup. Relevant for fleet machines with multi-core capacity.
- **What it isn't**: No evaluation on SHA-1/SHA-2/AES instances. Benchmarks are quantum (Kochen-Specker), graph theory (Murty-Simon, Ramsey). So results don't directly translate to cascade-collision SAT.

## Action items for our bets

1. **`programmatic_sat_propagator`**: AlphaMapleSAT's "deductive feedback" architecture is the closest published analog to what the bet wants (a SAT solver that exploits problem structure for guidance). The MCTS+deductive-feedback pattern could be adapted: replace MCTS rollouts with cascade-aware propagation. Worth deep-reading before designing the propagator.

2. **`true_sr61_n32`**: cube-and-conquer with AlphaMapleSAT-style cubing on aux-force CNFs is a plausible attack avenue. The 96-bit free-word space (W[57..59]) is naturally cube-able. If a fleet machine has a 32+ core box and wants to try, this is the cleanest application.

3. **`cascade_aux_encoding`**: aux variables are exactly the kind of structural hints AlphaMapleSAT's cubing could exploit. Aux + cube-and-conquer is a synergy worth testing.

## Reservations / caveats

- Speedup numbers (1.61-7.57x) are on hard combinatorics, not crypto. Cascade-collision instances may have different cubing structure that performs differently.
- 128-core systems are larger than the macbook (10-core) — gain on smaller fleets is unknown.
- AlphaMapleSAT is published as a tool but build complexity not characterized here. Need to evaluate before committing CPU.

## Update plan

When the `programmatic_sat_propagator` bet starts moving, deep-read this paper first. Until then, this TL;DR plus the architectural similarity is enough.

`literature.yaml` `read_status` for `alphamaplesat_mcts_cube_and_conquer` updated to `read`.
