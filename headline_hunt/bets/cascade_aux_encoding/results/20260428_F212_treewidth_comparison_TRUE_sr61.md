---
date: 2026-04-28
bet: cascade_aux_encoding
status: TRUE_SR61_HAS_SMALLER_TREEWIDTH — shell architecture is universal, hard core varies
---

# F212: TRUE sr=61 has smaller treewidth (480) than cascade_aux (699) — shell architecture universal, hard-core size encoder-dependent

## Setup

F211 measured cascade_aux N=32 treewidth upper bound at 699 with
shell architecture (75% of vars trivially eliminable). F210 had
shown TRUE sr=61's Tanner graph differs structurally from
cascade_aux. Open question: does TRUE sr=61 have a similar shell
structure, or is the entire graph dense?

Ran tanner_treewidth_bound.py on
`cnfs_n32/sr61_cascade_m17149975_fffffffff_bit31.cnf`.

## Comparative result

| Metric | cascade_aux N=32 (F211) | TRUE sr=61 (F212) |
|---|---:|---:|
| Vars | 13,179 | 11,256 |
| Edges | 40,893 | 36,908 |
| Mean degree | 6.2 | 6.6 |
| Max degree | 128 | 128 |
| 4-cycles (F207/F210) | 270K | 201K |
| Max single multiplicity | 36 | 10 |
| **Treewidth upper bound** | **699** | **480** |
| Wall-time elimination | 31s | 17s |

**TRUE sr=61 has 31% smaller treewidth than cascade_aux** despite
similar primal-graph density. The hard core in TRUE sr=61 is more
compact.

## Shell architecture is universal

Both encoders show the same shell pattern:

| Eliminated | cascade_aux max-fill | TRUE sr=61 max-fill |
|---:|---:|---:|
| 5% | 2 | 4 |
| 10% | 2 | 4 |
| 15% | 4 | 4 |
| 25% | 4 | 4 |
| 35% | 4 | 5 |
| 50% | 7 | 7 |
| 65% | 11 | 11 |
| 75% | 22 | 20 |
| 85% | 83 | 66 |
| 95% | 699 | 448 |
| 100% | 699 | 480 |

Shape is essentially identical: shallow-rise plateau through 65-75%
of vertices, then explosive rise in the last 25%. **Shell-then-core
structure is the canonical SHA-256 cnf-encoding shape**, not specific
to cascade_aux.

## Why cascade_aux has a larger hard core

cascade_aux is "expose" mode: aux vars + tying clauses, no extra hard
constraints (vs "force" mode which adds Theorem 1-4 constraints).
The expose-mode aux vars are designed to make implications explicit,
giving the SAT solver more decision freedom.

But "more aux vars" + "tying clauses" produces additional dense
couplings between message-schedule variables through the aux vars,
INCREASING hard-core treewidth from 480 (TRUE sr=61, no aux) to 699
(cascade_aux, with aux).

This is a real structural cost of the aux encoding. The aux vars
don't eliminate cleanly because the tying clauses create new dense
couplings. The "solver hint" benefit must outweigh this structural
cost for cascade_aux to win — and indeed yale's pre-pause campaign
showed 2-3.4× preprocessing speedup, so the trade-off is net positive.

## Strategic implications

### For F211's three-stage decoder design

The decoder design from F211 still applies: outer-shell elimination
+ BP on hard core + marginal-guided search. But the hard-core sizes
differ:

- cascade_aux: 3,000-var hard core, BP cost ~10⁷ ops
- TRUE sr=61: 2,400-var hard core (estimate from 11K × 22%), BP
  cost ~6·10⁶ ops

TRUE sr=61 may be 1.5-2× faster to decode than cascade_aux at the
BP stage. **TRUE sr=61 might be the better target for the decoder
benchmark**.

### Cross-bet thinking

The cascade_aux_encoding bet is scoped to cascade_aux. But if a
generic shell-elimination + BP decoder works on either encoder,
the algorithmic finding generalizes:

- BP decoder on TRUE sr=61 directly attacks the cnfs_n32 corpus
  (74 known TRUE sr=61 CNFs).
- Many of those CNFs are unsolved at the kissat/cadical scale used
  in the existing campaign.
- A successful BP decoder could newly solve some of them, providing
  empirical wins.

This suggests opening a sibling bet ("structural_decoder") or
extending cascade_aux_encoding's scope to cover TRUE sr=61 too.

### For yale's heuristic local search

The shell architecture insight applies to block2_wang too. If yale's
heuristic operates on the post-shell-eliminated representation, the
search space drops from ~13K dimensions to ~3K hard-core dimensions
(or 192 free schedule + 64 hardlock = 256 effective dims as currently
designed). The 192-dim parameterization yale already uses is
EFFECTIVELY operating on the hard core directly.

Confirms: yale's heuristic and the BP decoder operate on the same
fundamental ~256-dim subspace. They are complementary methods on the
same problem, not duplicates.

## Concrete next probes

(a) **Run tw bound on a "force" mode cascade_aux CNF**: tests
    whether force-mode constraints reduce or increase the hard core
    relative to expose-mode.

(b) **Vertex-cover-based decomposition**: identify the hard-core
    variables explicitly. Likely the message-schedule + tightly-
    coupled Tseitin chains. Per F209, the schedule is vars 2..257
    on cascade_aux; mapping the rest of the hard core to encoder
    semantics would be informative.

(c) **Compare profile across multiple TRUE sr=61 CNFs**: does the
    480 treewidth hold universally? F208-style cross-validation.

(d) **Extract the hard core as a standalone CNF + benchmark CDCL
    on it**: if kissat is much slower on the hard core alone (no
    shell), that confirms BP's marginal would help; if kissat is
    fast on the hard core, the bet's expected speedup is smaller.

## Discipline

- 0 SAT compute (graph analysis only)
- 0 solver runs
- 17s wall on TRUE sr=61 N=32
- F212 = first cross-encoder structural comparison; reveals shell
  is universal but hard-core size encoder-specific
- Strategic implication: TRUE sr=61 could be a parallel decoder
  target with smaller core; consider scope expansion of bet
