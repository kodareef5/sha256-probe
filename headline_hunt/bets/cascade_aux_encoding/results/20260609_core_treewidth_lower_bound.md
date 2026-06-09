---
date: 2026-06-09
bet: cascade_aux_encoding
status: NO-GO (decomposition/KC route) — cascade CNF treewidth LOWER bound >= 46-51 > 32
author: macbook-claude (fable model test)
evidence_level: VERIFIED (tw lower bound is rigorous + implementation-checked);
                EVIDENCE (interpretation: no width-bounded compiler beats the 2^32 barrier)
---

# Direction A: the missing treewidth LOWER bound closes the "compactness -> construction" route

## Why this probe

The "turn compactness into construction" headline class (TARGETS.md #2 — a SAT-free
compiler / knowledge-compilation enumerator beating the ~2^32 search barrier) had one
genuinely unpursued lead: GPT-5.4's #1-ranked **AND/OR search + component caching + XOR
elimination / separator-based compilation** over the nonlinear core. The `chunk_mode_dp`
Myhill-Nerode kill only foreclosed **forward-DP in a fixed *linear* variable order** (layer
width ~= collision count); it explicitly left open a *different variable order / tree
decomposition* (kill memo: "finding a polynomial-width order is itself the unsolved
problem"). Tree-decomposition / d-DNNF / AND-OR compilation is governed by **treewidth**, a
different cost model than the linear-order frontier.

F211/F212 measured treewidth **upper** bounds (cascade_aux=699, TRUE-sr61 m17149975=480)
via the min-degree heuristic. **An upper bound cannot decide GO/NO-GO**: a UB of 480 is
consistent with a true treewidth of 30 (compilable -> GO) or 150 (-> NO-GO). The deciding
quantity — a treewidth **lower** bound — was never computed. This probe adds it.

## Tool (new, reusing the existing primal-graph machinery)

`encoders/core_treewidth_probe.py` computes a treewidth BRACKET:
- **minor-min-width (MMD+) LOWER bound** — the decisive new number. Rigorous: treewidth is
  minor-monotone, so the min-degree of any minor lower-bounds tw.
- min-fill upper bound (tighter than min-degree).
- min-degree upper bound (reproduces F211/F212 for cross-check).

Implementation verified exact on graphs of known treewidth:
`P6->1, C6->2, K7->6, grid3x3->3` (LB == true tw on all four).

## Result — treewidth LOWER bound is ~50, robust across candidates

| CNF (cascade, N=32) | nodes | LB (MMD+) | UB (min-deg) | UB (min-fill) |
|---|---:|---:|---:|---:|
| sr61_cascade_m17149975 bit31 (the verified candidate) | 11256 | **51** | 498 | >=225 (partial) |
| TRUE_sr61_bit10_3304 | 11184 | **46** | 450 | — |
| sr61_cascade_md41b678d bit4 | 11234 | **50** | 498 | — |

**Treewidth >= 46-51** for every cascade CNF tested. This is a rigorous lower bound (the
prior 480/699 were only upper bounds).

## Verdict — NO-GO for the barrier-beating compiler

A treewidth-bounded compiler (junction tree / bucket elimination / d-DNNF / AND-OR with
component caching — i.e. GPT-5.4's #1 lead) costs ~2^tw. The headline goal is to **beat the
~2^32 search barrier**, which requires tw <~ 32. The measured **lower** bound (~50) means:

> Any width-bounded compilation of the cascade collision CNF costs >= 2^46, **strictly worse
> than the 2^32 SAT barrier it was meant to beat.**

So the decomposition / knowledge-compilation route does not yield a barrier-beating
constructive enumerator. This **rigorously** closes the lead the loose upper bounds could
not. It is consistent with — and independent from — the Myhill-Nerode result
(`chunk_mode_dp`): the **linear-order** width (~= collision count, exponential) and the
**tree-order** width (tw >= ~50 > 32) are *both* large. Two independent width measures agree:
the cascade collision relation has no small-width decomposition in any order.

## Scope / honesty

- The lower bound (tw >= ~50) is rigorous (minor-monotone + verified implementation).
- The leap "no compiler can beat 2^32" is EVIDENCE, not proof: heuristic compilers (d4) can
  occasionally exploit function-level determinism beyond the primal-graph treewidth. But this
  removes the *structural reason to expect success* (the "small treewidth" hope is dead), and
  it agrees with the orthogonal Myhill-Nerode bound. Empirically confirming with d4 would cost
  >= 2^50 and d4 is not installed — the lower bound already settles the barrier-beating
  question, so a d4 run is unnecessary.

## Reproduce
```
python3 headline_hunt/bets/cascade_aux_encoding/encoders/core_treewidth_probe.py \
  cnfs_n32/sr61_cascade_m17149975_fffffffff_bit31.cnf --no-minfill
```

## Negatives.yaml update

Adds the converse of the `forward_completion_quotient` / `bdd_completion_quotient` reopen
triggers: no small-width decomposition exists in *any* order (linear OR tree). Would-change-
my-mind: a variable order or branch decomposition with measured width <~ 32 on a cascade CNF.
