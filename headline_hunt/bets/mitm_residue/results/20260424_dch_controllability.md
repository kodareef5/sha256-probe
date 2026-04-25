# dCh controllability under W1[60] — narrowing the cascade-sr=61 search

Realized while extending the analysis: the cascade construction has a 4th free word **W1[60]** that I was anchoring to the cert value in all earlier runs. With cascade-2, w2_60 = w1_60 + cw60 (cw60 is determined). But w1_60 itself is a free 32-bit choice — and it changes e60 (the e-register at round 60) without changing any of the round-60 difference bits.

## Why W1[60] matters for sr=61

For cascade-sr=61: need de61 = 0 = dh60 + dSigma1(e60) + dCh(e60, f60, g60) + dW[61] (modular).

- dh60: candidate constant (function of W57..59) — fixed for a given triple
- dSigma1(e60): zero (cascade gives de60=0, so e1_60 = e2_60 → Sigma1 outputs equal)
- dCh(e60, f60, g60) = (e60 AND df60) XOR (NOT e60 AND dg60). **Depends on e60.**
- dW[61]: schedule-determined function of W57..59

Bit-i of dCh:
- df60[i] AND dg60[i] match? bit is FIXED (= dg60[i] = df60[i])
- df60[i] != dg60[i]? bit is W1[60]-CONTROLLABLE via e60[i]

So `ctrl_mask = df60 XOR dg60` identifies the controllable dCh bits.

## Empirical result (priority candidate, 100 triples)

| HW(ctrl_mask) | count |
|---:|---:|
| 12 | 2 |
| 14 | 1 |
| 15 | 6 |
| 16 | 8 |
| 17 | 19 |
| 18 | 18 |
| 19 | 14 |
| 20 | 19 |
| 21 | 4 |
| 22 | 2 |
| 23 | 5 |
| 24 | 2 |

**Mean HW(ctrl_mask) = 18.4, median = 18, range [12, 24].**

So per (W57, W58, W59) triple, ~**18 bits of dCh are W1[60]-controllable**, leaving ~**14 bits FIXED**.

## Implication for cascade-sr=61 search

The de61 = 0 constraint is 32 modular bits. With 18-bit XOR controllability of dCh per triple (which translates to ~18 bits of modular freedom approximately, modulo carry-chain interactions):

- Probability that a random triple admits a W1[60] making de61 = 0: roughly **2^18 / 2^32 = 2^-14**
- Expected # such triples in the forward-table 2^17 sample: **2^17 × 2^-14 = 2^3 = 8**

So among the 131k forward-table witnesses I built, roughly 8 should have a W1[60] that satisfies de61=0. Verifying takes ~2^32 W1[60] tries per triple (slow per-triple) OR an algebraic XOR-to-modular solver (~1 day of careful implementation).

For full sr=61 collision: also need de62=0 and de63=0. Each adds ~2^-N more constraints. So total expected sr=61 cascade collisions in 4D 128-bit search: 2^128 × 2^-96 ≈ 2^32 (over the universe). But for the specific 131k-witness forward table extended with W1[60] freedom, expected = 131k × 2^32 × 2^-96 = 2^17 × 2^-64 ≈ 2^-47 = essentially zero. 

So even with W1[60] freedom, the forward table alone won't find sr=61 collisions. Need the full 2^96 search (W57..59 × W1[60] = 128 bits, with ~2^-96 hit probability).

## What's actually shippable

This bit-controllability analysis sharpens the cascade-sr=61 search-cost estimate:
- Per-triple W1[60] check via brute force: 2^32 × ~1μs = ~1 hour
- Per-triple via algebraic solver (de61=0 constraint): seconds (~1 day to implement)
- Full 2^96 search: 2^96 × 1μs ≈ 2.5 × 10^21 years. Infeasible directly.

The bet's "MITM gives 2^17 search" interpretation is REFINED: 2^17 covers round-60 freedom, but full sr=61 needs the W1[60] dimension (effective 2^14 constraint on top of 2^17) and de62/63 constraints (additional 2^-64). The cascade-sr=61 problem is genuinely 2^96 under cascade-DP.

This is consistent with Theorem 5 + Theorem 6 + the ~1800 CPU-h empirical result.

## Next-action for whoever wants to push forward

Build the per-triple algebraic solver: given (W57, W58, W59) triple, solve dh60 + dCh(e60_func_of_W1[60], f60, g60) + dW[61] = 0 (mod 2^32) for W1[60]. ~1 day of careful Lipmaa-Moriai-style coding. Solver complexity: O(1) per triple via XOR-to-modular linearization.

If solver works: extend to de62=0 and de63=0 in series. Each is a similar constraint with diminishing controllability.

If all three constraints can be solved per-triple: search complexity drops from 2^128 to 2^96 (forward triples × constraint solving), still infeasible but a real improvement.

For a HEADLINE: combine with a structural argument that further reduces the search space (e.g., MITM at round 61 splitting forward-via-W57..58 vs backward-via-W59..60). Or pivot to a fundamentally different mechanism (block2_wang).

## Files

- This writeup
- The dCh controllability data (in this file's table)
- predict_hard_bits.py and forward_table for the priority candidate already shipped
