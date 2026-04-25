# Two modular constraints at r=63 — collapse 6 active registers to 4 d.o.f.

The unified Theorem 4 (`da_r − de_r ≡ dT2_r mod 2^32` for r ∈ {61,62,63}) plus shift-register algebra implies **two clean modular constraints among the 6 active registers at r=63** in the cascade-DP residual:

```
C1:  dc_63 ≡ dg_63                    (mod 2^32)
C3:  da_63 − de_63 ≡ dT2_63           (mod 2^32)
```

where `dT2_63 = dSigma0(a_62) + dMaj(a_62, a_61, a_60)`.

## Empirical validation

| corpus | records | C1 | C3 |
|---|---:|---:|---:|
| corpus_msb_200k_hw96.jsonl | 104,700 | 100.0000% | 100.0000% |
| lowest_da_plus_de.jsonl    | 50       | 100%      | 100%      |
| top50_lowest_hw.jsonl      | 50       | 100%      | 100%      |

Total: **104,800/104,800 records** satisfy both constraints.

## Derivation

### C1: `dc_63 ≡ dg_63`

By shift-register propagation:
- `c_63 = b_62 = a_61`
- `g_63 = f_62 = e_61`

Theorem 4 at r=61 (the specialization where dT2_61 = 0): `da_61 = de_61`. So `dc_63 = da_61 = de_61 = dg_63`.

### C3: `da_63 − de_63 ≡ dT2_63`

Unified Theorem 4 at r=63: `da_r − de_r = dT2_r − dd_{r-1}`. At r=63, `dd_62 = dc_61 = db_60 = da_59 = 0` (cascade-1 zero through round 60 propagates through the d-register at r=62). So `dd_62 = 0` and the relation reduces to `da_63 − de_63 = dT2_63`.

### The third natural relation

`db_63 − df_63 ≡ dT2_62` (mod 2^32) is the analogous statement at r=62. Verifying it on the corpus requires `a_59` to compute `dT2_62 = dSigma0(a_61) + dMaj(a_61, a_60, a_59)` correctly (Maj depends on actual values, not differences). The corpus only stores iv_63 which yields a_60..a_63. The fresh-sample cascade-aware harness already verified this 1000/1000 in commit `6ec9524`.

## What this gives us

The cascade-DP residual at r=63 has 6 active registers {a, b, c, e, f, g}. Two modular equations link them, so the modular state has **6 − 2 = 4 free degrees of freedom**.

For trail-design (block2_wang): instead of treating the 6 registers as independent in trail search, treat them as 4-dimensional with two algebraic links. Reduces the trail search space by a factor of 2^64 (two 32-bit moduli pinned).

For SAT encoding (cascade_aux_encoding Mode B): C1 is a trivial XOR-equality between two 32-bit registers (same modular value implies same XOR pattern when both registers are constructed from the same arithmetic primitives — caveat: this is XOR-equivalent only under specific conditions; encoder must use modular addition gates to enforce the equality safely). C3 is a 32-bit modular sum constraint encoded via the existing CNF ripple-carry adder.

For programmatic SAT propagator: C1 fires whenever 32 bits of dc_63 are decided to propagate to dg_63 (and vice versa). C3 fires whenever the (a_61, a_62, a_60) values are determined to constrain the (da_63, de_63) sum.

## Status

Locked at 105,800-sample scale (104,700 corpus + 1000 cascade-aware fresh + 50 trail starters + 50 lowest-HW). The unified Theorem 4 chain is empirically robust.

## Script

`validate_r63_three_constraints.py` — single file, ~70 lines, runs in ~3s on the 104k corpus.
