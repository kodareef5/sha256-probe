# Kill criteria — mitm_residue

## #1 — Prototype not faster than existing structural solver at small N

**Trigger**: N=8 / N=10 prototype completes but is not measurably faster than the
existing q5 structural solver on the same instances.

**Required evidence**: `results/prototype_vs_baseline.md`.

## #2 — Effective residue width at N=32 substantially > 24

**Trigger**: Bit-budget analysis (`prototypes/bit_budget.md`) determines that
the actual residue width is materially larger than 24 bits at N=32 across all
candidates — making 2^24 work an unrealistic estimate.

**Why this kills**: The headline depends on the 24-bit estimate. If it's actually
2^36 or higher, MITM is no longer competitive with SAT.

## Reopen triggers

- New cascade analysis identifies a smaller effective bottleneck (say 18-20 bits).
- A different structural decomposition gives a different residue with width <= 24.
