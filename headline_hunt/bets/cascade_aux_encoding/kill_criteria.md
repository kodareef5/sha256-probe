# Kill criteria — cascade_aux_encoding

Updated 2026-04-28 to reflect F207-F214 structural pivot.

## Status of original kill criteria

The original two kill criteria (#1 treewidth at N=8, #2 SAT robustness)
were written for the "make solver faster via aux encoding" direction.
Their status as of 2026-04-28:

### Original #1 — Treewidth at N=8 not below 110

**Status**: superseded by F211/F212 measurements at N=32.

F211 measured cascade_aux N=32 primal-graph treewidth upper bound
at **699** (min-degree heuristic). F212 measured TRUE sr=61 N=32 at
**480**. Direct N=8 comparison was never performed because the bet's
strategic direction shifted (see below). The N=32 measurements are
the relevant baselines now.

The treewidth comparison cascade_aux (699) > TRUE sr=61 (480) is
*opposite* to the original prediction (cascade_aux should LOWER
treewidth). This is itself near-falsifying for the original
direction — but the bet's value has migrated from "treewidth
reduction" to "shell architecture + BP decoder", per F211-F214.

### Original #2 — No SAT robustness improvement on N=10/N=12

**Status**: PARTIALLY FIRED. Mode B's 2-3.4× preprocessing speedup
(F76) is real; the original SPEC's "≥10× SAT speedup" target is
REFUTED. Mode B is a meaningful but not headline-class improvement.

## New kill criteria (BP-decoder direction, F211-F214)

Both signals must clear; either failure closes the bet.

### New #1 — BP decoder fails to converge on hard core within 50 iterations

**Trigger**: When the F211 three-stage decoder (outer-shell elimination
+ BP on hard core + marginal extraction) is implemented, BP message-
passing on the ~3,000-var cascade_aux hard core fails to converge to
useful marginals within 50 iterations.

**Why this kills**: The principles framework predicted convergence
in 10-20 iterations from spectral-gap = 2/3 reasoning. F207 falsified
the gap-9/11 cluster prediction; if the corrected gap-1-3+gap-32
cluster correction also fails to give convergence, the BP direction
is dead.

**Required evidence to fire**:
- Log-domain BP implementation (numerical stability)
- 5+ cascade_aux N=32 instances tested
- Per-instance convergence log showing oscillation or divergence

### New #2 — BP marginals don't reduce CDCL solve time on cascade_aux

**Trigger**: BP marginals computed on hard core are used as decision-
priority hints for kissat. Compared to baseline kissat + Mode B stack
hints, the BP-priority-augmented run does NOT show statistically
significant speedup (≥1.5× median across 10 instances).

**Why this kills**: The marginal-guided search hypothesis is the
bet's mechanism for headline-relevance. If marginals are computed
correctly but don't help CDCL, the structural pivot was the wrong
direction.

**Required evidence to fire**:
- 10 cascade_aux N=32 instances solved with BP-priority + kissat
- Same 10 with baseline + Mode B
- Wall-time comparison + variance analysis

### New #3 — 184-dim active-schedule reformulation doesn't reduce search

**Trigger**: F213/F214 identified the 184-dim active-schedule
parametrization. A reformulated SAT instance restricted to this
184-bit space (with shell variables eliminated) does not solve
faster than the original 13K-var instance.

**Why this kills**: If shell elimination is mathematically correct
but adds no solver value, the structural pivot was an analysis
exercise without algorithmic payoff.

**Required evidence to fire**:
- Standalone shell-elimination preprocessing tool (F213-c)
- Reduced CNF artifacts for ≥5 cascade_aux instances
- Side-by-side kissat solve times on original vs reduced

## Reopen triggers (updated)

- A different solver (BP-aware, IPASIR-UP propagator with
  schedule-aware side-channel) shows benefit from the
  184-dim active-schedule reformulation even if kissat does not.
- A new structural insight on the W1_58 redundancy mechanism
  suggests a different decoder architecture.
- The cross-bet 184-dim alignment (F213) yields a hybrid
  algorithm shape that none of the three component bets can
  achieve alone.

## Strategic context (post-F214)

The bet's structural characterization is now complete (F207-F214):
- Algebraic level: cascade-1 hardlock forces W1_58 entirely.
- Graph-theoretic level: shell-core 70/30 split, treewidth 699,
  ~3,907 hard-core vars.
- Algorithmic level: 184-dim active-schedule space; BP decoder
  candidate; cross-bet alignment with block2_wang and
  programmatic_sat_propagator.

The original "design CDCL+hints variant" direction is essentially
saturated. The next-iteration direction is the BP decoder, with
the three new kill criteria above as its falsification gates.
