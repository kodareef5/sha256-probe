# Kill criteria — cascade_aux_encoding

Both signals must clear; either failure closes the bet.

## #1 — Treewidth at N=8 not measurably below 110

**Trigger**: After encoder variant built and FlowCutter run on N=8 standard +
cascade-aux versions, the cascade-aux treewidth is within ~10% of 110 (i.e., no
real drop).

**Why this kills**: Treewidth reduction is the central mechanism. If it doesn't
happen, the encoding doesn't help d4 and likely doesn't help SAT either.

**Required evidence to fire**:
- `comparisons/treewidth.md` with FlowCutter output for both encodings at N=8,
  10, 12, repeated 3+ times for variance.

## #2 — No SAT robustness improvement on N=10/N=12 controlled instances

**Trigger**: Even if treewidth drops, SAT solve time / conflict counts on TRUE
sr=61 N=10 controlled instances do not improve vs. standard encoding across at
least 5 seeds.

**Why this kills**: A treewidth drop without solver behavior change means the
encoding is mathematically nicer but practically irrelevant.

**Required evidence to fire**:
- `comparisons/sat_n10.md` with side-by-side seed×encoding solve times.

## Reopen triggers

- New theoretical insight on cascade structure suggests a different auxiliary basis.
- A different solver (e.g., SAT solver with structure-aware branching) shows benefit
  from the auxiliaries even if Kissat does not.
