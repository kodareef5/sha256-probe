# Bit-Serial Automaton Width Profile — 2026-04-12

## Experiment

Enumerate all 2^32 message configs at N=8. For each, compute 7 rounds
for both messages and check collision bit by bit (bit 0 first, then 1, etc).
Count how many configs survive each bit-prefix depth.

Effective width = survivors(k) / 2^{4*(N-1-k)}

## Results

| Bit k | Survivors | log2 | Eff.Width | Prune rate |
|-------|-----------|------|-----------|-----------|
| 0 | 133,221,878 | 26.99 | 0.5 | — |
| 1 | 4,168,108 | 21.99 | 0.2 | 96.9% |
| 2 | 130,327 | 16.99 | 0.1 | 96.9% |
| 3 | 3,614 | 11.82 | 0.1 | 97.2% |
| 4 | 1,665 | 10.70 | 0.4 | 53.9% |
| 5 | 804 | 9.65 | 3.1 | 51.7% |
| 6 | 516 | 9.01 | 32.2 | 35.8% |
| 7 | 260 | 8.02 | 260.0 | 49.6% |

## Interpretation

1. **Bits 0-3**: Each bit eliminates ~97% of survivors. This is because the
   lower-order output bits have short carry chains — easy to constrain.

2. **Bits 4-7**: Pruning slows to 35-54%. Higher-order bits depend on long
   carry chains involving all lower bits — harder to constrain.

3. **Total work for bit-serial DP**: sum(survivors) ≈ 137M, vs 4.3B brute force.
   **31x speedup** from per-bit pruning alone.

4. **Bit N-1**: Exactly 260 survivors = #collisions. All configs that survive
   through all bits are actual collisions.

## Connection to GPU laptop's carry automaton

The GPU laptop found "width = 260 at every bit." This refers to the number
of DISTINCT CARRY STATES, not the number of message configs. At bit 0, there
are ~16 possible carry states (from 4 free message bits) but 133M message
configs consistent with any of those carry states. The carry automaton
deduplicates on carry state.

## Implication

A true bit-serial DP that tracks carry states (not full message configs)
would have width profile: ~16 at bit 0, growing toward 260. If the growth
is moderate, the DP would be much faster than O(2^{4N}).

Key question: what's the carry-state width profile? This requires implementing
carry-state deduplication, which is the TRUE bit-serial DP.
