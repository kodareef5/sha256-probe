# W[60] sweep: hard-bit positions are W[60]-independent

**Date**: 2026-04-24
**Machine**: macbook
**Sample size**: 100,000 cascade-held samples × 5 W[60] values on MSB candidate
**Status**: addresses next-action #2 from `20260424_hard_residue_findings.md`.

## Result

**The hard-residue bit positions at round 60 are completely independent of W[60].**

Tested 5 W[60] anchor values: `0xb6befe82` (cert), `0x12345678`, `0xdeadbeef`,
`0xcafef00d`, `0x55aa55aa`. For each, ran 100k samples with random
(W[57], W[58], W[59]) and identified the bits in f/g/h at round 60 with
freq within [0.45, 0.55].

Result: **identical 28 bits across all 5 W[60] values** (Jaccard = 1.00 between
every pair). The exact common set:

```
f60: 1, 6, 15, 21
g60: 0, 2, 3, 5, 6, 7, 8, 9, 10, 11, 14, 16, 20, 21, 23, 24, 26, 27, 31
h60: 5, 10, 15, 21, 29
```

## Why this matters

This confirms a clean architectural decoupling for the MITM design:

- **Hard-bit identification** is a function of (m0, fill, kernel_bit) and the
  (W[57], W[58], W[59]) sweep distribution. NOT of W[60].
- **W[60]** is *post-hoc*: once a forward+backward match is found on the
  hard bits, W[60] is determined as the cascade-2 offset that zeros de60.
  W[60] is not a free variable in the table key; it's a derived value.

## Implication for the bet's table design

The forward table is keyed on `(d_f60, d_g60, d_h60)` projected onto the 28
hard-bit positions — call this the 28-bit *hard-residue signature*. Each
table row holds:

```
key:   28-bit hard residue signature
value: (W1[57], W1[58], W1[59])  →  reproduces this signature
```

Since the signature has 28 bits, the table has at most 2^28 ≈ 268M entries.
Each entry is ~12 bytes (3 × uint32) → ~3.2 GB. Add some auxiliary fields
for fast lookups → ~5-10 GB. **Substantially less than the earlier 17 GB
estimate**, because we're keying on 28 bits rather than 32.

W[60] is computed deterministically from the round-59 state, so it doesn't
contribute to the table size.

## Implication for the bet's hypothesis

The bet's "24 hard bits" hypothesis is now even cleaner: **28 bits identified
empirically, and they depend on the candidate but not on the runtime W[60]
choice.** The original "g60, h60" framing is correct; we now know the precise
positions and that they're stable under W[60] variation.

## Open follow-up: algebraic prediction

The W[60]-independence supports a stronger conjecture: the hard-bit positions
are *algebraically* predictable from the candidate's round-56 state.
Specifically:
- df60 = de59. de59 is a function of the round-58 state and dW[59]=cw59.
- dg60 = de58. de58 is a function of the round-57 state and dW[58]=cw58.
- dh60 = de57. de57 is a function of the round-56 state and dW[57]=cw57.

Since cw57, cw58, cw59 are deterministic from the candidate's round-56 state,
the bit positions where de57, de58, de59 are uniform should also be
deterministic from the candidate.

A successful algebraic prediction would let us:
- Skip the empirical 200k-sample run per new candidate.
- Compute the hard-bit positions directly from (m0, fill, kernel_bit) in <1ms.
- Open the door to fast pre-screening: "given a candidate's m0/fill/kernel,
  predict the hard-bit count and identify the candidates with smallest
  hard residues."

This is the natural next investigation. Likely: derive the prediction in
Python, test against the 6 candidates already measured, confirm the predicted
positions match the empirical positions.

## Reproduce

```python
# Inline script (run from repo root):
import sys
sys.path.insert(0, "headline_hunt/bets/mitm_residue/prototypes")
from forward_table_builder import run_one
from lib.sha256 import precompute_state
import random

m0, fill = 0x17149975, 0xffffffff
M1 = [m0] + [fill]*15
M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
s1, W1p = precompute_state(M1)
s2, W2p = precompute_state(M2)

for w60 in [0xb6befe82, 0x12345678, 0xdeadbeef]:
    bit_count = [[0]*32 for _ in range(8)]
    rng = random.Random(42)
    n_kept = 0
    for _ in range(100_000):
        r = run_one(s1, s2, W1p, W2p,
                    rng.getrandbits(32), rng.getrandbits(32),
                    rng.getrandbits(32), w60, return_intermediate=True)
        if r is None: continue
        n_kept += 1
        for reg, v in enumerate(r['diff60']):
            for b in range(32):
                if (v >> b) & 1: bit_count[reg][b] += 1
    uniform_fgh = sum(1 for reg in [5,6,7] for b in range(32)
                      if 0.45 <= bit_count[reg][b]/n_kept <= 0.55)
    print(f"W[60]={w60:#010x}: {uniform_fgh} uniform bits in fgh")
```

~5 seconds per W[60] value on macbook.
