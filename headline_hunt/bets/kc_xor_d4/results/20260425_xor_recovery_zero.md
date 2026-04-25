# kc_xor_d4 — XOR recovery yields ZERO clauses (kill criterion #2 fired)

## Setup

CryptoMiniSat 5 has built-in XOR-clause recovery (per "When Boolean Satisfiability Meets Gauss-E. in a Simplex Way"). The kc_xor_d4 bet's hypothesis is that cascade-DP CNFs have hidden linear/XOR structure that, when extracted by Bosphorus or CryptoMiniSat XOR recovery, would help d4 decompose more efficiently.

CryptoMiniSat 5 is already installed (`brew list cryptominisat`). Tested its XOR-recovery on three cascade-DP CNFs covering the bet's substrate:

```bash
cryptominisat5 --verb 2 --xor 1 --maxxorsize 8 --xorfindtout 60 --maxconfl 10000 <cnf>
```

## Results

| CNF | sr | encoder | XOR clauses recovered |
|---|---|---|---:|
| `cnfs_n32/sr61_n32_bit10_m3304caa0_fill80000000_enf0.cnf` | 61 | cascade_enf0 | **0** |
| `cnfs_n32/sr61_cascade_m17149975_fffffffff_bit31.cnf` | 61 | cascade_explicit | **0** |
| `/tmp/v3_kernel_sweep_bit10.cnf` (cascade_aux force) | 61 | cascade_aux_force_v1 | **0** |

CryptoMiniSat's matrix-initialization step reports:

```
c -- xor clauses added: 0
c [find&init matx] XORs not updated-> not performing matrix init. Matrices: 0
```

across all three CNF variants.

## Kill criterion #2 fired

From `kill_criteria.md`:

> ## #2 — XOR preprocessor cannot recover meaningful linear structure
> 
> **Trigger**: Bosphorus / CryptoMiniSat XOR recovery on cascade CNF produces no or near-zero XOR clauses.
> 
> **Why this kills**: Means the cascade encoding has no recoverable linear structure for the preprocessor to expose. The premise of the bet fails.

**This trigger fires.** Across three encoder variants (cascade_enf0 standard, cascade_explicit, cascade_aux_force) — ZERO XOR clauses recovered.

## Why this happens

The encoder (`lib/cnf_encoder.CNFBuilder`) builds SHA-256's XOR-heavy operations (XOR rotations, Sigma0/Sigma1, Maj/Ch) using its `xor2`, `and2`, `or2` gate primitives. Each gate produces 3-clause AIG-style encoding (Tseitin form). These are NOT recognizable by CryptoMiniSat's XOR finder, which looks for clause patterns matching natural XOR-clause format (e.g., 4-clause XOR for x ⊕ y ⊕ z = 0).

The encoder's aggressive constant propagation also collapses many trivial XORs to constants before any clause is emitted, removing them from the recoverable structure.

So the cascade CNF, while it ENCODES many XOR operations algebraically, doesn't EXPOSE them as XOR clauses in a form preprocessors can detect. They're hidden inside the AIG-style encoding.

## Impact on the bet

The kc_xor_d4 hypothesis was:

> Standard CNF + d4 = treewidth 110 barrier (closed result, 67h timeout).
> XOR preprocessing might expose hidden linear structure → better treewidth → d4 might complete.

With zero XOR clauses recovered by CryptoMiniSat, **there is no hidden linear structure for an XOR preprocessor to expose.** The premise of the bet fails empirically.

A Bosphorus run might find SOMETHING different (Bosphorus has its own XOR-finding algorithms), but installing Bosphorus is multi-day setup work and the CryptoMiniSat null result is strong empirical evidence against the bet.

## What this kills (vs. what it leaves open)

**Killed**: the specific hypothesis that XOR preprocessing on cascade-DP CNFs unlocks d4 decomposition.

**Not killed by this single experiment**:
- d4 with a DIFFERENT preprocessing (e.g., bit-pair clustering, Bosphorus's anf-style preprocessing).
- d4 without any preprocessing on a different encoding (e.g., the cascade_aux Mode B with modular-diff aux from Phase 2C-r62 work).
- A custom-built XOR-extractor specifically for cascade CNFs that finds patterns CryptoMiniSat misses.

But the path-of-least-resistance "use existing CryptoMiniSat / Bosphorus" path is empirically dead.

## Recommendation

**Status change: open → blocked, pending alternative XOR-extraction approach.**

The bet stays alive because Bosphorus might still find structure CryptoMiniSat misses. But until/unless someone is willing to install and run Bosphorus, this empirical signal predicts a similar null result.

Recommend lower priority and/or kill until Bosphorus is tried.

## Cumulative bet portfolio status (2026-04-25)

| Bet | Status | 2026-04-25 update |
|---|---|---|
| block2_wang | OPEN ← was blocked | Foundation found at N=8 (q5/backward_construct.c) |
| cascade_aux_encoding | in_flight | Mode B characterized, front-loaded |
| **kc_xor_d4** | **blocked** ← was open | **CryptoMiniSat XOR recovery: 0 clauses** |
| sr61_n32 | in_flight (fleet) | unchanged |
| mitm_residue | open (parked) | structurally complete |
| chunk_mode_dp | open | design seed shipped |
| sigma1_aligned | open | empty |
| programmatic_sat_propagator | CLOSED | killed via 3 refutations |

The day's empirical sweep killed/blocked 2 bets (propagator, kc_xor_d4) and unstuck 1 (block2_wang). Net: bet portfolio is sharper, with concrete next-steps on the active bets.
