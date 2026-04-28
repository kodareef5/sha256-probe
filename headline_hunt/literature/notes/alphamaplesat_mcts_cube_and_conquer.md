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

---

## 2026-04-28 update: connection to yale's block2_wang absorber search results

After today's macbook ↔ yale 4-iteration falsification chain (F128-F133, F156), the AlphaMapleSAT framework is more directly relevant than the original note suggested.

### Yale's empirical findings (today)

Yale's F123/F125/F126/F127 established that the bit3 block-2 absorber hits **strict radius-2 local minima** under all natural local moves:
- M2-only bit flips (12,880 candidates, 0 improving)
- Both-side flips (also 0 improving)
- Common-mode flips (preserve message XOR, 0 improving)
- Fixed-diff resampling (preserve message XOR diff, 40k samples, 0 improving)
- Additive common-mode (radius-2, 0 improving)

Yale's stated next direction (F131): "structured moves that preserve late-schedule features, OR a solver that reasons directly over schedule words W16-W30 instead of raw message-bit flips."

### Direct alignment with AlphaMapleSAT

AlphaMapleSAT's MCTS-driven cubing IS a structured-move generator:
- **MCTS rollouts** explore beyond yale's local-search radius (which is the literal proposal yale needs to escape radius-2 minima)
- **Deductive feedback** from CaDiCaL guides which subtrees to expand — this is the "reason over schedule words" component yale described
- **Cube-and-conquer paradigm** lets MCTS pick the cubes and CaDiCaL solve them, splitting concerns

For yale's bit3 fixture: the W[57..60] free-word space is 128 bits (4 × 32). MCTS could cube on (e.g.) W[60] bit positions (32 bits → 32 cubes), with CaDiCaL conquering each cube via cascade-aware propagation. This is structurally aligned with cascade_aux_encoding's auxiliary variables.

### Gap between AlphaMapleSAT and cascade-1 use

AlphaMapleSAT was tested on quantum/combinatorial benchmarks (Kochen-Specker, Ramsey) — NOT cryptographic. The MCTS rollout reward signal there is "sub-instance solving time" or "branching depth saved." For cascade-1, the analogous signal would be:
- Rollout reward = lowest target distance reached after partial SAT solving
- Cube selection = structural cube design (fix a few W-bits, let CaDiCaL handle the rest)

This adaptation is non-trivial. Yale's F125 stated need ("solver reasoning over W16-W30") is closer to a custom IPASIR-UP propagator (per `programmatic_sat_propagator` BET) than to AlphaMapleSAT's MCTS approach. But the deductive-feedback PATTERN is the same.

### Connection to principles framework algorithmic candidates

The principles framework (april28_explore/principles/) identified 8 poly-time algorithm candidates. AlphaMapleSAT's MCTS-cubing is closest to:
- **Treewidth DP** (synthesis 5): tree-decomposition-based exact solving, where MCTS could pick favorable elimination orderings
- **BP-Bethe with level-4** (synthesis 8): MCTS rollouts could replace deterministic message passing on loopy regions

Neither is identical, but the architectural bridge is:
1. AlphaMapleSAT establishes that MCTS+deductive-feedback IS empirically faster than pure SAT
2. The principles framework identifies cascade-1's structural features (Σ-Steiner topology, Iwasawa pipelines)
3. A cascade-aware MCTS+CaDiCaL implementation would combine both

### Concrete cross-bet implication for next iteration

If yale's heuristic absorber search has plateaued (per F156), the natural next step is a STRUCTURED solver — and AlphaMapleSAT's MCTS-cubing approach is the closest published architecture.

For block2_wang specifically:
- Cube on W[60] bit-positions (32 cubes)
- Conquer each cube with cascade_aux force-mode CaDiCaL (Mode B, ~3-4× speedup per programmatic_sat_propagator findings)
- MCTS rollout depth = 1-2 conflict checks per cube
- Reward = chain-output target distance

Expected speedup over yale's pure local search: 2-7× (per AlphaMapleSAT paper's range), modulo the quantum-vs-crypto domain gap.

### Read status

Still flagged TL;DR-only. Deep read deferred until either:
- programmatic_sat_propagator reopens (per F147 reopen-candidate context)
- Yale's heuristic plateau warrants a structured-solver pivot (current state per F133/F156)

Either trigger justifies reading the full paper. The architectural alignment is strong enough that the reading is high-leverage.
