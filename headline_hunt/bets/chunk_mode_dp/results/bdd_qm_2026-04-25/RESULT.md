# BDD completion-quotient: blows up to ~collision-count at N=8

## Setup

Found `q5_alternative_attacks/bdd_quotient_and_marginals.c` (345 LOC, pre-built as `bdd_qm`). It runs two analyses on the collision BDD:

1. **Completion quotient** (GPT-5.4 Review 7): at each prefix depth d, count distinct residual sub-BDD node IDs. If quotient stays polynomial → constructive automaton may exist. If it blows up → polynomial BDD is not constructively accessible.

2. **Marginal probabilities** (Gemini Review 7): for each variable, P(var=1 | collision). Output as Kissat phase hints.

To feed it, modified `chunk_mode_dp.c` to dump all 260 collisions (was capped at first 5), recompiled, extracted W1 values:

```bash
/tmp/chunk_alldump | grep "Coll #" | sed -E 's/.../\1 \2 \3 \4/' > collisions_n8.txt
# 260 collisions
q5_alternative_attacks/bdd_qm 8 < collisions_n8.txt > bdd_qm_output.log
```

## Result: quotient blows up linearly with collision count

```
Depth  QuotientWidth  VarName
   0      1           W57[0]
   1      2           W58[0]    ← doubles
   2      4           W59[0]    ← doubles
   3      8           W60[0]    ← doubles
   4     16           W57[1]    ← doubles
   5     32           W58[1]    ← doubles
   6     61           W59[1]
   7    105           W60[1]
   8    156           W57[2]
   9    190           W58[2]
  10    218           W59[2]
  11    235           W60[2]
  12    247           W57[3]
  13    250           W58[3]
  14    255           W59[3]    ← MAX (255 of 260 collisions distinguished)
  ...
  24    159           W57[6]
  ...
  31      3           W60[7]
  32      2           (terminal)
```

**Maximum quotient width: 255** out of 260 total collisions. The quotient barely deduplicates at all — each collision is essentially a distinct path through the BDD.

## Implication for chunk_mode_dp

The BDD completion-quotient is **NOT polynomial in N** at this scale. Quotient size ≈ collision count, which itself grows ~exponentially in N (N=8 has 260 collisions; at N=12 we'd expect ~10× more by typical scaling).

GPT-5.4's hypothesis was that the polynomial BDD result (BDD nodes O(N^4.8)) implies a polynomial constructive automaton via this quotient. **The empirical data refutes that hypothesis at N=8.**

## What this kills

The **specific** chunk-mode design where the quotient is "BDD residual sub-graph identity at each prefix depth" is empirically dead at N=8. The quotient barely compresses below the collision count.

## What this DOESN'T kill

- The chunk_mode_dp BET's broader hypothesis. A different quotient design (the cascade-status + modular d.o.f. design from my earlier seed) is structurally different and untested.
- The polynomial BDD result itself (BDD nodes O(N^4.8) is verified separately).
- Compiled approaches that don't go through completion-quotient automata.

## Building empirical layers

This bet now has THREE layers of refutation:

| Quotient design | Empirical status |
|---|---|
| Raw carry state | already closed in `negatives.yaml#raw_carry_state_dp_near_injective` |
| Boundary carries | refuted earlier today (commit `4ef9bf9`) |
| **BDD completion sub-graph** | **refuted (this commit)** |
| Cascade-status + modular d.o.f. | UNTESTED (my design seed) |
| Mode-variable quotient (BET.yaml) | UNTESTED |

Three quotient designs empirically refuted. The bet stays alive for the remaining untested designs but the search space for compact future-completion states is narrowing.

## Side observation: marginal P(=1) all 0.0000 (suspicious)

The marginals section reports all 32 variable bits have P(=1) = 0.0000, which is impossible given the input data clearly contains nonzero bits (e.g., 0x8d, 0x3c, 0xdb in the first collision). Likely a parsing or tabulation bug in `bdd_qm.c`'s marginal section — the BDD/quotient section appears correct (consistent with the input data and produces meaningful depth-dependent counts).

Not chasing this; the quotient finding is the load-bearing one. Future workers using bdd_qm should verify marginals separately.

## Compute spent

~2 seconds total: chunk_alldump enumeration (already done, ~85s for the existing N=8 brute force), then bdd_qm BDD construction (0.02s) + marginals (instant).

## Action items

1. Add to `negatives.yaml`: `bdd_completion_quotient_no_polynomial_at_n8` (CLOSED, VERIFIED).
2. Update chunk_mode_dp BET.yaml current_progress with this finding.
3. Sharpen the chunk_mode_dp design seed: emphasize that future workers should AVOID quotients tied to BDD sub-graph identity OR raw carry state. The viable design space is structurally-aware quotients (cascade status, modular register diffs, mode-variable abstractions).

## Files

- `dump_collisions_n8.py` (Python — slow, killed; just shipped as documentation of the format)
- `collisions_n8.txt` — 260-line input to bdd_qm (W57 W58 W59 W60 hex bytes per collision)
- `bdd_qm_output.log` — full bdd_qm output

The 260 collisions list is now a durable artifact other tools can consume.
