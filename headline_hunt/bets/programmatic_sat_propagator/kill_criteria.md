# Kill criteria — programmatic_sat_propagator

## #1 — N=8 propagator doesn't reduce conflicts by >10x vs vanilla

**Trigger**: After prototype is running on N=8, conflict count is within an
order of magnitude of vanilla Kissat on the same instance.

**Why this kills**: 10x is roughly the threshold below which custom propagation
implementation cost exceeds the gain. Below that, plain CDCL with better
encoding (`cascade_aux_encoding`) is more cost-effective.

**Required evidence**: `results/n8_conflict_comparison.md` — conflict counts,
restart counts, wall time per seed.

## #2 — Implementation cost dominates CPU savings

**Trigger**: Propagator works but adds enough per-decision overhead that wall
time at N=10/N=12 is no better than vanilla even when conflicts are fewer.

## Reopen triggers

- New IPASIR-UP-compatible solver advance.
- New cascade theory gives propagation rules with formal soundness proofs (vs
  the current ad-hoc rule design).
