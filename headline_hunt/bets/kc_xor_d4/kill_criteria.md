# Kill criteria — kc_xor_d4

## #1 — N=8 still doesn't complete or shows no decomposition signal

**Trigger**: After XOR preprocessing + d4 attempt at N=8 (with both standard
and cascade-aux CNFs), d4 either fails to complete in 67h again OR completes but
component-cache hit rate is no better than baseline.

**Required evidence**: `d4_runs/n8_standard_xor.log`, `d4_runs/n8_aux_xor.log`,
component-cache stats per run.

## #2 — XOR preprocessor cannot recover meaningful linear structure

**Trigger**: Bosphorus / CryptoMiniSat XOR recovery on cascade CNF produces no
or near-zero XOR clauses.

**Why this kills**: Means the cascade encoding has no recoverable linear
structure for the preprocessor to expose. The premise of the bet fails.

## Reopen triggers

- New d-DNNF compiler with better vtree heuristics for ARX-style circuits.
- A different XOR recovery technique (e.g., higher-order linear structure
  detection) becomes available.
