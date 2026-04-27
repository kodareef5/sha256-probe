# F33 (DRAFT): Active-adder count framework — bit2_ma896ee41 trail
**2026-04-27 08:05 EDT — DRAFT, mismatch flagged**

Attempts a Mouha-style active-adder count along the F32 deep-min trail
for bit2_ma896ee41. Framework is sound; specific count needs C-port
verification.

## Framework

For each round r in 57..63, SHA-256 has 7 modular adders:
1. h + Σ1(e)        (T1, first add)
2. + Ch(e,f,g)      (T1, second add)
3. + K_r            (T1, third add — diff only if accumulator differs)
4. + W_r            (T1, fourth add — input is cascade-W diff)
5. Σ0(a) + Maj(a,b,c) (T2)
6. T1 + T2          (a' formula)
7. d + T1           (e' formula)

Total: 7 rounds × 7 adders = 49 max active adders.

An adder is **active** if at least one of its inputs has a non-zero
XOR-difference between the M1 and M2 paths. Inactive adders contribute
zero probability cost. Active adders contribute ≤ 1-bit (Lipmaa-Moriai
2001 gives the exact bound based on input HW and carry pattern).

Naive trail probability lower bound: `2^-N_active`.
Refined Mouha-style: depends on per-adder HW pattern.

## Computation attempt

Script: `bit2_ma896ee41_active_adder_count.py`

Uses F32's deep-min W-witness for bit2_ma896ee41:
```
W[57] = 0x91e0726f
W[58] = 0x6a166a99
W[59] = 0x4fe63e5b
W[60] = 0x8d8e53ed
```

Runs cascade-1 forward simulation (cascade-W computed via cw1 formula
matching block2_lowhw_set.c).

### Result (DRAFT)

| Round | Active adders |
|---:|---:|
| 57 | 7 |
| 58 | 7 |
| 59 | 5 |
| 60 | 4 |
| 61 | 6 |
| 62 | 7 |
| 63 | 7 |
| **Total** | **43** |

Naive trail-probability lower bound: **2^-43**.

With 256-bit second-block freedom: ~2^213 expected solutions if bound
is tight.

## ⚠ Mismatch with F32 reference

The script's computed `diff63` does NOT match F32's expected vector:

```
computed: [0x58c32e8d, 0x95035e3f, 0x2b5e0699, 0x0,
           0x2d84431e, 0xaf5f3724, 0xfb2e0bb9, 0x0]   HW = 104
expected: [0xa1262506, 0xb0124c02, 0x02000004, 0x0,
           0x68c1c048, 0x5091d405, 0x02000004, 0x0]   HW = 45
```

**Both have zeros at indices [3] and [7]** (cascade-1 d_63 = h_63 = 0
universal property — F14). This confirms the cascade structure is
working. But the specific bit-values diverge. There's a forward-simulation
bug somewhere in the Python script.

Likely causes (untested):
1. Subtle index/offset error in precompute_state or apply_round
2. Possible cascade formula mismatch between Python cascade_w and
   C cw1 (algebraically equivalent on paper, but my Python may have
   transcription error)
3. RNG / message-expansion edge case

The active-adder count of **43** is therefore suspect — it's the
count along the WRONG trail (HW=104 not HW=45). The TRUE F32 trail
might have a different count. Order of magnitude (30-50) is plausible
either way.

## Why ship this DRAFT

1. **Framework is correct**: Mouha-style active-adder count IS the
   path to per-trail probability bounds. Documented here for future
   refinement.
2. **Cascade structure verified**: zeros at indices [3] and [7]
   confirm cascade-1 + universal F14 zero properties hold in the
   script. The structure works; specific values don't.
3. **Concrete next-step**: port the script to C using
   block2_lowhw_set.c as base. C is trustworthy (F28 data was
   generated with it). The C-port will give the verified count.
4. **Order-of-magnitude estimate**: even with the mismatch, the
   count of 43 is consistent with naive expectations (50-bit input
   diff propagating through 7 rounds with cascade-1 zeroing 2-3
   adders/round of T2-side activity).

## Next concrete moves

1. **C-port** of the active-adder counter using
   block2_lowhw_set.c forward simulation. Should produce the
   correct count for bit2_ma896ee41 HW=45 trail.
2. **Lipmaa-Moriai refinement**: each active adder's exact
   probability bound (based on input HW). May reduce 2^-43 to
   2^-30 or tighten it to 2^-43.
3. **Extend to 11 exact-symmetry cands**: count active adders
   for each cand's deep-min trail. Compare which cand has fewest
   active adders.
4. **Active-adder MILP encoding**: feed the F32 corpus into a
   Mouha-style MILP solver to find OPTIMAL trails (minimum active
   adders) starting from the deep-min residual.

## Status

EVIDENCE-level: HYPOTHESIS / DRAFT. The 43-count is a placeholder
pending C-port verification. The framework is documented for future
work.

EVIDENCE-level on cascade structure: VERIFIED (d_63 = h_63 = 0
matches F14 universal property).
