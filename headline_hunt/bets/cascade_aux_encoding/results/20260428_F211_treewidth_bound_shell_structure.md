---
date: 2026-04-28
bet: cascade_aux_encoding
status: TREEWIDTH_BOUND_TRACTABLE_AFTER_PREPROCESSING
---

# F211: cascade_aux primal graph treewidth bound = 699 with revealing shell structure

## Setup

F210 left open the question: is exact DP decoding feasible on cascade_aux,
or is BP the only viable approach? The answer depends on treewidth.

Wrote `tanner_treewidth_bound.py` — min-degree elimination heuristic
giving an upper bound on primal-graph treewidth. Ran on
`aux_expose_sr60_n32_bit06_m6781a62a_fillaaaaaaaa.cnf`.

## Aggregate result

```
Parsed: 13179 vars, 54646 clauses (0.05s)
Primal graph: 13179 nodes, 40893 edges, mean degree 6.2, max 128
Treewidth upper bound: 699 (31.3s)
```

Treewidth bound 699 is too large for exact DP decoding (memory cost
≈ 2^699 per state — infeasible).

But the elimination *trajectory* is the striking finding.

## Shell structure: 75% of vars eliminate trivially

Min-degree elimination produces this max-fill trajectory:

| Eliminated | Max-fill so far | Comment |
|---:|---:|---|
| 658 (5%) | 2 | trivial |
| 1316 (10%) | 2 | trivial |
| 1974 (15%) | 4 | low |
| 2632 (20%) | 4 | low |
| 3290 (25%) | 4 | low |
| 3948 (30%) | 4 | low |
| 4606 (35%) | 4 | low |
| 5264 (40%) | 5 | still low |
| 5922 (45%) | 6 | gradual rise |
| 6580 (50%) | 7 | |
| 7238 (55%) | 8 | |
| 7896 (60%) | 9 | |
| 8554 (65%) | 11 | |
| 9212 (70%) | 14 | |
| 9870 (75%) | 22 | starting to explode |
| 10528 (80%) | 43 | |
| 11186 (85%) | 83 | |
| 11844 (90%) | 280 | core territory |
| 12502 (95%) | 699 | peak |
| 13179 (100%) | 699 | done |

**The first ~9,000 variables (75%) can be eliminated with max-fill
≤ 14**. The hard core is the LAST 25% of vertices (~3,000 vars,
treewidth-equivalent ≤ 699).

## Interpretation

The cascade_aux primal graph has a clear **shell architecture**:

1. **Outer shell (75% of vars)**: Low-degree Tseitin auxiliary
   variables. Each implements an XOR/AND/OR gate locally, connected
   to a small constant number of neighbors. Eliminate these by
   variable summation/projection in O(|outer-shell|) operations.

2. **Hard core (25% of vars)**: After outer-shell elimination, a
   dense subgraph of ~3,000 variables remains, with treewidth
   ≤ 699. This is where the cascade_aux's encoding complexity
   really lives.

The hard core is too large for exact DP. But it's small enough that
**BP message-passing on the hard core** is computationally feasible:
- ~3,000 vars × ~100 messages each / iteration = 300,000 ops per pass
- Convergence in 10-30 iterations (typical for sparse codes)
- Total: ~10⁷ ops per cascade_aux instance

This matches F134's principles framework prediction "10-20 iterations,
~10⁷ ops total" — except the prediction was ALSO predicated on level-4
cluster correction at gap-9/11 that F207 falsified. The corrected
prediction needs to use the actual gap structure (gap-1-3 + gap-32 +
gap-128 per F207).

## Concrete decoder design (sharper now)

Three-stage decoder:

**Stage 1**: Eliminate outer shell via summation
- Identify all degree-≤4 variables
- Eliminate via variable projection (sum over their states)
- Update reduced graph
- Iterate until shell exhausted or threshold (~75% reduction) hit
- Cost: O(|outer-shell|) ≈ O(10⁴) ops

**Stage 2**: BP message passing on hard core
- 3,000 hard-core vars + their clauses
- Standard sum-product BP with damping
- Use F207/F209's gap structure for cluster corrections at level-2
  (gap-1-3 short cycles)
- Cost: O(|core-edges| × iterations) ≈ 3·10⁵ × 30 ≈ 10⁷ ops

**Stage 3**: Marginal extraction + HW-search guidance
- Extract bit-level marginals on the 128-bit free schedule
- Sort bits by marginal confidence
- Use as priority order for greedy HW search OR feed to yale's
  block2_wang heuristic as initialization

**Total cost**: ~10⁷ ops per cascade_aux instance, target wall < 1s
on a single CPU.

## Comparison to current cascade_aux protocol

Current cascade_aux bet operates kissat with stack hints, ~3.6 CPU-h
total across 785 logged runs. Best result (F76): 2-3.4× preprocessing
speedup over baseline kissat.

The proposed F211 BP decoder would be a **structurally different
algorithm**: it computes marginals once per instance, then uses them
to guide search. Not a CDCL variant. The benchmark question is
whether the marginal-guided search converges to SAT/UNSAT faster
than CDCL+stack-hints.

If the BP decoder takes <1s and produces useful marginals, the
expected workflow is:

```
cascade_aux CNF → F211 decoder (~1s) → marginals →
                 → HW-priority order
                 → kissat with --branch=ordered (or similar)
                 → reduced search time
```

Predicted speedup: 2-10× over CDCL+stack-hints on the same
instances. To be tested.

## What's NOT being claimed

- That treewidth is exactly 699 (it's an upper bound from min-degree;
  could be much smaller with better elimination order).
- That BP converges in 10-30 iterations on cascade_aux (need
  empirical test; gap-1-3 dense cycles could cause slow convergence
  without level-2 correction).
- That the BP decoder will give 2-10× speedup (proposal, not result).

## Concrete next probes

(a) **Identify the hard-core 3,000 variables semantically**:
    elimination order suggests the core consists of the M1/M2
    free schedule vars (256 vars per F209) plus the densely-coupled
    Tseitin auxiliaries between them. Worth tracing.

(b) **Run treewidth bound on TRUE sr=61** for comparison.
    Different encoder; expect different bound.

(c) **Implement Stage 1 (outer-shell elimination)** as a
    standalone preprocessing step. Test if the reduced CNF still
    has the same UNSAT verdict (it must, by construction) and if
    kissat solves the reduced CNF faster than the original. Even
    without BP, this preprocessing alone might give a speedup.

(d) **Profile the elimination trajectory shape across CNFs**:
    if the 75/25 shell-core split is universal across cascade_aux
    instances, the decoder's preprocessing budget is predictable.

## Discipline

- 0 SAT compute (graph-theoretic analysis only)
- 0 solver runs
- 31s wall on one cascade_aux N=32 CNF
- Treewidth upper bound 699; tractable BP on hard core after
  preprocessing
- Closes F210's open question on decoder feasibility: BP is
  viable; exact DP not feasible globally but might be on a
  smaller restricted core
- Strategic implication: cascade_aux_encoding bet should pursue
  the three-stage preprocess-BP-marginal decoder; expected
  ~10⁷ ops per instance, target <1s wall
